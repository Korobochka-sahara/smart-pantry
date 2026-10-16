Запуск теста:
pytest -s ml/tests/ocr/test_receipt_parser.py

Запуск мануального теста (ручного, посмотреть вывод парсера):
python ml/tests/ocr/test_parser_manual.py "ml/tests/ocr/fixtures/receipt_$номер$_standard_response.json"