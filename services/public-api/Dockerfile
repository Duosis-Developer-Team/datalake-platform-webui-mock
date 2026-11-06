FROM python:3.11-slim

WORKDIR /app
COPY services/public-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/public-api/public_api/ ./public_api/
EXPOSE 8000
CMD ["uvicorn", "public_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
