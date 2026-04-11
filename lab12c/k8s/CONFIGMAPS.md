# Lab 12 — ConfigMaps & persistence

App: `lab12c/app_python`. Chart: `lab12c/k8s/devops-info` (v0.3.0).

## App

Visit counter lives in a file (`VISITS_FILE`, default `/data/visits`). Each `GET /` bumps it under a lock; writes go through a temp file + `os.replace`. `GET /visits` is read-only. The JSON from `/` includes `visits.total` and the file path.

Docker Compose maps `./data` to `/data` — bounce the stack a few times and the number should stick.

Tests: run `pytest` in `lab12c/app_python`; they point `VISITS_FILE` at a temp path.

## ConfigMaps

`files/config.json` ships with the chart. `templates/configmap.yaml` builds two objects: one embeds that JSON via `.Files.Get`, the other exposes `APP_NAME`, `APP_ENV`, `LOG_LEVEL` from values.

Deployment mounts the file ConfigMap at `/config` → `/config/config.json`. The env ConfigMap hooks in with `envFrom` when `config.injectEnv` is true.

Snippet from `helm template app12 lab12c/k8s/devops-info -f lab12c/k8s/devops-info/values-dev.yaml`:

```yaml
data:
  config.json: |-
    {
      "appName": "devops-info-service",
      "environment": "development",
      "features": {
        "metricsEnabled": true,
        "verboseLogging": false
      }
    }
data:
  APP_NAME: "devops-info-service"
  APP_ENV: "development"
  LOG_LEVEL: "info"
```

Sanity checks (release name `app12`):

```bash
kubectl get configmap -l app.kubernetes.io/instance=app12
kubectl exec deploy/app12-devops-info -c app -- cat /config/config.json
kubectl exec deploy/app12-devops-info -c app -- printenv | grep APP_
```

On Windows host use `findstr APP_` instead of `grep` if you run `kubectl exec` from PowerShell and pipe outside the container.

## PVC

`templates/pvc.yaml` requests `ReadWriteOnce` storage, size from `persistence.size`. If `persistence.storageClass` is empty, the cluster default StorageClass applies (kind/minikube usually give you one).

Deployment uses either that PVC or `emptyDir` when persistence is off. Mount is `/data`, app uses `VISITS_FILE=/data/visits`.

RWO = one pod at a time on that volume the normal way, so `values-prod.yaml` keeps a single replica. Scaling out with a file counter on RWO doesn’t fly without RWX or moving state somewhere else.

```yaml
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Mi
```

## Cluster install notes

Build/push `tsixphoenix/devops-info-python:lab12`, or load into kind:

```bash
kind load docker-image tsixphoenix/devops-info-python:lab12 --name lab11
```

Then:

```bash
helm upgrade --install app12 lab12c/k8s/devops-info -f lab12c/k8s/devops-info/values-dev.yaml --set image.pullPolicy=Never
```

If **lab 11** is installed on the same cluster, both charts default to NodePort `30080` — Kubernetes will reject the second Service. `values-dev.yaml` for lab 12 sets `nodePort: 30081` so app11 can keep `30080`.

## ConfigMap vs Secret

ConfigMap = non-sensitive config (flags, log level, JSON metadata). Secret = passwords, keys, certs. Even Secrets are base64 in the API, not magic crypto — if it’s sensitive, treat it as sensitive. For heavy stuff see lab 11 / Vault.

---

## Evidence (captured on kind v1.31, 2026-04-11)

**Unit tests:**

```text
.......                                                                  [100%]
7 passed in 0.39s
```

**Helm lint (chart ok):**

```text
==> Linting lab12c/k8s/devops-info
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed
```

**ConfigMaps + PVC:**

```text
NAME                               DATA   AGE
configmap/app12-devops-info-env    3      ...
configmap/app12-devops-info-file   1      ...

NAME                                           STATUS   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/app12-devops-info-data   Bound    100Mi      RWO            standard       ...
```

**File inside pod (`/config/config.json`):**

```json
{
  "appName": "devops-info-service",
  "environment": "development",
  "features": {
    "metricsEnabled": true,
    "verboseLogging": false
  }
}
```

**Env from ConfigMap:**

```text
APP_ENV=development
APP_NAME=devops-info-service
LOG_LEVEL=info
```

**Persistence (same PVC after pod delete):** after three hits to `/`, `/data/visits` contained `3`. Deleted the pod; new pod still showed `3` in `/data/visits`.

Step-by-step for Vault + both charts: `lab11c/k8s/RUNBOOK.md`.
