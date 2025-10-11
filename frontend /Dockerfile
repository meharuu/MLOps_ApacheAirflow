FROM python:3.11-slim

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project code
COPY . /app

# Expose the default Streamlit port
EXPOSE 8501

# Command to run the Streamlit application
# The main Streamlit file is often `main.py` in the root or `frontend/app.py`
# Assuming `frontend/app.py` is the main dashboard file
CMD ["streamlit", "run", "frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]