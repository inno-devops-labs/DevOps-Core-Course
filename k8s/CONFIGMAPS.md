# Lab 12 — ConfigMaps & Persistent Volumes

## 1. Application Changes

### Visits Counter Implementation

The Python service was upgraded with a persisted visits counter:

- `GET /` now increments a counter on every request.
- Counter is stored in a file (`VISITS_FILE`, default `/data/visits`).
- New endpoint `GET /visits` returns current counter value and file path.
- File access is protected with a process-level lock (`threading.Lock`) to prevent concurrent write conflicts.
- Writes are atomic (`tmp` file + `os.replace`) to reduce corruption risk.

### New Endpoint

`GET /visits` real response from running cluster:

```json
{
  "visits": 2,
  "file_path": "/data/visits",
  "timestamp": "2026-04-14T18:04:46.019567Z"
}
```

### Local Docker Persistence Setup

Added `app_python/docker-compose.yml` with persistent volume:

```yaml
services:
  devops-info-service:
    environment:
      VISITS_FILE: "/data/visits"
    volumes:
      - ./data:/data
```

Run from `app_python/`:

```bash
docker compose up --build -d
curl http://localhost:5000/
curl http://localhost:5000/visits
docker compose restart devops-info-service
curl http://localhost:5000/visits
docker compose down
```

Expected behavior: counter value remains after container restart.

Collected local Docker Compose output:

```text
$ docker compose up --build -d
[+] up 3/3
 ✔ Image app_python-devops-info-service Built                                     7.1s
 ✔ Network app_python_default           Created                                   0.0s
 ✔ Container devops-info-service        Started                                   0.4s

$ curl -s http://127.0.0.1:5000/
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"279834cb9003","platform":"Linux","platform_version":"#1 SMP Fri Mar 29 23:14:13 UTC 2024","architecture":"x86_64","cpu_count":20,"python_version":"3.13.13"},"runtime":{"uptime_seconds":3,"uptime_human":"0 hours, 0 minutes","current_time":"2026-04-14T18:11:30.825258Z","timezone":"UTC"},"request":{"client_ip":"172.19.0.1","user_agent":"curl/7.81.0","method":"GET","path":"/"},"visits":{"count":1},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"},{"path":"/visits","method":"GET","description":"Visits counter"},{"path":"/metrics","method":"GET","description":"Prometheus metrics"}]}

$ curl -s http://127.0.0.1:5000/visits
{"visits":1,"file_path":"/data/visits","timestamp":"2026-04-14T18:11:40.593347Z"}

$ docker compose restart devops-info-service
[+] restart 0/1
 ⠇ Container devops-info-service Restarting                                       0.8s

$ curl -s http://127.0.0.1:5000/visits
{"visits":1,"file_path":"/data/visits","timestamp":"2026-04-14T18:11:50.707154Z"}

$ docker compose down
[+] down 2/2
 ✔ Container devops-info-service Removed                                          0.6s
 ✔ Network app_python_default    Removed                                          0.6s
```

## 2. ConfigMap Implementation

### Files Added

- `k8s/devops-info-chart/files/config.json`
- `k8s/devops-info-chart/templates/configmap.yaml`

### ConfigMap Template Structure

Two ConfigMaps are generated:

1. File-based config (`*-config-file`)
- Loads `files/config.json` via `.Files.Get`.
- Uses `tpl` so values from `values.yaml` are rendered into JSON.

2. Env config (`*-config-env`)
- Exposes key-value pairs (`APP_ENV`, `LOG_LEVEL`, feature flags) for `envFrom`.

### `config.json` Content (Rendered)

```json
{
  "application": {
    "name": "devops-info-service",
    "environment": "dev",
    "version": "1.0.0"
  },
  "features": {
    "visitsCounter": true,
    "metricsEnabled": true
  },
  "settings": {
    "logLevel": "INFO",
    "defaultTimezone": "UTC"
  }
}
```

### How ConfigMap Is Mounted as File

In `templates/deployment.yaml`:

- Volume `config-volume` references `*-config-file` ConfigMap.
- Mounted to `/config` (read-only).
- Final file path in pod: `/config/config.json`.

### How ConfigMap Provides Environment Variables

In `templates/deployment.yaml`:

- `envFrom` includes `configMapRef` to `*-config-env`.
- All keys are injected automatically into container environment.

### Verification Output (Helm Render)

Rendered with:

```bash
helm template devops-info ./k8s/devops-info-chart -f ./k8s/devops-info-chart/values.yaml
```

Key evidence:

```text
kind: ConfigMap
kind: ConfigMap
envFrom:
  - configMapRef:
      name: devops-info-devops-info-config-env
volumeMounts:
  - name: config-volume
    mountPath: /config
```

### Kubernetes Runtime Verification Commands

```bash
kubectl get configmap,pvc
kubectl exec <pod-name> -- cat /config/config.json
kubectl exec <pod-name> -- printenv | grep -E "APP_|FEATURE_|LOG_LEVEL"
```

Collected runtime output (kind cluster):

```text
NAME                                            DATA   AGE
configmap/devops-info-devops-info-config-env    5      7m48s
configmap/devops-info-devops-info-config-file   1      7m48s
configmap/kube-root-ca.crt                      1      8m25s

NAME                                                 STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/devops-info-devops-info-data   Bound    pvc-3d803ea8-ab10-44ea-bf90-72981b67f1ef   100Mi      RWO            standard       <unset>                 7m48s
```

```text
$ kubectl exec devops-info-devops-info-55968cfffd-sxt7b -- cat /config/config.json
{
  "application": {
    "name": "devops-info-service",
    "environment": "dev",
    "version": "1.0.0"
  },
  "features": {
    "visitsCounter": true,
    "metricsEnabled": true
  },
  "settings": {
    "logLevel": "DEBUG",
    "defaultTimezone": "UTC"
  }
}
```

```text
$ kubectl exec devops-info-devops-info-55968cfffd-sxt7b -- printenv | grep -E "APP_|FEATURE_|LOG_LEVEL"
FEATURE_METRICS_ENABLED=true
FEATURE_VISITS_COUNTER=true
LOG_LEVEL=DEBUG
APP_ENV=dev
APP_NAME=devops-info-service
```

## 3. Persistent Volume Implementation

### PVC Configuration Explanation

Added `k8s/devops-info-chart/templates/pvc.yaml`:

- `accessModes: [ReadWriteOnce]`
- `resources.requests.storage: {{ .Values.persistence.size }}`
- `storageClassName` is optional and configurable (`.Values.persistence.storageClass`)

Default values in `values.yaml`:

```yaml
persistence:
  enabled: true
  size: 100Mi
  accessMode: ReadWriteOnce
  storageClass: ""
  mountPath: /data
```

### Access Modes and Storage Class Discussion

- `ReadWriteOnce` is used because a single pod writes the visits file.
- In local kind/minikube environments this maps well to a single-node lab cluster.
- `storageClass: ""` means Kubernetes uses the default storage class (`standard` in this run).
- The claim was dynamically provisioned and bound successfully:

```text
persistentvolumeclaim/devops-info-devops-info-data   Bound   ...   100Mi   RWO   standard
```

### Volume Mount Configuration

In `templates/deployment.yaml`:

- Volume `data-volume` references PVC `*-data`
- Mounted at `/data`
- App writes counter to `/data/visits` (`VISITS_FILE` env var)

Runtime confirmation:

```text
$ kubectl exec devops-info-devops-info-55968cfffd-sxt7b -- cat /data/visits
2
```

### Persistence Test Evidence

Counter value before pod deletion:

```text
$ kubectl exec devops-info-devops-info-55968cfffd-sxt7b -- cat /data/visits
2
```

Pod deletion command:

```text
$ kubectl delete pod devops-info-devops-info-55968cfffd-sxt7b
pod "devops-info-devops-info-55968cfffd-sxt7b" deleted from default namespace
```

Counter value after new pod starts:

```text
$ kubectl wait --for=condition=Ready pod/devops-info-devops-info-55968cfffd-4fv8q --timeout=120s
pod/devops-info-devops-info-55968cfffd-4fv8q condition met

$ kubectl exec devops-info-devops-info-55968cfffd-4fv8q -- cat /data/visits
2
```

Endpoint validation after pod restart:

```text
$ curl -s http://127.0.0.1:8080/visits
{"visits":2,"file_path":"/data/visits","timestamp":"2026-04-14T18:10:41.007963Z"}
```

### Persistence Test Procedure (Pod Recreation)

```bash
kubectl get configmap,pvc
kubectl get pods
kubectl exec <pod> -- cat /data/visits
kubectl delete pod <pod>
kubectl get pods -w
kubectl exec <new-pod> -- cat /data/visits
curl http://<service-or-port-forward>/visits
```

Expected result: value before pod deletion equals value after new pod starts.

Example:

```text
$ curl -s http://127.0.0.1:8080/
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"devops-info-devops-info-55968cfffd-sxt7b","platform":"Linux","platform_version":"#1 SMP Fri Mar 29 23:14:13 UTC 2024","architecture":"x86_64","cpu_count":20,"python_version":"3.13.13"},"runtime":{"uptime_seconds":96,"uptime_human":"0 hours, 1 minute","current_time":"2026-04-14T18:04:41.138231Z","timezone":"UTC"},"request":{"client_ip":"127.0.0.1","user_agent":"curl/7.81.0","method":"GET","path":"/"},"visits":{"count":2},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"},{"path":"/visits","method":"GET","description":"Visits counter"},{"path":"/metrics","method":"GET","description":"Prometheus metrics"}]}

$ curl -s http://127.0.0.1:8080/visits
{"visits":2,"file_path":"/data/visits","timestamp":"2026-04-14T18:04:46.019567Z"}

$ kubectl exec devops-info-devops-info-55968cfffd-sxt7b -- cat /data/visits
2

$ kubectl delete pod devops-info-devops-info-55968cfffd-sxt7b
pod "devops-info-devops-info-55968cfffd-sxt7b" deleted from default namespace

$ kubectl wait --for=condition=Ready pod/devops-info-devops-info-55968cfffd-4fv8q --timeout=120s
pod/devops-info-devops-info-55968cfffd-4fv8q condition met

$ kubectl exec devops-info-devops-info-55968cfffd-4fv8q -- cat /data/visits
2

$ curl -s http://127.0.0.1:8080/visits
{"visits":2,"file_path":"/data/visits","timestamp":"2026-04-14T18:10:41.007963Z"}
```

## 4. ConfigMap vs Secret

### Use ConfigMap When

- Data is non-sensitive.
- You need plain app settings (feature flags, log level, environment name).
- You want config mounted as files or injected as environment variables.

### Use Secret When

- Data is sensitive (passwords, tokens, API keys, certificates).
- Access should be restricted and handled as secret material.

### Key Differences

- `ConfigMap`: plain configuration, base64 not required, for non-confidential data.
- `Secret`: sensitive data object; values are base64-encoded in manifests and should be protected by RBAC and encryption-at-rest.

## 5. Validation Performed in This Environment

Successfully executed:

```bash
helm lint ./k8s/devops-info-chart -f ./k8s/devops-info-chart/values.yaml
helm template devops-info ./k8s/devops-info-chart -f ./k8s/devops-info-chart/values.yaml
helm template devops-info-dev ./k8s/devops-info-chart -f ./k8s/devops-info-chart/values-dev.yaml
helm template devops-info-prod ./k8s/devops-info-chart -f ./k8s/devops-info-chart/values-prod.yaml
```

Notes:

- Helm template/lint validation was executed in the development environment.
- Kubernetes runtime evidence (ConfigMaps, env vars, PVC persistence checks) was collected from a local `kind` cluster run.
- Docker Compose persistence run was executed locally and attached in Section 1.
