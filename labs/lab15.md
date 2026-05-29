# Lab 15 — StatefulSets & Persistent Storage

![difficulty](https://img.shields.io/badge/difficulty-advanced-red)
![topic](https://img.shields.io/badge/topic-StatefulSets-blue)
![points](https://img.shields.io/badge/points-10%2B2-orange)
![tech](https://img.shields.io/badge/tech-StatefulSet%20%7C%20PVC%20%7C%20K8s%201.36-informational)

> **Goal:** Run the workloads that *remember*. Give each pod a stable name and its own disk, prove the data on `web-1` follows `web-1` (not a random pod) across a `kubectl delete`.
> **Deliverable:** A PR from `lab15` converting your Lab 12 chart from a Deployment to a StatefulSet + headless Service, with `k8s/docs/LAB15.md` containing the per-pod-PVC persistence proof (write to `web-1`, kill `web-1`, read same value back; write to `web-0`, prove the values don't cross).

---

## Overview

Through Lab 14 every pod was disposable cattle — kill it, get a fresh one with a random name and an empty disk, nobody noticed. That breaks the moment a workload has to remember something *per pod* — a database replica, a queue partition, a search shard. A `Deployment` gives interchangeable pods with shared (or no) storage; a **StatefulSet** gives each pod a stable ordinal name, its own `PersistentVolumeClaim`, and an ordered lifecycle.

In this lab you will practice:

- **Writing a StatefulSet manifest from the API up** — `apiVersion`, `serviceName`, `replicas`, the label triangle, the pod template, and the `volumeClaimTemplates` list
- **Writing a headless Service from scratch** — and understanding *why* `clusterIP: None` is the thing that makes per-pod DNS exist
- The headline proof: **write a marker into `web-1`'s volume → `kubectl delete pod web-1` → read the marker back from the new `web-1` → it MATCHES** because `data-web-1` is bound to ordinal 1, not to the pod instance
- Cross-checking that `web-0`'s data is *its own*, not `web-1`'s — that's the second half of the proof

> ⚠️ **Scope:** k3d's default `local-path` StorageClass, one StatefulSet, three replicas, `ReadWriteOnce` access. No multi-AZ, no operators, no failover. The Bonus introduces update strategies — pick one of three paths.

> 🪨 **Pedagogical core.** Lab 12 proved a PVC survives a pod kill. That used **one shared PVC** for one Deployment replica. Lab 15 proves something deeper: with `volumeClaimTemplates`, each ordinal `N` is bound to its own PVC `data-<sts>-N`, and that binding is sticky across reschedule, restart, even node failure. **If only one capture survives, capture the write-delete-read on `web-1` showing the marker came back.**

---

## Project State

**You should have from previous labs:**

- Lab 9 — your `web` Deployment + Service on k3d (1.36) with 3 nodes
- Lab 10 — your `lab10-app` Helm chart
- Lab 11 — Secrets wired in
- Lab 12 — the `/visits` counter writing to `$DATA_DIR/visits`, with a PVC mounted at that path, and the write-delete-read persistence proof

**This lab adds (in your existing chart):**

- `templates/statefulset.yaml` — **you write** (replaces the Deployment for this lab; keep `deployment.yaml` in-tree but gate one off via values)
- `templates/service-headless.yaml` — **you write** (alongside the regular Service from Lab 9; both coexist)
- A small `values.yaml` change to flip from `Deployment` to `StatefulSet` and set `replicaCount: 3`
- `k8s/docs/LAB15.md` — your submission report

You **do not** remove the existing regular Service (the ClusterIP one from Lab 9). Keep both: the regular Service load-balances across pods for any client that doesn't care which one answers; the headless Service is for per-pod addressing.

> 📚 Pairs with **Lecture 15 — StatefulSets & Persistent Storage**. Re-read slides 5 (the three guarantees), 6–7 (headless Services + per-pod DNS), 8 (`volumeClaimTemplates`), and 19 (the orphaned-PVC trap) before you start.

---

## Setup

You need the k3d cluster from Lab 9 running on Kubernetes **1.36**, your `lab10-app` chart, and `kubectl`.

```bash
kubectl get nodes                       # k3d-devops-server-0 + 2 agents on v1.36.x
kubectl get storageclass                # local-path (default) — what your PVCs will use
helm list -n lab15 2>/dev/null
```

> 💡 The cluster note from Lab 12 still applies: k3d ships `local-path` (`rancher.io/local-path`) as the default `StorageClass`, marked `(default)`. It's RWO-only, dynamically-provisioned via hostPath under the hood, perfect for a 3-replica counter — and identical in *interface* to EBS / GCE PD / Ceph RBD in production, so the StatefulSet manifest you write here works unchanged on a real cluster.

Directory layout (you'll fill these files yourself):

```
lab10-app/                              # your Helm chart from Lab 10
├── templates/
│   ├── statefulset.yaml                # YOU write this (§Task 2)
│   ├── service-headless.yaml           # YOU write this (§Task 3)
│   ├── service.yaml                    # exists from Lab 9 — keep as-is
│   └── deployment.yaml                 # exists from Lab 9 — keep, gate behind values
└── values.yaml                         # add: kind toggle, replicaCount, persistence.*
k8s/docs/
└── LAB15.md                            # your submission report
```

---

## Task 1 — Concepts: When Identity & Per-Pod Storage Matter (2 pts)

Before you write a single line of YAML, write down *why* you're writing it. This task is documentation-only — answer in `k8s/docs/LAB15.md` (you'll extend the same file in every subsequent task).

`YOUR TASK`: in 2–3 sentences each, answer:

1. **The three guarantees.** What does a StatefulSet give you that a Deployment does not? Hint — the slide 5 list is: stable identity, stable storage, ordered lifecycle. Put them in **your own words** with one sentence each on *which kind of workload needs each one and why*.

2. **Why a Deployment is wrong for Postgres.** Pick **two** of: random pod names, shared (or no) PVC, parallel startup, pod IPs change on restart. For each one, write one sentence on the specific failure mode it causes in a Postgres cluster (lecture 15 slide 3 has the table).

3. **Headless Services.** Explain in your own words what `clusterIP: None` does to DNS, and why a StatefulSet *requires* a governing headless Service to address individual pods. (Hint: regular Service returns one VIP; headless returns N A records *plus* per-pod records.)

4. **When NOT to roll your own.** In 2-3 sentences, when would you stop using a raw StatefulSet and reach for an operator (e.g. CloudNativePG, Strimzi, Rook)? Hint: failover, coordinated backups, point-in-time restore.

`YOUR TASK`: fill in the Deployment vs StatefulSet comparison table in `LAB15.md`. The columns are given; the rows are yours to populate.

| Feature | Deployment | StatefulSet |
|---|---|---|
| Pod names | `YOUR TASK` | `YOUR TASK` |
| Storage | `YOUR TASK` | `YOUR TASK` |
| Scaling order | `YOUR TASK` | `YOUR TASK` |
| Network identity | `YOUR TASK` | `YOUR TASK` |
| Termination order | `YOUR TASK` | `YOUR TASK` |

### Proof of work

**Paste into `k8s/docs/LAB15.md`:**

- All four answers above, in your own words
- The completed comparison table
- One sentence applying the *operator rule of thumb* to your `visits` app: would *you* run it as a raw StatefulSet, or reach for an operator? Why?

---

## Task 2 — Convert the Deployment to a StatefulSet (3 pts)

The headline manifest. Below is the **skeleton** — the parts that are essentially the same as your Lab 10 Deployment template are filled in (chart helpers, container shape). The parts that *are the StatefulSet skill* — `replicas`, `selector.matchLabels`, the whole pod template body, and the entire `volumeClaimTemplates` block — are blank. Write them.

### 2.1 — Author `templates/statefulset.yaml`

```yaml
# lab10-app/templates/statefulset.yaml
apiVersion: apps/v1                                     # GA since K8s 1.9 — the only group/version
kind: StatefulSet
metadata:
  name: {{ include "lab10-app.fullname" . }}-web        # same `-web` component suffix as your Lab 10 Deployment;
                                                        # rendered name on the default release will be `lab10-app-web`,
                                                        # pods will be `lab10-app-web-0`, `lab10-app-web-1`, `lab10-app-web-2`.
  labels:
    {{- include "lab10-app.labels" . | nindent 4 }}
spec:
  serviceName: ___                                      # YOUR TASK: must equal the name of your headless Service in Task 3
                                                        #            ⚠️ if this is missing or wrong, the controller
                                                        #            still creates pods but per-pod DNS silently breaks
  replicas: ___                                         # YOUR TASK: how many ordinals do you need to
                                                        #            demonstrate per-pod identity AND prove the
                                                        #            data doesn't cross between pods?
  selector:
    matchLabels:
      ___: ___                                          # YOUR TASK: the label that matches pod template labels
                                                        #            AND the headless Service selector — immutable
  template:
    metadata:
      labels:
        ___: ___                                        # YOUR TASK: MUST equal selector.matchLabels above
    spec:
      containers:
        - name: app                                     # YOUR TASK: write the full container spec —
          # YOUR TASK: image, ports, env (DATA_DIR from Lab 12),
          # YOUR TASK: volumeMounts (data → /data, matching the volumeClaimTemplate name),
          # YOUR TASK: readinessProbe pointing at /health (cheap; not the visit counter).
          # The shape is identical to your Lab 10 Deployment container — copy that, then
          # change the volume name to match the volumeClaimTemplate you'll write below.
  volumeClaimTemplates:
    # YOUR TASK: the whole list. Each entry is a PVC template — it LOOKS like a normal PVC
    #            with metadata + spec, but it lives INSIDE the StatefulSet. The `metadata.name`
    #            becomes the PREFIX of the per-pod claim:  data-<sts>-0,  data-<sts>-1,  data-<sts>-2.
    #            Required fields:
    #              - metadata.name              (e.g. "data" — matches the volumeMount above)
    #              - spec.accessModes           (which one for one-Deployment-replica-style writes?)
    #              - spec.resources.requests.storage  (size — counter is one int)
    #              - spec.storageClassName      (optional; omit = use cluster default = local-path on k3d)
```

**Why each blank matters — read before filling:**

- **`spec.serviceName`** — the StatefulSet ↔ DNS bond. The controller uses this name to build the per-pod FQDN `<pod>.<serviceName>.<ns>.svc.cluster.local`. **A missing or wrong `serviceName` is a silent failure: pods still come up, but `kubectl exec web-0 -- getent hosts web-1.<wrong-svc>` returns nothing.** The StatefulSet docs literally call this field out as required.
- **`replicas`** — pick a number that lets you prove **two** things at once: (a) ordinal identity (need at least 2 to show `web-0 ≠ web-1`), and (b) per-pod PVC binding (the more pods, the more convincing the proof). The reference uses 3.
- **The label triangle** — same #1 K8s YAML error as Lab 9. `selector.matchLabels` must equal `template.metadata.labels`. The headless Service's `spec.selector` in Task 3 must match the *same* labels.
- **`volumeClaimTemplates`** — this is **not a PVC**, it is a *template* the controller stamps out one PVC per ordinal from. The block is **immutable after creation**. If you need to resize, you edit the PVCs directly (only works if the StorageClass has `allowVolumeExpansion: true`) — re-templating won't propagate. **Don't bury this in your head until later; lecture 15 slide 19 calls it the resizing trap.**
- **The container spec** — your `volumeMounts[].name` must equal the `volumeClaimTemplates[].metadata.name`. Mis-name them and the pod starts with `emptyDir` and zero error message — the writes just don't persist.

### 2.2 — Update `values.yaml` and gate the old Deployment

Add to `values.yaml`:

```yaml
# YOUR TASK: add the keys this lab needs. Required:
#   - a toggle that picks StatefulSet over Deployment (so deployment.yaml doesn't render)
#   - replicaCount (Task 2)
#   - persistence.size, persistence.storageClass (Task 2 volumeClaimTemplates)
# Suggested shape:
# kind: StatefulSet            # toggle: "StatefulSet" | "Deployment"
# replicaCount: ...
# persistence:
#   size: ...
#   storageClass: ""           # "" → cluster default = local-path on k3d
```

`YOUR TASK`: in `templates/deployment.yaml` (your Lab 10 file), wrap the whole thing in `{{- if eq .Values.kind "Deployment" }} ... {{- end }}` so it doesn't render when you flip the toggle. Do the same gate at the top of `statefulset.yaml` with `eq .Values.kind "StatefulSet"`. **Keep both files in-tree** — graders will check that you didn't delete history.

### 2.3 — Deploy and verify

```bash
helm upgrade --install lab10-app ./lab10-app -n lab15 --create-namespace
kubectl get statefulset -n lab15                # YOUR TASK: should show 3/3 READY
kubectl get pods -n lab15 -l app.kubernetes.io/name=lab10-app  # YOUR TASK: ordinal pods, NOT random suffixes
kubectl get pvc -n lab15                        # YOUR TASK: 3 PVCs named data-<sts>-0/1/2, all Bound
```

> 💡 **Debug ladder when this doesn't work first time:**
> 1. `kubectl describe statefulset <name>` — if the controller refuses to roll, the Events at the bottom name the field.
> 2. `kubectl get pvc` — `Pending` PVCs with `local-path` is **normal** (`WaitForFirstConsumer`); `Pending` PVCs without a pod consumer = wrong access mode or storage class.
> 3. `kubectl describe pod <name>-0` — bottom Events on a CrashLoopBackOff or never-starts.
> 4. **`spec.selector.matchLabels` is immutable** — if you got it wrong on first apply, `helm uninstall lab10-app -n lab15`, `kubectl delete pvc -n lab15 -l app.kubernetes.io/name=lab10-app`, then `helm upgrade --install` again.

### 2.4 — Proof of work

**Paste into `k8s/docs/LAB15.md`:**

- `kubectl get sts,pod,pvc -n lab15` — must show **3/3** ready, ordinal pod names, **3 PVCs** named `data-<sts>-0/1/2`, all `Bound`
- One sentence on which `accessModes` you chose for `volumeClaimTemplates` and why (`RWO` is correct here — defend it; `RWX` is wrong on local-path)
- One sentence on **why your `serviceName` value matches the headless Service name** in Task 3 (and what would break if it didn't)
- The relevant slice of your `statefulset.yaml` — the `volumeClaimTemplates` block specifically, so the grader can see how you defined the per-pod PVC

---

## Task 3 — Headless Service & Per-Pod DNS (2 pts)

This is where `clusterIP: None` earns its keep. A regular Service gets a virtual IP (one entry, kube-proxy load-balances). A **headless** Service has no IP at all — DNS returns the A records of *every* matching pod, *plus* per-pod records of the form `<pod>.<service>.<ns>.svc.cluster.local`. That second form is what makes pod-0 directly addressable in a way pod-1 can't impersonate.

### 3.1 — Author `templates/service-headless.yaml`

The skeleton below shows only the *kind* and `apiVersion` — every other field is yours.

```yaml
# lab10-app/templates/service-headless.yaml
apiVersion: v1                                          # Services live in core v1
kind: Service
metadata:
  name: ___                                             # YOUR TASK: must equal spec.serviceName from your StatefulSet
                                                        #            (Task 2). Pick a name that makes the per-pod FQDN
                                                        #            readable, e.g. <chart>-headless.
  labels:
    {{- include "lab10-app.labels" . | nindent 4 }}
spec:
  clusterIP: ___                                        # YOUR TASK: ONE specific value — the field is what makes this
                                                        #            Service "headless". A typo (e.g. an empty string,
                                                        #            or omitting the field) gives you a regular VIP
                                                        #            and silently defeats per-pod DNS.
  selector:
    ___: ___                                            # YOUR TASK: must match the StatefulSet pod template labels
                                                        #            EXACTLY — same label triangle as Task 2.
  ports:
    - ___                                               # YOUR TASK: the full port list — `name`, `port`, `targetPort`.
                                                        #            One entry pointing at your app's HTTP port. The
                                                        #            `port` field on a headless Service is informational
                                                        #            (no kube-proxy is involved), but you still need it
                                                        #            for DNS SRV records and for kubectl's port column.
```

**Why each blank matters:**

- **`metadata.name`** — this is the second half of the FQDN. Get it wrong and `serviceName` in the StatefulSet points at nothing → per-pod DNS broken, with no error from the StatefulSet controller (it doesn't validate that the Service exists).
- **`spec.clusterIP`** — the single field that distinguishes headless from regular. Spelled wrong / set to `""` / set to `192.x.x.x` and you get either a Service that won't apply or one that has a VIP and load-balances — which silently breaks the *whole point* of this lab. **There is exactly one valid value.**
- **`spec.selector`** — the third corner of the label triangle. `kubectl get endpoints <headless-svc>` is your debugging oracle: it must list the pod IPs of your StatefulSet pods. Empty list = selector typo.
- **`spec.ports`** — you still declare them. Headless Services don't load-balance, but kube-DNS uses the port name for SRV records (cluster-internal service discovery) and `kubectl get svc` shows `<none>` for ClusterIP only if you also forget the port.

### 3.2 — Apply and verify per-pod DNS

```bash
kubectl apply ...                                                # the `helm upgrade` from Task 2 already deployed it
kubectl get svc -n lab15                                         # YOUR TASK: confirm CLUSTER-IP column shows "None"
                                                                 #            for your headless Service
kubectl get endpoints <your-headless-svc> -n lab15               # YOUR TASK: MUST list 3 pod IPs (one per replica)
```

`YOUR TASK`: prove that the per-pod DNS record actually resolves. **busybox / your slim Lab 2 image may not ship `nslookup` or `dig`** — use one of these instead:

```bash
# Option A — getent (in glibc; works in most images, fails in busybox/alpine without bind-tools)
kubectl exec -n lab15 <pod-0> -- getent hosts <pod-1>.<headless>.lab15.svc.cluster.local

# Option B — throwaway debug pod with full networking tools
kubectl run net-debug --rm -it --image=nicolaka/netshoot --restart=Never -n lab15 -- \
  nslookup <pod-1>.<headless>.lab15.svc.cluster.local
```

Expect: a single A record matching `<pod-1>`'s current IP, with the FQDN pattern `<pod>.<headless>.<ns>.svc.cluster.local`. The name never changes for a given ordinal even if pod-1 is rescheduled to another node.

### 3.3 — Observe ordered startup

```bash
kubectl get pods -n lab15 -w                       # in one terminal — watch ordinal-by-ordinal startup
kubectl scale statefulset <name> -n lab15 --replicas=1   # in another — terminates -2 then -1 (reverse)
kubectl scale statefulset <name> -n lab15 --replicas=3   # back up — brings -1 then -2 in order
```

`YOUR TASK`: in `LAB15.md`, write 2–3 sentences on the default `OrderedReady` behaviour you observed, and one example of when `podManagementPolicy: Parallel` is appropriate (hint: Cassandra-style gossip clusters where every node is equal — most databases want the default).

### 3.4 — Proof of work

**Paste into `k8s/docs/LAB15.md`:**

- `kubectl get svc -n lab15` showing the headless Service with `CLUSTER-IP: None`, alongside your existing regular Service (so the grader sees both coexist)
- `kubectl get endpoints <headless> -n lab15` showing **3** pod IPs
- The per-pod DNS resolution output from §3.2, with the FQDN pattern called out
- The watched-pods capture from §3.3 (paste the relevant lines — ordinal 0 Ready before 1 starts; on scale-down, 2 terminates before 1)
- Your 2–3 sentences on `OrderedReady` vs `Parallel`

---

## Task 4 — Per-Pod PVC Persistence Proof (2 pts) ← **headline task**

This is the whole point of the lab. **A StatefulSet that runs is not the proof. The proof is:** write a unique marker into `web-1`'s volume, delete `web-1`, wait for the controller to recreate it, read the marker back from the **new** `web-1` — same value. Then write a *different* marker into `web-0`'s volume and show that the markers don't cross — `web-0`'s value is its own, not `web-1`'s.

### 4.1 — Write a per-pod marker

`YOUR TASK`: figure out the four steps yourself. Each one is a `kubectl exec` or `kubectl delete` — no manifest changes.

```bash
# YOUR TASK: write a UNIQUE marker (epoch seconds, your name, anything distinctive) into
#            web-1's mounted volume — into /data/marker, on web-1 only
#
# YOUR TASK: kubectl delete pod <sts>-1 -n lab15
#            (the StatefulSet controller will immediately reschedule it — same name,
#             possibly different node, same PVC reattached)
#
# YOUR TASK: kubectl wait --for=condition=Ready pod/<sts>-1 -n lab15 --timeout=60s
#            (so the next exec doesn't race the pod's startup)
#
# YOUR TASK: read /data/marker from the NEW <sts>-1 — assert it MATCHES the value you wrote
```

If the marker comes back the **same**, you've proven the headline guarantee: `data-<sts>-1` is bound to ordinal 1, not to the pod instance. The new pod inherited the old pod's PVC.

If the marker is **missing** (file not found) → your `volumeClaimTemplates` didn't mount at `DATA_DIR`, or you wrote to an `emptyDir` by accident (volume name mismatch — see Task 2 hints).

If the marker comes back **different / empty** → you're not using `volumeClaimTemplates`; you're using a shared PVC mounted twice, which is wrong for RWO.

### 4.2 — Prove the markers don't cross

`YOUR TASK`: write a **different** marker into `web-0`'s volume. Then read both back. Show that `web-0` has its own marker and `web-1` has its own — they are not the same. (This is the per-pod *isolation* half of the proof. Without it, you've only shown one pod's PVC survived, not that pod-N owns its own PVC.)

```bash
# YOUR TASK: write a DIFFERENT marker into <sts>-0 's /data/marker
# YOUR TASK: read /data/marker from <sts>-0 AND from <sts>-1
#            They must be DIFFERENT — each pod's marker is its own.
```

### 4.3 — One more sanity check — the visits counter

Your Lab 12 `/visits` counter now lives on a per-pod PVC. Drive traffic to each pod individually and show that the counters are *independent*:

```bash
kubectl port-forward -n lab15 pod/<sts>-0 8080:8080 &
kubectl port-forward -n lab15 pod/<sts>-1 8081:8080 &
# YOUR TASK: curl localhost:8080/visits   — pod-0's counter only
# YOUR TASK: curl localhost:8081/visits   — pod-1's counter only
# YOUR TASK: hit pod-0 a few extra times; pod-1's count must NOT change
```

### 4.4 — Proof of work

**Paste into `k8s/docs/LAB15.md` (this is the headline section — make it impossible to miss):**

- **The §4.1 capture**, side by side: `kubectl exec <sts>-1 -- cat /data/marker` (original) → `kubectl delete pod <sts>-1` → `kubectl wait ...` → `kubectl exec <sts>-1 -- cat /data/marker` (new pod, **same value**)
- **The §4.2 capture**: both pods' markers, clearly different values
- The §4.3 visit counter divergence — 2-3 curl outputs proving pod-0's count is decoupled from pod-1's
- One sentence on **why** this works (PVC bound to ordinal via `volumeClaimTemplates`, controller reattaches on reschedule)

---

## Task 5 — Documentation (1 pt)

Pull everything together into `k8s/docs/LAB15.md`. Required sections, in order:

1. **Concepts** — the four answers and the comparison table from Task 1
2. **Manifests** — short paragraphs on the choices you made in your `statefulset.yaml` and `service-headless.yaml`: which `accessModes`, which storage class, which `serviceName`, which `clusterIP`. Cite the *specific failure each would have caused* if you'd picked wrong.
3. **Resource inventory** — `kubectl get sts,pod,pvc,svc -n lab15` showing the StatefulSet, ordinal pods, per-ordinal PVCs, both Services (regular + headless)
4. **Network identity** — the per-pod DNS resolution from Task 3.2 with the FQDN pattern explained, plus the ordered startup/scale-down observation
5. **Per-pod PVC persistence proof** — the Task 4 captures: write-delete-wait-read on `web-1` with the same marker, plus the `web-0` vs `web-1` non-crossing check, plus the visits counter divergence
6. **Common pitfalls you hit** — at least one real one with how you debugged it (a `kubectl describe` line that unblocked you, a missing field, a typo)

> Keep all `kubectl`/`curl` output clearly marked as captured from your cluster. Do not paste output you didn't actually generate.

---

## Bonus Task — Update Strategies for Stateful Workloads (2 pts)

Upgrading the primary of a stateful cluster matters *far* more than swapping a stateless frontend — the cost of an automated mistake is "restore from backup". K8s gives you two strategies (`RollingUpdate` with `partition`, and `OnDelete`), and the broader ecosystem gives you a third (operators that handle upgrades for you).

**The problem:** you need to canary a stateful workload — upgrade *one* pod first, validate, then roll forward. A naive `RollingUpdate` of a Deployment ships the new image to every replica with no human gate.

**The task:** pick **one** of three paths below and implement it. Each is worth the full 2 points. Don't ship YAML you copied from a tutorial — research the strategy, decide why you picked it over the others, document the trade-off.

### Path A — `RollingUpdate` with `partition`

The `partition` field is the StatefulSet equivalent of a canary. Pods with ordinal `>= partition` get the new pod template; the rest stay on the old one. You decrement `partition` to roll the update forward.

`YOUR TASK`:

1. Add `spec.updateStrategy` to your StatefulSet. Pick `type: RollingUpdate` with `rollingUpdate.partition` set to your **highest ordinal** so only the top pod updates when you change the image.
2. Change `image.tag` in `values.yaml` to a new version (rebuild your Lab 2 image with a fresh tag, or temporarily change the container `name:` — anything that makes the pod template hash different).
3. `helm upgrade ...`. Verify that *only* the highest-ordinal pod restarts on the new template. The others stay on the old one.
4. Walk `partition` down (highest → ... → 0) re-applying each time, and capture the rollout progress between each step.

You write the YAML. No skeleton.

### Path B — `OnDelete`

`type: OnDelete` is the "the controller does *nothing* on a spec change; humans drive the rollout" mode — what most production database upgrades actually look like.

`YOUR TASK`:

1. Add `spec.updateStrategy.type: OnDelete` to your StatefulSet.
2. Change `image.tag` and `helm upgrade ...`. Verify that **no pods restart**. The controller is intentionally inert.
3. `kubectl delete pod <sts>-2` (or whichever ordinal you want to update first). Show that *only that pod* comes back on the new template. The others remain on the old one until you delete them too.
4. Document one real-world scenario where `OnDelete` is the right answer (hint: strict change windows; coordinated DB primary/replica upgrades where a human checks replication lag between each step).

You write the YAML. No skeleton.

### Path C — A database operator

Drop the hand-rolled StatefulSet for one stateful workload and run it via a purpose-built operator instead. Document what the operator does that your raw StatefulSet could not.

`YOUR TASK`:

1. Install **one** operator: **CloudNativePG** (PostgreSQL), **Strimzi** (Kafka), or a storage operator like **Rook** (Ceph) / **Longhorn**.
2. Declare a Custom Resource (e.g. CloudNativePG `kind: Cluster` with `instances: 3`).
3. Observe that the operator *itself* creates the underlying StatefulSet + Services + PVCs — `kubectl get sts,svc,pvc -n <op-ns>` after applying the CR.
4. Document the value-add in `LAB15.md`: automatic primary election + failover, continuous WAL or topic backups, coordinated rolling upgrades, bundled `PodMonitor` metrics — none of which a raw StatefulSet provides.

### Proof of work (whichever path you picked)

**Paste into `k8s/docs/LAB15.md`:**

- The updated manifest snippet (your `updateStrategy` block, or your CR YAML for Path C)
- The `kubectl rollout status` / `kubectl get pods -w` capture showing the partial rollout (Paths A & B), or the operator-managed `kubectl get sts,svc,pvc` (Path C)
- **One paragraph** on *why* you picked this path over the other two — the trade-offs, what your `visits` app actually needs, what production tooling you would consider next

---

## How to Submit

```bash
git switch -c lab15
git add lab10-app/ k8s/docs/LAB15.md
git commit -m "feat(lab15): convert chart to StatefulSet with per-pod PVCs + headless Service"
git push -u origin lab15
```

Open **two** PRs:

- `your-fork:lab15` → `course-repo:master` *(reviewed)*
- `your-fork:lab15` → `your-fork:master` *(merges into your own main)*

PR checklist:

```text
- [ ] Task 1 done — concepts, comparison table, operator rule-of-thumb in LAB15.md
- [ ] Task 2 done — StatefulSet with serviceName + replicas + label triangle + volumeClaimTemplates, 3 ordinal pods + 3 Bound per-pod PVCs
- [ ] Task 3 done — headless Service with clusterIP: None, per-pod DNS resolution captured, ordered startup observed
- [ ] Task 4 done — write→delete-pod→read SAME marker on web-1; web-0 marker is its own; visits counters independent per pod
- [ ] Task 5 done — LAB15.md with all 6 sections + real evidence
- [ ] Bonus done — Path A (partition) OR Path B (OnDelete) OR Path C (operator) with justification
```

---

## Acceptance Criteria

### Task 1 — Concepts (2 pts)
- ✅ Three StatefulSet guarantees described in your own words
- ✅ Two specific Deployment failure modes for Postgres explained
- ✅ Headless Service (`clusterIP: None`) DNS behaviour explained
- ✅ "When to use an operator" note included
- ✅ Comparison table filled in (all five rows)

### Task 2 — Convert to StatefulSet (3 pts)
- ✅ `templates/statefulset.yaml` written by hand
- ✅ `spec.serviceName` set and matches the headless Service name from Task 3
- ✅ Label triangle consistent (selector.matchLabels = template labels = headless Service selector)
- ✅ `replicas: 3` (or justified higher); pods named `<name>-0/1/2`
- ✅ `volumeClaimTemplates` block written; per-pod PVCs render as `data-<name>-N` and **all three Bound**
- ✅ Container `volumeMounts[].name` matches `volumeClaimTemplates[].metadata.name`
- ✅ Old `deployment.yaml` gated behind values, not deleted

### Task 3 — Headless Service & Lifecycle (2 pts)
- ✅ `templates/service-headless.yaml` written by hand
- ✅ `spec.clusterIP: None` set (not omitted, not "")
- ✅ Selector matches the StatefulSet pod labels exactly
- ✅ Regular Service (Lab 9) coexists, not deleted
- ✅ Per-pod DNS resolution captured with FQDN pattern visible
- ✅ Ordered startup / reverse-order scale-down observed

### Task 4 — PVC persistence proof (2 pts)
- ✅ **`web-1` marker survives `kubectl delete pod web-1`** — same value before and after, captured side by side
- ✅ **`web-0`'s marker is its own** — different from `web-1`'s
- ✅ Visit counters independent per pod
- ✅ One-sentence "why this works" referencing `volumeClaimTemplates` + ordinal binding

### Task 5 — docs (1 pt)
- ✅ All 6 sections in `k8s/docs/LAB15.md`; real CLI captures (not illustrative)
- ✅ Pitfalls section includes at least one real one you hit

### Bonus — Update Strategies / Operator (2 pts)
- ✅ Exactly one path implemented (A / B / C)
- ✅ YAML written by you, not copy-pasted from a tutorial
- ✅ Proof captures match the path (partition decrement, manual delete, or operator-managed resource list)
- ✅ Paragraph on *why this path over the other two*

---

## Rubric

| Task | Points | Criteria |
|------|-------:|----------|
| **Task 1** — Concepts | **2** | Guarantees, comparison table, headless DNS, operator rationale |
| **Task 2** — StatefulSet | **3** | Hand-written `statefulset.yaml` with serviceName + label triangle + volumeClaimTemplates; 3 ordinal pods + 3 Bound PVCs |
| **Task 3** — Headless Service & lifecycle | **2** | Hand-written headless Service (`clusterIP: None`); per-pod DNS proven; ordered start observed |
| **Task 4** — Persistence proof | **2** | `web-1` marker survives delete; `web-0` ≠ `web-1`; per-pod isolation proven |
| **Task 5** — Documentation | **1** | Six sections in `LAB15.md` with real evidence |
| **Bonus** — Update strategies / operator | **2** | One of three paths implemented, defended in writing |
| **Total** | **12** | 10 main + 2 bonus |

**Grading scale (main 10 pts):**

- **10/10:** All resources correct, per-pod PVC binding proven on `web-1`, non-crossing demonstrated on `web-0`, documentation excellent
- **8-9/10:** Works end-to-end; minor gaps in evidence or one weak explanation
- **6-7/10:** StatefulSet deploys but persistence proof is thin (only one half — survives delete OR per-pod isolation, not both)
- **<6/10:** Missing headless Service, broken `volumeClaimTemplates`, or no persistence proof

---

## Resources

<details>
<summary>📚 Kubernetes documentation</summary>

- [StatefulSets — concepts](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
- [StatefulSet Basics tutorial](https://kubernetes.io/docs/tutorials/stateful-application/basic-stateful-set/)
- [Headless Services](https://kubernetes.io/docs/concepts/services-networking/service/#headless-services)
- [Volume claim templates](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/#volume-claim-templates)
- [Update strategies & partition rollout](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/#update-strategies)
- [Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)
- [DNS for Services and Pods (per-pod records)](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/#pods)

</details>

<details>
<summary>🤖 Operators & cloud-native storage</summary>

- [Operator pattern](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/) · [OperatorHub.io](https://operatorhub.io/)
- [CloudNativePG](https://cloudnative-pg.io/) — the PostgreSQL operator (1.29, PG 18.3 default)
- [Strimzi](https://strimzi.io/) — Kafka on Kubernetes
- [Rook](https://rook.io/) — production storage on Ceph (v1.18 + Ceph 19 Squid)
- [Longhorn](https://longhorn.io/) — lightweight CNCF block storage (1.9)

</details>

<details>
<summary>⚠️ Common Pitfalls (from real dry-runs — read these BEFORE you debug)</summary>

- **Missing or wrong `spec.serviceName`.** The StatefulSet controller does **not** fail the apply — it happily creates pods with ordinal names, but per-pod DNS silently breaks because the `<pod>.<serviceName>` FQDN points at no Service. Symptom: pods Ready, but `kubectl exec web-0 -- getent hosts web-1.<wrong>` returns nothing. **Always pair the StatefulSet apply with the matching headless Service apply, and grep both files for the name match before committing.**

- **`clusterIP: None` typo'd or omitted.** A regular Service with `clusterIP: <some-vip>` has the same shape as a headless one except for that single field. Drop it or set it to `""` and you get a regular VIP that load-balances — which silently defeats per-pod DNS, the whole point of this lab. There is **exactly one valid value**: the literal string `None`.

- **`volumeClaimTemplates` PVCs persist after StatefulSet deletion — the bill-shock trap.** This is deliberate (your data outlives mistakes). It also means: `helm uninstall lab10-app -n lab15` leaves three PVCs sitting around, billing real money on a cloud StorageClass, with no obvious owner. Clean them up explicitly: `kubectl delete pvc -n lab15 -l app.kubernetes.io/name=lab10-app`. **The same trap applies when you fix the immutable `volumeClaimTemplates` block: `helm uninstall` does NOT wipe the PVCs; the next `helm install` may end up with mismatched claims.**

- **Ordered pod startup blocks rolling updates when one pod fails liveness.** Default `podManagementPolicy: OrderedReady` means pod-N waits for pod-(N-1) to be Ready before starting. A wedged pod-0 → pods 1, 2, ... never start. Symptom looks like "the StatefulSet is stuck"; root cause is **always** in pod-0's logs/events. Don't reach for `Parallel` to bypass — fix pod-0. Use `Parallel` only when the app's discovery is gossip-based and every node is equal (Cassandra-style).

- **busybox / slim images lack `nslookup` and `dig`.** Your Lab 2 Python image probably doesn't ship them either. Two clean ways to prove per-pod DNS without bloating the app image:
  - `kubectl exec <pod> -- getent hosts <fqdn>` — works if the image has glibc (most non-busybox bases do)
  - `kubectl run net-debug --rm -it --image=nicolaka/netshoot --restart=Never -- nslookup <fqdn>` — throwaway debug pod with full tools

- **`volumeClaimTemplates` is immutable after creation.** Lecture 15 slide 19 calls this the resizing trap. Edit the block in your chart, `helm upgrade`, and the StatefulSet controller silently ignores the change. To actually resize: `kubectl edit pvc data-<sts>-N` for each ordinal — and only if the StorageClass has `allowVolumeExpansion: true` (the k3d `local-path` default *does* support it; many cloud SCs do too). For deeper changes (storage class, access mode) you must `kubectl delete sts --cascade=orphan` and re-apply with the new template — your PVCs survive the orphan delete.

- **Label triangle drift.** Three places to keep in sync: `StatefulSet.spec.selector.matchLabels`, `StatefulSet.spec.template.metadata.labels`, and `Service.spec.selector` (on both the regular AND headless Services). The selector is **immutable after creation**. If you got it wrong, `helm uninstall`, `kubectl delete pvc -l ...`, then `helm install` — `kubectl edit` won't save you.

- **Confusing `serviceName` with the regular Service.** Your StatefulSet's `serviceName` field points at the **headless** Service, not at the regular ClusterIP Service from Lab 9. They are different Services with different selectors satisfied by the same pods. The regular Service is for `curl http://web/` from anywhere in the cluster (load-balanced). The headless Service is for `curl http://web-0.web-headless/` to address a specific pod.

</details>

<details>
<summary>🛠️ Useful CLI (no YAML — recipes only)</summary>

```bash
# Inspect what the cluster offers before you write YAML
kubectl get storageclass
kubectl get sc local-path -o yaml | grep -E 'provisioner|reclaimPolicy|volumeBindingMode|allowVolumeExpansion'

# The four together tell the whole StatefulSet story
kubectl get sts,pod,pvc,svc -n lab15

# Confirm per-pod PVC binding (the headline)
kubectl get pvc -n lab15 -l app.kubernetes.io/name=lab10-app
# Expect: data-<sts>-0, data-<sts>-1, data-<sts>-2 — all Bound

# Per-pod DNS without nslookup
kubectl exec -n lab15 <sts>-0 -- getent hosts <sts>-1.<headless>.lab15.svc.cluster.local
# Or with full tooling:
kubectl run net-debug --rm -it --image=nicolaka/netshoot --restart=Never -n lab15 -- bash

# Persistence proof (Task 4)
kubectl exec -n lab15 <sts>-1 -- sh -c 'echo "MARKER-$(date +%s)" > /data/marker'
kubectl exec -n lab15 <sts>-1 -- cat /data/marker
kubectl delete pod -n lab15 <sts>-1
kubectl wait --for=condition=Ready pod/<sts>-1 -n lab15 --timeout=60s
kubectl exec -n lab15 <sts>-1 -- cat /data/marker   # MUST match the value above
```

</details>

---

## Looking Ahead

| Lab | What it adds to this stack |
|---:|---|
| 16 | **kube-prometheus-stack** — scrape per-pod metrics from your StatefulSet via a `ServiceMonitor` |
| 17 *(bonus)* | **Cloudflare Workers** — when the cluster is overkill: V8 isolates, instant cold-start |
| 18 *(bonus)* | **Nix** — reproducible builds and dev shells without a container in sight |

---

**Good luck!** 💾

> **Remember:** StatefulSets are *managed pets* — stable identity + per-pod storage. The whole lab boils down to one capture: write a marker to `web-1`, delete `web-1`, read the marker back from the new `web-1` — same value, because `data-web-1` was bound to ordinal 1, not to the pod that lived there. If only one capture survives the lab, make it that one.
