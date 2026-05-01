# Lab 15 — StatefulSets & Persistent Storage

## 1. StatefulSet Concepts

### Зачем нужен StatefulSet

Deployment отлично подходит для stateless-приложений, где все поды взаимозаменяемы. Но для stateful-приложений — баз данных, очередей сообщений, распределённых систем — нужны гарантии, которые Deployment не даёт:

- **Стабильные имена подов** — при рестарте под получает то же имя (`app-0`, `app-1`), а не случайный суффикс
- **Стабильное хранилище** — каждый под привязан к своему PVC, который не удаляется при рестарте пода
- **Упорядоченный запуск** — следующий под запускается только после того, как предыдущий стал Ready

### StatefulSet vs Deployment

| Аспект | Deployment | StatefulSet |
|--------|-----------|------------|
| **Имена подов** | Случайный суффикс (`app-abc12`) | Порядковый индекс (`app-0`, `app-1`) |
| **Хранилище** | Общий PVC или без него | Отдельный PVC на каждый под |
| **Масштабирование** | Параллельное | Последовательное (0→1→2) |
| **Удаление** | Произвольный порядок | Обратный (2→1→0) |
| **Сетевая идентификация** | Через общий Service | Стабильное DNS-имя на под |
| **Применение** | Stateless-приложения | Базы данных, очереди, кластеры |

**Примеры stateful-нагрузок:** PostgreSQL, MongoDB, Kafka, Elasticsearch, Redis Cluster.

### Headless Service

Обычный Service получает ClusterIP и балансирует трафик между подами. Headless Service (`clusterIP: None`) не получает IP — вместо этого DNS-запрос возвращает IP-адреса всех подов напрямую.

Именно Headless Service позволяет StatefulSet создавать стабильные DNS-имена для каждого пода:

```
<pod-name>.<headless-service>.<namespace>.svc.cluster.local
```

Например:
```
info-service-info-service-0.info-service-info-service-headless.default.svc.cluster.local
info-service-info-service-1.info-service-info-service-headless.default.svc.cluster.local
info-service-info-service-2.info-service-info-service-headless.default.svc.cluster.local
```

Это имя остаётся неизменным даже после перезапуска пода — в отличие от IP-адреса.

---

## 2. Реализация StatefulSet

### Конфигурация

Файл: `k8s/info-service/templates/statefulset.yaml`

Ключевые отличия от Deployment:

```yaml
apiVersion: apps/v1
kind: StatefulSet
spec:
  serviceName: info-service-info-service-headless  # обязательное поле
  updateStrategy:
    type: RollingUpdate
  volumeClaimTemplates:                            # PVC создаётся автоматически для каждого пода
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Mi
```

`serviceName` — указывает на Headless Service, который обеспечивает DNS-имена для подов.

`volumeClaimTemplates` — вместо единого PVC для всех подов, Kubernetes автоматически создаёт отдельный PVC на каждый под при его запуске. При удалении пода PVC **не удаляется** — данные сохраняются.

### Headless Service

Файл: `k8s/info-service/templates/service-headless.yaml`

```yaml
apiVersion: v1
kind: Service
metadata:
  name: info-service-info-service-headless
spec:
  clusterIP: None   # ключевое поле — делает сервис headless
  selector:
    app.kubernetes.io/name: info-service
  ports:
  - port: 80
    targetPort: 8000
```

Headless Service должен быть создан **до** StatefulSet — Kubernetes требует этого для корректного формирования DNS-записей.

### Установка

```bash
helm upgrade --install info-service ./k8s/info-service \
  -f ./k8s/info-service/values.yaml \
  -f ./k8s/info-service/values-statefulset.yaml
```

Проверка ресурсов:

```bash
kubectl get po,sts,svc,pvc
```

После деплоя поды создаются последовательно: сначала `info-service-info-service-0` становится Running и Ready, затем запускается `info-service-info-service-1`, затем `info-service-info-service-2`.

Для каждого пода автоматически создаётся PVC с именем `data-<pod-name>`:
- `data-info-service-info-service-0`
- `data-info-service-info-service-1`
- `data-info-service-info-service-2`

---

## 3. Сетевая идентификация и изолированное хранилище

### DNS-резолюция между подами

Каждый под в StatefulSet получает стабильное DNS-имя. Для проверки выполняем `nslookup` из одного пода на другой:

```bash
kubectl exec -it info-service-info-service-0 -- /bin/sh
nslookup info-service-info-service-1.info-service-info-service-headless
```

DNS отвечает IP-адресом конкретного пода `info-service-info-service-1`, а не балансировщика. Имя разрешается независимо от того, был ли под перезапущен.

### Изоляция хранилища по подам

Каждый под пишет данные о визитах в свой собственный PVC (примонтирован в `/data`). Проверяем количество визитов для каждого пода независимо через port-forward:

```bash
kubectl port-forward pod/info-service-info-service-0 8080:8000
kubectl port-forward pod/info-service-info-service-1 8081:8000
kubectl port-forward pod/info-service-info-service-2 8082:8000

curl localhost:8080/visits
curl localhost:8081/visits
curl localhost:8082/visits
```

Каждый под возвращает свой независимый счётчик визитов — данные между подами не разделяются.

### Тест персистентности после удаления пода

Удаляем под `info-service-info-service-0` и проверяем, что после автоматического пересоздания данные сохранились:

```bash
# Фиксируем текущее количество визитов у пода-0
curl localhost:8080/visits

# Удаляем под
kubectl delete pod info-service-info-service-0

# Ждём пересоздания (StatefulSet восстанавливает под с тем же именем)
kubectl wait --for=condition=Ready pod/info-service-info-service-0 --timeout=60s

# Проверяем — счётчик сохранился
kubectl port-forward pod/info-service-info-service-0 8080:8000
curl localhost:8080/visits
```

После перезапуска под поднимается с тем же именем и подключается к тому же PVC (`data-info-service-info-service-0`). Данные не теряются — в этом и состоит главное преимущество StatefulSet перед Deployment.

---

## 4. Сравнение с Deployment и Rollout

| Контроллер | Назначение | Хранилище | Порядок запуска |
|-----------|-----------|-----------|----------------|
| **Deployment** | Stateless-приложения | Общий PVC или нет | Параллельный |
| **Rollout** (Argo) | Прогрессивная доставка stateless | Общий PVC или нет | По стратегии |
| **StatefulSet** | Stateful-приложения | PVC на каждый под | Последовательный |

Rollout (Lab 14) и StatefulSet решают разные задачи и не исключают друг друга: StatefulSet используется для базы данных, а Deployment/Rollout — для API-сервиса, который к ней обращается.

---

## Файловая структура

```
k8s/
├── info-service/
│   ├── values.yaml                     # statefulset.enabled: false по умолчанию
│   ├── values-statefulset.yaml         # replicaCount: 3, statefulset.enabled: true
│   └── templates/
│       ├── deployment.yaml             # не рендерится при rollout или statefulset
│       ├── rollout.yaml                # не рендерится при statefulset
│       ├── statefulset.yaml            # только при statefulset.enabled: true
│       ├── service.yaml                # основной Service (NodePort)
│       └── service-headless.yaml       # Headless Service для StatefulSet
└── STATEFULSET.md                      # эта документация
```

---

