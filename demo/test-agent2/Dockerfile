FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY arbitrage_agent.py .

CMD ["python", "arbitrage_agent.py"]