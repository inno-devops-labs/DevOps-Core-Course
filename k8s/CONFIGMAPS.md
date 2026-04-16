# Lab 12 - ConfigMaps & Persistent Volumes

## Application Changes

### Description of visits counter implementation

A visit counter was added to the app. On each `GET /` request the counter is read from a file, incremented, and written back. A new `GET /visits` endpoint returns the current count.

Counter file path is controlled by the `VISITS_FILE` env var (default `/data/visits`). A threading lock guards the read-modify-write cycle.

### New endpoint

```
GET /visits  ->  {"visits": <int>}
```

### Local testing with Docker Compose

`docker-compose.yml` mounts a named volume `visits_data` at `/data`:

```yaml
volumes:
  - visits_data:/data
```

A named volume is used instead of a bind mount because the container runs as a non-root user and a bind mount would inherit host directory ownership, causing permission errors.

Testing:

```
$ docker compose up -d
$ curl localhost:5000/
$ curl localhost:5000/
$ curl localhost:5000/
$ curl localhost:5000/visits
{"visits":3}
$ docker compose restart
$ curl localhost:5000/visits
{"visits":3}
```

Counter persists across restarts.

## ConfigMap Implementation

### File-based ConfigMap

`templates/configmap.yaml` defines two ConfigMaps. The first loads `files/config.json` using `.Files.Get`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "devops-info-service.fullname" . }}-config
data:
  config.json: |-
{{ .Files.Get "files/config.json" | indent 4 }}
```

`files/config.json` content:

```json
{
  "app_name": "devops-info-service",
  "environment": "production",
  "features": {
    "visits_counter": true,
    "prometheus_metrics": true
  }
}
```

### Env-var ConfigMap

The second ConfigMap provides key-value pairs:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "devops-info-service.fullname" . }}-env
data:
  APP_ENV: {{ .Values.appEnv | quote }}
  LOG_LEVEL: {{ .Values.logLevel | quote }}
```

### Mounting in deployment

`deployment.yaml` mounts the file ConfigMap as a volume and injects the env ConfigMap via `envFrom`:

```yaml
volumes:
  - name: config-volume
    configMap:
      name: <release>-devops-info-service-config
containers:
  - volumeMounts:
      - name: config-volume
        mountPath: /config
    envFrom:
      - configMapRef:
          name: <release>-devops-info-service-env
```

### Verification

```
$ kubectl get configmap | grep devops
configmap/devops-devops-info-service-config   1      5m43s
configmap/devops-devops-info-service-env      2      5m43s

$ kubectl exec devops-devops-info-service-5df8d55f7b-l7bgv -- cat /config/config.json
{
  "app_name": "devops-info-service",
  "environment": "production",
  "features": {
    "visits_counter": true,
    "prometheus_metrics": true
  }
}

$ kubectl exec devops-devops-info-service-5df8d55f7b-l7bgv -- printenv | grep -E "APP_ENV|LOG_LEVEL"
APP_ENV=production
LOG_LEVEL=info
```

## Persistent Volume

### PVC template

`templates/pvc.yaml`:

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
  {{- if .Values.persistence.storageClass }}
  storageClassName: {{ .Values.persistence.storageClass }}
  {{- end }}
```

`values.yaml` defaults:

```yaml
persistence:
  enabled: true
  size: 100Mi
  storageClass: ""
```

`storageClass: ""` uses the cluster default. On minikube this is the `standard` class backed by hostPath.

`ReadWriteOnce` is used because the visits file is written by the pod, and the deployment runs with one PVC shared across replicas on the same node.

### Volume mount

```yaml
volumes:
  - name: data-volume
    persistentVolumeClaim:
      claimName: <release>-devops-info-service-data
containers:
  - volumeMounts:
      - name: data-volume
        mountPath: /data
```

### Persistence test

Before pod deletion:

```
$ curl http://192.168.49.2:30082/visits
{"visits":3}

$ kubectl exec devops-devops-info-service-5df8d55f7b-862vt -- cat /data/visits
3
```

Delete pod:

```
$ kubectl delete pod devops-devops-info-service-5df8d55f7b-862vt
pod "devops-devops-info-service-5df8d55f7b-862vt" deleted
```

After new pod starts:

```
$ curl http://192.168.49.2:30082/visits
{"visits":3}
```

PVC status:

```
$ kubectl get configmap,pvc
NAME                                          DATA   AGE
configmap/devops-devops-info-service-config   1      5m43s
configmap/devops-devops-info-service-env      2      5m43s
NAME                                                    STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/devops-devops-info-service-data   Bound    pvc-1a718979-c50a-495a-9b81-c4fe527a608a   100Mi      RWO            standard       5m43s
```

## ConfigMap vs Secret

### When to use ConfigMap

Use ConfigMap for non-sensitive configuration. The values are stored in plaintext in etcd and visible to anyone with cluster read access.

### When to use Secret

Use Secret for sensitive data. Secrets are base64-encoded and can be restricted with role based access control and encrypted. Kubernetes also avoids logging Secret values.

### Key differences

- Secrets are base64-encoded; ConfigMaps are plain text.
- Different role based access control policies can restrict Secret access without affecting ConfigMaps.
- Helm has `secret` helpers and external tools (Vault, Sealed Secrets) that integrate with the Secret type, not ConfigMaps.
- Env vars from Secrets appear in `kubectl describe` as `<set to the key ...>`, while ConfigMap env vars show their values.
