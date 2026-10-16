import pytest

from app.api import ocr as ocr_module


def mock_ocr_service(monkeypatch, *, result=None, error=None):
    """Подменяет OCR-сервис, не вызывая MinerU и LLM."""
    calls = {}

    async def fake_recognize_receipt(
        filename,
        content,
        content_type,
        db,
    ):
        calls["filename"] = filename
        calls["content"] = content
        calls["content_type"] = content_type
        calls["db"] = db

        if error is not None:
            raise error

        return result or {
            "status": "completed",
            "tier": "standard",
            "markdown": "Молоко 1 л",
            "items": [],
        }

    monkeypatch.setattr(
        ocr_module.ocr_service,
        "recognize_receipt",
        fake_recognize_receipt,
    )

    return calls


def test_ocr_receipt_success(client, monkeypatch):
    """Принимает изображение и возвращает результат OCR."""
    calls = mock_ocr_service(monkeypatch)

    response = client.post(
        "/ocr/receipts",
        files={
            "file": (
                "receipt.jpg",
                b"fake image bytes",
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "completed"
    assert data["tier"] == "standard"
    assert data["markdown"] == "Молоко 1 л"
    assert data["items"] == []

    assert calls["filename"] == "receipt.jpg"
    assert calls["content"] == b"fake image bytes"
    assert calls["content_type"] == "image/jpeg"
    assert calls["db"] is not None


def test_ocr_rejects_unsupported_content_type(client):
    """Не принимает файлы неподдерживаемого типа."""
    response = client.post(
        "/ocr/receipts",
        files={
            "file": (
                "receipt.txt",
                b"some text",
                "text/plain",
            )
        },
    )

    assert response.status_code == 415


def test_ocr_rejects_empty_file(client):
    """Возвращает ошибку для пустого файла."""
    response = client.post(
        "/ocr/receipts",
        files={
            "file": (
                "receipt.jpg",
                b"",
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 400


def test_ocr_rejects_file_over_10_mb(client):
    """Не принимает изображение больше 10 MiB."""
    response = client.post(
        "/ocr/receipts",
        files={
            "file": (
                "large.jpg",
                b"x" * (10 * 1024 * 1024 + 1),
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 413


def test_ocr_service_error_returns_502(client, monkeypatch):
    """Преобразует ошибку OCR-сервиса в HTTP 502."""
    mock_ocr_service(
        monkeypatch,
        error=RuntimeError("Test OCR failure"),
    )

    response = client.post(
        "/ocr/receipts",
        files={
            "file": (
                "receipt.jpg",
                b"fake image bytes",
                "image/jpeg",
            )
        },
    )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "OCR-сервис недоступен или завершился с ошибкой."
    )