# Lab 12 — ConfigMaps & Persistent Volumes

![difficulty](https://img.shields.io/badge/difficulty-intermediate-yellow)
![topic](https://img.shields.io/badge/topic-Configuration%20%26%20Storage-blue)
![points](https://img.shields.io/badge/points-10%2B2-orange)
![tech](https://img.shields.io/badge/tech-ConfigMaps%20%7C%20PVC%20%7C%20K8s%201.36-informational)

> **Goal:** Externalize non-secret config with ConfigMaps and make application data survive `kubectl delete pod` with a PersistentVolumeClaim.
> **Deliverable:** A PR from `lab12` extending your Lab 10/11 chart with two ConfigMaps + a PVC, an app-side visit counter, and `docs/LAB12.md` containing the write-delete-pod-read-from-new-pod persistence proof.

---

## Overview

Lab 11 hid your *secrets* (DB passwords, API tokens). But not every value is a secret — log levels, feature flags, app names, `NGINX` configs — these belong in **ConfigMaps**. And containers are *ephemeral*: when a pod restarts, its writable layer is gone. Anything your app wrote to local disk vanishes. The fix is a **PersistentVolumeClaim** — the pod claims storage by name, the volume follows the pod from one node to another, and the data outlives any individual pod.

In this lab you will practice:

- The three ConfigMap injection patterns (single env, `envFrom` bulk, volume mount) and **picking the right one for the situation**
- Designing a PVC: access mode, size, storage class — by **reading what the cluster actually offers** instead of guessing
- The headline proof: **write → `kubectl delete pod` → read from the new pod → same value**. A PVC that merely `Bound`s does NOT prove persistence.

> ⚠️ **Scope:** one replica with `ReadWriteOnce` storage. `ReadWriteMany` (multi-node concurrent writes) needs a network FS (NFS/EFS/CephFS) and is outside this lab. StatefulSets + `volumeClaimTemplates` (one PVC per replica) come in Lab 15.

---

## Project State

**You should have from previous labs:**
- Lab 9 — your `web` Deployment + Service on k3d (1.36)
- Lab 10 — your `lab10-app` Helm chart packaging that Deployment + Service
- Lab 11 — Secret(s) wired into the same chart

**This lab adds (in your existing chart):**
- App-side **visit counter** that writes to a file under `DATA_DIR` (default `/data`)
- `templates/configmap.yaml` — two ConfigMaps; one mounted as a file, one bulk-injected as env vars
- `templates/pvc.yaml` — a PVC under `.Values.persistence.enabled`
- Deployment patches to wire them in
- `docs/LAB12.md` — the persistence proof + your design reasoning

> 📚 Pairs with **Lecture 12 — ConfigMaps and Persistent Volumes**. Re-read slides 6–8 (injection patterns), 13–15 (PV/PVC/StorageClass, access modes, reclaim policies), and 16 (`subPath` trap) before you start.

---

## Setup

You need the k3d cluster from Lab 9 running on Kubernetes 1.36, your `lab10-app` chart, and `kubectl`.

```bash
kubectl get nodes                # should show k3d-devops-server-0 + 2 agents on v1.36.x
helm list -n lab12 2>/dev/null   # namespace you'll use below
```

**Before you write a single line of YAML**, inspect what the cluster gives you for free — the answers to "which access mode?" and "which storage class?" depend on it:

```bash
kubectl get storageclass
# YOUR TASK: read the output. Which one has the (default) marker? What provisioner backs it?
# Write the answer in docs/LAB12.md — this is the storage class your PVC will use.
```

> 💡 k3d (k3s) ships **`local-path`** (`rancher.io/local-path`) marked `(default)`. It's RWO-only, no snapshots — fine for a single-pod visits counter, not what you'd run in prod. On a real cloud cluster the same chart would bind to an **AWS EBS** (`ebs.csi.aws.com`) or **GCE PD** (`pd.csi.storage.gke.io`) volume via its CSI driver, with no chart change.

---

## Task 1 — Application Persistence Upgrade (2 pts)

Before any Kubernetes work, the app needs something worth persisting. Add a visit counter that writes to a file, and prove it works locally before you move on.

### 1.1 — Add the visit counter

`YOUR TASK`: in `app_python/app.py` (or your language equivalent), add the counter.

Requirements:

- `GET /` increments a counter; the value is stored in a file under `DATA_DIR` (env var, default `/data`).
- On startup, read the file. If it's missing, default to `0` — don't crash.
- Add `GET /visits` returning `{"visits": N}` JSON.
- Write **atomically**: write to a temp file in the same directory, then `os.replace(tmp, final)`. A crash mid-write must not corrupt the count.
- Make the data dir on startup if it doesn't exist (`os.makedirs(..., exist_ok=True)`).

Hints — sketch of the moving parts (do NOT copy-paste, derive the code yourself):

- **constants** — `DATA_DIR = env("DATA_DIR","/data")`, `COUNTER = DATA_DIR + "/visits"`
- **read_count** — open + `int(...)`; on `FileNotFoundError` return `0`
- **write_count(n)** — `mkstemp` in `DATA_DIR` → write → `os.replace(tmp, COUNTER)` (atomic)
- **`GET /`** — `c = read_count() + 1`; `write_count(c)`; respond
- **`GET /visits`** — respond `{ "visits": read_count() }`

### 1.2 — Local Docker Compose persistence test

`YOUR TASK`: in `app_python/docker-compose.yml`, mount a host directory at `DATA_DIR`. Hit `/` three times, restart the container, hit `/visits` — the count must continue, not reset.

Skeleton (fill in the blanks):

```yaml
services:
  app:
    # ... your build/image from Lab 2 ...
    environment:
      DATA_DIR: # YOUR TASK
    volumes:
      - # YOUR TASK: host-path : DATA_DIR
```

### 1.3 — Proof of work

Paste into `docs/LAB12.md`:

- The three curls (`curl localhost:8080/` × 3) + the `/visits` reading.
- `docker compose restart app` followed by `/visits` showing the **same** count, not 0.
- `cat ./data/visits` from the host showing the same integer (proves it's actually persisted, not a race).

---

## Task 2 — ConfigMaps: Three Patterns, One Decision Per Value (3 pts)

The lecture covered three ways to inject a ConfigMap into a pod. **One pattern per *value* — not all three for every value.** You'll ship two ConfigMaps (one shaped as files, one shaped as env vars), wire each into the pod with the pattern that fits its shape, and defend the choice for the three example values in the decision table below.

### 2.1 — Author the two ConfigMaps

You'll ship two ConfigMaps in `templates/configmap.yaml`. The shape and *labels* are given; the **data** is yours to fill from the chart's `values.yaml`.

Skeleton — `templates/configmap.yaml` (one file, two CMs separated by `---`):

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "lab10-app.fullname" . }}-file
  labels: {{- include "lab10-app.labels" . | nindent 4 }}
data:
  config.json: |-                # YOUR TASK: load files/config.json via .Files.Get
                                 #            and indent 4 — hint: `| indent 4`
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "lab10-app.fullname" . }}-env
  labels: {{- include "lab10-app.labels" . | nindent 4 }}
data:                            # YOUR TASK: ≥3 K/V pairs from .Values
                                 # ⚠️ keys must match [A-Z_][A-Z0-9_]* (Lec 12 slide 7)
                                 # invalid names are silently skipped by envFrom
```

`YOUR TASK`: create `files/config.json` with at least these keys: `appName`, `environment`, `features` (object with `visitsCounter: true`). Add the corresponding values to `values.yaml`.

### 2.2 — Pick an injection pattern per value

Three injection patterns exist (Lecture 12, slides 6–8). Below is the skeleton of each as a separate Deployment-patch block — **keep the ones you need, delete the others**, then justify your choices in `docs/LAB12.md`. At minimum your Deployment ends up using Pattern B (the env-shaped CM) **and** Pattern C (the file-shaped CM); Pattern A is optional and only earns points if you can defend a specific reason to rename or single-pick a key.

**Pattern A — single env, renamed/optional control.** Use when you want ONE value, possibly RENAMED into the container.

```yaml
env:
  - name:                            # YOUR TASK: env name inside the container
    valueFrom:
      configMapKeyRef:
        name:                        # YOUR TASK: which of your two ConfigMaps holds this?
        key:                         # YOUR TASK: key in the ConfigMap (may differ from name)
        optional:                    # YOUR TASK: true/false — start if missing?
```

**Pattern B — `envFrom` (bulk).** EVERY key in the CM becomes an env var. No rename, no filter — curate the ConfigMap, not the injection.

```yaml
envFrom:
  - configMapRef:
      name:                          # YOUR TASK
```

**Pattern C — volume mount (whole directory, NOT `subPath`).** For structured files (JSON/YAML/conf) the app reads; auto-updates without an image rebuild (Bonus depends on this).

```yaml
volumeMounts:
  - name:                            # YOUR TASK: must match the volume name below
    mountPath:                       # YOUR TASK: dir where config.json appears
                                     # ⚠️ NO subPath: here — see Bonus + Pitfalls
volumes:
  - name:                            # YOUR TASK: same name as the volumeMount above
    configMap:
      name:                          # YOUR TASK: which ConfigMap supplies the files?
```

Pick the right pattern for each of these values and document the choice in `docs/LAB12.md` (one sentence each):

| Value | Pattern? | Why? |
|---|---|---|
| `LOG_LEVEL` (a single string the framework reads from env) | YOUR TASK | YOUR TASK |
| `config.json` (a structured file with feature flags) | YOUR TASK | YOUR TASK |
| ≥ 10 boolean feature flags that all need to be env vars | YOUR TASK | YOUR TASK |

> 💡 **Hint** — none of the three answers is "all three". One value, one pattern. The point is the *decision*, not the proliferation.

### 2.3 — Proof of work

`YOUR TASK`: after `helm upgrade --install lab10-app k8s/lab10-app -n lab12 --create-namespace` (same chart path as Lab 10/11), capture:

```bash
# YOUR TASK: get the pod name into $POD
# YOUR TASK: cat the mounted config.json from inside the pod — shows file mount works
# YOUR TASK: printenv | grep -E '<your env keys>' — shows env injection works
# YOUR TASK: kubectl describe pod $POD | grep -A2 -E 'Environment|Mounts' — shows the wiring
```

Paste into `docs/LAB12.md`:

- The three captures above (file contents, env vars, pod description excerpt)
- The decision table from 2.2 filled in
- One paragraph: *if the ConfigMap had 30 keys but you only needed 2, would you still use `envFrom`? Why/why not?*

---

## Task 3 — Persistent Volumes: Read the Cluster, Then Write the Claim (3 pts)

A PVC has four knobs: `accessModes`, `resources.requests.storage`, `storageClassName`, and (less obviously) the **reclaim policy** inherited from the StorageClass. You'll set the first three explicitly — but only after inspecting what the cluster already offers.

### 3.1 — Inspect the cluster's storage first

```bash
kubectl get storageclass
kubectl get sc <default-sc-name> -o yaml | grep -E 'provisioner|reclaimPolicy|volumeBindingMode'
```

`YOUR TASK`: in `docs/LAB12.md`, answer:

- Which StorageClass has the `(default)` marker? What provisioner backs it?
- What's its `reclaimPolicy` (Delete vs Retain)? What happens to your data if you delete the PVC?
- What's its `volumeBindingMode`? Why does `WaitForFirstConsumer` mean a `Pending` PVC is **normal**, not a bug?

### 3.2 — Pick `accessModes` for the visits-counter use case

The four modes (Lecture 12, slide 14):

- **`ReadWriteOnce`** — RW from one *node* (multiple pods on that node OK). Cloud block storage (EBS/PD/Azure Disk) only supports this.
- **`ReadOnlyMany`** — RO from many nodes. Content distribution.
- **`ReadWriteMany`** — RW from many nodes simultaneously. Needs NFS/EFS/CephFS — slower, more expensive.
- **`ReadWriteOncePod`** — RW from exactly *one* pod cluster-wide (GA in K8s 1.29).

`YOUR TASK`: pick ONE for the visits counter and justify it in `docs/LAB12.md`. Hint: you have one Deployment replica writing to one file. Don't reach for the most flexible option — reach for the one that actually fits.

### 3.3 — Author the PVC

Skeleton — `templates/pvc.yaml`:

```yaml
{{- if .Values.persistence.enabled }}
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "lab10-app.fullname" . }}-data
  labels: {{- include "lab10-app.labels" . | nindent 4 }}
spec:
  accessModes:
    -                              # YOUR TASK: RWO | ROX | RWX | RWOP — pick + defend
  resources:
    requests:
      storage:                     # YOUR TASK: size — counter is one int, don't ask 100Gi
  {{- with .Values.persistence.storageClass }}
  storageClassName: {{ . }}        # omit field → cluster default; "" → also default
  {{- end }}
{{- end }}
```

Add to `values.yaml`:

```yaml
persistence:
  enabled: true
  size: # YOUR TASK
  storageClass: # YOUR TASK: "" to use the cluster default, or a specific name (e.g. local-path)
```

### 3.4 — Mount it on the Deployment

Patch `templates/deployment.yaml` — only the new bits:

```yaml
volumeMounts:
  - name:                          # YOUR TASK: invent a volume name (match below)
    mountPath:                     # YOUR TASK: must equal DATA_DIR from Task 1
volumes:
  - name:                          # YOUR TASK: same name as the volumeMount above
    {{- if .Values.persistence.enabled }}
    persistentVolumeClaim:
      claimName:                   # YOUR TASK: same name as the PVC you authored above
    {{- else }}
    emptyDir: {}                   # fallback: data dies with the pod
    {{- end }}
```

### 3.5 — The persistence proof (the headline)

This is the heart of the lab. **A `Bound` PVC means a volume exists, NOT that your data survived a pod restart.** You prove persistence by writing, deleting the pod, and reading from the new pod.

`YOUR TASK`: figure out the four steps yourself. You'll need `kubectl exec ... -- sh -c 'echo ... > $DATA_DIR/marker'`, `kubectl delete pod`, `kubectl wait`, and a final `kubectl exec ... cat $DATA_DIR/marker`.

Use a **separate file** called `marker` for this proof — don't reuse `/data/visits`. The counter increments naturally and you want a constant string to compare. Both files live on the same PVC, so the proof for `marker` is also the proof for `visits`.

```bash
# YOUR TASK: write a unique marker (e.g. epoch seconds) to $DATA_DIR/marker
#            inside the running pod (DATA_DIR defaults to /data — adjust if you changed it)
# YOUR TASK: delete the pod and wait for the Deployment to spin up a fresh one
# YOUR TASK: read $DATA_DIR/marker from the NEW pod
# YOUR TASK: prove the marker is the SAME — the write survived the pod's death
```

The deliverable is the actual captured output showing the *same* string before and after. If it differs (or the second `cat` returns "No such file or directory"), your PVC isn't really mounted at the data dir, or your storage class is doing something unexpected — debug with `kubectl describe pvc` and `kubectl describe pod`.

> 💡 You may see `Unknown stream id 5` from `kubectl exec` — that's a harmless client-side websocket warning, not a failure. If the data round-trips, you're fine.

### 3.6 — Proof of work

Paste into `docs/LAB12.md`:

- The storage-class inspection from 3.1 + your answers
- The access-mode decision from 3.2 with justification
- `kubectl get pvc` showing the claim `Bound` (or `Pending` if `WaitForFirstConsumer` and no pod has consumed it yet — explain which)
- **The persistence proof from 3.5: original pod name, marker written, delete command, new pod name, marker read — same value, side by side**

---

## Task 4 — Documentation (2 pts)

Bundle everything into `docs/LAB12.md`. Required sections, in order:

1. **App changes** — counter design, `DATA_DIR`, the atomic-write rationale, the Compose persistence capture from Task 1
2. **ConfigMap design** — your `files/config.json`, the two ConfigMaps, the decision table from Task 2.2, the verification captures from 2.3
3. **PVC design** — the StorageClass inspection, the access-mode justification, the PVC YAML, the mount, **the headline persistence proof from 3.5**
4. **ConfigMap vs Secret** — when to use each (RBAC scope, tmpfs vs regular fs, encryption-at-rest story). Reference Lab 11.
5. **Common pitfalls you hit** — at least one real one with how you debugged it

---

## Bonus Task — ConfigMap Hot Reload (2 pts)

Edit a value in `lab10-app-env`. Watch the running pod. The env var **doesn't change**. Edit a value in `lab10-app-file`. Watch the mounted file. It **eventually** changes — minutes later. If you'd used `subPath` to mount it as a single file? It would **never** change.

These three behaviors are why every team eventually picks a hot-reload strategy. Your job is to:

1. **Reproduce the default behavior.** `YOUR TASK`: edit a value with `kubectl edit configmap`, time how long until (a) the env var inside a running pod reflects the change — measure in the pod with `printenv` — and (b) the mounted file reflects the change — measure with `cat` in a loop. Document the result.

2. **Explain `subPath`.** `YOUR TASK`: in one paragraph in `docs/LAB12.md`, explain why a `subPath` mount is a one-shot copy that never updates, and when you'd accept that trade-off anyway (hint: clean mount paths, no `..data` symlink visible to the app).

3. **Pick and implement ONE strategy.** Don't reach for the install command yet — research the three options and choose:

   - **A — Checksum annotation (GitOps-native, no extra controller):** the pod template carries an annotation whose value is the `sha256sum` of the rendered ConfigMap. Any data change → annotation change → Deployment rolls out. Implemented entirely in your Helm template.
   - **B — Reloader controller** (Stakater): an in-cluster controller watches ConfigMaps/Secrets and patches owning Deployments to trigger a rollout. Zero chart logic, one annotation.
   - **C — App-level watch:** the app `inotify`-watches the mounted file and re-reads on change. No restart, instant. Used by NGINX, Envoy, Prometheus, Loki natively.

   `YOUR TASK`: in `docs/LAB12.md`, write 3–4 sentences on which one you picked and **why** (think: GitOps fit? extra moving parts? does your app even support C?). Then implement it. **No install commands or annotation snippets are shown in this lab** — go to the lecture, the docs, or the upstream README and figure it out.

4. **Demonstrate it works.** `YOUR TASK`: change a ConfigMap value, observe either (a) a rolling restart for A/B or (b) an in-place re-read for C. Capture the evidence.

> 💡 If you picked A, the hash must change when the ConfigMap **data** changes. A `helm upgrade` with no changes should NOT roll the pod. If both `helm upgrade --dry-run` runs produce the same annotation, you've done it right.

---

## How to Submit

```bash
git switch -c lab12
git add app_python/ k8s/lab10-app/ docs/LAB12.md
git commit -m "feat(lab12): configmaps + persistence with hot-reload strategy"
git push -u origin lab12
```

Open **two** PRs:

- `your-fork:lab12` → `course-repo:master` *(reviewed)*
- `your-fork:lab12` → `your-fork:master` *(merges into your own main)*

PR checklist:

```text
- [ ] Task 1 done — counter + /visits + DATA_DIR + atomic write + Compose persistence
- [ ] Task 2 done — two ConfigMaps, three patterns understood, decision table filled in
- [ ] Task 3 done — PVC bound, mounted, write→delete-pod→read proof captured
- [ ] Task 4 done — docs/LAB12.md complete with all five sections
- [ ] Bonus done — default behavior measured, strategy chosen + implemented + demonstrated
```

---

## Acceptance Criteria

### Task 1 (2 pts)
- ✅ `GET /` increments + persists; `GET /visits` returns current count
- ✅ `DATA_DIR` env var honored; atomic write used (temp + rename)
- ✅ Compose restart preserves the count (captured)

### Task 2 (3 pts)
- ✅ `files/config.json` + `lab10-app-file` ConfigMap (volume mount)
- ✅ `lab10-app-env` ConfigMap with ≥ 3 valid env-shaped keys (`envFrom`)
- ✅ Decision table filled in for each of the three example values, with reasoning
- ✅ Verification captures: file readable in pod, env vars present, `describe pod` shows the wiring

### Task 3 (3 pts)
- ✅ StorageClass inspection documented (which one, what provisioner, what `volumeBindingMode`)
- ✅ Access mode picked + justified (`ReadWriteOnce` is correct here — defend it)
- ✅ PVC reaches `Bound` (or `Pending` explained via `WaitForFirstConsumer`)
- ✅ **Write → delete pod → read from new pod, same marker, captured side by side**

### Task 4 (2 pts)
- ✅ All five sections in `docs/LAB12.md` complete with real captures (not illustrative)

### Bonus (2 pts)
- ✅ Default behavior measured: env var update delay + file update delay
- ✅ `subPath` trap explained in own words
- ✅ One strategy (A/B/C) chosen with written justification, implemented, demonstrated

---

## Rubric

| Task | Points | Criteria |
|------|-------:|----------|
| **Task 1** — App persistence | **2** | Counter + atomic write + Compose proof |
| **Task 2** — ConfigMaps | **3** | Two CMs, three-pattern understanding, decision table |
| **Task 3** — PVC | **3** | Right access mode, right size/SC, headline persistence proof |
| **Task 4** — Documentation | **2** | All five LAB12.md sections with real evidence |
| **Bonus** — Hot reload | **2** | Default behavior measured, strategy chosen + implemented + demonstrated |
| **Total** | **12** | 10 main + 2 bonus |

**Grading guide:**
- **10/10:** All four tasks; persistence proof is unambiguous (same marker in both pods); ConfigMap decisions are defended, not just chosen
- **8–9/10:** ConfigMaps + PVC work; persistence proof present but reasoning is thin or one pattern decision is wrong
- **6–7/10:** PVC `Bound` but no write→delete→read proof, OR only one ConfigMap pattern used
- **< 6:** No persistence proof, or ConfigMap not wired into the pod

---

## Resources

<details>
<summary>📚 Documentation</summary>

- [ConfigMaps](https://kubernetes.io/docs/concepts/configuration/configmap/) — concepts
- [Configure a Pod with a ConfigMap](https://kubernetes.io/docs/tasks/configure-pod-container/configure-pod-configmap/) — the three injection patterns
- [Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/) — PV/PVC/StorageClass
- [Storage Classes](https://kubernetes.io/docs/concepts/storage/storage-classes/) — `reclaimPolicy`, `volumeBindingMode`
- [Access Modes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#access-modes) — RWO/ROX/RWX/RWOP
- [Helm `.Files.Get`](https://helm.sh/docs/chart_template_guide/accessing_files/) — embed a file into a ConfigMap
- [local-path-provisioner](https://github.com/rancher/local-path-provisioner) — the default StorageClass in k3d

</details>

<details>
<summary>⚠️ Common Pitfalls (from real dry-runs — read these BEFORE you debug)</summary>

- **ConfigMap env vars don't refresh in a running pod.** Change `LOG_LEVEL` in the CM, `printenv` in the running pod still shows the old value — forever, until the pod restarts. This is the #1 "my ConfigMap update isn't working" cause. Env vars are baked at pod start; nothing changes that.
- **`subPath` mounts NEVER auto-update.** A `subPath: config.json` mount is a one-shot file copy at pod start. The ConfigMap can change every five seconds; the file in the container won't. Whole-directory mounts DO auto-update (within `kubelet --sync-frequency`, default 60s + cache TTL — total delay can be a couple of minutes). If you want hot reload, mount the whole dir.
- **`WaitForFirstConsumer` PVC stays `Pending` — that's normal, not an error.** The default StorageClass on k3d (and on most cloud SCs in multi-AZ clusters) waits to bind until a pod actually mounts the PVC, so the PV can be provisioned in the same zone as the pod. If your PVC is `Pending` and no pod has consumed it yet, just deploy the pod — don't try to "fix" the SC.
- **`kubectl exec ... Unknown stream id` is harmless.** Client-side websocket message from a benign control-frame mismatch. The data round-trips fine. Don't chase it.
- **Deleting a PVC may NOT delete the PV (or the data).** Depends on `reclaimPolicy`: `Delete` (default for cloud SCs) wipes the volume; `Retain` keeps the PV and the disk after the PVC is gone — you must clean up manually. Set `Retain` for anything you'd cry over losing, and write the cleanup runbook **before** the day you need it.
- **Invalid env-var names from `envFrom` are silently skipped.** A ConfigMap key `feature.x.enabled` won't appear as an env var — `envFrom` only emits keys matching `[A-Z_][A-Z0-9_]*`. No error, no warning, just missing.
- **`hostPath` for "real" persistence ties a pod to a node.** Demo only. Use a PVC even for local clusters — the local-path provisioner gives you a real PVC backed by a host directory, with proper rescheduling semantics.
- **Don't overwrite `/data/visits` with your marker.** Use a *separate* file (e.g. `/data/marker`) for the 3.5 persistence proof. The visit counter is rewriting `visits` on every `GET /`, which makes side-by-side comparison flaky.

</details>

<details>
<summary>🛠️ Useful CLI (no YAML — exec recipes only)</summary>

- `kubectl get sc` / `kubectl describe sc <name>` — what storage the cluster offers
- `kubectl describe pvc <name>` — check Events at the bottom when a PVC is stuck
- `kubectl describe pod <name> | grep -A4 'Mounts\|Volumes'` — what's actually mounted
- `kubectl exec <pod> -- mount | grep /data` — confirm the volume is mounted
- `kubectl get events --field-selector involvedObject.name=<pvc>` — provisioning errors
- For the persistence proof: write a marker with `kubectl exec deploy/<name> -- sh -c 'echo $(date +%s) > /data/marker'` (NOT `/data/visits` — the counter overwrites that), then `kubectl delete pod -l <selector>`, then `kubectl wait --for=condition=Ready pod -l <selector> --timeout=60s`, then `kubectl exec deploy/<name> -- cat /data/marker`

</details>

---

## Looking Ahead

| Lab | What it adds |
|---:|---|
| 13 | ArgoCD GitOps — your ConfigMap + PVC reconciled from git |
| 14 | Argo Rollouts — canary the new ConfigMap before all pods see it |
| 15 | StatefulSets + `volumeClaimTemplates` — one PVC *per* replica, for Postgres/Kafka |
| 16 | kube-prometheus-stack — scrape `/metrics` from your app, alert on visit-count regressions |

> **Remember:** the goal of the lab is not "PVC `Bound`". The goal is "the value I wrote in pod A came back from pod B after I deleted pod A." That's persistence. Everything else is plumbing.
