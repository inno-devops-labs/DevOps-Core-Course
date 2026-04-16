# Lab 12

## 1. Application Changes

### Implementation
- Added two new endpoints to the FastAPI application:
  - `GET /visit` – increments the visit counter and returns the new value.
  - `GET /visits` – returns the current counter value without incrementing.
- Counter is stored in a file at `/data/visits`.
- The application creates the directory `/data` if it doesn't exist and writes the counter atomically.

```bash
$ curl http://localhost:8000/visit

{"visits":1}

$ curl http://localhost:8000/visit

{"visits":2}
$ docker-compose restart
$ curl http://localhost:8000/visits

{"visits":2}
```

## 2. ConfigMap Implementation

### Configmap template

```bash
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "simple-app.fullname" . }}-file
data:
  config.json: |-
{{ .Files.Get "files/config.json" | indent 4 }}
```

### config.json

```bash
{
  "app_name": "SimpleApp",
  "environment": "dev",
  "features": {
    "debug": true
  }
}
```

### Mounting as file

```bash
volumes:
  - name: config-volume
    configMap:
      name: {{ include "simple-app.fullname" . }}-file
containers:
  - name: {{ .Chart.Name }}
    volumeMounts:
      - name: config-volume
        mountPath: /config
```

### .env variables

```bash
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "simple-app.fullname" . }}-env
data:
  APP_ENV: {{ .Values.environment | default "dev" | quote }}
  LOG_LEVEL: {{ .Values.logLevel | default "info" | quote }}
```

### Verification

```bash
$ kubectl get configmap

NAME                                 DATA   AGE
kube-root-ca.crt                     1      23d
simple-app-release-simple-app-env    2      2d19h
simple-app-release-simple-app-file   1      2d19h
vexell@vexell-ASUS-TUF-Gaming-F15-FX506HC-FX506HC:
```

## 3. Persistent volume

### PVC Configuration

```bash
{{- if .Values.persistence.enabled }}
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "simple-app.fullname" . }}-data
spec:
  accessModes:
    - {{ .Values.persistence.accessMode | default "ReadWriteOnce" }}
  resources:
    requests:
      storage: {{ .Values.persistence.size | default "100Mi" }}
{{- end }}
```
- `resources.requests.storage` – the amount of storage requested (100 MiB in this case). Kubernetes will bind this claim to a PersistentVolume (PV) that can satisfy this size (or larger).

- `accessModes` – defines how the volume can be mounted by pods. 

 We use ReadWriteOnce because our simple application only needs to write the visits counter file from a single pod.
 
 A StorageClass provides a way to describe different “classes” of storage offered by the cluster administrator. 

### Volume mount configuration

```bash
volumes:
  - name: data-volume
    persistentVolumeClaim:
      claimName: {{ include "simple-app.fullname" . }}-data
containers:
  - volumeMounts:
      - name: data-volume
        mountPath: /data
```

### Proof

```bash
$ kubectl get pvc

NAME                                 STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
simple-app-release-simple-app-data   Bound    pvc-0f4ce554-a016-435b-b470-43f20788efbb   100Mi      RWO            standard       <unset>                 2d19h


$ kubectl exec simple-app-release-simple-app-546964bcbf-64tf8 -- cat /data/visits

2

$ kubectl delete pod simple-app-release-simple-app-546964bcbf-64tf8

pod "simple-app-release-simple-app-546964bcbf-64tf8" deleted from default namespace

$ kubectl get pods -w

NAME                                             READY   STATUS    RESTARTS   AGE
simple-app-release-simple-app-546964bcbf-6zj4w   1/1     Running   0          10s
simple-app-release-simple-app-546964bcbf-cpwlh   1/1     Running   0          103s
simple-app-release-simple-app-546964bcbf-d7ls5   1/1     Running   0          119s
simple-app-release-simple-app-546964bcbf-hbnn9   1/1     Running   0          2m12s
simple-app-release-simple-app-546964bcbf-x897n   1/1     Running   0          2m7s

$ kubectl exec simple-app-release-simple-app-546964bcbf-6zj4w -- cat /data/visits

2
```

## 4. ConfigMap vs Secret

| Feature | ConfigMap | Secret |
|---------|-----------|--------|
| **Purpose** | Non-sensitive configuration data (e.g., app settings, feature flags) | Sensitive data (passwords, API keys, TLS certificates) |
| **Data encoding** | Plain text (no encoding) | Base64-encoded (not encrypted by default) |
| **Size limit** | 1 MiB per object | 1 MiB per object |
| **Security** | No special protection; accessible to anyone with API access | Can be encrypted at rest (etcd encryption), supports finer RBAC |
| **Use cases** | Environment variables, config files, command-line arguments | Credentials, tokens, SSH keys, TLS secrets |
| **Creation methods** | `kubectl create configmap`, from literals/files, or via Helm | `kubectl create secret generic`, from literals/files, or via Helm |
| **Consumption** | As env vars, mounted volumes, or `--from-env-file` | Same as ConfigMap, but with added security considerations |
| **Immutability** | Can be made immutable (`immutable: true`) | Can be made immutable (`immutable: true`) |

### When to use which?

- **ConfigMap** – for everything that is **not** sensitive: application name, log level, feature flags, endpoint URLs, etc.
- **Secret** – for any data that must be kept confidential: database passwords, OAuth tokens, private keys, etc.

### Production Recommendations

- Always enable **etcd encryption** for Secrets (and optionally for ConfigMaps).
- Use **RBAC** to restrict access: read/write permissions for Secrets should be minimized.
- Never commit real secrets to Git. Use placeholders in `values.yaml` and inject real secrets at deployment time (Vault, Sealed Secrets, External Secrets Operator).
- Prefer **mounted Secrets** over environment variables if the secret is large or frequently updated.
- Set `immutable: true` for both ConfigMaps and Secrets that should not change after deployment.