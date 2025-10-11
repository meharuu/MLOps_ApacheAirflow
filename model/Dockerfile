# Use a Python image with development tools, as training often involves compilation
FROM python:3.11

WORKDIR /app

# Install system dependencies if required for ML libraries (e.g., specific compilers)
# RUN apt-get update && apt-get install -y build-essential

# Copy and install dependencies
COPY requirements.txt .
# Install dependencies, ensuring ML-specific packages are included
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project files
COPY . /app

# A model container often doesn't run a service by default but executes a script.
# Use an entrypoint to make it easy to run scripts like training or ingestion.
# ENTRYPOINT ["/bin/bash"]
# Example command for a training run (if triggered manually or by Airflow):
# CMD ["python", "scripts/data_ingestion.py"]