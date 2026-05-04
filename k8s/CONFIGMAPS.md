# Lab 12 — ConfigMaps & Persistent Volumes

## 1. Application Changes

A `visits` counter was added to `app_python/app.py`:

- `/` endpoint increments a file-based counter on every request
- `/visits` endpoint returns the current count as JSON
- Counter is stored at `$VISITS_FILE` (default `/data/visits`) using
  `fcntl` file locking for thread safety

```python
@app.route("/visits")
def visits():
    return jsonify({"visits": _read_visits()}), 200
```

Docker Compose volume configuration (`app_python/docker-compose.yml`):

```yaml
services:
  app:
    volumes:
      - app-data:/data
    environment:
      - VISITS_FILE=/data/visits
volumes:
  app-data:
```

Local test:

```
visits: 1
visits: 2
{"visits":2}
```

---

## 2. ConfigMap Implementation

### Chart structure

```
k8s/helm/devops-info/
├── files/
│   └── config.json        ← application config file
└── templates/
    ├── configmap.yaml     ← two ConfigMaps: file mount + env vars
    ├── deployment.yaml    ← mounts both, checksum annotation for hot-reload
    └── pvc.yaml           ← PVC for visits file
```

### ConfigMap for file mount

`templates/configmap.yaml` uses `.Files.Get` to embed `files/config.json`:

```yaml
data:
  config.json: |-
    {{ .Files.Get "files/config.json" | indent 4 }}
```

Mounted at `/config/config.json` in the pod:

```bash
kubectl exec <pod> -- cat /config/config.json
# {"app_name":"DevOps Info Service","environment":"development",...}
```

### ConfigMap for environment variables

```yaml
data:
  APP_ENV: {{ .Values.appEnv | default "development" | quote }}
  LOG_LEVEL: {{ .Values.logLevel | default "INFO" | quote }}
  VISITS_FILE: "/data/visits"
```

Injected via `envFrom`:

```yaml
envFrom:
  - configMapRef:
      name: devops-info-env
```

Verification:

```bash
kubectl exec <pod> -- printenv | grep -E "APP_ENV|LOG_LEVEL|VISITS_FILE"
# APP_ENV=production
# LOG_LEVEL=INFO
# VISITS_FILE=/data/visits
```

See [`configmaps/evidence/01-configmaps.txt`](./configmaps/evidence/01-configmaps.txt).

---

## 3. Persistent Volume

### PVC template

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: {{ .Values.persistence.size }}
```

- **`ReadWriteOnce`** — one node can mount the volume read-write at a time.
  Appropriate for a single-instance or same-node workload.
- **Storage class `""`** — uses the cluster default (minikube provides
  `standard` backed by hostPath).

### Persistence test

```
Visits before pod deletion:  3
--- kubectl delete pod devops-info-xxxx ---
Deployment rolled out new pod.
Visits after new pod started: 3   ← data survived pod restart
```

See [`configmaps/evidence/02-persistence.txt`](./configmaps/evidence/02-persistence.txt).

---

## 4. ConfigMap vs Secret

| Aspect | ConfigMap | Secret |
|--------|-----------|--------|
| Data type | Non-sensitive config | Sensitive credentials, tokens |
| Storage | Plain text in etcd | Base64 in etcd (encrypt at rest for real security) |
| Env vars | `envFrom.configMapRef` | `envFrom.secretRef` |
| File mount | `configMap` volume | `secret` volume |
| Use case | App config, feature flags, connection strings | Passwords, API keys, TLS certs |

**Rule of thumb:** if you'd be uncomfortable committing the value to a public
Git repo, use a Secret (and back it with Vault — see Lab 11).

---

## Bonus — ConfigMap Hot Reload

### Default kubelet sync behavior

Mounted ConfigMap **files** (not `subPath`) update automatically. The kubelet
polls `kube-apiserver` every `--sync-frequency` (default 60 s) plus an
additional TTL from its local cache. Total delay is typically 60–120 s.

**`subPath` exception**: when a file is mounted via `subPath: config.json`,
Kubernetes copies the file at pod start time. The bind-mount is to a regular
file, not a symlink chain, so updates to the ConfigMap are **never** reflected
in the running pod. Avoid `subPath` when you need live reloads.

### Env vars never auto-update

Environment variables set from `envFrom.configMapRef` are resolved at container
creation. Even if the ConfigMap changes, the running container's env stays
frozen. The pod must be restarted.

### Checksum annotation pattern (implemented)

The deployment template carries:

```yaml
spec:
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

When `helm upgrade` changes any value that affects `configmap.yaml`, the
sha256 of the rendered YAML changes → the pod template annotation changes →
Kubernetes creates new pods → old pods are terminated. Zero-downtime rolling
restart, no manual intervention.

Demonstrated:

```bash
helm upgrade devops-info k8s/helm/devops-info --set appEnv=production
# → pods restarted; new pods show APP_ENV=production
```

See [`configmaps/evidence/03-hot-reload.txt`](./configmaps/evidence/03-hot-reload.txt).

### Alternatives

- **Stakater Reloader** — watches ConfigMaps/Secrets cluster-wide and
  restarts annotated Deployments automatically, even outside of Helm upgrades.
- **Application-level file watching** — inotify / `watchdog` in Python to
  reload config at runtime without a pod restart (works only for file mounts,
  not env vars).
