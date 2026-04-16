# Lab 12: ConfigMaps and Persistent Volumes

## 1. Application Changes

Updated application: [app.py](C:\Users\sevan\Documents\GitHub\DevOps-Core-Course\Lab-1\app_python\app.py)

- Added file-based visits counter.
- `GET /` increments the counter and returns the current value.
- Added `GET /visits` to read the current counter without incrementing it.
- Counter is stored in a file defined by `VISITS_FILE_PATH`.
- Writes are protected with a process-local `Lock` and use atomic `os.replace(...)`.
- Application also reads optional JSON config from `APP_CONFIG_PATH`.

Local Docker setup: [docker-compose.yml](C:\Users\sevan\Documents\GitHub\DevOps-Core-Course\Lab-1\app_python\docker-compose.yml)

Local verification commands:

```bash
docker compose up --build
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/visits
cat ./data/visits
docker compose down
docker compose up
curl http://127.0.0.1:5000/visits
```

The local Docker Compose flow was executed to verify that the application can create and reuse the visits file through a mounted host directory. The main evidence collected for the lab report is shown in the Kubernetes sections below, where the same persistence behavior is demonstrated with a PVC.

## 2. ConfigMap Implementation

Helm config artifacts:

- File config source: [config.json](C:\Users\sevan\Documents\GitHub\DevOps-Core-Course\k8s\devops-info-service\files\config.json)
- ConfigMap templates: [configmap.yaml](C:\Users\sevan\Documents\GitHub\DevOps-Core-Course\k8s\devops-info-service\templates\configmap.yaml)
- Deployment mount/injection: [deployment.yaml](C:\Users\sevan\Documents\GitHub\DevOps-Core-Course\k8s\devops-info-service\templates\deployment.yaml)

Implemented structure:

1. File-backed ConfigMap
   Uses `tpl (.Files.Get "files/config.json")` so the file stays in chart `files/` while values such as environment and log level are rendered from Helm values.

2. Environment ConfigMap
   Injected with `envFrom.configMapRef` and provides:
   - `APP_ENV`
   - `LOG_LEVEL`
   - `APP_CONFIG_PATH`
   - `VISITS_FILE_PATH`

3. File mount
   The file ConfigMap is mounted as a full directory at `/config`.
   The application reads `/config/config.json`.

4. Why directory mount instead of `subPath`
   Full directory mounts receive ConfigMap updates.
   `subPath` mounts do not auto-refresh because the mounted file becomes a bind-mounted copy.

Verification commands:

```bash
kubectl get configmap
kubectl exec <pod> -- cat /config/config.json
kubectl exec <pod> -- printenv | grep -E 'APP_|LOG_LEVEL|VISITS'
```

Observed outputs:

```text
PS> kubectl get configmap,pvc
NAME                                                     DATA   AGE
configmap/devops-info-lab12-devops-info-service-config   1      10s
configmap/devops-info-lab12-devops-info-service-env      4      10s
configmap/kube-root-ca.crt                               1      6d23h

NAME                                                               STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/devops-info-lab12-devops-info-service-data   Bound    pvc-97dd1c5f-75b8-4ba3-9eca-7ec7fd1f4aff   100Mi      RWO            standard       <unset>                 10s
```

The mounted file content is defined by the chart file [config.json](C:\Users\sevan\Documents\GitHub\DevOps-Core-Course\k8s\devops-info-service\files\config.json) and rendered with `values-dev.yaml`:

```text
PS> kubectl exec pod/devops-info-lab12-devops-info-service-6bf9597c5-92crr -- cat /config/config.json
{
  "applicationName": "devops-info-service",
  "environment": "dev",
  "featureFlags": {
    "visitsCounter": true,
    "swaggerEnabled": true,
    "configFileMounted": true
  },
  "settings": {
    "logLevel": "debug",
    "configSource": "helm-configmap-reloaded",
    "persistenceEnabled": true
  }
}
```

```text
PS> kubectl exec devops-info-lab12-devops-info-service-6d4cb74585-mjwrc -- printenv | findstr APP_
APP_CONFIG_PATH=/config/config.json
APP_ENV=dev

PS> kubectl exec devops-info-lab12-devops-info-service-6d4cb74585-mjwrc -- printenv | findstr LOG_LEVEL
LOG_LEVEL=debug

PS> kubectl exec devops-info-lab12-devops-info-service-6d4cb74585-mjwrc -- printenv | findstr VISITS_FILE_PATH
VISITS_FILE_PATH=/data/visits
```

## 3. Persistent Volume

PVC template: [pvc.yaml](C:\Users\sevan\Documents\GitHub\DevOps-Core-Course\k8s\devops-info-service\templates\pvc.yaml)

Values: [values.yaml](C:\Users\sevan\Documents\GitHub\DevOps-Core-Course\k8s\devops-info-service\values.yaml)

Implemented configuration:

- `accessMode`: `ReadWriteOnce`
- default size: `100Mi`
- `storageClass` configurable through values
- PVC mounted into the container at `/data`
- counter file path inside pod: `/data/visits`

Persistence validation procedure:

```bash
kubectl get pods
curl http://127.0.0.1:8080/
curl http://127.0.0.1:8080/
curl http://127.0.0.1:8080/visits
kubectl exec <pod> -- cat /data/visits
kubectl delete pod <pod-name>
kubectl get pods -w
curl http://127.0.0.1:8080/visits
kubectl exec <new-pod> -- cat /data/visits
```

Observed persistence evidence:

```text
PS> curl http://127.0.0.1:8080/visits

StatusCode        : 200
StatusDescription : OK
Content           : {"count":0,"storage_path":"/data/visits"}
```

After incrementing the counter through the application, the value stored on the mounted PVC became:

```text
PS> kubectl exec $pod -- cat /data/visits
2
```

The pod was deleted:

```text
PS> kubectl delete pod $pod
pod "devops-info-lab12-devops-info-service-6c89bd94dd-d5g5v" deleted from default namespace
```

The Deployment created a replacement pod:

```text
PS> kubectl get pods -w
NAME                                                     READY   STATUS    RESTARTS   AGE
devops-info-lab12-devops-info-service-6c89bd94dd-nmtzd   1/1     Running   0          31s
```

The counter value in the new pod remained unchanged:

```text
PS> kubectl exec $pod -- cat /data/visits
2
```

The `port-forward` tunnel was attached to the deleted pod, so the HTTP check had to be restarted after pod recreation. Persistence itself was confirmed directly from the mounted file on the new pod.

After restarting `kubectl port-forward`, the HTTP endpoint returned the same persisted counter value:

```text
PS> curl http://127.0.0.1:8080/visits

StatusCode        : 200
StatusDescription : OK
Content           : {"count":2,"storage_path":"/data/visits"}
```

Storage discussion:

- `ReadWriteOnce` is appropriate because this deployment writes one shared counter file from a single mounted volume per pod.
- With the default Minikube storage class, a PVC is dynamically provisioned automatically.
- If a custom class is needed, set `persistence.storageClass`.

## 4. ConfigMap vs Secret

Use ConfigMap when:

- data is non-sensitive
- configuration should be human-readable
- application settings are safe to expose as environment variables or mounted files

Use Secret when:

- data is sensitive
- credentials, tokens, API keys, passwords or certificates are involved
- you want tighter RBAC handling and base64-backed Kubernetes Secret objects

Key differences:

| Aspect | ConfigMap | Secret |
|---|---|---|
| Intended data | Non-sensitive config | Sensitive data |
| Typical examples | Feature flags, env name, log level | Passwords, tokens, certificates |
| Encoding | Plain text in manifest/API | Base64-encoded values |
| Handling | Easy to inspect and mount | Requires stricter access control |

## 5. Bonus: Hot Reload and Restart Strategy

Implemented restart trigger:

- [deployment.yaml](C:\Users\sevan\Documents\GitHub\DevOps-Core-Course\k8s\devops-info-service\templates\deployment.yaml) includes:

```yaml
checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

Why this pattern:

- A ConfigMap update alone does not guarantee the application will reload config immediately.
- Mounted ConfigMaps are updated by kubelet asynchronously, usually with delay up to about 1-2 minutes depending on sync period and cache TTL.
- The checksum annotation forces a Deployment rollout on `helm upgrade`, which is deterministic and operationally simple.

`subPath` limitation:

- `subPath` mounts should be avoided for hot-reload scenarios.
- They do not receive updated ConfigMap content after the pod starts.

Chosen reload approach:

- Pod restart on ConfigMap checksum change.
- This is simpler and more predictable than implementing an in-app file watcher for this lab.

Observed rollout evidence after changing `files/config.json` and running `helm upgrade --reuse-values`:

```text
PS> helm upgrade devops-info-lab12 k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml --reuse-values
Release "devops-info-lab12" has been upgraded. Happy Helming!
REVISION: 3

PS> kubectl rollout status deployment/devops-info-lab12-devops-info-service --timeout=120s
deployment "devops-info-lab12-devops-info-service" successfully rolled out

PS> kubectl get pods -o name | findstr devops-info-lab12
pod/devops-info-lab12-devops-info-service-6bf9597c5-92crr
```

Updated config inside the new pod:

```text
PS> kubectl exec pod/devops-info-lab12-devops-info-service-6bf9597c5-92crr -- cat /config/config.json
{
  "applicationName": "devops-info-service",
  "environment": "dev",
  "featureFlags": {
    "visitsCounter": true,
    "swaggerEnabled": true,
    "configFileMounted": true
  },
  "settings": {
    "logLevel": "debug",
    "configSource": "helm-configmap-reloaded",
    "persistenceEnabled": true
  }
}
```
