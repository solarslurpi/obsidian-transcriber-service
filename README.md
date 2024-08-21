
> Note: Licensed to the Apache Software Foundation (ASF) under one or more contributor license agreements.  See the NOTICE file distributed with this work for additional information regarding copyright ownership.
The ASF licenses this file to You under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.  You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the License for the specific language governing permissions and limitations under the License.

# Obsidian Transcriber Service
The Obsidian Transcriber Service (OTS) is a FastAPI-based application designed to transcribe YouTube videos or audio files into Obsidian notes. It assumes Obidian will be the front end through the Obsidian Transcriber plugin.

# Key Features
Key features include:
- Transcription of YouTube videos.
- Transcription of '.mp3', '.m4a', '.wav', '.flac', '.aac', '.ogg', '.opus' audio files.
- Adjustable transcription speed and quality based on model selection (e.g.: `tiny`, `small`, `medium`, `large`).
- Extraction of metadata from YouTube videos or audio files to populate the front matter of the Obsidian note.
- Content organization into chapters using YouTube's embedded chapter data (title/topic, start time, end time) or by segmenting the audio into time slices.
- Server-Sent Events (SSE) for status updates, data delivery, and error messages to the client.

# Installation
The service can be installed through GitHub or Docker.
> Docker is the preferred method.  It is less hassle to use the Docker image.

## Docker

The docker image assumes a Linux distribution on the host machine. This includes `WSL2`on Windows.  It is assumed Docker is installed on your machine.

> To take advantage of GPUs, ensure that the NVIDIA (cuda) drivers are installed on your Linux-based machine.  For example, I installed the `WSL2` [cuda drivers](https://developer.nvidia.com/cuda/wsl) since I built the docker image on a Windows machine.  See [more information on the layout of the docker image](docs\README_Linux_Dockerfile_tldr.md).

> To get into the details of how the dockerfile was built, see [details on the layout of the docker image](/docs/README_Windows_Dockerfile_tldr.md).

## Pull the image from Docker Hub
Docker images can be downloaded from [Docker Hub](https://hub.docker.com/repository/docker/solarslurpie/transcriber_wsl/general):
```sh
docker pull solarslurpie/transcriber_wsl:latest
```
## Run the image
`docker run --name transcriber  --gpus all -d -p 8081:8081 --restart always solarslurpie/transcriber_wsl:latest`

For more information, see the section on [Running the Container](/docs/README_Linux_Dockerfile_tldr.md#running-the-container)

# Installation Through GitHub

## Clone the Repository
To get started, clone the repository to your local machine using the following command:
```sh
git clone https://github.com/solarslurpi/obsidian-transcriber-service.git
cd obsidian-transcriber-service
```
#### Create a Virtual Environment
Create a virtual environment and activate it:
```sh
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```
#### Install Dependencies
Install the required dependencies using pip:
```sh
pip install -r requirements.txt
```
#### Install FFmpeg
`yt-dlp` is used to download and process the YouTube videos. It requires `FFmpeg`.  Installation of `FFmpeg` varies depending on the operating system.
- Windows: I used `choco install ffmpeg`.  See [gyan.dev builds](https://www.gyan.dev/ffmpeg/builds/) for more information.
- Linux: `apt-get install -y -qqq ffmpeg`
- MacOS: `brew install ffmpeg` I don't have a Mac, so I can't verify this.

#### Start the Service
From the root directory, start the service:
```sh
python src/app.py
```
If the service is started successfully, the log messages will be:\
```
INFO:     Started server process [25]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

# Test the Service
Navigate to the Swagger UI at `http://<ip address to the machine hosting the service>:8081/docs` to test the service. The Swagger UI provides an interactive interface for testing the service's endpoints.  The server exposes the following endpoints:
- `/api/v1/health` - Health check endpoint to verify the service is running.
- `/api/v1/process_audio` - Start the transcription process of either a YouTube video or audio file.
- `/api/v1/cancel` - Cancel the transcription process.
- `/api/v1/sse` - Server-Sent Events endpoint to send status, data, and error messages to the client.
- `/api/v1/missing_content` - Request from the client to retrieve content that should have been sent but the client did not receive.

Open the heath check endpoint and click the "Try it out" then "Execute" buttons   to test the service. The response should be:
```json
{
  "status": "ok"
}
```


# Troubleshooting
## Check Port Settings
The first thing to check if you are unable to connect to the service is the port settings. The default IP and port setting used is `0.0.0.0:8081`,  `0.0.0.0` means the server will listen on all available network interfaces, allowing you to access it from localhost or any other IP address associated with the machine.
### app.py
Check these settings in `app.py`:
```python
uvicorn.run("app:app", host="0.0.0.0", port=8081, reload=True)
```
### Docker
If you are using the Docker container, check the following:
```sh
$ docker ps -a
CONTAINER ID   IMAGE                                              COMMAND               CREATED          STATUS          PORTS                    NAMES
e07feece369c   solarslurpie/obsidian-transcriber-service:latest   "python src/app.py"   46 minutes ago   Up 46 minutes   0.0.0.0:8081->8081/tcp   obsidian-transcriber-service
```
As the example shows what this command helps with:
- Since the -a flag is used, it shows all containers.  It is easy to tell if the container is running or not. Or exists at all.
- The PORTS column shows the port mapping.
## Log files
Each module has its own logger.  For example, in app.py:
```python
import logging
import logging_config

logger = logging.getLogger(__name__)
```
The output format, destination, and level of logging is set within the `logging_config.py` file.  The majority of the logging is set to DEBUG level.  To narrow which area of the app that is causing the issue, change the log level to focus the debug statements on that area.  For example, to focus on the `app.py` file, change the log level to DEBUG in `logging_config.py`:
```python
logging.getLogger('utils').setLevel(logging.WARNING)
logging.getLogger('youtube_handler_code').setLevel(logging.WARNING)
logging.getLogger('transcripton_code').setLevel(logging.WARNING)
logging.getLogger('app').setLevel(logging.DEBUG)
```
while keeping the other loggers at a level high than `DEBUG`. This way, log statements are restricted to this area of interest.

Log message currently go to `sysout`.  Since standard Python logging is used, handlers can be added to have the output go to a file or other destination.
