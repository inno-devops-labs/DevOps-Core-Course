# Lab 12 — ConfigMaps & Persistent Volumes

## 1. Application Changes

### Visits counter implementation

- A visit counter is incremented on each request to `GET /`.
- The counter is persisted to a file at `DATA_DIR/visits` (default: `/data/visits`).
- A new endpoint `GET /visits` returns the current counter value.

### New endpoint

- `GET /visits`
  - Response shape: `{"visits": <int>}`

### Local testing with Docker (commands to run)

From `monitoring/`:

```bash
docker compose up -d
curl -s http://localhost:5000/ | jq '.visits'
curl -s http://localhost:5000/visits
cat monitoring/data/visits
docker compose restart app-python
curl -s http://localhost:5000/visits
```

If the container cannot write `monitoring/data`, ensure the directory is writable by UID 1000 (the container user):

```bash
sudo chown -R 1000:1000 monitoring/data
```

---

## 2. ConfigMap Implementation

### Config file (`files/config.json`)

File location:

- `k8s/devops-info-service/files/config.json`

It is loaded into a ConfigMap and mounted into the pod at:

- `/config/config.json`

### ConfigMap template structure (file mount)

Template:

- `k8s/devops-info-service/templates/configmap.yaml` (ConfigMap `*-config`)

It uses `.Files.Get "files/config.json"` to include the file content as `data.config.json`.

### Mount ConfigMap as file

Deployment mounts the ConfigMap at:

- `/config` (file becomes `/config/config.json`)

Verification commands:

```bash
kubectl exec <pod> -- cat /config/config.json
```

### ConfigMap as environment variables

The same template also creates a second ConfigMap `*-env` with keys such as:

- `APP_NAME`, `APP_ENV`, `LOG_LEVEL`
- `FEATURE_VISITS_COUNTER`
- `DATA_DIR`, `CONFIG_PATH`

The Deployment injects these variables using:

- `envFrom.configMapRef` referencing `*-env`

Verification commands:

```bash
kubectl exec <pod> -- printenv | grep -E '^(APP_|LOG_LEVEL|FEATURE_|DATA_DIR|CONFIG_PATH)='
```

---

## 3. Persistent Volume

### PVC configuration

Template:

- `k8s/devops-info-service/templates/pvc.yaml`

Values:

- `persistence.enabled` (default: `true`)
- `persistence.size` (default: `100Mi`)
- `persistence.storageClass` (default: `""` → use cluster default)

The PVC uses:

- Access mode: `ReadWriteOnce`

### Volume mount configuration

The Deployment mounts the PVC at:

- `/data`

The app writes the visit counter file to:

- `/data/visits`

### Persistence test evidence (commands to run)

```bash
kubectl get pvc
kubectl get pods -l app.kubernetes.io/instance=<release>

# get visit count before deleting the pod
kubectl exec <pod> -- cat /data/visits
curl -s http://<service-url>/visits

# delete pod (deployment recreates it)
kubectl delete pod <pod>

# verify the new pod sees the same value
kubectl exec <new-pod> -- cat /data/visits
curl -s http://<service-url>/visits
```

Required outputs for submission (capture from your cluster):

- `kubectl get configmap,pvc`
- `kubectl exec <pod> -- cat /config/config.json`
- `kubectl exec <pod> -- printenv | grep APP_`
- Before/after value of `/data/visits` across a pod deletion

---

## 4. ConfigMap vs Secret

### When to use ConfigMap

- Non-sensitive configuration (feature flags, log level, environment name)
- Config files mounted into pods

### When to use Secret

- Sensitive values (passwords, API keys, tokens, private keys)
- Any credential material that must be protected with RBAC and (ideally) encrypted at rest

### Key differences

- **Security**: Secrets are still base64 in the API, but treated as sensitive and commonly protected with tighter RBAC and encryption-at-rest. ConfigMaps are for non-sensitive data.
- **Usage**: Both can be mounted as files or injected as environment variables.
- **Operational practice**: Keep secrets out of Git; ConfigMaps can safely be committed when they contain no sensitive data.

