# ML tests

Тесты проверяют функции подготовки текста MinerU и структурирование чека через Qwen. Они не запускают полный OCR на реальном изображении: используются JSON-фикстуры из `fixtures/`.

## Подготовка

Активируй ML-окружение, установи `ml/requirements.txt`. Для `test_receipt_parser_llm.py` запусти Ollama и загрузи модель:

```powershell
ollama pull qwen2.5:7b-instruct
```

## Запуск из корня репозитория

```powershell
python -m pytest ml/tests -v
python -m pytest ml/tests/test_clean_mineru.py -v
python -m pytest ml/tests/test_receipt_parser_llm.py -v
```

Можно запустить как модуль:

```powershell
python -m ml.tests.test_clean_mineru
python -m ml.tests.test_receipt_parser_llm
```

`test_clean_mineru.py` проверяет очистку HTML/Base64 из результата MinerU. `test_receipt_parser_llm.py` вызывает LLM и проверяет базовую структуру ответа. Из-за LLM результат зависит от доступности Ollama и конкретной модели; для CI лучше дополнительно сделать unit-тесты с mock без обращения к модели.
