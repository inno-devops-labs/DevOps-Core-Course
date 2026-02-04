# LAB02 — Docker Containerization

## Docker Best Practices Applied

### Non-root user

Создан пользователь `appuser` и использован с помощью директивы `USER appuser`. Это повышает безопасность контейнера, так как приложение работает не от root и снижает риски при взломе.

```dockerfile
RUN useradd --create-home --shell /bin/bash appuser
USER appuser
```

### Layer caching

Отдельно копируются `requirements.txt` и устанавливаются зависимости, а затем копируется остальной код. Это ускоряет сборку при изменении только кода, без повторной установки пакетов.

```
COPY requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash appuser \
    && pip install --no-cache-dir -r requirements.txt

COPY app.py .
```

### .dockerignore

В файле `.dockerignore` исключены временные файлы, кэш и ненужные папки, чтобы не передавать их в контекст сборки. Это снижает размер образа и ускоряет сборку.

### Specific base image version

Использован `python:3.12-slim` — оптимальный баланс между размером и функционалом.

### Proper layer ordering

Сначала копируются зависимости, затем основной код, что позволяет использовать кеш слоев эффективно и повышает скорость сборки и уменьшает итоговый размер контейнера.

## Image Information & Decisions

### Base image: `python:3.12-slim`

Выбран из-за баланса между легковесностью и совместимостью. Slim-версия меньше стандартного образа, но содержит нужные библиотеки.

### Final image size

Размер в ~160 Мб оптимален для Python-приложения с зависимостями.

### Layer structure:

1. Установка зависимостей
2. Копирование кода
3. Создание пользователя
4. Переключение на непользовательского пользователя
5. Запуск приложения

### Optimization choices:

- Использование --no-cache-dir при установке pip-зависимостей
- Отдельное копирование requirements.txt для кэширования
- Использование slim-базы

#### Reasons:

- Для работы python
- Для ускорения постройки контейнера
- Легкая настройки и оптимальный вес

## Build & Run Process

###Сборка образа

```
docker build -t app_python:lab02 .
```

```
... [вывод сборки] ...
[+] Building 27.1s (11/11) FINISHED                                                                                                            docker:desktop-linux
```

### Запуск контейнера

```
docker run -p 5000:5000 app_python:lab02
```

(Вывод)

```
INFO:     Started server process [1]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
INFO:     172.17.0.1:44156 - "GET / HTTP/1.1" 200 OK
```

### Тестирование эндпоинтов

```
curl http://localhost:5000
```

(Вывод)

```
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"30d261be1b68","platform":"Linux","architecture":"x86_64","cpu_count":16,"python_version":"3.12.12"},"runtime":{"uptime_seconds":10,"uptime_human":"0 hours, 0 minutes","current_time":"2026-02-04T19:50:44.709090+00:00","timezone":"UTC"},"request":{"client_ip":"172.17.0.1","user_agent":"curl/8.13.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}
```

`/health` тоже работает

### Technical Analysis

##### Всё это есть в лекции и/или очевидно, я не могу передать прочитанность лекции как-либо адекватно.

Dockerfile работает благодаря правильной структуре слоев и безопасности, включая запуск от некорневого пользователя.

Если поменять порядок слоев (например, сначала копировать весь код, а потом зависимости), кеширование будет менее эффективным, и сборка займет больше времени.

Реализована базовая безопасность через смену пользователя на не-root-пользователя, что снижает риски взлома.

`.dockerignore` уменьшает размер контекста и ускоряет сборку, исключая ненужные файлы.

### Challenges & Solutions

Проблема: Ошибки с запуском команд Docker из-за отсутствия Docker Desktop и неправильных настроек WSL.
Решение: Установил WSL, активировал интеграцию с Docker Desktop, перезапустил сервис.

При работе с тегами Docker иногда сталкивался с конфликтами, решил через удаление старых образов и контейнеров.

Был напрасно обеспокоен безопасностью использования имени docker hub'а в тэге. Решил, повторив всё несколько раз.

Настройка не-root-пользователя помогла понять важность безопасности в контейнерах, но я думал, что может потребоваться что-то ещё, но это вне рамок этой лабораторной.
Решил перечитывание критериев и лекции.

Научился правильно(надеюсь) структурировать Dockerfile для ускорения сборки и уменьшения размера образа.
Корректность решения будет известно после получения оценки.

Результат: Узнал, как создавать безопасные, оптимизированные образы, работать с Docker Hub и понимать внутренние механизмы сборки(надеюсь).

### Docker Hub URL

https://hub.docker.com/r/sfedbro/app_python
