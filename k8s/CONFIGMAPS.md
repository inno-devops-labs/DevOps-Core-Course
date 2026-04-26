# Lab 12: ConfigMaps and Persistent Volumes

## Application Changes

The Python Flask service now keeps a persistent visit counter for requests to
`GET /`. The counter is stored as plain text in `VISITS_FILE`, which defaults to
`/data/visits`. Writes use a process-local lock and atomic `os.replace()` to avoid
partial file updates.

New endpoints:

- `GET /visits` returns the current counter without incrementing it.
- `GET /config` returns the current JSON configuration loaded from `CONFIG_FILE`.

Local Docker Compose mounts:

- `./data:/data` for the visit counter.
- `./config:/config:ro` for local file-based configuration.

Local Docker verification:

```text
$ docker compose -f app_python/docker-compose.yml up --build -d
Container devops-info-python-lab12  Started

$ curl -sS http://127.0.0.1:8000/
... "visits":1 ...

$ curl -sS http://127.0.0.1:8000/
... "visits":2 ...

$ cat app_python/data/visits
2

$ docker compose -f app_python/docker-compose.yml restart devops-info-python
Container devops-info-python-lab12  Started

$ curl -sS http://127.0.0.1:8000/visits
{"file":"/data/visits","visits":2}
```

Local config reload verification:

```text
$ curl -sS http://127.0.0.1:8000/config
{"config":{"settings":{"message":"Hot reload verification", ...}}}

$ curl -sS http://127.0.0.1:8000/config
{"config":{"settings":{"message":"Local Docker Compose configuration", ...}}}
```

Note: on this machine `localhost:8000` was intercepted by a local proxy and
returned `503`; `127.0.0.1:8000` reached the container directly.

## ConfigMap Implementation

The Helm chart stores file configuration in
`k8s/python-app/files/config.json`:

```json
{
  "applicationName": "devops-info-service",
  "environment": "dev",
  "features": {
    "visitsCounter": true,
    "configHotReload": true,
    "structuredLogging": true,
    "prometheusMetrics": true
  },
  "settings": {
    "owner": "ellilin",
    "course": "DevOps Engineering",
    "lab": "lab12"
  }
}
```

`templates/configmap.yaml` creates two ConfigMaps:

- `python-app-devops-info-python-config` loads `files/config.json` with
  `.Files.Get` and mounts it as `/config/config.json`.
- `python-app-devops-info-python-env` exposes environment values such as
  `APP_ENV`, `LOG_LEVEL`, `FEATURE_VISITS_COUNTER`, and
  `FEATURE_CONFIG_HOT_RELOAD`.

The deployment consumes the env ConfigMap with `envFrom.configMapRef` and mounts
the file ConfigMap as a full directory mount:

```yaml
envFrom:
  - configMapRef:
      name: python-app-devops-info-python-env
volumeMounts:
  - name: config-volume
    mountPath: /config
    readOnly: true
```

Verification output:

```text
$ kubectl get configmap,pvc -n dev
NAME                                             DATA   AGE
configmap/kube-root-ca.crt                       1      15s
configmap/python-app-devops-info-python-config   1      15s
configmap/python-app-devops-info-python-env      4      15s

NAME                                                       STATUS   CAPACITY   ACCESS MODES   STORAGECLASS
persistentvolumeclaim/python-app-devops-info-python-data   Bound    100Mi      RWO            standard

$ kubectl exec -n dev pod/python-app-devops-info-python-78f9f6dd46-p9zpl -- cat /config/config.json
{
  "applicationName": "devops-info-service",
  "environment": "dev",
  "features": {
    "visitsCounter": true,
    "configHotReload": true,
    "structuredLogging": true,
    "prometheusMetrics": true
  },
  "settings": {
    "owner": "ellilin",
    "course": "DevOps Engineering",
    "lab": "lab12"
  }
}

$ kubectl exec -n dev pod/python-app-devops-info-python-78f9f6dd46-p9zpl -- printenv
APP_ENV=dev
LOG_LEVEL=info
FEATURE_VISITS_COUNTER=true
FEATURE_CONFIG_HOT_RELOAD=true
CONFIG_FILE=/config/config.json
VISITS_FILE=/data/visits
```

## Persistent Volume

`templates/pvc.yaml` creates a PVC when `persistence.enabled=true`:

```yaml
spec:
  accessModes:
    - "ReadWriteOnce"
  resources:
    requests:
      storage: "100Mi"
```

The deployment mounts the claim at `/data`, and the app writes `/data/visits`.
The storage class is configurable with `persistence.storageClass`; an empty value
uses the cluster default. Minikube provisioned the claim with the `standard`
storage class.

The chart defaults to one replica because this lab uses a single `ReadWriteOnce`
counter file. Multiple replicas would need a shared database or per-pod storage
pattern to avoid counter races.

Persistence test:

```text
$ kubectl exec -n dev pod/python-app-devops-info-python-78f9f6dd46-p9zpl -- python -c '... call / twice, then /visits ...'
... "visits":1 ...
... "visits":2 ...
{"file":"/data/visits","visits":2}
2

$ kubectl delete pod -n dev python-app-devops-info-python-78f9f6dd46-p9zpl
pod "python-app-devops-info-python-78f9f6dd46-p9zpl" deleted from dev namespace

$ kubectl wait --for=condition=Ready pod -n dev -l app.kubernetes.io/instance=python-app --timeout=120s
pod/python-app-devops-info-python-78f9f6dd46-bgkkf condition met

$ kubectl exec -n dev pod/python-app-devops-info-python-78f9f6dd46-bgkkf -- python -c '... call /visits and read /data/visits ...'
{"file":"/data/visits","visits":2}
2
```

## ConfigMap vs Secret

Use ConfigMaps for non-sensitive configuration: feature flags, log levels,
environment names, public endpoints, and JSON configuration files.

Use Secrets for sensitive values: passwords, API keys, tokens, TLS keys, and
database credentials. Secrets are separate Kubernetes resources, can be RBAC
restricted independently, and should be encrypted at rest in production.

Key differences:

- ConfigMaps are plain configuration and are not intended for sensitive data.
- Secrets are base64-encoded by the API and support secret-specific integrations,
  but base64 is not encryption.
- Both can be mounted as files or injected as environment variables.
- Both need rollout or reload handling when applications consume them at startup.

## Bonus: ConfigMap Hot Reload

### Default Update Behavior

Kubernetes updates mounted ConfigMap volumes automatically, but not instantly.
The kubelet sync period and ConfigMap cache can delay updates; Kubernetes
documentation describes delays up to the kubelet sync period plus cache TTL.

In Minikube, patching the ConfigMap was visible in the mounted file during the
first poll:

```text
$ kubectl patch configmap -n dev python-app-devops-info-python-config --type merge -p '... environment hot-reload ...'
configmap/python-app-devops-info-python-config patched

$ kubectl exec -n dev pod/python-app-devops-info-python-78f9f6dd46-bgkkf -- python -c 'import json; print(json.load(open("/config/config.json"))["environment"])'
hot-reload

$ kubectl exec -n dev pod/python-app-devops-info-python-78f9f6dd46-bgkkf -- python -c 'import urllib.request; print(urllib.request.urlopen("http://127.0.0.1:8000/config").read().decode())'
{"config":{"applicationName":"devops-info-service","environment":"hot-reload", ...}}
```

After Helm restored the ConfigMap content, the projected volume took about one
minute to return from `hot-reload` to `dev`:

```text
$ kubectl exec -n dev pod/python-app-devops-info-python-6d54658f65-vnwzq -- python -c 'import json; print(json.load(open("/config/config.json"))["environment"])'
dev

$ kubectl exec -n dev pod/python-app-devops-info-python-6d54658f65-vnwzq -- python -c 'import urllib.request; print(urllib.request.urlopen("http://127.0.0.1:8000/config").read().decode())'
{"config":{"applicationName":"devops-info-service","environment":"dev", ...}}
```

### subPath Limitation

ConfigMap volumes should be mounted as a directory when hot updates are required.
Mounting one ConfigMap key with `subPath` gives the container a bind-mounted file
snapshot. That file does not receive the kubelet's later atomic ConfigMap volume
updates. Use `subPath` only when the application requires a file at an exact path
inside an existing directory and stale content until restart is acceptable.

### Chosen Reload Approach

This lab implements application file watching. The Flask app stores the last
mtime of `CONFIG_FILE` and reloads JSON when `/` or `/config` observes a changed
file. This keeps the app responsive to regular ConfigMap volume updates without
adding a sidecar.

### Helm Upgrade Pattern

The deployment includes checksum annotations:

```yaml
annotations:
  checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
  checksum/secret: {{ include (print $.Template.BasePath "/secrets.yaml") . | sha256sum }}
```

When chart-rendered ConfigMaps or Secrets change, the pod template changes and
Kubernetes performs a rolling restart.

Checksum evidence:

```text
$ kubectl get deploy -n dev python-app-devops-info-python -o jsonpath='{.spec.template.metadata.annotations.checksum/config}'
6230bef0265cb09774fe492ee9424c54e18b1b2a25416aa0f796dd7c37ae0049

$ helm upgrade python-app k8s/python-app --namespace dev --set image.tag=lab12 --set image.pullPolicy=IfNotPresent --set hooks.enabled=false --set appConfig.environment=helm-upgrade --wait --timeout 180s
Release "python-app" has been upgraded. Happy Helming!
REVISION: 4
STATUS: deployed

$ kubectl get deploy -n dev python-app-devops-info-python -o jsonpath='{.spec.template.metadata.annotations.checksum/config}'
48f4096b6a1438373d59ecf07bf055591be011d561963bbbd92e5fc26b9431c6

$ kubectl rollout status deployment/python-app-devops-info-python -n dev --timeout=120s
deployment "python-app-devops-info-python" successfully rolled out
```

During the bonus test, a manual `kubectl patch` created a field-manager conflict
with Helm. I deleted the two chart-owned ConfigMaps and reran `helm upgrade` so
Helm owned the resources again in the local lab cluster.
