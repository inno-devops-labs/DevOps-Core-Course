# ConfigMaps & Persistence Notes

## Overview

This document describes the Lab 12 implementation built on top of the existing Helm chart and the current Python application from `labs/lab3/app_python/`.

The implemented scope in the provided project state covers:
- file-based visits counter logic in the application,
- local Docker-based persistence verification,
- ConfigMap creation from `files/config.json`,
- ConfigMap mounting inside the Kubernetes pod,
- PVC templating and PVC mounting through the Helm chart.

The available evidence also shows a successfully bound PVC and the application working in Kubernetes after the persistence-related chart update. However, the screenshot bundle does not explicitly include a pod deletion / recreation sequence with a before-and-after visits comparison.

---

## 1. Application Changes

The current Flask application in `labs/lab3/app_python/app.py` was extended with a persistent visits counter.

### Added logic
- `VISITS_FILE` path configurable through environment variable
- `read_visits()` helper to read the counter safely
- `write_visits()` helper to update the counter file
- `GET /visits` endpoint to read the current count
- counter increment on `GET /`
- `/visits` added to endpoint normalization for metrics

### Local Docker testing
The local `docker-compose.yaml` mounts the host file `./visits` into `/app/visits` inside the container. This allows the counter value to survive container restarts because the data is stored outside the container writable layer.

During verification, the mounted file had to remain writable for the container process. After that, repeated requests to `/` updated the value correctly and `/visits` returned the current count.

### Evidence
- `docs/screenshots/task_1_demo_of_work.png`

---

## 2. ConfigMap Implementation

### 2.1 File-based configuration
A chart-local file was created:

- `k8s/app-python-chart/files/config.json`

Its content is mounted into the pod as a JSON configuration file.

### 2.2 ConfigMap template structure
The chart contains:

- `k8s/app-python-chart/templates/configmap.yaml`

The template renders a ConfigMap using Helm `.Files.Get`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "app-python-chart.fullname" . }}-config
data:
  config.json: |
{{ .Files.Get "files/config.json" | indent 4 }}
```

### 2.3 File mount in the deployment
The deployment mounts this ConfigMap through a volume named `app-config` and exposes it inside the container as `/config.json`.

### 2.4 Verification
The mounted file was verified with:

```bash
kubectl exec <pod> -- cat /config.json
```

The saved output confirms that the file is present inside the running pod and contains the expected JSON configuration.

### Evidence
- `docs/screenshots/task_2_deployment.png`
- `docs/screenshots/task_2_helm_lint_template.png`
- `docs/evidence/lab12_config_inside_pod.txt`

---

## 3. Persistent Volume Implementation

### 3.1 PVC template
The chart now contains:

- `k8s/app-python-chart/templates/pvc.yaml`

This template creates a `PersistentVolumeClaim` for application data with configurable size and optional storage class.

### 3.2 Values for persistence
The chart values now contain:

```yaml
persistence:
  enabled: true
  size: 100Mi
  storageClass: ""
  mountPath: /data
```

This moves persistence configuration into the same chart-driven model as the rest of the deployment.

### 3.3 Deployment integration
The deployment template now includes:
- a PVC-backed volume named `data-volume`,
- a `volumeMount` to the configured persistence mount path,
- application runtime that is intended to use a file-backed visits counter together with persistent storage.

### 3.4 Verification
The available screenshots confirm:
- successful `helm lint`,
- successful Helm rendering after adding persistence resources,
- successful `helm upgrade --install`,
- PVC creation with `STATUS: Bound`,
- working application responses in the Kubernetes environment.

### 3.5 Evidence limitation
What is not explicitly shown in the current screenshots is a strict before/after persistence test around pod deletion. Because of that, this document states that PVC resources and PVC binding are implemented and verified, while the strongest runtime proof of survival across pod recreation is not directly visible in the provided archive.

### Evidence
- `docs/screenshots/task_3_helm_lint_tempalte.png`
- `docs/screenshots/task_3_helm_upgrade_get_pvc.png`
- `docs/screenshots/task_3_proof.png`

---

## 4. Environment Variables via ConfigMap

The bonus env-style ConfigMap part is not explicitly represented as a separate dedicated template in the provided chart state. The current Lab 12 implementation focuses on file-based ConfigMap delivery through `config.json`, which is the main required scenario.

Therefore, this document does not claim a separate env-based ConfigMap implementation beyond the already existing Secret-driven `envFrom` usage inherited from the previous lab.

---

## 5. ConfigMap vs Secret

### Use ConfigMap when
- the data is not sensitive,
- the configuration should remain readable and version-controlled,
- the same container image must be reused across environments.

Examples:
- JSON configuration,
- feature flags,
- app mode,
- log level.

### Use Secret when
- the data is sensitive,
- the value should not be stored as plain configuration,
- RBAC and stricter handling rules are needed.

Examples:
- passwords,
- API tokens,
- credentials,
- secret keys.

In this project:
- `config.json` is a ConfigMap use case,
- credentials from Lab 11 remain a Secret use case.

---

## 6. Verification Summary

The current collected evidence confirms:
- the Helm chart passes lint validation,
- the Kubernetes deployment is healthy,
- the ConfigMap-backed file is accessible in the pod,
- the chart contains and deploys a PVC that reaches the `Bound` state,
- the application was upgraded locally with a visits counter.

Available evidence files:
- `docs/evidence/lab12_helm_lint.txt`
- `docs/evidence/lab12_get_all.txt`
- `docs/evidence/lab12_get_pods.txt`
- `docs/evidence/lab12_config_inside_pod.txt`

---

## 7. Conclusion

The provided Lab 12 implementation now demonstrates application-side file persistence, ConfigMap-based file injection through Helm, and PVC resource creation as part of the Kubernetes chart.

The Kubernetes evidence clearly shows a bound PVC and a working application deployment. The remaining gap in the current evidence package is only the lack of an explicit before/after visits check across pod deletion, which would be the strongest runtime proof of persistence.