


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


```python
from faster_whisper import WhisperModel, BatchedInferencePipeline

model = WhisperModel("medium", device="cuda", compute_type="float16")
batched_model = BatchedInferencePipeline(model=model)
segments, info = batched_model.transcribe("audio.wav", batch_size=16)

for segment in segments:
print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))

ImportError: cannot import name 'BatchedInferencePipeline' from 'faster_whisper'
https://github.com/SYSTRAN/faster-whisper/issues/935

```
The batched inference pull request has been merged but hasn't been published to PYPI yet. Try installing faster-whisper directly from the source:

```sh
pip install --force-reinstall "faster-whisper @ https://github.com/SYSTRAN/faster-whisper/archive/refs/heads/master.tar.gz"
```
-> Batched