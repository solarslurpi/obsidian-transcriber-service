import json
import requests



def connect_to_process_audio():
    url = "http://127.0.0.1:8000/api/v1/process_audio"
    files=[]
    payload = {'youtube_url': 'https://www.youtube.com/watch?v=KbZDsrs5roI',
    'audio_quality': 'default'}
    headers = {
    'accept': 'application/json'
    }
    print('before post')
    response = requests.post(url, headers=headers, data=payload)
    print('after post')
    return response


def handle_client():
    print("Handling client")
    payload = {}
    headers = {
    'accept': 'application/json'
    }
    url = f"http://127.0.0.1:8000/api/v1/sse"
    print(f"Sending GET request to {url}")
    response = requests.request("GET", url, headers=headers, data=payload, stream=True)

    event_data = ""
    # SSE is a streaming protocol.
    for line in response.iter_lines():
        # Each SSE message has message
        # Line 1: data: {message}
        # line 2: b'data: '
        # line 3: b'data: '
        # line 4: b''
        if line != b'data: ' and line != b'':
            print(f"Line: {line}")
        if line.startswith(b'event: '):
            event_data = line.decode().replace('event: ', '')
        elif line.startswith(b'data: '):
            event_data += line.decode().replace('data: ', '')
        print(f"Event data: {event_data}")


if __name__ == "__main__":

    # response = connect_to_process_audio()
    # print(f'Response from POST: {response.text}')
    handle_client()
