# Lab 15 — StatefulSets & Persistent Storage

![difficulty](https://img.shields.io/badge/difficulty-advanced-red)
![topic](https://img.shields.io/badge/topic-StatefulSets-blue)
![points](https://img.shields.io/badge/points-10%2B2-orange)
![tech](https://img.shields.io/badge/tech-StatefulSet%20%7C%20PVC-informational)

> Run the workloads that *remember*. Give each pod a stable identity and its own disk, then prove the data survives a pod kill.

## Overview

Through Lab 14 every pod you ran was disposable cattle: kill it, get a fresh one with a random name and an empty disk, nobody noticed. That breaks the moment a workload has to remember something between requests — a database, a queue, a search cluster. A `Deployment` gives interchangeable pods with shared (or no) storage; a **StatefulSet** gives each pod a stable name, its own `PersistentVolumeClaim`, and an ordered lifecycle.

In this lab you convert your Lab 12 Helm chart from a `Deployment` to a `StatefulSet`, add a headless `Service` for per-pod DNS, wire up `volumeClaimTemplates` so each pod owns its disk, and demonstrate that pod `app-0`'s visit counter is independent from `app-1`'s and survives a pod deletion.

**What You'll Learn:**
- StatefulSet vs Deployment: the three guarantees and when each one matters
- Stable network identity and ordinal pod naming (`app-0`, `app-1`, …)
- Headless Services (`clusterIP: None`) and per-pod DNS resolution
- `volumeClaimTemplates` for automatic per-pod persistent storage
- Ordered (`OrderedReady`) vs `Parallel` pod management
- (Bonus) Update strategies — `RollingUpdate` with `partition`, and `OnDelete` — or reaching for a database operator

**Building On:** Your Helm chart with the `/visits` counter from Lab 12. StatefulSets serve a *different* purpose than the Argo Rollouts you built in Lab 14: Rollouts are for progressive delivery of *stateless* apps; StatefulSets are for *stateful* apps that need identity and storage.

**Tech Stack:** Kubernetes **1.36 "Haru"** | Helm **4** | StatefulSet (`apps/v1`) | Headless Service | `volumeClaimTemplates` | PersistentVolumes

> **Cluster note:** Your k3d cluster on K8s 1.36 ships a default `StorageClass` (the local-path-provisioner) that dynamically provisions PVs. That is all this lab needs — production swaps in an EBS / GCE PD CSI driver, or a storage layer like Rook-Ceph or Longhorn. The principles transfer unchanged.

---

## Tasks

### Task 1 — StatefulSet Concepts (2 pts)

**Objective:** Explain *why* a StatefulSet exists and when to choose it over a Deployment.

This task is documentation-only — no manifests yet. Write your answers into `k8s/STATEFULSET.md` (you will extend this file in Task 5).

**Requirements:**

1. **The three guarantees.** In your own words, describe what a StatefulSet gives you that a Deployment does not:
   - Stable, unique network identity (ordinal pod names that survive reschedule)
   - Stable, persistent per-pod storage (one PVC per ordinal)
   - Ordered, graceful deployment, scaling, and termination

2. **Deployment vs StatefulSet.** Fill in a comparison table (template in the hints) and give two concrete examples of stateful workloads and *why* a Deployment would hurt them.

3. **Headless Services.** Explain what `clusterIP: None` does to DNS and why a StatefulSet *requires* a governing headless Service to address individual pods.

4. **When NOT to roll your own.** In 2-3 sentences, say when you would stop using a raw StatefulSet and reach for an operator (e.g. CloudNativePG for PostgreSQL, Strimzi for Kafka, Rook for storage). Hint: failover, coordinated backups, point-in-time restore.

<details>
<summary>💡 Hints</summary>

**Stateful workload examples:** databases (PostgreSQL, MySQL, MongoDB), message queues (Kafka, RabbitMQ), distributed stores (Elasticsearch, Cassandra), and caches with a warm working set.

**Why a Deployment is wrong for Postgres:**
- Random pod names → a replica can't tell *which* pod is the primary.
- Shared / no PVC → two processes writing the same WAL = corruption.
- Parallel startup → bootstrap election races and split-brain.
- Pod IPs change on restart → replica connection strings break mid-stream.

**Comparison table to complete:**

| Feature | Deployment | StatefulSet |
|---------|------------|-------------|
| Pod names | Random suffix (`web-7b9c4-x4f2k`) | Ordinal index (`app-0`, `app-1`) |
| Storage | Shared PVC / none | Per-pod PVC via `volumeClaimTemplates` |
| Scaling order | Any order, parallel | Ordered (`0 → 1 → 2`) by default |
| Network identity | Random, via Service VIP | Stable per-pod DNS name |
| Termination | Any order | Reverse ordinal (highest first) |

**Headless Service DNS:** a `Service` with `clusterIP: None` makes cluster DNS return the A records of *every* matching pod instead of one virtual IP, and creates a per-pod record:
```
<pod-name>.<headless-service>.<namespace>.svc.cluster.local
# e.g. app-0.app-headless.default.svc.cluster.local
```

**Operator rule of thumb:** *if you'd page yourself at 3 AM for that database's failure, run it with an operator, not a raw StatefulSet.* A StatefulSet gives identity + storage; an operator (shipped as CRDs + a controller) adds failover, backups, restore, and upgrade choreography.

**Resources:**
- [StatefulSet concepts](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
- [StatefulSet Basics tutorial](https://kubernetes.io/docs/tutorials/stateful-application/basic-stateful-set/)
- [Operator pattern](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/)

</details>

---

### Task 2 — Convert the Deployment to a StatefulSet (3 pts)

**Objective:** Transform your Helm chart so the app runs as a StatefulSet with per-pod storage instead of a Deployment.

**Requirements:**

1. **Add a StatefulSet template.** Create `templates/statefulset.yaml` in your chart (keep the old `deployment.yaml`/`rollout.yaml` in the repo for reference, but don't render both — gate one behind a values flag or remove it from rendering).
   - Set `serviceName` to point at your headless Service.
   - Reuse the same pod template (container, image, ports, probes) you already had.
   - Mount the per-pod volume into your app's data directory (e.g. `/data`).

2. **Configure `volumeClaimTemplates`.** Add a `volumeClaimTemplates` block so each pod ordinal gets its own PVC automatically. Make the storage size and (optional) storage class configurable via `values.yaml`.

3. **Set `replicas: 3`** so you have three distinct ordinals to test with.

4. **Deploy and verify** that pods are named with ordinal suffixes (`<name>-0`, `<name>-1`, `<name>-2`) and that each pod has its own bound PVC.

**Manifest skeleton** (fill in every `# YOUR-TASK:` marker):

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: {{ include "mychart.fullname" . }}
  labels:
    {{- include "mychart.labels" . | nindent 4 }}
spec:
  serviceName: {{ include "mychart.fullname" . }}-headless   # must match the headless Service name
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "mychart.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "mychart.selectorLabels" . | nindent 8 }}
    spec:
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          ports:
            - name: http
              containerPort: {{ .Values.service.targetPort }}
          volumeMounts:
            - name: data
              mountPath: # YOUR-TASK: where your app writes the visits file (e.g. /data)
          readinessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 3
            periodSeconds: 5
  volumeClaimTemplates:
    - metadata:
        name: data                       # PVCs render as data-<name>-0, data-<name>-1, ...
      spec:
        accessModes: [ "ReadWriteOnce" ]
        # YOUR-TASK: set storageClassName from values (omit to use the cluster default)
        resources:
          requests:
            storage: {{ .Values.persistence.size | default "1Gi" }}
```

<details>
<summary>💡 Hints</summary>

**Make sure your app actually writes to the mounted path.** The Lab 12 `/visits` counter must persist to a file under the `mountPath` you chose (e.g. `/data/visits`), not to an in-memory variable — otherwise there is no per-pod state to demonstrate.

**`volumeClaimTemplates` immutability:** the block is **immutable after creation**. If you need to change the storage size later you edit the PVCs directly (and only if the `StorageClass` has `allowVolumeExpansion: true`) — re-templating won't propagate.

**Values you'll likely add:**
```yaml
replicaCount: 3
persistence:
  size: 1Gi
  storageClassName: ""   # "" → use cluster default StorageClass
```

**Verify (output illustrative — yours will differ):**
```bash
helm upgrade --install myapp ./mychart
kubectl get statefulset
kubectl get pods            # expect myapp-0, myapp-1, myapp-2 in order
kubectl get pvc             # expect data-myapp-0, data-myapp-1, data-myapp-2, all Bound
```

</details>

---

### Task 3 — Headless Service & Ordered Lifecycle (2 pts)

**Objective:** Give the StatefulSet its governing headless Service, confirm ordered startup, and explain `OrderedReady` vs `Parallel`.

**Requirements:**

1. **Create a headless Service.** Add `templates/service-headless.yaml` with `clusterIP: None`, selecting the same pod labels as your StatefulSet. Keep your existing regular Service (the one with a ClusterIP) for normal in-cluster / external access — the two coexist.

2. **Verify per-pod DNS.** Exec into a pod and resolve another pod by its stable DNS name. Capture the output. Confirm the FQDN pattern `<pod>.<headless-service>.<namespace>.svc.cluster.local`.

3. **Observe ordered deployment.** Watch the pods come up and document that pod-N only starts after pod-(N-1) is Ready. Then scale to 1 and back to 3, noting that scale-down terminates the *highest* ordinal first.

4. **Explain `podManagementPolicy`.** In `STATEFULSET.md`, describe the default `OrderedReady` behaviour and give one example where `Parallel` (start all pods at once) would be appropriate.

**Manifest skeleton:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "mychart.fullname" . }}-headless
  labels:
    {{- include "mychart.labels" . | nindent 4 }}
spec:
  clusterIP: None                        # the magic — no virtual IP, per-pod DNS records
  selector:
    {{- include "mychart.selectorLabels" . | nindent 4 }}   # must match the STS pod labels
  ports:
    - name: http
      port: {{ .Values.service.port }}
      targetPort: http
```

<details>
<summary>💡 Hints</summary>

**DNS resolution test (output illustrative):**
```bash
# K8s 1.36 minimal images may lack nslookup; use getent or a debug pod if needed
kubectl exec myapp-0 -- nslookup myapp-1.myapp-headless
# or, no nslookup available:
kubectl exec myapp-0 -- getent hosts myapp-1.myapp-headless.default.svc.cluster.local
```
Expect a single A record matching pod-1's current IP. The name never changes for a given ordinal, even if pod-1 is rescheduled to another node.

**Watch ordered startup:**
```bash
kubectl get pods -w        # -0 reaches Ready before -1 starts; -1 before -2
kubectl scale statefulset myapp --replicas=1   # terminates -2 then -1 (reverse order)
kubectl scale statefulset myapp --replicas=3   # brings -1 then -2 back, in order
```

**`Parallel` example:** a Cassandra-style cluster where every node is equal and discovery is via gossip (not "find pod-0 first") can use `spec.podManagementPolicy: Parallel` to start all pods simultaneously. Most databases want the default `OrderedReady` so the primary bootstraps before replicas join.

**Apply order gotcha:** apply the headless Service *before* (or together with) the StatefulSet. A missing or mis-selectored headless Service silently breaks per-pod DNS while pods still appear healthy.

</details>

---

### Task 4 — Per-Pod Storage & Persistence Proof (2 pts)

**Objective:** Prove the storage is genuinely per-pod and survives a pod kill — the whole point of a StatefulSet.

**Requirements:**

1. **Isolation.** Drive traffic to each pod individually and show that the visit counters are *independent* (hitting `app-0` does not change `app-1`'s count).

2. **Persistence across pod deletion.** Note pod-0's count, `kubectl delete pod <name>-0`, wait for the StatefulSet to recreate it, and show the *same* count comes back — because the PVC `data-<name>-0` was reattached to the rescheduled pod.

3. **Capture evidence** of both for your documentation in Task 5.

<details>
<summary>💡 Hints</summary>

**Hit each pod directly (output illustrative):**
```bash
kubectl port-forward pod/myapp-0 8080:8000 &
kubectl port-forward pod/myapp-1 8081:8000 &
curl localhost:8080/visits      # increments only pod-0's counter
curl localhost:8081/visits      # increments only pod-1's counter
```

**Persistence test (output illustrative):**
```bash
kubectl exec myapp-0 -- cat /data/visits      # e.g. 5
kubectl delete pod myapp-0                     # controller recreates it, same PVC
kubectl wait --for=condition=Ready pod/myapp-0 --timeout=60s
kubectl exec myapp-0 -- cat /data/visits      # still 5 — data survived
```

**Why the data survives:** PVCs created from `volumeClaimTemplates` are bound to the *ordinal*, not the pod instance. When `myapp-0` is rescheduled, the controller reattaches `data-myapp-0`. Those PVCs are also **deliberately retained on scale-down and on StatefulSet deletion** — your data outlives mistakes. Clean them up manually (`kubectl delete pvc data-myapp-{0..2}`) when you truly retire the workload.

</details>

---

### Task 5 — Documentation (1 pt)

**Objective:** Pull everything together into one reviewable document.

**Create / complete `k8s/STATEFULSET.md` with:**

1. **Concepts (from Task 1)** — the three guarantees, the Deployment-vs-StatefulSet table, headless Services, and the "when to use an operator" note.
2. **Resource inventory** — output of `kubectl get sts,pod,pvc,svc` showing the StatefulSet, ordinal pods, per-ordinal PVCs, and both Services (regular + headless). *Label real command output as captured from your cluster.*
3. **Network identity** — your DNS resolution output and the FQDN pattern, plus a note on ordered startup behaviour and `OrderedReady` vs `Parallel`.
4. **Per-pod storage evidence** — the independent visit counts across pods.
5. **Persistence proof** — the before/delete/after counts showing data survived a pod kill, with a one-line explanation of *why* (PVC bound to ordinal).

> Keep `kubectl`/`curl` output clearly marked as captured from your own cluster. Do not paste output you didn't actually generate.

---

## Bonus Task — Update Strategies (2 pts)

**Objective:** Control *how* a StatefulSet rolls out a new pod template. Upgrading the primary of a stateful cluster matters far more than swapping a stateless frontend, so K8s gives you two strategies. Pick **one** of the two paths below (either earns the full 2 pts).

### Path A — `RollingUpdate` with `partition` + `OnDelete`

1. **Partitioned canary.** Set `updateStrategy.type: RollingUpdate` with a `rollingUpdate.partition` equal to your highest ordinal so that only the top pod updates when you change the image. Validate it, then walk `partition` down (`2 → 1 → 0`) to roll the upgrade forward across the cluster.

2. **`OnDelete` strategy.** Switch to `updateStrategy.type: OnDelete`, change the pod template, and show that *nothing* happens until you manually `kubectl delete` a pod — the controller only updates the pod you delete. Document one real use case (strict change windows, coordinated DB upgrades where a human must be in the loop).

```yaml
spec:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 2        # only ordinals >= 2 get the new template (your canary)
---
spec:
  updateStrategy:
    type: OnDelete        # controller waits; you delete pods to trigger the update
```

### Path B — Database Operator

Replace the hand-rolled StatefulSet with a purpose-built operator for one stateful workload and explain what the operator does that your StatefulSet could not.

1. Install one operator — **CloudNativePG** (PostgreSQL), **Strimzi** (Kafka), or a storage operator like **Rook** (Ceph) / **Longhorn**.
2. Declare a Custom Resource (e.g. CloudNativePG `kind: Cluster` with `instances: 3`) and observe that the operator *itself* creates the underlying StatefulSet, Services, and PVCs.
3. Document the value-add: automatic primary election / failover, continuous WAL or topic backups, coordinated rolling upgrades, and bundled `PodMonitor` metrics — none of which a raw StatefulSet provides.

<details>
<summary>💡 Hints</summary>

**Partition mental model:** pods with ordinal `>= partition` receive the new template; the rest stay on the old one. `partition` is the StatefulSet equivalent of a canary. Set it *back* to a high number and re-apply the old image to roll back.

```bash
# Path A — drive the partition down to roll forward (output illustrative)
kubectl patch statefulset myapp --type merge \
  -p '{"spec":{"updateStrategy":{"rollingUpdate":{"partition":1}}}}'
kubectl rollout status statefulset/myapp
```

**Path B — CloudNativePG taste (illustrative):**
```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: app-db
spec:
  instances: 3            # 1 primary + 2 replicas; operator manages failover
  storage:
    size: 5Gi
```
```bash
kubectl get cluster,sts,pod,pvc      # the operator created the STS for you
```

**Resources:**
- [Update strategies & partitioned rollout](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/#update-strategies)
- [CloudNativePG](https://cloudnative-pg.io/) · [Strimzi](https://strimzi.io/) · [Rook](https://rook.io/) · [Longhorn](https://longhorn.io/)

</details>

---

## How to Submit

1. **Create a branch:**
   ```bash
   git checkout -b lab15
   ```

2. **Commit your work** (chart changes + documentation):
   ```bash
   git add mychart/ k8s/STATEFULSET.md
   git commit -m "feat: convert app to StatefulSet with per-pod persistent storage"
   git push -u origin lab15
   ```

3. **Open Pull Requests:**
   - **PR #1:** `your-fork:lab15` → `course-repo:master`
   - **PR #2:** `your-fork:lab15` → `your-fork:master`

4. **Verify before review:**
   - StatefulSet renders and deploys; pods are `-0`, `-1`, `-2`
   - Headless Service exists with `clusterIP: None`
   - Per-pod PVCs are `Bound`
   - `k8s/STATEFULSET.md` contains your captured evidence

---

## Acceptance Criteria

### Task 1 — Concepts (2 pts)
- [ ] Three StatefulSet guarantees described in your own words
- [ ] Deployment vs StatefulSet comparison table completed
- [ ] Two stateful workload examples with *why* a Deployment hurts them
- [ ] Headless Service (`clusterIP: None`) DNS behaviour explained
- [ ] "When to use an operator" note included

### Task 2 — Convert to StatefulSet (3 pts)
- [ ] `templates/statefulset.yaml` created with `serviceName` set
- [ ] `volumeClaimTemplates` configured; size/class from values
- [ ] `replicas: 3`; pods named `<name>-0/1/2`
- [ ] App writes its visits state to the mounted volume path
- [ ] Per-pod PVCs render and bind (`data-<name>-N`)

### Task 3 — Headless Service & Lifecycle (2 pts)
- [ ] Headless Service created with `clusterIP: None` and matching selector
- [ ] Existing regular Service retained alongside it
- [ ] Per-pod DNS resolution demonstrated with FQDN pattern
- [ ] Ordered startup / reverse-order scale-down observed
- [ ] `OrderedReady` vs `Parallel` explained with an example

### Task 4 — Storage & Persistence (2 pts)
- [ ] Independent per-pod visit counters demonstrated
- [ ] Pod deleted and recreated with the same data (PVC reattached)
- [ ] Evidence captured for documentation

### Task 5 — Documentation (1 pt)
- [ ] `k8s/STATEFULSET.md` covers concepts, inventory, identity, storage, persistence
- [ ] Real command output clearly marked as captured from your cluster

### Bonus — Update Strategies / Operator (2 pts)
- [ ] **Path A:** partitioned `RollingUpdate` canary walked down to roll forward, **and** `OnDelete` demonstrated with a use case; **OR**
- [ ] **Path B:** an operator installed, a Custom Resource declared, and the operator's value-add over a raw StatefulSet documented

---

## Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **Concepts** | 2 pts | Guarantees, comparison, headless DNS, operator rationale |
| **Convert to StatefulSet** | 3 pts | Working StatefulSet with `volumeClaimTemplates` and ordinal pods |
| **Headless Service & Lifecycle** | 2 pts | Per-pod DNS + ordered start/scale + policy explanation |
| **Storage & Persistence** | 2 pts | Per-pod isolation proven; data survives pod kill |
| **Documentation** | 1 pt | Complete, evidence-backed `STATEFULSET.md` |
| **Bonus** | 2 pts | Update strategies **or** a database/storage operator |
| **Total** | 12 pts | 10 pts required + 2 pts bonus |

**Grading scale (main 10 pts):**
- **10/10:** All resources correct, per-pod persistence proven, documentation excellent
- **8-9/10:** Works end-to-end; minor gaps in evidence or explanation
- **6-7/10:** StatefulSet deploys but identity/persistence proof is thin
- **<6/10:** Missing headless Service, broken PVCs, or no persistence demonstration

---

## Resources

<details>
<summary>📚 Official Documentation</summary>

- [StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
- [StatefulSet Basics tutorial](https://kubernetes.io/docs/tutorials/stateful-application/basic-stateful-set/)
- [Headless Services](https://kubernetes.io/docs/concepts/services-networking/service/#headless-services)
- [Volume claim templates](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/#volume-claim-templates)
- [Update strategies & partition rollout](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/#update-strategies)
- [Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)

</details>

<details>
<summary>🤖 Operators & Cloud-Native Storage</summary>

- [Operator pattern](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/) · [OperatorHub.io](https://operatorhub.io/)
- [CloudNativePG](https://cloudnative-pg.io/) — the PostgreSQL operator
- [Strimzi](https://strimzi.io/) — Kafka on Kubernetes
- [Rook](https://rook.io/) — production storage on Ceph
- [Longhorn](https://longhorn.io/) — lightweight CNCF block storage

</details>

<details>
<summary>📕 Books</summary>

- *Kubernetes Up & Running* (3e, 2022) — Burns, Beda, Hightower. The canonical StatefulSet chapter.
- *Kubernetes Patterns* (2e, 2024) — Ibryam & Huß. "Stateful Service" and "Service Discovery" patterns.
- *Learning Helm* (2e, 2024) — Butcher, Farina, Dolitsky. For the Helm 4 chart work.

</details>

---

## Looking Ahead

- **Lab 16:** Monitor your StatefulSet with Prometheus / Grafana — scrape per-pod metrics and alert on the workloads that remember.
- **Bonus Labs 17 & 18:** *Beyond Kubernetes* — deploy your Lab 1 service to Cloudflare Workers, then package it with Nix flakes.

---

**Good luck!** 💾

> **Remember:** StatefulSets are *managed pets* — stable identity plus per-pod storage. For progressive delivery of stateless apps, use Rollouts (Lab 14). For real databases that need failover and backups, reach past the StatefulSet for an operator.
