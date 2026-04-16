# Lab 12 — ConfigMaps & Persistent Volumes

## 1. Application Changes

### 1.1 Visits counter

Implemented in `app_python/app.py`:

- Added file-backed `VisitCounter` with thread lock.
- Counter file path is controlled by `VISITS_FILE`.
- Added `GET /visits` endpoint.
- `GET /` increments and persists counter.
- Startup reads existing value from file (defaults to `0`).
- Atomic write via temp file + `os.replace`.

### 1.2 Local Docker Compose persistence test

`app_python/docker-compose.yml` mounts:

- `./data:/app/data`
- `./config:/app/config:ro`

Run result:

```text
compose_visits_before_restart=2
host_file_before_restart=2
compose_visits_after_restart=2
host_file_after_restart=2
```

Counter persisted across container restart.

### 1.3 README updates

Updated `app_python/README.md`:

- documented `GET /visits`
- documented `VISITS_FILE` and `CONFIG_FILE`
- added Docker Compose persistence flow

---

## 2. ConfigMaps

### 2.1 Chart changes

Added:

- `k8s/devops-info-service/files/config.json`
- `k8s/devops-info-service/templates/configmap.yaml`

`config.json` is loaded with Helm `tpl`:

```yaml
{{ tpl (.Files.Get "files/config.json") . | indent 4 }}
```

So values are environment-specific (`values-dev.yaml` / `values-prod.yaml`).

### 2.2 Mounted file ConfigMap + env ConfigMap

Deployment mounts file config to `/config` and injects env vars via `envFrom.configMapRef`.

Runtime verification output:

```text
POD=lab12-devops-info-service-78c598c4b6-5r9cj
```

```json
{
  "applicationName": "devops-info-service-dev-reload",
  "environment": "dev",
  "featureFlags": {
    "visitsCounter": true,
    "metrics": true
  },
  "settings": {
    "showExtendedSystemInfo": true,
    "includeRequestMetadata": true
  }
}
```

```text
APP_NAME=devops-info-service-dev-reload
APP_ENV=dev
```

---

## 3. Persistent Volume

### 3.1 PVC implementation

Added `k8s/devops-info-service/templates/pvc.yaml`:

- `accessModes: [ReadWriteOnce]`
- size from values (`100Mi` in dev)
- configurable storage class

### 3.2 Required output: `kubectl get configmap,pvc`

```text
NAME                                         DATA   AGE
configmap/kube-root-ca.crt                   1      45m
configmap/lab12-devops-info-service-config   1      79s
configmap/lab12-devops-info-service-env      4      79s

NAME                                                   STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/lab12-devops-info-service-data   Bound    pvc-57764c0e-382f-42a8-bbd8-e44bf881d1d5   100Mi      RWO            standard       <unset>                 79s
```

### 3.3 Persistence test: before/after pod deletion

```text
visits_before_delete=2
old_pod=lab12-devops-info-service-78c598c4b6-5r9cj
new_pod=lab12-devops-info-service-78c598c4b6-748bn
visits_after_delete=2
```

Data survived pod recreation, confirming PVC persistence.

---

## 4. Validation

### 4.1 Python tests

```text
........                                                                 [100%]
8 passed in 0.61s
```

### 4.2 Helm lint

```text
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed
```

---

## 5. ConfigMap vs Secret

Use ConfigMap for non-sensitive configuration:

- app mode
- feature flags
- logging level
- non-sensitive JSON files

Use Secret for sensitive values:

- passwords
- tokens
- API keys
- private certificates/keys

Difference:

- ConfigMap: configuration data.
- Secret: sensitive data (with stricter access and storage hardening requirements).

---

## 6. Bonus — Hot Reload and Upgrade Pattern

### 6.1 Default ConfigMap update behavior (measured)

Patched ConfigMap and measured when mounted file changed in running pod.

Output:

```text
configmap/lab12-devops-info-service-config patched
config_update_seen=True
config_update_delay_seconds=48
```

Updated file inside pod:

```json
{
  "applicationName": "devops-info-service-dev-reload",
  "environment": "dev-hot",
  "featureFlags": {
    "visitsCounter": true,
    "metrics": true
  },
  "settings": {
    "showExtendedSystemInfo": true,
    "includeRequestMetadata": true
  }
}
```

### 6.2 `subPath` limitation

`subPath` mounts a file copy/bind target, not a live projected directory symlink. Because of this, ConfigMap file updates are not propagated automatically. For hot-updating config files, mount the whole directory (e.g. `/config`), not `subPath`.

### 6.3 Implemented reload mechanism

Implemented checksum-driven rollout in Deployment:

```yaml
annotations:
  checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

### 6.4 Helm upgrade restart evidence

Clean Helm flow (no manual ownership conflicts):

```text
old_pod=lab12-devops-info-service-68f4678fcd-kvtmx
old_checksum=6b4d0dfa995f20bf4eceb265980c17bc053f1c8bf99015351ee1d03703738586
new_pod=lab12-devops-info-service-78c598c4b6-5r9cj
new_checksum=38b3d904b6ae4e7a803cf07caa3a22ffd68eede5e246e2e149da94f75c2cce48
```

ReplicaSets confirm rollout to new template hash:

```text
NAME                                   DESIRED   CURRENT   READY
lab12-devops-info-service-68f4678fcd   0         0         <none>
lab12-devops-info-service-78c598c4b6   1         1         1
```


