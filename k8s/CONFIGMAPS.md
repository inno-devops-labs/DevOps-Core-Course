# Lab 12: ConfigMaps and Persistent Volumes

## 1. Application Changes

### Visits counter implementation

The FastAPI app in [app_python/app.py](/home/nodo/DevOps-Core-Course/app_python/app.py) now persists a file-backed visits counter.

What changed:
- `VisitsStore` reads and writes the counter from `VISITS_FILE` and defaults to `0` when the file is absent.
- `GET /` increments the counter and returns the current value under `visits.count`.
- `GET /visits` returns the current persisted value without incrementing it.
- Counter writes use a process-local lock and atomic rename (`*.tmp` then replace) to reduce corruption risk.
- `ConfigCache` reads `APP_CONFIG_PATH` and reloads JSON when the mounted file changes.

### New endpoint

`GET /visits`

Example response:
```json
{"visits":2,"storage":"/data/visits"}
```

## 2. Local Docker Verification

### Files used

- [app_python/docker-compose.yml](/home/nodo/DevOps-Core-Course/app_python/docker-compose.yml)
- [app_python/config/config.json](/home/nodo/DevOps-Core-Course/app_python/config/config.json)
- [app_python/data](/home/nodo/DevOps-Core-Course/app_python/data)

### Compose volume layout

The local compose file mounts:
- `./data -> /data`
- `./config -> /config:ro`

This keeps the image immutable and stores runtime state outside the container.

### Local verification output

The local Compose workflow was verified with the repository’s [app_python/docker-compose.yml](/home/nodo/DevOps-Core-Course/app_python/docker-compose.yml), which uses the local `devops-info-service:latest` image plus a bind-mounted [app.py](/home/nodo/DevOps-Core-Course/app_python/app.py).

Observed output from two `GET /` calls followed by `GET /visits`:

```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "f727c1e8050d",
    "platform": "Linux",
    "platform_version": "#1 SMP PREEMPT_DYNAMIC Thu Jun  5 18:30:46 UTC 2025",
    "architecture": "x86_64",
    "cpu_count": 32,
    "python_version": "3.12.13"
  },
  "runtime": {
    "uptime_seconds": 7,
    "uptime_human": "0 hours, 0 minutes",
    "current_time": "2026-04-16T18:04:29.475562",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "Python-urllib/3.12",
    "method": "GET",
    "path": "/"
  },
  "visits": {
    "count": 1,
    "storage": "/data/visits"
  },
  "configuration": {
    "environment": {
      "APP_ENV": "dev",
      "LOG_LEVEL": "info",
      "APP_DISPLAY_NAME": "DevOps Info Service",
      "FEATURE_VISITS_ENABLED": "true",
      "FEATURE_CONFIG_HOT_RELOAD": "true"
    },
    "file": {},
    "paths": {
      "visits_file": "/data/visits",
      "config_file": "/config/config.json"
    }
  }
}
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "FastAPI"
  },
  "system": {
    "hostname": "f727c1e8050d",
    "platform": "Linux",
    "platform_version": "#1 SMP PREEMPT_DYNAMIC Thu Jun  5 18:30:46 UTC 2025",
    "architecture": "x86_64",
    "cpu_count": 32,
    "python_version": "3.12.13"
  },
  "runtime": {
    "uptime_seconds": 7,
    "uptime_human": "0 hours, 0 minutes",
    "current_time": "2026-04-16T18:04:29.477102",
    "timezone": "UTC"
  },
  "request": {
    "client_ip": "127.0.0.1",
    "user_agent": "Python-urllib/3.12",
    "method": "GET",
    "path": "/"
  },
  "visits": {
    "count": 2,
    "storage": "/data/visits"
  },
  "configuration": {
    "environment": {
      "APP_ENV": "dev",
      "LOG_LEVEL": "info",
      "APP_DISPLAY_NAME": "DevOps Info Service",
      "FEATURE_VISITS_ENABLED": "true",
      "FEATURE_CONFIG_HOT_RELOAD": "true"
    },
    "file": {},
    "paths": {
      "visits_file": "/data/visits",
      "config_file": "/config/config.json"
    }
  }
}
{"visits":2,"storage":"/data/visits"}
```

Persistence after restart:

Compose-managed verification:

```text
$ docker compose ps
NAME                               IMAGE                        COMMAND           SERVICE               CREATED          STATUS         PORTS
app_python-devops-info-service-1   devops-info-service:latest   "python app.py"   devops-info-service   35 seconds ago   Up 7 seconds   0.0.0.0:5000->5000/tcp, [::]:5000->5000/tcp, 8000/tcp

$ in-container requests
{
  "first": 1,
  "second": 2,
  "visits": 2,
  "config_message": "Configuration loaded from mounted file"
}

$ cat app_python/data/visits
2

$ docker compose restart devops-info-service
Container app_python-devops-info-service-1 Restarting
Container app_python-devops-info-service-1 Started

$ GET /visits after container restart
{'visits': 2, 'storage': '/data/visits'}
```

Config file mounted locally:

```json
{
  "root_visits": 3,
  "visits_endpoint": 3,
  "config_file": {
    "applicationName": "devops-info-service",
    "environment": "dev",
    "features": {
      "visits": true,
      "configHotReload": true
    },
    "settings": {
      "region": "local",
      "message": "Configuration loaded from mounted file"
    }
  }
}
```

## 3. ConfigMap Implementation

### Chart files

- File-backed config: [k8s/devops-info-service/files/config.json](/home/nodo/DevOps-Core-Course/k8s/devops-info-service/files/config.json)
- ConfigMap templates: [k8s/devops-info-service/templates/configmap.yaml](/home/nodo/DevOps-Core-Course/k8s/devops-info-service/templates/configmap.yaml)
- Deployment wiring: [k8s/devops-info-service/templates/deployment.yaml](/home/nodo/DevOps-Core-Course/k8s/devops-info-service/templates/deployment.yaml)
- Values: [k8s/devops-info-service/values.yaml](/home/nodo/DevOps-Core-Course/k8s/devops-info-service/values.yaml)

### Structure

Two ConfigMaps are created:
- `lab12-devops-info-service-config`: mounts `files/config.json` into `/config/config.json`
- `lab12-devops-info-service-env`: injects key/value settings with `envFrom`

### Config file content

Mounted file:

```json
{
  "applicationName": "devops-info-service",
  "environment": "dev",
  "features": {
    "visits": true,
    "configHotReload": true
  },
  "settings": {
    "region": "eu-central",
    "message": "Mounted from Helm chart files/config.json"
  }
}
```

### Live verification from Kind

Rendered and applied resources used the `kind-lab10` cluster. The original dev `NodePort` conflicted with an existing allocation during the first apply, so `values-dev.yaml` was updated from `30090` to `30091`. That did not affect the ConfigMap/PVC verification.

`kubectl get configmap,pvc -n lab12`:

```text
NAME                                         DATA   AGE
configmap/kube-root-ca.crt                   1      3m46s
configmap/lab12-devops-info-service-config   1      50s
configmap/lab12-devops-info-service-env      7      50s

NAME                                                   STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/lab12-devops-info-service-data   Bound    pvc-a1a33421-bb7b-49c9-8a38-8b3d4deca2a5   100Mi      RWO            standard       <unset>                 50s
```

Mounted config file inside the pod:

```text
$ kubectl exec -n lab12 <pod> -- cat /config/config.json
{
  "applicationName": "devops-info-service",
  "environment": "dev",
  "features": {
    "visits": true,
    "configHotReload": true
  },
  "settings": {
    "region": "eu-central",
    "message": "Mounted from Helm chart files/config.json"
  }
}
```

Injected environment variables:

```text
APP_CONFIG_PATH=/config/config.json
APP_DISPLAY_NAME=DevOps Info Service Dev
APP_ENV=dev
LOG_LEVEL=debug
VISITS_FILE=/data/visits
```

### Deployment mount and env details

Verified from `kubectl describe pod`:

```text
Environment Variables from:
  lab12-devops-info-service-env     ConfigMap  Optional: false
  lab12-devops-info-service-secret  Secret     Optional: false

Mounts:
  /config from config-volume (ro)
  /data from data-volume (rw)
```

## 4. Persistent Volume

### PVC configuration

PVC template: [k8s/devops-info-service/templates/pvc.yaml](/home/nodo/DevOps-Core-Course/k8s/devops-info-service/templates/pvc.yaml)

Key settings:
- `accessModes: [ReadWriteOnce]`
- `requests.storage: 100Mi`
- `storageClass` is configurable from values
- Deployment mounts the claim at `/data`

### Access mode and storage class

- `ReadWriteOnce` is appropriate here because one pod writes a single file-based counter.
- On Kind/Minikube-style local clusters, the default `standard` storage class provisions storage automatically.
- The pod security context uses `fsGroup: 1000`, which helps writable volume access for the non-root container.

### Persistence test evidence

Before pod deletion:

```text
$ kubectl exec -n lab12 <pod> -- sh -c 'echo 7 > /data/visits && cat /data/visits'
7
```

Deletion command:

```text
kubectl delete pod -n lab12 lab12-devops-info-service-54c99bb6d6-c7z8c
```

PVC still bound after deletion:

```text
NAME                             STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
lab12-devops-info-service-data   Bound    pvc-a1a33421-bb7b-49c9-8a38-8b3d4deca2a5   100Mi      RWO            standard       29s
```

After the replacement pod became ready:

```text
$ kubectl exec -n lab12 lab12-devops-info-service-54c99bb6d6-6wqk4 -- cat /data/visits
7
```

This confirms the data survived pod replacement and the deployment is reading from the same PVC-backed volume.

## 5. ConfigMap vs Secret

### Use a ConfigMap when

- The data is not sensitive
- You want human-readable config files or plain env vars
- The values are safe to store in Git
- You want predictable config rollout behavior

Examples:
- `config.json`
- `APP_ENV`
- `LOG_LEVEL`
- feature flags

### Use a Secret when

- The data is sensitive
- Disclosure would be a security issue
- The value should be base64-encoded in Kubernetes objects and handled with tighter RBAC

Examples:
- passwords
- API tokens
- private keys
- registry credentials

### Key differences

- ConfigMaps are for non-sensitive configuration
- Secrets are for confidential data
- Both can be mounted as files or exposed as environment variables
- Secrets should have stricter access controls and usually come from Vault or secret managers in production

## 6. Bonus: ConfigMap Hot Reload

### Default mounted ConfigMap update behavior

Mounted ConfigMaps are not updated instantly. Kubelet refreshes projected ConfigMap volumes periodically, so changes typically appear with a delay that is often around one minute and can be longer depending on cache timing.

### Why `subPath` is avoided here

`subPath` creates a bind mount to a single file path. That mounted file does not receive live ConfigMap updates. For that reason the chart mounts the entire ConfigMap directory at `/config` instead of mounting a single file via `subPath`.

### Implemented reload approach

Two complementary approaches are implemented:
- Application-level reload: `ConfigCache` in [app_python/app.py](/home/nodo/DevOps-Core-Course/app_python/app.py) checks the file mtime and reloads JSON on demand.
- Deployment-level rollout: checksum annotations in [k8s/devops-info-service/templates/deployment.yaml](/home/nodo/DevOps-Core-Course/k8s/devops-info-service/templates/deployment.yaml) trigger a pod rollout when the file ConfigMap or env ConfigMap content changes.

Checksum annotations used:

```yaml
annotations:
  checksum/config-file: {{ .Files.Get "files/config.json" | sha256sum }}
  checksum/config-env: {{ toJson .Values.config.env | sha256sum }}
```

### Local hot reload evidence

Using the mounted local config file and the updated `ConfigCache` logic:

Before config file edit:

```text
Configuration hot reloaded without restart
```

After changing the mounted JSON file and calling `GET /` again, without restarting the container:

```text
Configuration changed live after file update
```

This demonstrates the application-side hot reload path. In Kubernetes, the checksum annotation pattern additionally guarantees a rollout when Helm changes the ConfigMap content.

### Measured Kubernetes mounted-file update delay

I also measured the default mounted ConfigMap refresh behavior in the Kind cluster by:
- patching `lab12-devops-info-service-config`
- polling `/config/config.json` inside the running pod

Observed sequence:

```text
Patch time:        1776363769
After 17 seconds:  "message": "Mounted from Helm chart files/config.json"
After 44 seconds:  "message": "Mounted ConfigMap updated second time"
```

Measured delay in this cluster: approximately `44 seconds`.

That result is consistent with Kubernetes documentation: mounted ConfigMap updates are not instantaneous and depend on kubelet sync and cache timing.

## 7. Test Results

I ran the Python test suite in a container using the current workspace code:

```text
============================= test session starts ==============================
platform linux -- Python 3.12.13, pytest-9.0.2, pluggy-1.6.0
rootdir: /app
configfile: pyproject.toml
plugins: anyio-4.12.1
collected 36 items

tests/test_get_health.py ..............                                  [ 38%]
tests/test_get_ready.py ...                                              [ 47%]
tests/test_get_root.py ...........                                       [ 77%]
tests/test_metrics.py .....                                              [ 91%]
tests/test_visits.py ...                                                 [100%]

======================== 36 passed, 2 warnings in 0.46s ========================
```
