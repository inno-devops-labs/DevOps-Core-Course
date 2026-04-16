# ConfigMaps & Persistent Volumes

## 1. Application Changes

### Visits Counter Implementation

A thread-safe visit counter was added to the application (`app_python/visits_counter.py`).  
It reads/writes a plain integer from a file specified by the `VISITS_FILE` environment variable (default: `/data/visits`).  
Writes use an atomic `os.replace()` pattern to avoid partial writes.

**New endpoint:**

| Method | Path      | Description                                  |
|--------|-----------|----------------------------------------------|
| `GET`  | `/visits` | Returns the current total visit count as JSON |

**Counter flow:**
```
GET /  →  SysInfoService.get_info()  →  visits_counter.increment()  →  write to /data/visits
GET /visits  →  visits_counter.get_count()  →  read from /data/visits
```

### Local Testing with Docker Compose

`docker-compose.yml` mounts the `./data` host directory to `/data` inside the container:

```yaml
volumes:
  - ./data:/data
```

**Test run:**
```bash
$ docker-compose up -d
$ curl -s http://localhost:5000/ > /dev/null
$ curl -s http://localhost:5000/ > /dev/null
$ curl -s http://localhost:5000/ > /dev/null
$ curl -s http://localhost:5000/visits
{"visits":3}
$ cat ./data/visits
3

# Restart container — counter preserved
$ docker-compose restart
$ curl -s http://localhost:5000/visits
{"visits":3}
```

---

## 2. ConfigMap Implementation

### File structure

```
k8s/devops-info-service/
├── files/
│   └── config.json          ← application config file
└── templates/
    └── configmap.yaml       ← two ConfigMaps defined in one file
```

### config.json content

```json
{
  "app_name": "devops-info-service",
  "environment": "dev",
  "features": {
    "visits_counter": true,
    "metrics": true
  },
  "log_level": "INFO"
}
```

### ConfigMap for file mount (`-config`)

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: <release>-devops-info-service-config
data:
  config.json: |-
    {
      "app_name": "devops-info-service",
      ...
    }
```

`deployment.yaml` mounts it at `/config`:
```yaml
volumes:
  - name: config-volume
    configMap:
      name: <release>-devops-info-service-config
containers:
  - volumeMounts:
      - name: config-volume
        mountPath: /config
```

### ConfigMap for environment variables (`-env`)

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: <release>-devops-info-service-env
data:
  APP_ENV: "dev"
  LOG_LEVEL: "INFO"
  VISITS_FILE: "/data/visits"
```

Injected via `envFrom` in `deployment.yaml`:
```yaml
envFrom:
  - configMapRef:
      name: <release>-devops-info-service-env
```

### Verification

```bash
# List ConfigMaps and PVC
$ kubectl get configmap,pvc
NAME                                              DATA   AGE
configmap/app-devops-info-service-config          1      2m
configmap/app-devops-info-service-env             3      2m

NAME                                                   STATUS   VOLUME   CAPACITY   ACCESS MODES
persistentvolumeclaim/app-devops-info-service-data     Bound    ...      100Mi      RWO

# File content inside pod
$ kubectl exec deploy/app-devops-info-service -- cat /config/config.json
{
  "app_name": "devops-info-service",
  "environment": "dev",
  "features": {
    "visits_counter": true,
    "metrics": true
  },
  "log_level": "INFO"
}

# Environment variables in pod
$ kubectl exec deploy/app-devops-info-service -- printenv | grep -E 'APP_ENV|LOG_LEVEL|VISITS_FILE'
APP_ENV=dev
LOG_LEVEL=INFO
VISITS_FILE=/data/visits
```

---

## 3. Persistent Volume

### PVC configuration (`templates/pvc.yaml`)

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

**Access modes discussion:**
- `ReadWriteOnce` — the volume can be mounted read-write by a single node. Suitable for a single-pod deployment writing a visits file.
- `ReadOnlyMany` / `ReadWriteMany` — needed if multiple pods on different nodes must share the same volume simultaneously (e.g., NFS). Not required here since we run on one node in Minikube.

**Storage class:** left empty (`""`) so Kubernetes uses the cluster's default. In Minikube this is `standard` (hostPath provisioner).

### Volume mount in deployment

```yaml
volumes:
  - name: data-volume
    persistentVolumeClaim:
      claimName: <release>-devops-info-service-data
containers:
  - volumeMounts:
      - name: data-volume
        mountPath: /data
```

### Persistence test (pod deletion)

```bash
# 1. Make some requests
$ for i in $(seq 1 5); do curl -s http://$(minikube ip):30080/ > /dev/null; done

# 2. Check counter
$ curl -s http://$(minikube ip):30080/visits
{"visits":5}

# 3. Note current pod name
$ kubectl get pods
NAME                                        READY   STATUS    RESTARTS   AGE
app-devops-info-service-7d9f6b8b9c-xk2pq   1/1     Running   0          3m

# 4. Delete pod
$ kubectl delete pod app-devops-info-service-7d9f6b8b9c-xk2pq
pod "app-devops-info-service-7d9f6b8b9c-xk2pq" deleted

# 5. Wait for new pod
$ kubectl get pods -w
NAME                                        READY   STATUS    RESTARTS   AGE
app-devops-info-service-7d9f6b8b9c-n8mtr   1/1     Running   0          15s

# 6. Verify counter is preserved
$ curl -s http://$(minikube ip):30080/visits
{"visits":5}
```

The new pod mounted the same PVC and found the counter file intact.

---

## 4. ConfigMap vs Secret

| Aspect              | ConfigMap                                      | Secret                                            |
|---------------------|------------------------------------------------|---------------------------------------------------|
| **Purpose**         | Non-sensitive configuration                    | Sensitive data (passwords, tokens, keys)          |
| **Storage**         | Stored in plain text in etcd                   | Stored base64-encoded in etcd (not encrypted by default, but can be) |
| **Access control**  | Standard RBAC                                  | Tighter RBAC; `kubectl get secret` requires permission |
| **Use cases**       | App settings, feature flags, config files, env | DB passwords, API keys, TLS certificates, SSH keys |
| **Helm integration**| `.Files.Get`, `configMapRef`                   | `secretRef`, Sealed Secrets, Vault injection      |

**Rule of thumb:** if the value would be embarrassing or dangerous if leaked, it belongs in a Secret.  
In this chart, `APP_ENV` and `LOG_LEVEL` → ConfigMap; `USERNAME`, `PASSWORD`, `SECRET_KEY` → Secret (via Vault injection from Lab 11).

---

## Bonus: ConfigMap Hot Reload (checksum annotation)

The deployment includes a checksum annotation that forces pod restart whenever the ConfigMap changes:

```yaml
annotations:
  checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

When you run `helm upgrade` after modifying `files/config.json` or any ConfigMap value, the sha256 changes, Kubernetes detects a template change, and performs a rolling update — so pods always run with the latest config.

**Default kubelet sync period:** ~60 s + cache TTL (can be up to ~2 min) for volume-mounted ConfigMaps.

**subPath limitation:** mounting with `subPath` copies the file at pod creation time. The kubelet does not watch sub-path mounts for updates. Use a full directory mount (as done here: `mountPath: /config`) to receive automatic updates.
