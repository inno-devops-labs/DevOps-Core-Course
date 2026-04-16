# Lab 12

## Application Changes

### Description of visits counter implementation

- / endpoint reads the current count from /data/visits.json, increments it by one, and writes the updated value back to the file.
- /visits endpoint provides read-only access by loading the current count from the same JSON file without modifying it.

### New endpoint documentation

#### `/visits`

Return current visits count.

Example:

```json
{
    'visits': 43,
    'timestamp': "YYYY-MM-DD HH:MM:SS.mmmmmm"
}
```

### Local testing evidence with Docker

```bash
curl localhost:8000/
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"a121d2d4582b","platform":"Linux","platform_version":"6.15.4-200.fc42.x86_64","architecture":"x86_64","cpu_count":12,"python_version":"3.12.13"},"runtime":{"uptime_seconds":21,"uptime_human":"0 hours, 0 minutes","current_time":"2026-04-16T10:18:07.804996+00:00","timezone":"UTC"},"request":{"client_ip":"172.20.0.1","user_agent":"curl/8.11.1","method":"GET","path":"/"},"endpoints":[{"path":"/openapi.json","description":"openapi","methods":["GET","HEAD"]},{"path":"/docs","description":"swagger_ui_html","methods":["GET","HEAD"]},{"path":"/docs/oauth2-redirect","description":"swagger_ui_redirect","methods":["GET","HEAD"]},{"path":"/redoc","description":"redoc_html","methods":["GET","HEAD"]},{"path":"/metrics","description":"metrics","methods":["GET"]},{"path":"/visits","description":"get_visits","methods":["GET"]},{"path":"/","description":"read_root","methods":["GET"]},{"path":"/health","description":"health","methods":["GET"]}]}

curl localhost:8000/visits
{"visits":2,"timestamp":"2026-04-16T10:18:13.907677+00:00"}
```

## ConfigMap Implementation

### ConfigMap template structure

The ConfigMap implementation uses **two separate ConfigMaps** defined in `templates/configmap.yaml`:

| ConfigMap | Purpose | Type | Usage |
|-----------|---------|------|-------|
| `{{ release }}-config` | Stores application configuration file | File-based | Mounted as volume to `/config/config.json` |
| `{{ release }}-env-config` | Stores environment variables as key-value pairs | Environment variables | Injected via `envFrom.configMapRef` |

Both ConfigMaps include proper metadata and labels using Helm templating:

```yaml
metadata:
  name: {{ include "mychart.fullname" . }}-config
  labels:
    {{- include "mychart.labels" . | nindent 4 }}
```

### config.json Content

The configuration file is stored in `files/config.json` and contains the application settings:

```json
{
    "application_name": "Python app",
    "env": "dev"
}
```

This file is loaded into the first ConfigMap using **`.Files.Get`** Helm function, which reads the file content directly:

```yaml
data:
  config.json: |
    {{- .Files.Get "files/config.json" | nindent 4 }}
```

The `.Files.Get` approach ensures the configuration file is embedded in the ConfigMap and version-controlled with your Helm chart.

---

### How ConfigMap is Mounted as File

The configuration file is mounted as a **volume** in the pod's filesystem. In `templates/deployment.yaml`:

```yaml
volumeMounts:
  - name: config-volume
    mountPath: /config
```

The volume definition maps the ConfigMap to the pod:

```yaml
volumes:
  - name: config-volume
    configMap:
      name: {{ include "mychart.fullname" . }}-config
```

**Result:** The `config.json` file becomes accessible at **`/config/config.json`** inside the running container.

#### Verification

```bash
kubectl exec myapp-mychart-589fdc4574-blsk5 -- cat /config/config.json
{
    "application_name": "Python app",
    "env": "dev"
}
```

### How ConfigMap Provides Environment Variables

The second ConfigMap (`env-config`) stores key-value pairs that are injected directly as **environment variables**:

```yaml
data:
  APPLICATION_NAME: "Python app"
  APP_ENV: "dev"
  LOG_LEVEL: "info"
```

These are loaded into the pod using **`envFrom` with `configMapRef`**:

```yaml
envFrom:
  - secretRef:
      name: {{ include "mychart.fullname" . }}-credentials
  - configMapRef:
      name: {{ include "mychart.fullname" . }}-env-config
```

**Result:** All keys from the ConfigMap become environment variables in the container with **exact key names**.

#### Verification

```bash
kubectl exec myapp-mychart-589fdc4574-blsk5 -- printenv | grep APP_
APP_ENV=dev
```

Persistent Volume

## PVC configuration explanation

The **PersistentVolumeClaim (PVC)** is defined in `templates/pvc.yaml` and requests storage resources from the Kubernetes cluster:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "mychart.fullname" . }}-data
  labels:
    {{- include "mychart.labels" . | nindent 4 }}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: {{ .Values.persistence.size }}
  {{- if .Values.persistence.storageClass }}
  storageClassName: {{ .Values.persistence.storageClass }}
  {{- end }}
```

The PVC is **conditionally created** using `{{- if .Values.persistence.enabled }}`, allowing it to be disabled entirely through `values.yaml`. Storage size is **configurable** (default **100Mi**) and can be modified without changing the template.

### Access Modes and Storage Class Discussion

| Aspect | Configuration | Purpose |
|--------|---------------|---------|
| **Access Mode** | `ReadWriteOnce` | Storage can be mounted by **one pod at a time** for read and write operations. Ideal for single-instance applications like visit counters. |
| **Storage Class** | `{{ .Values.persistence.storageClass }}` | Dynamically provisions storage based on the cluster's available storage backends. **Empty string** uses the default storage class (Minikube provides hostPath by default). |
| **Storage Size** | `{{ .Values.persistence.size }}` | Set to **100Mi** in `values.yaml`, sufficient for application data like visit counters or logs. Configurable without template modifications. |

### Volume Mount Configuration

The PVC is mounted to the pod in `templates/deployment.yaml`:

**Volume Definition (spec.volumes):**

```yaml
volumes:
  {{- if .Values.persistence.enabled }}
  - name: data-volume
    persistentVolumeClaim:
      claimName: {{ include "mychart.fullname" . }}-data
  {{- end }}
```

**Volume Mount Definition (containers.volumeMounts):**

```yaml
volumeMounts:
  - name: data-volume
    mountPath: /data
```

**Result:** The PVC is mounted at **`/data`** inside the container, making it accessible to the application for reading and writing persistent data.

| Configuration | Value | Purpose |
|---|---|---|
| **Volume Name** | `data-volume` | Reference identifier used in volumeMounts |
| **Mount Path** | `/data` | Directory inside pod where PVC is accessible |
| **Claim Name** | Release-specific name | Links to the PVC created by `templates/pvc.yaml` |

**Application Usage:**
The Python app writes the visit counter to `/data/visits`. When the pod restarts, a new pod mounts the same PVC and reads the persisted counter value, ensuring **data continuity**.

### Persistence test evidence

```bash
minikube service myapp-mychart
┌───────────┬───────────────┬─────────────┬───────────────────────────┐
│ NAMESPACE │     NAME      │ TARGET PORT │            URL            │
├───────────┼───────────────┼─────────────┼───────────────────────────┤
│ default   │ myapp-mychart │ http/80     │ http://192.168.49.2:31813 │
└───────────┴───────────────┴─────────────┴───────────────────────────┘
🎉  Opening service default/myapp-mychart in default browser...

curl http://192.168.49.2:31813/visits
{"visits":42,"timestamp":"2026-04-16T18:38:03.077385+00:00"}

kubectl delete pod myapp-mychart-59bf6d5c68-dd8z9 
pod "myapp-mychart-59bf6d5c68-dd8z9" deleted from default namespace

curl http://192.168.49.2:31813/visits
{"visits":47,"timestamp":"2026-04-16T18:38:47.554049+00:00"}
```


```bash
kubectl get configmap,pvc
NAME                                 DATA   AGE
configmap/kube-root-ca.crt           1      6h42m
configmap/myapp-mychart-config       1      148m
configmap/myapp-mychart-env-config   3      148m

NAME                                       STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/myapp-mychart-data   Bound    pvc-eab79707-c994-4af6-ac56-d397597543a7   100Mi      RWO            standard       <unset>                 17m
```