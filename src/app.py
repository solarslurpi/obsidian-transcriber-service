#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
###########################################################################################
# Author: Margaret Johnson
# Copyright (c) 2024 Margaret Johnson
###########################################################################################
import asyncio

import json
import logging
import logging_config
import os
from typing import Optional, List



from fastapi import FastAPI, Request, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette import EventSourceResponse


from exceptions_code import MissingContentException
from global_stuff import global_message_queue
from process_check_code import process_check, send_sse_data_messages
from audio_processing_model import AudioProcessRequest, save_local_audio_file
from transcription_state_code import TranscriptionStatesSingleton
from utils import send_sse_message

# Create a logger instance for this module
logger = logging.getLogger(__name__)


LOCAL_DIRECTORY = os.getenv("LOCAL_DIRECTORY", "local")
# Ensure the local directory exists

RETRY_TIMEOUT = 3000 # For sending SSE messages



class MissingContent(BaseModel):
    key: str
    missing_contents: List[str]


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/v1/process_audio")
async def init_process_audio(youtube_url: Optional[str] = Form(None),
                             upload_file: UploadFile = File(None),
                             audio_quality: str = Form("default")):
    async def clear_queue(queue):
        while True:
            try:
                queue.get_nowait()  # remove an item
            except asyncio.QueueEmpty:
                break
    try:
        await clear_queue(global_message_queue)
        # Instantiante and trigger Pydantic class validation.
        audio_input = AudioProcessRequest(
            youtube_url=youtube_url,
            audio_filepath=upload_file.filename if upload_file else None,
            audio_quality=audio_quality
        )
    except ValueError as e:
        await send_sse_message("server-error", str(e))
        return {"status": f"Error reading in the audio input. Error: {e}"}
    if upload_file:
        # Save the audio file locally to use for transcription processing.
        try:
            audio_input.audio_filepath = save_local_audio_file(upload_file)
        except OSError as e:
            error_message = f"OS error occurred while saving uploaded audio file: {e}"
            await send_sse_message("server-error", error_message)
            return {"status": error_message}
        except Exception as e:
            error_message = f"Unexpected error occurred while saving uploaded audio file: {e}"
            await send_sse_message("server-error", error_message)
            return {"status": error_message}
    asyncio.create_task(process_check(audio_input))
    return {"status": "Transcription process has started."}

@app.post("/api/v1/missing_content")
# Body(...) tells fastapi that the input is json. It will then validate the input again the MissingContentRequest model.  If the input does not match the model, an error will be returned.
async def missing_content(missing_content: MissingContent):
    logger.debug(f"Received missing content list: {missing_content}")
    try:
        states = TranscriptionStatesSingleton.get_states()
        state = states.get_state(missing_content.key)
        if not state:
            await send_sse_message("server-error", f"No state found for key: {missing_content.key}.  Do not know what content is wanted.")
            raise KeyError(f"No state found for key: {missing_content.key}")
    except KeyError as e:
        return {"status": f"Error processing missing content. Error {e}"}
    try:
        # the missing_content prop is perhaps most useful for testing.  Understanding whethe a missing_content event has been sent.
        await send_sse_data_messages(state, missing_content.missing_contents)
    except MissingContentException as e:
        await send_sse_message("server-error", f"Error processing missing content. Error: {e}")
        return {"status": f"Error processing missing content. Error: {e}"}
    return {"status": f"{', '.join(missing_content.missing_contents)}"}



@app.get("/api/v1/sse")
async def sse_endpoint(request: Request):
    client_ip = request.client.host
    method = request.method
    url = str(request.url)
    user_agent = request.headers.get('user-agent', 'unknown')

    logger.debug(f"app.get.sse: Request received: {method} {url} from {client_ip}")
    logger.debug(f"app.get.sse: User-Agent: {user_agent}")
    # I should learn pytest better. I want to test sse messages.
    # return EventSourceResponse(mock_event_generator(request))
    return EventSourceResponse(event_generator(request))

async def event_generator(request: Request):
    message_id_counter = 0
    try:
        while True:
            if await request.is_disconnected():
                break
            message = await global_message_queue.get()
            try:
                event = message['event']
                data = message['data']

                if event == "server-error" or (event == "data" and data == 'done'):
                    logger.debug(f"--> EXITING EVENT GENERATOR. Event: {event}, Data: {data}")
                    asyncio.sleep(0.1)
                    break

                # Just in case the message is an empty string or None.
                if message:
                    info = data
                    if event == "data":
                    # FOR DEBUGGING START
                        dict_data = json.loads(data)
                        key = list(dict_data.keys())[0]
                        if key not in ['num_chapters', 'basename', 'key']:
                            info = key
                        if key in ['chapter']:
                            info ="chapter" + json.dumps(dict_data["chapter"]["number"]) + json.dumps(dict_data["chapter"]["text"][:200] )
                    logger.debug(f"--> SENDING MESSAGE. Event: {event}, Info: {info}")
                    # FOR DEBUGGING STOP
                    message_id_counter += 1
                    yield {
                        "event": event,
                        "id": str(message_id_counter),
                        "retry": RETRY_TIMEOUT,
                        "data": data
                    }
            except Exception as e:
                logger.error(f"Error sending message: {message}", exc_info=e)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received. ")

@app.get("/api/v1/health")
async def health_check():
    logger.debug("app.health_check: Health check endpoint accessed.")
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8081, reload=True)