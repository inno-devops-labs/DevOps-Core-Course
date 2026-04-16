# Lab 12 — ConfigMaps & Persistent Volumes

Concise report (namespace `app`).

---

## 1. Application changes

- **Visits counter:** each `GET /` increments a counter stored in `/data/visits` (override with `VISITS_FILE_PATH`).
- **Endpoint:** `GET /visits` returns `{"visits": <n>}` (read-only, no increment).

**Local Docker (compose volume):**

```bash
cd app_python && docker compose up --build
curl -s http://localhost:8000/
curl -s http://localhost:8000/visits
```

Example:

```
{"visits":1}
```

Repeated `GET /visits` without new `GET /` keeps the same value.

---

## 2. ConfigMap implementation

**Files in chart:**

- `k8s/app-python/files/config.json` — baked into a ConfigMap with `{{ .Files.Get "files/config.json" | indent 4 }}` in `templates/configmap.yaml`.
- Second ConfigMap in the same template supplies `APP_ENV`, `LOG_LEVEL`, `APP_NAME` from `values.yaml`.
- Deployment mounts the file ConfigMap at `/config` (read-only) and uses `envFrom` + `configMapRef` for the env ConfigMap.

**`kubectl get configmap,pvc -n app`:**

```
NAME                                         DATA   AGE
configmap/app-python-app-python-app-config   1      30m
configmap/app-python-app-python-env          3      30m

NAME                                               STATUS   CAPACITY   ACCESS MODES   STORAGECLASS
persistentvolumeclaim/app-python-app-python-data   Bound    100Mi      RWO            standard
```

**Mounted file:**

```bash
kubectl exec -n app deploy/app-python-app-python -- cat /config/config.json
```

```json
{
  "appName": "devops-info-service",
  "environment": "dev",
  "features": {
    "verboseErrors": false,
    "metricsEnabled": true
  }
}
```

**Env from ConfigMap (only keys from our chart; avoids service-discovery noise):**

```bash
kubectl exec -n app deploy/app-python-app-python -- printenv | grep -E '^(APP_ENV|APP_NAME|LOG_LEVEL)='
```

```
APP_ENV=dev
APP_NAME=devops-info-service
LOG_LEVEL=info
```

---

## 3. Persistent volume

**PVC:** `templates/pvc.yaml` — `ReadWriteOnce`, `100Mi`, storage class from `values` (`standard` on minikube).

**Mount:** PVC → `/data`; visits file: `/data/visits`.

```bash
kubectl exec -n app deploy/app-python-app-python -- cat /data/visits
```

```
3
```

**Persistence after pod delete (same PVC, new pod):**

```bash
kubectl delete pod -n app app-python-app-python-f58749448-9c7mp
```

```
pod "app-python-app-python-f58749448-9c7mp" deleted from app namespace
```

```bash
kubectl get pods -n app
```

```
NAME                                    READY   STATUS    RESTARTS   AGE
app-python-app-python-f58749448-wd48f   1/1     Running   0          7s
```

With `minikube service` (or `kubectl port-forward`) active, `/visits` did not reset to `0` after the new pod; the counter stayed on the volume. Example session: `curl .../visits` showed `{"visits":2}` before delete; after a new tunnel port, further checks still reflected the same PVC-backed file (e.g. `{"visits":3}` after additional `GET /`).

---

## 4. ConfigMap vs Secret

| | ConfigMap | Secret |
|---|-----------|--------|
| Use | Non-sensitive config (flags, log level, JSON app config) | Passwords, tokens, keys |
| Default encoding | Plaintext in API | Base64 in manifests |

Use **Secret** for credentials; this chart keeps secrets in the existing Secret and puts non-sensitive settings in ConfigMaps.
