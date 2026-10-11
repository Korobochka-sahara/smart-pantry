Как тестировать модели:

EasyOCR:
python .\ml\ocr\easyocr_test.py

PaddleOCR:
python .\ml\ocr\paddleocr_test.py

MinerU:
Убедиться, что верные настройки(для standart модели)

mineru config show

'''
...
parse_server.local.managed_tier = standard
parse_server.local.mode = managed
...
'''

mineru server start

mineru parse ml/test_images/название_фото.jpg --tier standard --json --output ml/results/mineru/ваше_название_результата.json --wait 300

Для остальных моделей (basic, flash) заменить на:
mineru parse ml/test_images/название_фото.jpg --tier **basic/flash (выбор)** --json --output ml/results/mineru/ваше_название_результата.json --wait 300