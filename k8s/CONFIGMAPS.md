# Lab 12 — ConfigMaps and persistent volumes

This report documents the visit counter, Helm ConfigMaps, PVC-backed storage, and verification for Lab 12. **Cluster:** Minikube. **Release:** `lab12`, **namespace:** `lab12`.

---

## 1. Application changes

### Behaviour

- **`GET /`** increments a counter and persists it to **`VISITS_FILE`** (default `/data/visits`).
- **`GET /visits`** returns the current value without incrementing.
- Updates use a temporary file and `Path.replace()` for atomic writes; a `threading.Lock` serializes concurrent updates.

### Unit tests

From `app_python/` (virtual environment with dev dependencies):

```bash
pytest -q
```

```text
.....                                                                                 [100%]
5 passed in 0.21s
```

### Local Docker Compose

From `app_python/`:

```bash
docker compose up --build -d
curl -s http://localhost:8080/
curl -s http://localhost:8080/visits
cat ./data/visits
docker compose restart devops-info-service
curl -s http://localhost:8080/visits
```

```text
{"file":"/app/data/visits","visits":1}
1
{"file":"/app/data/visits","visits":1}
```

Lines: response to `GET /visits` before restart; contents of `./data/visits`; response to `GET /visits` after `docker compose restart`.

The compose file sets `VISITS_FILE=/app/data/visits` and mounts `./data` so the counter survives container restarts.

---

## 2. Helm chart: ConfigMaps and image for Kubernetes

### ConfigMap sources

| Path | Role |
|------|------|
| [`devops-info-service/files/config.json`](./devops-info-service/files/config.json) | JSON config embedded into a ConfigMap |
| [`devops-info-service/templates/configmap.yaml`](./devops-info-service/templates/configmap.yaml) | File ConfigMap (`.Files.Get`) + env ConfigMap (`APP_NAME`, `APP_ENV`, `LOG_LEVEL`) |

The Deployment mounts the file ConfigMap at **`/config/config.json`** and uses **`envFrom`** for the env ConfigMap (alongside the credentials Secret when enabled).

### Image build (Minikube)

The public image `mararokkel/devops-info-service:latest` did not include the new routes until a **local image** was built inside Minikube’s Docker daemon:

```bash
eval $(minikube docker-env)
docker build -t devops-info-service:lab12 ./app_python
```

Helm was then pointed at that image with `pullPolicy: IfNotPresent`.

---

## 3. Helm lint and install

### Lint

```bash
helm lint ./k8s/devops-info-service
```

```text
==> Linting ./k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### Install / upgrade

The first attempt with **`nodePort: 30082`** failed because that port was already allocated. **`service.nodePort=30083`** was used instead.

```bash
helm upgrade --install lab12 ./k8s/devops-info-service \
  -f k8s/devops-info-service/values-dev.yaml \
  --namespace lab12 --create-namespace \
  --set service.nodePort=30083 \
  --set image.repository=devops-info-service \
  --set image.tag=lab12 \
  --set image.pullPolicy=IfNotPresent
```

```text
Release "lab12" has been upgraded. Happy Helming!
NAME: lab12
LAST DEPLOYED: Thu Apr 16 21:16:06 2026
NAMESPACE: lab12
STATUS: deployed
REVISION: 3
```

```bash
kubectl rollout status deployment/lab12-devops-info-service -n lab12
```

```text
deployment "lab12-devops-info-service" successfully rolled out
```

---

## 4. ConfigMap verification

### Objects

```bash
kubectl get configmap,pvc -n lab12
```

`kubectl` prints **ConfigMaps** and **PVCs** as two tables (same result as running `kubectl get configmap` and `kubectl get pvc` separately):

```text
NAME                               DATA   AGE
kube-root-ca.crt                   1      5m27s
lab12-devops-info-service-config   1      5m23s
lab12-devops-info-service-env      3      5m23s

NAME                             STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
lab12-devops-info-service-data   Bound    pvc-e9441154-a847-4b86-ad7f-102b7aae2be4   100Mi      RWO            standard       <unset>                 5m27s
```

### File mount: `/config/config.json`

```bash
kubectl exec -n lab12 deploy/lab12-devops-info-service -- cat /config/config.json
```

```json
{
  "applicationName": "devops-info-service",
  "environment": "dev",
  "features": {
    "visitsCounter": true,
    "metrics": true
  },
  "settings": {
    "logLevel": "info",
    "responseFormat": "json"
  }
}
```

### Environment variables from ConfigMap

```bash
kubectl exec -n lab12 deploy/lab12-devops-info-service -- printenv | grep -E '^(APP_|LOG_)'
```

```text
APP_NAME=devops-info-service
LOG_LEVEL=info
APP_ENV=dev
```

---

## 5. PersistentVolumeClaim

Details appear in the combined listing in Section 4. PVC excerpt:

```text
NAME                             STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
lab12-devops-info-service-data   Bound    pvc-e9441154-a847-4b86-ad7f-102b7aae2be4   100Mi      RWO            standard       5m27s
```

[`values-dev.yaml`](./devops-info-service/values-dev.yaml) enables **`persistence.enabled: true`** with **`replicaCount: 1`** (single replica is required for a single **ReadWriteOnce** volume). The Deployment mounts the PVC at **`/data`** and sets **`VISITS_FILE=/data/visits`**. **`podSecurityContext.fsGroup: 1000`** matches the non-root user in the image (UID/GID 1000).

---

## 6. HTTP checks (Minikube)

Direct **`curl` to `NodeIP:NodePort`** timed out from the host (common with Docker Desktop / Minikube networking). **Port-forward** was used for reliable access:

```bash
kubectl port-forward -n lab12 svc/lab12-devops-info-service 8082:80
```

After the local image was deployed, the first checks were:

```bash
curl -sS http://localhost:8082/visits
curl -sS http://localhost:8082/
```

```text
{"file":"/data/visits","visits":0}
```

A follow-up `GET /` returned `visits.count` **1** and listed **`/visits`** under `endpoints`.

---

## 7. Persistence test (delete pod)

Commands:

```bash
kubectl get pods -n lab12
kubectl delete pod -n lab12 lab12-devops-info-service-78b444d574-xs4q6
kubectl rollout status deployment/lab12-devops-info-service -n lab12
kubectl exec -n lab12 deploy/lab12-devops-info-service -- cat /data/visits
curl -sS http://localhost:8082/visits
```

**Result:** the counter stayed **2** after the pod was recreated — the PVC retained the file.

```text
2
```

```text
{"file":"/data/visits","visits":2}
```

---

## 8. ConfigMap vs Secret

| | ConfigMap | Secret |
|---|-----------|--------|
| Typical content | Non-sensitive config (flags, URLs, log level) | Passwords, tokens, TLS material |
| API storage | Plaintext; often base64-encoded in manifests | Base64 in API; use encryption at rest for sensitive data |
| RBAC | Limit read access to ConfigMaps | Limit read access to Secrets more strictly |
| This lab | `config.json` and `APP_*` / `LOG_LEVEL` | Helm `Secret` for demo credentials when `credentials.enabled` |
