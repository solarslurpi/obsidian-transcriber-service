- i was using python3.12 and installed and used that but it adds significant overhead...
- use yt_dlp which uses ffmpeg and ffprobe. I install this.
- go up the application stack and start with the docker file at the head of the stack.


# Docker on Windows -> WSL2
> Note: After much gnashing of teeth, I was finally able to get a dockerfile that worked on Windows and used the GPU.  While I acknowledge limitless cluelessnes, I found building this dockerfile extremely tedious.  I do acknowledge my limited knowledge of docker did not make this challenge any easier.
# WSL2 Dockerfile
Requires the following to be installed on your Windows PC:
- Docker Desktop or VS Code Docker extension.
- WSL2.
-


# Building the Container on WSL2

`docker build -f dockerfile.transcriber_cuda_wsl -t solarslurpie/transcriber_cuda_wsl:latest .`

`-f dockerfile.transcriber_cuda_wsl`: The name of the Dockerfile to build the image from.
`-t solarslurpie/transcriber_cuda_wsl:latest`: The name and tag of the image to build.
`.`: The path to the build context. In this case, the Dockerfile is in the current directory.

# Running the Container on WSL2

`docker run --name transcriber  --gpus all -d -p 8081:8081 --restart always solarslurpie/transcriber_cuda_wsl:latest`

`--name`: name of the container. Assigning a name is optional but makes it easier to interact with the container. For example:
```
docker stop <name>
docker start <name>
docker logs <name>
...
```
`--gpus all`: Must be used to enable GPU support in the container.
`-d`: Run the container in the background (i.e.: detached mode).
`-p 8081:8081`: Map port 8081 on the host to port 8081 on the container.
`--restart always`: Restart the container if it stops.
`solarslurpie/transcriber_cuda_wsl:latest`: The name of the image to run.