# Lab 12 — ConfigMaps & Persistent Volumes



## 1. Application changes (Task 1)

### Visit counter and `/visits`

- **`GET /`** increments a counter persisted on disk (default path `/data/visits`, overridable with `VISITS_FILE`).
- The JSON response includes `visits.total` and `visits.file`.
- **`GET /visits`** returns `{"visits": <int>, "file": "<path>"}` without incrementing.
- Implementation uses a **thread lock** and **atomic replace** (write temp file, then `replace`) for simple concurrency safety.

### Optional mounted configuration

- If **`/config/config.json`** exists (path overridable with `CONFIG_JSON_PATH`), the app merges it into the root payload (`service.name`, `service.environment`, `service.mountedConfig`).

### Local Docker Compose

`app_python/docker-compose.yml` bind-mounts `./data` to `/data` and sets `VISITS_FILE=/data/visits`. For bind mounts, the compose file uses `user: "0:0"` so the process can write to the host directory in local dev.

**Suggested local test** — run from **`app_python/`** (the compose file and `./data` are there, not at the repo root).

```bash
cd app_python
mkdir -p data
docker compose up --build
# second terminal, still with cwd = app_python for cat / restart:
curl -s http://127.0.0.1:5000/ | jq .visits
curl -s http://127.0.0.1:5000/visits
cat data/visits
docker compose restart
curl -s http://127.0.0.1:5000/visits   # same count as before restart (persisted)
```

**Docker Compose evidence** (from `app_python/`):

```text
$ curl -s http://127.0.0.1:5000/ | jq .visits
{ "total": 5, "file": "/data/visits" }

$ curl -s http://127.0.0.1:5000/visits
{"visits":6,"file":"/data/visits"}

$ cat data/visits
6

$ docker compose restart
[+] Restarting 1/1
        Container app_python-devops-info-service-1  Started

$ curl -s http://127.0.0.1:5000/visits
{"visits":6,"file":"/data/visits"}
```

After restart, **`GET /visits`** still returns **`6`** and the host file **`data/visits`** contains **`6`** — the counter persists across container restarts via the bind-mounted volume.

 `pytest tests/ -v` from `app_python/` — **20 passed** 

**README:** `app_python/README.md` documents **`/visits`**, `VISITS_FILE`, and Docker Compose persistence (**Task 1**).

---

## 2. ConfigMap implementation (Task 2)

### Chart layout

| Path | Role |
|------|------|
| `files/config.json` | Source file bundled into a ConfigMap for file mount |
| `templates/configmap.yaml` | Renders `*-config-file` and optional `*-env` ConfigMaps |
| `templates/deployment.yaml` | Mounts `/config`, sets `CONFIG_JSON_PATH`, `envFrom` for env ConfigMap |

### File-based ConfigMap

`templates/configmap.yaml` loads JSON via `.Files.Get` (with `trim` for clean YAML) into key `config.json`. The Pod mounts the ConfigMap at **`/config`** (read-only), so the application sees **`/config/config.json`**.

### Environment ConfigMap

Non-sensitive key/value pairs come from `values.yaml` → `configMapEnv` (e.g. `APP_ENV`, `LOG_LEVEL`). The Deployment uses:

```yaml
envFrom:
  - configMapRef:
      name: <release>-env
  - secretRef:
      name: <release>-credentials   # when Lab 11 secrets are enabled
```

The same values appear in **`GET /`** as `service.mountedConfig` and related fields when the app reads **`CONFIG_JSON_PATH`** (`/config/config.json`).

---

## 3. Persistent volume (Task 3)

### PVC template

`templates/pvc.yaml` creates `*-data` when `persistence.enabled` is true:

- **Access mode:** `ReadWriteOnce`
- **Size:** `persistence.size` (e.g. `100Mi`)
- **Storage class:** optional `persistence.storageClass` (empty string = cluster default)

### Deployment mounts

- **`/data`** is backed by the PVC when persistence is enabled; otherwise an **`emptyDir`** is used so non-root workloads can still write the counter (ephemeral per Pod).
- **`VISITS_FILE`** defaults to `/data/visits` via `values.visits.filePath`.

### ReadWriteOnce and replicas

With **RWO**, only one node/Pod can mount the volume at a time. **`values-dev.yaml`** sets `replicaCount: 1` with `persistence.enabled: true`. The default `values.yaml` keeps `persistence.enabled: false` and `replicaCount: 3` for HA (each Pod then has its own `emptyDir` counter).

### Persistence test

With **`persistence.enabled: true`**, the counter file on **`/data`** survives Pod replacement. **Recorded verification:** delete the Pod, wait for a new Pod, then **`kubectl exec ... cat /data/visits`** and **`GET /visits`** (via port-forward) — same value; see section 5.

---

## 4. ConfigMap vs Secret (Task 4)

| | ConfigMap | Secret |
|--|-----------|--------|
| **Content** | Non-sensitive config (JSON, flags, log level) | Passwords, tokens, TLS keys |
| **API storage** | Plaintext in etcd (still protect with RBAC) | Base64 in API; enable etcd encryption for defense in depth |
| **Use** | Feature flags, `config.json`, env for non-secret settings | Credentials (Lab 11), TLS material |

Use **Secrets** for anything that would be a security incident if leaked; use **ConfigMaps** for everything else.

---

## 5. Minikube — Lab 12 image, Helm, recorded `kubectl`

### Image build and push

From **`app_python/`**: `docker build -t mclavrushka/devops-info-service:lab12 .` and `docker push ...` — digest `sha256:bbf28de49b1f004c1beefd51804e9e1005655aa4f02ca32a733ad48a29ac58a6`.

### Helm

Run **`helm upgrade --install`** from the **repository root** (not `app_python/`). Cluster must be up (**`minikube start`** if the API is unreachable). Example:

```bash
helm upgrade --install devops-dev ./k8s/devops-info-service \
  -f k8s/devops-info-service/values-dev.yaml \
  --set image.tag=lab12
```

**Recorded:** `Release "devops-dev"`, `REVISION: 7`, namespace `default`, `STATUS: deployed`.

### `kubectl get configmap`, PVC (Task 4)

```text
$ kubectl get pods,svc,pvc,configmap -n default -l app.kubernetes.io/instance=devops-dev

NAME                                       READY   STATUS    RESTARTS   AGE
pod/devops-info-service-69cf97cd5b-gw68r   0/1     Pending   0          17s
pod/devops-info-service-754544ff9-wg4fh    0/2     Error     0          6d18h

NAME                          TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service   NodePort   10.104.229.39   <none>        80:30222/TCP   15d

NAME                                             STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/devops-info-service-data   Pending                                      standard       17s

NAME                                        DATA   AGE
configmap/devops-info-service-config-file   1      17s
configmap/devops-info-service-env           2      17s
```

(Early snapshot: PVC was **`Pending`** until provisioned; then the Pod became **`Running`**.)

### File and env inside the Pod (Task 4)

**Recorded** (live `kubectl exec` against the running Deployment):

```text
$ kubectl exec -n default deploy/devops-info-service -- cat /config/config.json
{
  "applicationName": "devops-info-service",
  "environment": "development",
  "features": {
    "visitsCounter": true,
    "metrics": true
  }
}

$ kubectl exec -n default deploy/devops-info-service -- printenv | grep -E '^(APP_ENV|LOG_LEVEL|VISITS_FILE)='
APP_ENV=development
LOG_LEVEL=debug
VISITS_FILE=/data/visits
```

### Port-forward (HTTP checks)

In a separate terminal:

```bash
kubectl port-forward -n default svc/devops-info-service 8080:80
# Service maps to app port 5000 — forward shows: 127.0.0.1:8080 -> 5000
```

Then `curl -s http://127.0.0.1:8080/` / `/visits` hit the Pod. **`curl` only works while that port-forward process is running** — if it exits, requests to `127.0.0.1:8080` return nothing until you start port-forward again.

### PVC persistence test (recorded)

After the Pod was **`1/1 Running`**, the Pod was deleted; the ReplicaSet created a replacement. **`cat /data/visits` in the new Pod** still showed the same total — counter stored on the PVC.

```text
$ kubectl get pods -n default -l app.kubernetes.io/instance=devops-dev
NAME                                   READY   STATUS    RESTARTS   AGE
devops-info-service-69cf97cd5b-gw68r   1/1     Running   0          9m19s

$ kubectl delete pod -n default devops-info-service-69cf97cd5b-gw68r
pod "devops-info-service-69cf97cd5b-gw68r" deleted

$ kubectl wait --for=condition=ready pod -n default -l app.kubernetes.io/instance=devops-dev --timeout=120s
pod/devops-info-service-69cf97cd5b-s2xct condition met

$ kubectl exec -n default deploy/devops-info-service -- cat /data/visits
2

$ curl -s http://127.0.0.1:8080/visits   # with port-forward active (separate terminal)
{"visits":2,"file":"/data/visits"}
```

**Result:** Old Pod **`devops-info-service-69cf97cd5b-gw68r`**, new Pod **`devops-info-service-69cf97cd5b-s2xct`** — same **`/data/visits`** value (**`2`**) and same **`GET /visits`** over HTTP, so **PVC persistence across Pod deletion is confirmed** (Task 3 / Task 4 persistence evidence).

