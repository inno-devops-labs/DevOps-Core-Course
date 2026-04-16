# Lab 12 - ConfigMaps and Persistent Volumes

## What I changed

For this lab I extended the Python service and the Helm chart so the app no longer keeps all of its state and configuration inside the container image.

The final setup has four moving parts:

- the Flask app keeps a visits counter in a real file and exposes it through `/visits`
- a file-based ConfigMap mounts `config.json` into the pod at `/config/config.json`
- a second ConfigMap injects a few operational environment variables through `envFrom`
- a PersistentVolumeClaim mounts `/data`, so the visits file survives pod replacement

I also completed the bonus task:

- the app reloads file-backed configuration when the mounted ConfigMap file changes
- I measured the live update delay for a mounted ConfigMap
- I documented why I avoided `subPath`
- the deployment uses checksum annotations, so a Helm config change triggers a rollout automatically

The namespace I used for verification was `lab12`.

## Application changes

The main application changes are in `app_python/app.py`.

What changed there:

- every request to `/` increments a counter stored in `VISITS_FILE_PATH`
- `/visits` returns the current value without incrementing it
- the counter file is created automatically if it does not exist
- file updates use `fcntl.flock`, `truncate`, `flush`, and `fsync`, so the write path is predictable even with concurrent requests
- the app reads JSON configuration from `APP_CONFIG_PATH`
- the config is reloaded when the file modification time changes

The Docker image was updated too:

- `/data` and `/config` are created in the image
- both directories are owned by the non-root app user

For local testing I added:

- `app_python/docker-compose.yml`
- `app_python/config/config.json`
- `app_python/data/.gitignore`

## Local Docker verification

I used Docker Compose for the local persistence check because it gives the app the same two mounts that the Kubernetes version uses later:

- `./config -> /config` as read-only
- `./data -> /data` as writable

Command:

```bash
cd app_python
mkdir -p data
docker compose up -d --build
```

Then I hit `/` twice and checked the visits file before and after a container restart:

```text
$ curl -fsS http://127.0.0.1:5000/ >/dev/null
$ curl -fsS http://127.0.0.1:5000/ >/dev/null
$ cat data/visits
3

$ docker compose restart devops-info-service
$ curl -fsS http://127.0.0.1:5000/visits
{"count":3,"file_path":"/data/visits"}
```

The counter was already at `1` from an earlier sanity check, so after two more `/` requests the file reached `3`. The important part is that the same value came back after restart.

## Helm chart changes

I kept the lab inside the existing Python chart from the previous labs:

```text
k8s/devops-info-service/
├── files/
│   └── config.json
├── templates/
│   ├── configmap.yaml
│   ├── deployment.yaml
│   ├── pvc.yaml
│   ├── secrets.yaml
│   ├── service.yaml
│   └── serviceaccount.yaml
└── values.yaml
```

The new or changed pieces are:

- `files/config.json`
  The JSON configuration that gets packaged into the chart and rendered through `.Files.Get`
- `templates/configmap.yaml`
  Creates two ConfigMaps:
  - one for the mounted `config.json`
  - one for environment variables
- `templates/pvc.yaml`
  Creates the PVC for `/data`
- `templates/deployment.yaml`
  Mounts `/config` and `/data`, injects env vars, and adds checksum annotations
- `templates/_helpers.tpl`
  Holds helper names, rendered config content, env data, and file path helpers

## ConfigMap implementation

### File-based ConfigMap

The file-based ConfigMap is rendered from `files/config.json` with `.Files.Get` and `tpl`, so the JSON stays readable in its own file but still picks up Helm values like the current environment and greeting.

That file is mounted as a full directory at `/config`. I intentionally mounted the whole directory instead of a single file through `subPath`, because the bonus task is about observing live updates, and `subPath` would break that behavior.

### Environment ConfigMap

The env ConfigMap is smaller and only carries operational values:

- `APP_ENV`
- `APP_LOG_LEVEL`
- `APP_CONFIG_PATH`
- `VISITS_FILE_PATH`

I kept the feature flags and greeting inside the mounted JSON file. That split turned out to be cleaner for the bonus task, because changing the file-backed config now has an obvious effect on the application response.

### Resource check

```text
$ kubectl get configmap,pvc -n lab12
NAME                                         DATA   AGE
configmap/devops-info-service-lab12-config   1      79s
configmap/devops-info-service-lab12-env      4      8m49s
configmap/kube-root-ca.crt                   1      8m54s

NAME                                                   STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/devops-info-service-lab12-data   Bound    pvc-c05497f9-3306-401f-986d-f0b58e96b577   100Mi      RWO            standard       <unset>                 8m49s
```

### Mounted file inside the pod

```text
$ kubectl exec -n lab12 devops-info-service-lab12-7cd7bdcc-p2fkk -- cat /config/config.json
{
  "application": {
    "name": "devops-info-service",
    "environment": "dev",
    "feature_flags": {
      "show_hostname": true,
      "show_request_headers": false
    },
    "settings": {
      "greeting": "Welcome to the DevOps info service",
      "log_level": "INFO"
    }
  }
}
```

### Environment variables inside the pod

```text
$ kubectl exec -n lab12 devops-info-service-lab12-7cd7bdcc-p2fkk -- sh -lc 'printenv | grep "^APP_" | sort'
APP_CONFIG_PATH=/config/config.json
APP_ENV=dev
APP_LOG_LEVEL=INFO
```

That is the split I wanted:

- the env ConfigMap tells the process where to look and what environment it is in
- the file-based ConfigMap carries the settings that I want to hot-reload

## Persistent volume

The chart creates a PVC with these defaults:

- access mode: `ReadWriteOnce`
- size: `100Mi`
- storage class: cluster default

On this local cluster the default storage class is `standard`, backed by `rancher.io/local-path`:

```text
$ kubectl get storageclass
NAME                 PROVISIONER             RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
standard (default)   rancher.io/local-path   Delete          WaitForFirstConsumer   false                  17d
```

The app writes the counter to `/data/visits`, and the deployment mounts the PVC at `/data`.

I also added `fsGroup: 999` to the pod security context so the non-root container can write to the mounted volume without needing a privileged container.

One honest note here: this repo still keeps the Python deployment at 3 replicas from the earlier labs. That works in this single-node kind cluster because the local-path volume is mounted on the same node and the file lock protects the shared counter file. In a real multi-node cluster I would not build a shared counter around one file on a single PVC. For production I would move the counter into a database or change the workload shape entirely.

## Persistence test

Before deleting a pod, the counter was:

```text
$ curl -fsS http://127.0.0.1:8083/visits
{"count":2,"file_path":"/data/visits"}
```

I deleted one pod directly:

```bash
kubectl delete pod -n lab12 devops-info-service-lab12-68544fdbfb-45s6v
kubectl rollout status deployment/devops-info-service-lab12 -n lab12 --timeout=180s
```

The replacement pod came up with a new name:

```text
$ kubectl get pods -n lab12 -o wide
NAME                                         READY   STATUS    RESTARTS   AGE    IP            NODE
devops-info-service-lab12-68544fdbfb-hzzgb   1/1     Running   0          110s   10.244.0.26   lab9-control-plane
devops-info-service-lab12-68544fdbfb-mghn2   1/1     Running   0          110s   10.244.0.25   lab9-control-plane
devops-info-service-lab12-68544fdbfb-sjtjf   1/1     Running   0          35s    10.244.0.29   lab9-control-plane
```

After the replacement, the counter was still there:

```text
$ curl -fsS http://127.0.0.1:8083/visits
{"count":2,"file_path":"/data/visits"}

$ kubectl exec -n lab12 devops-info-service-lab12-68544fdbfb-sjtjf -- cat /data/visits
2
```

That satisfied the core storage requirement: deleting a pod did not reset the counter.

## ConfigMap vs Secret

This lab uses both patterns now, so the difference is clearer in the repo than it was on paper.

| Use case | ConfigMap | Secret |
| --- | --- | --- |
| Non-sensitive application settings | Yes | No |
| Passwords, tokens, API keys | No | Yes |
| Mounted as regular config files | Yes | Yes |
| Injected as env vars | Yes | Yes |
| Meant to be human-readable in Git | Yes | No |
| Should be rotated and access-controlled more carefully | Not the main use case | Yes |

My own rule here is simple:

- if I would be comfortable printing it in a debug log, it can live in a ConfigMap
- if printing it would be a security mistake, it belongs in a Secret

Lab 11 already covered the Secret side. Lab 12 is the place for settings, flags, file paths, and similar runtime configuration.

## Bonus task

### Default mounted ConfigMap update behavior

I patched the live ConfigMap directly and then waited for the file inside the pod to change.

Observed result:

```text
$ kubectl patch configmap devops-info-service-lab12-config ...
$ while true; do ...; done
update_delay_seconds=31
```

That matched the documented behavior reasonably well. Kubernetes does not update the mounted file instantly. The ConfigMap object changes first, then the kubelet refreshes the projected volume later.

Once the mounted file updated, the app picked it up without a pod restart:

```text
$ curl -fsS http://127.0.0.1:8084/ | jq -r '.message'
Hello from hot reload
```

### Why I avoided `subPath`

The Kubernetes docs call this out explicitly: a ConfigMap mounted through `subPath` does not receive live updates.

That is why the deployment mounts the entire `/config` directory:

```yaml
volumeMounts:
  - name: config-volume
    mountPath: /config
    readOnly: true
```

If I had mounted only `/config/config.json` through `subPath`, the bonus reload test would have been dead on arrival.

### Reload approach I implemented

I chose application-level reload instead of a sidecar.

The app now:

- checks the mounted config file path on request
- compares the modification time to the cached value
- reloads JSON when the file changes
- uses the updated greeting and feature flags on the next request

I picked this approach because it fits the scope of the lab:

- no extra controller to install
- no sidecar image to manage
- easy to prove locally

It is also a good reminder that not every config change needs a full rollout if the application can safely reload it.

### Helm checksum rollout pattern

Live file updates are useful, but they only cover mounted ConfigMap content. Some changes still need a pod restart. For that path I added checksum annotations to the pod template:

```yaml
annotations:
  checksum/config-file: ...
  checksum/config-env: ...
```

That means a Helm-managed config change changes the pod template hash and creates a new ReplicaSet.

I tested it by upgrading the release with a different greeting:

```bash
helm upgrade devops-info-service-lab12 k8s/devops-info-service \
  -n lab12 \
  --set service.nodePort=30082 \
  --set config.settings.greeting='Hello from Helm checksum rollout'
```

Before the upgrade, the active ReplicaSet hash was `7cd7bdcc`:

```text
$ kubectl get rs -n lab12
NAME                                   DESIRED   CURRENT   READY   AGE
devops-info-service-lab12-7cd7bdcc     3         3         3       2m4s
```

After the upgrade, Helm created a new ReplicaSet with a new hash:

```text
$ kubectl get rs -n lab12
NAME                                   DESIRED   CURRENT   READY   AGE
devops-info-service-lab12-78c974bb5c   3         3         3       78s
devops-info-service-lab12-7cd7bdcc     0         0         0       3m27s
```

And the service returned the new message from the rolled-out pods:

```text
$ curl -fsS http://127.0.0.1:8085/ | jq -r '.message'
Hello from Helm checksum rollout
```

That gave me both bonus behaviors:

- file-mounted ConfigMap content can change in place and be reloaded by the app
- Helm-managed config changes can force a rollout through checksum annotations

## Official references

- ConfigMaps: https://kubernetes.io/docs/concepts/configuration/configmap/
- Mounted ConfigMap updates: https://kubernetes.io/docs/concepts/configuration/configmap/#mounted-configmaps-are-updated-automatically
- Persistent Volumes: https://kubernetes.io/docs/concepts/storage/persistent-volumes/
- Persistent Volume Claims: https://kubernetes.io/docs/concepts/storage/persistent-volumes/#persistentvolumeclaims

## Summary

This lab ended up being less about YAML volume mounts and more about separation of concerns.

The final version works because the responsibilities are clear:

- Secrets stay in the Secret workflow from Lab 11
- operational process settings come from env vars
- live-reloadable app settings live in `config.json`
- persistent state lives on the PVC

That split made the app easier to reason about and made the bonus task much less awkward than it would have been with one giant blob of configuration.
