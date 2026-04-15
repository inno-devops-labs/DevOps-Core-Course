# LAB12 - ConfigMaps and Persistent Volumes

Cluster: `minikube`
Namespace: `lab12`
Release: `lab12-app`

## 1. Application Changes

### 1.1 Visits counter implementation

Implemented in `app_python/app.py`:

- Added file-backed visits counter with configurable path via `VISITS_FILE`.
- Default path is `data/visits` for local runs.
- In Kubernetes, `VISITS_FILE=/data/visits` is injected through ConfigMap env vars.
- `GET /` now increments the counter and returns current count in response.
- Added `GET /visits` endpoint that returns current counter value without incrementing.
- Added lock + atomic write pattern:
  - thread mutex (`threading.Lock`)
  - file lock (`fcntl.flock` on Linux)
  - atomic replace (`os.replace`) for safe writes

### 1.2 Local Docker Compose persistence test

`app_python/docker-compose.yml` mounts host directory `./data` into container path `/app/data` and sets `VISITS_FILE=/app/data/visits`.

Commands used:

```bash
cd app_python
docker compose up --build -d
curl -s http://localhost:5000/ >/dev/null
curl -s http://localhost:5000/ >/dev/null
curl http://localhost:5000/visits
cat ./data/visits

docker compose restart devops-info
curl http://localhost:5000/visits
cat ./data/visits
```

Output:

```text
before_endpoint={"visits":2}
before_file=2
after_endpoint={"visits":2}
after_file=2
```

This confirms the counter survives container restart.

## 2. ConfigMap Implementation

### 2.1 Helm files and templates

Added:

- `k8s/devops-info/files/config.json`
- `k8s/devops-info/templates/configmap.yaml`

`configmap.yaml` defines two ConfigMaps:

1. File-based config:
- Name: `{{ include "devops-info.configFileConfigMapName" . }}`
- Key: `config.json`
- Data loaded with `.Files.Get "files/config.json"`

2. Env-based config:
- Name: `{{ include "devops-info.configEnvConfigMapName" . }}`
- Keys from `.Values.configEnv`

### 2.2 Mounted file verification

Command:

```bash
kubectl -n lab12 exec <pod> -- cat /config/config.json
```

Output:

```json
{
  "application": {
    "name": "devops-info-service",
    "component": "api"
  },
  "environment": "default",
  "features": {
    "visitsCounter": true,
    "prometheusMetrics": true,
    "requestLogging": true
  },
  "settings": {
    "logFormat": "json",
    "timezone": "UTC",
    "refreshSeconds": 30
  }
}
```

### 2.3 Env vars injection verification

Command:

```bash
kubectl -n lab12 exec <pod> -- /bin/sh -c \
  'printenv | grep -E "^(APP_ENV|APP_USERNAME|APP_PASSWORD|LOG_LEVEL|VISITS_FILE|FEATURE_VISITS_COUNTER)=" | sort'
```

Output:

```text
APP_ENV=dev
APP_PASSWORD=change-me-password
APP_USERNAME=change-me-username
FEATURE_VISITS_COUNTER=true
LOG_LEVEL=debug
VISITS_FILE=/data/visits
```

## 3. Persistent Volume Implementation

### 3.1 PVC configuration

Added `k8s/devops-info/templates/pvc.yaml` with:

- `accessModes: [ReadWriteOnce]`
- `resources.requests.storage: 100Mi`
- optional `storageClassName` controlled by values

Values in `k8s/devops-info/values.yaml`:

```yaml
persistence:
  enabled: true
  existingClaim: ""
  accessModes:
    - ReadWriteOnce
  size: 100Mi
  storageClass: ""
```

### 3.2 Deployment mount configuration

`k8s/devops-info/templates/deployment.yaml` updated with:

- ConfigMap volume mounted at `/config`
- PVC volume mounted at `/data`
- `envFrom.configMapRef` for env ConfigMap

### 3.3 Required resource output (`kubectl get configmap,pvc`)

```text
NAME                                     DATA   AGE
configmap/kube-root-ca.crt               1      6m1s
configmap/lab12-app-devops-info-config   1      6m1s
configmap/lab12-app-devops-info-env      4      6m1s

NAME                                               STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/lab12-app-devops-info-data   Bound    pvc-17a5c3ee-9e27-4160-b2d6-7bf626fc5316   100Mi      RWO            standard       <unset>                 6m1s
```

### 3.4 Persistence test (before/after pod deletion)

Commands:

```bash
kubectl -n lab12 delete pod <pod-name>
kubectl -n lab12 wait --for=condition=Ready pod -l app.kubernetes.io/instance=lab12-app --timeout=180s
```

Output:

```text
pod_before=lab12-app-devops-info-78f6cc588c-qkb74
pod_after=lab12-app-devops-info-78f6cc588c-hbg6c
visits_before=3
file_before=3
visits_after=3
file_after=3
```

Counter value remained unchanged after pod replacement, proving persistence through PVC.

## 4. ConfigMap vs Secret

- Use **ConfigMap** for non-sensitive configuration:
  - app settings
  - feature flags
  - environment labels
  - logging options

- Use **Secret** for sensitive data:
  - passwords
  - API tokens
  - credentials
  - private keys

Key differences:

- ConfigMap values are plain text in etcd unless cluster-level protections are added.
- Secret values are base64-encoded in API objects and should be protected with etcd encryption at rest and RBAC.
- Operationally both can be consumed as env vars or mounted files, but Secrets are for confidential data and should be redacted in logs/docs.
