import logging
import requests
import threading

from logger_code import LoggerBase

def handle_sse(logger):
    payload = {}
    headers = {'accept': 'application/json'}
    url = f"http://127.0.0.1:8000/api/v1/sse"
    logger.debug(f"handle_sse: Sending GET request to {url}")

    response = requests.request("GET", url, headers=headers, data=payload, stream=True)

    event_type = None
    data_lines = []

    for line in response.iter_lines():
        if len(line) == 0:
            # End of an event, process the event
            if data_lines:
                handle_event(event_type, data_lines, logger)
            # Reset for the next event
            event_type = None
            data_lines = []
        else:
            line = line.decode('utf-8')
            logger.debug(f" ****{line}****")
            if line.startswith('event:'):
                event_type = line.split(': ', 1)[1]
            elif line.startswith('data:'):
                data_lines.append(line[5:].strip())
            elif line.startswith('id:'):
                event_id = line.split(': ', 1)[1]
            elif line.startswith('retry:'):
                retry_timeout = line.split(': ', 1)[1]
            elif line.strip() == '':
                # End of an event, process the event
                if data_lines:
                    handle_event(event_type, data_lines, logger)
                # Reset for the next event
                event_type = None
                data_lines = []

def handle_event(event_type, data_lines, logger):
    data = "\n".join(data_lines)
    logger.info(f"Event: {event_type if event_type else 'message'}")
    logger.info(f"Data: {data}")

def test_receive_post_error_message(logger):
    thread = threading.Thread(target=handle_sse, args=(logger,))
    thread.start()
    response = post_to_process_audio(logger)
    logging.debug(f"Response Status Code: {response.status_code}")
    logging.debug(f"Response Body: {response.text}")
    logging.debug(f"Response Headers: {response.headers}")
    logging.debug(f"ResponseElapsed Time: {response.elapsed}")

def post_to_process_audio(logger):
    url = "http://127.0.0.1:8000/api/v1/process_audio"
    payload = {'youtube_url': 'junk_url', 'audio_quality': 'default'}
    headers = {'accept': 'application/json'}
    response = requests.post(url, headers=headers, data=payload)
    logging.debug(f"Response Status Code: {response.status_code}")
    logging.debug(f"Response Body: {response.text}")
    logging.debug(f"Response Headers: {response.headers}")
    logging.debug(f"ResponseElapsed Time: {response.elapsed}")
    return response

def main():
    logger = LoggerBase.setup_logger(__name__, level=logging.DEBUG)
    test_receive_post_error_message(logger)

if __name__ == "__main__":
    main()
