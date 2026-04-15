# Lab 12: ConfigMaps & Persistent Volumes

## 1. Application Changes

### Implementation

The Python application was updated to persist a visits counter in a file and expose it through a new `/visits` endpoint.

Main changes:

- `app_python/app.py`
  - added `DATA_DIR`, `VISITS_FILE`, and `CONFIG_FILE`
  - added `read_visits_count()`, `write_visits_count()`, and `increment_visits_count()`
  - added `VISITS_LOCK` to avoid concurrent write races
  - writes the counter with an atomic temporary-file replacement
  - root endpoint `/` now increments and returns `runtime.visits_count`
  - new `/visits` endpoint returns the current value without incrementing it
- `monitoring/docker-compose.yml`
  - added persistent volume `app-python-data`
  - mounted it to `/app/data`
  - passed `DATA_DIR=/app/data`
- `app_python/README.md`
  - updated runtime and persistence usage examples


### Local Docker Evidence

The local container was started with a Docker volume mounted to `/app/data`.

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ docker compose ps app-python
NAME         IMAGE                                COMMAND                  SERVICE      CREATED              STATUS                        PORTS
app-python   s3rap1s/devops-info-service:latest   "sh -c 'mkdir -p /ap…"   app-python   About a minute ago   Up About a minute (healthy)   0.0.0.0:5000->5000/tcp, [::]:5000->5000/tcp
```

The root endpoint was called twice. The first response returned `visits_count: 1`, and the second returned `visits_count: 2`.

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ curl -s http://localhost:5000/
{"configuration":{"environment":{"APP_ENV":"undefined","CONFIG_FILE":"/app_python/config/config.json","DATA_DIR":"/app/data","FEATURE_GREETINGS":"undefined","LOG_LEVEL":"undefined"},"file":{}},"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"},{"description":"Visit counter","method":"GET","path":"/visits"},{"description":"Prometheus metrics","method":"GET","path":"/metrics"}],"request":{"client_ip":"172.20.0.1","method":"GET","path":"/","user_agent":"curl/8.18.0"},"runtime":{"current_time":"2026-04-15T10:22:42.476879+00:00","timezone":"UTC","uptime_human":"0 hours, 0 minutes","uptime_seconds":10,"visits_count":1},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"2.0.0"},"system":{"architecture":"x86_64","cpu_count":12,"hostname":"10a3e4f65471","platform":"Linux","platform_version":"6.18.9-arch1-2","python_version":"3.13.13"}}
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ curl -s http://localhost:5000/
{"configuration":{"environment":{"APP_ENV":"undefined","CONFIG_FILE":"/app_python/config/config.json","DATA_DIR":"/app/data","FEATURE_GREETINGS":"undefined","LOG_LEVEL":"undefined"},"file":{}},"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"},{"description":"Visit counter","method":"GET","path":"/visits"},{"description":"Prometheus metrics","method":"GET","path":"/metrics"}],"request":{"client_ip":"172.20.0.1","method":"GET","path":"/","user_agent":"curl/8.18.0"},"runtime":{"current_time":"2026-04-15T10:22:42.482292+00:00","timezone":"UTC","uptime_human":"0 hours, 0 minutes","uptime_seconds":10,"visits_count":2},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"2.0.0"},"system":{"architecture":"x86_64","cpu_count":12,"hostname":"10a3e4f65471","platform":"Linux","platform_version":"6.18.9-arch1-2","python_version":"3.13.13"}}
```

The `/visits` endpoint and the visits file both returned the same persisted value.

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ curl -s http://localhost:5000/visits
{"file":"/app/data/visits","visits":2}
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ docker compose exec app-python cat /app/data/visits
2
```

After restarting the container, the counter was still present.

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ docker compose restart app-python
 Container app-python Restarting 
 Container app-python Started 
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ docker compose ps app-python
NAME         IMAGE                                COMMAND                  SERVICE      CREATED         STATUS                    PORTS
app-python   s3rap1s/devops-info-service:latest   "sh -c 'mkdir -p /ap…"   app-python   6 minutes ago   Up 12 seconds (healthy)   0.0.0.0:5000->5000/tcp, [::]:5000->5000/tcp
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ curl -s http://localhost:5000/visits
{"file":"/app/data/visits","visits":2}
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ docker compose exec app-python cat /app/data/visits
2
```


## 2. ConfigMap Implementation

### Implementation

The Helm chart was extended with a `files/` directory and a new `templates/configmap.yaml`.

`k8s/devops-python/files/config.json` stores the file-based application configuration:

```json
{
  "application_name": "{{ .Values.configFile.applicationName }}",
  "environment": "{{ .Values.configFile.environment }}",
  "settings": {
    "featureGreeting": {{ .Values.configFile.settings.featureGreeting }},
    "maxVisitsDisplay": {{ .Values.configFile.settings.maxVisitsDisplay }}
  }
}
```

`k8s/devops-python/templates/configmap.yaml` renders two ConfigMaps:

- `lab12-release-devops-python-config`
  - stores `config.json`
  - uses `.Files.Get` together with `tpl`
- `lab12-release-devops-python-env`
  - stores environment variables from `.Values.configEnv`

The deployment uses both ConfigMaps:

- the file ConfigMap is mounted as `/config`
- the application reads `/config/config.json`
- the environment ConfigMap is injected through `envFrom`

### Verification Outputs

`kubectl get configmap,pvc`:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ kubectl get configmap,pvc -l app.kubernetes.io/instance=lab12-release
NAME                                           DATA   AGE
configmap/lab12-release-devops-python-config   1      48s
configmap/lab12-release-devops-python-env      5      48s

NAME                                                     STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/lab12-release-devops-python-data   Bound    pvc-0cf99f5e-1543-4ab8-b8f9-dd40041fca7b   100Mi      RWO            standard       <unset>                 48s
```

File content inside pod:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ kubectl exec lab12-release-devops-python-648c79689f-74xfn -- cat /config/config.json
Defaulted container "app" out of: app, volume-permissions (init)
{
  "application_name": "devops-info-service",
  "environment": "development",
  "settings": {
    "featureGreeting": true,
    "maxVisitsDisplay": 10
  }
}
```

Environment variables inside pod:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ kubectl exec lab12-release-devops-python-648c79689f-74xfn
Defaulted container "app" out of: app, volume-permissions (init)
development
info
true
/data
/config/config.json
```

This confirms both ConfigMap delivery methods:

- file-based configuration through `/config/config.json`
- key-value environment injection through `envFrom`


## 3. Persistent Volume

### Implementation

Persistent storage is defined in `k8s/devops-python/templates/pvc.yaml`.

The PVC configuration is:

- `accessModes: ReadWriteOnce`
- `resources.requests.storage: 100Mi`
- `storageClassName` configurable via values
- current Minikube deployment uses the default `standard` storage class

The deployment mounts the claim at `/data`, and the application stores the counter in `/data/visits`.

Because the application container runs as UID `999`, an init container prepares the mounted directory:

- image: `busybox:1.36.1`
- command: `mkdir -p /data && chown -R 999:999 /data`

### Persistence Test Evidence

The application was accessed through the NodePort service twice. The first response returned `visits_count: 1`, and the second returned `visits_count: 2`.

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ curl -s http://192.168.49.2:32172/
{"configuration":{"environment":{"APP_ENV":"development","CONFIG_FILE":"/config/config.json","DATA_DIR":"/data","FEATURE_GREETINGS":"true","LOG_LEVEL":"info"},"file":{"application_name":"devops-info-service","environment":"development","settings":{"featureGreeting":true,"maxVisitsDisplay":10}}},"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"},{"description":"Visit counter","method":"GET","path":"/visits"},{"description":"Prometheus metrics","method":"GET","path":"/metrics"}],"request":{"client_ip":"10.244.0.1","method":"GET","path":"/","user_agent":"curl/8.18.0"},"runtime":{"current_time":"2026-04-15T10:26:15.139157+00:00","timezone":"UTC","uptime_human":"0 hours, 0 minutes","uptime_seconds":47,"visits_count":1},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"2.0.0"},"system":{"architecture":"x86_64","cpu_count":12,"hostname":"lab12-release-devops-python-648c79689f-74xfn","platform":"Linux","platform_version":"6.18.9-arch1-2","python_version":"3.13.13"}}
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ curl -s http://192.168.49.2:32172/
{"configuration":{"environment":{"APP_ENV":"development","CONFIG_FILE":"/config/config.json","DATA_DIR":"/data","FEATURE_GREETINGS":"true","LOG_LEVEL":"info"},"file":{"application_name":"devops-info-service","environment":"development","settings":{"featureGreeting":true,"maxVisitsDisplay":10}}},"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"},{"description":"Visit counter","method":"GET","path":"/visits"},{"description":"Prometheus metrics","method":"GET","path":"/metrics"}],"request":{"client_ip":"10.244.0.1","method":"GET","path":"/","user_agent":"curl/8.18.0"},"runtime":{"current_time":"2026-04-15T10:26:15.144858+00:00","timezone":"UTC","uptime_human":"0 hours, 0 minutes","uptime_seconds":47,"visits_count":2},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"2.0.0"},"system":{"architecture":"x86_64","cpu_count":12,"hostname":"lab12-release-devops-python-648c79689f-74xfn","platform":"Linux","platform_version":"6.18.9-arch1-2","python_version":"3.13.13"}}
```

Counter value before pod deletion:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ curl -s http://192.168.49.2:32172/visits
{"file":"/data/visits","visits":2}
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ kubectl exec lab12-release-devops-python-648c79689f-74xfn -- cat /data/visits
Defaulted container "app" out of: app, volume-permissions (init)
2
```

Pod deletion command:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ kubectl delete pod lab12-release-devops-python-648c79689f-74xfn
pod "lab12-release-devops-python-648c79689f-74xfn" deleted from default namespace
```

New pod startup after deletion:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ kubectl get pods -l app.kubernetes.io/instance=lab12-release -o wide
NAME                                           READY   STATUS        RESTARTS   AGE   IP             NODE       NOMINATED NODE   READINESS GATES
lab12-release-devops-python-648c79689f-74xfn   1/1     Terminating   0          90s   10.244.0.118   minikube   <none>           <none>
lab12-release-devops-python-648c79689f-bjpxd   1/1     Running       0          18s   10.244.0.120   minikube   <none>           <none>
```

Counter value after the new pod started:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ curl -s http://192.168.49.2:32172/visits
{"file":"/data/visits","visits":2}
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ kubectl exec lab12-release-devops-python-648c79689f-bjpxd -- cat /data/visits
Defaulted container "app" out of: app, volume-permissions (init)
2
```

This verifies that the visits counter survived pod deletion because the data was stored on the PVC, not in the container filesystem.


## 4. ConfigMap vs Secret

### When to Use ConfigMap

ConfigMap should be used for non-sensitive configuration such as:

- application name
- environment name
- feature flags
- log levels
- file paths

### When to Use Secret

Secret should be used for sensitive values such as:

- passwords
- API tokens
- private keys
- database credentials

### Key Differences

- ConfigMap is intended for plain configuration data
- Secret is intended for confidential data
- both can be mounted as files or exposed as environment variables
- Secret values are still only base64-encoded in Kubernetes manifests, so stronger protection usually requires encryption at rest and access control


## 5. ConfigMap Hot Reload

### Default Update Behavior

The mounted ConfigMap was updated directly without restarting the pod.

Initial pod state:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ kubectl get pods -l app.kubernetes.io/instance=lab12-release -o wide
NAME                                           READY   STATUS    RESTARTS   AGE   IP             NODE       NOMINATED NODE   READINESS GATES
lab12-release-devops-python-648c79689f-bjpxd   1/1     Running   0          36m   10.244.0.120   minikube   <none>           <none>
```

The mounted file initially contained the original value:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ kubectl exec lab12-release-devops-python-648c79689f-bjpxd -- cat /config/config.json
Defaulted container "app" out of: app, volume-permissions (init)
{
  "application_name": "devops-info-service",
  "environment": "development",
  "settings": {
    "featureGreeting": true,
    "maxVisitsDisplay": 10
  }
}
```

The ConfigMap was then patched directly:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ kubectl patch configmap lab12-release-devops-python-config
configmap/lab12-release-devops-python-config patched
```

The file inside the running pod updated without recreating the pod. The measured delay was `31s`.

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ kubectl exec lab12-release-devops-python-648c79689f-bjpxd
Detected update after 31s
{
  "application_name": "devops-info-service",
  "environment": "live-patched",
  "settings": {
    "featureGreeting": true,
    "maxVisitsDisplay": 15
  }
}
```

This matches the expected Kubernetes behavior for mounted ConfigMaps: updates are not instant, but they propagate after the kubelet refresh cycle.

### subPath Limitation

`subPath` should be avoided for hot-reloaded configuration files.

Why:

- a normal ConfigMap directory mount is updated by Kubernetes in place
- a `subPath` file mount is effectively a bind-mounted copy
- when the ConfigMap changes, that copied file is not refreshed inside the container

Use `subPath` only when a fixed file path is required and live updates are not needed. For auto-updating mounted config, mount the full directory, as done in this lab with `/config`.

### Chosen Reload Approach

The implemented reload approach is pod restart via checksum annotation.

The deployment template now includes:

```yaml
annotations:
  checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

This means:

- when the rendered ConfigMap changes during `helm upgrade`
- the checksum value changes
- the Deployment pod template changes
- Kubernetes creates a new ReplicaSet and rolls out new pods automatically

### Helm Upgrade Pattern Evidence

First, the chart renders the checksum annotation:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ helm template lab12-release k8s/devops-python -f k8s/devops-python/values-dev.yaml --set image.tag=lab12 --set secret.username=appuser --set secret.password=appsecret
  name: lab12-release-devops-python
  name: lab12-release-devops-python-secret
  name: lab12-release-devops-python-config
  name: lab12-release-devops-python-env
  name: lab12-release-devops-python-data
  name: lab12-release-devops-python
kind: Deployment
  name: lab12-release-devops-python
        checksum/config: 0cef5b51a9aff2a47a2c5f65d25a3bcd85a43af1514d28b4ed5e3e3ee1fff3fb
  name: lab12-release-devops-python-post-install
  name: lab12-release-devops-python-pre-install
```

The release was upgraded with changed ConfigMap values:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ helm upgrade lab12-release k8s/devops-python -f k8s/devops-python/values-dev.yaml --set image.tag=lab12 --set secret.username=appuser --set secret.password=appsecret --set configFile.environment=bonus-reload --set configEnv.APP_ENV=bonus-reload --set configFile.settings.maxVisitsDisplay=25 --wait --wait-for-jobs --force-conflicts
Release "lab12-release" has been upgraded. Happy Helming!
NAME: lab12-release
LAST DEPLOYED: Wed Apr 15 14:04:28 2026
NAMESPACE: default
STATUS: deployed
REVISION: 3
DESCRIPTION: Upgrade complete
TEST SUITE: None
```

After the upgrade, Kubernetes created a new pod:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ kubectl get pods -l app.kubernetes.io/instance=lab12-release -o wide
NAME                                           READY   STATUS        RESTARTS   AGE   IP             NODE       NOMINATED NODE   READINESS GATES
lab12-release-devops-python-648c79689f-bjpxd   1/1     Terminating   0          38m   10.244.0.120   minikube   <none>           <none>
lab12-release-devops-python-75d7bf4d94-bl8dw   1/1     Running       0          20s   10.244.0.121   minikube   <none>           <none>
```

The new deployment template contains a different checksum:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ kubectl get deployment lab12-release-devops-python -o yaml
  name: lab12-release-devops-python
        checksum/config: 195b6fddf4edff2b38e3f2d57464a0831ab6d2943a7a64bc5af3460ae5ede3d8
            name: lab12-release-devops-python-env
            name: lab12-release-devops-python-secret
        image: s3rap1s/devops-info-service:lab12
        image: busybox:1.36.1
      serviceAccountName: lab12-release-devops-python
          name: lab12-release-devops-python-config
```

The new pod received the updated file-based and environment-based configuration:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ kubectl exec lab12-release-devops-python-75d7bf4d94-bl8dw -- cat /config/config.json
Defaulted container "app" out of: app, volume-permissions (init)
{
  "application_name": "devops-info-service",
  "environment": "bonus-reload",
  "settings": {
    "featureGreeting": true,
    "maxVisitsDisplay": 25
  }
}
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab12 λ kubectl exec lab12-release-devops-python-75d7bf4d94-bl8dw
Defaulted container "app" out of: app, volume-permissions (init)
bonus-reload
info
true
/data
/config/config.json
```

This demonstrates the chosen reload mechanism: changing the ConfigMap through Helm changes the checksum annotation, which forces a rolling update and applies the new configuration to new pods.
