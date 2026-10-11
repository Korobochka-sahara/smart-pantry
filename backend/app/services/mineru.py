'''Работа с локальным MinerU'''
import httpx

from app.schemas.ocr import OCRResponse


class MinerUClient:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8001",
        timeout: float = 300.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def recognize(
        self,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> OCRResponse:
        async with httpx.AsyncClient(
            timeout=self.timeout
        ) as client:
            response = await client.post(
                f"{self.base_url}/ocr",
                files={
                    "file": (
                        filename,
                        content,
                        content_type,
                    )
                },
            )

            response.raise_for_status()
            return OCRResponse.model_validate(
                response.json()
            )