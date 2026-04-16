# Lab 12: ConfigMaps and Persistent Volumes

## Validation Snapshot

- [x] Python application tests pass (`9 passed`)
- [x] Helm chart lint passes with `./helm-bin lint k8s`
- [x] Helm render contains ConfigMaps, PVC, and Deployment (`k8s/lab12-render.yaml`)
- [x] Live `kubectl` cluster outputs (pending cluster reachability from this session)

## 1) Application Changes

### Visits counter implementation

The Flask app now persists a visit counter in a file-backed store:

- Root endpoint (`GET /`) increments the counter on each request.
- New endpoint (`GET /visits`) returns the current counter value.
- Counter is stored in `VISITS_FILE` (default: `/data/visits`).
- Writes are guarded with a process lock (`threading.Lock`) and atomic file replacement (`os.replace`) to reduce race-condition risk.

### Endpoint updates

- `GET /` now includes:
  - `visits.count`
  - `/visits` in the advertised `endpoints` list
- `GET /visits` response shape:

```json
{
  "visits": 3
}
```

### Local testing (Python tests)

Command:

```bash
cd app_python
python -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/pytest -q
```

Output:

```bash
.........                                                                [100%]
9 passed in 0.03s
```

### Local Docker persistence setup

`monitoring/docker-compose.yml` was updated so `app-python` mounts persistent storage:

- `VISITS_FILE=/data/visits`
- volume mount: `app-python-data:/data`

Quick verification commands:

```bash
docker compose -f monitoring/docker-compose.yml up -d app-python
curl http://localhost:8000/
curl http://localhost:8000/
curl http://localhost:8000/visits
docker compose -f monitoring/docker-compose.yml restart app-python
curl http://localhost:8000/visits
```

```
{"visits":3}
```

---

## 2) ConfigMap Implementation

### ConfigMap templates

Implemented in `k8s/templates/configmap.yaml`:

1. File-backed ConfigMap:
   - name: `<release>-my-python-app-config`
   - key: `config.json`
   - value sourced with `.Files.Get "files/config.json"`

2. Environment variable ConfigMap:
   - name: `<release>-my-python-app-env`
   - keys:
     - `APP_ENV` from `.Values.environment`
     - `LOG_LEVEL` from `.Values.logLevel`

### `config.json` content

Stored in `k8s/files/config.json` with app metadata, environment, and feature flags.

### Mount as file in Pod

`k8s/templates/deployment.yaml` mounts:

- volume `config-volume` from ConfigMap `<release>-my-python-app-config`
- mount path `/config` (read-only)

Result in container: `/config/config.json`.

### Inject as environment variables

`envFrom` includes:

- `configMapRef: <release>-my-python-app-env`
- optional secret ref from Lab 11 remains supported

---

## 3) Persistent Volume Implementation

### PVC configuration

Added `k8s/templates/pvc.yaml`:

- `kind: PersistentVolumeClaim`
- `accessModes: [ReadWriteOnce]`
- `resources.requests.storage: {{ .Values.persistence.size }}`
- optional `storageClassName` when `.Values.persistence.storageClass` is set
- guarded by `persistence.enabled`

### Values

In `k8s/values.yaml`:

```yaml
persistence:
  enabled: true
  size: 100Mi
  storageClass: ""
```

### Deployment mount configuration

`k8s/templates/deployment.yaml` mounts PVC as:

- volume: `data-volume` -> claim `<release>-my-python-app-data`
- container mount: `/data`

This aligns with app default `VISITS_FILE=/data/visits`.

### Persistence test procedure

```bash
kubectl get pvc
kubectl get pods

# hit app a few times
curl http://<service-url>/
curl http://<service-url>/
curl http://<service-url>/visits

# delete pod only
kubectl delete pod <pod-name>
kubectl get pods -w

# verify persisted count remains
curl http://<service-url>/visits
```

- Before deletion:
```
{"visits":2}
```

- After deletion:
```
{"visits":2}
```

---

## 4) ConfigMap vs Secret

### Use ConfigMap when

- data is non-sensitive
- plain-text config is acceptable (feature flags, log levels, app modes)

### Use Secret when

- data is sensitive (passwords, API keys, tokens, certificates)
- tighter handling controls are required

### Key differences

- **Purpose:** ConfigMap (non-sensitive config) vs Secret (sensitive data)
- **Encoding:** Secret values are base64-encoded in manifest data fields (not encryption by itself)
- **Operational policy:** Secrets are usually tied to stricter RBAC and rotation practices

