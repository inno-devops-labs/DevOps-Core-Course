# lab 12: configmaps & persistent volumes

## 1. application changes

### visits counter implementation

The application was extended with a file-based visit counter that persists across container restarts.

**key logic ([app.py](../../app_python/app.py)):**

```python
import fcntl
from pathlib import Path

VISITS_FILE = os.getenv('VISITS_FILE', '/data/visits')

def read_visits() -> int:
    """Read visit count from file, default to 0."""
    try:
        if Path(VISITS_FILE).exists():
            with open(VISITS_FILE, 'r') as f:
                content = f.read().strip()
                return int(content) if content else 0
    except (ValueError, IOError, PermissionError):
        pass
    return 0

def write_visits(count: int) -> None:
    """Write visit count to file with file locking."""
    Path(VISITS_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(VISITS_FILE, 'w') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        f.write(str(count))
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```

### new endpoints

| endpoint | method | description |
|----------|--------|-------------|
| `/` | GET | returns service info + increments visit counter |
| `/visits` | GET | returns current visit count |
| `/health` | GET | health check (unchanged) |

The `/` endpoint now calls `increment_visits()` and includes the count in the response. The `/visits` endpoint calls `read_visits()` without incrementing.

### local testing with docker

**docker-compose.yml:**

```yaml
services:
  devops-info-service:
    build: .
    ports:
      - "8080:5000"
    volumes:
      - ./data:/data
    environment:
      - HOST=0.0.0.0
      - PORT=5000
      - DEBUG=True
      - VISITS_FILE=/data/visits
```

**testing evidence:**

[[docker persistency](screenshots/docker-persistency.png)]

---

## 2. configmap implementation

### chart structure

```
k8s/devops-info-service/
├── files/
│   └── config.json              # application configuration
└── templates/
    ├── configmap.yaml            # configmap template
    └── ...
```

### configmap from file ([configmap.yaml](devops-info-service/templates/configmap.yaml))

Loads `files/config.json` using `.Files.Get`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "devops-info-service.fullname" . }}-config
  labels:
    {{- include "devops-info-service.labels" . | nindent 4 }}
data:
  config.json: |-
{{ .Files.Get "files/config.json" | indent 4 }}
```

### configmap as environment variables

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "devops-info-service.fullname" . }}-env
data:
  APP_ENV: {{ .Values.environment | quote }}
  LOG_LEVEL: {{ .Values.logLevel | quote }}
  METRICS_ENABLED: {{ .Values.metrics.enabled | quote }}
```

### how configmap is mounted as file

In [deployment.yaml](devops-info-service/templates/deployment.yaml):

```yaml
volumes:
  - name: config-volume
    configMap:
      name: {{ include "devops-info-service.fullname" . }}-config
containers:
  - volumeMounts:
      - name: config-volume
        mountPath: /config
        readOnly: true
```

### how configmap provides environment variables

```yaml
envFrom:
  - configMapRef:
      name: {{ include "devops-info-service.fullname" . }}-env
```

### verification outputs

[config configmap details](screenshots/configmap-config.png)

[env configmap details](screenshots/configmap-env.png)

[env vars from configmap and volume points](screenshots/vars-mount.png)

---

## 3. persistent volume

### pvc template ([pvc.yaml](devops-info-service/templates/pvc.yaml))

```yaml
{{- if .Values.persistence.enabled -}}
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "devops-info-service.fullname" . }}-data
  labels:
    {{- include "devops-info-service.labels" . | nindent 4 }}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: {{ .Values.persistence.size }}
  {{- if .Values.persistence.storageClass }}
  storageClassName: {{ .Values.persistence.storageClass }}
  {{- end }}
{{- end }}
```

### values.yaml configuration

```yaml
persistence:
  enabled: true
  size: 100Mi
  storageClass: ""  # use default storage class
```

### volume mount in deployment

```yaml
volumes:
  - name: data-volume
    persistentVolumeClaim:
      claimName: {{ include "devops-info-service.fullname" . }}-data
containers:
  - volumeMounts:
      - name: data-volume
        mountPath: /data
```

### verification outputs

[pvc details](screenshots/pvc-details.png)

[pod persistency](screenshots/pod-persistency.png)

data survives pod deletion because the PVC persists independently of pods.

---

## 4. configmap vs secret

| aspect | configmap | secret |
|--------|-----------|--------|
| purpose | non-sensitive configuration | sensitive data (passwords, keys, tokens) |
| encoding | plain text | base64 encoded |
| encryption at rest | no | optional (etcd encryption) |
| size limit | 1mb | 1mb |
| use with env vars | `configMapRef` | `secretRef` |
| use with volumes | `configMap` volume | `secret` volume |

### when to use configmap

- application settings (environment, log level)
- feature flags
- configuration files (json, yaml, ini)
- any non-sensitive data that varies between environments

### when to use secret

- database credentials
- api keys and tokens
- tls certificates
- any data that must not be exposed in plain text

### key insight

Kubernetes Secrets are only **base64-encoded**, not encrypted by default. For production, use etcd encryption or external secret managers like HashiCorp Vault (covered in Lab 11).
