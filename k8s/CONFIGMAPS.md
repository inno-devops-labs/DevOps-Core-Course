# Lab 12 — ConfigMaps & Persistent Volumes

## 1. Application Changes

### Visits Counter Implementation

The application (`app_python/app.py`) was extended with a file-based visit counter:

- **`/` endpoint** — increments the counter on each request, persists it to `/data/visits`
- **`/visits` endpoint** — returns the current visit count without incrementing
- Thread-safe file operations using `threading.Lock` and atomic writes (`os.replace`)
- Counter defaults to 0 if the file does not exist

### New Endpoint

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/visits` | GET | Returns `{"visits": <count>}` |

### Local Testing with Docker

A `docker-compose.yml` was added to `app_python/` with a named volume `app-data` mounted at `/data`.

```bash
cd app_python
docker compose up -d --build
# Access root endpoint several times
curl http://localhost:5000/
curl http://localhost:5000/
curl http://localhost:5000/
# Check counter
curl http://localhost:5000/visits
# Restart and verify persistence
docker compose restart
curl http://localhost:5000/visits
```

**Output — 3 visits, then restart, then check:**

```
$ curl http://localhost:5050/visits
{"visits":3}

$ docker compose restart
[+] Restarting 1/1
 ✔ Container devops-python-app  Started

$ curl http://localhost:5050/visits
{"visits":3}
```

Counter persists across container restarts.

---

## 2. ConfigMap Implementation

### Chart Structure

```
k8s/python-app/
├── files/
│   └── config.json          # Application configuration file
├── templates/
│   ├── configmap.yaml        # ConfigMap templates (file + env)
│   ├── deployment.yaml       # Updated with volume mounts
│   └── ...
└── values.yaml               # ConfigMap values
```

### config.json Content

```json
{
  "app_name": "devops-info-service",
  "environment": "dev",
  "version": "1.0.0",
  "features": {
    "metrics_enabled": true,
    "debug_mode": false,
    "visits_tracking": true
  },
  "logging": {
    "level": "INFO",
    "format": "json"
  }
}
```

### ConfigMap for File Mounting

The template uses `.Files.Get` to load `files/config.json` into a ConfigMap:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: <release>-python-app-config
data:
  config.json: |-
    <contents of files/config.json>
```

Mounted in the deployment at `/config`:

```yaml
volumeMounts:
  - name: config-volume
    mountPath: /config
volumes:
  - name: config-volume
    configMap:
      name: <release>-python-app-config
```

### ConfigMap for Environment Variables

A second ConfigMap injects env vars via `envFrom`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: <release>-python-app-env
data:
  APP_ENV: "dev"
  LOG_LEVEL: "INFO"
  APP_NAME: "devops-info-service"
```

Consumed in the deployment:

```yaml
envFrom:
  - configMapRef:
      name: <release>-python-app-env
```

### Verification

**ConfigMap file inside pod:**

```bash
kubectl exec python-app-766d569d9b-9x8dl -- cat /config/config.json
```

```json
{
  "app_name": "devops-info-service",
  "environment": "dev",
  "version": "1.0.0",
  "features": {
    "metrics_enabled": true,
    "debug_mode": false,
    "visits_tracking": true
  },
  "logging": {
    "level": "INFO",
    "format": "json"
  }
}
```

**Environment variables in pod:**

```bash
kubectl exec python-app-766d569d9b-9x8dl -- printenv | grep -E "APP_|LOG_"
```

```
APP_ENV=dev
APP_NAME=devops-info-service
LOG_LEVEL=INFO
```

**List of ConfigMaps and PVCs:**

```bash
kubectl get configmap,pvc
```

```
NAME                          DATA   AGE
configmap/kube-root-ca.crt    1      22d
configmap/python-app-config   1      2m14s
configmap/python-app-env      3      2m14s

NAME                                    STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/python-app-data   Bound    pvc-a1c4f751-8bd2-47a3-96d2-5a73e0e49c9a   100Mi      RWO            standard       <unset>                 2m14s
```

---

## 3. Persistent Volume

### PVC Configuration

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: <release>-python-app-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Mi
```

- **AccessMode `ReadWriteOnce`** — volume can be mounted as read-write by a single node
- **Storage class** — uses the cluster default (Minikube provides `standard` hostPath provisioner)
- **Size** — 100Mi is sufficient for a simple counter file

### Volume Mount

The PVC is mounted at `/data` in the container, where the app stores `/data/visits`.

```yaml
volumeMounts:
  - name: data-volume
    mountPath: /data
volumes:
  - name: data-volume
    persistentVolumeClaim:
      claimName: <release>-python-app-data
```

### Access Modes

| Mode | Description |
|------|-------------|
| `ReadWriteOnce` (RWO) | Single node read-write. Most common for single-pod workloads |
| `ReadOnlyMany` (ROX) | Multiple nodes read-only |
| `ReadWriteMany` (RWX) | Multiple nodes read-write. Requires NFS or similar |

RWO is used here because the deployment writes to the volume from a single pod at a time.

### Persistence Test

**1. Deploy and access root endpoint several times:**

```bash
helm upgrade --install python-app ./k8s/python-app -f ./k8s/python-app/values-dev.yaml
kubectl rollout status deployment python-app

# Access the app 3 times
curl http://127.0.0.1:52647/
curl http://127.0.0.1:52647/
curl http://127.0.0.1:52647/

# Check counter
kubectl exec python-app-766d569d9b-9x8dl -- cat /data/visits
```

```
3
```

**2. Delete the pod:**

```bash
kubectl delete pod python-app-766d569d9b-9x8dl
# Wait for replacement
kubectl get pods -l app.kubernetes.io/instance=python-app
```

```
NAME                          READY   STATUS    RESTARTS   AGE
python-app-766d569d9b-xxxxx   1/1     Running   0          30s
```

**3. Verify counter after restart:**

```bash
NEW_POD=$(kubectl get pods -l app.kubernetes.io/instance=python-app -o jsonpath='{.items[0].metadata.name}')
kubectl exec $NEW_POD -- cat /data/visits
```

```
3
```

Counter preserved after pod deletion — PVC persistence confirmed.

---

## 4. ConfigMap vs Secret

| Aspect | ConfigMap | Secret |
|--------|-----------|--------|
| **Purpose** | Non-sensitive configuration | Sensitive data (passwords, tokens, keys) |
| **Encoding** | Plain text | Base64-encoded (not encrypted by default) |
| **Size limit** | 1 MiB | 1 MiB |
| **Consumption** | Env vars, files, CLI args | Env vars, files |
| **RBAC** | Standard access | Should be restricted with tighter RBAC |
| **etcd storage** | Plain text | Base64 (enable encryption at rest for production) |

**Use ConfigMap** for: app settings, feature flags, config files, log levels.

**Use Secret** for: database passwords, API keys, TLS certificates, auth tokens.

---

## Bonus: ConfigMap Hot Reload

### Checksum Annotation Pattern

The deployment includes a checksum annotation that triggers a pod restart when ConfigMap content changes:

```yaml
annotations:
  checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

When `helm upgrade` is run and ConfigMap content has changed, the checksum changes, causing the deployment spec to differ and Kubernetes to roll out new pods.

### Default Update Behavior

When a ConfigMap mounted as a volume is updated (e.g., via `kubectl edit configmap`), kubelet syncs the change within **60s + cache TTL** (total up to ~2 minutes). The mounted file is a symlink that gets atomically updated.

### subPath Limitation

When using `subPath` in a volume mount, the file is copied (not symlinked), so it **does not receive automatic updates**. Avoid `subPath` if you need hot reload. This chart uses a full directory mount at `/config` for this reason.

### Reload Approaches

| Approach | How it works |
|----------|-------------|
| **Checksum annotation** (used here) | Helm upgrade detects checksum change → triggers rolling restart |
| **Stakater Reloader** | Controller watches ConfigMaps → auto-restarts dependent pods |
| **Application file watching** | App uses inotify/polling to detect file changes → reloads config |

The checksum annotation approach is implemented in this chart as it requires no additional controllers.

### Testing Hot Reload

```bash
# 1. Upgrade with changed config value
helm upgrade python-app ./k8s/python-app -f ./k8s/python-app/values-dev.yaml --set config.logLevel=DEBUG

# 2. Verify rollout
kubectl rollout status deployment python-app
kubectl get pods -l app.kubernetes.io/instance=python-app
```

```
deployment "python-app" successfully rolled out

NAME                          READY   STATUS        RESTARTS   AGE
python-app-6d8c8699bd-t5ftc   1/1     Running       0          22s
python-app-766d569d9b-dr9cs   1/1     Terminating   0          3m17s
```

The checksum annotation detected the ConfigMap change and triggered a rolling restart — old pod is terminating, new pod is running with updated config.
