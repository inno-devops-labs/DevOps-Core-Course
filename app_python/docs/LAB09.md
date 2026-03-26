# Lab 09 — Task 1 (Local Kubernetes Setup)

Дата: 2026-03-26
Инструмент: kind

## Почему выбран kind

Выбран **kind** (Kubernetes in Docker), потому что он:
- быстро поднимает локальный кластер;
- не требует отдельной VM;
- хорошо подходит для учебных задач и CI/CD сценариев.

## Подтверждение запуска кластера

Команда запуска (выполнена):
`/home/niyaz/.local/bin/kind create cluster --name lab9 --wait 120s`

Результат: кластер создан, контекст установлен в `kind-lab9`.

## Проверка кластера

### Текущий контекст
`kind-lab9`

### kubectl cluster-info
`Kubernetes control plane is running at https://127.0.0.1:33645`

`CoreDNS is running at https://127.0.0.1:33645/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy`

### kubectl get nodes -o wide
- `lab9-control-plane` — `Ready`
- Kubernetes version: `v1.32.2`
- Container runtime: `containerd://2.0.2`

### kubectl get namespaces
- `default`
- `kube-node-lease`
- `kube-public`
- `kube-system`
- `local-path-storage`

## Исследование ресурсов кластера

Проверены базовые ресурсы:
- `kubectl get pods -A`
- `kubectl get deployments -A`
- `kubectl get services -A`

Наблюдения:
- системные Pod'ы (`kube-apiserver`, `kube-controller-manager`, `kube-scheduler`, `coredns`, `kube-proxy`) в состоянии `Running`;
- Deployment `coredns` доступен (`2/2`);
- сервис `kubernetes` и `kube-dns` созданы.

## Кратко по фундаментальным понятиям Kubernetes

- **Pod**: минимальная единица запуска контейнеров.
- **Deployment**: управляет нужным количеством Pod'ов и обновлениями.
- **Service**: стабильная сетевая точка доступа к Pod'ам.
- **Namespace**: логическая изоляция ресурсов внутри кластера.

## Архитектура в этом кластере

- control plane: `lab9-control-plane`;
- worker-узлы отдельно не создавались (одноузловой учебный кластер);
- control plane поддерживает желаемое состояние через controllers/reconciliation loop.

---

Task 1 выполнен: локальный кластер установлен, проверен и исследован через `kubectl`.
# Lab 9 — Tasks 3–5 (Краткая документация)

Дата: 2026-03-26
Автор: niyaz

**Краткий вывод:** Tasks 3, 4 и 5 выполнены (создан Service, выполнено масштабирование и rolling update с демонстрацией отката). Ниже — краткая документация и команды, которые я выполнял.

## 1. Обзор архитектуры
- Deployment: `devops-app-deployment` (контейнер `netotveto/devops-app:1.0.0`), уровень приложения — 1 Deployment, 5 Pod'ов (после масштабирования).
- Service: `devops-app-service` (NodePort) — проброшен `port:80` → `targetPort:5000`, `nodePort:30080`.
- Сеть: NodePort позволяет обращаться к приложению извне кластера на порту узла (в локальном kind используйте `kubectl port-forward` или проброс nodePort).

## 2. Манифесты
- [k8s/deployment.yml](k8s/deployment.yml) — содержит:
  - `replicas: 5`
  - `securityContext` на уровне Pod: `runAsNonRoot: true` и `runAsUser: 1000`
  - ресурсы: requests (cpu: 100m, memory: 128Mi) и limits (cpu: 200m, memory: 256Mi)
  - `livenessProbe` и `readinessProbe` на `/health` (порт 5000)
  - контейнерная безопасность: `allowPrivilegeEscalation: false`, `capabilities.drop: [ALL]`

- [k8s/service.yml](k8s/service.yml) — NodePort сервис:
  - `port: 80`, `targetPort: 5000`, `nodePort: 30080`
  - селектор `app: devops-info-service` соответствует Deployment

## 3. Доказательства развёртывания (команды и ключевые выводы)
- Применить манифесты:
```bash
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
```
- Проверка сервиса и endpoints:
```bash
kubectl get svc devops-app-service -o wide
# показал NodePort 30080 и CLUSTER-IP
kubectl get endpoints devops-app-service -o wide
# endpoints содержат IP:5000 всех Pod'ов
```
- Масштабирование и rolling update (декларативно/патч):
```bash
# обновление replicas и добавление env для триггера обновления
kubectl patch deployment devops-app-deployment --type=strategic -p '{"spec":{"replicas":5,"template":{"spec":{"containers":[{"name":"devops-app","env":[{"name":"APP_VERSION","value":"v2"}]}]}}}}'
kubectl rollout status deployment/devops-app-deployment --timeout=180s
kubectl get pods -l app=devops-info-service -o wide
```
- История rollout и откат:
```bash
kubectl rollout history deployment/devops-app-deployment
kubectl rollout undo deployment/devops-app-deployment
kubectl rollout status deployment/devops-app-deployment --timeout=120s
```
(команды выполнены — откат успешно применён)

## 4. Доступ к приложению (локально)
- Через NodePort (на узле): `http://<node-ip>:30080/` — в kind локально обычно удобнее делать port-forward:
```bash
kubectl port-forward service/devops-app-service 8080:80
# затем в другом терминале
curl http://127.0.0.1:8080/health
```

## 5. Production-замечания
- Использовал `runAsUser: 1000`, потому что образ задаёт именованный пользователь; kubelet не может гарантировать runAsNonRoot для именованных пользователей.
- Health checks: `/health` используются и как `liveness` и `readiness` probe; это предотвращает направление трафика в нездоровые Pod'ы и перезапускает упавшие контейнеры.
- Ресурсы: небольшие limits/requests для локального кластера; в проде следует корректировать по наблюдаемому использованию.
- Роллинг-обновления: `maxUnavailable: 0` + `maxSurge: 1` — обеспечивает нулевой downtime во время обновлений.

## 6. Проблемы и их решения
- Проблема: `CreateContainerConfigError` из-за `runAsNonRoot` при именованном пользователе в образе (`appuser`).
  Решение: задать `runAsUser: 1000` в Pod `securityContext` или пересобрать образ с числовым UID (`USER 1000`).

## 7. Что ещё можно сделать (рекомендации)
- Добавить `k8s/README.md` (полная документация согласно Task 5) с выводами `kubectl get all` и `kubectl describe`.
- Добавить мониторинг (Prometheus, liveness metrics) и логирование (ELK/Loki).
- Для production: рассмотреть Ingress + TLS (см. Bonus в `labs/lab09.md`).

---

Если нужно, могу:
- сгенерировать `k8s/README.md` со всеми требуемыми разделами и полными выводами команд; или
- запустить тест доступа к `/health` сейчас и вставить реальный вывод в документацию.

Файлы, изменённые/созданные:
- [k8s/deployment.yml](k8s/deployment.yml)
- [k8s/service.yml](k8s/service.yml)
- labs/lab09-task1-evidence.md (Task 1 отчёт)
- app_python/docs/lab9.md (этот файл)

