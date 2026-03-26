# Kubernetes Deployment - DevOps Python App

## Architecture Overview

Данное развертывание состоит из следующих компонентов:

```
┌─────────────────────────────────────┐
│           Kubernetes Cluster        │
│                                     │
│  ┌─────────────────────────────────┐│
│  │         Service                 ││
│  │    (NodePort: 30080)           ││
│  │                                 ││
│  │  ┌─────────────────────────────┐││
│  │  │       Deployment            │││
│  │  │     (3 replicas)            │││
│  │  │                             │││
│  │  │  ┌─────┐ ┌─────┐ ┌─────┐   │││
│  │  │  │Pod 1│ │Pod 2│ │Pod 3│   │││
│  │  │  │8000 │ │8000 │ │8000 │   │││
│  │  │  └─────┘ └─────┘ └─────┘   │││
│  │  └─────────────────────────────┘││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
```

### Компоненты:

- **3 Pod'а** с Python FastAPI приложением
- **1 Service** типа NodePort для внешнего доступа
- **1 Deployment** для управления Pod'ами
- **Health checks** для liveness и readiness проверок
- **Resource limits** для контроля ресурсов

## Manifest Files

### 1. deployment.yml

**Основные конфигурации:**

- **Replicas**: 3 - обеспечивает высокую доступность
- **Rolling Update Strategy**: 
  - `maxSurge: 1` - максимум 1 дополнительный Pod во время обновления
  - `maxUnavailable: 0` - гарантирует zero-downtime deployment
- **Resource Limits**:
  - Requests: 128Mi RAM, 100m CPU (0.1 core)
  - Limits: 256Mi RAM, 200m CPU (0.2 core)
- **Health Checks**:
  - Liveness Probe: проверяет `/health` каждые 10 секунд
  - Readiness Probe: проверяет `/health` каждые 5 секунд
- **Security Context**: non-root пользователь, минимальные привилегии

### 2. service.yml

**Конфигурация Service:**

- **Type**: NodePort - позволяет доступ извне кластера
- **Port Mapping**: 
  - Service Port: 80
  - Target Port: 8000 (порт контейнера)
  - Node Port: 30080 (внешний порт)
- **Selector**: `app: devops-python-app` - связывает с Pod'ами

## Deployment Commands

### Предварительные требования

1. Установить kubectl:
```bash
# macOS
brew install kubectl

# Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
```

2. Установить локальный кластер (minikube или kind):
```bash
# minikube
brew install minikube
minikube start

# или kind
brew install kind
kind create cluster
```

### Развертывание приложения

1. **Применить манифесты:**
```bash
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
```

2. **Проверить статус развертывания:**
```bash
kubectl get deployments
kubectl get pods
kubectl get services
```

3. **Получить доступ к приложению:**
```bash
# Для minikube
minikube service devops-python-app-service

# Для других кластеров
kubectl port-forward service/devops-python-app-service 8080:80
```

## Operations Performed

### Scaling Operations

**Масштабирование до 5 реплик:**
```bash
# Декларативный подход (рекомендуется)
# Изменить replicas: 5 в deployment.yml, затем:
kubectl apply -f k8s/deployment.yml

# Императивный подход (для быстрого тестирования)
kubectl scale deployment/devops-python-app --replicas=5
```

**Мониторинг масштабирования:**
```bash
kubectl get pods -w
kubectl rollout status deployment/devops-python-app
```

### Rolling Updates

**Обновление образа:**
```bash
# Изменить image tag в deployment.yml, затем:
kubectl apply -f k8s/deployment.yml

# Или императивно:
kubectl set image deployment/devops-python-app devops-python-app=your-username/devops-python-app:v2.0.0
```

**Мониторинг обновления:**
```bash
kubectl rollout status deployment/devops-python-app
kubectl rollout history deployment/devops-python-app
```

**Откат изменений:**
```bash
kubectl rollout undo deployment/devops-python-app
kubectl rollout undo deployment/devops-python-app --to-revision=1
```

### Service Access and Verification

**Проверка доступности:**
```bash
# Получить URL сервиса (minikube)
minikube service devops-python-app-service --url

# Тестирование эндпоинтов
curl http://<service-url>/
curl http://<service-url>/health
curl http://<service-url>/metrics
```

**Проверка endpoints:**
```bash
kubectl get endpoints
kubectl describe service devops-python-app-service
```

## Production Considerations

### Health Checks Implementation

**Liveness Probe:**
- Проверяет, жив ли контейнер
- При неудаче Kubernetes перезапускает Pod
- Использует `/health` endpoint нашего приложения
- Настройки: 10s задержка, проверка каждые 10s, таймаут 5s

**Readiness Probe:**
- Проверяет, готов ли контейнер принимать трафик
- При неудаче Pod исключается из Service endpoints
- Более частые проверки (каждые 5s) для быстрого реагирования

### Resource Limits Rationale

**Requests (гарантированные ресурсы):**
- CPU: 100m (0.1 core) - минимум для Python FastAPI
- Memory: 128Mi - базовое потребление приложения

**Limits (максимальные ресурсы):**
- CPU: 200m (0.2 core) - предотвращает CPU throttling
- Memory: 256Mi - защита от memory leaks

### Production Improvements

1. **Secrets Management:**
   - Использовать Kubernetes Secrets для чувствительных данных
   - Интеграция с внешними системами (Vault, AWS Secrets Manager)

2. **ConfigMaps:**
   - Вынести конфигурацию в ConfigMaps
   - Разделение конфигурации по окружениям

3. **Ingress:**
   - Добавить Ingress Controller для HTTP/HTTPS routing
   - SSL/TLS termination

4. **Monitoring:**
   - Prometheus для сбора метрик
   - Grafana для визуализации
   - Alertmanager для уведомлений

5. **Logging:**
   - Centralized logging (ELK stack, Fluentd)
   - Structured logging (уже реализовано в приложении)

6. **Security:**
   - Network Policies для сетевой изоляции
   - Pod Security Standards
   - Image scanning

7. **Backup & Disaster Recovery:**
   - Регулярные бэкапы конфигураций
   - Multi-region deployment

### Monitoring and Observability Strategy

1. **Metrics Collection:**
   - Приложение уже экспортирует Prometheus метрики на `/metrics`
   - Kubernetes metrics через kube-state-metrics
   - Node metrics через node-exporter

2. **Health Monitoring:**
   - Kubernetes health checks (liveness/readiness)
   - Application-level health checks
   - Dependency health checks

3. **Logging Strategy:**
   - Structured JSON logging (уже реализовано)
   - Log aggregation с помощью Fluentd/Fluent Bit
   - Centralized log storage (Elasticsearch)

4. **Alerting:**
   - Pod restart alerts
   - Resource utilization alerts
   - Application error rate alerts

## Challenges & Solutions

### Возможные проблемы и их решения:

1. **ImagePullBackOff:**
   - **Проблема:** Kubernetes не может скачать Docker образ
   - **Решение:** Проверить правильность имени образа в deployment.yml
   - **Отладка:** `kubectl describe pod <pod-name>`

2. **CrashLoopBackOff:**
   - **Проблема:** Контейнер постоянно падает
   - **Решение:** Проверить логи приложения
   - **Отладка:** `kubectl logs <pod-name>`

3. **Service недоступен:**
   - **Проблема:** Нет доступа к приложению через Service
   - **Решение:** Проверить селекторы и порты
   - **Отладка:** `kubectl get endpoints`, `kubectl describe service`

4. **Health checks failing:**
   - **Проблема:** Probes не проходят
   - **Решение:** Увеличить initialDelaySeconds или проверить endpoint
   - **Отладка:** `kubectl describe pod <pod-name>`

### Debugging Commands

```bash
# Общая информация о кластере
kubectl cluster-info
kubectl get nodes

# Информация о ресурсах
kubectl get all
kubectl get pods -o wide
kubectl describe deployment devops-python-app

# Логи и события
kubectl logs <pod-name>
kubectl logs <pod-name> --previous
kubectl get events --sort-by=.metadata.creationTimestamp

# Отладка сети
kubectl exec -it <pod-name> -- /bin/sh
kubectl port-forward <pod-name> 8080:8000
```

## What I Learned About Kubernetes

1. **Declarative Configuration:**
   - Kubernetes работает с желаемым состоянием (desired state)
   - Контроллеры постоянно сверяют текущее состояние с желаемым
   - YAML манифесты описывают желаемое состояние

2. **Pod Lifecycle:**
   - Pod - минимальная единица развертывания
   - Контейнеры в Pod'е разделяют сеть и storage
   - Kubernetes автоматически перезапускает failed Pod'ы

3. **Service Discovery:**
   - Service предоставляет стабильный endpoint для Pod'ов
   - Label selectors связывают Service с Pod'ами
   - Kubernetes автоматически обновляет endpoints

4. **Rolling Updates:**
   - Zero-downtime deployments через постепенную замену Pod'ов
   - Возможность отката к предыдущей версии
   - Контроль скорости обновления через maxSurge/maxUnavailable

5. **Resource Management:**
   - Requests гарантируют минимальные ресурсы
   - Limits предотвращают превышение ресурсов
   - Правильная настройка критична для стабильности кластера

6. **Health Checks:**
   - Liveness проверяет здоровье контейнера
   - Readiness проверяет готовность к трафику
   - Правильная настройка предотвращает каскадные сбои

## Testing Checklist

- [ ] Deployment создан и все Pod'ы в состоянии Running
- [ ] Service создан и имеет правильные endpoints
- [ ] Приложение доступно через NodePort (30080)
- [ ] Health check endpoint `/health` отвечает 200 OK
- [ ] Metrics endpoint `/metrics` доступен
- [ ] Scaling до 5 реплик работает
- [ ] Rolling update выполняется без downtime
- [ ] Rollback работает корректно
- [ ] Resource limits применены корректно
- [ ] Liveness и readiness probes работают

## Next Steps

После успешного развертывания рекомендуется:

1. Изучить Helm для управления пакетами
2. Настроить CI/CD pipeline с автоматическим deployment
3. Добавить мониторинг и алертинг
4. Изучить StatefulSets для stateful приложений
5. Настроить Ingress для production-ready routing