# Lab 12 - ConfigMaps and Persistent Volumes


## Task 1 - Application Persistence Upgrade

### Application changes

The Flask app in [app_python/app.py](/home/setterwars/Documents/IU/DevOps-Core-Course/app_python/app.py) was extended with:

- A file-backed visits counter stored in `/data/visits` by default.
- A new `GET /visits` endpoint returning the current count and backing file path.
- Startup initialization that creates the visits file if it does not exist.
- A `threading.Lock` around counter updates to prevent overlapping writes inside one process.
- Runtime config loading from `/config/config.json` so the app can expose ConfigMap-backed settings.

Implementation summary:

- `read_visits()` reads the integer value from disk and falls back to `0`.
- `increment_visits()` reads, increments, writes, and returns the new value.
- `write_visits()` flushes and `fsync`s the file so the counter is persisted to disk.
- `load_runtime_config()` reads the mounted JSON config file and merges it with env-driven defaults.

### New endpoint

- `GET /visits`
- Example response:

```json
{"count":4,"storage_file":"/data/visits"}
```

### Local Docker testing

The local Docker setup was added in [app_python/docker-compose.yml](/home/setterwars/Documents/IU/DevOps-Core-Course/app_python/docker-compose.yml) and mounts:

- `./data:/data`
- `./config:/config:ro`

The app README was updated in [app_python/README.md](/home/setterwars/Documents/IU/DevOps-Core-Course/app_python/README.md).

### Local verification evidence

`docker compose ps`

```text
NAME               IMAGE            COMMAND           SERVICE   CREATED         STATUS         PORTS
app_python-app-1   app_python-app   "python app.py"   app       9 seconds ago   Up 8 seconds   0.0.0.0:5000->5000/tcp, [::]:5000->5000/tcp
```

First local request to `/`

```json
{"configuration":{"appName":"devops-info-service","environment":"docker-compose","featureFlags":{"configHotReload":true,"visitsCounter":true},"settings":{"banner":"local-docker","logLevel":"INFO"}},"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"},{"description":"Persistent visits counter","method":"GET","path":"/visits"},{"description":"Prometheus metrics","method":"GET","path":"/metrics"}],"request":{"client_ip":"10.10.3.1","method":"GET","path":"/","user_agent":"curl/8.18.0"},"runtime":{"current-time":"2026-04-12T17:27:28.395168+00:00","timezone":"UTC","uptime_human":"0 hours, 0 minutes","uptime_seconds":18},"service":{"description":"DevOps course info service","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"x86_64","cpu_count":8,"hostname":"234c11e07b73","platform":"Linux","platform_version":"#12-Ubuntu SMP PREEMPT_DYNAMIC Thu Apr  2 10:21:43 UTC 2026","python_version":"3.13.13"},"visits":{"count":1,"storage_file":"/data/visits"}}
```

Counter after restart:

```text
$ cat data/visits
4

$ curl -s http://127.0.0.1:5000/visits
{"count":4,"storage_file":"/data/visits"}
```

That confirms the counter survived the container restart.

### Automated test evidence

Host Python did not have `pip` or installed dependencies, so tests were run in a temporary Python container against the repo source:

```text
............                                                             [100%]
12 passed, 1 warning in 0.22s
```

## Task 2 - ConfigMaps

### Chart files

Added:

- [k8s/myapp/files/config.json](/home/setterwars/Documents/IU/DevOps-Core-Course/k8s/myapp/files/config.json)
- [k8s/myapp/templates/configmap.yaml](/home/setterwars/Documents/IU/DevOps-Core-Course/k8s/myapp/templates/configmap.yaml)

Updated:

- [k8s/myapp/templates/deployment.yml](/home/setterwars/Documents/IU/DevOps-Core-Course/k8s/myapp/templates/deployment.yml)
- [k8s/myapp/values.yaml](/home/setterwars/Documents/IU/DevOps-Core-Course/k8s/myapp/values.yaml)
- [k8s/myapp/values-dev.yaml](/home/setterwars/Documents/IU/DevOps-Core-Course/k8s/myapp/values-dev.yaml)
- [k8s/myapp/values-prod.yaml](/home/setterwars/Documents/IU/DevOps-Core-Course/k8s/myapp/values-prod.yaml)

### ConfigMap structure

Two ConfigMaps are created:

1. `lab12-myapp-config`
   - Contains `config.json`
   - Loaded from `files/config.json` using `tpl (.Files.Get ...)`

2. `lab12-myapp-env`
   - Contains key-value env vars:
   - `APP_NAME`
   - `APP_ENV`
   - `LOG_LEVEL`
   - `APP_CONFIG_PATH`
   - `VISITS_FILE`

### Mounted file configuration

The deployment mounts `lab12-myapp-config` as a directory:

- Volume name: `config-volume`
- Mount path: `/config`
- Effective file path: `/config/config.json`

Directory mount was used deliberately instead of `subPath` so mounted config updates can propagate into the pod.

### Environment variable injection

The deployment uses:

```yaml
envFrom:
  - secretRef:
      name: {{ include "myapp.fullname" . }}-secret
  - configMapRef:
      name: {{ include "myapp.fullname" . }}-env
```

That injects all keys from the env ConfigMap at once.

### Verification outputs

`kubectl get configmap,pvc`

```text
NAME                           DATA   AGE
configmap/kube-root-ca.crt     1      23d
configmap/lab12-myapp-config   1      28s
configmap/lab12-myapp-env      5      28s

NAME                                     STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/lab12-myapp-data   Bound    pvc-2b08a763-2be7-41d4-a462-0e58e29652aa   100Mi      RWO            standard       <unset>                 28s
```

Mounted file inside pod:

```text
$ kubectl exec deploy/lab12-myapp -- cat /config/config.json
{
  "appName": "devops-info-service",
  "environment": "dev",
  "featureFlags": {
    "visitsCounter": true,
    "configHotReload": true
  },
  "settings": {
    "logLevel": "INFO",
    "greeting": "Hello from Helm checksum rollout"
  }
}
```

Environment variables inside pod:

```text
APP_CONFIG_PATH=/config/config.json
APP_ENV=dev
APP_NAME=devops-info-service
LOG_LEVEL=INFO
VISITS_FILE=/data/visits
```

## Task 3 - Persistent Volumes

### PVC implementation

The PVC is defined in [k8s/myapp/templates/pvc.yaml](/home/setterwars/Documents/IU/DevOps-Core-Course/k8s/myapp/templates/pvc.yaml).

Configuration:

- Access mode: `ReadWriteOnce`
- Requested size: `100Mi`
- Storage class: configurable through `persistence.storageClass`
- Current cluster binding: default `standard` storage class from `minikube`

### Volume mount configuration

The deployment mounts the PVC as:

- Volume name: `data-volume`
- Mount path: `/data`
- Visits file path: `/data/visits`

An init container was added to fix PVC ownership before the app starts:

```yaml
initContainers:
  - name: volume-permissions
    image: busybox:1.36
    command: ["sh", "-c", "mkdir -p /data && chown -R 999:999 /data"]
```

That matches the app container UID/GID (`999`) created in the Docker image.

### Persistence test evidence

Pre-deletion consistency check from the same pod shell:

```text
BEFORE=4
ROOT=5
AFTER_ENDPOINT=5
AFTER_FILE=5
```

Pod deletion command:

```text
$ kubectl delete pod lab12-myapp-85dd96784d-xlfpx
pod "lab12-myapp-85dd96784d-xlfpx" deleted
```

Replacement pod:

```text
NAME                           READY   STATUS    RESTARTS   AGE   IP            NODE
lab12-myapp-85dd96784d-rfgcx   1/1     Running   0          27s   10.244.0.60   minikube
```

Counter after new pod started:

```text
AFTER_RESTART_ENDPOINT=5
AFTER_RESTART_FILE=5
```

That proves the data survived pod deletion because the replacement pod read the same value from the PVC.

## Task 4 - ConfigMap vs Secret

### When to use ConfigMap

Use ConfigMaps for non-sensitive configuration:

- app name
- runtime environment
- feature flags
- log level
- config files like `config.json`

### When to use Secret

Use Secrets for sensitive values:

- passwords
- tokens
- API keys
- certificates
- private connection strings

### Key differences

- ConfigMaps store plain non-sensitive configuration.
- Secrets are intended for sensitive data and are base64-encoded in manifests.
- ConfigMaps are appropriate for data you are comfortable exposing in logs or repo history.
- Secrets should be combined with stronger controls such as RBAC, external secret stores, and restricted access.

This chart already keeps credentials in a separate Secret template, while all non-sensitive app settings are moved into ConfigMaps.

## Bonus - ConfigMap Hot Reload

### Default update behavior test

Live ConfigMap patch:

```text
configmap/lab12-myapp-config patched
```

Measured mounted-file update delay:

```text
UPDATE_DELAY_SECONDS=41.8
```

Mounted file after propagation:

```json
{
  "appName": "devops-info-service",
  "environment": "dev",
  "featureFlags": {
    "visitsCounter": true,
    "configHotReload": true
  },
  "settings": {
    "logLevel": "INFO",
    "greeting": "Hello from delayed patch"
  }
}
```

Application output after the file changed, without restarting the pod:

```text
Hello from delayed patch
```

This matches normal Kubernetes behavior: mounted ConfigMaps update asynchronously, not instantly.

### Chosen reload approach

The application reload approach is request-time file reload:

- The app reads `/config/config.json` for every `/` request.
- Once Kubernetes updates the mounted file, the next request returns the new config.
- No sidecar and no manual restart are needed for the app-level reload path.

### `subPath` limitation

`subPath` was intentionally avoided for the config file mount.

Why:

- A normal ConfigMap directory mount is updated by Kubernetes.
- A `subPath` mount behaves like a copied file bind mount.
- That copied file does not receive ConfigMap updates automatically.

Use `subPath` only when you need to place one file at an exact existing path and you accept that live updates will not appear automatically.

### Helm upgrade pattern with checksum annotation

The deployment template includes:

```yaml
annotations:
  checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

That means a Helm-rendered ConfigMap change changes the pod template hash and forces a rollout.

Evidence:

Before Helm upgrade:

```text
lab12-myapp-85dd96784d-rfgcx
```

After changing `k8s/myapp/files/config.json` and running `helm upgrade`:

```text
NAME                           READY   STATUS        RESTARTS   AGE
lab12-myapp-565dd789f8-nxp6p   1/1     Running       0          28s
lab12-myapp-85dd96784d-rfgcx   1/1     Terminating   0          3m26s
```

The new pod served the updated config:

```text
"greeting": "Hello from Helm checksum rollout"
```

And the app response included:

```json
"settings":{"greeting":"Hello from Helm checksum rollout","logLevel":"INFO"}
```

## Command summary

Main verification commands used:

```bash
docker compose up --build -d
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/visits
cat app_python/data/visits
docker compose restart app

helm upgrade --install lab12 k8s/myapp -f k8s/myapp/values-dev.yaml \
  --set image.repository=lab12-devops-info-service \
  --set image.tag=v2 \
  --set service.nodePort=30081 \
  --wait --timeout 5m

kubectl get configmap,pvc
kubectl exec deploy/lab12-myapp -- cat /config/config.json
kubectl exec deploy/lab12-myapp -- printenv | grep APP_
kubectl delete pod <pod-name>
kubectl wait --for=condition=ready pod/<new-pod-name> --timeout=180s
```