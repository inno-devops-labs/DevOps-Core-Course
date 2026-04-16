# Lab 12 — ConfigMaps & Persistent Volumes

This document matches the current repository state and the validation run I executed on April 16, 2026.

Validation targets:

- Local Docker Compose run from [app_python/docker-compose.yml](/Users/pepega/Developer/learning/DevOps-Core-Course/app_python/docker-compose.yml)
- Helm release `lab12-audit` in namespace `lab12-audit`
- Current chart: [k8s/devops-info-python](/Users/pepega/Developer/learning/DevOps-Core-Course/k8s/devops-info-python)

Chart and test validation commands:

```bash
app_python/.venv/bin/pytest app_python/tests
/tmp/darwin-arm64/helm lint k8s/devops-info-python
/tmp/darwin-arm64/helm template lab12-check k8s/devops-info-python -f k8s/devops-info-python/values-dev.yaml
/tmp/darwin-arm64/helm template lab12-check k8s/devops-info-python -f k8s/devops-info-python/values-prod.yaml
```

## Application Changes

The Flask app now persists a visit counter in a file and exposes `GET /visits`.

Relevant implementation points:

- [app_python/app.py](/Users/pepega/Developer/learning/DevOps-Core-Course/app_python/app.py) stores the counter in `VISITS_FILE_PATH` and protects updates with `fcntl.flock(...)`.
- `GET /` increments the counter and returns the new value.
- `GET /visits` reads the persisted value without incrementing it.
- [app_python/docker-compose.yml](/Users/pepega/Developer/learning/DevOps-Core-Course/app_python/docker-compose.yml) bind-mounts `./data` to `/data` and `./config` to `/config`.
- [app_python/README.md](/Users/pepega/Developer/learning/DevOps-Core-Course/app_python/README.md) documents the persistence check.

### Local Docker Evidence

Validation commands:

```bash
cd app_python
curl http://127.0.0.1:3001/visits
curl http://127.0.0.1:3001/
curl http://127.0.0.1:3001/
curl http://127.0.0.1:3001/visits
cat data/visits
docker compose restart devops-info-service
curl http://127.0.0.1:3001/visits
```

Observed outputs:

```text
{"count":2,"path":"/data/visits","timestamp":"2026-04-16T17:35:11.136544+00:00"}
{"count":4,"path":"/data/visits","timestamp":"2026-04-16T17:35:11.171157+00:00"}
4
{"count":4,"path":"/data/visits","timestamp":"2026-04-16T17:35:18.865785+00:00"}
```

That confirms the counter persisted across the container restart.

## ConfigMap Implementation

The chart renders two ConfigMaps from [k8s/devops-info-python/templates/configmap.yaml](/Users/pepega/Developer/learning/DevOps-Core-Course/k8s/devops-info-python/templates/configmap.yaml):

- `*-config` stores the rendered [k8s/devops-info-python/files/config.json](/Users/pepega/Developer/learning/DevOps-Core-Course/k8s/devops-info-python/files/config.json)
- `*-env` stores key-value pairs injected with `envFrom`

The deployment in [k8s/devops-info-python/templates/deployment.yaml](/Users/pepega/Developer/learning/DevOps-Core-Course/k8s/devops-info-python/templates/deployment.yaml):

- mounts the file-based ConfigMap at `/config`
- mounts the PVC at `/data`
- injects the env ConfigMap with `envFrom`
- avoids `subPath`, so mounted ConfigMap files can update automatically

### Current ConfigMap and PVC Resources

```bash
kubectl get configmap,pvc -n lab12-audit
```

```text
NAME                                              DATA   AGE
configmap/kube-root-ca.crt                        1      11m
configmap/lab12-audit-devops-info-python-config   1      11m
configmap/lab12-audit-devops-info-python-env      11     11m

NAME                                                        STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/lab12-audit-devops-info-python-data   Bound    pvc-0bdba1a0-3c98-48bd-a481-d5ac2bbaad44   100Mi      RWO            standard       <unset>                 11m
```

### Rendered Config File Inside the Pod

```bash
kubectl exec -n lab12-audit deploy/lab12-audit-devops-info-python -c devops-info-python -- cat /config/config.json
```

```json
{
  "application": {
    "name": "devops-info-service",
    "environment": "dev",
    "version": "1.1.0"
  },
  "features": {
    "visitsEndpoint": true,
    "metricsEndpoint": true,
    "configHotReload": true
  },
  "settings": {
    "host": "0.0.0.0",
    "port": 3000,
    "logLevel": "WARNING",
    "configMountPath": "/config",
    "dataMountPath": "/data",
    "configFileName": "config.json",
    "visitsFileName": "visits",
    "visitsFilePath": "/data/visits",
    "configFilePath": "/config/config.json"
  }
}
```

### Environment Variables Injected from ConfigMap

```bash
kubectl exec -n lab12-audit deploy/lab12-audit-devops-info-python -c devops-info-python -- \
  sh -lc "env | grep -E '^(APP_NAME|APP_ENV|APP_MESSAGE|HOST|PORT|LOG_LEVEL|APP_CONFIG_PATH|VISITS_FILE_PATH|FEATURE_.*)=' | sort"
```

```text
APP_CONFIG_PATH=/config/config.json
APP_ENV=dev
APP_MESSAGE=Lab 12 release lab12-audit in dev
APP_NAME=devops-info-service
FEATURE_CONFIG_RELOAD_ENABLED=true
FEATURE_METRICS_ENDPOINT_ENABLED=true
FEATURE_VISITS_ENDPOINT_ENABLED=true
HOST=0.0.0.0
LOG_LEVEL=WARNING
PORT=3000
VISITS_FILE_PATH=/data/visits
```

## Persistent Volume

The PVC template is [k8s/devops-info-python/templates/pvc.yaml](/Users/pepega/Developer/learning/DevOps-Core-Course/k8s/devops-info-python/templates/pvc.yaml). It requests `100Mi`, defaults to `ReadWriteOnce`, and keeps `storageClass` configurable through values.

The deployment mounts that claim at `/data`, and the application writes the counter to `/data/visits`.

I also set the chart defaults to `replicaCount: 1` in [k8s/devops-info-python/values.yaml](/Users/pepega/Developer/learning/DevOps-Core-Course/k8s/devops-info-python/values.yaml) because this lab uses one file-backed counter on one RWO volume. That keeps the storage model deterministic.

### Persistence Test Evidence

Before deleting the pod:

```bash
kubectl exec -n lab12-audit deploy/lab12-audit-devops-info-python -c devops-info-python -- cat /data/visits
```

```text
2
```

Pod replacement test:

```bash
kubectl delete pod -n lab12-audit lab12-audit-devops-info-python-55c75c894-zm8sl
kubectl wait -n lab12-audit --for=condition=ready pod -l app.kubernetes.io/instance=lab12-audit --timeout=180s
kubectl exec -n lab12-audit deploy/lab12-audit-devops-info-python -c devops-info-python -- cat /data/visits
curl http://127.0.0.1:28086/visits
```

Observed result after the replacement pod became ready:

```text
2
{"count":2,"path":"/data/visits","timestamp":"2026-04-16T17:43:06.725104+00:00"}
```

That confirms the visit counter survived pod deletion and recreation through the PVC.

## ConfigMap vs Secret

| Use case | ConfigMap | Secret |
| --- | --- | --- |
| Non-sensitive application settings | Yes | No |
| Credentials, tokens, certificates | No | Yes |
| Typical delivery mechanism | File mount, env vars, `envFrom` | File mount, env vars, `envFrom` |
| Security expectation | Plain configuration object | Sensitive object, still protected mainly through RBAC and platform controls |

This chart keeps credentials in [k8s/devops-info-python/templates/secrets.yaml](/Users/pepega/Developer/learning/DevOps-Core-Course/k8s/devops-info-python/templates/secrets.yaml) and non-sensitive runtime settings in ConfigMaps.

## Bonus — ConfigMap Hot Reload

### Default Update Behavior

I patched the live file-backed ConfigMap directly and watched the application until the mounted file changed:

```bash
kubectl patch configmap -n lab12-audit lab12-audit-devops-info-python-config --type merge -p '<patched config.json>'
```

Measured result on April 16, 2026:

```text
observed_after_seconds=81
```

Observed runtime state after the change propagated:

```json
{
  "file_env": "hot-reload-audit",
  "file_log_level": "NOTICE",
  "env_env": "dev",
  "env_log_level": "DEBUG"
}
```

This is the important part:

- the file-backed configuration changed without restarting the pod
- the env-backed configuration did not change, because environment variables are fixed at container start

### `subPath` Limitation

This chart intentionally mounts `/config` as a directory, not with `subPath`:

```yaml
volumeMounts:
  - name: config-volume
    mountPath: /config
    readOnly: true
```

`subPath` mounts do not receive later ConfigMap updates, so they are the wrong fit for this bonus task. A normal directory mount is the correct choice when the application must observe file changes.

### Chosen Reload Approach

I implemented two complementary reload paths:

1. Application-level file reload. The app calls `load_application_config()` on every request, so the next request sees the updated mounted file once Kubernetes refreshes it.
2. Helm checksum rollout. The deployment template uses `checksum/config-file` and `checksum/config-env` annotations, so a Helm-managed ConfigMap change produces a new ReplicaSet and updates env-backed configuration too.

### Helm Upgrade Rollout Evidence

ReplicaSet state before and after a Helm-driven config change:

```text
before:
lab12-audit-devops-info-python-55c75c894   1     1     1

after:
lab12-audit-devops-info-python-55c75c894    0     0     <none>
lab12-audit-devops-info-python-675598d496   1     1     1
```

Observed state after:

- `helm upgrade lab12-audit ... --reuse-values --set config.logLevel=WARNING`
- `kubectl rollout status deployment/lab12-audit-devops-info-python -n lab12-audit`

File-backed configuration inside the new pod:

```json
{
  "environment": "dev",
  "logLevel": "WARNING"
}
```

Env-backed configuration inside the new pod:

```json
{"APP_ENV":"dev","LOG_LEVEL":"WARNING"}
```

That confirms the checksum annotation pattern works as intended for Helm-driven configuration changes.
