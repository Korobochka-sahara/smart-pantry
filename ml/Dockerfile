FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MINERU_TIER=standard

# Runtime libraries commonly needed by document/image processing wheels.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libgl1 libgomp1 libsm6 libxext6 libxrender1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/ml/ocr_service
COPY ml/requirements.txt /tmp/ml-requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install -r /tmp/ml-requirements.txt

COPY ml/ocr_service/main.py /app/ml/ocr_service/main.py
COPY ml/ocr_service/mineru_service.py /app/ml/ocr_service/mineru_service.py

EXPOSE 8001
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
