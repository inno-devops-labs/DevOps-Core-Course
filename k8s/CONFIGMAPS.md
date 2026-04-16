# Lab 12 — ConfigMaps & Persistent Volumes

I completed Lab 12 and the bonus task on the local `kind-lab9` cluster. The implementation extends the Lab 11 Helm chart in `k8s/devops-info-service/` and the Python service in `app_python/` with:

- a file-backed visit counter stored at `/data/visits`
- a new `GET /visits` endpoint
- JSON configuration loaded from `/config/config.json`
- a Helm-managed file ConfigMap and env ConfigMap
- a PersistentVolumeClaim mounted at `/data`
- checksum-based rollout on ConfigMap changes

The final chart is intentionally configured for a single replica because the visit counter is file-based and should have a single writer.

## Task 1 — Application Persistence Upgrade

### Application changes

I updated the Python service in `app_python/app.py` so that:

- `GET /` increments a persistent visit counter
- the counter is stored in a file (`VISITS_FILE_PATH`, default `/data/visits`)
- `GET /visits` returns the current persisted count without incrementing it
- writes are protected with `threading.Lock`
- persistence uses atomic replacement via `os.replace`
- the application loads optional JSON config from `APP_CONFIG_FILE`

At startup the service reads the counter file if it exists; otherwise it starts from `0`.

### Local unit tests

I updated `app_python/tests/test_app.py` to cover:

- visit counter increments and file persistence
- `GET /visits`
- config file loading
- fallback behavior when the config file is missing

Test result:

```text
26 passed in 1.17s
Total coverage: 90.26%
```

### Local Docker persistence test

I added `app_python/docker-compose.yml` with a bind mount:

```yaml
volumes:
  - ./data:/data
```

In my local environment, host port `5000` was already occupied, so I mapped `5005 -> 5000` for the Docker Compose verification. The container itself still runs on port `5000`.

Commands used:

```bash
docker compose up --build -d
curl http://localhost:5005/
curl http://localhost:5005/
cat ./data/visits
docker compose down
docker compose up -d
curl http://localhost:5005/visits
```

Observed results:

First request:

```json
"visits":{"count":1,"file_path":"/data/visits"}
```

Second request:

```json
"visits":{"count":2,"file_path":"/data/visits"}
```

Counter on the host after two requests:

```text
2
```

Counter after container restart:

```json
{"count":2,"file_path":"/data/visits","timestamp":"2026-04-16T13:44:25.397932+00:00"}
```

## Task 2 — ConfigMaps

### Helm chart changes

I added the following chart pieces:

```text
k8s/devops-info-service/
  files/config.json
  templates/configmap.yaml
  templates/pvc.yaml
  templates/deployment.yaml
  templates/_helpers.tpl
  values.yaml
  values-dev.yaml
  values-prod.yaml
```

### File ConfigMap

The file-based ConfigMap is rendered from `files/config.json` using Helm `tpl` so values files can change the content per environment.

Rendered example from the running release:

```json
{
  "application": {
    "name": "devops-info-service",
    "environment": "stable",
    "description": "DevOps course info service deployed with Helm"
  },
  "settings": {
    "releaseTrack": "stable",
    "logLevel": "INFO",
    "persistenceEnabled": true,
    "visitsFilePath": "/data/visits",
    "featureFlags": {
      "visitsCounter": true,
      "configMapDemo": true,
      "pvcPersistence": true
    }
  }
}
```

### Env ConfigMap

The second ConfigMap injects key-value configuration via `envFrom`.

Verified environment variables inside the pod:

```text
APP_CONFIG_FILE=/config/config.json
APP_ENV=stable
APP_PASSWORD=change-me
APP_USERNAME=change-me
LOG_LEVEL=INFO
VISITS_FILE_PATH=/data/visits
```

### Verification

I deployed the chart into namespace `devops-lab12`:

```bash
helm upgrade --install lab12 k8s/devops-info-service \
  -n devops-lab12 \
  --create-namespace \
  --wait
```

Resource check:

```text
NAME                                         DATA   AGE
configmap/kube-root-ca.crt                   1      55s
configmap/lab12-devops-info-service-config   1      47s
configmap/lab12-devops-info-service-env      4      47s

NAME                                                   STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/lab12-devops-info-service-data   Bound    pvc-b685d510-333b-4312-94a9-06d2ba505192   100Mi      RWO            standard       <unset>                 47s
```

Mounted file inside the pod:

```bash
kubectl exec -n devops-lab12 deploy/lab12-devops-info-service -- cat /config/config.json
```

Output:

```json
{
  "application": {
    "name": "devops-info-service",
    "environment": "stable",
    "description": "DevOps course info service deployed with Helm"
  },
  "settings": {
    "releaseTrack": "stable",
    "logLevel": "INFO",
    "persistenceEnabled": true,
    "visitsFilePath": "/data/visits",
    "featureFlags": {
      "visitsCounter": true,
      "configMapDemo": true,
      "pvcPersistence": true
    }
  }
}
```

The application also confirmed that the config file was loaded successfully:

```json
"configuration":{
  "loaded":true,
  "path":"/config/config.json",
  "data":{
    "application":{"name":"devops-info-service","environment":"stable","description":"DevOps course info service deployed with Helm"},
    "settings":{"featureFlags":{"configMapDemo":true,"pvcPersistence":true,"visitsCounter":true},"logLevel":"INFO","persistenceEnabled":true,"releaseTrack":"stable","visitsFilePath":"/data/visits"}
  }
}
```

## Task 3 — Persistent Volumes

### PVC implementation

I added `templates/pvc.yaml` and the following values in the chart:

```yaml
persistence:
  enabled: true
  size: "100Mi"
  storageClass: ""
  accessModes:
    - ReadWriteOnce
  mountPath: "/data"
  fileName: "visits"
```

Notes:

- `ReadWriteOnce` is appropriate for a single-writer pod
- `storageClass: ""` means the cluster default storage class is used
- on this cluster the claim bound to the default `standard` class

### Persistence verification

I first generated visits and confirmed the file content before deleting the pod.

Before pod deletion:

```json
{"count":3,"file_path":"/data/visits","timestamp":"2026-04-16T13:46:50.827943+00:00"}
```

File content before deletion:

```text
3
```

Pod before deletion:

```text
lab12-devops-info-service-765488f99c-xfrc5
f75518e8-17cf-47e4-a327-1e6821f37b3e
```

Deletion command:

```bash
kubectl delete pod -n devops-lab12 lab12-devops-info-service-765488f99c-xfrc5
kubectl rollout status deployment/lab12-devops-info-service -n devops-lab12
```

New pod after recreation:

```text
lab12-devops-info-service-765488f99c-d98v6
c7421270-a1dc-4736-b9b9-b72bd5476673
```

Counter after the new pod started:

```json
{"count":3,"file_path":"/data/visits","timestamp":"2026-04-16T13:48:02.848145+00:00"}
```

This confirms that the counter survived pod deletion because the file was stored on the PVC.

## Task 4 — ConfigMap vs Secret

### When to use ConfigMap

Use a ConfigMap for non-sensitive configuration such as:

- application environment names
- log levels
- feature flags
- JSON application settings
- file paths and other runtime options

### When to use Secret

Use a Secret for sensitive data such as:

- passwords
- API tokens
- database credentials
- private keys

### Key differences

| Aspect | ConfigMap | Secret |
|--------|-----------|--------|
| Intended data | Non-sensitive | Sensitive |
| Encoding | Plain string data | Base64-encoded in the API object |
| Typical usage | Config files, env vars | Credentials, tokens, keys |
| This repository example | `config.json`, `APP_ENV`, `LOG_LEVEL` | `APP_USERNAME`, `APP_PASSWORD` |

ConfigMaps are not a security boundary. Sensitive values should stay in Secrets or an external secret manager such as Vault.

## Bonus — ConfigMap Hot Reload

### 1. Default mounted ConfigMap update behavior

I tested the default projected-volume behavior by updating the live ConfigMap directly with `kubectl apply` and then polling `/config/config.json` in the running pod until the new value appeared.

Changed field:

```json
"releaseTrack": "patched-live"
```

Measured delay:

```text
delay_seconds=22
```

Observed mounted file after the update:

```json
{
  "application": {
    "name": "devops-info-service",
    "environment": "stable",
    "description": "DevOps course info service deployed with Helm"
  },
  "settings": {
    "releaseTrack": "patched-live",
    "logLevel": "INFO",
    "persistenceEnabled": true,
    "visitsFilePath": "/data/visits",
    "featureFlags": {
      "visitsCounter": true,
      "configMapDemo": true,
      "pvcPersistence": true
    }
  }
}
```

The pod UID stayed the same during this test:

```text
c7421270-a1dc-4736-b9b9-b72bd5476673
```

This confirms the default behavior: mounted ConfigMap files update in-place, but not instantly.

### 2. Why I did not use `subPath`

I intentionally mounted the whole directory:

```yaml
volumeMounts:
  - name: config-volume
    mountPath: /config
    readOnly: true
```

I did not mount `/config/config.json` with `subPath` because `subPath` mounts do not receive live ConfigMap updates. Kubernetes copies the file for the container instead of maintaining the projected symlink structure used by the normal ConfigMap volume mount.

Use `subPath` when:

- you must place a file at an exact fixed path inside an existing directory

Avoid `subPath` when:

- you need automatic ConfigMap refresh inside the pod

### 3. Implemented reload approach

For the bonus implementation, I chose a restart-driven reload pattern with checksum annotations in `templates/deployment.yaml`:

```yaml
annotations:
  checksum/configmaps: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

That makes the Deployment pod template change whenever Helm renders different ConfigMap content, which triggers a rollout automatically.

### 4. Helm upgrade pattern verification

I then updated the release through Helm using a version-portable flow:

```bash
kubectl delete configmap lab12-devops-info-service-config -n devops-lab12

helm upgrade lab12 k8s/devops-info-service \
  -n devops-lab12 \
  --set config.settings.releaseTrack=bonus-rollout \
  --wait
```

I had intentionally modified the live ConfigMap directly in the previous step. On some Helm/Kubernetes combinations that can create an ownership conflict on the next upgrade, because the ConfigMap was changed outside Helm. Deleting the manually modified ConfigMap before the upgrade is the most portable way to hand control back to Helm and let it recreate the resource from the chart.

In my local session with Helm 4.1.3, `helm upgrade ... --force-conflicts` also worked, but the command block above is the portable reproduction flow I would recommend documenting.

Pod before Helm-driven rollout:

```text
lab12-devops-info-service-765488f99c-d98v6
c7421270-a1dc-4736-b9b9-b72bd5476673
```

Pod after Helm-driven rollout:

```text
lab12-devops-info-service-7c98d55dc4-cchmr
68ec08c9-1ee6-4bfb-b5cd-30e492b9b5f1
```

This proves a new pod was created.

The ConfigMap object itself contained the new value immediately:

```json
{
  "settings": {
    "releaseTrack": "bonus-rollout"
  }
}
```

The mounted file inside the restarted pod reflected the new value shortly after rollout completion:

```text
post_upgrade_file_delay_seconds=10
```

Final mounted file:

```json
{
  "application": {
    "name": "devops-info-service",
    "environment": "stable",
    "description": "DevOps course info service deployed with Helm"
  },
  "settings": {
    "releaseTrack": "bonus-rollout",
    "logLevel": "INFO",
    "persistenceEnabled": true,
    "visitsFilePath": "/data/visits",
    "featureFlags": {
      "visitsCounter": true,
      "configMapDemo": true,
      "pvcPersistence": true
    }
  }
}
```

After recording the bonus evidence, I reset the live release back to the repository defaults with:

```bash
helm upgrade lab12 k8s/devops-info-service \
  -n devops-lab12 \
  --reset-values \
  --wait
```

That returned the running release to the default `stable` configuration while keeping the bonus verification documented above.

## Summary

For Lab 12 I:

- implemented a file-backed visit counter and `GET /visits`
- verified persistence locally with Docker Compose
- added a file ConfigMap, env ConfigMap, and PVC to the Helm chart
- mounted config at `/config/config.json` and data at `/data`
- verified PVC-backed persistence across pod deletion
- documented ConfigMap vs Secret usage
- completed the bonus by measuring ConfigMap update delay, documenting the `subPath` limitation, and implementing checksum-based rollout on ConfigMap changes
