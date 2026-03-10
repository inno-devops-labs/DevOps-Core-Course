# Lab 7 — Объяснение: Теория и Практика

## Содержание
1. [Введение в Observability](#1-введение-в-observability)
2. [Loki: Архитектура и Принципы](#2-loki-архитектура-и-принципы)
3. [Promtail: Сборщик Логов](#3-promtail-сборщик-логов)
4. [Grafana: Визуализация](#4-grafana-визуализация)
5. [Structured Logging: Почему JSON?](#5-structured-logging-почему-json)
6. [LogQL: Язык Запросов](#6-logql-язык-запросов)
7. [Docker Compose: Оркестрация](#7-docker-compose-оркестрация)
8. [Production Best Practices](#8-production-best-practices)

---

## 1. Введение в Observability

### Что такое Observability?

**Observability** (наблюдаемость) — это способность понимать внутреннее состояние системы на основе её внешних выходных данных. В DevOps это критически важная концепция, которая включает **три столпа**:

1. **Logs (Логи)** — запись событий, происходящих в системе
2. **Metrics (Метрики)** — числовые измерения состояния системы во времени
3. **Traces (Трейсы)** — отслеживание пути запроса через распределённую систему

```
┌─────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY                            │
├─────────────────┬─────────────────┬─────────────────────────┤
│     LOGS        │    METRICS      │        TRACES           │
│                 │                 │                         │
│  Что произошло? │  Сколько раз?   │  Где это произошло?     │
│  "User login    │  "500 requests  │  "Request A → Service B │
│   failed"       │   per minute"   │   → Database C → ..."   │
│                 │                 │                         │
│  Loki, ELK      │  Prometheus,    │  Jaeger, Zipkin,        │
│                 │  InfluxDB       │  OpenTelemetry          │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### Почему нам нужно централизованное логирование?

В современных распределённых системах приложение может работать на десятках или сотнях контейнеров. Без централизованного логирования:

- 😫 Приходится заходить на каждый сервер отдельно
- 😫 Логи теряются при перезапуске контейнера
- 😫 Невозможно коррелировать события между сервисами
- 😫 Нет поиска по всем логам одновременно

**Centralized Logging** решает все эти проблемы:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Container 1 │    │ Container 2 │    │ Container 3 │
│   logs      │    │   logs      │    │   logs      │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   Log Aggregator      │
              │   (Loki)              │
              │                       │
              │  • Хранит все логи    │
              │  • Индексирует        │
              │  • Позволяет поиск    │
              └───────────────────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   Visualization       │
              │   (Grafana)           │
              │                       │
              │  • Dashboards         │
              │  • Alerts             │
              │  • Explore            │
              └───────────────────────┘
```

---

## 2. Loki: Архитектура и Принципы

### Что такое Grafana Loki?

**Loki** — это горизонтально масштабируемая, высоко-доступная система агрегации логов, разработанная Grafana Labs. Её часто называют "Prometheus для логов", потому что она следует похожей философии.

### Ключевое отличие от Elasticsearch

| Аспект | Elasticsearch | Loki |
|--------|---------------|------|
| **Индексация** | Полнотекстовый индекс всего содержимого | Индексирует только **метки (labels)** |
| **Ресурсы** | Требует много RAM и CPU | Легковесный |
| **Стоимость** | Дорого в эксплуатации | Дёшево |
| **Поиск** | Очень быстрый по любому тексту | Быстрый по меткам, grep по содержимому |

**Почему Loki индексирует только метки?**

```
Традиционный подход (Elasticsearch):
┌─────────────────────────────────────────────────────────────────┐
│ {"timestamp": "2024-01-15T10:30:45", "level": "INFO",           │
│  "message": "User john@example.com logged in from 192.168.1.1"} │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ ПОЛНОТЕКСТОВЫЙ ИНДЕКС:                                          │
│ "timestamp" → doc1, doc5, doc999...                             │
│ "level" → doc1, doc2, doc3...                                   │
│ "INFO" → doc1, doc47, doc88...                                  │
│ "User" → doc1, doc23...                                         │
│ "john" → doc1, doc156...                                        │
│ "example.com" → doc1, doc89...                                  │
│ "logged" → doc1, doc34...                                       │
│ ... (каждое слово индексируется!)                               │
└─────────────────────────────────────────────────────────────────┘
💾 Размер индекса ≈ размер данных (или больше!)
```

```
Подход Loki:
┌─────────────────────────────────────────────────────────────────┐
│ Labels: {app="auth", level="INFO", env="prod"}                  │
│ Log line: User john@example.com logged in from 192.168.1.1      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ ИНДЕКС ТОЛЬКО ПО МЕТКАМ:                                        │
│ {app="auth", level="INFO", env="prod"} → chunk123               │
└─────────────────────────────────────────────────────────────────┘
💾 Индекс очень маленький!
   А содержимое логов хранится сжатым и ищется через grep
```

### Архитектура Loki

```
┌─────────────────────────────────────────────────────────────────────┐
│                         LOKI ARCHITECTURE                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐         │
│  │ Distributor │─────▶│  Ingester   │─────▶│   Storage   │         │
│  │             │      │             │      │             │         │
│  │ Принимает   │      │ Буферизует  │      │ Хранит      │         │
│  │ логи        │      │ в память    │      │ chunks      │         │
│  └─────────────┘      └─────────────┘      └─────────────┘         │
│         ▲                                         │                 │
│         │                                         │                 │
│  Promtail/Agent                                   │                 │
│         │                                         ▼                 │
│         │             ┌─────────────┐      ┌─────────────┐         │
│         │             │   Querier   │◀─────│    Index    │         │
│         │             │             │      │             │         │
│         │             │ Выполняет   │      │ TSDB/BoltDB │         │
│         │             │ запросы     │      │ index       │         │
│         │             └─────────────┘      └─────────────┘         │
│         │                    │                                      │
│         │                    ▼                                      │
│         │             ┌─────────────┐                               │
│         └─────────────│   Grafana   │                               │
│                       │             │                               │
│                       │ Визуализа-  │                               │
│                       │ ция         │                               │
│                       └─────────────┘                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Loki 3.0 и TSDB

**TSDB (Time Series Database)** — новый формат индекса в Loki 3.0, заменивший BoltDB-shipper:

```yaml
# Старый способ (Loki 2.x)
schema_config:
  configs:
    - store: boltdb-shipper  # ← медленнее

# Новый способ (Loki 3.0+)
schema_config:
  configs:
    - store: tsdb            # ← до 10x быстрее!
      schema: v13
```

**Преимущества TSDB:**
- ⚡ До 10x быстрее выполнение запросов
- 💾 Меньше использование памяти
- 📦 Лучшее сжатие данных
- 🔄 Эффективнее работает compactor

### Наша конфигурация Loki (config.yml)

```yaml
# Отключаем multi-tenancy для простоты
auth_enabled: false

# HTTP сервер на порту 3100
server:
  http_listen_port: 3100
  grpc_listen_port: 9096
  log_level: info

# Общие настройки для всех компонентов
common:
  instance_addr: 127.0.0.1
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks    # Где хранить данные
      rules_directory: /loki/rules      # Где хранить правила
  replication_factor: 1                 # Single instance
  ring:
    kvstore:
      store: inmemory                   # Для single-node

# Схема хранения — определяет формат индекса
schema_config:
  configs:
    - from: 2024-01-01      # С какой даты
      store: tsdb           # Тип индекса (новый быстрый)
      object_store: filesystem  # Где хранить chunks
      schema: v13           # Версия схемы
      index:
        prefix: index_
        period: 24h         # Новый индексный файл каждые 24 часа

# Конфигурация TSDB shipper
storage_config:
  tsdb_shipper:
    active_index_directory: /loki/tsdb-index
    cache_location: /loki/tsdb-cache

# Лимиты и retention
limits_config:
  retention_period: 168h     # 7 дней хранения логов
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h
  ingestion_rate_mb: 10      # Макс скорость приёма
  ingestion_burst_size_mb: 20
  max_streams_per_user: 10000
  max_line_size: 256kb       # Макс размер одной строки лога

# Compactor — удаляет старые данные
compactor:
  working_directory: /loki/compactor
  compaction_interval: 10m   # Запуск каждые 10 минут
  retention_enabled: true    # Включить удаление старых логов
  retention_delete_delay: 2h # Задержка перед удалением
  retention_delete_worker_count: 150
  delete_request_store: filesystem
```

### Что такое Chunks и Index?

```
Log Entry:
{app="python", level="INFO"} "User logged in"
   │
   └──────────────────────┐
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                        INDEX                                     │
│  Маленькая структура данных, которая отвечает на вопрос:        │
│  "В каком chunk находятся логи с метками {app=python}?"         │
│                                                                  │
│  {app="python", level="INFO"} → chunk_001, chunk_002, chunk_003 │
│  {app="python", level="ERROR"} → chunk_004                       │
└─────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                        CHUNKS                                    │
│  Сжатые файлы с реальным содержимым логов                       │
│                                                                  │
│  chunk_001: [timestamp1] "User logged in"                        │
│             [timestamp2] "Processing request"                    │
│             [timestamp3] "Request completed"                     │
│             ...                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Promtail: Сборщик Логов

### Что такое Promtail?

**Promtail** — это агент для сбора логов, который:
- Обнаруживает источники логов (файлы, Docker контейнеры, journald)
- Добавляет метки к логам
- Отправляет логи в Loki

### Service Discovery

**Service Discovery** позволяет Promtail автоматически находить новые контейнеры:

```yaml
scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock  # Подключение к Docker
        refresh_interval: 5s                # Проверять каждые 5с
        filters:
          - name: label
            values: ["logging=promtail"]    # Только с этим label
```

**Как это работает:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    Docker Engine                                 │
│                                                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Container A │  │ Container B │  │ Container C │              │
│  │ labels:     │  │ labels:     │  │ labels:     │              │
│  │  logging:   │  │  (none)     │  │  logging:   │              │
│  │  promtail   │  │             │  │  promtail   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│        │                                   │                     │
│        │                                   │                     │
│        └───────────────┬───────────────────┘                     │
│                        │                                         │
│                        ▼                                         │
│  ┌─────────────────────────────────────────────────────┐        │
│  │              Docker Socket                           │        │
│  │              /var/run/docker.sock                    │        │
│  └─────────────────────────────────────────────────────┘        │
│                        │                                         │
└────────────────────────┼─────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Promtail                                    │
│                                                                  │
│  1. Подключается к Docker socket                                 │
│  2. Получает список контейнеров                                  │
│  3. Фильтрует по label "logging=promtail"                        │
│  4. Читает логи из /var/lib/docker/containers/<id>/<id>-json.log│
│  5. Добавляет метки (container name, app, etc.)                  │
│  6. Отправляет в Loki                                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Relabeling: Добавление меток

**Relabeling** — это механизм преобразования меток:

```yaml
relabel_configs:
  # Docker возвращает имя контейнера с "/" в начале
  # Например: __meta_docker_container_name = "/app-python"
  
  - source_labels: ['__meta_docker_container_name']
    regex: '/(.*)'           # Capture group для удаления /
    target_label: 'container'  # Результат: container="app-python"
  
  # Извлечь кастомный label "app" из контейнера
  - source_labels: ['__meta_docker_container_label_app']
    target_label: 'app'      # Если label app="devops-python"
                             # То получим: app="devops-python"
```

**Доступные meta-labels от Docker SD:**

| Meta Label | Описание |
|------------|----------|
| `__meta_docker_container_id` | ID контейнера |
| `__meta_docker_container_name` | Имя контейнера (с /) |
| `__meta_docker_container_label_<name>` | Любой label контейнера |
| `__meta_docker_network_ip` | IP адрес в сети |
| `__meta_docker_port_public` | Публичный порт |

### Pipeline Stages: Обработка логов

**Pipeline** — это последовательность преобразований для каждой строки лога:

```yaml
pipeline_stages:
  # 1. Парсим JSON
  - json:
      expressions:
        level: level         # Извлечь поле "level" из JSON
        message: message     # Извлечь поле "message"
        timestamp: timestamp # Извлечь поле "timestamp"
  
  # 2. Превращаем извлечённые значения в labels
  - labels:
      level:                 # level становится индексируемой меткой
  
  # 3. Используем timestamp из лога (а не время получения)
  - timestamp:
      source: timestamp
      format: RFC3339Nano
```

**Визуализация pipeline:**

```
Входящий лог:
{"timestamp": "2024-01-15T10:30:45Z", "level": "INFO", "message": "Hello"}
       │
       ▼
┌──────────────────┐
│   json stage     │  Извлекает: level="INFO", message="Hello"
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  labels stage    │  Добавляет label: {level="INFO"}
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ timestamp stage  │  Устанавливает timestamp из лога
└────────┬─────────┘
         │
         ▼
Результат в Loki:
Labels: {app="python", level="INFO"}
Timestamp: 2024-01-15T10:30:45Z
Line: {"timestamp": "2024-01-15T10:30:45Z", "level": "INFO", "message": "Hello"}
```

### Positions File

Promtail отслеживает, до какого места он прочитал каждый файл:

```yaml
positions:
  filename: /tmp/positions.yaml
```

Содержимое такого файла:

```yaml
positions:
  /var/lib/docker/containers/abc123.../abc123...-json.log:
    "1234567890"  # Offset в байтах
```

**Зачем это нужно?**
- При перезапуске Promtail продолжит с того места, где остановился
- Не будет дублирования логов
- Не будет потери логов

---

## 4. Grafana: Визуализация

### Что такое Grafana?

**Grafana** — это платформа для визуализации и анализа данных. Она может подключаться к разным источникам данных (Prometheus, Loki, InfluxDB, PostgreSQL и др.) и создавать дашборды.

### Data Source Provisioning

Вместо ручной настройки data source, мы используем **provisioning**:

```yaml
# grafana/provisioning/datasources/loki.yml
apiVersion: 1

datasources:
  - name: Loki                  # Имя источника
    type: loki                  # Тип
    access: proxy               # Grafana проксирует запросы
    url: http://loki:3100       # URL Loki (внутренний в Docker)
    isDefault: true             # Использовать по умолчанию
    editable: true              # Можно редактировать в UI
```

**Почему provisioning лучше ручной настройки?**

| Ручная настройка | Provisioning |
|------------------|--------------|
| Теряется при пересоздании контейнера | Автоматически применяется |
| Невозможно версионировать | Хранится в Git |
| Нужно повторять на каждой среде | Одинаково везде |
| Human error | Infrastructure as Code |

### Dashboard Provisioning

Аналогично, дашборды можно провижонить:

```yaml
# grafana/provisioning/dashboards/dashboard.yml
apiVersion: 1

providers:
  - name: 'default'
    folder: ''
    type: file
    options:
      path: /etc/grafana/provisioning/dashboards
```

Grafana автоматически загрузит JSON файлы дашбордов из этой директории.

### Панели Dashboard

**1. Logs Panel (Таблица логов)**
```logql
{app=~"devops-.*"}
```
Показывает сырые логи с возможностью раскрытия деталей.

**2. Time Series (График)**
```logql
sum by (app) (rate({app=~"devops-.*"} [1m]))
```
Показывает количество логов в секунду.

**3. Pie Chart (Круговая диаграмма)**
```logql
sum by (level) (count_over_time({app=~"devops-.*"} | json [5m]))
```
Показывает распределение по уровням логирования.

---

## 5. Structured Logging: Почему JSON?

### Проблема текстовых логов

```
# Текстовые логи — плохо для машинной обработки
2024-01-15 10:30:45 INFO User john logged in from 192.168.1.1
2024-01-15 10:30:46 ERROR Failed to process request: timeout

# Как извлечь информацию?
# - Нужны сложные regex
# - Разные форматы в разных приложениях
# - Легко сломать парсер
```

### Решение: Structured Logging (JSON)

```json
{
  "timestamp": "2024-01-15T10:30:45Z",
  "level": "INFO",
  "message": "User logged in",
  "user": "john",
  "ip": "192.168.1.1",
  "method": "POST",
  "path": "/login"
}
```

**Преимущества:**
- ✅ Все поля явно названы
- ✅ Машиночитаемый формат
- ✅ Легко парсить и фильтровать
- ✅ Стандартизация между приложениями
- ✅ LogQL может извлекать поля: `| json | user="john"`

### Реализация в Python

```python
class JSONFormatter(logging.Formatter):
    """Кастомный форматтер для вывода логов в JSON"""
    
    def format(self, record):
        # Собираем базовую информацию о логе
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,      # INFO, ERROR, etc.
            "logger": record.name,          # Имя логгера
            "message": record.getMessage(), # Текст сообщения
            "module": record.module,        # Имя модуля
            "function": record.funcName,    # Имя функции
            "line": record.lineno,          # Номер строки
        }
        
        # Добавляем exception если есть
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Добавляем кастомные поля
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)
        
        return json.dumps(log_data)
```

**Как добавить контекст к логу:**

```python
def log_request(request, message, **extra):
    """Логирует запрос с контекстом"""
    log_data = {
        "method": request.method,
        "path": str(request.url.path),
        "client_ip": request.client.host,
        "user_agent": request.headers.get("user-agent"),
        **extra,  # Дополнительные поля
    }
    
    record = logging.LogRecord(...)
    record.extra_data = log_data
    logger.handle(record)

# Использование:
log_request(request, "Request processed", status_code=200, duration_ms=45)
```

---

## 6. LogQL: Язык Запросов

### Структура запроса LogQL

```
{labels} | line_filters | parsers | label_filters | aggregations

Примеры:
{app="python"}                         # Только выбор по меткам
{app="python"} |= "error"              # + фильтр по тексту
{app="python"} | json                  # + парсинг JSON
{app="python"} | json | level="ERROR"  # + фильтр по полю
rate({app="python"}[1m])               # + агрегация
```

### 1. Stream Selectors (Выбор потоков)

```logql
# Точное совпадение
{app="python"}

# Не равно
{app!="python"}

# Regex совпадение
{app=~"python|golang"}

# Regex не совпадает
{app!~"test.*"}

# Несколько условий (AND)
{app="python", env="prod"}
```

### 2. Line Filters (Фильтры строк)

```logql
# Содержит текст
{app="python"} |= "error"

# НЕ содержит
{app="python"} != "debug"

# Regex совпадение
{app="python"} |~ "error|fail|crash"

# Regex НЕ совпадает
{app="python"} !~ "health|ready"
```

### 3. Parsers (Парсеры)

```logql
# JSON парсер — извлекает все поля из JSON
{app="python"} | json

# Выбрать конкретные поля
{app="python"} | json level, message

# logfmt парсер (для формата key=value)
{app="nginx"} | logfmt

# regexp парсер (кастомный regex)
{app="python"} | regexp `status=(?P<status>\d+)`

# pattern парсер (простой шаблон)
{app="nginx"} | pattern `<ip> - - [<timestamp>] "<method> <path>"`
```

### 4. Label Filters (Фильтры меток)

После парсинга можно фильтровать по извлечённым полям:

```logql
# Точное совпадение
{app="python"} | json | level="ERROR"

# Числовое сравнение
{app="python"} | json | status_code >= 400

# Regex на извлечённом поле
{app="python"} | json | message =~ ".*timeout.*"
```

### 5. Aggregations (Агрегации)

**Log Range Aggregations:**

```logql
# Количество логов за период
count_over_time({app="python"}[5m])

# Скорость логов (в секунду)
rate({app="python"}[1m])

# Байтов в секунду
bytes_rate({app="python"}[1m])

# Отсутствие логов (для alerting)
absent_over_time({app="python"}[5m])
```

**Aggregation Operators:**

```logql
# Сумма по метке
sum by (level) (count_over_time({app="python"} | json [5m]))

# Максимум
max(rate({app="python"}[1m]))

# Среднее
avg by (app) (rate({job="docker"}[5m]))

# Top-K
topk(5, count_over_time({job="docker"}[1h]))
```

### Практические примеры

```logql
# 1. Все ошибки за последний час
{app="python"} | json | level="ERROR"

# 2. Запросы с кодом 5xx
{app="python"} | json | status_code >= 500

# 3. Медленные запросы (> 1 секунды)
{app="python"} | json | duration_ms > 1000

# 4. Количество ошибок по уровням
sum by (level) (count_over_time({app="python"} | json | level=~"ERROR|WARNING" [5m]))

# 5. Rate ошибок (для alerting)
sum(rate({app="python"} | json | level="ERROR" [5m]))

# 6. Поиск конкретного пользователя
{app="python"} | json | user="john@example.com"

# 7. Все 404 ошибки
{app="python"} |= "404" | json | status_code=404
```

---

## 7. Docker Compose: Оркестрация

### Почему Docker Compose?

Docker Compose позволяет:
- 📦 Определить все сервисы в одном файле
- 🔗 Создать изолированную сеть для сервисов
- 💾 Управлять volumes для persistent storage
- 🔄 Запускать/останавливать всё одной командой

### Структура нашего docker-compose.yml

```yaml
services:
  # 1. Loki — хранение логов
  loki:
    image: grafana/loki:3.0.0
    ports:
      - "3100:3100"              # Expose HTTP API
    volumes:
      - ./loki/config.yml:/etc/loki/config.yml:ro  # Config (read-only)
      - loki-data:/loki                             # Persistent data
    command: -config.file=/etc/loki/config.yml
    networks:
      - logging                  # Внутренняя сеть
    healthcheck:                 # Проверка здоровья
      test: ["CMD-SHELL", "wget --spider http://localhost:3100/ready"]
      interval: 10s
      retries: 5
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G

  # 2. Promtail — сбор логов
  promtail:
    image: grafana/promtail:3.0.0
    volumes:
      - ./promtail/config.yml:/etc/promtail/config.yml:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro  # Docker logs
      - /var/run/docker.sock:/var/run/docker.sock:ro              # Docker API
    depends_on:
      loki:
        condition: service_healthy  # Ждём пока Loki готов

  # 3. Grafana — визуализация
  grafana:
    image: grafana/grafana:12.3.1
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana              # Persistent data
      - ./grafana/provisioning:/etc/grafana/provisioning:ro  # Auto-config
    environment:
      - GF_AUTH_ANONYMOUS_ENABLED=false            # Требуем логин
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}

  # 4. Application — наше приложение
  app-python:
    build:
      context: ../app_python
    ports:
      - "8080:8080"
    labels:
      logging: "promtail"        # Promtail подберёт этот контейнер
      app: "devops-python"       # Метка для LogQL
    environment:
      - LOG_FORMAT=json          # Включаем JSON логи

networks:
  logging:
    driver: bridge

volumes:
  loki-data:
  grafana-data:
```

### Важные концепции

**1. Named Networks:**
```yaml
networks:
  logging:
    driver: bridge
```
- Контейнеры могут обращаться друг к другу по имени (например, `http://loki:3100`)
- Изоляция от других Docker сетей

**2. Named Volumes:**
```yaml
volumes:
  loki-data:
  grafana-data:
```
- Данные сохраняются даже после `docker compose down`
- Удаляются только при `docker compose down -v`

**3. Depends On с Condition:**
```yaml
depends_on:
  loki:
    condition: service_healthy
```
- Promtail не запустится, пока Loki не пройдёт healthcheck
- Предотвращает ошибки при старте

**4. Environment Variables из .env:**
```yaml
environment:
  - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
```
- Docker Compose автоматически читает `.env` файл
- Секреты не хранятся в коде

---

## 8. Production Best Practices

### 1. Resource Limits

**Зачем нужны лимиты?**
- Предотвращают "утечку" ресурсов одним сервисом
- OOM killer не убьёт случайный контейнер
- Предсказуемая производительность

```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'    # Макс 1 CPU ядро
      memory: 1G     # Макс 1GB RAM
    reservations:
      cpus: '0.25'   # Гарантированно получит 25% CPU
      memory: 256M   # Гарантированно получит 256MB RAM
```

### 2. Health Checks

**Зачем нужны healthcheck?**
- Docker знает, когда сервис реально готов
- `depends_on: condition: service_healthy` работает
- Kubernetes может использовать для restart

```yaml
healthcheck:
  test: ["CMD-SHELL", "wget --spider http://localhost:3100/ready"]
  interval: 10s         # Проверять каждые 10 секунд
  timeout: 5s           # Таймаут проверки
  retries: 5            # Сколько раз попробовать
  start_period: 20s     # Grace period при старте
```

### 3. Security

**Grafana Security:**
```yaml
environment:
  - GF_AUTH_ANONYMOUS_ENABLED=false  # Требовать аутентификацию
  - GF_USERS_ALLOW_SIGN_UP=false     # Запретить регистрацию
  - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}  # Из .env
```

**Docker Socket Security:**
```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock:ro  # Read-only!
```
⚠️ Docker socket даёт полный контроль над Docker — монтировать только read-only!

**Secrets в .env:**
```bash
# .env
GRAFANA_ADMIN_PASSWORD=MySecurePassword123!

# .gitignore
.env  # Никогда не коммитить!
```

### 4. Retention Policy

**Зачем удалять старые логи?**
- Экономия места на диске
- Соответствие требованиям (GDPR и др.)
- Производительность запросов

```yaml
# loki/config.yml
limits_config:
  retention_period: 168h  # 7 дней

compactor:
  retention_enabled: true
  retention_delete_delay: 2h  # Не удалять сразу
  compaction_interval: 10m    # Проверять каждые 10 минут
```

### 5. Restart Policy

```yaml
restart: unless-stopped
```
- Контейнер перезапустится при падении
- Но не перезапустится если его остановили вручную

---

## Заключение

В этой лабораторной работе мы:

1. **Развернули Loki Stack** — современную систему централизованного логирования
2. **Настроили Promtail** с Docker Service Discovery для автоматического сбора логов
3. **Реализовали Structured Logging** в Python с JSON форматом
4. **Создали Dashboard** в Grafana с несколькими типами визуализации
5. **Применили Production Best Practices** — ресурсные лимиты, healthchecks, security

### Ключевые концепции

| Концепция | Что это | Зачем нужно |
|-----------|---------|-------------|
| **Observability** | Три столпа: логи, метрики, трейсы | Понимать состояние системы |
| **Loki** | Log aggregation система | Хранить и искать логи |
| **TSDB** | Time Series Database индекс | Быстрые запросы |
| **Promtail** | Log collector | Собирать логи из контейнеров |
| **Service Discovery** | Автообнаружение | Не нужно ручная настройка |
| **LogQL** | Язык запросов Loki | Поиск и агрегация логов |
| **Structured Logging** | JSON формат логов | Машиночитаемые логи |
| **Provisioning** | Автоконфигурация | Infrastructure as Code |

### Что дальше?

- **Lab 8:** Добавим **метрики** с Prometheus — второй столп observability
- **Lab 9-12:** Перенесём всё в **Kubernetes**
- **Lab 16:** Полная observability в Kubernetes

---

*Документ создан для Lab 7 — Observability & Logging with Loki Stack*
