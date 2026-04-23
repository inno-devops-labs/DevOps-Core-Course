# Lab 12 Report - ConfigMaps and Persistent Volumes

## 1. Application Changes

### 1.1 Visits counter implementation

Implemented in app code:
- app_python/app.py

Behavior:
- Counter is stored in a file path from VISITS_FILE env var.
- Default path is ./data/visits for local runs.
- For Kubernetes, VISITS_FILE is set to /data/visits.
- Root endpoint / increments the counter and returns the current value in stats.visits.
- New endpoint /visits returns current counter value.

Implementation notes:
- File operations are guarded with a process-level lock to reduce concurrent write races.
- Atomic file update pattern is used: write to temporary file, then replace target file.
- Startup initializes visits file if it does not exist.

### 1.2 New endpoint documentation

- GET /visits -> returns:

```json
{"visits": 2}
```

### 1.3 Local testing evidence

Automated tests:

```bash
cd app_python
./venv/bin/pytest -q
```

Output:

```text
......                                                                   [100%]
6 passed, 2 warnings in 0.55s
```

Runtime evidence (executed with TestClient):

```text
root-call-1-visits=1
root-call-2-visits=2
visits-endpoint=2
file-content=2
```

### 1.4 Docker Compose for local persistence

Added file:
- app_python/docker-compose.yml

Volume mapping:

```yaml
volumes:
  - ./data:/app/data
```

Env override:

```yaml
environment:
  VISITS_FILE: "/app/data/visits"
```

---

## 2. ConfigMap Implementation

### 2.1 File-based ConfigMap

Added chart file:
- k8s/devops-info/files/config.json

Added template:
- k8s/devops-info/templates/configmap-file.yaml

Template uses Helm file loading:

```yaml
data:
  config.json: |-
{{ tpl (.Files.Get "files/config.json") . | indent 4 }}
```

This mounts JSON config as a file in the pod.

### 2.2 Environment variable ConfigMap

Added template:
- k8s/devops-info/templates/configmap-env.yaml

Data comes from values:
- .Values.configEnv.APP_ENV
- .Values.configEnv.LOG_LEVEL
- .Values.configEnv.FEATURE_VISITS

### 2.3 Deployment wiring

Updated:
- k8s/devops-info/templates/deployment.yaml

Changes:
- Config file mounted as volume at /config.
- Env vars injected via envFrom -> configMapRef.
- Rollout checksums added:
  - checksum/config-file
  - checksum/config-env

Verification commands to run in cluster:

```bash
kubectl get configmap
kubectl exec <pod> -- cat /config/config.json
kubectl exec <pod> -- printenv | grep -E 'APP_ENV|LOG_LEVEL|FEATURE_VISITS'
```

---

## 3. Persistent Volume Implementation

### 3.1 PVC template

Added:
- k8s/devops-info/templates/pvc.yaml

PVC spec:
- accessModes: ReadWriteOnce
- storage request: .Values.persistence.size (default 100Mi)
- storageClassName: optional from .Values.persistence.storageClass

### 3.2 Deployment volume mount

Updated deployment to mount PVC:
- volume name: data-volume
- claimName: <release>-data
- mountPath: /data (from values)

Application path alignment:
- VISITS_FILE=/data/visits

### 3.3 Persistence test procedure

Run in cluster:

```bash
kubectl get pvc
kubectl get pods -l app.kubernetes.io/name=devops-info

# hit / several times
kubectl exec <pod> -- cat /data/visits

kubectl delete pod <pod-name>
kubectl get pods -l app.kubernetes.io/name=devops-info -w

# after new pod is running
kubectl exec <new-pod> -- cat /data/visits
kubectl exec <new-pod> -- curl -s localhost:5000/visits
```

Expected result:
- Counter value is the same before and after pod deletion.

---

## 4. ConfigMap vs Secret

Use ConfigMap when:
- Data is non-sensitive configuration.
- Plain application settings are needed (feature flags, log level, environment name).

Use Secret when:
- Data is sensitive (passwords, tokens, API keys, certificates).
- You need stricter access control and secret management integration.

Key differences:
- ConfigMap stores plain config data.
- Secret stores sensitive data (base64 encoded in manifests and should be protected with RBAC and encryption at rest).
- Operationally both can be consumed as files or environment variables.

---

## 6. Changed Files Summary

Application:
- app_python/app.py
- app_python/tests/test_app.py
- app_python/README.md
- app_python/docker-compose.yml

Helm chart:
- k8s/devops-info/values.yaml
- k8s/devops-info/files/config.json
- k8s/devops-info/templates/_helpers.tpl
- k8s/devops-info/templates/configmap-file.yaml
- k8s/devops-info/templates/configmap-env.yaml
- k8s/devops-info/templates/pvc.yaml
- k8s/devops-info/templates/deployment.yaml
