# Lab 12 — ConfigMaps & Persistent Volumes

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Configuration%20%26%20Storage-blue)
![points](https://img.shields.io/badge/points-10%2B2-orange)
![tech](https://img.shields.io/badge/tech-ConfigMaps%20%7C%20PVC%20%7C%20K8s%201.36-informational)

> Externalize runtime configuration with ConfigMaps and make application data survive a pod restart with a PersistentVolumeClaim. One image, three environments, zero rebuilds — and a visit counter that outlives the pod that wrote it.

## Overview

In Labs 9–10 you deployed your apps to Kubernetes and packaged them into a Helm chart; Lab 11 secured the sensitive values. But not every value is a secret — log levels, feature flags, app names, and feature settings belong in **ConfigMaps**. And containers are ephemeral: a pod restart wipes the writable layer, so any state your app keeps on disk vanishes. This lab adds both: ConfigMap-driven configuration and a **PersistentVolumeClaim** that keeps your data across restarts.

**What You'll Learn:**
- ConfigMap creation and the three injection patterns: single env var, `envFrom`, volume mount
- File-based vs environment-variable configuration (12-Factor, Factor III)
- The PV / PVC / StorageClass trio and dynamic provisioning
- Access modes, reclaim policies, and how a PVC binds to a PV
- ConfigMap update behavior and the hot-reload trap (`subPath`)

**Building On:** The Helm chart from Labs 10–11 (which packaged your Lab 9 Kubernetes deployment) is extended with ConfigMaps and persistent storage.

**Tech Stack:** Kubernetes **1.36 "Haru"** | ConfigMaps | PersistentVolumeClaim + StorageClass | Helm **4** | CSI dynamic provisioning

> **Cluster note:** This course standardizes on **Kubernetes 1.36** via **k3d** (released Apr 22 2026; 1.33–1.35 are still in support under the N-2 policy). Run all commands below against your 1.36 k3d cluster. k3d (k3s) ships a default `StorageClass` backed by the **local-path-provisioner** (`rancher.io/local-path`) out of the box — RWO only, no snapshots, fine for the visits counter. On a real cloud cluster the same PVC binds to an **AWS EBS** (`ebs.csi.aws.com`) or **GCE PD** (`pd.csi.storage.gke.io`) volume via its CSI driver.

---

## Tasks

> **Note on outputs:** All command outputs shown below are **illustrative** — your pod names, hashes, and timestamps will differ. Capture *your own* real output for the documentation task.

Main tasks sum to **10 points**. The bonus is worth **2 points**.

### Task 1 — Application Persistence Upgrade (2 pts)

**Objective:** Add a visit counter that persists to a file. This task is standalone — it changes only your application code and `docker-compose.yml`; no Kubernetes resources yet.

**Requirements:**

1. **Add a Visit Counter**
   - Increment a counter on every request to `GET /`.
   - Store the value in a file (e.g. `/data/visits`), read on startup (default `0` if the file is missing).
   - Add a new `GET /visits` endpoint that returns the current count as JSON.

2. **Handle the Filesystem Honestly**
   - Create the data directory if it does not exist.
   - Write atomically (write to a temp file, then `rename`) so a crash mid-write can't corrupt the count.
   - Make the data path configurable via an environment variable (e.g. `DATA_DIR`, default `/data`).

3. **Test Locally with Docker Compose**
   - Mount a host volume for the data directory in `docker-compose.yml`.
   - Hit `/` several times, confirm `/visits` reflects the count, restart the container, and confirm the count **continues** rather than resetting.
   - Update your application's `README.md` with the new endpoint and the `DATA_DIR` variable.

<details>
<summary>💡 Hints</summary>

**Flow:**
```
GET /        → read counter file → increment → atomic write → respond
GET /visits  → read counter file → respond { "visits": N }
```

**Atomic write (Python sketch — fill in your framework's handler):**
```python
import os, tempfile

DATA_DIR = os.getenv("DATA_DIR", "/data")
COUNTER = os.path.join(DATA_DIR, "visits")

def read_count():
    try:
        with open(COUNTER) as f:
            return int(f.read().strip() or 0)
    except FileNotFoundError:
        return 0

def write_count(n):
    os.makedirs(DATA_DIR, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=DATA_DIR)
    with os.fdopen(fd, "w") as f:
        f.write(str(n))
    os.replace(tmp, COUNTER)   # atomic on the same filesystem
```

**Docker Compose volume:**
```yaml
services:
  app:
    # ... your build/image ...
    environment:
      DATA_DIR: /data
    volumes:
      - ./data:/data          # host ./data persists across `docker compose down/up`
```

**Test:**
```bash
docker compose up -d
curl localhost:8080/ ; curl localhost:8080/ ; curl localhost:8080/visits   # illustrative -> {"visits": 2}
docker compose restart app
curl localhost:8080/visits                                                  # still 2, not reset
cat ./data/visits                                                           # 2
```

> Basic read/write is acceptable for this lab; the atomic `rename` is the one habit worth keeping.

</details>

---

### Task 2 — ConfigMaps (3 pts)

**Objective:** Externalize non-sensitive configuration into ConfigMaps and inject it two ways — as a mounted file and as bulk environment variables.

**Requirements:**

1. **Config File ConfigMap (volume mount)**
   - Add `files/config.json` to your chart with at least: app name, environment (`dev`/`prod`), and one or more feature flags.
   - Add `templates/configmap.yaml` that loads the file with `.Files.Get` and mount it into the pod at a path (e.g. `/config/config.json`).

2. **Env-Var ConfigMap (`envFrom`)**
   - Add a **second** ConfigMap of plain key-value pairs (e.g. `APP_ENV`, `LOG_LEVEL`).
   - Inject all of its keys with `envFrom: configMapRef` so they appear as environment variables in the container.

3. **Verify Both**
   - Confirm the file is readable inside the pod and the env vars are present.

**Skeleton — `templates/configmap.yaml` (fill in the YOUR-TASK markers):**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "mychart.fullname" . }}-config
  labels:
    {{- include "mychart.labels" . | nindent 4 }}
data:
  config.json: |-
{{ .Files.Get "files/config.json" | indent 4 }}      # YOUR-TASK: ensure files/config.json exists
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "mychart.fullname" . }}-env
  labels:
    {{- include "mychart.labels" . | nindent 4 }}
data:
  APP_ENV: {{ .Values.environment | quote }}          # YOUR-TASK: add LOG_LEVEL and any feature flags
```

**Skeleton — Deployment wiring (fill in the YOUR-TASK markers):**
```yaml
spec:
  template:
    spec:
      containers:
        - name: app
          envFrom:
            - configMapRef:
                name: {{ include "mychart.fullname" . }}-env   # bulk env injection
          volumeMounts:
            - name: config-vol
              mountPath: /config                                # YOUR-TASK: whole dir, NOT subPath
      volumes:
        - name: config-vol
          configMap:
            name: {{ include "mychart.fullname" . }}-config
```

> **Pattern reminder:** `envFrom` takes *every* key in the ConfigMap and can't rename or filter — curate the ConfigMap, not the injection. Mount the config file as a **whole directory** (no `subPath`) so it can auto-update (you'll exploit this in the bonus).

<details>
<summary>💡 Hints</summary>

**`files/config.json` (example):**
```json
{
  "appName": "devops-info-service",
  "environment": "dev",
  "features": { "visitsCounter": true, "verboseErrors": false }
}
```

**`values.yaml` additions:**
```yaml
environment: dev
logLevel: info
```

**Verify (illustrative):**
```bash
POD=$(kubectl get pod -l app.kubernetes.io/name=mychart -o jsonpath='{.items[0].metadata.name}')
kubectl exec "$POD" -- cat /config/config.json
# {"appName":"devops-info-service","environment":"dev", ...}
kubectl exec "$POD" -- printenv | grep -E 'APP_ENV|LOG_LEVEL'
# APP_ENV=dev
# LOG_LEVEL=info
```

**Resources:**
- [ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/)
- [Configure a Pod with a ConfigMap](https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/)
- [Helm `.Files.Get`](https://helm.sh/docs/chart_template_guide/accessing_files/)

</details>

---

### Task 3 — Persistent Volumes (3 pts)

**Objective:** Back the visit counter with a PersistentVolumeClaim so the count survives `kubectl delete pod`.

**Requirements:**

1. **PersistentVolumeClaim**
   - Add `templates/pvc.yaml` requesting a small volume (e.g. `100Mi`), access mode `ReadWriteOnce`, and a **configurable** `storageClassName` (empty string ⇒ cluster default).
   - Gate the whole feature behind `.Values.persistence.enabled`.

2. **Mount the PVC**
   - Add a volume referencing the PVC and mount it at your data directory (the `DATA_DIR` from Task 1, e.g. `/data`).
   - Confirm the app writes `visits` onto the mounted volume.

3. **Prove Persistence**
   - Deploy, hit `/` several times, note the count from `/visits`.
   - `kubectl delete pod <pod>` (the Deployment recreates it), then confirm the new pod reports the **same** count.

**Skeleton — `templates/pvc.yaml` (fill in the YOUR-TASK markers):**
```yaml
{{- if .Values.persistence.enabled }}
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "mychart.fullname" . }}-data
  labels:
    {{- include "mychart.labels" . | nindent 4 }}
spec:
  accessModes:
    - ReadWriteOnce                                  # YOUR-TASK: RWO is correct for a single writer — explain why
  resources:
    requests:
      storage: {{ .Values.persistence.size }}
  {{- with .Values.persistence.storageClass }}
  storageClassName: {{ . }}                          # omit entirely to use the cluster default
  {{- end }}
{{- end }}
```

**Skeleton — Deployment volume (fill in the YOUR-TASK markers):**
```yaml
spec:
  template:
    spec:
      containers:
        - name: app
          volumeMounts:
            - name: data-vol
              mountPath: /data                       # YOUR-TASK: match DATA_DIR from Task 1
      volumes:
        - name: data-vol
          persistentVolumeClaim:
            claimName: {{ include "mychart.fullname" . }}-data
```

<details>
<summary>💡 Hints</summary>

**`values.yaml` additions:**
```yaml
persistence:
  enabled: true
  size: 100Mi
  storageClass: ""   # "" => cluster default (local-path on k3d, gp3/pd on cloud)
```

**Verify the claim binds (illustrative):**
```bash
kubectl get pvc
# NAME             STATUS   VOLUME        CAPACITY   ACCESS MODES   STORAGECLASS
# mychart-data     Bound    pvc-1a2b...   100Mi      RWO            standard
```
> On k3d with `WaitForFirstConsumer`, the PVC stays **Pending** until a pod mounts it — that's expected, not an error.

**Persistence test (illustrative):**
```bash
POD=$(kubectl get pod -l app.kubernetes.io/name=mychart -o jsonpath='{.items[0].metadata.name}')
kubectl exec "$POD" -- cat /data/visits          # e.g. 5
kubectl delete pod "$POD"                          # Deployment spins up a replacement
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=mychart --timeout=60s
kubectl exec deploy/mychart -- cat /data/visits  # still 5 — survived the restart
```

**Resources:**
- [Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
- [Configure a Pod to Use a PersistentVolume](https://kubernetes.io/docs/tasks/configure-pod-container/configure-persistent-volume-storage/)
- [Storage Classes](https://kubernetes.io/docs/concepts/storage/storage-classes/)

</details>

---

### Task 4 — Documentation (2 pts)

**Objective:** Document your ConfigMap and persistence implementation with real evidence.

**Create `k8s/CONFIGMAPS.md` with:**

1. **Application Changes** — the visit-counter design, the `/visits` endpoint, the `DATA_DIR` variable, and your local Docker Compose persistence evidence.
2. **ConfigMap Implementation** — the two ConfigMaps, your `config.json`, how the file is mounted vs how the env vars are injected (`envFrom`), and verification output (`cat /config/config.json`, `printenv`).
3. **Persistent Volume** — your PVC config, a short note on the **access mode** and **storage class** you chose, the volume mount, and the persistence proof: count before delete, the `kubectl delete pod` command, count after the new pod starts.
4. **ConfigMap vs Secret** — when to use each and the key differences (RBAC, tmpfs, encryption-at-rest). Reference Lab 11.

**Required outputs/screenshots:**
- `kubectl get configmap,pvc`
- File content inside the pod (`cat /config/config.json`)
- Environment variables in the pod (`printenv`)
- Persistence test: before and after pod deletion

---

## Bonus Task — ConfigMap Hot Reload (2 pts)

**Objective:** Understand why a ConfigMap change does **not** restart pods, and make config changes actually take effect.

**Requirements:**

1. **Observe Default Behavior**
   - Edit a value in your mounted-file ConfigMap (e.g. `kubectl edit configmap mychart-config`).
   - Watch the mounted file inside the pod and **measure** how long until the change appears. Note that env-var ConfigMaps never update a running pod at all.

2. **Explain the `subPath` Trap**
   - In one short paragraph, explain why a `subPath` mount is a one-shot copy that never updates, and when you'd accept that trade-off.

3. **Implement ONE Reload Strategy**
   - **A — Checksum annotation (GitOps-native):** add a `checksum/config` pod-template annotation whose value is the `sha256sum` of the ConfigMap; changing the CM changes the annotation ⇒ rolling restart. *(Recommended.)*
   - **B — Reloader controller:** install `stakater/Reloader` and annotate the Deployment `reloader.stakater.com/auto: "true"`.
   - **C — App-level watch:** have your app `inotify`/`fsnotify` (or poll) the mounted config file and re-read on change.
   - Demonstrate that changing the ConfigMap takes effect (a rolling restart for A/B, an in-place re-read for C).

**Skeleton — checksum annotation (Option A; fill in the YOUR-TASK markers):**
```yaml
spec:
  template:
    metadata:
      annotations:
        # YOUR-TASK: hash the rendered configmap so any change rolls the Deployment
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

<details>
<summary>💡 Hints</summary>

- **Whole-directory** mounts auto-update via a `..data` symlink swap, within `kubelet --sync-frequency` (default 60s) + cache TTL — total delay up to a couple of minutes. `subPath` files never update.
- **Env vars** are baked at pod start and never change in a running pod, regardless of the mount style.
- **Option B install (illustrative):**
  ```bash
  helm repo add stakater https://stakater.github.io/stakater-charts
  helm install reloader stakater/reloader -n reloader --create-namespace
  ```

**Resources:**
- [Mounted ConfigMaps are updated automatically](https://kubernetes.io/docs/concepts/configuration/configmap/#mounted-configmaps-are-updated-automatically)
- [Stakater Reloader](https://github.com/stakater/Reloader)

</details>

**Bonus Documentation:** add a section to `k8s/CONFIGMAPS.md` with your measured update delay, the `subPath` explanation, the strategy you chose, and evidence the reload worked.

---

## How to Submit

1. **Create Branch:**
   ```bash
   git checkout -b lab12
   ```

2. **Commit Work:**
   ```bash
   git add app_python/ <your-chart-dir>/ k8s/
   git commit -m "feat: implement lab12 configmaps and persistent volumes"
   git push -u origin lab12
   ```

3. **Create Pull Requests:**
   - **PR #1:** `your-fork:lab12` → `course-repo:master`
   - **PR #2:** `your-fork:lab12` → `your-fork:master`

4. **Verify:** chart + app changes present, `k8s/CONFIGMAPS.md` complete, persistence evidence captured.

---

## Acceptance Criteria

### Main Tasks (10 points)

**Task 1 — Application Persistence Upgrade (2 pts):**
- [ ] Visit counter increments on `GET /` and persists to a file
- [ ] `GET /visits` endpoint returns the current count
- [ ] Data path configurable (e.g. `DATA_DIR`); atomic write used
- [ ] `docker-compose.yml` mounts a volume; count survives a container restart
- [ ] App `README.md` updated

**Task 2 — ConfigMaps (3 pts):**
- [ ] `files/config.json` created and loaded via `.Files.Get`
- [ ] File-based ConfigMap mounted as a whole-directory volume (no `subPath`)
- [ ] Second ConfigMap injected via `envFrom: configMapRef`
- [ ] File readable in pod; env vars present (verification captured)

**Task 3 — Persistent Volumes (3 pts):**
- [ ] `templates/pvc.yaml` with `ReadWriteOnce`, configurable size + storage class
- [ ] PVC mounted at the data directory; app writes `visits` there
- [ ] PVC reaches `Bound` (or Pending→Bound on first consumer)
- [ ] Count verified identical after `kubectl delete pod`

**Task 4 — Documentation (2 pts):**
- [ ] `k8s/CONFIGMAPS.md` complete with all four sections and real evidence
- [ ] ConfigMap vs Secret comparison included (references Lab 11)

### Bonus Task (2 points)
- [ ] Default update behavior observed and delay measured; `subPath` trap explained
- [ ] One reload strategy (checksum annotation **/** Reloader **/** app-level watch) implemented and demonstrated
- [ ] Bonus documented in `k8s/CONFIGMAPS.md`

---

## Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **App Persistence Upgrade** | 2 pts | Visit counter, file persistence, `/visits` endpoint, Compose volume |
| **ConfigMaps** | 3 pts | File mount + `envFrom`, proper Helm templating, verified |
| **Persistent Volumes** | 3 pts | PVC, mount, verified survival across pod deletion |
| **Documentation** | 2 pts | Complete `CONFIGMAPS.md` with evidence |
| **Bonus** | 2 pts | Hot-reload strategy implemented + `subPath` understanding |
| **Total** | 12 pts | 10 pts required + 2 pts bonus |

**Grading:**
- **10/10:** Working persistence, both ConfigMap injection patterns, verified data survival
- **8–9/10:** ConfigMaps work, persistence mostly working, minor gaps
- **6–7/10:** Basic ConfigMap mounting, persistence issues
- **<6/10:** ConfigMaps not properly mounted, no persistence

---

## Resources

<details>
<summary>📚 Official Documentation</summary>

- [ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/)
- [Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
- [Persistent Volume Claims](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#persistentvolumeclaims)
- [Storage Classes](https://kubernetes.io/docs/concepts/storage/storage-classes/)

</details>

<details>
<summary>🎓 Tutorials</summary>

- [Configure a Pod with a ConfigMap](https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/)
- [Configure a Pod to Use a PersistentVolume](https://kubernetes.io/docs/tasks/configure-pod-container/configure-persistent-volume-storage/)
- [Mounting ConfigMaps as Files](https://kubernetes.io/docs/concepts/configuration/configmap/#using-configmaps-as-files-from-a-pod)

</details>

<details>
<summary>🛠️ Tools & CSI Drivers</summary>

- [Helm Files Function](https://helm.sh/docs/chart_template_guide/accessing_files/)
- [Stakater Reloader](https://github.com/stakater/Reloader) — auto-restart on ConfigMap/Secret change
- [local-path-provisioner](https://github.com/rancher/local-path-provisioner) — the default StorageClass in k3d (k3s)
- [AWS EBS CSI driver](https://github.com/kubernetes-sigs/aws-ebs-csi-driver)
- [GCE PD CSI driver](https://github.com/kubernetes-sigs/gcp-compute-persistent-disk-csi-driver)

</details>

---

## Looking Ahead

- **Lab 13:** ArgoCD deploys your configured Helm charts via GitOps — every ConfigMap and PVC lives in git
- **Lab 14:** Progressive delivery with Argo Rollouts
- **Lab 15:** StatefulSets — one PVC per pod via `volumeClaimTemplates`, for stateful workloads
- **Lab 16:** Monitoring your application's configuration and storage

---

**Good luck!** 📦

> **Remember:** ConfigMaps are for **non-sensitive** configuration only — use Secrets (Lab 11) for anything you'd file an incident over losing. A PersistentVolumeClaim is what makes your data outlive the pod that wrote it.
