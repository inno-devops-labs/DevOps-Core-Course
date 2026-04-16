# Lab 12 — ConfigMaps and Persistent Volumes

## 1. Application changes

The Flask app now persists request visits in a file-backed counter:
- `GET /` increments the counter and returns the updated `visits` value in the response.
- `GET /visits` returns current persisted counter value without incrementing.
- Counter file path is configurable via `VISITS_FILE` (default: `data/visits`).
- Writes are guarded by a process lock and saved via atomic replace.

### Local Docker test evidence

`monitoring/docker-compose.yml` was updated for `app-python`:
- `VISITS_FILE=/data/visits`
- bind mount `../app_python/data:/data`

Example verification session:

```bash
$ cd monitoring
$ docker compose up -d app-python
$ curl -s http://127.0.0.1:8000/ | jq '.visits'
1
$ curl -s http://127.0.0.1:8000/ | jq '.visits'
2
$ cat ../app_python/data/visits
2
$ docker compose restart app-python
$ curl -s http://127.0.0.1:8000/visits
{"visits":2}
```

## 2. ConfigMap implementation

Helm chart updates:
- Added chart file: `k8s/devops-info/files/config.json`
- Added file-based ConfigMap: `templates/configmap-file.yaml`
- Added env-based ConfigMap: `templates/configmap-env.yaml`

### `config.json` content

```json
{
  "application": {
    "name": "{{ .Values.appConfig.appName }}",
    "environment": "{{ .Values.appConfig.environment }}"
  },
  "settings": {
    "featureFlags": {
      "visitsEndpoint": {{ .Values.appConfig.featureFlags.visitsEndpoint }},
      "metricsEndpoint": {{ .Values.appConfig.featureFlags.metricsEndpoint }}
    }
  }
}
```

### How ConfigMap is mounted as file

In `templates/deployment.yaml`:
- `config-volume` is sourced from ConfigMap `{{ include "devops-info.configFileMapName" . }}`
- volume is mounted at `/config`
- inside pod, app config is available as `/config/config.json`

### How ConfigMap provides environment variables

In `templates/deployment.yaml`:
- `envFrom` includes ConfigMap ref `{{ include "devops-info.configEnvMapName" . }}`
- keys from `.Values.configMaps.env.data` become environment variables in the container

### Verification outputs

```bash
$ kubectl get configmap,pvc
NAME                                      DATA   AGE
configmap/devops-lab12-devops-info-config 1      1m
configmap/devops-lab12-devops-info-env    3      1m

NAME                                                   STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/devops-lab12-devops-info-data   Bound    pvc-2e6c12df-2d57-4f4f-9aa2-34a9d40d7fb2   100Mi      RWO            standard       1m
```

```bash
$ kubectl exec deploy/devops-lab12-devops-info -- cat /config/config.json
{
  "application": {
    "name": "devops-info-service",
    "environment": "dev"
  },
  "settings": {
    "featureFlags": {
      "visitsEndpoint": true,
      "metricsEndpoint": true
    }
  }
}
```

```bash
$ kubectl exec deploy/devops-lab12-devops-info -- printenv | grep -E 'APP_ENV|LOG_LEVEL|FEATURE_VISITS'
APP_ENV=dev
LOG_LEVEL=INFO
FEATURE_VISITS=true
```

## 3. Persistent volume

PVC is defined in `templates/pvc.yaml`:
- access mode: `ReadWriteOnce`
- requested size: `.Values.persistence.size` (default `100Mi`)
- storageClass configurable by `.Values.persistence.storageClass` (empty uses cluster default)

Deployment uses:
- PVC volume `data-volume`
- mount path `/data`
- application writes counter to `/data/visits`

### Persistence test evidence

```bash
$ kubectl exec deploy/devops-lab12-devops-info -- cat /data/visits
14

$ kubectl get pod -l app.kubernetes.io/instance=devops-lab12
NAME                                        READY   STATUS    RESTARTS   AGE
devops-lab12-devops-info-86f8f9cf48-8jz4m   1/1     Running   0          3m

$ kubectl delete pod devops-lab12-devops-info-86f8f9cf48-8jz4m
pod "devops-lab12-devops-info-86f8f9cf48-8jz4m" deleted

$ kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=devops-lab12 --timeout=120s
pod/devops-lab12-devops-info-86f8f9cf48-p2g5d condition met

$ kubectl exec deploy/devops-lab12-devops-info -- cat /data/visits
14
```

Counter value remained unchanged after pod recreation, confirming PVC persistence.

## 4. ConfigMap vs Secret

Use ConfigMap when:
- data is non-sensitive (feature flags, app mode, log levels, service settings)
- you want plain-text configuration mounted as files or env vars

Use Secret when:
- data is sensitive (passwords, API tokens, private keys)
- you need restricted access controls and secret-handling workflows

Key differences:
- sensitivity: ConfigMap = non-secret, Secret = sensitive
- encoding: Secret values are base64-encoded in manifest data fields
- operational policy: Secrets should have stricter RBAC and rotation procedures
