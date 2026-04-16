# ConfigMaps & Persistent Volumes

## 1. Application Changes

### Visits Counter Implementation
The application was extended with a thread-safe visit counter that:
- Increments on every request to the root endpoint (`/`)
- Persists the count to a file at `/data/visits`
- Reads the count from file on startup (defaults to 0 if file doesn't exist)
- Uses a `threading.Lock` for thread-safe concurrent access

### New Endpoint: `/visits`
Returns the current visit count as JSON:
```json
{"visits": 42}
```

### Root Endpoint Update
The `/` endpoint now includes a `visits` field in its response and increments the counter on each request.

### Local Testing with Docker Compose
The `docker-compose.yml` mounts a local `./data` directory to `/data` inside the container:
```yaml
volumes:
  - ./data:/data
```

### Test persistence
```bash
$ curl -fsS http://127.0.0.1:5000/ >/dev/null
$ curl -fsS http://127.0.0.1:5000/ >/dev/null
$ cat data/visits
3

$ docker compose down
$ docker compose up -d
$ curl http://127.0.0.1:5000/visits
{"visits":3}
```
---

## 2. ConfigMap Implementation

### ConfigMap for File Mounting
**Template:** `k8s/my-python-app/templates/configmap.yaml`

Uses `.Files.Get` to load configuration from `files/config.json`:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "my-python-app.fullname" . }}-config
  labels:
    {{- include "my-python-app.labels" . | nindent 4 }}
data:
  config.json: |-
{{ .Files.Get "files/config.json" | indent 4 }}
```

**Config file content** (`files/config.json`):
```json
{
    "app_name": "devops-info-service",
    "environment": "production",
    "features": {
        "visits_counter": true,
        "metrics": true,
        "health_checks": true
    },
    "log_format": "json",
    "version": "1.1.0"
}
```

### ConfigMap Mounted as File
The ConfigMap is mounted as a volume at `/config` in the deployment:
```yaml
volumes:
  - name: config-volume
    configMap:
      name: {{ include "my-python-app.fullname" . }}-config
```
```yaml
volumeMounts:
  - name: config-volume
    mountPath: /config
    readOnly: true
```

This makes the file available at `/config/config.json` inside the pod.

### ConfigMap for Environment Variables
**Template:** `k8s/my-python-app/templates/configmap-env.yaml`

A second ConfigMap provides key-value pairs for environment variables:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "my-python-app.fullname" . }}-env
  labels:
    {{- include "my-python-app.labels" . | nindent 4 }}
data:
  APP_ENV: {{ .Values.env.APP_ENV | quote }}
  LOG_LEVEL: {{ .Values.env.LOG_LEVEL | default "info" | quote }}
  PORT: {{ .Values.env.PORT | quote }}
```

### Environment Variables Injected via `envFrom`
All keys from the env ConfigMap are injected as environment variables:
```yaml
envFrom:
  - configMapRef:
      name: {{ include "my-python-app.fullname" . }}-env
```

### Verification

Check config file inside pod
```bash
$ kubectl exec -n my-app2 myapp2-my-python-app-67d691dd-p2axt -- cat /config/config.json
{
    "app_name": "devops-info-service",
    "environment": "production",
    "features": {
        "visits_counter": true,
        "metrics": true,
        "health_checks": true
    },
    "log_format": "json",
    "version": "1.1.0"
}
```

Check environment variables
```bash
$ kubectl exec myapp2-my-python-app-67d691dd-p2axt -- sh -lc 'printenv | grep "^APP_" | sort'
APP_CONFIG_PATH=/config/config.json
APP_ENV=dev
APP_LOG_LEVEL=INFO
```

---

## 3. Persistent Volume

### PVC Configuration
**Template:** `k8s/my-python-app/templates/pvc.yaml`

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "my-python-app.fullname" . }}-data
  labels:
    {{- include "my-python-app.labels" . | nindent 4 }}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: {{ .Values.persistence.size }}
  {{- if .Values.persistence.storageClass }}
  storageClassName: {{ .Values.persistence.storageClass }}
  {{- end }}
```

### Access Modes and Storage Class
- **ReadWriteOnce**: The volume can be mounted as read-write by a single node. This is the standard access mode for most stateful workloads that don't require concurrent multi-node writes.
- **Storage Class**: Configurable via `values.yaml`. An empty string uses the cluster's default StorageClass (in Minikube, this provisions a hostPath volume automatically).

### Volume Mount Configuration
The PVC is mounted at `/data` in the container:
```yaml
volumes:
  - name: data-volume
    persistentVolumeClaim:
      claimName: {{ include "my-python-app.fullname" . }}-data
```
```yaml
volumeMounts:
  - name: data-volume
    mountPath: /data
```

### Persistence Test
```bash
# Deploy the application
helm install my-app ./k8s/my-python-app

# Access root endpoint multiple times
```bash
$ curl http://192.168.56.21
{"endpoints":[{"description":"Service 
<...>
"python_version":"3.12.13"}}
```

Check visits count
```bash
curl http://192.168.56.21/visits
3
```

Delete the pod
```bash
kubectl delete pod myapp2-my-python-app-67d691dd-p2axt
```

Verify visits count is preserved
```bash
$ curl http://192.168.56.21/visits
2
```

---

## 4. ConfigMap vs Secret

| Aspect | ConfigMap | Secret |
|---------|-----------|--------|
| **Purpose** | Store non-sensitive configuration data | Store sensitive data (passwords, tokens, keys) |
| **Data Storage** | Plain text in etcd | Base64-encoded in etcd |
| **Size Limit** | 1 MiB per ConfigMap | 1 MiB per Secret |
| **Use Case** | Environment variables, config files, feature flags | Database passwords, API keys, TLS certificates |
| **Security** | No encryption at rest | Can be encrypted at rest (with encryption config) |
| **Access** | Readable by all authenticated users | Can be restricted with RBAC more strictly |

**When to use ConfigMap:**
- Application settings (environment, log level, feature flags)
- Configuration files (JSON, YAML, properties)
- Command-line arguments or environment variables that are not sensitive

**When to use Secret:**
- Database credentials
- API keys and tokens
- TLS certificates and private keys
- Any data that should not be visible to all cluster users
