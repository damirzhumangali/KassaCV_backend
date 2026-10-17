# KassaCV Backend

Сервис локального компьютерного зрения и анализа видеопотока кассовой зоны для выявления нарушений кассовой дисциплины.

## Архитектура проекта

```
KassaCV_backend/
├── app/
│   ├── main.py               # создание FastAPI, роуты, middleware
│   ├── config.py             # настройки из env
│   ├── auth.py               # проверка X-API-Key (constant-time)
│   ├── api/
│   │   ├── analyze.py        # POST /api/v1/analyze
│   │   ├── jobs.py           # GET /api/v1/jobs/{id}
│   │   └── health.py         # GET /health
│   ├── db.py                 # SQLite, модель Job
│   ├── storage.py            # временные файлы, TTL, удаление
│   ├── worker.py             # цикл воркера, дедлайн, обработка падений
│   ├── worker_process.py     # запуск воркера как отдельного процесса
│   ├── schemas.py            # Pydantic-модели ответа
│   ├── pipeline/
│   │   ├── ingest.py         # ffprobe, проверка, нормализация видео
│   │   ├── sampling.py       # выборка кадров
│   │   ├── detectors.py      # детекторы объектов и поз
│   │   ├── tracking.py       # трекинг, роли, зоны
│   │   ├── events.py         # правила-автоматы по времени
│   │   ├── vlm.py            # проверка и описание кадров
│   │   ├── aggregate.py      # слияние событий, вердикт
│   │   ├── evidence.py       # выбор кадров, рамки, JPEG, base64
│   │   └── runner.py         # оркестрация этапов + бюджет времени
│   └── rules/
│       ├── rules_catalog.json
│       └── catalog.py        # загрузка и валидация каталога
├── models/                   # локальные веса моделей (YOLO / VLM)
├── tests/                    # юнит и контрактные тесты
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Быстрый старт

### Локальный запуск (Python 3.11+)

1. Установите зависимости:
```sh
pip install -r requirements.txt
```

2. Запустите сервис:
```sh
export API_KEYS="secret_test_key"
export DATA_DIR="$PWD/data"
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Запуск в Docker Compose

```sh
API_KEYS="secret_test_key" docker compose up --build
```

## API Эндпоинты

- `GET /health` — публичный мониторинг состояния сервиса.
- `POST /api/v1/analyze` — загрузка видео на анализ (`multipart/form-data`, поле `file`). Требует заголовок `X-API-Key`. Возвращает `{"job_id": "..."}` со статусом 202.
- `GET /api/v1/jobs/{job_id}` — получение статуса и результатов анализа (`processing`, `failed`, `done`). Требует заголовок `X-API-Key`.
