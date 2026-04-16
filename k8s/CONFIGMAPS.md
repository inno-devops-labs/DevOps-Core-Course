# Lab 12 Report - ConfigMaps and Persistent Volumes

## 1) Application Changes

Implemented in `app_python/app.py`:
- Added file-backed visits counter (`VISITS_FILE`, default `/data/visits`)
- Added thread lock for safe increment logic
- Added atomic write via temp file + `os.replace`
- Added `GET /visits` endpoint
- Added visits metadata to `GET /` response

Also updated:
- `app_python/tests/test_endpoints.py` with visits tests
- `app_python/docker-compose.yml` with persistent host mount (`./data:/data`)
- `app_python/README.md` with usage instructions

### Local Docker Evidence

Command flow:
```bash
docker compose up -d --build
curl http://localhost:5050/visits
curl http://localhost:5050/
curl http://localhost:5050/visits
docker compose restart app
curl http://localhost:5050/visits
cat ./data/visits
docker compose down
```

Output excerpt:
```text
{"storage_file":"/data/visits","visits":0}
...
{"visits":{"count":1,"storage_file":"/data/visits"}}
{"storage_file":"/data/visits","visits":1}
... restart ...
{"storage_file":"/data/visits","visits":1}
1
```

## 2) ConfigMap Implementation

### Chart Files
- `k8s/devops-info-service/files/config.json`
- `k8s/devops-info-service/templates/configmap-file.yaml`
- `k8s/devops-info-service/templates/configmap-env.yaml`

### Mount and Env Injection

In deployment:
- File ConfigMap mounted to `/config`
- Env ConfigMap injected with `envFrom.configMapRef`
- `VISITS_FILE=/data/visits` injected via env helper

### Verification Evidence

`kubectl get configmap,pvc`:
```text
NAME                                              DATA   AGE
configmap/lab12-devops-info-service-config-env    4      5m30s
configmap/lab12-devops-info-service-config-file   1      5m30s
...
NAME                                                   STATUS   VOLUME                                       CAPACITY   ACCESS MODES   STORAGECLASS
persistentvolumeclaim/lab12-devops-info-service-data   Bound    pvc-ff2169b6-85f3-49e0-be6c-dccb3dc24e71     100Mi      RWO            standard
```

File inside pod:
```bash
kubectl exec lab12-devops-info-service-5f89c695f6-6m5bw -- cat /config/config.json
```
Output excerpt:
```json
{
  "applicationName": "devops-info-service",
  "environment": "dev",
  "features": {
    "visitsCounter": true,
    "prometheusMetrics": true
  },
  "settings": {
    "timezone": "UTC",
    "reloadStrategy": "checksum-annotation"
  }
}
```

Environment variables in pod (`kubectl exec lab12-devops-info-service-5f89c695f6-6m5bw -- printenv`):
```text
APP_ENV=dev
APP_NAME=devops-info-service
FEATURE_VISITS_COUNTER=true
LOG_LEVEL=INFO
VISITS_FILE=/data/visits
```

## 3) Persistent Volume (PVC)

Implemented:
- `k8s/devops-info-service/templates/pvc.yaml`
- Access mode: `ReadWriteOnce`
- Requested storage: `100Mi`
- Configurable storageClass: `.Values.persistence.storageClass`
- Mounted PVC path: `/data`

### Persistence Test Evidence

Commands:
```bash
kubectl exec lab12-devops-info-service-5f89c695f6-6m5bw -- python -c "import urllib.request; [urllib.request.urlopen('http://127.0.0.1:5000/').read() for _ in range(2)]"
kubectl exec lab12-devops-info-service-5f89c695f6-6m5bw -- cat /data/visits
kubectl delete pod lab12-devops-info-service-5f89c695f6-6m5bw
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/instance=lab12 --timeout=180s
kubectl exec lab12-devops-info-service-5f89c695f6-t4v2r -- cat /data/visits
```

Output:
```text
6
pod "lab12-devops-info-service-5f89c695f6-6m5bw" deleted
pod/lab12-devops-info-service-5f89c695f6-t4v2r condition met
6
```

Result: counter survived pod recreation.

## 4) ConfigMap vs Secret

Use ConfigMap when:
- Non-sensitive app config
- Feature flags, env mode, static service settings
- Files or env key-value pairs

Use Secret when:
- Passwords, tokens, API keys, credentials
- Any value requiring stronger access control and secure handling

Key differences:
- ConfigMap is plaintext-oriented configuration
- Secret is intended for sensitive data
- Both are base64 in manifests, but Secret has security-focused semantics and RBAC usage patterns

## Bonus - Hot Reload and Restart Pattern

### 1) Default ConfigMap update delay

Measured mounted file update delay after patching ConfigMap data:
```text
dev
dev
...
patched
UPDATED_IN:57
```

Observed delay: ~57 seconds (matches kubelet sync + cache behavior).

### 2) subPath limitation

`subPath` mount does not auto-refresh ConfigMap updates because container gets a file copy bind mount, not the live projected directory.  
Use full directory mount (as implemented with `/config`) when runtime updates are required.

### 3) Implemented reload approach

Implemented checksum annotations in deployment template:
- `checksum/config-file`
- `checksum/config-env`

This forces a rollout when chart-managed config content changes via Helm upgrade.

### 4) Helm upgrade behavior

Deployment template includes checksum annotations and new pod rollout was observed after config-related upgrade:
```text
OLD_POD:lab12-devops-info-service-58dccf686c-rrp8v
... helm upgrade ...
lab12-devops-info-service-5f89c695f6-7qpdv   Running
```
