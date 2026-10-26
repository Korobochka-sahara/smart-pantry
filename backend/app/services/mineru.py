'''Работа с локальным MinerU'''
import httpx

from app.schemas.ocr import OCRResponse


class MinerUClient:
    def __init__(
        self,
        base_url: str = "http://ml:8001",
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = httpx.Timeout(
            connect=10.0,
            read=600.0,
            write=60.0,
            pool=10.0,
        )

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