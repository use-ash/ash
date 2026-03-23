FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir "fastmcp==1.0"

COPY ash_safety_server.py .

EXPOSE 8080

CMD ["python3", "ash_safety_server.py"]
