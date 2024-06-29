
import logging
import requests
import time

from logger_code import LoggerBase
# Post transcribing mp3 file.
# Send Get to set up sse channel.
# Assert the following messages occur before the done message.
# measure the time between getting different messages.


logger = LoggerBase.setup_logger(__name__, level=logging.DEBUG)


def handle_sse(logger):
    payload = {}
    headers = {'accept': 'application/json'}
    url = f"http://127.0.0.1:8000/api/v1/sse"
    logger.debug(f"Sending GET request to {url}")

    response = requests.request("GET", url, headers=headers, data=payload, stream=True)
    total_start_time = time.time()
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