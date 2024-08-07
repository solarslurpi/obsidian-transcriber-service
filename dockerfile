# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies (except for torch)
RUN pip install --no-cache-dir -r requirements.txt

# Install torch with the specified CUDA version - we are on Windows at this point.
RUN pip install torch --index-url https://download.pytorch.org/whl/cu124

# Copy the rest of the application code into the container
COPY src/ src/

# Expose the port that the app runs on
EXPOSE 8081

# Command to run the application
CMD ["python", "src/app.py"]