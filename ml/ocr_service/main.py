import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel

from mineru_service import MinerUService


app = FastAPI(title="Smart Pantry OCR Service")

OCR_TIER = os.getenv("MINERU_TIER", "standard")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

mineru_service = MinerUService(tier=OCR_TIER)


class OCRResult(BaseModel):
    status: str
    tier: str
    markdown: str


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "ocr",
        "tier": OCR_TIER,
    }


@app.post("/ocr", response_model=OCRResult)
async def recognize_receipt(
    file: UploadFile = File(...),
):
    allowed_types = {"image/jpeg", "image/png", "image/webp"}

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=415,
            detail="Поддерживаются JPEG, PNG и WebP.",
        )

    suffix_by_type = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }
    suffix = suffix_by_type[file.content_type]

    temp_path = None

    try:
        content = await file.read(MAX_FILE_SIZE + 1)

        if not content:
            raise HTTPException(
                status_code=400,
                detail="Получен пустой файл.",
            )

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="Размер файла превышает 10 MB.",
            )

        with tempfile.NamedTemporaryFile(
            suffix=suffix,
            delete=False,
        ) as temp_file:
            temp_file.write(content)
            temp_path = Path(temp_file.name)

        markdown = await mineru_service.parse(temp_path)

        return OCRResult(
            status="completed",
            tier=OCR_TIER,
            markdown=markdown,
        )

    except HTTPException:
        raise
    except Exception as exc:
        # Подробности ошибки остаются в логах сервиса.
        print(f"OCR error: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=502,
            detail="Не удалось распознать изображение.",
        ) from exc

    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()

        await file.close()