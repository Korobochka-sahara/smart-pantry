'''Координация всего процесса преобразования фото в текст'''
from app.schemas.ocr import OCRResponse
from app.services.mineru import MinerUClient


class OCRService:
    def __init__(self):
        self.mineru = MinerUClient()

    async def recognize_receipt(
        self,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> OCRResponse:
        return await self.mineru.recognize(
            filename=filename,
            content=content,
            content_type=content_type,
        )