# Lab 12 — ConfigMaps and persistent storage

This document describes how the DevOps Info Service uses **ConfigMaps** (file + environment), a **PersistentVolumeClaim** for the visit counter, and how to verify behavior in a cluster.

## Application changes

### Visit counter

- Each **GET /** increments a counter stored in a file whose path is set by **`VISITS_DATA_PATH`** (default `/data/visits`).
- The file is created on first write. Parent directories are created if needed.
- Writes use a **temporary file in the same directory** and **`os.replace`** for an atomic rename on the same filesystem.
- A **`threading.Lock`** serializes read–increment–write to avoid lost updates under concurrent requests.
- **GET /visits** returns the current total **without** incrementing, plus the resolved path and a timestamp.

### Local Docker Compose

`monitoring/docker-compose.yml` mounts **`./data` → `/data`** in the app container and sets **`VISITS_DATA_PATH=/data/visits`**. After several requests to `/`, you can inspect the file on the host:

```bash
cat monitoring/data/visits
```

Restart the `app-python` container and call **GET /visits** (or **GET /**) again; the counter should continue from the last value.

## Helm: ConfigMaps

The chart `k8s/devops-python` defines two ConfigMaps when **`config.enabled`** is true (see `values.yaml`):

| Resource | Purpose |
|----------|---------|
| `{{ release-name }}-devops-python-file` | File **`config.json`** from `files/config.json` (via `.Files.Get`) |
| `{{ release-name }}-devops-python-env` | Keys **`APP_CONFIG_ENV`**, **`LOG_LEVEL`**, **`FEATURE_DEBUG`** from values |

### File mount

The Deployment mounts the file ConfigMap at **`/config`**, so the app reads **`/config/config.json`** (see `load_config_file()` in `app_python/app.py`). The JSON is included in **GET /** under **`config.file`** when the file exists.

### Environment variables

**`envFrom`** includes **`configMapRef`** for the env ConfigMap (when **`config.injectEnv`** is true) **in addition to** any **`secretRef`** from Lab 11. The app exposes these in **GET /** under **`config.environment`**, **`config.log_level`**, and **`config.feature_debug`**.

### Verification commands

Replace `<release>` and `<namespace>` as appropriate.

```bash
kubectl get configmap,pvc -n <namespace> -l app.kubernetes.io/instance=<release>
kubectl exec deploy/<release>-devops-python -n <namespace> -- cat /config/config.json
kubectl exec deploy/<release>-devops-python -n <namespace> -- printenv | grep -E '^(APP_CONFIG_ENV|LOG_LEVEL|FEATURE_DEBUG)='
```

Example output shapes (your names and ages will differ):

```text
NAME                                        DATA   AGE
configmap/<release>-devops-python-env       3      1m
configmap/<release>-devops-python-file      1      1m

NAME                                              STATUS   VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/<release>-devops-python-data   Bound    pvc-...   100Mi      RWO            standard       1m
```

## Persistent volume (visit counter)

### PVC template

`templates/pvc.yaml` creates a claim **`{{ fullname }}-data`** when **`persistence.enabled`** is true:

- **Access mode:** `ReadWriteOnce` (one node can mount the volume read-write at a time).
- **Size:** `persistence.size` (default `100Mi`).
- **Storage class:** omitted if `persistence.storageClass` is empty (cluster default).

The Deployment mounts this PVC at **`/data`**, matching **`VISITS_DATA_PATH=/data/visits`** in chart values.

### RWO and replicas

With **ReadWriteOnce**, only **one** pod can attach the volume on many multi-node clusters. **kind** / **minikube** single-node setups often allow multiple pods on the same node, but that is not portable. For production-like multi-node clusters, either:

- run **one replica** while using this PVC, or
- use **ReadWriteMany** / shared storage if you need multiple writers.

`values-prod.yaml` sets **`replicaCount: 5`**; if you enable this PVC in a multi-node environment, scale down or switch storage class accordingly.

### Persistence test (pod delete)

1. Note **`visits_total`** from **GET /visits** (via port-forward or Ingress).
2. Delete only the pod (Deployment will recreate it):

   ```bash
   kubectl delete pod -n <namespace> -l app.kubernetes.io/instance=<release>
   ```

3. Wait for the new pod to become ready, then call **GET /visits** again. The count should match the pre-delete value.
4. Optional: `kubectl exec` and `cat /data/visits` before and after.

## ConfigMap vs Secret

| Use ConfigMap | Use Secret |
|---------------|------------|
| Non-sensitive settings (log level, feature flags, app name, JSON config) | Passwords, API keys, TLS private keys, database URLs with credentials |
| Readable by anyone with `get/list` on ConfigMaps in the namespace | Base64-encoded at rest; restrict RBAC; consider encryption at rest / external secret managers |

**Rule of thumb:** if disclosure would harm security or compliance, use a **Secret** (or Vault, as in Lab 11), not a ConfigMap.

## Bonus: reload and checksum annotations

### Mounted ConfigMap updates

For a **directory** mount (not **`subPath`**), the kubelet periodically refreshes files when the ConfigMap changes; total delay can be on the order of a minute or more depending on sync and cache behavior. See [Mounted ConfigMaps are updated automatically](https://kubernetes.io/docs/concepts/configuration/configmap/#mounted-configmaps-are-updated-automatically).

### `subPath`

If you mount a single file with **`subPath`**, the file is **not** updated when the ConfigMap changes, because it is effectively copied at mount time. Avoid **`subPath`** when you need hot reload of individual files from a ConfigMap; prefer mounting the whole directory.

### Pod restart on config change (this chart)

When **`configMapChecksum.enabled`** and **`config.enabled`** are true, the Pod template includes annotations:

- **`checksum/config-file`** — SHA-256 of `files/config.json`
- **`checksum/config-env`** — SHA-256 of a string derived from **`config.environment`**, **`config.logLevel`**, and **`config.featureDebug`**

Changing those inputs changes the annotation values, which updates the Deployment spec and triggers a **rolling restart** so the app sees new env vars and file content immediately (without relying on kubelet sync alone).

To simulate a change, run **`helm upgrade`** after editing **`values.yaml`** or **`files/config.json`**, then observe a new ReplicaSet and rolled pods:

```bash
helm upgrade <release> ./k8s/devops-python -n <namespace> -f k8s/devops-python/values.yaml
kubectl rollout status deploy/<release>-devops-python -n <namespace>
```
