# ConfigMaps & Persistent Volumes Implementation

## Application Changes

### Visits Counter Implementation
Added a file-based visits counter to the application that:
- Reads the counter from `/data/visits` on each root endpoint access
- Increments the counter and persists it back to the file
- Returns the current count via the new `/visits` endpoint
- Handles file creation and missing files gracefully

**New Endpoint:**
- `GET /visits` - Returns current visit count and timestamp

**Key Functions:**
- `get_visits_count()` - Reads current counter from file (defaults to 0)
- `increment_visits()` - Increments counter and writes back to file
- `/data` directory is created automatically if missing

**Local Testing with Docker Compose:**
```bash
# Build and start the container with volume mount
docker-compose up

# Access root endpoint to increment counter
curl http://localhost:8000/

# Check visits count
curl http://localhost:8000/visits

# Verify file on host
cat ./data/visits

# Restart container and verify counter persists
docker-compose restart
curl http://localhost:8000/visits
```

---

## ConfigMap Implementation

### Configuration Files

**`files/config.json`** - Application configuration stored as ConfigMap data:
```json
{
  "appName": "devops-info-service",
  "environment": "dev",
  "logLevel": "INFO",
  "features": {
    "metricsEnabled": true,
    "cachingEnabled": true,
    "debugMode": false
  }
}
```

### ConfigMap Templates

**`templates/configmap.yaml`** creates two ConfigMaps:

1. **File-based ConfigMap** - Mounts `config.json`:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-python-config
data:
  config.json: |-
    <content from files/config.json>
```

2. **Environment Variable ConfigMap** - Provides env vars:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-python-env
data:
  APP_ENV: "dev"
  LOG_LEVEL: "INFO"
```

### ConfigMap Mounting

**In Deployment:**
- ConfigMap mounted as volume at `/config`
- Environment variables injected via `envFrom` with `configMapRef`

**Verification:**
```bash
# View config file inside pod
kubectl exec <pod> -- cat /config/config.json

# View environment variables
kubectl exec <pod> -- env | grep -E "APP_|LOG_"

# List all ConfigMaps
kubectl get configmap
```

---

## Persistent Volume Implementation

### PersistentVolumeClaim

**`templates/pvc.yaml`** creates:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-python-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Mi
```

### Configuration in `values.yaml`
```yaml
persistence:
  enabled: true
  size: "100Mi"
  storageClass: ""  # Uses default storage class (e.g., standard in Minikube)
```

### Volume Mount in Deployment
- Mounted at `/data` where visits counter file is written
- Pod can read/write visits counter persistently

### Persistence Test

**Test Procedure:**
1. Deploy application: `helm install myapp ./k8s/app-python`
2. Access root endpoint multiple times: `curl http://<service>:80/`
3. Check visits count: `curl http://<service>:80/visits`
4. Delete pod to trigger restart: `kubectl delete pod <pod-name>`
5. Wait for new pod to start
6. Verify counter continues: `curl http://<service>:80/visits`

**Expected Result:** Counter value preserved after pod deletion

---

## ConfigMap vs Secret

### ConfigMap
- **Use for:** Non-sensitive configuration (settings, feature flags, etc.)
- **Storage:** Plain text, not encrypted at rest
- **Typical data:** App config, environment variables, config files
- **Size limit:** 1MB per ConfigMap
- **Example:** `LOG_LEVEL=INFO`, `DATABASE_URL=...` (without credentials)

### Secret
- **Use for:** Sensitive data (passwords, API keys, credentials)
- **Storage:** Base64 encoded (should use Sealed Secrets or external secret management in production)
- **Typical data:** API keys, passwords, certificates
- **Size limit:** 1MB per Secret
- **Example:** `API_KEY=secret123`, `DB_PASSWORD=...`

### Key Differences
| Aspect | ConfigMap | Secret |
|--------|-----------|--------|
| Encryption | No | Base64 (not encrypted) |
| Data Type | Non-sensitive | Sensitive |
| Audit | Standard logging | Restricted access (should be) |
| Size Limit | 1MB | 1MB |
| Use Cases | Config files, settings | Credentials, tokens |

---

## Verification Outputs

### ConfigMaps and PVC
```bash
$ kubectl get configmap,pvc
NAME                          DATA   AGE
configmap/app-python-config   1      2m
configmap/app-python-env      2      2m

NAME                         STATUS   VOLUME                                   CAPACITY   ACCESS MODES
pvc/app-python-data          Bound    pvc-xxxxx                                100Mi      RWO
```

### Config File Inside Pod
```bash
$ kubectl exec app-python-xxxxx -- cat /config/config.json
{
  "appName": "devops-info-service",
  "environment": "dev",
  "logLevel": "INFO",
  "features": {
    "metricsEnabled": true,
    "cachingEnabled": true,
    "debugMode": false
  }
}
```

### Environment Variables in Pod
```bash
$ kubectl exec app-python-xxxxx -- env | grep -E "APP_|LOG_"
APP_ENV=dev
LOG_LEVEL=INFO
```

### Persistence Test
```bash
# Before pod deletion
$ curl http://app-python:80/visits
{"visits": 5, "timestamp": "2026-04-16T19:10:00.000000+00:00"}

# Pod deletion
$ kubectl delete pod app-python-xxxxx
pod "app-python-xxxxx" deleted

# After pod restart (new pod starts)
$ curl http://app-python:80/visits
{"visits": 5, "timestamp": "2026-04-16T19:12:00.000000+00:00"}
# Counter value preserved!
```

---

## Summary

- **Visits Counter:** File-based counter at `/data/visits` persists across restarts
- **ConfigMaps:** Two types deployed - file-based and environment variable-based
- **PersistentVolume:** Kubernetes PVC ensures data survives pod rescheduling
- **Best Practices:** ConfigMaps for configuration, Secrets for sensitive data
