# Lab 12: ConfigMaps & Persistent Volumes

This document describes the completed implementation for Lab 12:
- visits counter persistence in the Python app
- ConfigMap file + ConfigMap environment variables in Helm
- PVC mount for durable `/data/visits`
- hot-reload strategy (bonus)

## 1. Application Changes

### Visits counter behavior

- `GET /` increments visits counter and returns `visits` in response.
- `GET /visits` returns current counter without increment.
- Counter is stored in file from `VISITS_FILE` (default: `/data/visits`).
- Counter updates are protected with a cross-platform exclusive lock:
  - `fcntl` on Unix-like systems
  - `msvcrt` on Windows

Relevant code:
- `app_python/app.py`:
  - `_read_visits()`
  - `_exclusive_file_lock()`
  - `_increment_visits()`
  - `@app.get("/visits")`

### Local Docker persistence setup

`app_python/docker-compose.yml` mounts host directory `./data` to `/data`:

```yaml
volumes:
  - ./data:/data
```

This keeps `./data/visits` on host and survives container restarts.

### Test coverage

`app_python/tests/test_app.py` now covers:
- root payload includes `visits`
- `/visits` starts from `0` when file is missing
- `/` increments counter and persists value to file
- `/visits` does not increment counter
- invalid counter file content falls back to `0`

Test result artifact:
- `k8s/lab12-evidence/pytest-app_python.txt`

## 2. ConfigMap Implementation

### File-based ConfigMap

Source file:
- `k8s/devops-info-chart/files/config.json`

Template:
- `k8s/devops-info-chart/templates/configmap.yaml`

`config.json` is loaded with `.Files.Get` and mounted into pod at `/config/config.json`.

### Env ConfigMap

Template:
- `k8s/devops-info-chart/templates/configmap-env.yaml`

Injected keys:
- `APP_ENV`
- `LOG_LEVEL`
- `VISITS_FILE`

### Deployment wiring

File:
- `k8s/devops-info-chart/templates/deployment.yaml`

Implemented:
- `envFrom.configMapRef` for env ConfigMap
- `config-volume` mount at `/config`
- checksum annotations:
  - `checksum/config`
  - `checksum/config-env`

## 3. Persistent Volume (PVC)

Template:
- `k8s/devops-info-chart/templates/pvc.yaml`

Configuration from `values.yaml`:

```yaml
persistence:
  enabled: true
  size: 100Mi
  storageClass: ""
  visitsFile: "/data/visits"
```

PVC details:
- access mode: `ReadWriteOnce`
- requested storage: `100Mi`
- storage class: configurable (default cluster class when empty)

Deployment mounts claim to `/data`:
- `persistentVolumeClaim.claimName: <release>-devops-info-chart-data`
- `volumeMounts.mountPath: /data`

## 4. Verification Evidence

### Static artifacts already captured

- `k8s/lab12-evidence/helm-lint.txt`
- `k8s/lab12-evidence/helm-template-dev.yaml`
- `k8s/lab12-evidence/pytest-app_python.txt`
- `k8s/lab12-evidence/environment-status.txt`
- `k8s/lab12-evidence/runtime-k8s.txt`
- `k8s/lab12-evidence/runtime-k8s-attempt.log`

### Runtime kubectl proof capture (required outputs)

When Docker + Minikube are running, execute:

```powershell
powershell -ExecutionPolicy Bypass -File k8s/scripts/capture-lab12-runtime-evidence.ps1
```

It generates:
- `k8s/lab12-evidence/runtime-k8s.txt`

The generated file includes all required lab outputs:
- `kubectl get configmap,pvc`
- `kubectl exec ... -- cat /config/config.json`
- `kubectl exec ... -- printenv` filtered to `APP_ENV|LOG_LEVEL|VISITS_FILE`
- persistence test:
  - visits value before pod deletion
  - `kubectl delete pod ...`
  - visits value after pod recreation

Current execution status (2026-04-16):
- Script execution was performed in this workspace.
- Generated `runtime-k8s.txt` with status `COMPLETED WITH ERRORS`.
- Blocking issue is host-level runtime availability (Docker service/cluster unreachable), not chart or app code.
- See `k8s/lab12-evidence/environment-status.txt` for concrete command errors.

## 5. ConfigMap vs Secret

| Topic | ConfigMap | Secret |
|---|---|---|
| Purpose | Non-sensitive configuration | Sensitive data (passwords, tokens, certs) |
| Storage in etcd | Plain text | Base64-encoded (and can be encrypted at rest) |
| Typical values | Feature flags, log level, app env | API keys, credentials, TLS keys |
| Exposure risk | Higher | Lower with RBAC + secret handling |

Rule: if value is sensitive, use Secret (or external secret manager), not ConfigMap.

## 6. Bonus: ConfigMap Hot Reload

Implemented restart-on-config-change pattern:

```yaml
annotations:
  checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
  checksum/config-env: {{ include (print $.Template.BasePath "/configmap-env.yaml") . | sha256sum }}
```

Behavior notes:
- Full ConfigMap directory mounts update automatically with kubelet sync delay.
- `subPath` does not auto-update for ConfigMap file changes.
- Alternative auto-restart approach: `stakater/reloader`.

## 7. Checklist Status

- [x] Visits counter implemented and persisted in file
- [x] `/visits` endpoint implemented
- [x] Docker Compose volume for persistence configured
- [x] App README updated
- [x] ConfigMap file template implemented
- [x] ConfigMap env template implemented
- [x] ConfigMap mounted into pod at `/config`
- [x] Env vars injected via `envFrom`
- [x] PVC template implemented
- [x] PVC mounted to `/data`
- [x] Checksum annotation pattern implemented (bonus)
- [x] Lab documentation completed in this file
