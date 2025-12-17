FROM python:3.9-slim

WORKDIR /app

COPY backend/requirements.txt backend/requirements.txt

RUN pip install --no-cache-dir -r backend/requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]