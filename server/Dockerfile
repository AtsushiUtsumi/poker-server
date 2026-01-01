FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY poker_server_full.py .
COPY static/ static/

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "poker_server_full.py"]
