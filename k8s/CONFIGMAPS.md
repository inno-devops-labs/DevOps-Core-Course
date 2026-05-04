# Lab 12 — ConfigMaps & Persistent Volumes

## 1. Application Changes

### Visits counter implementation

The application was extended to persist a visit counter in a file.

Implemented behavior:
- each request to `/` reads the current counter value
- the counter is incremented
- the new value is written back to a file
- a new `/visits` endpoint returns the current value without incrementing it

### Data file location

The application now uses a configurable data directory:
- local default: `app_python/data`
- container runtime: `/data`

The visits counter is stored in:

```text
/data/visits
```

or, during local testing outside the container, in the local application data directory.

### New endpoint

A new endpoint was added:

```text
/visits
```

Example response:

```json
{"visits": 3}
```

### Local Docker testing evidence

A local Docker Compose setup was created:

- `app_python/docker-compose.yml`
- host volume mount: `./data:/data`

Testing steps:
1. start the container
2. call `/` multiple times
3. check `/visits`
4. inspect the file `app_python/data/visits`
5. restart the container
6. verify the counter value remains the same

### Local persistence result

Observed outputs:

After repeated requests:
- `/` returned `"visits": 2`
- then `/` returned `"visits": 3`
- `/visits` returned `{"visits":3}`
- `app_python/data/visits` contained `3`

After container restart:
- `/visits` still returned `{"visits":3}`
- `app_python/data/visits` still contained `3`

This confirmed persistence across local container restarts.

---

## 2. ConfigMap Implementation

### Chart file structure additions

The Helm chart was extended with:

- `app-python-chart/files/config.json`
- `app-python-chart/templates/configmap.yaml`

### `config.json` content

A file-based application configuration was added:

```json
{
  "appName": "devops-info-service",
  "environment": "dev",
  "featureFlags": {
    "visitsCounter": true,
    "metricsEnabled": true
  }
}
```

### ConfigMap template structure

The chart creates two ConfigMaps:

1. **File-based ConfigMap** for mounting `config.json`
2. **Environment ConfigMap** for injecting key-value settings into the pod

### File-based ConfigMap

The file-based ConfigMap uses Helm `.Files.Get`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "app-python-chart.fullname" . }}-config
data:
  config.json: |-
{{ .Files.Get "files/config.json" | indent 4 }}
```

### Environment variable ConfigMap

The second ConfigMap exposes environment variables:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "app-python-chart.fullname" . }}-env
data:
  APP_ENV: "dev"
  APP_NAME: "devops-info-service"
  FEATURE_VISITS_COUNTER: "true"
```

### How ConfigMap is mounted as file

In the Deployment:
- a volume is created from the ConfigMap
- the volume is mounted into the pod at `/config`

Relevant deployment logic:

```yaml
volumes:
  - name: config-volume
    configMap:
      name: {{ include "app-python-chart.fullname" . }}-config

volumeMounts:
  - name: config-volume
    mountPath: /config
```

This makes the file available as:

```text
/config/config.json
```

### How ConfigMap provides environment variables

The environment ConfigMap is injected using `envFrom`:

```yaml
envFrom:
  - configMapRef:
      name: {{ include "app-python-chart.fullname" . }}-env
```

### Verification outputs

#### File content inside the pod

Command used:

```bash
kubectl exec -it app-release-app-python-chart-75b56f9dd-h6l67 -- cat /config/config.json
```

Observed output:

```json
{
  "appName": "devops-info-service",
  "environment": "dev",
  "featureFlags": {
    "visitsCounter": true,
    "metricsEnabled": true
  }
}
```

#### Environment variables inside the pod

Command used:

```bash
kubectl exec -it app-release-app-python-chart-75b56f9dd-h6l67 -- printenv | grep APP_
```

Observed output:

```text
APP_ENV=dev
APP_NAME=devops-info-service
APP_RELEASE_APP_PYTHON_CHART_PORT=tcp://10.101.118.150:80
APP_RELEASE_APP_PYTHON_CHART_SERVICE_HOST=10.101.118.150
APP_RELEASE_APP_PYTHON_CHART_PORT_80_TCP_PROTO=tcp
APP_RELEASE_APP_PYTHON_CHART_SERVICE_PORT=80
APP_RELEASE_APP_PYTHON_CHART_PORT_80_TCP_ADDR=10.101.118.150
APP_RELEASE_APP_PYTHON_CHART_PORT_80_TCP_PORT=80
APP_RELEASE_APP_PYTHON_CHART_SERVICE_PORT_HTTP=80
APP_RELEASE_APP_PYTHON_CHART_PORT_80_TCP=tcp://10.101.118.150:80
```

The important evidence is:
- `APP_ENV=dev`
- `APP_NAME=devops-info-service`

The additional `APP_RELEASE_...` variables were automatically injected by Kubernetes service discovery.

### ConfigMap creation evidence

Command used:

```bash
kubectl get configmap,pvc
```

Observed output:

```text
NAME                                            DATA   AGE
configmap/app-release-app-python-chart-config   1      7m30s
configmap/app-release-app-python-chart-env      3      7m30s
configmap/kube-root-ca.crt                      1      96m

NAME                                                      STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/app-release-app-python-chart-data   Bound    pvc-4ff6e54e-6239-467c-8efd-5e3f1f7ef340   100Mi      RWO            standard       <unset>                 7m30s
```

This confirms that both ConfigMaps were created successfully.

---

## 3. Persistent Volume

### PVC configuration

A new template was added:

- `app-python-chart/templates/pvc.yaml`

The chart creates a PersistentVolumeClaim:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "app-python-chart.fullname" . }}-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: {{ .Values.persistence.size }}
```

### Persistence values

The Helm values file contains:

```yaml
persistence:
  enabled: true
  size: 100Mi
  storageClass: ""
```

### Access mode explanation

The PVC uses:

```text
ReadWriteOnce
```

Meaning:
- the volume can be mounted as read-write by a single node at a time

This is appropriate for the lab because:
- minikube runs on one node
- the visits file is a simple single-writer persistence example

### Storage class discussion

The PVC was bound to the default minikube storage class:

```text
standard
```

Minikube automatically provisioned the backing PersistentVolume using its default local storage provisioner.

### Volume mount configuration

The PVC is mounted into the application pod at `/data`.

Relevant deployment logic:

```yaml
volumes:
  - name: data-volume
    persistentVolumeClaim:
      claimName: {{ include "app-python-chart.fullname" . }}-data

volumeMounts:
  - name: data-volume
    mountPath: /data
```

This ensures the visits file is written to persistent storage instead of the container filesystem.

### Persistence test evidence

#### Counter value before pod deletion

A service URL was opened via minikube and checked with curl.

Observed output:

```json
{"visits":1}
```

This established the baseline counter value before pod deletion.

#### Pod deletion command

A running application pod was deleted:

```bash
kubectl delete pod app-release-app-python-chart-75b56f9dd-rqzgr
```

Kubernetes then created a replacement pod automatically.

#### Counter value after new pod starts

After the new pod reached `2/2 Running`, the service was checked again:

```bash
curl http://127.0.0.1:63866/visits
```

Observed output:

```json
{"visits":1}
```

The value remained unchanged.

#### File content inside the new pod

Command used:

```bash
kubectl exec -it app-release-app-python-chart-75b56f9dd-glk4n -- cat /data/visits
```

Observed result:
- file content was `1`

This confirms the visits counter survived pod deletion and recreation.

### PVC status evidence

From `kubectl get configmap,pvc`:

```text
persistentvolumeclaim/app-release-app-python-chart-data   Bound    pvc-4ff6e54e-6239-467c-8efd-5e3f1f7ef340   100Mi      RWO            standard       <unset>                 7m30s
```

This proves the PVC was successfully provisioned and bound.

---

## 4. ConfigMap vs Secret

### When to use ConfigMap

Use a ConfigMap for:
- non-sensitive configuration
- feature flags
- application settings
- environment names
- file-based configuration such as JSON or YAML

Examples from this lab:
- `config.json`
- `APP_ENV`
- `APP_NAME`
- `FEATURE_VISITS_COUNTER`

### When to use Secret

Use a Secret for:
- passwords
- tokens
- API keys
- certificates
- credentials

Examples from the previous lab:
- `username`
- `password`
- Vault-injected secret data

### Key differences

| Aspect | ConfigMap | Secret |
|---|---|---|
| Purpose | Non-sensitive configuration | Sensitive configuration |
| Encoding | Plain text in API objects | Base64-encoded in API objects |
| Typical use | app config, env settings, config files | credentials, keys, tokens |
| Security expectation | low sensitivity | higher sensitivity, though native K8s Secrets still need protection |

### Important note

Even though Kubernetes Secrets are meant for sensitive values, they are still not strongly secure by default unless:
- etcd encryption at rest is enabled
- RBAC is configured properly
- access is tightly controlled

For high-value production secrets, Vault remains the stronger solution.

---

## 5. Final Result

By the end of the lab, the following were implemented successfully:

- application-level visits counter persisted in a file
- new `/visits` endpoint
- local Docker volume persistence verified
- file-based ConfigMap mounted into the pod
- environment variable ConfigMap injected into the pod
- PersistentVolumeClaim created and bound
- persistent storage mounted to `/data`
- visits counter survived pod deletion and pod recreation

This lab demonstrated how to externalize configuration with ConfigMaps and preserve application state with PersistentVolumeClaims in Kubernetes.
