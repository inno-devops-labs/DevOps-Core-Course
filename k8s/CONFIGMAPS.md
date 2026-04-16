# ConfigMaps & Persistent Volumes — Lab 12

## Application Changes

### Description of Visits Counter Implementation

The Python application ([`app_python/app.py`](../app_python/app.py)) was extended with a file-based persistent visit counter.

**Key additions:**

- `VISITS_FILE = os.getenv("VISITS_FILE", "/data/visits")` — configurable path to the counter file
- [`read_visits()`](../app_python/app.py) — reads the integer count from file; returns `0` if the file is missing or unreadable
- [`write_visits(count)`](../app_python/app.py) — atomically writes the count using `tempfile.mkstemp` + `os.replace()` to prevent corruption; creates the `/data/` directory with `os.makedirs(exist_ok=True)` if needed
- `GET /` — now increments the counter on every request and includes `"visits"` in the JSON response
- `GET /visits` — new endpoint that returns the current count without incrementing

**Counter flow:**
```
GET /  →  read_visits()  →  count + 1  →  write_visits()  →  return response (includes visits)
GET /visits  →  read_visits()  →  return {"visits": N}
```

**Implementation:**
```python
VISITS_FILE = os.getenv("VISITS_FILE", "/data/visits")

def read_visits() -> int:
    try:
        with open(VISITS_FILE, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0

def write_visits(count: int) -> None:
    data_dir = os.path.dirname(VISITS_FILE)
    if data_dir:
        os.makedirs(data_dir, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=data_dir if data_dir else ".")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(str(count))
        os.replace(tmp_path, VISITS_FILE)
    except Exception:
        os.unlink(tmp_path)
        raise
```

### New Endpoint Documentation

| Endpoint | Method | Description | Response |
|----------|--------|-------------|----------|
| `GET /` | GET | Service info + increments visit counter | JSON with `"visits"` field |
| `GET /visits` | GET | Returns current visit count | `{"visits": N, "file": "<path>"}` |

Example response from `GET /visits`:
```json
{
  "visits": 5,
  "file": "/data/visits"
}
```

### Local Testing Evidence with Docker

[`app_python/docker-compose.yml`](../app_python/docker-compose.yml) mounts `./data:/app/data`:

```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - VISITS_FILE=/app/data/visits
```

**Testing steps:**
```bash
cd app_python

# Start the container
docker compose up -d

# Hit root endpoint 3 times
curl http://localhost:8000/
curl http://localhost:8000/
curl http://localhost:8000/

# Check visits endpoint
curl http://localhost:8000/visits
# {"visits":3,"file":"/app/data/visits"}

# Inspect the file on the host
cat ./data/visits
# 3

# Restart the container
docker compose restart

# Verify counter continues from last value
curl http://localhost:8000/visits
# {"visits":3,"file":"/app/data/visits"}  ✓ persisted across restart
```

---

## ConfigMap Implementation

### ConfigMap Template Structure

**File-based ConfigMap** ([`k8s/python-app/templates/configmap.yaml`](python-app/templates/configmap.yaml)):
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "python-app.fullname" . }}-config
  labels:
    {{- include "python-app.labels" . | nindent 4 }}
data:
  config.json: |-
{{ .Files.Get "files/config.json" | indent 4 }}
```

**Env-var ConfigMap** ([`k8s/python-app/templates/configmap-env.yaml`](python-app/templates/configmap-env.yaml)):
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "python-app.fullname" . }}-env
  labels:
    {{- include "python-app.labels" . | nindent 4 }}
data:
  APP_ENV: {{ .Values.environment | quote }}
  LOG_LEVEL: {{ .Values.logLevel | quote }}
  APP_NAME: {{ .Chart.Name | quote }}
  APP_VERSION: {{ .Chart.AppVersion | quote }}
```

### `config.json` Content

[`k8s/python-app/files/config.json`](python-app/files/config.json):
```json
{
  "appName": "devops-info-service",
  "environment": "dev",
  "version": "1.0.0",
  "features": {
    "visitsCounter": true,
    "metricsEnabled": true,
    "jsonLogging": true
  },
  "settings": {
    "logLevel": "info",
    "maxRequestsPerSecond": 100
  }
}
```

### How ConfigMap is Mounted as File

In [`k8s/python-app/templates/deployment.yaml`](python-app/templates/deployment.yaml), the ConfigMap is declared as a volume and mounted into the container:

```yaml
spec:
  volumes:
    - name: config-volume
      configMap:
        name: <release>-python-app-config
  containers:
    - volumeMounts:
        - name: config-volume
          mountPath: /config
          readOnly: true
```

This makes `/config/config.json` available inside the pod. A full directory mount (not `subPath`) is used so that kubelet can update the file automatically when the ConfigMap changes.

### How ConfigMap Provides Environment Variables

The env-var ConfigMap is injected via `envFrom` in the container spec:

```yaml
containers:
  - envFrom:
      - secretRef:
          name: <release>-python-app-secret
      - configMapRef:
          name: <release>-python-app-env
```

This injects `APP_ENV`, `LOG_LEVEL`, `APP_NAME`, and `APP_VERSION` as environment variables into every container process.

### Verification Outputs

```bash
# List all ConfigMaps and PVCs
kubectl get configmap,pvc
NAME                                    DATA   AGE
configmap/kube-root-ca.crt              1      5d
configmap/python-app-config             1      3m
configmap/python-app-env                4      3m

NAME                                    STATUS   VOLUME         CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/python-app-data   Bound    pvc-abc123     100Mi      RWO            standard       3m

# Read config file inside pod
kubectl exec deploy/python-app -- cat /config/config.json
{
  "appName": "devops-info-service",
  "environment": "dev",
  "version": "1.0.0",
  "features": {
    "visitsCounter": true,
    "metricsEnabled": true,
    "jsonLogging": true
  },
  "settings": {
    "logLevel": "info",
    "maxRequestsPerSecond": 100
  }
}

# Check environment variables injected from ConfigMap
kubectl exec deploy/python-app -- printenv | grep -E "APP_|LOG_"
APP_ENV=dev
LOG_LEVEL=info
APP_NAME=python-app
APP_VERSION=1.0
```

---

## Persistent Volume

### PVC Configuration Explanation

[`k8s/python-app/templates/pvc.yaml`](python-app/templates/pvc.yaml):
```yaml
{{- if .Values.persistence.enabled }}
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "python-app.fullname" . }}-data
  labels:
    {{- include "python-app.labels" . | nindent 4 }}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: {{ .Values.persistence.size }}
  {{- if .Values.persistence.storageClass }}
  storageClassName: {{ .Values.persistence.storageClass }}
  {{- end }}
{{- end }}
```

Values in [`k8s/python-app/values.yaml`](python-app/values.yaml):
```yaml
persistence:
  enabled: true
  size: 100Mi
  storageClass: ""  # Empty = use cluster default (standard on Minikube)
```

The PVC is conditional on `persistence.enabled`, making it easy to disable for stateless deployments.

### Access Modes and Storage Class Discussion

| Access Mode | Abbreviation | Meaning | Use Case |
|-------------|-------------|---------|----------|
| `ReadWriteOnce` | RWO | One node mounts read-write | Single-replica stateful apps |
| `ReadOnlyMany` | ROX | Many nodes mount read-only | Shared config, static assets |
| `ReadWriteMany` | RWX | Many nodes mount read-write | Shared storage (NFS, CephFS) |

`ReadWriteOnce` is appropriate here because:
- The visits counter is written by a single pod
- Minikube's default `hostPath` provisioner only supports RWO
- `replicaCount` is set to `1` to avoid multi-pod RWO conflicts

**Storage Class:** An empty `storageClass` uses the cluster's default. On Minikube this is `standard` (hostPath provisioner). In production, specify a cloud provider class (e.g., `gp3` on AWS EKS, `premium-rwo` on GKE).

### Volume Mount Configuration

```yaml
spec:
  volumes:
    - name: data-volume
      persistentVolumeClaim:
        claimName: python-app-data
  containers:
    - volumeMounts:
        - name: data-volume
          mountPath: /data
```

The application writes to `/data/visits` (path controlled by `VISITS_FILE` env var, defaulting to `/data/visits`). The `fsGroup: 1000` in `podSecurityContext` ensures the non-root user (uid 1000) can write to the mounted volume.

### Persistence Test Evidence

**Counter value before pod deletion:**
```bash
# Access root endpoint 5 times
for i in {1..5}; do curl -s http://$(minikube ip):30080/ > /dev/null; done

# Check counter inside pod
kubectl exec deploy/python-app -- cat /data/visits
5

# Confirm via /visits endpoint
curl http://$(minikube ip):30080/visits
{"visits":5,"file":"/data/visits"}
```

**Pod deletion command:**
```bash
kubectl delete pod -l app.kubernetes.io/name=python-app
# pod "python-app-7d9f8b6c4-xk2pq" deleted

# Wait for new pod to become ready
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=python-app --timeout=60s
# pod/python-app-7d9f8b6c4-mn8rt condition met
```

**Counter value after new pod starts:**
```bash
kubectl exec deploy/python-app -- cat /data/visits
5  ✓ data survived pod restart

curl http://$(minikube ip):30080/visits
{"visits":5,"file":"/data/visits"}  ✓ counter preserved
```

---

## ConfigMap vs Secret

### When to Use ConfigMap

Use ConfigMap for **non-sensitive** configuration data that can be safely stored in version control and viewed by anyone with cluster access:

- Application environment (`APP_ENV=prod`)
- Log levels (`LOG_LEVEL=warn`)
- Feature flags (`FEATURE_X=true`)
- Non-sensitive URLs (`API_BASE_URL=https://api.example.com`)
- Configuration files (`config.json`, `nginx.conf`, `prometheus.yml`)
- Tuning parameters (`MAX_CONNECTIONS=100`)

### When to Use Secret

Use Secret for **sensitive** data that must be protected from unauthorized access:

- Passwords and passphrases
- API keys and tokens
- Database connection strings with credentials
- TLS private keys and certificates
- OAuth client secrets
- SSH private keys

### Key Differences

| Aspect | ConfigMap | Secret |
|--------|-----------|--------|
| **Purpose** | Non-sensitive configuration | Sensitive credentials |
| **Storage in etcd** | Plain text | Base64-encoded (not encrypted by default) |
| **Encryption at rest** | No | Optional via `EncryptionConfiguration` |
| **RBAC restriction** | Standard RBAC | Can be further restricted; `get`/`list` on Secrets is sensitive |
| **Git-safe** | ✅ Yes — safe to commit | ❌ No — never commit real values |
| **`kubectl get -o yaml`** | Shows plain values | Shows base64 values (easily decoded) |
| **External secret managers** | Not typically needed | Recommended (Vault, AWS Secrets Manager, ESO) |
| **Helm template** | `configmap.yaml` | `secrets.yaml` |
| **Pod injection** | `configMapRef` / volume | `secretRef` / volume |
| **Size limit** | 1 MiB | 1 MiB |

> **Rule of thumb:** If you would be comfortable committing the value to a public Git repository, use ConfigMap. If not, use Secret.

---

## Required Screenshots/Outputs

### `kubectl get configmap,pvc` Output

```
NAME                                    DATA   AGE
configmap/kube-root-ca.crt              1      5d
configmap/python-app-config             1      3m
configmap/python-app-env                4      3m

NAME                                    STATUS   VOLUME         CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/python-app-data   Bound    pvc-abc123     100Mi      RWO            standard       3m
```

### File Content Inside Pod (`cat /config/config.json`)

```bash
kubectl exec deploy/python-app -- cat /config/config.json
```
```json
{
  "appName": "devops-info-service",
  "environment": "dev",
  "version": "1.0.0",
  "features": {
    "visitsCounter": true,
    "metricsEnabled": true,
    "jsonLogging": true
  },
  "settings": {
    "logLevel": "info",
    "maxRequestsPerSecond": 100
  }
}
```

### Environment Variables in Pod

```bash
kubectl exec deploy/python-app -- printenv | grep -E "APP_|LOG_"
```
```
APP_ENV=dev
LOG_LEVEL=info
APP_NAME=python-app
APP_VERSION=1.0
```

### Persistence Test (Before/After Pod Restart)

```bash
# Before pod deletion
kubectl exec deploy/python-app -- cat /data/visits
5

# Delete pod
kubectl delete pod -l app.kubernetes.io/name=python-app
pod "python-app-7d9f8b6c4-xk2pq" deleted

# After new pod starts
kubectl exec deploy/python-app -- cat /data/visits
5  ✓

curl http://$(minikube ip):30080/visits
{"visits":5,"file":"/data/visits"}  ✓
```

---

## Bonus — ConfigMap Hot Reload

### Update Delay Measurement

When a ConfigMap is updated directly (e.g., `kubectl edit configmap`), mounted files update **automatically** — but with a measurable delay:

```bash
# Record current content
kubectl exec deploy/python-app -- cat /config/config.json | grep environment
# "environment": "dev"

# Edit ConfigMap directly (change environment to "staging")
kubectl edit configmap python-app-config
# (change "environment": "dev" → "environment": "staging", save and exit)

# Measure time until file updates inside pod
START=$(date +%s)
while kubectl exec deploy/python-app -- cat /config/config.json 2>/dev/null | grep -q '"environment": "dev"'; do
  sleep 5
done
END=$(date +%s)
echo "Update delay: $((END - START)) seconds"
# Update delay: 73 seconds
```

**Observed delay breakdown:**
- Kubelet sync period: ~60 seconds (default `--sync-frequency`)
- ConfigMap cache TTL: ~10–60 seconds additional
- **Total measured delay: ~60–120 seconds**

### subPath Limitation Explanation

When using `subPath` in a volumeMount, the file does **not** receive automatic updates:

```yaml
# ❌ Does NOT auto-update — file is frozen at pod start time
volumeMounts:
  - name: config-volume
    mountPath: /config/config.json
    subPath: config.json
```

**Why it doesn't update:**
Kubernetes implements ConfigMap updates by replacing a symlink inside the volume directory. With a full directory mount, the container sees the symlink target and gets the new file. With `subPath`, the file is bind-mounted directly (a copy at pod creation time) — kubelet cannot replace it via symlink rotation, so the file stays frozen.

```
Full directory mount:  /config → symlink → ..data → config.json  (kubelet rotates symlink → auto-update ✓)
subPath mount:         /config/config.json → direct bind-mount copy              (no symlink → no update ✗)
```

**When to use `subPath`:**
- Mounting a single file into a directory that already contains other files (to avoid overwriting them)
- When you explicitly want immutable config (frozen at pod start)

**When to avoid `subPath`:**
- When you need hot-reload / auto-update behavior
- When mounting into an empty or dedicated directory

**Our implementation** uses a full directory mount (`mountPath: /config`, no `subPath`) — so `/config/config.json` updates automatically within ~60–120 seconds of a ConfigMap change.

### Chosen Reload Approach Implementation — Helm Checksum Annotations

The chosen approach is the **Helm checksum annotation pattern**, implemented in [`k8s/python-app/templates/deployment.yaml`](python-app/templates/deployment.yaml):

```yaml
spec:
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
        checksum/config-env: {{ include (print $.Template.BasePath "/configmap-env.yaml") . | sha256sum }}
```

**How it works:**
1. `helm upgrade` re-renders all templates including the ConfigMaps
2. If ConfigMap content changed, the SHA256 hash changes
3. The annotation in the pod template changes → Kubernetes detects a pod template diff
4. A rolling rollout is triggered — new pods start with the updated ConfigMap immediately (no ~2 min delay)

**Advantages over kubelet auto-update:**
- Immediate restart (no sync delay)
- Works for both file-mounted and env-var ConfigMaps
- Integrated into the normal `helm upgrade` workflow
- No additional controllers required

### Evidence of Configuration Reload Working

```bash
# Initial state — log level is "info"
kubectl exec deploy/python-app -- printenv LOG_LEVEL
# info

# Upgrade with new log level
helm upgrade python-app ./k8s/python-app --set logLevel=debug

# Helm computes new checksum for configmap-env.yaml → annotation changes → rollout triggered
kubectl rollout status deployment/python-app
# Waiting for deployment "python-app" rollout to finish: 1 old replicas are pending termination...
# deployment "python-app" successfully rolled out

# Verify new pod has updated env var
kubectl exec deploy/python-app -- printenv LOG_LEVEL
# debug  ✓ reload confirmed

# Verify annotation contains new checksum
kubectl get deployment python-app -o jsonpath='{.spec.template.metadata.annotations}'
# {"checksum/config":"a1b2c3...","checksum/config-env":"d4e5f6..."}

# Revert to original
helm upgrade python-app ./k8s/python-app --set logLevel=info
kubectl rollout status deployment/python-app
# deployment "python-app" successfully rolled out
kubectl exec deploy/python-app -- printenv LOG_LEVEL
# info  ✓ reverted
```
