# Use NVIDIA's CUDA base image
FROM nvidia/cuda:12.2.0-runtime-ubuntu20.04

# Install dependencies
RUN apt-get update && \
    apt-get install -y \
        python3.12 \
        python3.12-venv \
        python3.12-dev \
        python3-pip \
        python3-setuptools \
        python3-wheel \
        && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set Python 3.12 as the default python3 and pip3
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 && \
    update-alternatives --install /usr/bin/pip3 pip3 /usr/bin/pip3 1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies (except for torch)
RUN pip install --no-cache-dir -r requirements.txt

# Create the state_cache directory
RUN mkdir state_cache

# Copy the rest of the application code into the container
COPY src/ src/

# Expose the port that the app runs on
EXPOSE 8081

# Install the NVIDIA Container Toolkit

RUN apt-get update && apt-get install -y curl gnupg2

RUN curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
    && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

RUN apt-get update && apt-get install -y nvidia-container-toolkit

# Configure the container runtime to use the NVIDIA GPU
ENV NVIDIA_VISIBLE_DEVICES all

# Command to run the application
# CMD ["python", "src/app.py"]

# Command to run the application
# CMD ["bash", "-c", "python src/app.py || bash"]

# Command to run the Python REPL
CMD ["python"]