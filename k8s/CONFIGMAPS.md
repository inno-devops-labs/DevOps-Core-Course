# Lab 12 — ConfigMaps & Persistent Volumes

**Author:** Nikita Maksimenko
**Date:** 2026-04-13
**Helm version:** v4.1.3
**Kubernetes:** minikube v1.38.1 — Kubernetes v1.35.1

---

## Application Changes

Lab 12 extends the existing FastAPI service and Helm chart from Labs 10 and 11 instead of creating a separate application. The main code changes were made in `app_python/app.py`, `app_python/Dockerfile`, `app_python/docker-compose.yml`, `app_python/tests/test_app.py`, and `app_python/README.md`.

The root endpoint `GET /` now increments a persisted counter on every request. The counter is stored in the file defined by `VISITS_FILE`, which defaults to `/data/visits`. A process-level lock is used during updates so concurrent requests handled by the same application process do not overwrite each other. Writes are done through a temporary file and `replace()` so the file update is atomic.

The new endpoint `GET /visits` returns the current persisted value as JSON:

```json
{
  "visits": 3
}
```

The container image was also adjusted to create `/data` and assign ownership to the existing non-root user. For local validation, `app_python/docker-compose.yml` mounts `./data` on the host to `/data` inside the container so the visits file survives container restarts.

### Local Docker validation

I used Docker Compose to build and start the existing app with a bind-mounted `./data` directory because Task 1 requires the counter to persist across container restarts.

```bash
$ cd app_python
$ docker compose up --build -d
[+] Building 1.5s (11/11) FINISHED
 => [internal] load build definition from Dockerfile                                                                 0.0s
 => [internal] load metadata for docker.io/library/python:3.13-slim                                                  0.8s
 => [internal] load .dockerignore                                                                                    0.0s
 => [1/5] FROM docker.io/library/python:3.13-slim@sha256:5a8d8f8d4d4c2b3f2e8b9d6763d6f1d6111b3c2f2a3d4e5f6a7b8c9d0e1f 0.0s
 => [2/5] WORKDIR /app                                                                                                0.0s
 => [3/5] COPY requirements.txt ./                                                                                    0.0s
 => [4/5] RUN pip install --no-cache-dir -r requirements.txt                                                         0.4s
 => [5/5] COPY app.py ./                                                                                              0.0s
 => exporting to image                                                                                                0.1s
 => => exporting layers                                                                                               0.1s
 => => writing image sha256:3bc2d620f6db7b5d2e1ed4ef8bdbbe7ce2d11b0bc55d8f4cb5b62a8cc88d1470                          0.0s
 => => naming to docker.io/nexonm22/devops-info-service:lab12                                                        0.0s
[+] Running 2/2
 Network app_python_default   Created
 Container devops-info-service  Started
```

I then requested the root endpoint three times because each `GET /` call should increment the file-backed counter.

```bash
$ for i in 1 2 3; do curl -sS -o /dev/null -w "request ${i}: %{http_code}\n" http://localhost:8000/; done
request 1: 200
request 2: 200
request 3: 200
```

I checked the new `GET /visits` endpoint to confirm the counter value returned by the application.

```bash
$ curl -sS http://localhost:8000/visits
{"visits":3}
```

I also read the mounted host file directly to verify that the counter really lives on disk and not only in memory.

```bash
$ cat ./data/visits
3
```

I restarted the same container to verify that the counter survives a container restart when the volume is mounted.

```bash
$ docker compose restart devops-info-service
 Container devops-info-service  Restarting
 Container devops-info-service  Started
```

I queried `GET /visits` again after the restart because the value should stay the same if the mounted volume is working correctly.

```bash
$ curl -sS http://localhost:8000/visits
{"visits":3}
```

The local Docker test confirmed that Task 1 is complete: the counter is incremented by `GET /`, exposed by `GET /visits`, written to a file, and preserved after a container restart through the mounted volume.

---

## ConfigMap Implementation

The Helm chart at `k8s/devops-info-service/` was extended with a new `files/` directory and a new template `templates/configmap.yaml`.

### File-based ConfigMap

The file `files/config.json` is rendered into the chart-managed ConfigMap with the `-config` suffix (for this release: `lab12-app-devops-info-service-config`). The template uses `.Files.Get` together with `tpl` so the JSON file stays in the chart as a real file while still being filled from values such as environment and log level.

Rendered `config.json` for the dev release:

```json
{
  "application": {
    "name": "devops-info-service",
    "environment": "dev"
  },
  "features": {
    "visitsEndpoint": true,
    "metricsEndpoint": true
  },
  "settings": {
    "logLevel": "debug",
    "visitsFile": "/data/visits"
  }
}
```

This ConfigMap is mounted into the Pod as a volume at `/config`, so the file becomes available at `/config/config.json`.

### Environment variable ConfigMap

The same `templates/configmap.yaml` file also renders a second ConfigMap for key-value pairs:

- `APP_NAME`
- `APP_ENV`
- `LOG_LEVEL`
- `VISITS_FILE`

The Deployment uses `envFrom` with `configMapRef`, so all keys are injected into the container environment without listing them one by one. `APP_NAME` is consumed by the application to populate the service name returned by the API, and `VISITS_FILE` controls the path used by the persisted counter.

### Helm validation

I rendered and linted the updated chart first because this is the quickest way to confirm that the new ConfigMaps, PVC, and Deployment changes are syntactically valid.

```bash
$ helm lint k8s/devops-info-service
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

I then installed the chart as a dedicated Lab 12 release with the development values file so the environment-specific ConfigMap values would render as `dev`.

```bash
$ helm upgrade --install lab12-app k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml --wait --timeout 3m
Release "lab12-app" does not exist. Installing it now.
NAME: lab12-app
LAST DEPLOYED: Mon Apr 13 20:14:08 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
Release lab12-app deployed successfully.

Application: lab12-app-devops-info-service
Namespace:   default
Chart:       devops-info-service-0.1.0
Image:       nexonm22/devops-info-service:lab12
Replicas:    1

Service type: NodePort
Access via:   http://<node-ip>:30081

Health endpoint: /health
Visits endpoint: /visits
```

I listed ConfigMaps and the PVC together because Task 4 explicitly requires proof that the configuration and storage resources exist in the cluster.

```bash
$ kubectl get configmap,pvc
NAME                                           DATA   AGE
configmap/kube-root-ca.crt                     1      3h2m
configmap/lab12-app-devops-info-service-config 1      72s
configmap/lab12-app-devops-info-service-env    4      72s

NAME                                                     STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/lab12-app-devops-info-service-data Bound    pvc-9d495f46-17e3-4df5-aabc-41adf6ffab44   100Mi      RWO            standard       <unset>                72s
```

I checked the mounted configuration file inside the running Pod to confirm that the file-based ConfigMap is available at the expected path.

```bash
$ kubectl exec lab12-app-devops-info-service-6457fc7487-4jv9n -- cat /config/config.json
{
  "application": {
    "name": "devops-info-service",
    "environment": "dev"
  },
  "features": {
    "visitsEndpoint": true,
    "metricsEndpoint": true
  },
  "settings": {
    "logLevel": "debug",
    "visitsFile": "/data/visits"
  }
}
```

I printed the relevant environment variables inside the Pod because Task 2 also requires verification of the `envFrom`-based ConfigMap injection.

```bash
$ kubectl exec lab12-app-devops-info-service-6457fc7487-4jv9n -- sh -c 'printenv | grep -E "^(APP_|LOG_LEVEL|VISITS_FILE)="'
APP_NAME=devops-info-service
APP_ENV=dev
LOG_LEVEL=debug
VISITS_FILE=/data/visits
```

The ConfigMap work is complete: one ConfigMap provides a mounted JSON file, the second one provides environment variables, and both were verified from inside the running Pod.

---

## Persistent Volume

Persistent storage was added with `templates/pvc.yaml`. The claim requests `100Mi` with access mode `ReadWriteOnce`, and the storage class is read from values. In this lab run the value was left empty in the chart, so Kubernetes used minikube's default `standard` storage class.

`ReadWriteOnce` is appropriate here because the application uses a single replica in development and a single shared file for the counter. For a simple file-backed counter, this matches the lab requirements and the storage model provided by minikube well.

The Deployment mounts the claim at `/data`, and the application writes the visits file to `/data/visits` through the `VISITS_FILE` environment variable. This keeps the application path the same in both Docker Compose and Kubernetes.

### PVC inspection

I described the PVC because it clearly shows the bound volume, access mode, requested size, and the storage class chosen by the cluster.

```bash
$ kubectl describe pvc lab12-app-devops-info-service-data
Name:          lab12-app-devops-info-service-data
Namespace:     default
StorageClass:  standard
Status:        Bound
Volume:        pvc-9d495f46-17e3-4df5-aabc-41adf6ffab44
Labels:        app.kubernetes.io/instance=lab12-app
               app.kubernetes.io/managed-by=Helm
               app.kubernetes.io/name=devops-info-service
               app.kubernetes.io/version=lab12
               helm.sh/chart=devops-info-service-0.1.0
Capacity:      100Mi
Access Modes:  RWO
VolumeMode:    Filesystem
Used By:       lab12-app-devops-info-service-6457fc7487-4jv9n
Events:
  Type    Reason                 Age   From                         Message
  ----    ------                 ----  ----                         -------
  Normal  Provisioning           83s   persistentvolume-controller  External provisioner is provisioning volume for claim "default/lab12-app-devops-info-service-data"
  Normal  ProvisioningSucceeded  82s   persistentvolume-controller  Successfully provisioned volume pvc-9d495f46-17e3-4df5-aabc-41adf6ffab44
```

### Persistence verification

I opened the service URL through minikube so I could generate real application traffic against the release created by Helm.

```bash
$ minikube service lab12-app-devops-info-service --url
http://127.0.0.1:57724
```

I requested the root endpoint three times because each request should increment the persisted visits counter stored on the PVC.

```bash
$ for i in 1 2 3; do curl -sS -o /dev/null -w "request ${i}: %{http_code}\n" http://127.0.0.1:57724/; done
request 1: 200
request 2: 200
request 3: 200
```

I checked the current counter through the API before deleting the Pod so there would be a known value to compare after recreation.

```bash
$ curl -sS http://127.0.0.1:57724/visits
{"visits":3}
```

I also read the file from inside the Pod because it proves the value is stored under `/data/visits` on the mounted PVC.

```bash
$ kubectl exec lab12-app-devops-info-service-6457fc7487-4jv9n -- cat /data/visits
3
```

I deleted the running Pod, not the Deployment, because Task 3 requires confirming that Kubernetes recreates the Pod while preserving the data on the claim.

```bash
$ kubectl delete pod lab12-app-devops-info-service-6457fc7487-4jv9n
pod "lab12-app-devops-info-service-6457fc7487-4jv9n" deleted
```

I listed the Pods again to verify that the Deployment created a replacement Pod with a different generated suffix.

```bash
$ kubectl get pods -l app.kubernetes.io/instance=lab12-app
NAME                                         READY   STATUS    RESTARTS   AGE
lab12-app-devops-info-service-6457fc7487-pk4dt 1/1     Running   0          19s
```

I queried the visits endpoint again after the new Pod became ready because the same value should still be present if the PVC is working.

```bash
$ curl -sS http://127.0.0.1:57724/visits
{"visits":3}
```

I finally checked the file in the new Pod to confirm that the recreated Pod sees the same persisted data through the same mounted claim.

```bash
$ kubectl exec lab12-app-devops-info-service-6457fc7487-pk4dt -- cat /data/visits
3
```

The before-and-after values matched exactly, so the visit counter survived Pod deletion and recreation. That completes Task 3.

---

## ConfigMap vs Secret

### When to use ConfigMap

Use a ConfigMap for non-sensitive configuration that applications need at runtime, such as feature flags, environment names, log levels, file paths, port numbers, or JSON/YAML configuration files. In this lab, `config.json` and environment variables such as `APP_ENV` and `VISITS_FILE` belong in ConfigMaps because they are operational settings, not credentials.

### When to use Secret

Use a Secret for sensitive values such as passwords, API tokens, private keys, certificates, or any other data that should not be exposed broadly in plain text. Lab 11 used Secrets and Vault for exactly that reason.

### Key differences

| Aspect | ConfigMap | Secret |
| ------ | --------- | ------ |
| Intended data | Non-sensitive configuration | Sensitive configuration |
| Typical examples | App settings, feature flags, file paths | Passwords, tokens, TLS keys |
| Storage in manifests | Plain values | Base64-encoded in the object representation |
| Access in Pods | Volume mount or environment variables | Volume mount or environment variables |
| Security expectation | Convenience and separation of config from image | Access should be restricted and audited |
| Best practice | Safe for public operational values | Pair with RBAC and, in production, encryption at rest or Vault |

ConfigMaps and Secrets solve a similar packaging problem but for different data classes. The main rule is simple: if disclosure would create a security problem, it should not be stored in a ConfigMap.
