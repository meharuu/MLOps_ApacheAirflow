# Use a Python base image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy the requirements file first to leverage Docker layer caching
COPY requirements.txt .
# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app

# The model file is likely loaded from /app/model/model.pkl
# The main application file is likely `api/app.py` or `api/main.py`
# Assuming the main app object is named 'app' in `api/app.py`
EXPOSE 8000

# Command to run the FastAPI application using Uvicorn
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]