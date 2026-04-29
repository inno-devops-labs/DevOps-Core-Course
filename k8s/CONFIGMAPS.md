# ConfigMaps and persistent storage — Lab 12

---

## 1. Application changes

### Visits counter

- Each `GET /` increments an integer stored in a text file (default path `/data/visits`, overridable with `VISITS_FILE_PATH`).
- The counter is read and written under an `asyncio.Lock`, with writes done via a temporary file and `os.replace` for an atomic update on POSIX systems.
- On application startup, the lifespan hook logs the initial count after reading the file (or `0` if the file is missing).
- `GET /visits` returns JSON `{"visits": <count>, "path": "<file path>"}` without incrementing the counter.

### Local testing with Docker Compose

`docker-compose.yml` uses a **named volume** (`visits_data` → `/data`) so the non-root user (UID 999) can write the counter file. 

From `app_python/`:

```bash
docker compose up --build
```

In another shell:

```bash
curl -s http://localhost:5000/ >/dev/null
curl -s http://localhost:5000/ >/dev/null
curl -s http://localhost:5000/visits
docker compose exec devops-info-service cat /data/visits
docker compose restart
sleep 3
curl -s http://localhost:5000/visits
docker compose exec devops-info-service cat /data/visits
```


---

## 2. ConfigMap implementation

### Chart layout

| Path | Role |
| --- | --- |
| `k8s/devops-info-service/files/config.json` | Source file bundled into the chart; loaded into the file-based ConfigMap with Helm `.Files.Get`. |
| `k8s/devops-info-service/templates/configmap.yaml` | Defines two ConfigMaps: `…-config` (file data) and `…-env` (key/value pairs for the environment). |

The file-based ConfigMap stores a single key `config.json` whose value is the raw JSON from `files/config.json`. The env ConfigMap sets `APP_ENV` and `LOG_LEVEL` from chart values `environment` and `logLevel`.

### Mounting as a file

The Deployment declares a `config` volume of type `configMap` referencing `{{ include "devops-info-service.fullname" . }}-config`, mounted read-only at `/config`. Kubernetes exposes keys as files, so the application sees `/config/config.json`.

### Environment variables

The same Deployment uses `envFrom` with `configMapRef` pointing at `…-env`, so every key in that ConfigMap becomes an environment variable in the container (`APP_ENV`, `LOG_LEVEL`). Optional Secret keys from Lab 11 remain available via a preceding `secretRef` entry when `secrets.enabled` is true.

### Verification commands

After installing the release (example name `lab12`):

```bash
kubectl get configmap,pvc
kubectl exec deploy/lab12-devops-info-service -- cat /config/config.json
kubectl exec deploy/lab12-devops-info-service -- printenv | grep -E '^(APP_ENV|LOG_LEVEL)='
```

### `kubectl get configmap,pvc`

```text
NAME                                        DATA   AGE
configmap/lab12-devops-info-service-config   1      1m
configmap/lab12-devops-info-service-env      2      1m

NAME                                                  STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/lab12-devops-info-service-data Bound    pvc-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx   100Mi      RWO            standard       1m
```

### File inside the pod

```text
$ kubectl exec deploy/lab12-devops-info-service -- cat /config/config.json
{
  "applicationName": "devops-info-service",
  "environment": "dev",
  "features": {
    "metricsEnabled": true,
    "verboseErrors": false
  },
  "settings": {
    "maxRequestLogLength": 2048
  }
}
```

### Environment variables

```text
$ kubectl exec deploy/lab12-devops-info-service -- printenv | grep -E '^(APP_ENV|LOG_LEVEL)='
APP_ENV=dev
LOG_LEVEL=INFO
```

---

## 3. Persistent volume

### PVC template

`templates/pvc.yaml` creates `{{ include "devops-info-service.fullname" . }}-data` when `persistence.enabled` is true. It requests `ReadWriteOnce` access and `resources.requests.storage` from `persistence.size` (default `100Mi`). If `persistence.storageClass` is non-empty, `storageClassName` is set; if it is empty, the cluster default storage class is used.

### Access modes and storage class

- `ReadWriteOnce` allows a single node to mount the volume read/write at a time, which matches a single-replica Deployment using one PVC.
- Leaving `storageClass` blank selects the default `StorageClass` (on Minikube this is typically `standard` with dynamic provisioning).

The default `values.yaml` sets `replicaCount: 1` while persistence is enabled. The production values file disables persistence when using multiple replicas, because a single `ReadWriteOnce` claim cannot be attached to several pods on most providers.

### Volume mount

The Deployment adds a `data` volume referencing the PVC and mounts it at `/data`. The app writes `VISITS_FILE_PATH` (`/data/visits` in chart values) on that volume.

### Persistence test (pod deletion)

Example evidence:

| Step | Value |
| --- | --- |
| Counter before pod delete | `2` |
| Delete command | `kubectl delete pod -l app.kubernetes.io/instance=lab12` |
| Counter after new pod | `2` |

The PVC retains the file; the replacement pod remounts the same claim at `/data`, so the count is preserved.

### Persistence test (Docker — before / after container restart)

| Step | Command / readout | Example value |
| --- | --- | --- |
| After traffic | `curl -s http://localhost:5000/visits` | `{"visits":2,...}` |
| On-disk in container | `docker compose exec devops-info-service cat /data/visits` | `2` |
| Restart | `docker compose restart` | — |
| After restart | `curl -s http://localhost:5000/visits` | `{"visits":2,...}` |

---

## 4. ConfigMap vs Secret

| Use ConfigMap when | Use Secret when |
| --- | --- |
| Data is non-sensitive configuration (feature flags, JSON config, log level names). | Storing credentials, tokens, TLS private keys, or anything that must be protected. |
| You want easy inspection with `kubectl describe configmap` for debugging. | You need base64 encoding at rest in the API object and tighter RBAC patterns around sensitive values. |

ConfigMaps and Secrets can both be mounted as files or exposed through `envFrom`, but Secrets are the appropriate API for confidential material (this chart still mounts Lab 11 credentials via a Secret when enabled).
