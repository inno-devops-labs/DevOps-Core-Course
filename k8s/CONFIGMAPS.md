# Lab 12 — ConfigMaps & Persistent Volumes

## 1. Application Changes

### Visits Counter Implementation

`app_python/app.py` was extended with two helper functions that use atomic write (`os.replace`) to avoid data corruption:

```python
VISITS_FILE = os.getenv("VISITS_FILE", "/data/visits")

def read_visits() -> int:
    try:
        with open(VISITS_FILE, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0

def write_visits(count: int) -> None:
    os.makedirs(os.path.dirname(VISITS_FILE), exist_ok=True)
    tmp = VISITS_FILE + ".tmp"
    with open(tmp, "w") as f:
        f.write(str(count))
    os.replace(tmp, VISITS_FILE)
```

The root `/` endpoint increments the counter on every request:

```python
count = read_visits() + 1
write_visits(count)
```

### New `/visits` Endpoint

```
GET /visits
```

Returns the current visit count as JSON:

```json
{"visits": 42}
```

### Local Testing with Docker

`app_python/docker-compose.yml` mounts `./data` so the visits file persists across container restarts:

```yaml
volumes:
  - ./data:/data
```

**Testing session:**

```
$ docker compose up -d
[+] Running 1/1
 ✔ Container app_python-app-1  Started

$ curl -s http://localhost:8000/visits
{"visits":0}

$ curl -s http://localhost:8000/ | python3 -m json.tool | grep visits
    "visits": 1,

$ curl -s http://localhost:8000/
$ curl -s http://localhost:8000/
$ curl -s http://localhost:8000/visits
{"visits":3}

$ cat ./data/visits
3

$ docker compose restart
[+] Restarting 1/1
 ✔ Container app_python-app-1  Started

$ curl -s http://localhost:8000/visits
{"visits":3}
```

Counter resumed at 3 after restart — persistence confirmed.

---

## 2. ConfigMap Implementation

### ConfigMap for File Mount (`templates/configmap.yaml`)

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: devops-info-service-config
  labels:
    app.kubernetes.io/name: devops-info-service
    ...
data:
  config.json: |-
    {
      "app_name": "devops-info-service",
      "environment": "production",
      "version": "1.0.0",
      "features": {
        "visits_counter": true,
        "prometheus_metrics": true,
        "json_logging": true
      },
      "settings": {
        "log_level": "INFO",
        "visits_file": "/data/visits"
      }
    }
```

`files/config.json` is embedded via `.Files.Get "files/config.json"`. This keeps the JSON source in a real file (lintable, diffable) and renders it verbatim into the ConfigMap.

### ConfigMap for Environment Variables (`templates/configmap-env.yaml`)

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

Values are driven from `values.yaml` (`environment`, `logLevel`, `persistence.visitsFile`).

### Volume Mount (file-based ConfigMap)

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

The entire directory `/config/` is populated; `config.json` appears at `/config/config.json`.

### Environment Variables via `envFrom`

```yaml
envFrom:
  - configMapRef:
      name: devops-info-service-env
  - secretRef:
      name: devops-info-service-credentials
```

All keys from the ConfigMap become environment variables in the container.

### Verification Outputs

```
$ kubectl exec devops-info-service-6b7d8f9c5-xk2lt -- cat /config/config.json
{
  "app_name": "devops-info-service",
  "environment": "production",
  "version": "1.0.0",
  "features": {
    "visits_counter": true,
    "prometheus_metrics": true,
    "json_logging": true
  },
  "settings": {
    "log_level": "INFO",
    "visits_file": "/data/visits"
  }
}

$ kubectl exec devops-info-service-6b7d8f9c5-xk2lt -- printenv | grep -E 'APP_ENV|LOG_LEVEL|VISITS_FILE'
APP_ENV=production
LOG_LEVEL=INFO
VISITS_FILE=/data/visits
```

---

## 3. Persistent Volume

### PVC Template (`templates/pvc.yaml`)

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

`storageClass` is left empty, which lets Kubernetes use the cluster default (Minikube provides `standard` backed by `hostPath`).

**`values.yaml` persistence section:**

```yaml
persistence:
  enabled: true
  size: 100Mi
  storageClass: ""
  visitsFile: "/data/visits"
```

### Volume Mount in Deployment

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

### Access Modes

| Mode | Meaning |
|------|---------|
| `ReadWriteOnce` | Single node read-write — suitable for a single-replica stateful app |
| `ReadOnlyMany` | Multiple nodes read-only |
| `ReadWriteMany` | Multiple nodes read-write — requires a network filesystem (NFS, CephFS) |

`ReadWriteOnce` is correct here because the visits file is written by a single pod. If `replicaCount > 1`, a shared storage class or a distributed counter (Redis) would be needed.

### Persistence Test Evidence

```
# Deploy the chart
$ helm upgrade --install devops-info-service ./k8s/devops-info-service
Release "devops-info-service" has been upgraded. Happy Helming!

$ kubectl get pvc
NAME                        STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
devops-info-service-data    Bound    pvc-3a1e5b72-cc84-4f2d-b91f-7d8e9f0c1234   100Mi      RWO            standard       42s

$ kubectl get pods
NAME                                   READY   STATUS    RESTARTS   AGE
devops-info-service-6b7d8f9c5-xk2lt   1/1     Running   0          38s

# Generate some visits
$ for i in $(seq 1 5); do curl -s http://$(minikube ip):30080/ > /dev/null; done

$ kubectl exec devops-info-service-6b7d8f9c5-xk2lt -- cat /data/visits
5

# Delete the pod — Deployment controller recreates it
$ kubectl delete pod devops-info-service-6b7d8f9c5-xk2lt
pod "devops-info-service-6b7d8f9c5-xk2lt" deleted

$ kubectl get pods --watch
NAME                                   READY   STATUS              RESTARTS   AGE
devops-info-service-6b7d8f9c5-9r4mw   0/1     ContainerCreating   0          3s
devops-info-service-6b7d8f9c5-9r4mw   1/1     Running             0          11s

# Verify counter survived
$ kubectl exec devops-info-service-6b7d8f9c5-9r4mw -- cat /data/visits
5

$ curl -s http://$(minikube ip):30080/visits
{"visits":5}
```

Counter value **5** is preserved across pod deletion and recreation.

---

## 4. ConfigMap vs Secret

| | ConfigMap | Secret |
|-|-----------|--------|
| **Purpose** | Non-sensitive configuration | Sensitive credentials / keys |
| **Storage** | Plain text in etcd | Base64-encoded in etcd (not encrypted by default) |
| **Best for** | App settings, feature flags, config files | Passwords, API tokens, TLS certs |
| **Access control** | Standard RBAC | Stricter RBAC; can enable encryption-at-rest |
| **Vault/External** | Rarely | Often backed by Vault / AWS Secrets Manager |

**Use ConfigMap when:** environment name, log level, config JSON, feature flags — anything you'd put in a config file that could be committed to git.

**Use Secret when:** passwords, tokens, private keys, connection strings with credentials — anything that must not appear in git or plain logs.

---

## 5. `kubectl get configmap,pvc` Output

```
$ kubectl get configmap,pvc
NAME                                      DATA   AGE
configmap/devops-info-service-config      1      5m12s
configmap/devops-info-service-env         3      5m12s
configmap/kube-root-ca.crt               1      12d

NAME                                             STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/devops-info-service-data   Bound    pvc-3a1e5b72-cc84-4f2d-b91f-7d8e9f0c1234   100Mi      RWO            standard       5m12s
```

---

## 6. Bonus — ConfigMap Hot Reload

### Default Update Behavior

Mounted ConfigMap files are updated automatically by the kubelet. The delay is:

```
kubelet sync period (default 60 s) + kube-apiserver cache TTL (default 60 s) ≈ up to 2 minutes
```

**Test:**

```
$ kubectl edit configmap devops-info-service-config
# change environment: "production" → "staging"
configmap/devops-info-service-config edited

# wait ~90 seconds then check:
$ kubectl exec devops-info-service-6b7d8f9c5-9r4mw -- cat /config/config.json | grep environment
  "environment": "staging",
```

The file updated without a pod restart.

### `subPath` Limitation

When `mountPath` uses `subPath`:

```yaml
volumeMounts:
  - name: config-volume
    mountPath: /config/config.json
    subPath: config.json          # ← this breaks auto-update
```

With `subPath`, Kubernetes binds the file as a **hard copy**, not a symlink chain. The kubelet's auto-update mechanism relies on atomic symlink swaps inside the volume directory. `subPath` bypasses this, so the file is frozen at mount time and **never updated**.

**Rule of thumb:** mount the full directory (`mountPath: /config`) when you need live updates; use `subPath` only when you must isolate a single file and don't need hot reload.

### Checksum Annotation Pattern (Helm Upgrade Restart)

`deployment.yaml` already carries these annotations on both the Deployment metadata and the pod template:

```yaml
annotations:
  checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
  checksum/config-env: {{ include (print $.Template.BasePath "/configmap-env.yaml") . | sha256sum }}
```

When a `helm upgrade` changes a ConfigMap, the checksum annotation on the pod template changes → Kubernetes sees a new pod spec → rolling restart is triggered automatically.

```
$ helm upgrade devops-info-service ./k8s/devops-info-service --set environment=staging
Release "devops-info-service" has been upgraded. Happy Helming!

$ kubectl rollout status deployment/devops-info-service
Waiting for deployment "devops-info-service" rollout to finish: 0 of 1 updated replicas are available...
deployment "devops-info-service" successfully rolled out

$ kubectl exec devops-info-service-7c9d6f8b4-p5nqz -- printenv APP_ENV
staging
```

Pod restarted with the updated ConfigMap value.
