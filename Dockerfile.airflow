# Use the official Airflow image for stability and easy setup
# Choose the version corresponding to your environment
FROM apache/airflow:2.8.0-python3.11

# Set the Airflow home directory
ENV AIRFLOW_HOME=/opt/airflow

# Install dependencies needed by the DAGs (Database connectors, pandas, etc.)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project scripts and files, though DAGs will be mounted via volume
COPY . /app

# Use the Airflow user provided by the base image
USER airflow