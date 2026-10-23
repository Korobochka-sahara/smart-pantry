$ErrorActionPreference = "Stop"

# Корень репозитория: папка на уровень выше backend
$projectRoot = Split-Path -Parent $PSScriptRoot

# Добавляем корень проекта и backend в пути поиска Python
$env:PYTHONPATH = "$projectRoot;$PSScriptRoot"

# Переходим в папку backend
Set-Location $PSScriptRoot

# Запускаем FastAPI
python -m uvicorn app.main:app --reload