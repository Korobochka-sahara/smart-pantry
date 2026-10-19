# OCR experiments

Скрипты сравнивают OCR-инструменты на изображениях из `ml/test_images/` и сохраняют ответы в `ml/results/`.

## EasyOCR

Из корня репозитория с активным ML-окружением:

```powershell
python ml/ocr/easyocr_test.py
```

Скрипт читает `receipt_01.jpg`, использует языки `ru` и `en`, запускается в CPU-режиме и пишет `ml/results/easyocr/easyocr_receipt_01.json`.

## PaddleOCR

```powershell
python ml/ocr/paddleocr_test.py
```

Используется русский язык и CPU-режим. Результат сохраняется в `ml/results/paddleocr/paddleocr_receipt_01.json`.

## MinerU CLI

Убедись, что MinerU установлен в активном ML-окружении и его конфигурация/модели доступны. Проверь настройки:

```powershell
mineru config show
```

Для ручного разбора:

```powershell
mineru parse ml/test_images/receipt_01.jpg --tier standard --json --output ml/results/mineru/receipt_01_standard.json --wait 600
```

Вместо `standard` можно проверить поддерживаемые локальной версией режимы, например `basic` или `flash`, если они доступны в текущей конфигурации. Не сравнивай результаты без фиксации версии, tier, времени обработки и критериев качества.

## Добавление эксперимента

1. Используй фиксированное изображение из `test_images/` или добавь новый образец.
2. Сохрани JSON в соответствующую папку `results/<engine>/`.
3. Укажи в имени файла изображение и режим.
4. Запиши время, версию модели/пакета и заметки о качестве в описании эксперимента.
