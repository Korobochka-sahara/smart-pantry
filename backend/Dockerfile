FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app:/app/backend

WORKDIR /app

COPY backend/requirements.txt /tmp/backend-requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install -r /tmp/backend-requirements.txt

COPY backend /app/backend
# Backend imports the Qwen receipt parser from this small source package;
# MinerU and the OCR HTTP service themselves live in the separate ML image.
COPY ml/__init__.py /app/ml/__init__.py
COPY ml/ocr_service/__init__.py /app/ml/ocr_service/__init__.py
COPY ml/ocr_service/receipt_parser.py /app/ml/ocr_service/receipt_parser.py

WORKDIR /app/backend
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
