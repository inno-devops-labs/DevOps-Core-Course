# Lab 12 — ConfigMaps & Persistent Volumes

## 1. Application Changes

The application was updated to persist a visits counter in a file.

Implemented changes:
- each request to `/` increments the visits counter
- the counter is stored in `/data/visits`
- new endpoint `/visits` returns the current counter value
- on startup, the application creates the file if it does not exist
- local Docker Compose mounts `./data` to `/data`

### Local Docker Compose test

Run:

```bash
docker compose up --build
curl http://localhost:8000/
curl http://localhost:8000/
curl http://localhost:8000/visits
cat ./data/visits
```

Observed output:

```text
{"visits":2,"file":"/data/visits"}
2
```

After restart:

```bash
docker compose down
docker compose up
curl http://localhost:8000/visits
cat ./data/visits
```

Observed output:

```text
{"visits":2,"file":"/data/visits"}
2
```

This confirms that the counter persists across container restarts.

---

## 2. ConfigMap Implementation

### Chart structure additions

Added files:
- `k8s/python-app/files/config.json`
- `k8s/python-app/templates/configmap.yaml`
- `k8s/python-app/templates/pvc.yaml`

### File-based ConfigMap

A ConfigMap was created from `files/config.json` and mounted inside the pod as a file.

Example rendered ConfigMap content:

```json
{
  "applicationName": "python-app",
  "environment": "dev",
  "featureFlags": {
    "visitsEnabled": true,
    "metricsEnabled": true,
    "vaultEnabled": false
  },
  "settings": {
    "logLevel": "info",
    "visitsFile": "/data/visits"
  }
}
```

### Environment variable ConfigMap

A second ConfigMap was created for environment variables:
- `APP_ENV`
- `LOG_LEVEL`
- `FEATURE_VISITS_ENABLED`
- `FEATURE_METRICS_ENABLED`

### Verification

Commands:

```bash
kubectl get configmap,pvc
kubectl exec -it python-app-dev-78f6bb67f5-wp9km -- cat /config/config.json
kubectl exec -it python-app-dev-78f6bb67f5-wp9km -- printenv | grep -E '^(APP_ENV|LOG_LEVEL|FEATURE_VISITS_ENABLED|FEATURE_METRICS_ENABLED|APP_NAME|APP_VERSION|APP_DESCRIPTION|VISITS_FILE|APP_USERNAME|APP_PASSWORD)='
```

Observed output:

```text
NAME                              DATA   AGE
configmap/kube-root-ca.crt        1      19d
configmap/python-app-dev-config   1      44s
configmap/python-app-dev-env      4      44s
```

Mounted file:

```json
{
  "applicationName": "python-app",
  "environment": "dev",
  "featureFlags": {
    "visitsEnabled": true,
    "metricsEnabled": true,
    "vaultEnabled": false
  },
  "settings": {
    "logLevel": "info",
    "visitsFile": "/data/visits"
  }
}
```

Environment variables in pod:

```text
APP_ENV=dev
FEATURE_VISITS_ENABLED=true
LOG_LEVEL=debug
APP_PASSWORD=dev-password
APP_USERNAME=dev-user
APP_NAME=python-app
APP_VERSION=lab12-dev
APP_DESCRIPTION=DevOps course info service
FEATURE_METRICS_ENABLED=true
VISITS_FILE=/data/visits
```

This confirms:
- ConfigMap file mount works
- ConfigMap environment variable injection works
- Secret-based variables from Lab 11 are still present

---

## 3. Persistent Volume

### PVC configuration

A PersistentVolumeClaim was added to the Helm chart with:
- access mode: `ReadWriteOnce`
- requested size: `100Mi`
- default storage class from Minikube (`standard`)

Observed PVC:

```text
persistentvolumeclaim/python-app-dev-data   Bound    pvc-40088b21-6b4e-4d00-98b0-97168662cca0   100Mi   RWO   standard
```

### Volume mount

The PVC is mounted into the application container at:

```text
/data
```

The visits counter file is stored at:

```text
/data/visits
```

### Persistence test

Before pod deletion:

```bash
curl http://127.0.0.1:54690/
curl http://127.0.0.1:54690/visits
kubectl exec -it python-app-dev-fb89d59f4-4wx47 -- cat /data/visits
```

Observed output:

```text
{"visits":2,"file":"/data/visits"}
2
```

Delete pod:

```bash
kubectl delete pod python-app-dev-fb89d59f4-4wx47
kubectl get pods -l app.kubernetes.io/instance=python-app-dev -w
```

Observed new pod:

```text
python-app-dev-fb89d59f4-sp9lf   1/1   Running   0   17s
```

After pod recreation:

```bash
kubectl exec -it python-app-dev-fb89d59f4-sp9lf -- cat /data/visits
curl http://127.0.0.1:54690/visits
```

Observed output:

```text
2
{"visits":2,"file":"/data/visits"}
```

This confirms that the data survives pod deletion and recreation.

---

## 4. ConfigMap vs Secret

### ConfigMap
Use ConfigMap for:
- non-sensitive application settings
- feature flags
- environment names
- log levels
- JSON/YAML/text configuration files

### Secret
Use Secret for:
- passwords
- API keys
- tokens
- credentials
- any sensitive data

### Key differences
- ConfigMaps are for **non-sensitive** configuration
- Secrets are for **sensitive** data
- both can be mounted as files or injected as environment variables
- Secrets should be protected with RBAC and, in production, encryption at rest and/or an external secret manager

---

## 5. Conclusion

Implemented in this lab:
- visits counter stored in a file
- `/visits` endpoint
- Docker Compose volume for local persistence
- file-based ConfigMap mounted at `/config/config.json`
- environment variable ConfigMap injected into the pod
- PersistentVolumeClaim mounted at `/data`
- persistence verified after pod deletion

This satisfies the Lab 12 requirements for ConfigMaps, Persistent Volumes, and documentation.
