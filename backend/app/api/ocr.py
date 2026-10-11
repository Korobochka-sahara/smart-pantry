'''HTTP endpoint и приём изображения'''
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.ocr import OCRResponse
from app.services.ocr import OCRService


router = APIRouter(
    prefix="/ocr",
    tags=["OCR"],
)

ocr_service = OCRService()

MAX_FILE_SIZE = 10 * 1024 * 1024

ALLOWED_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}


@router.post("/receipts", response_model=OCRResponse)
async def recognize_receipt(
    file: UploadFile = File(...),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Поддерживаются JPEG, PNG и WebP.",
        )

    content = await file.read(MAX_FILE_SIZE + 1)

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Файл пуст.",
        )

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Размер файла превышает 10 MB.",
        )

    try:
        return await ocr_service.recognize_receipt(
            filename=file.filename or "receipt.jpg",
            content=content,
            content_type=file.content_type,
        )
    except Exception as exc:
        # В production нужно логировать ошибку,
        # не раскрывая внутренние детали клиенту.
        raise HTTPException(
            status_code=502,
            detail="OCR-сервис недоступен или завершился с ошибкой.",
        ) from exc
    finally:
        await file.close()