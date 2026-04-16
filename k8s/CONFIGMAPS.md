# Lab 12 - ConfigMaps & Persistent Volumes

## 1. Application Changes

### Visits counter implementation

The Python app now persists visits count in a file path from `VISITS_FILE` (default: `/data/visits`):

- `GET /` increments the counter and stores it in the file.
- `GET /visits` returns the current persisted value.
- Access is synchronized with a thread lock to avoid race conditions during concurrent requests.

### Local Docker Compose persistence test

`app_python/docker-compose.yml` mounts host directory `./data` to container path `/data`, and sets:

- `VISITS_FILE=/data/visits`

Evidence from local run:

```text
before_restart={"visits":2}
after_restart={"visits":2}
```

This confirms counter data survives container restart.

## 2. ConfigMap Implementation

### Templates added

- `k8s/devops-info/templates/configmap.yaml`
  - `*-config-file` ConfigMap mounts `files/config.json`
  - `*-config-env` ConfigMap provides environment variables
- `k8s/devops-info/files/config.json`
  - application metadata, environment, feature flags, settings

### ConfigMap mounted as file

Deployment mount:

- volume `config-volume` from ConfigMap `devops-info-dev-config-file`
- mount path `/config/config.json` using `subPath: config.json`

Verification:

```text
$ kubectl exec <pod> -- cat /config/config.json
{
  "application": {
    "name": "devops-info-service",
    "environment": "dev"
  },
  "features": {
    "visitsCounter": true
  },
  "settings": {
    "responseFormat": "json",
    "collectSystemInfo": true
  }
}
```

### ConfigMap as environment variables

Deployment uses:

- `envFrom.configMapRef.name: devops-info-dev-config-env`

Verification:

```text
LOG_LEVEL=info
APP_NAME=devops-info-service
FEATURE_VISITS_COUNTER=true
APP_CONFIG_ENVIRONMENT=dev
APP_ENV=dev
```

## 3. Persistent Volume

### PVC configuration

Template: `k8s/devops-info/templates/pvc.yaml`

- `accessModes: [ReadWriteOnce]`
- `resources.requests.storage: 100Mi`
- configurable storage class via `values.yaml` (`persistence.storageClass`)

Deployment mount:

- PVC `devops-info-dev-data` mounted at `/data`
- app writes visits file to `/data/visits`

PVC status:

```text
$ kubectl get configmap,pvc
NAME                                    DATA   AGE
configmap/devops-info-dev-config-env    5      43s
configmap/devops-info-dev-config-file   1      43s
configmap/kube-root-ca.crt              1      62s

NAME                                         STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS
persistentvolumeclaim/devops-info-dev-data   Bound    pvc-7db2a951-a78b-4723-8c57-7702f5ce4026   100Mi      RWO            standard
```

### Persistence test evidence

1. Targeted one pod, made requests, verified visits count:

```text
target_pod=devops-info-dev-74748b54f7-m7rwp
target_pod_visits_api={"visits":4}
target_pod_visits_file_before_delete=4
```

2. Deleted pod and waited for replacement:

```text
pod "devops-info-dev-74748b54f7-m7rwp" deleted from default namespace
replacement_pod=devops-info-dev-74748b54f7-7rh6s
```

3. Verified counter persisted in replacement pod:

```text
target_volume_visits_after_delete=4
```

This confirms data survives pod recreation.

## 4. Deployment and Cluster Evidence

Cluster was brought up from Lab 9 profile:

```text
$ minikube start -p lab09 --driver=docker --kubernetes-version=v1.35.1
Done! kubectl is now configured to use "lab09" cluster
```

Deployed with Helm:

```text
$ helm upgrade --install devops-info-dev k8s/devops-info --set image.tag=lab12 --wait --timeout 240s
STATUS: deployed
REVISION: 1
```

Current resources:

```text
$ kubectl get pods,svc -o wide
NAME                                   READY   STATUS    RESTARTS   AGE
pod/devops-info-dev-74748b54f7-7rh6s   1/1     Running   0          84s
pod/devops-info-dev-74748b54f7-wxksg   1/1     Running   0          2m35s
pod/devops-info-dev-74748b54f7-zg6ws   1/1     Running   0          3m41s

NAME                      TYPE       CLUSTER-IP      PORT(S)
service/devops-info-dev   NodePort   10.107.241.33   80:30596/TCP
```

## 5. ConfigMap vs Secret

- Use **ConfigMap** for non-sensitive configuration (feature flags, log level, app mode, JSON config files).
- Use **Secret** for sensitive values (passwords, tokens, API keys, certificates).

Key differences:

- **Encoding and intent**: Secret values are base64-encoded and treated as sensitive; ConfigMaps are plain-text config.
- **Access control**: Secrets should have stricter RBAC and handling policies.
- **Operational practice**: ConfigMaps are easy to inspect/debug; Secrets should be rotated, audited, and minimized in plaintext exposure.

