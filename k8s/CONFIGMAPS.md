# Lab 12 — ConfigMaps & Persistent Volumes

## Overview

This lab extends the Helm chart from Lab 11 with externalized configuration and persistent storage. The application was updated to keep a visits counter in a file, expose a new `/visits` endpoint, mount configuration from ConfigMaps, and persist data using a PersistentVolumeClaim.

## 1. Application Changes

### Visits Counter Implementation

The application was updated to persist a visits counter in a file stored at:

`/data/visits`

Implementation details:
- On each request to `/`, the application reads the current counter value
- The value is incremented
- The new value is written back to `/data/visits`
- A new `/visits` endpoint returns the current counter value
- A lock is used in application code to reduce race conditions during file updates

### New Endpoint

`GET /visits`

This endpoint returns the current number of visits stored in the persistent file.

### Local Docker Testing

A Docker Compose volume was added so the visits file survives container restarts.

Example local test commands:

```bash
mkdir -p data
docker compose up --build
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/visits
cat ./data/visits
docker compose down
docker compose up
curl http://127.0.0.1:5000/visits
cat ./data/visits
```

Screenshot before restart (2 visits): `docs/screenshots/12-1-before.png`
Screenshot after restart (3 visits): `docs/screenshots/12-2-after.png`

## 2. ConfigMap Implementation

### File-Based ConfigMap

A `files/` directory was added to the Helm chart and contains:

`k8s/devops-chart/files/config.json`

Example content:

```json
{
  "appName": "devops-app",
  "environment": "dev",
  "featureFlag": true
}
```

This file is loaded into a ConfigMap using Helm `.Files.Get`.

### ConfigMap Template Structure

The chart creates two ConfigMaps:

1. A file-based ConfigMap for `config.json`
2. An env-based ConfigMap for application environment variables

Example structure:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "devops-chart.fullname" . }}-config
data:
  config.json: |
{{ .Files.Get "files/config.json" | nindent 4 }}
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "devops-chart.fullname" . }}-env
data:
  APP_ENV: {{ .Values.config.appEnv | quote }}
  LOG_LEVEL: {{ .Values.config.logLevel | quote }}
  VISITS_FILE: "/data/visits"
```

### Mounting ConfigMap as a File

The file-based ConfigMap is mounted into the container at:

`/config/config.json`

Volume configuration pattern:

```yaml
volumes:
  - name: config-volume
    configMap:
      name: {{ include "devops-chart.fullname" . }}-config
```

Volume mount pattern:

```yaml
volumeMounts:
  - name: config-volume
    mountPath: /config
```

### Injecting ConfigMap as Environment Variables

The env-based ConfigMap is injected using:

```yaml
envFrom:
  - configMapRef:
      name: {{ include "devops-chart.fullname" . }}-env
```

### Verification Commands

List resources:

```bash
kubectl get configmap,pvc
```

Verify file mount:

```bash
kubectl exec -it <pod> -- cat /config/config.json
```

Verify environment variables:

```bash
kubectl exec -it <pod> -- printenv | grep -E 'APP_|LOG_LEVEL|VISITS_FILE'
```

#### `kubectl get configmap,pvc`
```
NAME                                       DATA   AGE
configmap/devops-app-devops-chart-config   1      7s
configmap/devops-app-devops-chart-env      3      7s
configmap/kube-root-ca.crt                 1      21d

NAME                                                 STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/devops-app-devops-chart-data   Bound    pvc-b35b8e3d-cc3e-4982-8aae-9939fc85d4b6   100Mi      RWO            standard       <unset>                 7s
```

#### `/config/config.json` inside the pod
```
{
  "appName": "devops-app",
  "environment": "dev",
  "featureFlag": true
}
```

#### Environment variables inside the pod

Expected variables include:
- `APP_ENV=dev`
- `LOG_LEVEL=info`
- `VISITS_FILE=/data/visits`

## 3. Persistent Volume Implementation

### PVC Configuration

A `PersistentVolumeClaim` was added to the Helm chart to persist application data.

Example template:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "devops-chart.fullname" . }}-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Mi
```

### Access Mode

This lab uses:

`ReadWriteOnce`

This means the volume can be mounted as read-write by a single node at a time. This is sufficient for the application in Minikube.

### Storage Class

The PVC used the cluster default storage class. In Minikube, this usually provisions storage automatically using the `standard` storage class.

### Volume Mount

The PVC is mounted into the application container at:

`/data`

That is where the visits counter file is stored:

`/data/visits`

### Verification Commands

Check the visits file in the pod:

```bash
kubectl exec -it <pod> -- cat /data/visits
```

Get service URL:

```bash
minikube service devops-app-devops-chart-service --url
```

Trigger requests:

```bash
curl <url>/
curl <url>/
curl <url>/visits
```

Screenshot: `docs/screenshots/12-3-visits.png`

### Persistence Test

1. Check the current value:
```bash
curl <url>/visits
kubectl exec -it <pod> -- cat /data/visits
```

2. Delete one pod:
```bash
kubectl delete pod <pod>
```

3. Wait for a new pod to be created:
```bash
kubectl get pods
```

4. Verify that the value is still present:
```bash
kubectl exec -it <new-pod> -- cat /data/visits
curl <url>/visits
```

### Result

If the counter value remains the same after deleting the pod, the data is persistent and the PVC works correctly.

## 4. ConfigMap vs Secret

### When to use ConfigMap

Use a ConfigMap for:
- Non-sensitive application configuration
- JSON, YAML, or text-based config files
- Environment variables that are not confidential
- Feature flags and environment names

Examples in this lab:
- `APP_ENV`
- `LOG_LEVEL`
- `VISITS_FILE`
- `config.json`

### When to use Secret

Use a Secret for:
- Passwords
- Tokens
- API keys
- Credentials and other sensitive values

Examples from the previous lab:
- application username
- application password
- Vault-injected values

### Key Differences

| Feature | ConfigMap | Secret |
|---|---|---|
| Intended for sensitive data | No | Yes |
| Default encoding | Plain text | Base64-encoded |
| Common usage | App config | Credentials |
| Mounted as file | Yes | Yes |
| Injected as env vars | Yes | Yes |

### Recommendation

- Use **ConfigMaps** for non-sensitive configuration
- Use **Secrets** for any sensitive values
- In production, combine ConfigMaps with proper secret management and persistent storage

## 5. Summary

This lab implemented:
- a persistent visits counter in the application
- a `/visits` endpoint
- a file-based ConfigMap mounted at `/config/config.json`
- an env-based ConfigMap injected with `envFrom`
- a `PersistentVolumeClaim` mounted at `/data`
- a persistence test showing data survives pod recreation

## Commands Used in This Lab

### Local testing
```bash
mkdir -p data
docker compose up --build
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/visits
cat ./data/visits
docker compose down
docker compose up
curl http://127.0.0.1:5000/visits
```

### Helm and Kubernetes
```bash
helm lint .
helm template devops-app .
helm upgrade --install devops-app . \
  --set image.tag=v3 \
  --set vault.enabled=false \
  --set secret.enabled=true \
  --set secret.username=admin \
  --set secret.password=supersecret

kubectl get configmap,pvc
kubectl get pods
kubectl exec -it <pod> -- cat /config/config.json
kubectl exec -it <pod> -- printenv | grep -E 'APP_|LOG_LEVEL|VISITS_FILE'
kubectl exec -it <pod> -- cat /data/visits
minikube service devops-app-devops-chart-service --url
kubectl delete pod <pod>
```