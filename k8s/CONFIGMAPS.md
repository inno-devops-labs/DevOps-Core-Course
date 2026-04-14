# Lab 12 — ConfigMaps & Persistent Volumes

## 1. Application Changes

### Visits counter implementation
The application was updated to persist a visits counter in a file stored at `/data/visits`.
A new `/visits` endpoint returns the current value. On startup, the application checks whether the file exists and creates it with `0` if missing. Each request to `/` reads the current value, increments it, and writes the new value back to the file.

To reduce race conditions during concurrent requests, the FastAPI application uses an `asyncio.Lock` around the increment operation and writes the file atomically through a temporary file and `os.replace()`.

### New endpoint
- `GET /visits` — returns the current visit counter and the path to the visits file.

```python
@app.get("/visits", response_class=JSONResponse)
async def visits():
    return {
        "visits": read_visits_count(),
        "visits_file": str(VISITS_FILE),
    }
```

### Local Docker testing
Example `docker-compose.yml` volume mapping:

```yaml
services:
  devops-info-service:
    build: .
    container_name: devops-info-service
    ports:
      - "5000:5000"
    environment:
      HOST: 0.0.0.0
      PORT: 5000
      DEBUG: "false"
      SERVICE_NAME: devops-info-service
      SERVICE_VERSION: "1.0.0"
      SERVICE_DESCRIPTION: "DevOps course info service"
      APP_ENV: local
      LOG_LEVEL: INFO
      DATA_DIR: /app/data
      VISITS_FILE: /app/data/visits
      CONFIG_FILE: /app/config/config.json
    volumes:
      - ./data:/app/data
      - ./config:/app/config:ro
```

Commands used:

```bash
docker compose up --build -d
curl http://localhost:5000/
curl http://localhost:5000/
curl http://localhost:5000/visits
cat ./data/visits
docker compose restart
curl http://localhost:5000/visits
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course\app_python> curl http://localhost:5000/
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"application":{"environment":"local","log_level":"INFO"},"config":{"config_file":"/app/config/config.json","loaded":false,"reason":"config file not found"},"persistence":{"visits_file":"/app/data/visits","visits_count":2},"system":{"hostname":"2b2c1442ee13","platform":"Linux","platform_version":"#1 SMP PREEMPT_DYNAMIC Thu Jun  5 18:30:46 UTC 2025","architecture":"x86_64","cpu_count":8,"python_version":"3.13.11"},"runtime":{"uptime_seconds":74,"uptime_human":"0 hours, 1 minutes","current_time":"2026-04-06T12:44:37.341Z","timezone":"UTC"},"request":{"client_ip":"172.21.0.1","user_agent":"curl/8.18.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"},{"path":"/visits","method":"GET","description":"Current visits counter"},{"path":"/metrics","method":"GET","description":"Prometheus metrics"}]}
PS C:\Users\zagur\DevOps\DevOps-Core-Course\app_python> curl http://localhost:5000/
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"application":{"environment":"local","log_level":"INFO"},"config":{"config_file":"/app/config/config.json","loaded":true,"content":{"applicationName":"devops-info-service","environment":"local","settings":{"featureFlags":{"debugEndpoints":true,"showVisitsInRoot":true},"logLevel":"INFO"}}},"persistence":{"visits_file":"/app/data/visits","visits_count":3},"system":{"hostname":"2b2c1442ee13","platform":"Linux","platform_version":"#1 SMP PREEMPT_DYNAMIC Thu Jun  5 18:30:46 UTC 2025","architecture":"x86_64","cpu_count":8,"python_version":"3.13.11"},"runtime":{"uptime_seconds":119,"uptime_human":"0 hours, 1 minutes","current_time":"2026-04-06T12:45:22.843Z","timezone":"UTC"},"request":{"client_ip":"172.21.0.1","user_agent":"curl/8.18.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"},{"path":"/visits","method":"GET","description":"Current visits counter"},{"path":"/metrics","method":"GET","description":"Prometheus metrics"}]}
PS C:\Users\zagur\DevOps\DevOps-Core-Course\app_python> curl http://localhost:5000/visits
{"visits":3,"visits_file":"/app/data/visits"}
PS C:\Users\zagur\DevOps\DevOps-Core-Course\app_python> cat ./data/visits                
3
PS C:\Users\zagur\DevOps\DevOps-Core-Course\app_python> docker compose restart
time="2026-04-06T15:45:55+03:00" level=warning msg="C:\\Users\\zagur\\DevOps\\DevOps-Core-Course\\app_python\\docker-compose.yml: the attribute `version` is obsolete, it will be ignored, please remove it to avoid potential confusion"
[+] Restarting 1/1
 ✔ Container devops-info-service  Started                                                             1.4s 
PS C:\Users\zagur\DevOps\DevOps-Core-Course\app_python> curl http://localhost:5000/visits
{"visits":3,"visits_file":"/app/data/visits"}
```

This demonstrates that the counter survives container restarts.

---

## 2. ConfigMap Implementation

### File-based ConfigMap
A `files/config.json` file was added to the Helm chart and loaded through `.Files.Get` in `templates/configmap.yaml`.
The ConfigMap is mounted into the Pod at `/config`, so the file becomes available as `/config/config.json`.

Example template:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "devops-info-service.fullname" . }}-config
data:
  config.json: |-
{{ tpl (.Files.Get "files/config.json") . | indent 4 }}
```

Actual `ConfigMap`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "devops-info-service.fullname" . }}-config
  labels:
    {{- include "devops-info-service.labels" . | nindent 4 }}
data:
  config.json: |-
{{ tpl (.Files.Get "files/config.json") . | indent 4 }}
```

`config.json` content:

```json
{
  "applicationName": "{{ .Values.config.applicationName }}",
  "environment": "{{ .Values.environment }}",
  "settings": {
    "featureFlags": {
      "debugEndpoints": "{{ .Values.config.features.debugEndpoints }}",
      "showVisitsInRoot": "{{ .Values.config.features.showVisitsInRoot }}"
    },
    "logLevel": "{{ .Values.logLevel }}"
  }
}
```

### Environment-variable ConfigMap
A second ConfigMap was added for key-value settings injected via `envFrom`.
This ConfigMap provides values such as `APP_ENV`, `LOG_LEVEL`, `DATA_DIR`, `VISITS_FILE`, and `CONFIG_FILE`.

Example template:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "devops-info-service.fullname" . }}-env
data:
  APP_ENV: {{ .Values.environment | quote }}
  LOG_LEVEL: {{ .Values.logLevel | quote }}
  DATA_DIR: {{ .Values.persistence.mountPath | quote }}
  VISITS_FILE: {{ printf "%s/visits" .Values.persistence.mountPath | quote }}
  CONFIG_FILE: "/config/config.json"
```

Actual content:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "devops-info-service.fullname" . }}-env
  labels:
    {{- include "devops-info-service.labels" . | nindent 4 }}
data:
  APP_ENV: {{ .Values.environment | quote }}
  LOG_LEVEL: {{ .Values.logLevel | quote }}
  DATA_DIR: {{ .Values.persistence.mountPath | quote }}
  VISITS_FILE: {{ printf "%s/visits" .Values.persistence.mountPath | quote }}
  CONFIG_FILE: "/config/config.json"
  SERVICE_NAME: {{ .Values.config.applicationName | quote }}
  SERVICE_VERSION: {{ .Chart.AppVersion | quote }}
  SERVICE_DESCRIPTION: "DevOps course info service"
```

### Deployment integration
The Deployment mounts the file ConfigMap as a volume and injects the env ConfigMap through `envFrom`.

```yaml
volumeMounts:
  - name: config-volume
    mountPath: /config
    readOnly: true

envFrom:
  - configMapRef:
      name: {{ include "devops-info-service.fullname" . }}-env
```

### Verification
Commands:

```bash
kubectl get configmap
kubectl exec <pod-name> -- cat /config/config.json
kubectl exec <pod-name> -- printenv | grep -E 'APP_ENV|LOG_LEVEL|DATA_DIR|VISITS_FILE|CONFIG_FILE'
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get configmap
NAME                                     DATA   AGE
dev-release-devops-info-service-config   1      2m17s
dev-release-devops-info-service-env      8      2m17s
kube-root-ca.crt                         1      47h
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl exec -it dev-release-devops-info-service-77fb4df4d-7txf2 -- cat /config/config.json
{
  "applicationName": "devops-info-service",
  "environment": "dev",
  "settings": {
    "featureFlags": {
      "debugEndpoints": "true",
      "showVisitsInRoot": "true"
    },
    "logLevel": "DEBUG"
  }
}
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl exec -it dev-release-devops-info-service-77fb4df4d-7txf2 -- printenv
PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
HOSTNAME=dev-release-devops-info-service-77fb4df4d-7txf2
TERM=xterm
VISITS_FILE=/data/visits
APP_ENV=dev
DATA_DIR=/data
PORT=5000
SERVICE_DESCRIPTION=DevOps course info service
SERVICE_NAME=devops-info-service
SERVICE_VERSION=1.0.0
CONFIG_FILE=/config/config.json
LOG_LEVEL=DEBUG
PYTHONUNBUFFERED=1
VAULT_SERVICE_PORT_HTTP=8200
VAULT_PORT_8201_TCP_PORT=8201
VAULT_AGENT_INJECTOR_SVC_PORT_443_TCP_PORT=443
VAULT_AGENT_INJECTOR_SVC_PORT_443_TCP_ADDR=10.106.186.21
DEV_RELEASE_DEVOPS_INFO_SERVICE_PORT_80_TCP_PORT=80
KUBERNETES_PORT_443_TCP=tcp://10.96.0.1:443
VAULT_SERVICE_PORT=8200
VAULT_SERVICE_HOST=10.101.33.242
VAULT_PORT=tcp://10.101.33.242:8200
VAULT_PORT_8201_TCP_PROTO=tcp
VAULT_AGENT_INJECTOR_SVC_SERVICE_HOST=10.106.186.21
VAULT_AGENT_INJECTOR_SVC_SERVICE_PORT_HTTPS=443
DEV_RELEASE_DEVOPS_INFO_SERVICE_SERVICE_PORT_HTTP=80
KUBERNETES_SERVICE_PORT_HTTPS=443
KUBERNETES_PORT=tcp://10.96.0.1:443
DEV_RELEASE_DEVOPS_INFO_SERVICE_PORT_80_TCP_ADDR=10.111.128.142
DEV_RELEASE_DEVOPS_INFO_SERVICE_SERVICE_PORT=80
KUBERNETES_PORT_443_TCP_ADDR=10.96.0.1
VAULT_AGENT_INJECTOR_SVC_PORT_443_TCP=tcp://10.106.186.21:443
VAULT_AGENT_INJECTOR_SVC_SERVICE_PORT=443
VAULT_PORT_8200_TCP=tcp://10.101.33.242:8200
VAULT_PORT_8200_TCP_ADDR=10.101.33.242
VAULT_AGENT_INJECTOR_SVC_PORT_443_TCP_PROTO=tcp
DEV_RELEASE_DEVOPS_INFO_SERVICE_PORT_80_TCP=tcp://10.111.128.142:80
DEV_RELEASE_DEVOPS_INFO_SERVICE_PORT_80_TCP_PROTO=tcp
KUBERNETES_SERVICE_HOST=10.96.0.1
VAULT_PORT_8201_TCP=tcp://10.101.33.242:8201
VAULT_AGENT_INJECTOR_SVC_PORT=tcp://10.106.186.21:443
DEV_RELEASE_DEVOPS_INFO_SERVICE_SERVICE_HOST=10.111.128.142
DEV_RELEASE_DEVOPS_INFO_SERVICE_PORT=tcp://10.111.128.142:80
KUBERNETES_PORT_443_TCP_PORT=443
VAULT_PORT_8200_TCP_PROTO=tcp
KUBERNETES_SERVICE_PORT=443
VAULT_PORT_8200_TCP_PORT=8200
VAULT_PORT_8201_TCP_ADDR=10.101.33.242
KUBERNETES_PORT_443_TCP_PROTO=tcp
VAULT_SERVICE_PORT_HTTPS_INTERNAL=8201
GPG_KEY=7169605F62C751356D054A26A821E680E5FA6305
PYTHON_VERSION=3.13.11
PYTHON_SHA256=16ede7bb7cdbfa895d11b0642fa0e523f291e6487194d53cf6d3b338c3a17ea2
PYTHONDONTWRITEBYTECODE=1
PIP_DISABLE_PIP_VERSION_CHECK=1
PIP_NO_CACHE_DIR=1
HOST=0.0.0.0
DEBUG=FALSE
HOME=/
```

---

## 3. Persistent Volume

### PVC configuration
A `PersistentVolumeClaim` template was added as `templates/pvc.yaml`.
It requests `100Mi` of storage with the `ReadWriteOnce` access mode. The storage class is configurable through `values.yaml`; when it is left empty, the cluster default storage class is used.

Example template:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "devops-info-service.fullname" . }}-data
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: {{ .Values.persistence.size }}
```

Actual content:

```yaml
{{- if .Values.persistence.enabled }}
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "devops-info-service.fullname" . }}-data
  labels:
    {{- include "devops-info-service.labels" . | nindent 4 }}
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: {{ .Values.persistence.size }}
  {{- if .Values.persistence.storageClass }}
  storageClassName: {{ .Values.persistence.storageClass | quote }}
  {{- end }}
{{- end }}
```

### Volume mount
The Deployment mounts the PVC to `/data`, which is where the application writes the visits file.

```yaml
volumes:
  - name: data-volume
    persistentVolumeClaim:
      claimName: {{ include "devops-info-service.fullname" . }}-data

volumeMounts:
  - name: data-volume
    mountPath: /data
```

### Persistence test
Commands:

```bash
kubectl get pvc
kubectl get pods
curl $(minikube service dev-release-devops-info-service --url)/
curl $(minikube service dev-release-devops-info-service --url)/
curl $(minikube service dev-release-devops-info-service --url)/visits
kubectl exec <pod-name> -- cat /data/visits
kubectl delete pod <pod-name>
kubectl get pods -w
kubectl exec <new-pod-name> -- cat /data/visits
curl $(minikube service dev-release-devops-info-service --url)/visits
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get pvc
NAME                                   STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
data-vault-0                           Bound    pvc-bb496615-47de-4f35-8858-dc1d49b606ce   10Gi       RWO            standard       <unset>                 47h
dev-release-devops-info-service-data   Bound    pvc-095ac863-4a1e-408a-b6e0-eefa463d56e1   100Mi      RWO            standard       <unset>                 3m10s
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl exec -it dev-release-devops-info-service-77fb4df4d-7txf2 -- cat /data/visits 
5
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl delete pod dev-release-devops-info-service-77fb4df4d-7txf2                  
pod "dev-release-devops-info-service-77fb4df4d-7txf2" deleted from default namespace
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get pods                                        
NAME                                              READY   STATUS    RESTARTS      AGE
dev-release-devops-info-service-77fb4df4d-7wwwt   0/1     Running   0             8s
vault-0                                           1/1     Running   1 (46h ago)   47h
vault-agent-injector-75998c9b76-dtzxm             1/1     Running   1 (46h ago)   47h
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get pods
NAME                                              READY   STATUS    RESTARTS      AGE
dev-release-devops-info-service-77fb4df4d-7wwwt   0/1     Running   0             10s
vault-0                                           1/1     Running   1 (46h ago)   47h
vault-agent-injector-75998c9b76-dtzxm             1/1     Running   1 (46h ago)   47h
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get pods
NAME                                              READY   STATUS    RESTARTS      AGE
dev-release-devops-info-service-77fb4df4d-7wwwt   1/1     Running   0             11s
vault-0                                           1/1     Running   1 (46h ago)   47h
vault-agent-injector-75998c9b76-dtzxm             1/1     Running   1 (46h ago)   47h
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl exec -it dev-release-devops-info-service-77fb4df4d-7wwwt -- cat /data/visits
5
```

This confirms that the counter survives Pod recreation because the file is stored on a persistent volume rather than in the container filesystem.

---

## 4. ConfigMap vs Secret

### When to use ConfigMap
ConfigMaps should be used for non-sensitive configuration data:
- environment name;
- log level;
- feature flags;
- JSON/YAML/text configuration files.

### When to use Secret
Secrets should be used for sensitive data:
- passwords;
- API tokens;
- database credentials;
- certificates and keys.

### Key differences
- ConfigMaps are intended for non-confidential configuration.
- Secrets are intended for confidential data and are handled separately by Kubernetes.
- Both can be consumed as files or environment variables, but Secrets should receive stricter access control.