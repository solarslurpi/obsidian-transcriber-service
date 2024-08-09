FROM ghcr.io/opennmt/ctranslate2:4.3.1-ubuntu20.04-cuda12.2

RUN apt-get update -qqq

RUN apt-get install -y -qqq software-properties-common wget

RUN add-apt-repository -y ppa:deadsnakes

RUN apt-get install -y -qqq python3.12

RUN apt-get install -y -qqq python3.12-distutils

# The app uses yt_dlp for converting youtube videos to audio files.  This requires ffmpeg and ffprobe.
RUN apt-get install -y -qqq ffmpeg
# pip didn't work without this.
RUN wget https://bootstrap.pypa.io/get-pip.py -O get-pip.py

RUN python3.12 get-pip.py

RUN rm -rf /var/lib/apt/lists/* get-pip.py

# Set the working directory in the container
WORKDIR /app
# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies and create the state_cache directory in a single RUN command
RUN python3.12 -m pip install --no-cache-dir -r requirements.txt && \
    mkdir state_cache

# Copy the rest of the application code into the container
COPY src/ src/

# Set the working directory in the container
WORKDIR /app

# Expose the port that the app runs on
EXPOSE 8081

# Command to run the application
ENTRYPOINT ["python3.12", "src/app.py"]
