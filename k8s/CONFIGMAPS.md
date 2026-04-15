# Lab 12 — ConfigMaps & Persistent Volumes

## 1. Application changes

### Visits counter implementation

- Added a file-backed visits counter in `app_python/app.py`.
- Counter file path is configurable via `VISITS_FILE` (default: `/data/visits`).
- On each `GET /` request, counter is incremented and atomically persisted.
- Added `GET /visits` endpoint returning current counter value.
- Added thread-safe access with `threading.Lock`.

### New endpoint

```json
GET /visits
{
  "visits": 4,
  "storage_file": "/data/visits"
}
```

### Local Docker test evidence

Used `app_python/docker-compose.yml` with a bind mount:

```yaml
volumes:
  - ./data:/data
```

Evidence:

```text
visits_before_restart={"storage_file":"/data/visits","visits":4}
file_before_restart=4
visits_after_restart={"storage_file":"/data/visits","visits":4}
file_after_restart=4
```

Counter value persisted after container restart.

---

## 2. ConfigMap implementation

### Structure

1. `k8s/devops-info-service/files/config.json` — file-based app config.
2. `templates/configmap.yaml` — ConfigMap from file using `.Files.Get`.
3. `templates/configmap-env.yaml` — key/value ConfigMap for env injection.

### `config.json` content

```json
{
  "applicationName": "devops-info-service",
  "environment": "dev",
  "settings": {
    "enableVisitsCounter": true,
    "defaultLogLevel": "info",
    "metricsEnabled": true
  }
}
```

### Mount as file

In Deployment:

- Volume from ConfigMap `...-config`
- Mounted directory: `/config` (no `subPath`)
- Effective file path: `/config/config.json`

### Env vars from ConfigMap

In Deployment:

```yaml
envFrom:
  - configMapRef:
      name: <release>-devops-info-service-env
```

Injected keys:

- `APP_ENV`
- `LOG_LEVEL`
- `FEATURE_VISITS`

### Verification outputs

```text
$ kubectl get configmap,pvc
NAME                                                 DATA   AGE
configmap/kube-root-ca.crt                           1      22d
configmap/lab12-release-devops-info-service-config   1      10m
configmap/lab12-release-devops-info-service-env      3      10m

NAME                                                           STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/lab12-release-devops-info-service-data   Bound    pvc-ea7f1950-cd76-4fe1-a1a8-921b3dd0af18   100Mi      RWO            standard       <unset>                 10m
```

```text
$ kubectl exec <pod> -- cat /config/config.json
{
  "applicationName": "devops-info-service",
  "environment": "dev",
  "settings": {
    "enableVisitsCounter": true,
    "defaultLogLevel": "info",
    "metricsEnabled": true
  }
}
```

```text
$ kubectl exec <pod> -- printenv | grep -E 'APP_ENV|LOG_LEVEL|FEATURE_VISITS'
LOG_LEVEL=info
APP_ENV=dev
FEATURE_VISITS=true
```

---

## 3. Persistent Volume implementation

### PVC configuration

Created `templates/pvc.yaml`:

- `accessModes: [ReadWriteOnce]`
- requested storage from values (`persistence.size`, default `100Mi`)
- optional `storageClassName` from values (`persistence.storageClass`)

### Deployment mount

- Added `data-volume` in Deployment.
- If `persistence.enabled=true` → PVC mount at `/data`.
- If disabled → `emptyDir` fallback.
- App writes visits counter to `/data/visits`.

### Persistence test evidence

Before deleting pod:

```text
{"storage_file":"/data/visits","visits":4}
```

Deleted pod:

```text
$ kubectl delete pod lab12-release-devops-info-service-677788c695-d2pfn
pod "lab12-release-devops-info-service-677788c695-d2pfn" deleted from default namespace
```

Replacement pod:

```text
NEW_POD=lab12-release-devops-info-service-677788c695-2zz67
```

After replacement started:

```text
{"storage_file":"/data/visits","visits":4}
```

Counter value stayed the same, confirming PVC persistence.

---

## 4. ConfigMap vs Secret

| Aspect | ConfigMap | Secret |
|---|---|---|
| Data type | Non-sensitive config | Sensitive data (passwords, keys, tokens) |
| Storage | Plain in etcd (unless etcd encryption is enabled) | Base64-encoded object; intended for sensitive values |
| Typical use | App settings, feature flags, config files | Credentials, API keys, certs |
| Access pattern | `envFrom`, `configMapRef`, mounted files | `secretRef`, mounted secret volumes |

Use **ConfigMap** for normal configuration and **Secret** for confidential values.

---

## Bonus — ConfigMap hot reload

### 1. Default update behavior (mounted file)

Patched ConfigMap and measured when change appeared in `/config/config.json`.

```text
TOKEN=reload-1776281181
DELAY_SECONDS=11
```

Observed delay confirms mounted ConfigMap updates are not instantaneous.

### 2. Why `subPath` should be avoided for dynamic config

- `subPath` mounts a copied file path at container start.
- It does not track future ConfigMap updates.
- For auto-refresh behavior, mount full directory (as implemented: `/config`).

### 3. Implemented reload approach

Implemented **pod restart via checksum annotations** in Deployment:

- `checksum/config-file` from `files/config.json`
- `checksum/config-env` from rendered env ConfigMap
- `checksum/pvc` from PVC template

Any checksum change updates Pod template and triggers rollout.

### 4. Helm upgrade rollout evidence

Changed `configEnv.featureVisits` via Helm upgrade:

```text
FEATURE_BEFORE=false
CHECKSUM_ENV_BEFORE=519d264e9e9a17872144c77e6ce2691cbffc9b5e8ec344bd51e4a79d83099c04
CHECKSUM_ENV_AFTER=555aa15be1ea6b9afcbd8bd5a53d69093cf16f067951c37c98370fde0d6b695e
FEATURE_AFTER=true
```

Rollout status:

```text
deployment "lab12-release-devops-info-service" successfully rolled out
```

Old vs new pods:

```text
before:
lab12-release-devops-info-service-fcc885bc-bdwc7
lab12-release-devops-info-service-fcc885bc-gqc92
lab12-release-devops-info-service-fcc885bc-rg8gf

after:
lab12-release-devops-info-service-677788c695-kmdwd
lab12-release-devops-info-service-677788c695-qhx5j
lab12-release-devops-info-service-677788c695-vr565
```

This demonstrates checksum-driven restart on ConfigMap-related change.
