# ml/ocr_service/mineru_service.py

import asyncio
import logging
from pathlib import Path

from mineru.parser import parse


logger = logging.getLogger(__name__)


class MinerUService:
    def __init__(self, tier: str = "standard"):
        self.tier = tier

    def _parse_sync(self, image_path: Path) -> str:
        logger.info(
            "Начинаем обработку файла: %s",
            image_path,
        )

        if not image_path.is_file():
            raise FileNotFoundError(
                f"Файл не найден: {image_path}"
            )

        try:
            result = parse(
                str(image_path.resolve()),
                tier=self.tier,
            )

            markdown = result.markdown()

            if not isinstance(markdown, str):
                raise TypeError(
                    "MinerU вернул Markdown не в виде строки."
                )

            if not markdown.strip():
                raise ValueError(
                    "MinerU вернул пустой Markdown."
                )

            logger.info(
                "Обработка завершена: %s",
                image_path.name,
            )

            return markdown

        except Exception:
            logger.exception(
                "Ошибка при обработке файла %s",
                image_path,
            )
            raise

    async def parse(self, image_path: Path) -> str:
        return await asyncio.to_thread(
            self._parse_sync,
            image_path,
        )