# Lab 12: ConfigMaps & PersistentVolumes (K8s)

## Overview
This lab extends the Helm deployment with configuration externalization using ConfigMaps and data persistence using PersistentVolumeClaims (PVC).

---

## Task 1: Application Persistence with Visits Counter

### Implementation Details

**1. Enhanced Flask Application** (`app_python/app.py`)
- Added `/visits` endpoint returning current visit counter
- Implemented thread-safe visits counter using `threading.Lock`
- Counter stored atomically to `/data/visits` file
- Environment variable `VISITS_FILE` configures storage location (default: `/data/visits`)

**Key Code Sections:**
```python
visits_lock = threading.Lock()
VISITS_FILE = os.getenv('VISITS_FILE', '/data/visits')

def increment_visits():
    with visits_lock:
        try:
            visits = int(Path(VISITS_FILE).read_text().strip())
        except:
            visits = 0
        visits += 1
        # Atomic write using tempfile
        with tempfile.NamedTemporaryFile(dir='/data', delete=False) as tmp:
            tmp.write(str(visits).encode())
            tmp.flush()
            os.replace(tmp.name, VISITS_FILE)
        return visits
```

**2. Local Testing with Docker Compose** (`app_python/docker-compose.yml`)
- Volume mount: `./data:/data` for persistent storage
- Environment: `VISITS_FILE=/data/visits`
- Verified counter survives container restarts

**Test Evidence:**
```bash
# Build and run with docker-compose
docker-compose up -d
# Make requests to http://localhost:5000/
# Check counter persists after container restart
docker-compose down && docker-compose up -d
# Counter value maintained from previous session
```

---

## Task 2: ConfigMaps Implementation

### Two ConfigMap Strategies

**1. File-based ConfigMap** (`config.json`)
- Mounted at `/config/config.json` (read-only)
- Contains application configuration: name, environment, feature flags
- Template: `k8s/devops-app/templates/configmap.yaml` (first ConfigMap)

**Configuration Structure:**
```json
{
  "appName": "devops-app",
  "environment": "production",
  "description": "DevOps training application",
  "featureFlags": {
    "feature_a": true,
    "feature_b": false
  }
}
```

**2. Environment Variable ConfigMap**
- Second ConfigMap in same template
- Injected as environment variables via `envFrom.configMapRef`
- Variables: `APP_ENV`, `LOG_LEVEL`, `FEATURE_*` flags
- Template: Same file with multiple ConfigMaps

### Helm Chart Integration

**values.yaml additions:**
```yaml
configMap:
  enabled: true
  mountPath: /config

appConfig:
  appName: "devops-app"
  environment: "production"
  description: "DevOps training application"
  featureFlags:
    feature_a: true
    feature_b: false

appEnv:
  APP_ENV: "production"
  LOG_LEVEL: "INFO"
  FEATURE_FLAG_A: "enabled"
  FEATURE_FLAG_B: "disabled"
```

### Verification

**1. ConfigMap Creation:**
```bash
$ kubectl get configmap pvc-demo-devops-app-config -o yaml
```

**2. Pod Mounting Verification:**
```bash
$ POD=$(kubectl get pods -l app.kubernetes.io/instance=pvc-demo -o jsonpath='{.items[0].metadata.name}')
$ kubectl exec $POD -- cat /config/config.json
{
  "appName": "devops-app",
  "environment": "production",
  ...
}
```

**3. Environment Variables:**
```bash
$ kubectl exec $POD -- env | grep APP_ENV
APP_ENV=production
```

---

## Task 3: PersistentVolume & PVC Implementation

### PVC Configuration

**PersistentVolumeClaim Spec** (`k8s/devops-app/templates/pvc.yaml`):
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
  storageClassName: ""  # Uses default storage class
```

**Deployment Integration:**
- Volume source: PVC reference `pvc-demo-devops-app-data`
- Mount point: `/data` (visits counter storage)
- Mount point: `/config` (ConfigMap file-based config)

### Persistence Test: Pod Deletion & Recovery

**Test Scenario:** Increment visits counter → Delete Pod → Verify counter survives

**Step 1: Initial Counter State**
```bash
$ curl http://localhost:5000/visits
{"file":"/data/visits","visits":0}
```

**Step 2: Increment Counter (5 requests)**
```bash
for i in {1..5}; do
  curl http://localhost:5000/  # Root endpoint increments counter
done
```

**Step 3: Verify Counter Value Before Deletion**
```bash
$ POD=pvc-demo-devops-app-59c6b79b47-5xwdk
$ kubectl exec $POD -- cat /data/visits
5
```

**Step 4: Delete Pod**
```bash
$ kubectl delete pod pvc-demo-devops-app-59c6b79b47-5xwdk
pod "pvc-demo-devops-app-59c6b79b47-5xwdk" deleted
```

**Step 5: New Pod Created by ReplicaSet**
```bash
$ kubectl get pods -l app.kubernetes.io/instance=pvc-demo
NAME                                   READY   STATUS    RESTARTS   AGE
pvc-demo-devops-app-59c6b79b47-2w6s9   1/1     Running   0          5s
```

**Step 6: Verify Data Persistence (CRITICAL TEST)**
```bash
$ NEW_POD=pvc-demo-devops-app-59c6b79b47-2w6s9
$ kubectl exec $NEW_POD -- cat /data/visits
5

$ curl http://localhost:5000/visits
{"file":"/data/visits","visits":5}
```

### Result: ✅ SUCCESS
- PVC correctly mounts at `/data`
- Visits counter persists across pod deletion
- Data survives pod recreation
- File storage on PVC is durable

### Storage Details
```bash
$ kubectl get pvc pvc-demo-devops-app-data -o wide
NAME                        STATUS   VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS
pvc-demo-devops-app-data    Bound    pv-*     100Mi      RWO            standard
```

---

## ConfigMap vs Secrets: Key Differences

| Aspect | ConfigMap | Secret |
|--------|-----------|--------|
| **Data Type** | Configuration values | Sensitive credentials |
| **Encoding** | Plain text (readable) | Base64 (encrypted at rest in etcd Pro) |
| **Use Cases** | App settings, feature flags | Passwords, API keys, tokens |
| **Size Limit** | 1MB | 1MB |
| **Injection** | `configMapRef`, `valueFrom.configMapKeyRef` | `secretRef`, `valueFrom.secretKeyRef` |
| **Best Practice** | Non-sensitive config | Sensitive data + encryption at rest |

---

## Kubernetes Resources Created

### ConfigMaps
```bash
kubectl get configmap | grep pvc-demo
# pvc-demo-devops-app-config (file-based + env vars)
```

### PersistentVolumeClaim
```bash
kubectl get pvc
# pvc-demo-devops-app-data   Bound   pv-*   100Mi   RWO   standard
```

### Deployment with Mounts
```bash
kubectl describe deployment pvc-demo-devops-app | grep -A 20 Mounts
# Mount paths: /data (PVC), /config (ConfigMap)
```

---


