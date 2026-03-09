# ConfigMaps & Persistent Volumes — Lab 12

## 1. Application Changes

### Visits Counter

The root endpoint (`GET /`) now tracks how many times it has been called.
The counter is persisted in a plain-text file whose path is controlled by the
`VISITS_FILE` environment variable (default: `/data/visits`).

**New endpoint:**

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/visits` | Returns `{"visits": <count>}` without incrementing the counter |

**Implementation details (`app_python/app.py`):**

```python
VISITS_FILE: str = os.getenv("VISITS_FILE", "/data/visits")

def _read_visits() -> int:
    try:
        with open(VISITS_FILE, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0

def _increment_visits() -> int:
    os.makedirs(os.path.dirname(VISITS_FILE), exist_ok=True)
    with open(VISITS_FILE, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)   # exclusive lock → thread-safe
        ...
```

File locking (`fcntl`) prevents race conditions when multiple concurrent
requests try to update the counter simultaneously.

### Local Testing with Docker Compose

```bash
cd app_python
docker compose up --build -d

# Hit the root endpoint several times
curl http://localhost:5000/
curl http://localhost:5000/
curl http://localhost:5000/

# Check the counter
curl http://localhost:5000/visits
# {"visits":3}

# Restart the container — counter must survive
docker compose restart
curl http://localhost:5000/visits
# {"visits":3}   ← same value
```

The named Docker volume `visits_data` is mounted at `/data`.

---

## 2. ConfigMap Implementation

### a) File-based ConfigMap (`configmap.yaml`)

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: <release>-devops-info-chart-config
data:
  config.json: |-
    {
      "app_name": "devops-info-service",
      "environment": "production",
      "features": { "visits_counter": true, ... }
    }
```

The content of `files/config.json` is embedded at chart render time using
`.Files.Get`. It is mounted as a read-only file at `/config/config.json` inside
every pod.

### b) Environment-variable ConfigMap (`configmap-env.yaml`)

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: <release>-devops-info-chart-env
data:
  APP_ENV: "production"
  LOG_LEVEL: "info"
  VISITS_FILE: "/data/visits"
```

Values come from `values.yaml` (`appEnv`, `logLevel`, `persistence.visitsFile`).

### c) Volume mount for config file (in `deployment.yaml`)

```yaml
# pod spec
volumes:
  - name: config-volume
    configMap:
      name: <release>-devops-info-chart-config

# container spec
volumeMounts:
  - name: config-volume
    mountPath: /config
```

### d) Environment variables via `envFrom`

```yaml
envFrom:
  - secretRef:
      name: <release>-secret
  - configMapRef:
      name: <release>-devops-info-chart-env
```

All keys from the env ConfigMap are injected as environment variables
(e.g. `APP_ENV`, `LOG_LEVEL`, `VISITS_FILE`).

### Verification

```bash
# File content inside pod
kubectl exec <pod> -- cat /config/config.json
# {
#   "app_name": "devops-info-service",
#   ...
# }

# Environment variables
kubectl exec <pod> -- printenv | grep -E "APP_ENV|LOG_LEVEL|VISITS_FILE"
# APP_ENV=production
# LOG_LEVEL=info
# VISITS_FILE=/data/visits

# List ConfigMaps and PVC
kubectl get configmap,pvc
# NAME                                       DATA   AGE
# configmap/dev-devops-info-chart-config     1      2m
# configmap/dev-devops-info-chart-env        3      2m
# NAME                                           STATUS   VOLUME   CAPACITY   ACCESS MODES
# persistentvolumeclaim/dev-devops-info-chart-data   Bound    ...      100Mi      RWO
```

---

## 3. Persistent Volume

### PVC Template (`pvc.yaml`)

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: <release>-devops-info-chart-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Mi
```

Controlled by:

```yaml
# values.yaml
persistence:
  enabled: true
  size: 100Mi
  storageClass: ""   # empty → cluster default (standard on Minikube)
```

**Access mode `ReadWriteOnce`** — the volume can be mounted by a single node at
a time. Sufficient for a single-replica deployment; use `ReadWriteMany` if you
need multi-pod writes.

**Storage class** — leaving `storageClass` empty uses the cluster's default
class. On Minikube this is `standard` (hostPath provisioner). In cloud
environments (GKE, EKS, AKS) the default class is backed by cloud block storage.

### Volume mount (in `deployment.yaml`)

```yaml
volumes:
  - name: data-volume
    persistentVolumeClaim:
      claimName: <release>-devops-info-chart-data

volumeMounts:
  - name: data-volume
    mountPath: /data
```

### Persistence Test

```bash
# 1. Deploy
helm upgrade --install dev k8s/devops-info-chart -f k8s/devops-info-chart/values-dev.yaml

# 2. Hit the endpoint multiple times
for i in $(seq 1 5); do curl -s $(minikube service dev-devops-info-chart --url)/; done

# 3. Check counter
kubectl exec <pod> -- cat /data/visits
# 5

# 4. Delete the pod
kubectl delete pod <pod>
# pod deleted — Deployment immediately creates a new one

# 5. Wait for the new pod
kubectl rollout status deployment/<deployment>

# 6. Verify counter is preserved
kubectl exec <new-pod> -- cat /data/visits
# 5   ← data survived the pod deletion
```

---

## 4. ConfigMap vs Secret

| | ConfigMap | Secret |
|---|---|---|
| **Purpose** | Non-sensitive application configuration | Sensitive credentials and tokens |
| **Storage at rest** | Stored as plain text in etcd | Base64-encoded in etcd (encrypted if etcd encryption is configured) |
| **Access** | Any pod in the namespace by default | Can be restricted via RBAC |
| **Typical content** | Feature flags, environment names, file-based config, log levels | Passwords, API keys, TLS certificates, SSH private keys |
| **Visible in `kubectl get`** | Yes, fully readable | Yes, but values are base64-encoded |
| **Use when** | Data is safe to expose to all team members / developers | Data must be restricted; values are secret |

**Rule of thumb:** if you would be comfortable putting the value in a public Git
repository, use a ConfigMap. If not, use a Secret (and ideally back it with an
external secret manager such as HashiCorp Vault or AWS Secrets Manager).

---

## 5. Bonus — ConfigMap Hot Reload

### Checksum Annotation Pattern

```yaml
# deployment.yaml — pod template metadata
annotations:
  checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
  checksum/config-env: {{ include (print $.Template.BasePath "/configmap-env.yaml") . | sha256sum }}
```

When `helm upgrade` is run after changing a ConfigMap, the SHA-256 checksums in
the pod template annotations change. Kubernetes sees this as a pod template
change and performs a rolling restart, ensuring pods always run with the latest
configuration.

### Update Delay

Without the checksum annotation, changes to a mounted ConfigMap propagate after
the kubelet's sync period (default **60 s**) plus the kube-apiserver watch
cache TTL. Total observed delay is typically **1–3 minutes**.

### `subPath` Limitation

When a ConfigMap key is mounted using `subPath`, Kubernetes copies the file at
pod start time instead of creating a symlink into the ConfigMap directory.
Because there is no symlink, kubelet cannot replace the file atomically, so
**updates to the ConfigMap are never reflected in the mounted file** while the
pod is running.

Use full directory mounts (without `subPath`) when you need automatic updates.
Use `subPath` only when you need to inject a single file without overwriting
other files in the same directory.

### stakater/Reloader (alternative approach)

`Reloader` is a Kubernetes controller that watches ConfigMaps and Secrets and
automatically triggers rolling restarts of Deployments/DaemonSets/StatefulSets
when they change — without requiring annotation churn.

```bash
helm repo add stakater https://stakater.github.io/stakater-charts
helm install reloader stakater/reloader -n kube-system

# Annotate the deployment
kubectl annotate deployment <name> reloader.stakater.com/auto="true"
```

With this in place, any `kubectl edit configmap ...` or `helm upgrade` that
changes a ConfigMap referenced by the deployment will automatically trigger a
rolling restart.
