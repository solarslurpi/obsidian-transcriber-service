import logging
import requests
from dotenv import load_dotenv

load_dotenv()

from logger_code import LoggerBase

'''The data messages that must be received by the client include:

data: {data: title}
data: {data: frontmatter}
data: {data: num_chapters}
data: {data: chapter}
data: {data: done}

the goal of this test is to verify the client got these and to hammer out the process of building the transcript considering the fields can come in asynchronously.

'''

logger = LoggerBase.setup_logger(__name__, level=logging.DEBUG)

def handle_sse():
    payload = {}
    headers = {
    'accept': 'application/json'
    }
    url = f"http://127.0.0.1:8000/api/v1/sse"
    logger.debug(f"Sending GET request to {url}")

    response = requests.request("GET", url, headers=headers, data=payload, stream=True)

    event_data = ""
    # SSE is a streaming protocol.
    for line in response.iter_lines():
        # update_state(line)
        print(f"{line}")


def main():
    handle_sse()

if __name__ == "__main__":
    main()





def test_receive_transcript():
    # Step 1: Set up SSE
    handle_sse()

    #The goal of this test is to receive the transcript components  from the `https://www.youtube.com/watch?v=KbZDsrs5roI` YouTube Url.
    # Transcript messages:
    # data: {data: basefilename}
    # data: {data: frontmatter}
    # data: {data: num_chapters}
    # data: {data: chapter}
    # data: {data: done}

    # The test starts by sending out the two HTTP requests to the endpoints.  The POST request is sent to the `/api/v1/process_audio` endpoint with the YouTube URL and audio quality.  The GET request is sent to the `/api/v1/sse` endpoint to receive the transcript messages.  The test then processes the transcript messages and prints them out.  The test is successful if the transcript messages are received and printed out.
    pass