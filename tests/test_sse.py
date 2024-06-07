'''The tests in this code are to understand and evaluate sending SSE messages and how the client interprets them. The message types that are sent include:
- `data:{status: message}` - Sent to keep the client updated on progress (or not)
- `data:{data: message}`
- `data:{error: message}`
- `data: {debug: message}` - Provides more detailed information.  This is useful if the process is going along in unexpected ways.

'youtube_url': 'https://www.youtube.com/watch?v=KbZDsrs5roI'

'''
import logging
import requests
import threading

from logger_code import LoggerBase




def post_to_process_audio(logger):
    url = "http://127.0.0.1:8000/api/v1/process_audio"
    files=[]
    payload = {'youtube_url': 'junk_url',
    'audio_quality': 'default'}
    headers = {
    'accept': 'application/json'
    }
    logger.debug('before post')
    response = requests.post(url, headers=headers, data=payload)
    logger.debug('after post')
    return response

def handle_sse(logger):
    payload = {}
    headers = {'accept': 'application/json'}
    url = f"http://127.0.0.1:8000/api/v1/sse"
    logger.debug(f"Sending GET request to {url}")

    # Set up the generator (stream=True) SSE is a streaming protocol.
    response = requests.request("GET", url, headers=headers, data=payload, stream=True)
    # response.iter.lines() is a generator that yields lines from the response.
    # The thread will block here until a line is received.
    for line in response.iter_lines():
        logger.debug(f" {line}")

def test_receive_post_error_message(logger):
    # Create a thread that to handle incoming sse messages.
    thread = threading.Thread(target=handle_sse, args=(logger,))
    response = post_to_process_audio(logger)
    logger.debug(f"Response: {response.text}")

    # Start the new thread
    thread.start()

def main():
    logger = LoggerBase.setup_logger(__name__,level=logging.DEBUG)
    test_receive_post_error_message(logger)

if __name__ == "__main__":
    main()
