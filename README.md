
> Note: Licensed to the Apache Software Foundation (ASF) under one or more contributor license agreements.  See the NOTICE file distributed with this work for additional information regarding copyright ownership.
The ASF licenses this file to You under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License.  You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.  See the License for the specific language governing permissions and limitations under the License.

# Obsidian Transcriber Service
The Obsidian Transcriber Service is a FastAPI-based application designed to transcribe YouTube videos or audio files into text. It assumes Obidian will be the front end through the Obsidian Transcriber plugin.  The service leverages OpenAI's whisper model to process audio files and generate metadata and text from the audio files into an Obsidian note with the metadata as front matter.

## Key Features
Key features include:
- Transcription of YouTube videos.
- Transcription of '.mp3', '.m4a', '.wav', '.flac', '.aac', '.ogg', '.opus' audio files.
- Custom setting the audio quality per transcription to:
    - "default":  "tiny.en",
    - "tiny": "tiny.en",
    - "small": "small.en",
    - medium": "medium.en",
    - "large": "large-v3"
> Note: The quality mappings map a user friendly name to the actual quality setting used by Whisper.
- Extraction of metadata from YouTube videos or audio files to populate the front matter of the Obsidian note.
- Organizing content into chapters by either utilizing chapter information embedded within a YouTube video or dividing the audio file into manageable time slices. By breaking the transcription into chapters, it becomes more structured and client-friendly, facilitating easier review, editing, and analysis.
- Return of SSE messages to the client providing both status messages as well as data messages containing the transcription text and metadata.
- Logging and debugging support to track the transcription process.


## Installation
To set up the Obsidian Transcriber Service on your local machine, follow these steps. This guide will walk you through cloning the repository, setting up a virtual environment, installing dependencies, and starting the service.

### Through GitHub
To set up the Obsidian Transcriber Service on your local machine, follow these steps.
#### Clone the Repository
To get started, clone the repository to your local machine using the following command:
```sh
git clone https://github.com/your-username/obsidian-transcriber-service.git
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
## Through Docker
The dockerfile for Windows is provided in the repository.
#### Download the Docker Image
Go to the Docker Hub repository and download the image:
```sh
To build the Docker image, navigate to the root directory of the repository and run the following command:
```sh
docker build -t obsidian-transcriber-service .
```
## Get Started
Once the service is running, try connecting via FastAPI's Swagger UI. Open a browser and navigate to `http://127.0.0.1:8080/docs`. You should see the Swagger UI, which provides an interactive interface for testing the service's endpoints.

### Troubleshooting
#### Check Port Settings
If you are unable to connect to the service, check the port settings. The default IP and port setting used is `0.0.0.0:8081`,  `0.0.0.0` Means the server will listen on all available network interfaces, allowing you to access it from localhost or any other IP address associated with the machine.
##### app.py
Check these settings in `app.py`:
```python
uvicorn.run("app:app", host="0.0.0.0", port=8081, reload=True)
```
##### Docker
If you are using the Docker container, check the following:
```sh
$ docker ps -a
CONTAINER ID   IMAGE                                              COMMAND               CREATED          STATUS          PORTS                    NAMES
e07feece369c   solarslurpie/obsidian-transcriber-service:latest   "python src/app.py"   46 minutes ago   Up 46 minutes   0.0.0.0:8081->8081/tcp   obsidian-transcriber-service
```
As the example shows what this command helps with:
- Since the -a flag is used, it shows all containers.  It is easy to tell if the container is running or not. Or exists at all.
- The PORTS column shows the port mapping.




## Usage
The Obsidian Transcriber Service is designed to be used in conjunction with the Obsidian Transcriber plugin. The plugin sends a request to the service to transcribe a YouTube video or audio file. The service processes the request and returns the transcription text and metadata to the plugin, which then creates an Obsidian note with the transcription text and metadata as front matter.
### FastAPI Endpoints