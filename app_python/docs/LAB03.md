# LAB03 — Continuous Integration (CI/CD)

## Task 1 — Unit Testing

### Testing Framework Selection
**Choice:** `pytest`

**Why pytest:**
- **Simple syntax**: readable tests with minimal boilerplate.
- **Great ecosystem**: fixtures (`client`), monkeypatching, plugins.
- **Works well with Flask**: integrates cleanly with Flask’s built-in test client.

### Test Structure
- Tests are located in `app_python/tests/`
- Main test file: `app_python/tests/test_endpoints.py`
- Covered cases:
  - `GET /` — JSON structure and required fields
  - `GET /health` — health response fields
  - `404` — JSON error response for unknown endpoint
  - `500` — JSON error response on internal exception

### How to Run Tests Locally
Install dev dependencies:

```bash
pip install -r requirements-dev.txt
```

Run tests:

```bash
pytest
```

### Pytest Output (Proof)

```text
MojPK@MacBook-Pro-168 app_python % pytest
========================================================== test session starts ===========================================================
platform darwin -- Python 3.13.1, pytest-8.3.4, pluggy-1.6.0
rootdir: /Users/MojPK/Downloads/University/DevOps/DevOps-Core-Course/app_python
plugins: anyio-4.9.0
collected 4 items

tests/test_endpoints.py ....                                                                                                       [100%]

=========================================================== 4 passed in 0.08s ============================================================
```

### Screenshot

![Pytest output](screenshots/04-pytest-output.png)

---

## Task 2 — GitHub Actions CI Workflow

### Workflow Overview
- **Workflow name:** `Python CI (app_python)`
- **Location:** `.github/workflows/python-ci.yml`
- **What it does:**
  - On every change in `app_python/**` (any branch):
    - install dev dependencies
    - run `ruff check .`
    - run `pytest`
  - On `push` в `master`/`main`:
    - собирает Docker-образ для Python-приложения
    - пушит его в Docker Hub с CalVer-тегами

### Triggers (when CI runs)
- **`push`** на любую ветку (`branches: "**"`) при изменениях:
  - в `app_python/**`
  - или в `.github/workflows/python-ci.yml`
- **`pull_request`** на любую ветку (`branches: "**"`) при тех же путях.

**Причём:**
- job **`test`** (lint + pytest) запускается на **любой ветке**.
- job **`docker`** (build & push) запускается **только на `push` в `master` или `main`**:
  - защищает от случайного пуша образов из feature-веток.

### Actions Used and Why
- **`actions/checkout@v4`** — стандарт для выкачивания кода в CI.
- **`actions/setup-python@v5`** — гарантирует нужную версию Python (`3.11`) независимо от runner’а.
- **`docker/setup-buildx-action@v3`** — готовит окружение для современных Docker build’ов.
- **`docker/login-action@v3`** — безопасный логин в Docker Hub через `DOCKERHUB_USERNAME` и `DOCKERHUB_TOKEN`.
- **`docker/build-push-action@v6`** — единый шаг “build + push” с несколькими тегами.

### Versioning Strategy (CalVer)
Я выбрала **Calendar Versioning (CalVer)**, потому что:
- он хорошо показывает **дату релиза**;
- удобно видеть, какие релизы были в одном месяце;
- хорошо подходит для **частых CI/CD релизов** без ручного bump’а SemVer.

В job `docker` вычисляются 2 тега на основе текущей даты в UTC:
- `YYYY.MM.DD` — полный “дневной” релиз, например `2026.02.10`
- `YYYY.MM` — релизы за месяц, например `2026.02`

К ним добавляется ещё тег:
- `latest`

**Итоговые теги образа в Docker Hub:**
- `${DOCKERHUB_USERNAME}/devops-info-service:YYYY.MM.DD`
- `${DOCKERHUB_USERNAME}/devops-info-service:YYYY.MM`
- `${DOCKERHUB_USERNAME}/devops-info-service:latest`

### Proof (CI Run)
- Вкладка **Actions** в GitHub показывает успешный прогон workflow `Python CI (app_python)` для ветки `lab03` (зелёный чек-марк).
- Скриншот/ссылка на успешный run можно вставить сюда:

> _[вставить скрин экрана/ссылку на успешный workflow run]_ 

