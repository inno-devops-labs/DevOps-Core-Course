# Lab 12 - ConfigMaps & Persistent Volumes

## Application Changes

The Flask app now keeps a persistent visit counter.

### What changed

- `GET /` increments the visit counter and returns it in the JSON response
- `GET /visits` returns the current counter without incrementing it
- The counter is stored in a file at `VISITS_FILE` and defaults to `/data/visits`
- The Docker Compose setup mounts a local folder to `/data` so the counter survives restarts

### Implementation notes

- The counter is read from disk on startup and defaults to `0` if the file does not exist
- File writes are atomic through a temporary file and `os.replace()`
- A file lock is used when incrementing the counter to reduce race conditions

### Local Docker verification

```bash
docker compose -f k8s/docker-compose.yml up -d
curl http://localhost:5000/
curl http://localhost:5000/
curl http://localhost:5000/visits
```

Expected result:

```json
{
  "visits": 2,
  "timestamp": "2026-04-15T18:00:00+00:00"
}
```

After restarting the container, the count should stay the same because the file is stored on the mounted volume.

---

## ConfigMap Implementation

### Chart files

```text
k8s/python-app/
  files/config.json
  templates/configmap.yaml
  templates/configmap-env.yaml
  templates/deployment.yaml
  templates/pvc.yaml
```

### `files/config.json`

This file stores non-sensitive application configuration:

```json
{
  "app": {
    "name": "devops-info-service",
    "environment": "production",
    "version": "1.0.0"
  },
  "features": {
    "visits_counter": true,
    "detailed_system_info": true,
    "health_check": true
  },
  "logging": {
    "level": "INFO",
    "format": "json"
  }
}
```

### ConfigMap templates

- `templates/configmap.yaml` mounts `config.json` into the pod as a file
- `templates/configmap-env.yaml` injects `APP_ENV`, `LOG_LEVEL`, and `APP_NAME` as environment variables

### Deployment wiring

The Deployment mounts the file ConfigMap at `/config`:

```yaml
volumeMounts:
  - name: config-volume
    mountPath: /config
```

The pod sees the file as `/config/config.json`.

Environment variables are injected with:

```yaml
envFrom:
  - configMapRef:
      name: {{ include "python-app.fullname" . }}-env
```

### Verification

```bash
kubectl get configmap,pvc
kubectl exec deployment/myrelease-python-app -- cat /config/config.json
kubectl exec deployment/myrelease-python-app -- printenv | grep -E "APP_|LOG_"
```

Sanity checks performed:

- `helm lint k8s/python-app`
- `helm template test k8s/python-app`

---

## Persistent Volume

### PVC template

`templates/pvc.yaml` creates a `ReadWriteOnce` PVC:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "python-app.fullname" . }}-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: {{ .Values.persistence.size }}
```

### Deployment mount

The PVC is mounted to `/data`:

```yaml
volumeMounts:
  - name: data-volume
    mountPath: /data
```

The app writes the visits counter to `/data/visits`, so the number survives pod recreation.

### Persistence test

1. Deploy the chart
2. Hit `/` several times
3. Confirm `/data/visits` contains the expected count
4. Delete the pod, not the deployment
5. Verify the new pod still reports the same count from `/visits`

Example:

```bash
kubectl delete pod myrelease-python-app-7d8f9c6b4-xkp2n
kubectl exec deployment/myrelease-python-app -- cat /data/visits
```

Expected result: the value remains unchanged after the pod is replaced.

---

## ConfigMap vs Secret

### Use ConfigMap for

- Non-sensitive settings
- Feature flags
- File-based app configuration
- Values safe to keep in Git

### Use Secret for

- Passwords
- API keys
- Tokens
- TLS material

### Key difference

ConfigMaps are plain configuration. Secrets are for sensitive data and should be handled separately, even though base64 encoding is not encryption.

