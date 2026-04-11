# Lab 12 - ConfigMaps and Persistent Volumes

## 1. Application Changes

### 1.1 Visits counter implementation

Implemented in `app_python/app.py`:

- file-based visits counter using `VISITS_FILE` (default `/data/visits`)
- thread lock around increment
- atomic file write using temp file + `os.replace`
- new endpoint `GET /visits`
- root endpoint `GET /` increments and persists counter

### 1.2 Tests and local validation

Application tests (WSL, April 5, 2026):

```bash
$ cd app_python
$ pytest -q
......                                                                                             [100%]
6 passed in 2.77s
```

Added for local container testing:

- `app_python/docker-compose.yml` with `./data:/data`
- `VISITS_FILE=/data/visits`

---

## 2. ConfigMap Implementation

### 2.1 Helm templates

Added:

- `k8s/devops-python/files/config.json`
- `k8s/devops-python/templates/configmap.yaml`

Deployment mounts config as directory:

- `/config/config.json`

Deployment injects env ConfigMap via `envFrom.configMapRef`.

### 2.2 Helm validation evidence

```bash
$ helm lint k8s/devops-python
==> Linting k8s/devops-python
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

Rendered manifest checks:

```bash
$ grep -n "kind: ConfigMap" /tmp/lab12-render.yaml
33:kind: ConfigMap
61:kind: ConfigMap

$ grep -n "kind: PersistentVolumeClaim" /tmp/lab12-render.yaml
79:kind: PersistentVolumeClaim

$ grep -n "checksum/config:" /tmp/lab12-render.yaml
146:        checksum/config: a212be7ce0073c29c7cdc3bacea520610c2ae1e692cef33e198a09d075c224ee

$ grep -n "mountPath: \"/config\"" /tmp/lab12-render.yaml
174:              mountPath: "/config"

$ grep -n "mountPath: \"/data\"" /tmp/lab12-render.yaml
177:              mountPath: "/data"

$ grep -n "VISITS_FILE:" /tmp/lab12-render.yaml
75:  VISITS_FILE: "/data/visits"
```

### 2.3 Runtime ConfigMap evidence

```bash
$ kubectl -n lab12 get configmap,pvc,pods
NAME                                           DATA   AGE
configmap/lab12-release-devops-python-config   1      17s
configmap/lab12-release-devops-python-env      5      17s
...
```

Mounted file inside pod:

```json
{
  "applicationName": "devops-info-service",
  "environment": "dev",
  "featureFlags": {
    "visitsCounter": true,
    "metricsEnabled": true
  },
  "settings": {
    "logLevel": "debug",
    "listenHost": "0.0.0.0",
    "listenPort": "8080",
    "visitsFile": "/data/visits"
  }
}
```

Environment variables inside pod:

```bash
APP_NAME=devops-info-service
VISITS_FILE=/data/visits
APP_MODE=dev
APP_ENV=dev
FEATURE_METRICS=true
FEATURE_VISITS=true
```

---

## 3. Persistent Volume Implementation

### 3.1 PVC template and mount

Added:

- `k8s/devops-python/templates/pvc.yaml`

PVC settings:

- access mode: `ReadWriteOnce`
- requested storage: `100Mi` (dev)
- mounted in pod at `/data`

### 3.2 Runtime PVC evidence

```bash
$ kubectl -n lab12 get pvc,pods
NAME                                                     STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS
persistentvolumeclaim/lab12-release-devops-python-data   Bound    pvc-d3a12c94-fb88-431d-8a3d-e7f1f17d9fe5   100Mi      RWO            standard

NAME                                              READY   STATUS    RESTARTS   AGE
pod/lab12-release-devops-python-d9bc49ff8-bpcwg   1/1     Running   0          17s
```

### 3.3 Persistence before/after pod recreation

Before deletion:

- `GET /` twice returned visits counts `1` then `2`
- `GET /visits` returned `"visits":2`
- `cat /data/visits` returned `2`

After deleting pod and waiting for rollout:

- `cat /data/visits` in new pod returned `2`

This confirms data persisted across pod restart using PVC.

---

## 4. ConfigMap vs Secret

- ConfigMap: non-sensitive config (feature flags, app settings, config files).
- Secret: sensitive values (credentials/tokens), used in Lab 11.

Use ConfigMap for non-confidential data and Secret/Vault for confidential data.

---

## 5. Bonus - ConfigMap Hot Reload

### 5.1 Checksum-based rollout trigger implemented

In deployment template:

```yaml
checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

This triggers Deployment rollout when ConfigMap content changes.

### 5.2 `subPath` limitation

Documented: `subPath` ConfigMap mounts do not receive live updates because mounted file is not updated projection.

### 5.3 Default update behavior

Documented: ConfigMap projected file updates are not instant; delay can be up to a few minutes due to kubelet sync/cache behavior.

---

## 6. Notes and Resolution Log

During runtime validation, first install attempt failed due to NodePort collision (`30080` already allocated). Resolved by deploying Lab 12 release with `service.type=ClusterIP` for verification.

Also observed transient `port-forward` disconnect after pod deletion (`network namespace ... is closed`), which is expected when forwarded pod is terminated; restarting `port-forward` resolved it.

---

## 7. Final Status

Lab 12 required tasks and bonus are implemented and validated with real runtime evidence on April 5, 2026:

- Task 1: visits persistence + `/visits` endpoint
- Task 2: ConfigMap file mount + env injection
- Task 3: PVC + persistence across pod recreation
- Task 4: documentation complete
- Bonus: checksum restart pattern + update behavior/subPath analysis
