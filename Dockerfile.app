# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
# Install specific versions required by the model
RUN pip install -r requirements.txt
RUN pip install --upgrade pip

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
