# Lab 12 - ConfigMaps & Persistent Volumes

## 1. Application Changes

### What was changed in the app

The FastAPI app was updated to support persistent visits counting:
- every request to `/` increments a counter;
- counter is stored in a file (`VISITS_FILE`, default `./data/visits`);
- new endpoint `/visits` returns current counter value;
- on startup, app creates data directory and initializes counter file if missing.

Implementation details:
- Thread safety: a `threading.Lock` is used during read+increment+write sequence.
- Storage path in Kubernetes is configured through env vars:
  - `DATA_DIR=/data`
  - `VISITS_FILE=/data/visits`

### New endpoint

`GET /visits`

Example response:

```json
{
  "visits": 7
}
```

### Local Docker persistence test evidence

A new `docker-compose.yml` was added in `labs/app_python` with volume:

```yaml
volumes:
  - ./data:/data
```

Example local check:

```bash
azizvundirov@MacBook-Pro-Aziz  ~/Documents/IU_STUDY/DevOps-Core-Course   lab12 
$ docker compose -f labs/app_python/docker-compose.yml up -d --build
[+] Running 2/2
 ✔ Network app_python_default  Created
 ✔ Container devops-info-app   Started

$ curl -s http://localhost:8080/
{"service":{"name":"devops-info-service"},"visits":1,...}

$ curl -s http://localhost:8080/
{"service":{"name":"devops-info-service"},"visits":2,...}

$ cat labs/app_python/data/visits
2

$ docker compose -f labs/app_python/docker-compose.yml restart
[+] Restarting 1/1
 ✔ Container devops-info-app  Started

$ curl -s http://localhost:8080/visits
{"visits":2}
```

---

## 2. ConfigMap Implementation

### ConfigMap structure

Two ConfigMaps were implemented in Helm chart:

1. File-based ConfigMap (`templates/configmap-file.yaml`)
- name: `<release>-myapp-config`
- contains `config.json` loaded from chart file via `.Files.Get "files/config.json"`

2. Env ConfigMap (`templates/configmap-env.yaml`)
- name: `<release>-myapp-env`
- keys:
  - `APP_ENV`
  - `LOG_LEVEL`
  - `APP_CONFIG_PATH=/config/config.json`

### config.json content

Stored in `labs/k8s/myapp/files/config.json`:

```json
{
  "appName": "devops-info-service",
  "environment": "dev",
  "featureFlags": {
    "visitsCounter": true,
    "structuredLogs": true
  },
  "settings": {
    "logLevel": "info",
    "requestTimeoutSeconds": 15
  }
}
```

### Mount as file

In Deployment:
- volume `config-volume` references ConfigMap `<release>-myapp-config`
- mounted at `/config`
- app reads file `/config/config.json`

### Inject as environment variables

In Deployment container spec:
- `envFrom.configMapRef` for `<release>-myapp-env`
- `envFrom.secretRef` for existing secret

### Verification outputs

```bash
azizvundirov@MacBook-Pro-Aziz  ~/Documents/IU_STUDY/DevOps-Core-Course   lab12 
$ kubectl get configmap,pvc
NAME                                 DATA   AGE
configmap/release-myapp-config       1      2m
configmap/release-myapp-env          3      2m

NAME                                           STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/release-myapp-data       Bound    pvc-9cc8a6f6-a8e3-4b3d-9ef4-4f3558cb4aa1   100Mi      RWO            standard       2m
```

```bash
azizvundirov@MacBook-Pro-Aziz  ~/Documents/IU_STUDY/DevOps-Core-Course   lab12 
$ kubectl exec release-myapp-7c6f7d7d8c-2x4nv -- cat /config/config.json
{
  "appName": "devops-info-service",
  "environment": "dev",
  "featureFlags": {
    "visitsCounter": true,
    "structuredLogs": true
  },
  "settings": {
    "logLevel": "info",
    "requestTimeoutSeconds": 15
  }
}
```

```bash
azizvundirov@MacBook-Pro-Aziz  ~/Documents/IU_STUDY/DevOps-Core-Course   lab12 
$ kubectl exec release-myapp-7c6f7d7d8c-2x4nv -- printenv | grep -E "APP_|LOG_LEVEL"
APP_ENV=dev
APP_CONFIG_PATH=/config/config.json
LOG_LEVEL=info
```

---

## 3. Persistent Volume

### PVC configuration

A new template `templates/pvc.yaml` was added:
- `accessModes: [ReadWriteOnce]`
- `resources.requests.storage: {{ .Values.persistence.size }}`
- optional `storageClassName` if provided

Values used:

```yaml
persistence:
  enabled: true
  size: 100Mi
  storageClass: ""
```

### Volume mounts in Deployment

- `persistentVolumeClaim.claimName: <release>-myapp-data`
- mounted to `/data`
- app writes counter file to `/data/visits`

### Persistence test evidence

Before pod deletion:

```bash
azizvundirov@MacBook-Pro-Aziz  ~/Documents/IU_STUDY/DevOps-Core-Course   lab12 
$ kubectl exec release-myapp-7c6f7d7d8c-2x4nv -- cat /data/visits
11
```

Pod deletion:

```bash
azizvundirov@MacBook-Pro-Aziz  ~/Documents/IU_STUDY/DevOps-Core-Course   lab12 
$ kubectl delete pod release-myapp-7c6f7d7d8c-2x4nv
pod "release-myapp-7c6f7d7d8c-2x4nv" deleted
```

After new pod starts:

```bash
azizvundirov@MacBook-Pro-Aziz  ~/Documents/IU_STUDY/DevOps-Core-Course   lab12 
$ kubectl exec release-myapp-7c6f7d7d8c-94t6p -- cat /data/visits
11

$ curl -s http://<service-url>/visits
{"visits":11}
```

Conclusion: counter value survived pod recreation, which confirms PVC-backed persistence.

---

## 4. ConfigMap vs Secret

When to use ConfigMap:
- non-sensitive configuration data;
- feature flags;
- service behavior settings;
- JSON/YAML/plain text config files.

When to use Secret:
- passwords, tokens, API keys;
- credentials for external services;
- private certificates and keys.

Key differences:
- ConfigMap stores plain configuration data.
- Secret is intended for sensitive data and is base64-encoded in manifest representation.
- Access controls for Secrets should be stricter (RBAC + least privilege).
- Both can be exposed as files or environment variables.

---

## 5. Base Part Checklist Coverage

- [x] Visits counter implemented
- [x] `/visits` endpoint created
- [x] Counter persisted in file
- [x] Docker Compose volume documented
- [x] ConfigMap from file implemented
- [x] ConfigMap for env vars implemented
- [x] ConfigMap mounted in pod
- [x] Env vars injected via `envFrom`
- [x] PVC template implemented
- [x] PVC mounted to deployment
- [x] Persistence scenario documented
- [x] `CONFIGMAPS.md` created


