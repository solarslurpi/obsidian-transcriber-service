'''This code helped me reorder the yield order of data messages.  It was successful with that. However,I did not do a great job because it should handle two cases: 1. post to process_audio 2. post to missing_content.  I assume there might be dependency injection and better use of pytest which I can go learn right now or let go.  I'm letting it go for now.'''

import asyncio
import json
import logging
import random
from typing import List, Dict, Tuple

from fastapi import  Request

from global_stuff import global_message_queue
from logger_code import LoggerBase
from transcription_state_code import TranscriptionStates

RETRY_TIMEOUT = 3000 # For sending SSE messages

REQUIRED_DATA_MESSAGES = 4  # To build the document

logger = LoggerBase.setup_logger(__name__, logging.DEBUG)

# Different methods to test the client's message handling.
class MessageQueueHandler:
    def handle(self, messages: List[Dict]) -> List[Dict]:
        raise NotImplementedError("The intended use is to use a subclass.")

class ShuffleHandler(MessageQueueHandler):
    def handle(self, messages: List[Dict]) -> List[Dict]:
        random.shuffle(messages)
        return messages
class DropMessageHandler(MessageQueueHandler):
    # Drop the message at index `drop_index`
    def __init__(self, drop_index: int):
        self.drop_index = drop_index

    def handle(self, messages: List[Dict]) -> List[Dict]:
        if 0 <= self.drop_index < len(messages):
            del messages[self.drop_index]
        return messages

# Mock event generator function to simulate SSE events
# This is an integration test of a function within the same process
async def mock_event_generator(request: Request):
    logger.debug("==> mock_event_generator.")
    data_messages_to_send = []
    message_id_counter = 0
    while True:
        # Check if the client has disconnected
        if await request.is_disconnected():
            break

        # Simulate getting a message from the global message queue
        message = await global_message_queue.get()
        # logger.debug(f"!> INCOMING: EVENT: {message['event']}, DATA: {message['data'][:20]}")
        # Handle 'data' events by collecting and reversing messages
        if message['event'] == 'data':
            data_part = json.loads(message['data'])  # Parse the JSON string into a Python dictionary
            if 'key' in data_part:
                for _ in range(3):  # Send the message 3 times as an example
                    message_id_counter, message_dict = generate_message(message, message_id_counter, RETRY_TIMEOUT)
                    yield message_dict
                    logger.flow("!!!! Sent important key message.")
                    await asyncio.sleep(1)  # Asynchronous pause for 1 second between sends
                return

            data_messages_to_send.append(message)
            # logger.flow(f"+ Added data message: {message['data'][:20]}. Total data messages: {len(data_messages_to_send)}")
            # collect all the data messages (REQUIRED_DATA_MESSAGES).
            key_names = []
            if len(data_messages_to_send) < REQUIRED_DATA_MESSAGES:
                for message in data_messages_to_send:
                    # Get the key name from the 'data' dictionary
                    data_dict = json.loads(message['data'])
                    key_name = list(data_dict)[0]
                    # Append the key name to the list
                    key_names.append(key_name)
                logger.flow(f"!>? Have {len(data_messages_to_send)} of {REQUIRED_DATA_MESSAGES}.\n-----\nhave {len(data_messages_to_send)}. {', '.join(key_names)}" )
            else:
                logger.flow(f"!>=/= Have {REQUIRED_DATA_MESSAGES} data messages, dropping messages")
                drop_message = DropMessageHandler(2)
                data_messages_to_send = drop_message.handle(data_messages_to_send)
                # drop_message_handler = DropMessageHandler(3)
                # data_messages_to_send = drop_message_handler.handle(data_messages_to_send)
                # logger.debug each message on a line for readability.
                logger.flow(f"-=- messages being sent:\n")
                for msg in data_messages_to_send:
                    # Get the key name from the 'data' dictionary
                    data_dict = json.loads(message['data'])
                    key_name = list(data_dict)[0]
                    # Append the key name to the list
                    key_names.append(key_name)
                logger.flow(f"!>-> Sending\n-----\n{', '.join(key_names)}" )
                for msg in data_messages_to_send:
                    message_id_counter, message_dict = generate_message(msg, message_id_counter, RETRY_TIMEOUT)
                    yield message_dict
        else:
            logger.flow(f"!!> immediate send:  event: {message['event']} message: {message['data'][:20]}")
            message_id_counter, message_dict = generate_message(message, message_id_counter, RETRY_TIMEOUT)
            yield message_dict

def generate_message(message, message_id_counter, RETRY_TIMEOUT) -> Tuple[int, Dict]:
    message_id_counter += 1
    message_dict = {
        "event": message['event'],
        "id": str(message_id_counter),
        "retry": RETRY_TIMEOUT,
        "data": message.get('data', '')  # Assuming you want to handle missing 'data' gracefully
    }
    return message_id_counter, message_dict