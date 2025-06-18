FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn==0.24.0 \
    numpy==1.26.0 \
    pydantic==2.4.2

# Copy application
COPY main.py .

# Expose HTTP port for benchmarking
EXPOSE 8002

# Run the agent
CMD ["python", "main.py"]