'''Координация всего процесса преобразования фото в текст'''
import logging
import time
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.schemas.ocr import OCRResponse
from app.services.mineru import MinerUClient
from app.services.product_matching import find_product_candidates
from ml.ocr_service.receipt_parser import parse_receipt


logger = logging.getLogger(__name__)


class OCRService:
    def __init__(self):
        self.mineru = MinerUClient()

    async def _parse_receipt_async(self, markdown: str):
        """Запускает синхронный парсер Qwen вне event loop."""
        return await run_in_threadpool(
            parse_receipt,
            markdown,
        )

    async def recognize_receipt(
        self,
        filename: str,
        content: bytes,
        content_type: str,
        db: Session,
    ) -> OCRResponse:
        
        total_started = time.perf_counter()

        logger.info(
            "OCR: старт | file=%s | size=%d b | type=%s",
            filename, len(content), content_type,
        )
        # 1. Получаем результат распознавания изображения от MinerU
        started = time.perf_counter()
        try:
            mineru_result = await self.mineru.recognize(
                filename=filename,
                content=content,
                content_type=content_type,
            )
        except Exception:
            logger.exception(
                "OCR: MinerU упал | file=%s | %.2f c",
                filename, time.perf_counter() - started,
            )
            raise

        logger.info(
            "OCR: MinerU ok | file=%s | status=%s | tier=%s | markdown=%d симв. | %.2f c",
            filename, mineru_result.status, mineru_result.tier,
            len(mineru_result.markdown), time.perf_counter() - started,
        )

        #markdown может быть огромным и содержать персональные данные — только DEBUG
        logger.debug("OCR: markdown от MinerU | file=%s\n%s", filename, mineru_result.markdown)

        # 2. Qwen синхронный, поэтому запускаем его вне event loop
        started = time.perf_counter()
        try:
            parsed_items = await self._parse_receipt_async(
                mineru_result.markdown,
            )
        except Exception:
            logger.exception(
                "OCR: парсер (Qwen) упал | file=%s | %.2f c",
                filename,
                time.perf_counter() - started,
            )
            raise

        logger.info(
            "OCR: распознано позиций=%d | file=%s | %.2f c",
            len(parsed_items), filename, time.perf_counter() - started,
        )
        logger.debug("OCR: распознанные позиции | file=%s | %s", filename, parsed_items)

    # 3. Ищем кандидатов для каждого распознанного товара
        started = time.perf_counter()
        result_items = []
        matched = 0

        for idx, item in enumerate(parsed_items, start=1):
            candidates = find_product_candidates(
                db=db,
                receipt_item=item,
                limit=3,
            )
            if candidates:
                matched += 1

            logger.debug(
                "OCR: кандидаты | file=%s | #%d '%s' -> %d",
                filename, idx, item.get("name", "?"), len(candidates),
            )

            result_items.append({**item, "candidates": candidates})

        logger.info(
            "OCR: матчинг завершён | file=%s | найдено кандидатов для %d/%d позиций | %.2f c",
            filename, matched, len(parsed_items), time.perf_counter() - started,
        )

         # 4. Возвращаем результат клиенту, ничего не записывая в бд
        logger.info(
            "OCR: готово | file=%s | позиций=%d | итого %.2f c",
            filename, len(result_items), time.perf_counter() - total_started,
        )

        return OCRResponse(
            status=mineru_result.status,
            tier=mineru_result.tier,
            markdown=mineru_result.markdown,
            items=result_items,
        )