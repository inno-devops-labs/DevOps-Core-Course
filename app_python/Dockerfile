# app_python/Dockerfile

# ========== STAGE 1: Builder ==========
FROM python:3.13-slim AS builder

# Устанавливаем системные зависимости только для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Создаем и активируем виртуальное окружение
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ========== STAGE 2: Runtime ==========
FROM python:3.13-slim

# Метаданные образа
LABEL maintainer="DevOps Team"
LABEL version="1.0.0"
LABEL description="DevOps Info Service"

# Устанавливаем системные зависимости (минимальные)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создаем не-root пользователя
RUN useradd -m -u 1000 -s /bin/bash appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

# Копируем виртуальное окружение из builder stage
COPY --from=builder --chown=appuser:appuser /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Рабочая директория
WORKDIR /app

# Копируем только необходимые файлы приложения
COPY --chown=appuser:appuser app.py /app/
COPY --chown=appuser:appuser requirements.txt /app/

# Переключаемся на не-root пользователя
USER appuser

# Открываем порт приложения
EXPOSE 5000

# Переменные окружения по умолчанию
ENV HOST=0.0.0.0
ENV PORT=5000
ENV DEBUG=false
ENV LOG_LEVEL=info
ENV SERVICE_NAME=devops-info-service
ENV SERVICE_VERSION=1.0.0

# Проверяем здоровье контейнера
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Команда запуска
CMD ["python", "app.py"]