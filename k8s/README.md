# k8s/README — DevOps App

Дата: 2026-03-26

Краткое описание: документация по развёртыванию `devops-app` в локальном kind-кластере. Включает архитектуру, описание манифестов, доказательства развёртывания, операции и рекомендации.

**Архитектура**
- Deployment `devops-app-deployment` — 5 реплик (Pod'ы запускают контейнер `netotveto/devops-app:1.0.0`).
- Service `devops-app-service` — NodePort, `port:80` → `targetPort:5000`, `nodePort:30080`.
- В локальном kind: single control-plane node, Pods запущены на `lab9-control-plane`.

---

## Манифесты
- `k8s/deployment.yml` — Deployment с:
  - `replicas: 5`
  - `securityContext` (pod-level): `runAsNonRoot: true`, `runAsUser: 1000`
  - `resources`: requests `100m/128Mi`, limits `200m/256Mi`
  - `livenessProbe` и `readinessProbe` на `/health` (порт 5000)
  - контейнерный `securityContext`: `allowPrivilegeEscalation: false`, `capabilities.drop: [ALL]`

- `k8s/service.yml` — Service типа `NodePort`, селектор `app=devops-info-service`, `port:80`, `targetPort:5000`, `nodePort:30080`.

---

## Доказательства развёртывания (вывод команд)

=== kubectl get all -o wide ===

```
NAME                                         READY   STATUS    RESTARTS   AGE     IP            NODE    
pod/devops-app-deployment-6cd6857779-5lccx   1/1     Running   0          6m24s   10.244.0.22   lab9-control-plane
pod/devops-app-deployment-6cd6857779-9rfww   1/1     Running   0          6m45s   10.244.0.19   lab9-control-plane
pod/devops-app-deployment-6cd6857779-nqwnp   1/1     Running   0          6m31s   10.244.0.21   lab9-control-plane
pod/devops-app-deployment-6cd6857779-p84sd   1/1     Running   0          6m38s   10.244.0.20   lab9-control-plane
pod/devops-app-deployment-6cd6857779-wgvz5   1/1     Running   0          6m51s   10.244.0.18   lab9-control-plane

NAME                         TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE   SELECTOR
service/devops-app-service   NodePort    10.96.115.172   <none>        80:30080/TCP   11m   app=devops-info-service
service/kubernetes           ClusterIP   10.96.0.1       <none>        443/TCP        29m   <none>

NAME                                    READY   UP-TO-DATE   AVAILABLE   AGE   CONTAINERS   IMAGES                 SELECTOR
deployment.apps/devops-app-deployment   5/5     5            5           22m   devops-app   netotveto/devops-app:1.0.0   app=devops-info-service

NAME                                               DESIRED   CURRENT   READY   AGE     CONTAINERS   IMAGES                       SELECTOR
replicaset.apps/devops-app-deployment-659dbc47d9   0         0         0       22m     devops-app   netotveto/devops-app:1.0.0   app=devops-info-service,pod-template-hash=659dbc47d9
replicaset.apps/devops-app-deployment-6cd6857779   5         5         5       16m     devops-app   netotveto/devops-app:1.0.0   app=devops-info-service,pod-template-hash=6cd6857779
replicaset.apps/devops-app-deployment-6f74dd646    0         0         0       9m34s   devops-app   netotveto/devops-app:1.0.0   app=devops-info-service,pod-template-hash=6f74dd646
```

=== kubectl get pods -o wide ===

```
NAME                                     READY   STATUS    RESTARTS   AGE     IP            NODE
devops-app-deployment-6cd6857779-5lccx   1/1     Running   0          6m24s   10.244.0.22   lab9-control-plane
devops-app-deployment-6cd6857779-9rfww   1/1     Running   0          6m45s   10.244.0.19   lab9-control-plane
devops-app-deployment-6cd6857779-nqwnp   1/1     Running   0          6m31s   10.244.0.21   lab9-control-plane
devops-app-deployment-6cd6857779-p84sd   1/1     Running   0          6m38s   10.244.0.20   lab9-control-plane
devops-app-deployment-6cd6857779-wgvz5   1/1     Running   0          6m51s   10.244.0.18   lab9-control-plane
```

=== kubectl get svc -o wide ===

```
NAME                 TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE   SELECTOR
devops-app-service   NodePort    10.96.115.172   <none>        80:30080/TCP   11m   app=devops-info-service
kubernetes           ClusterIP   10.96.0.1       <none>        443/TCP        29m   <none>
```

=== kubectl get endpoints devops-app-service -o wide ===

```
NAME                 ENDPOINTS                                                        AGE
devops-app-service   10.244.0.18:5000,10.244.0.19:5000,10.244.0.20:5000 + 2 more...   11m
```

=== kubectl describe deployment devops-app-deployment ===

```
(см. ниже ключевые поля)
Name:                   devops-app-deployment
Namespace:              default
Replicas:               5 desired | 5 updated | 5 total | 5 available | 0 unavailable
StrategyType:           RollingUpdate
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Containers:
  devops-app:
    Image:      netotveto/devops-app:1.0.0
    Port:       5000/TCP (http)
    Limits:     cpu: 200m, memory: 256Mi
    Requests:   cpu: 100m, memory: 128Mi
    Liveness:   http-get http://:http/health delay=10s timeout=2s period=10s
    Readiness:  http-get http://:http/health delay=5s timeout=2s period=5s
Pod SecurityContext:
  runAsNonRoot: true
  runAsUser: 1000
```

=== kubectl rollout history deployment/devops-app-deployment ===

```
deployment.apps/devops-app-deployment 
REVISION  CHANGE-CAUSE
1         <none>
3         <none>
4         <none>
```

=== Проверка HTTP /health (curl из временного pod) ===

```
{"status":"healthy","timestamp":"2026-03-26T14:22:02.980760Z","uptime_seconds":519}
```

(вывод получен через `kubectl run --image=curlimages/curl` внутри кластера)

---

## Операции, которые были выполнены

- Применение манифестов:
```bash
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
```

- Масштабирование и rolling update (через патч):
```bash
kubectl patch deployment devops-app-deployment --type=strategic -p '{"spec":{"replicas":5,"template":{"spec":{"containers":[{"name":"devops-app","env":[{"name":"APP_VERSION","value":"v2"}]}]}}}}'
kubectl rollout status deployment/devops-app-deployment --timeout=180s
```

- Проверки и отладка:
```bash
kubectl get pods -o wide
kubectl get svc devops-app-service -o wide
kubectl get endpoints devops-app-service -o wide
kubectl describe deployment devops-app-deployment
kubectl rollout history deployment/devops-app-deployment
kubectl rollout undo deployment/devops-app-deployment
```

- Тест доступа к приложению (изнутри кластера):
```bash
kubectl run curltest --rm -i --restart=Never --image=curlimages/curl --command -- sh -c "curl -sS -m 5 http://devops-app-service:80/health"
```

---

## Production considerations
- Health checks: `liveness` и `readiness` на `/health` защищают от направления трафика в неготовые Pod'ы и позволяют kubelet перезапустить упавшие контейнеры.
- Security: использование `runAsUser:1000` и `runAsNonRoot:true` + `allowPrivilegeEscalation:false` и `capabilities.drop: [ALL]` повышает безопасность.
- Resources: заданы минимальные requests/limits; в продакшне подобрать по нагрузке, добавить HPA при необходимости.
- Networking: вместо NodePort для продакшна использовать Ingress + LoadBalancer/TLS.
- Observability: добавить Prometheus metrics, логирование (Loki/ELK) и трассировку.

## Challenges & Solutions
- Проблема: `CreateContainerConfigError` из-за того, что образ использует именованный пользователь (`appuser`) — kubelet не может проверить `runAsNonRoot`. Решение: задать `runAsUser:1000` в Pod securityContext или пересобрать образ с числовым UID.
- Отладка: `kubectl describe pod`, `kubectl logs`, `kubectl get events` помогли найти причину и исправить.

---

Если нужно, могу дополнить этот README скриншотами терминала (вставлю в формате Base64 или как текст вывода), или добавить шаги для Ingress/TLS (bonus).
