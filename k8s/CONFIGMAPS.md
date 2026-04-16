# Lab 12 - ConfigMaps and Persistent Volumes

Validated on `2026-04-16` with:

- `helm v4.1.3+gc94d381`
- `kubectl v1.35.3`
- `kind v0.31.0`
- `Docker Compose v5.1.0`
- Kubernetes node `lab09-control-plane` on `v1.35.0`

Environment note:

- The host kubeconfig still pointed at an unusable forwarded API endpoint, so live cluster validation used `docker exec lab09-control-plane ... --kubeconfig=/etc/kubernetes/admin.conf`.
- Local Docker Compose validation was run from `app_python/docker-compose.yml`.

## 1. Application Changes

### Implementation summary

Relevant files:

- `app_python/app.py`
- `app_python/tests/test_app.py`
- `app_python/docker-compose.yml`
- `app_python/README.md`

Application changes made for Lab 12:

- Added a persistent visits counter stored in `VISITS_FILE_PATH`.
- Added a new `GET /visits` endpoint.
- Updated `GET /` to increment the counter on every request.
- Added file locking with `fcntl.flock(...)` so reads and writes stay consistent across concurrent requests and multiple processes.
- Added `APP_CONFIG_PATH` support and JSON config loading from `/config/config.json`.
- The root response now exposes both the current `visits` state and the loaded `configuration`.

### Local Docker validation

The local compose file binds `./data` into the container and sets `VISITS_FILE_PATH=/data/visits`.

Because Docker created the host directory as `root:root`, the compose service runs as `root` locally so it can initialize the bind mount. The Kubernetes deployment still runs as non-root (`10001`) and uses `fsGroup: 10001`.

Initial counter:

```bash
$ curl -s http://127.0.0.1:5000/visits
{"visits":0,"path":"/data/visits","timestamp":"2026-04-16T19:50:43.029673+00:00"}
```

After hitting the root endpoint:

```bash
$ curl -s http://127.0.0.1:5000/
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI","variant":"primary"},"system":{"hostname":"baa3776a1a6f","platform":"Linux","platform_version":"#20~24.04.1-Ubuntu SMP PREEMPT_DYNAMIC Thu Mar 19 01:28:37 UTC 2","architecture":"x86_64","cpu_count":12,"python_version":"3.13.13"},"runtime":{"uptime_seconds":8,"uptime_human":"0 hours, 0 minutes","current_time":"2026-04-16T19:50:47.960120+00:00","timezone":"UTC"},"request":{"client_ip":"172.19.0.1","user_agent":"curl/8.5.0","method":"GET","path":"/"},"visits":{"count":1,"path":"/data/visits"},"configuration":{"path":"/config/config.json","loaded":false,"values":{}},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Liveness probe"},{"path":"/ready","method":"GET","description":"Readiness probe"},{"path":"/visits","method":"GET","description":"Persistent visits counter"},{"path":"/metrics","method":"GET","description":"Prometheus metrics"}]}

$ curl -s http://127.0.0.1:5000/
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI","variant":"primary"},"system":{"hostname":"baa3776a1a6f","platform":"Linux","platform_version":"#20~24.04.1-Ubuntu SMP PREEMPT_DYNAMIC Thu Mar 19 01:28:37 UTC 2","architecture":"x86_64","cpu_count":12,"python_version":"3.13.13"},"runtime":{"uptime_seconds":13,"uptime_human":"0 hours, 0 minutes","current_time":"2026-04-16T19:50:53.003931+00:00","timezone":"UTC"},"request":{"client_ip":"172.19.0.1","user_agent":"curl/8.5.0","method":"GET","path":"/"},"visits":{"count":2,"path":"/data/visits"},"configuration":{"path":"/config/config.json","loaded":false,"values":{}},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Liveness probe"},{"path":"/ready","method":"GET","description":"Readiness probe"},{"path":"/visits","method":"GET","description":"Persistent visits counter"},{"path":"/metrics","method":"GET","description":"Prometheus metrics"}]}
```

Host-side file content:

```bash
$ cat app_python/data/visits
2
```

After container restart:

```bash
$ docker compose restart devops-info
 Container devops-info-lab12 Restarting
 Container devops-info-lab12 Started

$ curl -s http://127.0.0.1:5000/visits
{"visits":2,"path":"/data/visits","timestamp":"2026-04-16T19:51:05.086483+00:00"}
```

Conclusion:

- The file-backed counter survives container recreation.
- Local Docker runs without a mounted ConfigMap, so `configuration.loaded` is `false`. That is expected outside Kubernetes.

## 2. ConfigMap Implementation

Relevant chart files:

- `k8s/devops-info/files/config.json`
- `k8s/devops-info/templates/configmap.yaml`
- `k8s/devops-info/templates/deployment.yaml`
- `k8s/devops-info/templates/_helpers.tpl`
- `k8s/devops-info/values.yaml`

### File-backed ConfigMap

`templates/configmap.yaml` creates:

- `devops-info-config` from `files/config.json`
- `devops-info-env` from `.Values.env`

The mounted JSON file content is:

```json
{
  "application": {
    "name": "devops-info-service",
    "environment": "development"
  },
  "features": {
    "visitsCounter": true,
    "prometheusMetrics": true,
    "healthChecks": true
  },
  "settings": {
    "logFormat": "json",
    "configSource": "helm-configmap",
    "persistencePath": "/data/visits"
  }
}
```

### ConfigMap mounts and env injection

Deployment behavior:

- `devops-info-config` is mounted at `/config`
- The app reads `/config/config.json`
- `devops-info-env` is injected with `envFrom.configMapRef`
- Helm secrets from Lab 11 are still injected with `envFrom.secretRef`

### Verification output

Resources:

```bash
$ kubectl get configmap,pvc -n devops-lab12
NAME                           DATA   AGE
configmap/devops-info-config   1      54s
configmap/devops-info-env      10     54s
configmap/kube-root-ca.crt     1      67s

NAME                                     STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/devops-info-data   Bound    pvc-94bcae34-aa16-48b1-9d08-e418f1b44200   100Mi      RWO            standard       <unset>                 54s
```

Mounted file in the pod:

```bash
$ kubectl exec -n devops-lab12 devops-info-79df6fcbc8-54fxx -- cat /config/config.json
{
  "application": {
    "name": "devops-info-service",
    "environment": "development"
  },
  "features": {
    "visitsCounter": true,
    "prometheusMetrics": true,
    "healthChecks": true
  },
  "settings": {
    "logFormat": "json",
    "configSource": "helm-configmap",
    "persistencePath": "/data/visits"
  }
}
```

Environment variables inside the pod:

```bash
$ kubectl exec -n devops-lab12 devops-info-79df6fcbc8-54fxx -- sh -c 'printenv | grep -E "^(APP_|SERVICE_|VISITS_FILE_PATH|LOG_LEVEL|HOST|PORT)" | sort'
APP_CONFIG_PATH=/config/config.json
APP_ENV=development
APP_PASSWORD=lab12-pass
APP_USERNAME=lab12-user
HOST=0.0.0.0
HOSTNAME=devops-info-79df6fcbc8-54fxx
LOG_LEVEL=INFO
PORT=5000
SERVICE_DESCRIPTION=DevOps course info service packaged with Helm
SERVICE_NAME=devops-info-service
SERVICE_VARIANT=primary
SERVICE_VERSION=1.0.0
VISITS_FILE_PATH=/data/visits
```

App-level proof that the mounted file is being read:

```bash
$ kubectl exec -n devops-lab12 devops-info-79df6fcbc8-9dh2k -- python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5000/').read().decode())"
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service packaged with Helm","framework":"FastAPI","variant":"primary"},"system":{"hostname":"devops-info-79df6fcbc8-9dh2k","platform":"Linux","platform_version":"#20~24.04.1-Ubuntu SMP PREEMPT_DYNAMIC Thu Mar 19 01:28:37 UTC 2","architecture":"x86_64","cpu_count":12,"python_version":"3.13.13"},"runtime":{"uptime_seconds":49,"uptime_human":"0 hours, 0 minutes","current_time":"2026-04-16T19:57:12.890001+00:00","timezone":"UTC"},"request":{"client_ip":"127.0.0.1","user_agent":"Python-urllib/3.13","method":"GET","path":"/"},"visits":{"count":5,"path":"/data/visits"},"configuration":{"path":"/config/config.json","loaded":true,"values":{"application":{"name":"devops-info-service","environment":"development"},"features":{"visitsCounter":true,"prometheusMetrics":true,"healthChecks":true},"settings":{"logFormat":"json","configSource":"helm-configmap","persistencePath":"/data/visits"}}},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Liveness probe"},{"path":"/ready","method":"GET","description":"Readiness probe"},{"path":"/visits","method":"GET","description":"Persistent visits counter"},{"path":"/metrics","method":"GET","description":"Prometheus metrics"}]}
```

## 3. Persistent Volume Implementation

Relevant files:

- `k8s/devops-info/templates/pvc.yaml`
- `k8s/devops-info/templates/deployment.yaml`
- `k8s/devops-info/values.yaml`
- `k8s/common-lib/templates/_security.tpl`

### PVC configuration

The chart creates `devops-info-data` with:

- access mode `ReadWriteOnce`
- requested capacity `100Mi`
- configurable `storageClass`
- mount path `/data`

Why `fsGroup` was added:

- The app image runs as `10001:10001`
- Kubernetes volumes are typically mounted as `root`
- `fsGroup: 10001` allows the non-root container to write to the PVC-backed `/data` directory

### Persistence test

Before pod deletion:

```bash
$ kubectl exec -n devops-lab12 devops-info-79df6fcbc8-54fxx -- python -c "import json, urllib.request; [print(json.load(urllib.request.urlopen('http://127.0.0.1:5000/'))['visits']['count']) for _ in range(3)]"
2
3
4

$ kubectl exec -n devops-lab12 devops-info-79df6fcbc8-54fxx -- cat /data/visits
4

$ kubectl exec -n devops-lab12 devops-info-79df6fcbc8-54fxx -- python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5000/visits').read().decode())"
{"visits":4,"path":"/data/visits","timestamp":"2026-04-16T19:56:16.178180+00:00"}
```

Delete the pod:

```bash
$ kubectl delete pod -n devops-lab12 devops-info-79df6fcbc8-54fxx
pod "devops-info-79df6fcbc8-54fxx" deleted from devops-lab12 namespace

$ kubectl wait --for=condition=Ready pod -l app.kubernetes.io/instance=devops-info -n devops-lab12 --timeout=180s
pod/devops-info-79df6fcbc8-9dh2k condition met
```

After the new pod started:

```bash
$ kubectl get pods -n devops-lab12 -o wide
NAME                           READY   STATUS    RESTARTS   AGE   IP            NODE                  NOMINATED NODE   READINESS GATES
devops-info-79df6fcbc8-9dh2k   1/1     Running   0          13s   10.244.0.28   lab09-control-plane   <none>           <none>

$ kubectl exec -n devops-lab12 devops-info-79df6fcbc8-9dh2k -- cat /data/visits
4

$ kubectl exec -n devops-lab12 devops-info-79df6fcbc8-9dh2k -- python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5000/visits').read().decode())"
{"visits":4,"path":"/data/visits","timestamp":"2026-04-16T19:56:34.693898+00:00"}
```

Conclusion:

- The PVC stayed bound while the pod was replaced.
- The new pod picked up the exact same persisted counter value.

## 4. ConfigMap vs Secret

- Use `ConfigMap` for non-sensitive settings such as app metadata, log levels, feature flags, mount paths, and environment names.
- Use `Secret` for credentials, tokens, passwords, API keys, certificates, and anything that should not be exposed in plain text.
- `ConfigMap` data is plain configuration and is routinely visible in manifests and debugging output.
- `Secret` data is still only base64-encoded unless cluster encryption at rest is enabled, but it has distinct access controls and the correct semantic boundary.
- In this chart, `APP_USERNAME` and `APP_PASSWORD` stay in a Secret, while `APP_CONFIG_PATH`, `VISITS_FILE_PATH`, `SERVICE_*`, `HOST`, and `PORT` are supplied by ConfigMaps.

## 5. Bonus - ConfigMap Hot Reload

Relevant implementation:

- `app_python/app.py` rereads `/config/config.json` on every `GET /` request
- `k8s/devops-info/templates/deployment.yaml` adds:
  - `checksum/config-file`
  - `checksum/config-env`

That gives two useful behaviors:

- Live projected-volume updates are picked up by the app without a restart.
- `helm upgrade` changes to chart-managed config also change the pod template checksum and force a rollout.

### Measured update delay

I patched the live ConfigMap and waited for the mounted file to change inside the pod.

Patch result:

```bash
$ kubectl patch configmap devops-info-config -n devops-lab12 ...
configmap/devops-info-config patched
```

Observed mounted-file update:

```bash
$ grep -q hot-reloaded /config/config.json   # polled every 5s
52
{"application":{"name":"devops-info-service","environment":"hot-reloaded"},"features":{"visitsCounter":true,"prometheusMetrics":true,"healthChecks":true},"settings":{"logFormat":"json","configSource":"helm-configmap","persistencePath":"/data/visits"}}
```

The file updated after about `52` seconds, which matches the documented kubelet sync/cache delay behavior.

### App reload proof without pod restart

The pod creation timestamp stayed the same:

```bash
$ kubectl get pod devops-info-79df6fcbc8-9dh2k -n devops-lab12 -o jsonpath='{.metadata.creationTimestamp}'
2026-04-16T19:56:20Z
```

But the app immediately served the new config once the mounted file changed:

```bash
$ kubectl exec -n devops-lab12 devops-info-79df6fcbc8-9dh2k -- python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5000/').read().decode())"
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service packaged with Helm","framework":"FastAPI","variant":"primary"},"system":{"hostname":"devops-info-79df6fcbc8-9dh2k","platform":"Linux","platform_version":"#20~24.04.1-Ubuntu SMP PREEMPT_DYNAMIC Thu Mar 19 01:28:37 UTC 2","architecture":"x86_64","cpu_count":12,"python_version":"3.13.13"},"runtime":{"uptime_seconds":147,"uptime_human":"0 hours, 2 minutes","current_time":"2026-04-16T19:58:51.307539+00:00","timezone":"UTC"},"request":{"client_ip":"127.0.0.1","user_agent":"Python-urllib/3.13","method":"GET","path":"/"},"visits":{"count":6,"path":"/data/visits"},"configuration":{"path":"/config/config.json","loaded":true,"values":{"application":{"name":"devops-info-service","environment":"hot-reloaded"},"features":{"visitsCounter":true,"prometheusMetrics":true,"healthChecks":true},"settings":{"logFormat":"json","configSource":"helm-configmap","persistencePath":"/data/visits"}}},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Liveness probe"},{"path":"/ready","method":"GET","description":"Readiness probe"},{"path":"/visits","method":"GET","description":"Persistent visits counter"},{"path":"/metrics","method":"GET","description":"Prometheus metrics"}]}
```

### Why `subPath` is avoided

- `subPath` mounts copy a single file into the container filesystem.
- That copied file does not receive ConfigMap refreshes.
- A full directory mount at `/config` keeps the projected volume semantics, so kubelet can replace the file when the ConfigMap changes.

### Checksum annotation proof

The Deployment template includes checksum annotations:

```bash
$ kubectl get deploy devops-info -n devops-lab12 -o jsonpath='{.spec.template.metadata.annotations}'
{"checksum/config-env":"6b84769b6ce16989efa4bdad3a82edfacea1917c1748792881c757ccf2e5e96c","checksum/config-file":"a05ecd27bcc88dfa323d132df14153680a1bd4272e2dd113d45fe19fa2680dcc"}
```

That means a future `helm upgrade` that changes either the file-based ConfigMap or the env ConfigMap will also change the pod template and trigger a rollout automatically.
