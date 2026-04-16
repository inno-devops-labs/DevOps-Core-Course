# Lab 12 - ConfigMaps & Persistent Volumes

## 1. Application Changes

### Visit counter implementation

The Flask service now persists a visit counter in a file instead of keeping it only in memory.

Implemented changes:

- `GET /` increments the counter and writes the new value to the visits file
- `GET /visits` returns the current persisted counter without incrementing it
- the counter path is configurable with `VISITS_FILE`
- the app loads non-secret JSON configuration from `APP_CONFIG_PATH`
- file access uses an exclusive file lock plus `fsync()` so concurrent writes from the same mounted volume do not corrupt the counter

Relevant application files:

- `app_python/src/app.py`
- `app_python/tests/test_app.py`
- `app_python/docker-compose.yml`
- `app_python/config/config.json`
- `app_python/README.md`

### New endpoint

`GET /visits` response shape:

```json
{"file":"/data/visits","visits":2}
```

### Local Docker testing evidence

Compose file:

- bind-mounts `./data` to `/data` for visit persistence
- bind-mounts `./config` to `/config` for a real local JSON config file

Commands used:

```bash
docker compose up --build -d
rm -f data/visits
curl -s http://localhost:5000/visits
curl -s http://localhost:5000/
curl -s http://localhost:5000/
cat ./data/visits
docker compose restart
curl -s http://localhost:5000/visits
```

Observed outputs:

```text
{"file":"/data/visits","visits":0}
```

```text
... "visits":{"count":1,"file":"/data/visits"} ...
... "visits":{"count":2,"file":"/data/visits"} ...
```

```text
2
```

```text
{"file":"/data/visits","visits":2}
```

That confirms the counter survives a container restart.

## 2. ConfigMap Implementation

### Helm chart structure

The chart now includes:

```text
k8s/devops-info-service/
├── files/
│   └── config.json
└── templates/
    ├── configmap.yaml
    ├── deployment.yaml
    └── pvc.yaml
```

### File-backed ConfigMap

`templates/configmap.yaml` renders a ConfigMap named `<release>-config` and loads `files/config.json`.

Rendered `config.json` inside the pod:

```bash
kubectl exec lab12-devops-devops-info-service-c88866b7b-h5dsq -- cat /config/config.json
```

```json
{
  "application": {
    "name": "devops-info-service",
    "environment": "dev",
    "description": "DevOps course info service",
    "version": "1.0.0"
  },
  "featureFlags": {
    "visitsCounter": true,
    "metricsEndpoint": true,
    "showRuntimeDetails": true
  },
  "settings": {
    "logLevel": "DEBUG",
    "visitsFile": "/data/visits"
  }
}
```

Mount strategy:

- ConfigMap volume name: `config-volume`
- mount path: `/config`
- target file used by the app: `/config/config.json`
- `subPath` is intentionally not used so ConfigMap updates can propagate to the mounted file

### Environment-variable ConfigMap

The second ConfigMap (`<release>-env`) is consumed with `envFrom`.

Verification:

```bash
kubectl exec lab12-devops-devops-info-service-c88866b7b-v7lzk -- \
  sh -c 'printenv | grep -E "^(APP_|LOG_LEVEL|FEATURE_)" | sort'
```

```text
APP_CONFIG_PATH=/config/config.json
APP_ENV=dev
APP_NAME=devops-info-service
APP_PASSWORD=replace-me-in-dev
APP_USERNAME=dev-user
FEATURE_RUNTIME_DETAILS=true
FEATURE_VISITS=true
LOG_LEVEL=DEBUG
```

The `APP_ENV`, `APP_NAME`, `LOG_LEVEL`, and `FEATURE_*` variables come from the ConfigMap. `APP_USERNAME` and `APP_PASSWORD` come from the existing Secret from Lab 11.

### Resource snapshot

```bash
kubectl get pods,svc,configmap,pvc -l app.kubernetes.io/instance=lab12-devops
```

```text
NAME                                                   READY   STATUS    RESTARTS   AGE
pod/lab12-devops-devops-info-service-c88866b7b-h5dsq   1/1     Running   0          46s

NAME                                       TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/lab12-devops-devops-info-service   NodePort   10.100.95.214   <none>        80:30082/TCP   23s

NAME                                                DATA   AGE
configmap/lab12-devops-devops-info-service-config   1      46s
configmap/lab12-devops-devops-info-service-env      5      46s

NAME                                                          STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/lab12-devops-devops-info-service-data   Bound    pvc-82a5758c-1e4a-46a4-9036-6cf5ba37a89f   100Mi      RWO            standard       <unset>                 46s
```

## 3. Persistent Volume

### PVC configuration

The chart creates `templates/pvc.yaml` when `persistence.enabled=true`.

Configured values:

- storage size: `100Mi` in `values-dev.yaml`
- access mode: `ReadWriteOnce`
- storage class: empty in values, so Minikube uses the default `standard` class
- mount path in the pod: `/data`

Minikube storage class in this cluster:

```bash
kubectl get storageclass
```

```text
NAME                 PROVISIONER                RECLAIMPOLICY   VOLUMEBINDINGMODE   ALLOWVOLUMEEXPANSION   AGE
standard (default)   k8s.io/minikube-hostpath   Delete          Immediate           false                  13d
```

### Persistence verification

Before deleting the pod:

```bash
curl -s http://127.0.0.1:38385/visits
kubectl exec lab12-devops-devops-info-service-c88866b7b-h5dsq -- cat /data/visits
```

```text
{"file":"/data/visits","visits":2}
```

```text
2
```

Delete the pod:

```bash
kubectl delete pod lab12-devops-devops-info-service-c88866b7b-h5dsq
kubectl rollout status deployment/lab12-devops-devops-info-service --timeout=180s
```

Observed replacement pod:

```bash
kubectl get pods -l app.kubernetes.io/instance=lab12-devops -o wide
```

```text
NAME                                               READY   STATUS        RESTARTS   AGE   IP            NODE       NOMINATED NODE   READINESS GATES
lab12-devops-devops-info-service-c88866b7b-h5dsq   1/1     Terminating   0          86s   10.244.0.49   minikube   <none>           <none>
lab12-devops-devops-info-service-c88866b7b-v7lzk   0/1     Running       0          5s    10.244.0.50   minikube   <none>           <none>
```

After the new pod started:

```bash
kubectl wait --for=condition=Ready pod/lab12-devops-devops-info-service-c88866b7b-v7lzk --timeout=180s
curl -s http://127.0.0.1:38385/visits
kubectl exec lab12-devops-devops-info-service-c88866b7b-v7lzk -- cat /data/visits
```

```text
{"file":"/data/visits","visits":2}
```

```text
2
```

The counter value survived pod deletion because it was stored on the PVC-backed `/data` mount rather than inside the container filesystem.

## 4. ConfigMap vs Secret

### When to use a ConfigMap

Use ConfigMaps for non-sensitive runtime data:

- application name
- environment labels
- feature flags
- log levels
- JSON/YAML configuration files

### When to use a Secret

Use Secrets for confidential values:

- usernames and passwords
- tokens
- API keys
- certificates

### Key differences

- ConfigMaps are for plain configuration, Secrets are for sensitive data
- ConfigMaps are readable in plain text; Secrets are still only base64-encoded unless encryption at rest is enabled
- both can be mounted as files or injected as environment variables

In this lab:

- ConfigMap supplies `config.json`, `APP_ENV`, `APP_NAME`, `LOG_LEVEL`, and `FEATURE_*`
- Secret still supplies `APP_USERNAME` and `APP_PASSWORD`

## 5. Bonus - ConfigMap Hot Reload

### Default update behavior

I tested a live ConfigMap update by changing the mounted file content in the cluster and polling until the new text appeared inside the running pod.

Command result:

```text
configmap/lab12-devops-devops-info-service-config configured
hot_reload_seconds=42
```

That means the mounted file updated in about 42 seconds in this Minikube environment. The app reads the JSON file on each request, so the updated description became visible without restarting the container:

```bash
curl -s http://127.0.0.1:38385/ | rg -o 'ConfigMap hot reload successful|"count":[0-9]+'
```

```text
ConfigMap hot reload successful
"count":3
```

The pod itself was not restarted during that check:

```bash
kubectl get pod lab12-devops-devops-info-service-c88866b7b-v7lzk -o jsonpath='{.metadata.name} {.status.containerStatuses[0].restartCount}'
```

```text
lab12-devops-devops-info-service-c88866b7b-v7lzk 0
```

### Why `subPath` was avoided

`subPath` mounts a copied file view instead of the projected ConfigMap directory symlink structure. Because of that, a file mounted via `subPath` does not receive ConfigMap updates automatically. For hot-reload behavior, mounting the whole directory at `/config` is the correct pattern.

### Helm restart pattern

The deployment also includes:

- `checksum/config-file`
- `checksum/config-env`

Those pod-template annotations are derived from the rendered config content. When the chart-managed ConfigMap content changes during `helm upgrade`, the checksums change too, which forces Kubernetes to roll the Deployment and restart the pods in a controlled way.
