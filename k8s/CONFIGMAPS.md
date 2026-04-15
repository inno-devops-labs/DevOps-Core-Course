# Lab 12 - ConfigMaps and Persistent Volumes

Run date: April 15, 2026

Resource-saving note:
To avoid spinning up Docker or a local Kubernetes cluster for this turn, I validated the implementation with application tests, `flake8`, `helm lint`, and `helm template`. Live `kubectl` screenshots were not collected here, so Kubernetes verification sections below use rendered manifests plus the exact commands to run against a cluster.

## Validation Summary

Application checks executed locally:

```text
py -3 -m flake8 app.py tests/test_app.py
py -3 -m pytest tests/test_app.py -q
.......................................                                  [100%]
39 passed, 91 warnings in 6.43s
```

Helm checks executed locally:

```text
.\.tools\helm.exe dependency build .\k8s\devops-info-service
Saving 1 charts
Deleting outdated charts

.\.tools\helm.exe lint .\k8s\devops-info-service
==> Linting .\k8s\devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

Replica validation for the PVC-backed counter:

```text
.\.tools\helm.exe template devops-info-service .\k8s\devops-info-service --set replicaCount=2
Error: execution error at (devops-info-service/templates/pvc.yaml:1:4): devops-info-service:
persistence.enabled with ReadWriteOnce requires replicaCount <= 1
```

## Application Changes

Files changed:

- `app_python/app.py`
- `app_python/tests/test_app.py`
- `app_python/docker-compose.yml`
- `app_python/README.md`

What changed:

- `GET /` now increments a persistent visits counter and writes it to `VISITS_FILE`.
- `GET /visits` returns the current counter without incrementing it.
- the counter is loaded from disk on startup through `VisitCounterStore`
- writes use a process-local lock plus atomic `os.replace(...)`
- the app reads `CONFIG_PATH` on each request, so mounted `config.json` changes can be observed without rebuilding the image

Local behavior transcript from a real `TestClient` run:

```json
{
  "first_root_count": 1,
  "second_root_count": 2,
  "visits_endpoint_count": 2,
  "file_after_two_root_calls": "2",
  "file_after_reload_request": "3",
  "reloaded_environment": "reloaded"
}
```

Interpretation:

- the first two `GET /` calls incremented the file-backed counter from `0` to `2`
- `GET /visits` returned `2` without incrementing
- updating the JSON config file before the next `GET /` changed the reported environment to `reloaded`

Docker compose support was added in `app_python/docker-compose.yml`:

```yaml
services:
  devops-info-service:
    build:
      context: .
    environment:
      VISITS_FILE: /app/data/visits
    volumes:
      - ./data:/app/data
```

This was prepared for the lab, but not executed here to conserve Docker resources.

## ConfigMap Implementation

Chart files added:

- `k8s/devops-info-service/files/config.json`
- `k8s/devops-info-service/templates/configmap-file.yaml`
- `k8s/devops-info-service/templates/configmap-env.yaml`

Design:

- `configmap-file.yaml` renders `files/config.json` with `tpl (.Files.Get "files/config.json") .`
- `configmap-env.yaml` exposes key-value settings through `envFrom`
- the Deployment mounts the file ConfigMap at `/config`
- the Deployment injects the env ConfigMap from `devops-info-service-env`

Rendered file ConfigMap (`values-dev.yaml`):

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: devops-info-service-config
data:
  config.json: |-
    {
      "application": {
        "name": "devops-info-service",
        "environment": "development",
        "version": "1.0.0"
      },
      "featureFlags": {
        "visitsCounter": true,
        "metrics": true,
        "hotReload": true
      },
      "settings": {
        "responseMode": "detailed",
        "configMountPath": "/config",
        "visitsFile": "/data/visits"
      }
    }
```

Rendered env ConfigMap (`values-dev.yaml`):

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: devops-info-service-env
data:
  APP_NAME: "devops-info-service"
  APP_ENV: "development"
  APP_REGION: "lab12-dev"
  LOG_LEVEL: "debug"
  FEATURE_CONFIG_RELOAD: "true"
  FEATURE_VISITS_COUNTER: "true"
```

Rendered Deployment excerpt:

```yaml
metadata:
  annotations:
    checksum/config-file: edef89f96e9943069adfb547bb2b802c30d2b0c0b2e0d32682d36d733e7f8da6
    checksum/config-env: e66dfabbfa0cb466ec21c64a7d3e55619912bf5877e394b12db21f7c727726ff
spec:
  containers:
    - env:
        - name: CONFIG_PATH
          value: /config/config.json
        - name: VISITS_FILE
          value: /data/visits
      envFrom:
        - configMapRef:
            name: devops-info-service-env
        - secretRef:
            name: devops-info-service-secret
      volumeMounts:
        - name: config-volume
          mountPath: /config
          readOnly: true
```

Prepared live verification commands:

```powershell
kubectl get configmap -n <namespace>
kubectl exec deploy/devops-info-service -n <namespace> -- cat /config/config.json
kubectl exec deploy/devops-info-service -n <namespace> -- printenv | grep APP_
```

## Persistent Volume

Chart file added:

- `k8s/devops-info-service/templates/pvc.yaml`

Values added:

```yaml
persistence:
  enabled: true
  accessMode: ReadWriteOnce
  size: 100Mi
  storageClass: ""
  mountPath: /data
  visitsFileName: visits
```

Rendered PVC (`values-dev.yaml`):

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: devops-info-service-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Mi
```

Rendered Deployment storage excerpt:

```yaml
volumeMounts:
  - name: data-volume
    mountPath: /data
volumes:
  - name: data-volume
    persistentVolumeClaim:
      claimName: devops-info-service-data
```

Why the chart now defaults to one replica:

- a single visits file is mounted through one PVC
- the lab uses `ReadWriteOnce`
- that access mode is the correct simple choice for this exercise, but it does not support a multi-replica shared-writer Deployment
- the chart therefore validates and fails fast if `replicaCount > 1` while `ReadWriteOnce` persistence is enabled

Prepared live persistence test:

```powershell
kubectl get pvc -n <namespace>
kubectl exec deploy/devops-info-service -n <namespace> -- cat /data/visits
kubectl delete pod <pod-name> -n <namespace>
kubectl exec deploy/devops-info-service -n <namespace> -- cat /data/visits
```

Expected success criteria:

- count before pod deletion matches the file content in `/data/visits`
- after the Deployment recreates the pod, the same file still exists on the PVC
- `GET /visits` returns the preserved value

## ConfigMap vs Secret

Use ConfigMap when:

- the data is non-sensitive
- the application needs plain configuration files or environment variables
- the same image should run in multiple environments with different settings

Use Secret when:

- the data is sensitive
- credentials, tokens, passwords, or keys are involved
- the value should be separated from general application configuration

Key differences:

- ConfigMaps are for non-secret configuration; Secrets are for sensitive values
- both can be mounted as files or exposed as env vars
- Secrets are still only base64-encoded unless cluster encryption at rest is enabled
- in this chart, ConfigMaps now provide `config.json` and app env vars, while Secrets still hold `username` and `password`

## Bonus - Hot Reload Notes

What was implemented:

- the application reloads `CONFIG_PATH` on each request
- the ConfigMap file is mounted as a directory, not through `subPath`
- the Deployment template adds checksum annotations so `helm upgrade` triggers a rollout when either ConfigMap changes

Why `subPath` was avoided:

- `subPath` mounts a copied file view
- Kubernetes does not update that copied file when the source ConfigMap changes
- mounting the whole `/config` directory preserves the standard ConfigMap update behavior

Default update behavior:

- mounted ConfigMaps are refreshed by kubelet asynchronously
- in practice the delay is commonly around the kubelet sync period plus cache TTL, so changes can take roughly a minute or a bit more to appear
- I did not measure this live in a cluster on April 15, 2026 because the cluster was not started for this run

Helm-driven reload pattern:

- `checksum/config-file` changes when `files/config.json` or values affecting it change
- `checksum/config-env` changes when env-style ConfigMap values change
- a Helm upgrade therefore changes the pod template and forces a clean rollout

## Commands for a Full Live Run Later

```powershell
kubectl create namespace lab12 --dry-run=client -o yaml | kubectl apply -f -
.\.tools\helm.exe dependency build .\k8s\devops-info-service
.\.tools\helm.exe install devops-info-service .\k8s\devops-info-service --namespace lab12 -f .\k8s\devops-info-service\values-dev.yaml
kubectl get configmap,pvc -n lab12
kubectl exec deploy/devops-info-service -n lab12 -- cat /config/config.json
kubectl exec deploy/devops-info-service -n lab12 -- printenv | grep APP_
kubectl port-forward svc/devops-info-service 18080:80 -n lab12
Invoke-RestMethod http://127.0.0.1:18080/
Invoke-RestMethod http://127.0.0.1:18080/visits
kubectl delete pod -n lab12 -l app.kubernetes.io/instance=devops-info-service
```
