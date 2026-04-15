# Lab 12 — ConfigMaps & Persistent Volumes

## Task 1 — Application Changes

### Visits Counter

The app now tracks how many times the root endpoint `/` is called. The counter is stored in a file so it survives restarts.

**How it works:**
- On every request to `/`, the app reads the current value from `/data/visits`, adds 1, and writes it back.
- If the file doesn't exist yet (first run), it starts from 0.
- The `/visits` endpoint returns the current count.

**New endpoint:**
- `GET /visits` — returns `{"visits": <number>}`

**File path** can be changed via the `VISITS_FILE` environment variable (default: `/data/visits`).

### Docker local testing

The `docker-compose.yml` mounts `./data` so the counter file stays on the host:

```yaml
volumes:
  - ./data:/data
```

**Test run:**

```bash
# Build and start
docker build -t devops-info-service:latest .
docker run -d --name test-visits -p 8001:8000 -v $(pwd)/data:/data devops-info-service:latest

# Hit root endpoint 3 times
curl http://localhost:8001/
curl http://localhost:8001/
curl http://localhost:8001/

# Check visits endpoint
curl http://localhost:8001/visits
# {"visits":3}

# Check the file on the host
cat ./data/visits
# 3

# Restart the container
docker restart test-visits

# Counter is still 3 — data survived the restart
curl http://localhost:8001/visits
# {"visits":3}
```

Output I got locally:
```
$ curl -s http://localhost:8001/visits
{"visits":3}

$ cat ./data/visits
3

# After restart:
$ curl -s http://localhost:8001/visits
{"visits":3}
```

---

## Task 2 — ConfigMaps

### Config file: `files/config.json`

```json
{
  "app_name": "devops-info-service",
  "environment": "production",
  "features": {
    "visit_counter": true,
    "metrics": true
  },
  "settings": {
    "log_format": "json",
    "visits_file": "/data/visits"
  }
}
```

### ConfigMap templates

There are two ConfigMaps in `templates/configmap.yaml`:

**1. File-based ConfigMap** (`-config`) — loads `config.json` using `.Files.Get`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: devops-info-service-config
data:
  config.json: |-
    { ...contents of files/config.json... }
```

Mounted as a volume at `/config`, so inside the pod:
```
/config/config.json
```

**2. Env var ConfigMap** (`-env`) — key-value pairs for environment variables:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: devops-info-service-env
data:
  APP_ENV: "production"
  LOG_LEVEL: "INFO"
  VISITS_FILE: "/data/visits"
```

Injected into the pod via `envFrom.configMapRef`.

### How ConfigMap is mounted as file

In `deployment.yaml`:

```yaml
volumes:
  - name: config-volume
    configMap:
      name: devops-info-service-config

containers:
  - volumeMounts:
      - name: config-volume
        mountPath: /config
```

### How ConfigMap provides environment variables

```yaml
envFrom:
  - configMapRef:
      name: devops-info-service-env
```

All keys from `devops-info-service-env` become environment variables in the container.

### Verification

```bash
$ kubectl get configmap
NAME                          DATA   AGE
devops-info-service-config    1      17s
devops-info-service-env       3      17s

$ kubectl exec deploy/devops-info-service -- cat /config/config.json
{
  "app_name": "devops-info-service",
  "environment": "production",
  "features": {
    "visit_counter": true,
    "metrics": true
  },
  "settings": {
    "log_format": "json",
    "visits_file": "/data/visits"
  }
}

$ kubectl exec deploy/devops-info-service -- printenv | grep -E "APP_ENV|LOG_LEVEL|VISITS_FILE"
APP_ENV=production
LOG_LEVEL=INFO
VISITS_FILE=/data/visits
```

---

## Task 3 — Persistent Volumes

### PVC configuration (`templates/pvc.yaml`)

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: devops-info-service-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Mi
```

`ReadWriteOnce` means the volume can be mounted by one node at a time. This is fine for our setup since all pods run on the same kind node.

Storage class is left empty (`""`), which uses the cluster default — on kind that's the `standard` class backed by hostPath.

### Volume mount in deployment

```yaml
volumes:
  - name: data-volume
    persistentVolumeClaim:
      claimName: devops-info-service-data

containers:
  - volumeMounts:
      - name: data-volume
        mountPath: /data
```

The app writes `/data/visits` which lives on the PVC.

### Persistence test

```bash
$ kubectl get pvc
NAME                       STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
devops-info-service-data   Bound    pvc-67fe7840-efee-4fa4-9751-9bd556721e05   100Mi      RWO            standard       17s

# Hit root endpoint 5 times
$ for i in $(seq 5); do curl -s http://localhost:8080/ > /dev/null; done
$ curl -s http://localhost:8080/visits
{"visits":5}

# Check the file on PVC before deleting pod
$ kubectl exec deploy/devops-info-service -- cat /data/visits
5

# Delete the pod (Deployment recreates it automatically)
$ kubectl delete pod devops-info-service-8558ccb8d8-5f8hv
pod "devops-info-service-8558ccb8d8-5f8hv" deleted

# New pod comes up: devops-info-service-8558ccb8d8-5qgkh
$ kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=devops-info-service
pod/devops-info-service-8558ccb8d8-5qgkh condition met

# Check count in the new pod — still 5
$ kubectl exec deploy/devops-info-service -- cat /data/visits
5
```

Data survived the pod deletion because the PVC is separate from the pod lifecycle.

---

## Task 4 — ConfigMap vs Secret

| | ConfigMap | Secret |
|---|---|---|
| **Use for** | Non-sensitive config (app settings, feature flags, file paths) | Sensitive data (passwords, tokens, API keys) |
| **Storage** | Plain text in etcd | Base64-encoded in etcd (encrypted at rest if cluster is configured) |
| **Access control** | Normal RBAC | Stricter RBAC, not shown in `kubectl get` by default |
| **Examples** | `APP_ENV`, `LOG_LEVEL`, config files | `DB_PASSWORD`, `API_TOKEN`, TLS certs |

**Rule of thumb:** if you'd feel uncomfortable putting it in a git repo, use a Secret. Everything else goes in a ConfigMap.

In this app:
- `APP_ENV`, `LOG_LEVEL`, `VISITS_FILE`, `config.json` → ConfigMap
- `APP_USERNAME`, `APP_PASSWORD` (from lab 11) → Secret

---

## Bonus — ConfigMap Hot Reload

### How ConfigMap updates work

When you update a ConfigMap, Kubernetes does NOT restart the pod automatically. The kubelet syncs the mounted files eventually — this takes about 60 seconds plus cache TTL, so the delay can be up to a few minutes.

```bash
# Edit the configmap live
kubectl edit configmap devops-info-service-config

# Wait ~1-2 minutes, then check the file inside the pod
kubectl exec deploy/devops-info-service -- cat /config/config.json
# You'll see the new content without any pod restart
```

### subPath limitation

If you mount a ConfigMap with `subPath`:

```yaml
volumeMounts:
  - name: config-volume
    mountPath: /config/config.json
    subPath: config.json     # <-- this breaks auto-updates
```

The file is copied at pod start time, not symlinked. So updates to the ConfigMap **do not** appear in the pod. You have to restart the pod manually to pick up changes.

**Without subPath** (what we use): Kubernetes creates a symlink chain inside the mount. When the ConfigMap updates, the symlink is swapped, so the new content appears automatically.

**When to use subPath:** Only when you need to inject a single file into a directory that already has other files (to avoid overwriting them). Accept that you lose auto-update.

### Helm checksum annotation — trigger pod restart on ConfigMap change

Added to `deployment.yaml`:

```yaml
template:
  metadata:
    annotations:
      checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

Every time the ConfigMap content changes, the sha256 checksum changes. Helm sees this as a new pod template, so it rolls out new pods — effectively restarting them to pick up the new config immediately instead of waiting for kubelet sync.

**How to verify:**
```bash
# Change something in files/config.json, then upgrade
helm upgrade devops-info-service k8s/devops-info-service

# Pods restart automatically
kubectl get pods -w
# NAME                                    READY   STATUS        RESTARTS
# devops-info-service-old-pod            0/1     Terminating   0
# devops-info-service-new-pod            1/1     Running       0

# New pod has the updated config
kubectl exec deploy/devops-info-service -- cat /config/config.json
```

This approach is simpler than running a sidecar reloader and works well when you control deployments through Helm.

---

## All Verification Outputs

```bash
$ kubectl get configmap,pvc
NAME                                   DATA   AGE
configmap/devops-info-service-config   1      17s
configmap/devops-info-service-env      3      17s
configmap/kube-root-ca.crt             1      69s

NAME                                             STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/devops-info-service-data   Bound    pvc-67fe7840-efee-4fa4-9751-9bd556721e05   100Mi      RWO            standard       17s

$ kubectl exec deploy/devops-info-service -- cat /config/config.json
{
  "app_name": "devops-info-service",
  "environment": "production",
  "features": {
    "visit_counter": true,
    "metrics": true
  },
  "settings": {
    "log_format": "json",
    "visits_file": "/data/visits"
  }
}

$ kubectl exec deploy/devops-info-service -- printenv | grep -E "APP_ENV|LOG_LEVEL|VISITS_FILE"
APP_ENV=production
LOG_LEVEL=INFO
VISITS_FILE=/data/visits

# Before pod deletion
$ kubectl exec deploy/devops-info-service -- cat /data/visits
5

$ kubectl delete pod devops-info-service-8558ccb8d8-5f8hv
pod "devops-info-service-8558ccb8d8-5f8hv" deleted

# After new pod comes up (devops-info-service-8558ccb8d8-5qgkh)
$ kubectl exec deploy/devops-info-service -- cat /data/visits
5
```
