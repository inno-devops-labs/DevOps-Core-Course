# Lab 12 Report — ConfigMaps & Persistent Volumes

## 1. Overview

Lab 12 extends the existing `devops-info` Flask application and Helm chart with:

- a file-backed visits counter stored in `/data/visits`
- a new `GET /visits` endpoint
- ConfigMaps for both file-based and environment-variable configuration
- a PersistentVolumeClaim so the counter survives pod recreation
- a checksum-based Helm rollout pattern for configuration changes

Relevant files:

```text
app_python/
├── app.py
├── Dockerfile
├── README.md
├── docker-compose.yml
└── tests/test_app.py

k8s/
├── CONFIGMAPS.md
└── devops-info/
    ├── files/config.json
    ├── values.yaml
    ├── values-dev.yaml
    ├── values-prod.yaml
    └── templates/
        ├── _helpers.tpl
        ├── configmap.yaml
        ├── deployment.yaml
        └── pvc.yaml
```

## 2. Task 1 — Application Persistence Upgrade

### 2.1 Application changes

I updated the Flask app so the root endpoint increments a persisted counter on every request.

Implementation details:

- the counter file path is configurable through `VISITS_FILE`
- the default path is `/data/visits`
- the application reads the current value from the file, defaults to `0` if the file does not exist, increments it, and writes it back
- writes use an atomic `os.replace(...)` pattern
- a process-local `threading.Lock()` protects concurrent access inside the same container

I also added a new endpoint:

- `GET /visits` returns the current counter without incrementing it

The root endpoint now also returns:

- the current visits count
- the storage file path
- the currently loaded JSON configuration file
- selected non-secret environment variables

### 2.2 Local Docker Compose persistence test

I created `app_python/docker-compose.yml` with a bind mount:

```yaml
volumes:
  - ./data:/data
```

This makes the counter visible on the host and keeps it across container recreation.

Local test evidence:

```bash
$ docker compose exec -T devops-info python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5002/visits').read().decode())"
{"count":0,"storage_file":"/data/visits"}
```

Then I hit the root endpoint twice and checked the counter:

```bash
$ docker compose exec -T devops-info python -c "import urllib.request; urls=['http://127.0.0.1:5002/','http://127.0.0.1:5002/','http://127.0.0.1:5002/visits']; [print(urllib.request.urlopen(url).read().decode()) for url in urls]"
...
"visits":{"count":1,"storage_file":"/data/visits"}
...
"visits":{"count":2,"storage_file":"/data/visits"}
{"count":2,"storage_file":"/data/visits"}
```

The bind-mounted host file contained the same value:

```bash
$ cat app_python/data/visits
2
```

After restarting the compose stack, the counter was still there:

```bash
$ docker compose down
$ docker compose up -d
$ docker compose exec -T devops-info python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5002/visits').read().decode())"
{"count":2,"storage_file":"/data/visits"}
```

That verifies the local persistence requirement from Task 1.

### 2.3 README and tests

I also updated:

- `app_python/README.md` with `CONFIG_PATH`, `VISITS_FILE`, `GET /visits`, and Docker Compose persistence steps
- `app_python/tests/test_app.py` with a visits persistence test

Unit test result:

```bash
$ ./.venv/bin/python -m unittest discover -s tests
Ran 6 tests in 0.028s

OK
```

## 3. Task 2 — ConfigMaps

### 3.1 File-based ConfigMap

I created `k8s/devops-info/files/config.json` and loaded it through Helm with `.Files.Get` plus `tpl`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "devops-info.fileConfigMapName" . }}
data:
  config.json: |-
{{ tpl (.Files.Get "files/config.json") . | indent 4 }}
```

The file content is value-driven:

```json
{
  "applicationName": "devops-info-service",
  "environment": "dev",
  "featureFlags": {
    "visitsCounter": true,
    "configHotReload": true
  },
  "settings": {
    "logFormat": "json",
    "storagePath": "/data/visits"
  }
}
```

### 3.2 Environment-variable ConfigMap

I created a second ConfigMap for key-value injection:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "devops-info.envConfigMapName" . }}
data:
  APP_MODE: "lab12-dev"
  LOG_LEVEL: "debug"
  FEATURE_PROFILE: "persistence-demo"
  FEATURE_RUNTIME_CONFIG: "enabled"
```

### 3.3 Deployment changes

The Deployment now:

- mounts the file ConfigMap as a full directory at `/config`
- avoids `subPath` so mounted files can receive live updates
- uses `envFrom.configMapRef` to inject all keys from the env ConfigMap

Relevant Deployment fragment:

```yaml
env:
  {{- include "devops-info.envVars" . | nindent 12 }}
envFrom:
  - configMapRef:
      name: {{ include "devops-info.envConfigMapName" . }}
  - secretRef:
      name: {{ include "devops-info.secretName" . }}
volumeMounts:
  - name: config-volume
    mountPath: /config
    readOnly: true
```

### 3.4 Verification outputs

Resources created in the cluster:

```bash
$ kubectl get pods,svc,configmap,pvc -n lab12
NAME                                    READY   STATUS    RESTARTS   AGE
pod/lab12-devops-info-d9d889b4d-7bz7w   1/1     Running   0          47s

NAME                        TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/lab12-devops-info   NodePort   10.96.79.204   <none>        80:30085/TCP   47s

NAME                                 DATA   AGE
configmap/kube-root-ca.crt           1      61s
configmap/lab12-devops-info-config   1      47s
configmap/lab12-devops-info-env      4      47s

NAME                                           STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/lab12-devops-info-data   Bound    pvc-30ffc5aa-4482-4b2c-9915-5fe036a36565   100Mi      RWO            standard       <unset>                 47s
```

Mounted file inside the pod:

```bash
$ kubectl exec -n lab12 deployment/lab12-devops-info -- cat /config/config.json
{
  "applicationName": "devops-info-service",
  "environment": "dev",
  "featureFlags": {
    "visitsCounter": true,
    "configHotReload": true
  },
  "settings": {
    "logFormat": "json",
    "storagePath": "/data/visits"
  }
}
```

Relevant environment variables inside the pod:

```bash
$ kubectl exec -n lab12 deployment/lab12-devops-info -- printenv
CONFIG_PATH=/config/config.json
VISITS_FILE=/data/visits
APP_ENV=helm-dev
APP_REVISION=dev-v1
APP_MODE=lab12-dev
FEATURE_PROFILE=persistence-demo
FEATURE_RUNTIME_CONFIG=enabled
LOG_LEVEL=debug
```

That verifies both required ConfigMap consumption patterns:

- file mount
- env var injection

## 4. Task 3 — Persistent Volume

### 4.1 PVC implementation

I added `templates/pvc.yaml`:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "devops-info.pvcName" . }}
spec:
  accessModes:
    - {{ .Values.persistence.accessMode }}
  resources:
    requests:
      storage: {{ .Values.persistence.size }}
  {{- if .Values.persistence.storageClass }}
  storageClassName: {{ .Values.persistence.storageClass | quote }}
  {{- end }}
```

Values used for the lab:

- `enabled: true`
- `accessMode: ReadWriteOnce`
- `size: 100Mi`
- `storageClass: ""`

Because `storageClass` is empty, Kubernetes used the default storage class on this cluster, which is `standard`.

### 4.2 Volume mount configuration

The Deployment mounts the PVC at `/data`:

```yaml
volumes:
  - name: data-volume
    persistentVolumeClaim:
      claimName: {{ include "devops-info.pvcName" . }}

volumeMounts:
  - name: data-volume
    mountPath: /data
```

This matches the application’s `VISITS_FILE=/data/visits`.

### 4.3 Persistence test evidence

Initial counter before incrementing:

```bash
$ kubectl exec -n lab12 deployment/lab12-devops-info -- python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5002/visits').read().decode())"
{"count":0,"storage_file":"/data/visits"}
```

After two `GET /` requests:

```bash
$ kubectl exec -n lab12 deployment/lab12-devops-info -- python -c "import urllib.request; urls=['http://127.0.0.1:5002/','http://127.0.0.1:5002/','http://127.0.0.1:5002/visits']; [print(urllib.request.urlopen(url).read().decode()) for url in urls]"
...
"visits":{"count":1,"storage_file":"/data/visits"}
...
"visits":{"count":2,"storage_file":"/data/visits"}
{"count":2,"storage_file":"/data/visits"}
```

The persisted file in the pod also contained `2`:

```bash
$ kubectl exec -n lab12 deployment/lab12-devops-info -- cat /data/visits
2
```

Then I deleted the pod directly:

```bash
$ kubectl delete pod lab12-devops-info-d9d889b4d-7bz7w -n lab12
pod "lab12-devops-info-d9d889b4d-7bz7w" deleted from lab12 namespace
```

Kubernetes recreated it:

```bash
$ kubectl get pods -n lab12
NAME                                READY   STATUS    RESTARTS   AGE
lab12-devops-info-d9d889b4d-nvvjl   1/1     Running   0          33s
```

After recreation, the value was still present:

```bash
$ kubectl exec -n lab12 deployment/lab12-devops-info -- python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5002/visits').read().decode())"
{"count":2,"storage_file":"/data/visits"}

$ kubectl exec -n lab12 deployment/lab12-devops-info -- cat /data/visits
2
```

That proves the data survived pod deletion because it was stored on the PVC instead of the container filesystem.

## 5. ConfigMap vs Secret

The key difference is sensitivity of the data.

Use a ConfigMap when:

- the data is not confidential
- the application needs normal runtime configuration
- examples include environment names, feature flags, log levels, or JSON settings

Use a Secret when:

- the data is sensitive
- examples include passwords, tokens, API keys, or certificates

In this chart:

- ConfigMaps store non-sensitive config such as `APP_MODE`, `LOG_LEVEL`, and `config.json`
- Secrets still hold `username` and `password` placeholders from Lab 11

So the correct rule is:

- ConfigMap for configuration
- Secret for credentials

## 6. Bonus — ConfigMap Hot Reload

### 6.1 Default update behavior

I tested a direct live ConfigMap change with `kubectl patch`:

```bash
$ kubectl patch configmap lab12-devops-info-config -n lab12 --type merge -p '{"data":{"config.json":"{\"applicationName\":\"devops-info-service\",\"environment\":\"patched-live\",\"featureFlags\":{\"visitsCounter\":true,\"configHotReload\":true},\"settings\":{\"logFormat\":\"json\",\"storagePath\":\"/data/visits\"}}"}}'
configmap/lab12-devops-info-config patched
```

Immediately after the patch, the mounted file still showed the old content:

```bash
$ kubectl exec -n lab12 deployment/lab12-devops-info -- cat /config/config.json
{
  "applicationName": "devops-info-service",
  "environment": "dev",
  ...
}
```

On the next check, the mounted file had updated without restarting the pod:

```bash
$ kubectl exec -n lab12 deployment/lab12-devops-info -- cat /config/config.json
{"applicationName":"devops-info-service","environment":"patched-live","featureFlags":{"visitsCounter":true,"configHotReload":true},"settings":{"logFormat":"json","storagePath":"/data/visits"}}
```

Observed result:

- the update was not instantaneous
- on this local `kind` cluster it appeared within a few seconds of the patch
- the pod was not restarted for that direct ConfigMap update

### 6.2 Why `subPath` is a limitation

I intentionally mounted the full `/config` directory and did not use `subPath`.

Reason:

- normal ConfigMap volume mounts are updated by kubelet
- `subPath` mounts behave like a one-time file bind/copy
- because of that, `subPath` files do not receive live ConfigMap updates

So for hot-reload behavior:

- use a full directory mount
- avoid `subPath`

### 6.3 Chosen reload approach

I implemented the checksum annotation pattern in `templates/deployment.yaml`:

```yaml
annotations:
  checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

This means:

- whenever the rendered ConfigMap changes through Helm
- the Pod template annotation changes too
- Kubernetes creates a new ReplicaSet and rolls the pod

### 6.4 Helm upgrade demonstration

After the direct patch test, I ran a Helm upgrade with changed config values:

```bash
$ helm upgrade --install lab12-devops-info ./k8s/devops-info \
    -n lab12 \
    -f ./k8s/devops-info/values-dev.yaml \
    --set service.nodePort=30085 \
    --set image.tag=lab12 \
    --set config.file.environment=helm-upgrade \
    --set config.env.data.LOG_LEVEL=trace \
    --set config.env.data.FEATURE_PROFILE=helm-rollout \
    --server-side=true --force-conflicts
```

Why `--force-conflicts` was needed:

- I had deliberately edited the ConfigMap directly with `kubectl patch`
- that created a server-side apply field-manager conflict
- `--force-conflicts` let Helm take back control of the resource

Before the Helm upgrade, the running pod was:

```text
lab12-devops-info-d9d889b4d-nvvjl
```

After the Helm upgrade, the pod changed to:

```bash
$ kubectl get pods -n lab12
NAME                                READY   STATUS    RESTARTS   AGE
lab12-devops-info-d4bdc8677-f5x49   1/1     Running   0          86s
```

That confirms the checksum annotation triggered a rollout.

The mounted file after the Helm upgrade:

```bash
$ kubectl exec -n lab12 deployment/lab12-devops-info -- cat /config/config.json
{
  "applicationName": "devops-info-service",
  "environment": "helm-upgrade",
  "featureFlags": {
    "visitsCounter": true,
    "configHotReload": true
  },
  "settings": {
    "logFormat": "json",
    "storagePath": "/data/visits"
  }
}
```

Relevant env vars after the Helm upgrade:

```bash
$ kubectl exec -n lab12 deployment/lab12-devops-info -- printenv
APP_MODE=lab12-dev
FEATURE_PROFILE=helm-rollout
FEATURE_RUNTIME_CONFIG=enabled
LOG_LEVEL=trace
CONFIG_PATH=/config/config.json
VISITS_FILE=/data/visits
```

This demonstrates the chosen reload mechanism end to end:

- direct ConfigMap file mounts can update live
- env vars do not update live by themselves
- the checksum annotation solves that by forcing a rollout on Helm-driven config changes

