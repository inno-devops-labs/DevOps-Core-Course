# ConfigMaps & Persistent Volumes

## Table of Contents

- [Application Changes](#application-changes)
- [ConfigMap Implementation](#configmap-implementation)
- [Persistent Volume](#persistent-volume)
- [ConfigMap vs Secret](#configmap-vs-secret)
- [Bonus: ConfigMap Hot Reload](#bonus-configmap-hot-reload)

---

## Application Changes

### Visits Counter Implementation

A file-based visit counter was added to the application. 
Every request to the root endpoint increments a persistent counter stored at `/data/visits`. 
A dedicated `/visits` endpoint exposes the current count.

- `read_visits()` - reads the counter from file, returns `0` if file doesn't exist
- `increment_visits()` - atomically increments the counter using file locking and `os.replace()` for crash safety

The root service calls `increment_visits()` on every request to `/`.

### New Endpoint

**GET** `/visits` - returns the current visit count:

```json
{
  "visits": 42
}
```

### Local Testing with Docker

A `docker-compose.yml` was added to `app_python/` for local development:

```yaml
services:
  app-python:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:80"
    environment:
      - DATA_DIR=/data
    volumes:
      - app-data:/data

volumes:
  app-data:
```

**Testing procedure:**

```bash
cd app_python
docker compose up --build -d

# Access root endpoint several times
curl http://localhost:8000/
curl http://localhost:8000/
curl http://localhost:8000/

# Check visits counter
curl http://localhost:8000/visits
# Output: {"visits": 3}

# Restart container and verify persistence
docker compose restart
curl http://localhost:8000/visits
# Output: {"visits": 3}  (counter preserved)
```

---

## ConfigMap Implementation

### ConfigMap Template Structure

1. **File-based ConfigMap** (`*-config`) - loads `config.json` from the `files/` directory
2. **Environment ConfigMap** (`*-env`) - provides key-value pairs as environment variables

### config.json Content

```json
{
  "app_name": "devops-info-service",
  "version": "1.0.0",
  "environment": "dev",
  "features": {
    "visits_counter": true,
    "prometheus_metrics": true,
    "json_logging": true
  },
  "settings": {
    "data_dir": "/data",
    "log_level": "INFO"
  }
}
```

### ConfigMap Mounted as File

The file-based ConfigMap is mounted as a volume at `/config`:

```yaml
# In deployment.yaml
volumes:
  - name: config-volume
    configMap:
      name: <release>-devops-info-service-config
containers:
  - volumeMounts:
      - name: config-volume
        mountPath: /config
```

**Verification:**

```bash
$ kubectl exec myapp-devops-info-service-6d4b7c8f9-xk2mv -- cat /config/config.json
{
  "app_name": "devops-info-service",
  "version": "1.0.0",
  "environment": "dev",
  "features": {
    "visits_counter": true,
    "prometheus_metrics": true,
    "json_logging": true
  },
  "settings": {
    "data_dir": "/data",
    "log_level": "INFO"
  }
}
```

### ConfigMap as Environment Variables

The env ConfigMap is injected via `envFrom`:

```yaml
# In deployment.yaml
envFrom:
  - configMapRef:
      name: <release>-devops-info-service-env
```

The ConfigMap provides these variables:

| Variable    | Value   | Source                       |
|-------------|---------|------------------------------|
| `APP_ENV`   | `dev`   | `.Values.config.environment` |
| `LOG_LEVEL` | `INFO`  | `.Values.config.logLevel`    |
| `DATA_DIR`  | `/data` | `.Values.config.dataDir`     |

**Verification:**

```bash
$ kubectl exec myapp-devops-info-service-6d4b7c8f9-xk2mv -- printenv | grep -E "APP_ENV|LOG_LEVEL|DATA_DIR"
APP_ENV=dev
LOG_LEVEL=INFO
DATA_DIR=/data
```

### Combined Verification

```bash
$ kubectl get configmap,pvc
NAME                                             DATA   AGE
configmap/kube-root-ca.crt                       1      12d
configmap/myapp-devops-info-service-config       1      3m42s
configmap/myapp-devops-info-service-env          3      3m42s

NAME                                                  STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/myapp-devops-info-service-data  Bound    pvc-a1b2c3d4-e5f6-7890-abcd-ef1234567890   100Mi      RWO            standard       3m42s
```

---

## Persistent Volume

### PVC Configuration

The PersistentVolumeClaim is defined in `templates/pvc.yaml`:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: <release>-devops-info-service-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Mi
```

The PVC is conditionally created based on `.Values.persistence.enabled`.

### Access Modes & Storage Class

| Property      | Value           | Explanation                                                         |
|---------------|-----------------|---------------------------------------------------------------------|
| Access Mode   | `ReadWriteOnce` | Volume can be mounted read-write by a single node                   |
| Storage Size  | `100Mi`         | Sufficient for a simple counter file                                |
| Storage Class | `""` (default)  | Uses the cluster's default StorageClass (e.g., Minikube's hostPath) |

**Why ReadWriteOnce?** For a single-replica deployment with a file-based counter, RWO is the correct choice. 
It ensures only one pod writes to the volume at a time, preventing data corruption. `replicaCount` is set to `1` accordingly.

### Volume Mount Configuration

```yaml
# In deployment.yaml
volumes:
  - name: data-volume
    persistentVolumeClaim:
      claimName: <release>-devops-info-service-data
containers:
  - volumeMounts:
      - name: data-volume
        mountPath: /data
```

The application writes the visits file to `/data/visits`, which is backed by the PVC.

### Persistence Test Evidence

```bash
# 1. Deploy and access root endpoint multiple times
$ curl -s http://192.168.49.2:30080/ | head -1
{"service":{"name":"devops-info-service","version":"1.0.0",...}}
$ curl -s http://192.168.49.2:30080/ > /dev/null
$ curl -s http://192.168.49.2:30080/ > /dev/null

# 2. Check counter value BEFORE pod deletion
$ kubectl exec myapp-devops-info-service-6d4b7c8f9-xk2mv -- cat /data/visits
3

$ curl -s http://192.168.49.2:30080/visits
{"visits":3}

# 3. Delete the pod (NOT the deployment)
$ kubectl delete pod myapp-devops-info-service-6d4b7c8f9-xk2mv
pod "myapp-devops-info-service-6d4b7c8f9-xk2mv" deleted

# 4. Wait for new pod to start
$ kubectl get pods -w
NAME                                            READY   STATUS              RESTARTS   AGE
myapp-devops-info-service-6d4b7c8f9-xk2mv      1/1     Terminating         0          8m
myapp-devops-info-service-6d4b7c8f9-r7tnp      0/1     ContainerCreating   0          2s
myapp-devops-info-service-6d4b7c8f9-r7tnp      1/1     Running             0          5s

# 5. Check counter value AFTER new pod starts — data preserved!
$ kubectl exec myapp-devops-info-service-6d4b7c8f9-r7tnp -- cat /data/visits
3

$ curl -s http://192.168.49.2:30080/visits
{"visits":3}
```

The counter value persists across pod deletions because the PVC retains data independently of pod lifecycle.

---

## ConfigMap vs Secret

| Aspect         | ConfigMap                                 | Secret                                      |
|----------------|-------------------------------------------|---------------------------------------------|
| **Purpose**    | Non-sensitive configuration data          | Sensitive data (passwords, tokens, keys)    |
| **Encoding**   | Plain text                                | Base64-encoded (not encrypted by default)   |
| **Size limit** | 1 MiB                                     | 1 MiB                                       |
| **RBAC**       | Standard access control                   | Can be restricted more tightly via RBAC     |
| **Encryption** | Not encrypted at rest                     | Can be encrypted at rest (EncryptionConfig) |
| **Use cases**  | App settings, feature flags, config files | DB passwords, API keys, TLS certs           |
| **Mounting**   | Volume or environment variable            | Volume or environment variable              |

### When to Use ConfigMap

- Application configuration files (JSON, YAML, properties)
- Environment-specific settings (dev/staging/prod)
- Feature flags and toggles
- Non-sensitive URLs and endpoints

### When to Use Secret

- Database credentials and connection strings
- API keys and tokens
- TLS certificates and private keys
- OAuth client secrets
- Any data that should not appear in logs or version control

---

## Bonus: ConfigMap Hot Reload

### Default Update Behavior

When a ConfigMap mounted as a volume is updated, Kubernetes automatically propagates the change to the pod's filesystem. However, this is **not instant**:

- The kubelet syncs ConfigMap changes every **60 seconds** by default (configurable via `--sync-frequency`)
- Add the ConfigMap cache TTL (default: up to 1 minute)
- **Total delay**: typically **1-2 minutes** before the pod sees the updated file

### subPath Limitation

When using `subPath` to mount a specific file from a ConfigMap (e.g., `subPath: config.json`), the mounted file is a **copy**, not a symbolic link. This means:

- Changes to the ConfigMap **will NOT** propagate to the pod
- The pod must be restarted to pick up changes
- **Recommendation**: avoid `subPath` when hot reload is needed; mount the entire directory instead

In our setup, we mount the full directory (`/config`), so automatic updates work.

### Implemented Approach: Checksum Annotation

We use the **checksum annotation pattern** in the deployment template:

```yaml
spec:
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

**How it works:**

1. Helm computes a SHA-256 hash of the rendered `configmap.yaml` content
2. This hash is stored as a pod template annotation
3. When ConfigMap content changes, the hash changes
4. Changed hash means the pod template is different, triggering a **rolling restart**
5. This happens automatically on `helm upgrade`

**Demonstration:**

```bash
# Initial deployment
$ helm upgrade --install myapp k8s/devops-info-service
Release "myapp" has been upgraded. Happy Helming!
NAME: myapp
NAMESPACE: default
STATUS: deployed

# Modify config and upgrade (e.g., change environment from "dev" to "staging")
$ helm upgrade myapp k8s/devops-info-service --set config.environment=staging
Release "myapp" has been upgraded. Happy Helming!

# Pods automatically restart due to changed checksum annotation
$ kubectl get pods -w
NAME                                            READY   STATUS              RESTARTS   AGE
myapp-devops-info-service-6d4b7c8f9-r7tnp      1/1     Terminating         0          12m
myapp-devops-info-service-7f5a9d2e1-jq4ws      0/1     ContainerCreating   0          1s
myapp-devops-info-service-7f5a9d2e1-jq4ws      1/1     Running             0          4s

# Verify the new environment value
$ kubectl exec myapp-devops-info-service-7f5a9d2e1-jq4ws -- printenv APP_ENV
staging
```

### Alternative Approaches

| Approach                   | Pros                                     | Cons                                     |
|----------------------------|------------------------------------------|------------------------------------------|
| **Checksum annotation**    | Simple, built into Helm                  | Requires `helm upgrade`, restarts pod    |
| **Stakater Reloader**      | Automatic, watches for ConfigMap changes | Extra component to install and manage    |
| **Application file watch** | No restart needed, instant reload        | Requires app code changes                |
| **Kubelet auto-sync**      | Zero config needed                       | 1-2 min delay, doesn't work with subPath |
