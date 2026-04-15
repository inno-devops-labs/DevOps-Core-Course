# ConfigMaps and Persistent Volumes

## Application Changes

The Python application now stores a visit counter in a file-backed `VisitCounter` helper.

- Root endpoint `/` increments the counter and returns the current value.
- New endpoint `/visits` returns the current counter without incrementing it.
- The counter file path is configurable with `VISITS_FILE` and defaults to `/data/visits`.
- Counter writes are protected by a lock and saved with an atomic `os.replace(...)`.

### Local Docker verification

The app now includes `app_python/docker-compose.yml` with a bind mount:

```yaml
volumes:
  - ./data:/data
```

Commands used:

```bash
docker compose up -d --build
curl -s http://127.0.0.1:8000/
cat data/visits
docker compose down
docker compose up -d
curl -s http://127.0.0.1:8000/visits
```

Observed results:

```text
{"visits":1,"visits_file":"/data/visits"}
```

```text
1
```

The counter file remained on the host after `docker compose down`, and after `docker compose up -d` the `/visits` endpoint still returned `1`.

## ConfigMap Implementation

### Chart files

- File-backed config template: `k8s/python-app/files/config.json`
- ConfigMap templates: `k8s/python-app/templates/configmap.yaml`
- Deployment mount/env wiring: `k8s/python-app/templates/deployment.yaml`

Two ConfigMaps are created:

1. `lab12-python-app-config`
2. `lab12-python-app-env`

`lab12-python-app-config` mounts `config.json` into `/config/config.json`.

`lab12-python-app-env` injects:

- `APP_ENV`
- `LOG_LEVEL`
- `FEATURE_VISITS_ENABLED`
- `CONFIG_PATH`

### Mounted file inside the pod

Command:

```bash
kubectl exec lab12-python-app-86c7545d8-t8p7t -- cat /config/config.json
```

Output:

```json
{
  "application": {
    "name": "devops-info-service",
    "environment": "development",
    "visitsFile": "/data/visits"
  },
  "features": {
    "visitsEndpoint": true,
    "metricsEndpoint": true
  },
  "settings": {
    "logLevel": "DEBUG",
    "port": "8000"
  }
}
```

### Environment variables inside the pod

Command:

```bash
kubectl exec lab12-python-app-86c7545d8-ht979 -- sh -c "env | sort | grep -E 'APP_|LOG_LEVEL|CONFIG_PATH|FEATURE_'"
```

Output:

```text
APP_ENV=development
CONFIG_PATH=/config/config.json
FEATURE_VISITS_ENABLED=true
LOG_LEVEL=DEBUG
```

### Render verification

The chart renders both ConfigMaps and mounts them into the deployment:

```bash
helm template lab12 ./k8s/python-app -f ./k8s/python-app/values-dev.yaml
```

Relevant rendered snippets:

```yaml
data:
  config.json: |-
    {
      "application": {
        "name": "devops-info-service",
        "environment": "development",
        "visitsFile": "/data/visits"
      }
    }
```

```yaml
envFrom:
  - configMapRef:
      name: lab12-python-app-env
```

## Persistent Volume

### PVC configuration

PVC template: `k8s/python-app/templates/pvc.yaml`

Values used:

```yaml
persistence:
  enabled: true
  mountPath: /data
  accessMode: ReadWriteOnce
  size: 100Mi
  storageClass: ""
```

- Access mode: `ReadWriteOnce`
- Storage size: `100Mi`
- Storage class: default Minikube `standard`

### Cluster resources

Command:

```bash
kubectl get configmap,pvc
```

Output:

```text
NAME                                DATA   AGE
configmap/kube-root-ca.crt          1      2m21s
configmap/lab12-python-app-config   1      21s
configmap/lab12-python-app-env      4      21s

NAME                                          STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/lab12-python-app-data   Bound    pvc-8eb4c18e-0ae3-4ae7-a4a0-c41523fa1786   100Mi      RWO            standard       21s
```

### Persistence test

Initial requests:

```bash
curl -s http://127.0.0.1:18080/
curl -s http://127.0.0.1:18080/
curl -s http://127.0.0.1:18080/
kubectl exec lab12-python-app-86c7545d8-t8p7t -- cat /data/visits
```

Counter before pod deletion:

```text
3
```

Deletion command:

```bash
kubectl delete pod lab12-python-app-86c7545d8-t8p7t
kubectl rollout status deployment/lab12-python-app --timeout=180s
```

New pod:

```text
lab12-python-app-86c7545d8-ht979
```

Counter after the new pod started:

```bash
kubectl exec lab12-python-app-86c7545d8-ht979 -- cat /data/visits
kubectl exec lab12-python-app-86c7545d8-ht979 -- python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/visits').read().decode())"
```

Outputs:

```text
3
```

```json
{"visits":3,"visits_file":"/data/visits"}
```

This confirms the visits counter survived pod replacement because the file lives on the PVC rather than in the container filesystem.

## ConfigMap vs Secret

### Use ConfigMap when

- The data is not sensitive.
- You want to externalize plain configuration files.
- You need key-value application settings such as environment name or log level.

### Use Secret when

- The data is sensitive.
- You are storing credentials, API keys, tokens, or passwords.
- You want Kubernetes to treat the values as secret material rather than normal config.

### Key differences

- ConfigMaps are for non-confidential configuration.
- Secrets are for sensitive data and are base64-encoded in manifests.
- ConfigMaps are commonly mounted as config files or env vars.
- Secrets are commonly mounted the same way, but with stricter handling and access expectations.
