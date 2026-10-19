# MinerU results

JSON-файлы CLI MinerU для разных чеков и режимов (`standard`, `basic`, `flash`). Создание нового результата из корня репозитория:

```powershell
mineru parse ml/test_images/receipt_01.jpg --tier standard --json --output ml/results/mineru/receipt_01_standard.json --wait 600
```

Перед запуском проверь, что текущая версия MinerU поддерживает указанный tier и настроена на нужный backend. Сохраняй режим в имени файла.
