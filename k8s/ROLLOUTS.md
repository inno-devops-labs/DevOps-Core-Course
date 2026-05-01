# Lab 14 — Progressive Delivery with Argo Rollouts

## 1. Argo Rollouts Setup

### Установка контроллера

Argo Rollouts установлен в отдельный namespace `argo-rollouts`:

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl rollout status deploy/argo-rollouts -n argo-rollouts
```

### Установка kubectl plugin

```bash
curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64
chmod +x kubectl-argo-rollouts-linux-amd64
sudo mv kubectl-argo-rollouts-linux-amd64 /usr/local/bin/kubectl-argo-rollouts
kubectl argo rollouts version
```

### Установка Dashboard

```bash
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

Dashboard доступен по адресу `http://localhost:3100`.

### Rollout vs Deployment — ключевые отличия

| Аспект                    | Deployment              | Rollout                |
| ------------------------- | ----------------------- | ---------------------- |
| **API Group**             | `apps/v1`               | `argoproj.io/v1alpha1` |
| **Kind**                  | `Deployment`            | `Rollout`              |
| **Стратегии**             | RollingUpdate, Recreate | canary, blueGreen      |
| **Traffic shifting**      | Нет                     | Есть (по весу реплик)  |
| **Автоматический анализ** | Нет                     | Через AnalysisTemplate |
| **Ручные паузы**          | Нет                     | `pause: {}`            |
| **Мгновенный откат**      | ~2-3 минуты             | Секунды                |
| **Pod template**          | Идентичен               | Идентичен Deployment   |

Rollout — это drop-in замена Deployment. Pod template, selector, replicas — всё то же самое. Добавляется только блок `strategy` с расширенными возможностями.

---

## 2. Canary Deployment

### Конфигурация стратегии

Файл: `k8s/info-service/templates/rollout.yaml`

Canary-стратегия настроена с пятью шагами прогрессии:

```yaml
strategy:
  canary:
    steps:
      - setWeight: 20 # 20% трафика на новую версию
      - pause: {} # Ручная пауза — требует promote
      - setWeight: 40
      - pause: { duration: 30s }
      - setWeight: 60
      - pause: { duration: 30s }
      - setWeight: 80
      - pause: { duration: 30s }
      # 100% — автоматически после последнего шага
```

Логика работы: Argo Rollouts создаёт два ReplicaSet — `stable` (старая версия) и `canary` (новая). Доля трафика задаётся количеством реплик: при `setWeight: 20` и 4 репликах всего — 1 pod canary, 3 pods stable.

### Деплой и активация Rollout

```bash
# Установка с canary-values
helm upgrade --install info-service ./k8s/info-service \
  -f ./k8s/info-service/values.yaml \
  -f ./k8s/info-service/values-canary.yaml

# Проверка статуса
kubectl argo rollouts get rollout info-service-info-service -w
```

### Прогрессия canary-роллаута

Обновляем image tag для запуска нового роллаута:

```bash
helm upgrade info-service ./k8s/info-service \
  -f ./k8s/info-service/values.yaml \
  -f ./k8s/info-service/values-canary.yaml \
  --set image.tag=v2
```

Роллаут входит в паузу на шаге 1 (20%). Ручной promote для перехода к следующему шагу:

```bash
kubectl argo rollouts promote info-service-info-service
```

После promote роллаут продолжается автоматически: 40% → пауза 30с → 60% → пауза 30с → 80% → пауза 30с → 100%.

### Тест отката

Запускаем новый роллаут и прерываем его на этапе 20%:

```bash
helm upgrade info-service ./k8s/info-service \
  -f ./k8s/info-service/values.yaml \
  -f ./k8s/info-service/values-canary.yaml \
  --set image.tag=v3

kubectl argo rollouts abort info-service-info-service
```

После abort трафик мгновенно возвращается на stable-версию. Повторная попытка после исправления:

```bash
kubectl argo rollouts retry rollout info-service-info-service
```

---

## 3. Blue-Green Deployment

### Конфигурация стратегии

Blue-Green использует два Service:

- **Active** (`info-service-info-service`) — production-трафик, указывает на текущую версию
- **Preview** (`info-service-info-service-preview`) — тестовый трафик, указывает на новую версию

```yaml
strategy:
  blueGreen:
    activeService: info-service-info-service
    previewService: info-service-info-service-preview
    autoPromotionEnabled: false # ручной promote
    scaleDownDelaySeconds: 30 # задержка удаления старых подов
```

### Установка blue-green Rollout

```bash
helm upgrade --install info-service ./k8s/info-service \
  -f ./k8s/info-service/values.yaml \
  -f ./k8s/info-service/values-bluegreen.yaml

kubectl argo rollouts get rollout info-service-info-service -w
```

### Тест blue-green флоу

Обновляем image до `v2` — запускается green-среда:

```bash
helm upgrade info-service ./k8s/info-service \
  -f ./k8s/info-service/values.yaml \
  -f ./k8s/info-service/values-bluegreen.yaml \
  --set image.tag=v2
```

Rollout создаёт новый ReplicaSet (green), preview service переключается на него. Тестируем обе версии через port-forward:

```bash
# Production (blue) — старая версия
kubectl port-forward svc/info-service-info-service 8080:80

# Preview (green) — новая версия для QA
kubectl port-forward svc/info-service-info-service-preview 8081:80
```

После проверки — promote зелёной среды:

```bash
kubectl argo rollouts promote info-service-info-service
```

Active service мгновенно переключается на зелёные поды. Через 30 секунд (scaleDownDelaySeconds) старые поды удаляются.

### Тест мгновенного отката

```bash
kubectl argo rollouts undo info-service-info-service
```

Трафик возвращается на предыдущую версию мгновенно (< 1 секунды) — старый ReplicaSet ещё не был полностью удалён, поэтому поды не пересоздаются.

---

## 4. Сравнение стратегий

| Аспект            | Canary                                | Blue-Green                     |
| ----------------- | ------------------------------------- | ------------------------------ |
| **Сдвиг трафика** | Постепенный (20% → 40% → ... → 100%)  | Мгновенный (0% → 100%)         |
| **Откат**         | Мгновенный (abort)                    | Мгновенный (undo)              |
| **Ресурсы**       | Минимальный overhead (1-2 extra pods) | 2x реплик во время деплоя      |
| **Риск**          | Минимальный (малый % пользователей)   | Весь трафик сразу после switch |
| **Тестирование**  | Реальный % production-трафика         | Изолированная preview-среда    |
| **Сложность**     | Выше (управление весами)              | Проще (два сервиса)            |
| **Использование** | Большинство релизов                   | Крупные изменения, DB-миграции |

**Когда использовать Canary:**

- Обычные feature-релизы, когда нужно постепенно убедиться в стабильности
- Высоконагруженные сервисы, где нельзя рисковать полным трафиком
- Когда есть метрики для автоматического принятия решений

**Когда использовать Blue-Green:**

- Breaking changes (изменение API, формата данных)
- Когда нужна полная изоляция нового кода для QA до попадания в production
- Когда важен мгновенный rollback без постепенного снижения трафика

**Рекомендация:** для данного сервиса canary предпочтительнее — он позволяет поймать проблемы на минимальном проценте пользователей, не прерывая весь трафик.

---

## 5. Справочник команд

```bash
# Статус роллаута (live)
kubectl argo rollouts get rollout <name> -w

# Promote (следующий шаг / подтверждение)
kubectl argo rollouts promote <name>

# Promote пропуская все оставшиеся шаги
kubectl argo rollouts promote <name> --full

# Abort (прерывание, откат на stable)
kubectl argo rollouts abort <name>

# Undo (откат на предыдущую версию)
kubectl argo rollouts undo <name>

# Retry после abort
kubectl argo rollouts retry rollout <name>

# Список всех роллаутов
kubectl argo rollouts list rollouts

# Dashboard
kubectl argo rollouts dashboard
# → http://localhost:3100
```

---

## Файловая структура

```
k8s/
├── info-service/
│   ├── Chart.yaml
│   ├── values.yaml                    # Базовые values (rollout.enabled: false)
│   ├── values-canary.yaml             # Canary-стратегия (rollout.enabled: true)
│   ├── values-bluegreen.yaml          # Blue-green стратегия
│   └── templates/
│       ├── deployment.yaml            # Условный (не рендерится при rollout.enabled)
│       ├── rollout.yaml               # Argo Rollout (canary или blue-green)
│       ├── service.yaml               # Active service
│       └── service-preview.yaml       # Preview service (только для blue-green)
└── ROLLOUTS.md                        # Эта документация
```

---
