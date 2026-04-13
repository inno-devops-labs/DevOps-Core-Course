# Kubernetes ConfigMaps & Persistent Volumes

## Table of Contents

- [Application Changes](#1-application-changes)
- [ConfigMap Implementation](#2-configmap-implementation)
- [Persistent Volume](#3-persistent-volume)
- [ConfigMap vs Secret](#4-configmap-vs-secret)
- [Bonus: ConfigMap Hot Reload](#5-bonus-configmap-hot-reload)

---

## 1. Application Changes

### Visits Counter Implementation

The application was extended with a persistent visit counter. Every `GET /` request increments the counter stored in a file at `$DATA_DIR/visits` (default `/data/visits`). A new `GET /visits` endpoint returns the current count without incrementing.

**Key design decisions:**

- **Thread safety** — a `threading.Lock` guards all file reads and writes, preventing race conditions under concurrent requests.
- **Atomic writes** — the counter is written to a `.tmp` file first, then atomically moved with `os.replace()`, so a crash mid-write never corrupts the file.
- **Graceful fallback** — if the visits file doesn't exist on startup, the counter defaults to 0.

### New Endpoint

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/visits` | GET | Returns `{"visits": <int>}` — current counter value |

The root endpoint (`/`) now also includes a `visits` field in its response.

### Local Testing with Docker

```bash
cd monitoring
docker compose up --build -d

# Hit the root endpoint a few times
curl http://localhost:8000/
curl http://localhost:8000/
curl http://localhost:8000/

# Check the counter
curl http://localhost:8000/visits
```

```json
{"visits": 3}
```

```bash
# Restart the container — counter persists
docker compose restart app-python
curl http://localhost:8000/visits
```

```json
{"visits": 3}
```

The `docker-compose.yml` mounts a named volume for each app instance:

```yaml
volumes:
  - app-python-data:/data
```

---

## 2. ConfigMap Implementation

### Chart Structure

```
devops-app/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
├── files/
│   └── config.json              # ← application configuration file
├── templates/
│   ├── _helpers.tpl
│   ├── configmap.yaml           # ← NEW: two ConfigMaps
│   ├── deployment.yaml          # updated with volumeMounts & envFrom
│   ├── pvc.yaml                 # ← NEW: PersistentVolumeClaim
│   ├── secrets.yaml
│   ├── service.yaml
│   ├── serviceaccount.yaml
│   ├── NOTES.txt
│   └── hooks/
│       ├── pre-install-job.yaml
│       └── post-install-job.yaml
```

### ConfigMap from File (`config.json`)

The file `files/config.json` contains application settings:

```json
{
  "app_name": "devops-app",
  "environment": "default",
  "features": {
    "visits_counter": true,
    "prometheus_metrics": true,
    "json_logging": true
  },
  "server": {
    "graceful_shutdown_timeout": 30,
    "max_request_size": 1048576
  }
}
```

The first ConfigMap in `templates/configmap.yaml` loads this file using `.Files.Get`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "devops-app.fullname" . }}-config
data:
  config.json: |-
{{ .Files.Get "files/config.json" | indent 4 }}
```

### ConfigMap for Environment Variables

The second ConfigMap iterates over `.Values.configMap` to produce key-value pairs:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "devops-app.fullname" . }}-env
data:
  APP_ENV: "default"
  LOG_LEVEL: "info"
  FEATURES_VISITS: "true"
```

Values defined in `values.yaml`:

```yaml
configMap:
  APP_ENV: "default"
  LOG_LEVEL: "info"
  FEATURES_VISITS: "true"
```

### How ConfigMap Is Mounted as a File

The deployment mounts the file-based ConfigMap as a volume at `/config`:

```yaml
volumes:
  - name: config-volume
    configMap:
      name: {{ include "devops-app.fullname" . }}-config
containers:
  - volumeMounts:
      - name: config-volume
        mountPath: /config
        readOnly: true
```

### How ConfigMap Provides Environment Variables

The deployment uses `envFrom` with `configMapRef`:

```yaml
envFrom:
  - secretRef:
      name: {{ include "devops-app.fullname" . }}-secret
  - configMapRef:
      name: {{ include "devops-app.fullname" . }}-env
```

This injects all keys (`APP_ENV`, `LOG_LEVEL`, `FEATURES_VISITS`) as environment variables.

### Verification

```bash
# Deploy the chart
helm upgrade --install devops-app ./k8s/devops-app

# Check ConfigMaps
kubectl get configmap
```

```
NAME                      DATA   AGE
devops-app-config         1      30s
devops-app-env            3      30s
```

```bash
# Verify file mount
kubectl exec -it deploy/devops-app -- cat /config/config.json
```

```json
{
  "app_name": "devops-app",
  "environment": "default",
  "features": {
    "visits_counter": true,
    "prometheus_metrics": true,
    "json_logging": true
  },
  "server": {
    "graceful_shutdown_timeout": 30,
    "max_request_size": 1048576
  }
}
```

```bash
# Verify environment variables
kubectl exec -it deploy/devops-app -- env | grep -E 'APP_ENV|LOG_LEVEL|FEATURES'
```

```
APP_ENV=default
LOG_LEVEL=info
FEATURES_VISITS=true
```

---

## 3. Persistent Volume

### PVC Configuration

`templates/pvc.yaml` creates a PersistentVolumeClaim when `persistence.enabled` is `true`:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "devops-app.fullname" . }}-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Mi
```

### Access Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `ReadWriteOnce` (RWO) | Single node can mount read-write | Single-replica deployments, databases |
| `ReadOnlyMany` (ROX) | Many nodes can mount read-only | Shared config, static assets |
| `ReadWriteMany` (RWX) | Many nodes can mount read-write | Shared storage (NFS, CephFS) |

We use `ReadWriteOnce` because the visits counter file is written by a single pod.

### Storage Class

The `storageClass` is left empty (`""`) to use the cluster default. On Minikube this provisions `hostPath` volumes automatically.

| Environment | Storage Size |
|-------------|-------------|
| **dev** | 50Mi |
| **default** | 100Mi |
| **prod** | 1Gi |

### Volume Mount Configuration

The deployment mounts the PVC at `/data`:

```yaml
volumes:
  - name: data-volume
    persistentVolumeClaim:
      claimName: {{ include "devops-app.fullname" . }}-data
containers:
  - volumeMounts:
      - name: data-volume
        mountPath: /data
```

The application writes the visits counter to `/data/visits`, which now persists on the PVC.

### Persistence Test

```bash
# Deploy
helm upgrade --install devops-app ./k8s/devops-app

# Check PVC is bound
kubectl get pvc
```

```
NAME               STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
devops-app-data    Bound    pvc-a1b2c3d4-e5f6-7890-abcd-ef1234567890   100Mi      RWO            standard       45s
```

```bash
# Access the app multiple times
curl http://<node-ip>:30080/
curl http://<node-ip>:30080/
curl http://<node-ip>:30080/

# Check counter before pod deletion
kubectl exec -it deploy/devops-app -- cat /data/visits
```

```
3
```

```bash
# Delete the pod (NOT the deployment)
kubectl delete pod -l app.kubernetes.io/name=devops-app
```

```
pod "devops-app-6f7b8c9d-x2k4m" deleted
```

```bash
# Wait for new pod, then verify counter is preserved
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=devops-app --timeout=60s
kubectl exec -it deploy/devops-app -- cat /data/visits
```

```
3
```

The counter survived the pod deletion because the data lives on the PersistentVolume, not inside the container's ephemeral filesystem.

---

## 4. ConfigMap vs Secret

| Aspect | ConfigMap | Secret |
|--------|-----------|--------|
| **Purpose** | Non-sensitive configuration data | Sensitive data (passwords, tokens, keys) |
| **Storage** | Plaintext in etcd | Base64-encoded in etcd (optionally encrypted at rest) |
| **Size limit** | 1 MiB | 1 MiB |
| **Mounting** | Volume or env vars | Volume or env vars |
| **Access control** | Standard RBAC | Stricter RBAC recommended |
| **Example data** | App config, feature flags, log levels | DB passwords, API keys, TLS certs |

### When to Use ConfigMap

- Application configuration files (JSON, YAML, properties)
- Feature flags and environment settings
- Non-sensitive key-value pairs (log levels, service URLs)
- Configuration that may change between environments

### When to Use Secret

- Database credentials and connection strings
- API keys and authentication tokens
- TLS certificates and private keys
- Any data that would be a security risk if exposed

### Key Differences

1. **Encoding** — Secrets are base64-encoded; ConfigMaps store plaintext.
2. **`kubectl get`** — Secret values are masked in describe output; ConfigMap values are visible.
3. **tmpfs** — Secrets mounted as volumes use in-memory `tmpfs` by default; ConfigMaps do not.
4. **RBAC** — Best practice is to restrict Secret access more tightly than ConfigMap access.

---

## 5. Bonus: ConfigMap Hot Reload

### Checksum Annotation Pattern

The deployment includes a checksum annotation that triggers a rolling restart whenever the ConfigMap content changes:

```yaml
metadata:
  annotations:
    checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

When `helm upgrade` is run and the ConfigMap template renders differently (e.g., a value in `values.yaml` changed), the checksum changes, which updates the pod template spec and triggers a new rollout.

### Update Delay Measurement

Without the checksum pattern, mounted ConfigMap updates rely on the kubelet sync loop:

| Component | Default Interval |
|-----------|-----------------|
| kubelet sync | 60 seconds |
| ConfigMap cache TTL | 60 seconds |
| **Total worst-case delay** | **~2 minutes** |

The checksum annotation bypasses this entirely by forcing a pod restart on `helm upgrade`.

### subPath Limitation

When a ConfigMap is mounted with `subPath` (mounting a single file into an existing directory), the file is a **static copy**, not a symlink:

```yaml
# This does NOT receive automatic updates:
volumeMounts:
  - name: config-volume
    mountPath: /app/config.json
    subPath: config.json
```

```yaml
# This DOES receive automatic updates (full directory mount):
volumeMounts:
  - name: config-volume
    mountPath: /config
```

We use the full directory mount (`/config`) to preserve auto-update capability.

### Alternative Reload Approaches

| Approach | How It Works | Pros | Cons |
|----------|-------------|------|------|
| **Checksum annotation** (implemented) | Pod restart on config change | Simple, no extra components | Causes pod restart |
| **Stakater Reloader** | Controller watches ConfigMaps, triggers rollouts | Automatic, no Helm needed | Extra deployment to manage |
| **Application file watcher** | App watches `/config` for changes | No restart, instant reload | Requires app-level code |
| **SIGHUP handler** | External signal triggers config reload | Standard UNIX pattern | Requires orchestration to send signal |
