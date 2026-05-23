# Lab 15 — StatefulSets & Persistent Storage


**Helm chart:** `k8s/devops-python` (visits counter from Lab 12)  
**Related labs:** Lab 14 Rollouts (progressive delivery for **stateless** apps) — different use case than StatefulSets

| Controller | Use when |
|------------|----------|
| **Deployment / Rollout** | Stateless HTTP services, interchangeable replicas |
| **StatefulSet** | Stable pod names, ordered lifecycle, **dedicated storage per replica** |

---

## Task 1 — StatefulSet Concepts

### 1. StatefulSet guarantees

A StatefulSet is a workload controller for applications that need **identity** and **durability** beyond what a Deployment provides. Kubernetes documents three core guarantees:

#### Stable, unique network identifiers

Each pod gets a **predictable name** derived from the StatefulSet name plus an ordinal index:

```
<statefulset-name>-0
<statefulset-name>-1
<statefulset-name>-2
```

These names stay tied to the same logical instance across reschedules. If `app-0` is deleted, the replacement pod is still named `app-0` — not a random hash like `app-7f3c9d8b-xk2lm`.

With a **headless Service** (see below), each pod also gets a **stable DNS name**:

```
<pod-name>.<headless-service>.<namespace>.svc.cluster.local
```

Example (after Task 2 implementation):

```
devops-python-sts-0.devops-python-sts-headless.dev.svc.cluster.local
```

Other pods (or clients inside the cluster) can resolve and connect to a **specific** replica by name — required for databases, Kafka brokers, and quorum-based systems.

#### Stable, persistent storage

StatefulSets use **`volumeClaimTemplates`**: for each pod ordinal, Kubernetes automatically creates a **separate PVC**.

```
Pod app-0  →  PVC data-app-0
Pod app-1  →  PVC data-app-1
Pod app-2  →  PVC data-app-2
```

When `app-1` is rescheduled, it reattaches to `data-app-1`. Data follows the **identity**, not the node.

**Contrast with our current Lab 12–14 setup:** the Helm chart uses a **single shared PVC** (`templates/pvc.yaml`) mounted by all Rollout pods. Every replica reads/writes the same `/data/visits` file — fine for a demo counter, wrong for per-instance isolation or databases.

#### Ordered, graceful deployment and scaling

| Operation | StatefulSet behavior |
|-----------|---------------------|
| **Scale up** | Creates pods in order: 0, then 1, then 2 … (waits for each to be Ready unless `podManagementPolicy: Parallel`) |
| **Scale down** | Removes highest index first: … 2, then 1, then 0 |
| **Rolling update** | Updates pods in reverse ordinal order by default; supports `partition` for staged rollouts (bonus task) |
| **Delete pod** | Replacement keeps same name and same PVC |

Deployments/Rollouts create and terminate pods in **any order** — appropriate when replicas are fungible.

---

### 2. Deployment vs StatefulSet

| Feature | Deployment / Rollout | StatefulSet |
|---------|---------------------|-------------|
| **Pod names** | Random suffix (`…-775c7bc848-m4gmm`) | Ordered index (`…-0`, `…-1`, `…-2`) |
| **Network identity** | Random; Service load-balances to any pod | Stable DNS per pod via headless Service |
| **Storage** | Shared PVC or no persistence | **Per-pod PVC** via `volumeClaimTemplates` |
| **Scale order** | Any order | Sequential (default) or parallel |
| **Pod replacement** | New pod = new identity | New pod = **same** ordinal and PVC |
| **Use with Argo Rollouts** | Yes (canary, blue-green) | No — different controller |
| **Typical workloads** | REST APIs, workers, static sites | Databases, queues, clustered search |

#### When to use Deployment / Rollout

- Replicas are **interchangeable** — any pod can serve any request.
- No need to address a **specific** pod by name.
- Shared storage is acceptable, or the app is stateless.
- You want progressive delivery (Lab 14 canary / blue-green).

**Our `devops-python` Rollout** fits here: FastAPI info service, health checks, optional shared visit file for simplicity.

#### When to use StatefulSet

- Each replica needs **its own durable data** (MySQL data dir, Kafka log dir).
- Peers must discover each other at **stable hostnames** (MongoDB replica set, etcd cluster).
- Startup/shutdown order matters (primary before replicas, or index 0 is leader).
- You must prove **per-pod data isolation** (Lab 15 visits counter — each pod keeps its own count).

#### Examples of stateful workloads

| Category | Examples | Why StatefulSet |
|----------|----------|-----------------|
| **Relational DB** | PostgreSQL, MySQL (with operators) | Dedicated data directory per instance |
| **Document / KV** | MongoDB replica set, Cassandra | Stable peer DNS for cluster formation |
| **Search / analytics** | Elasticsearch, ClickHouse | Shard identity tied to node name |
| **Message streaming** | Kafka, RabbitMQ clustered mode | Broker ID ↔ pod ordinal ↔ persistent log |
| **Coordination** | ZooKeeper, etcd | Quorum members need fixed identities |
| **Lab demo** | `devops-python` visits counter | One counter file per pod at `/data/visits` |

**Not StatefulSet:** Redis **Cache** (often Deployment + shared nothing), nginx frontends, our canary Rollout — stateless or shared-state patterns.

#### Rollout vs StatefulSet (Lab 14 vs Lab 15)

Do **not** replace a StatefulSet with a Rollout for databases. They solve orthogonal problems:

- **Rollout** — *how* to update stateless replicas safely (traffic splitting).
- **StatefulSet** — *who* each replica is and *where* its data lives.

For stateful apps, updates use StatefulSet `updateStrategy` (RollingUpdate with partition, or OnDelete), not Argo Rollouts.

---

### 3. Headless Services

A **headless Service** is a Kubernetes Service with:

```yaml
spec:
  clusterIP: None   # no virtual IP — "headless"
```

#### Normal Service vs headless

| | ClusterIP Service (our `…-service`) | Headless Service (`clusterIP: None`) |
|--|--------------------------------------|--------------------------------------|
| **Virtual IP** | Yes — kube-proxy load-balances | No — DNS returns **pod IPs directly** |
| **DNS `A` record** | Single IP for the Service name | **One record per ready pod** |
| **Client behavior** | Connect to Service name → any pod | Resolve `pod-0.service…` → **that** pod only |
| **Typical pairing** | Deployment, Rollout | **StatefulSet** |

Our chart keeps the existing **NodePort/ClusterIP Service** for external access (Task 2) **and** adds a headless Service for stable per-pod DNS.

#### DNS naming pattern

For StatefulSet `web` in namespace `default` with headless Service `web-headless`:

**Per-pod (direct access):**

```
web-0.web-headless.default.svc.cluster.local
web-1.web-headless.default.svc.cluster.local
```

**Governed set (all pods — returns multiple A records):**

```
web-headless.default.svc.cluster.local  →  IP of web-0, web-1, …
```

Short names inside the same namespace:

```
web-0.web-headless
web-1.web-headless
```

#### How DNS is wired

1. StatefulSet `spec.serviceName` must match the headless Service name.
2. Kubernetes sets pod hostname/subdomain so CoreDNS publishes records.
3. Clients use `nslookup` / `getent hosts` from inside the cluster to resolve peers.

**Verification commands (Task 3):**

```bash
kubectl exec -it <sts-name>-0 -n <ns> -- sh
nslookup <sts-name>-1.<headless-service>.<ns>.svc.cluster.local
# or
wget -qO- http://<sts-name>-1.<headless-service>:80/health
```

#### Why both Services?

```
                    ┌─────────────────────┐
  External client   │  NodePort Service   │  → any ready pod (load balanced)
                    └─────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │    StatefulSet     │
                    │  pod-0   pod-1     │
                    └─────────┬─────────┘
                              │
                    ┌─────────┴─────────┐
  In-cluster peer   │ Headless Service   │  → pod-0.service…, pod-1.service…
                    └─────────────────────┘
```

- **Headless** — pod-to-pod identity (DNS, per-pod storage tests).
- **Regular Service** — human/browser access without knowing ordinals.

---

## Task 2 — Convert Deployment to StatefulSet

Implemented in the Helm chart under [k8s/devops-python/templates/statefulset.yaml](k8s/devops-python/templates/statefulset.yaml) and [k8s/devops-python/templates/service-headless.yaml](k8s/devops-python/templates/service-headless.yaml).

### What changed

- Added a StatefulSet workload with the same app container, probes, labels, and config/secrets wiring as the Rollout version.
- Added a headless Service with `clusterIP: None` for stable per-pod DNS.
- Switched persistence from one shared PVC to `volumeClaimTemplates`, so each replica gets its own PVC automatically.
- Kept the regular Service for external access.
- Gated the old Rollout and shared PVC templates behind `workload.kind`, so the chart renders the StatefulSet instead of both controllers at once.

### Verification to run

```bash
kubectl get statefulset
kubectl get pods
kubectl get pvc
kubectl get svc
```

Expected result:

- Pod names like `...-0`, `...-1`, `...-2`
- A headless Service named `...-headless`
- One PVC per pod ordinal

---

## Task 3 — Headless Service & Pod Identity

### 1. Test DNS Resolution

Verified pod-to-pod DNS resolution via the headless service. From within `lab15-sts-devops-python-0`, resolved `lab15-sts-devops-python-1.lab15-sts-devops-python-headless.lab15.svc.cluster.local`:

```
10.244.0.129    lab15-sts-devops-python-1.lab15-sts-devops-python-headless.lab15.svc.cluster.local
```

**Result:** Each pod is resolvable by its stable DNS name within the headless service namespace.

### 2. Test Per-Pod Storage Isolation

Made different numbers of requests to each pod and verified independent visit counts:

**Before requests:**
```
Pod-0: {"visits":0,"file":"/data/visits"}
Pod-1: {"visits":0,"file":"/data/visits"}
Pod-2: {"visits":0,"file":"/data/visits"}
```

**After 5 requests to pod-0, 3 to pod-1, and 7 to pod-2:**
```
Pod-0: {"visits":5,"file":"/data/visits"}
Pod-1: {"visits":3,"file":"/data/visits"}
Pod-2: {"visits":7,"file":"/data/visits"}
```

**Result:** Each pod maintains its own isolated PVC → file `/data/visits`. The `volumeClaimTemplates` automatically created:
- `data-lab15-sts-devops-python-0` (100Mi)
- `data-lab15-sts-devops-python-1` (100Mi)
- `data-lab15-sts-devops-python-2` (100Mi)

### 3. Test Persistence

Deleted `lab15-sts-devops-python-0` and waited for restart. Verified visit count survived:

**Before deletion:** Pod-0 had 5 visits  
**After deletion and restart:** Pod-0 still has 5 visits  
**Final state (all pods):**
```
Pod-0: {"visits":5,"file":"/data/visits"}
Pod-1: {"visits":3,"file":"/data/visits"}
Pod-2: {"visits":7,"file":"/data/visits"}
```

**Result:** StatefulSet replaced `pod-0` with the same ordinal index and reattached to the same PVC (`data-lab15-sts-devops-python-0`), preserving data durability.

---

## Task 4 — Full Verification & Evidence

### 1. StatefulSet Overview

**Why StatefulSet?**
- Each replica requires a **stable, unique identity** (pod-0, pod-1, pod-2, …)
- Each replica needs **dedicated persistent storage** that survives pod deletion/restart
- Ordered lifecycle management ensures predictable startup/shutdown sequence
- Replicas must be **discoverable by stable DNS names** for peer-to-peer communication

**Key Differences from Deployment:**

| Aspect | Deployment | StatefulSet |
|--------|-----------|-------------|
| **Pod naming** | Random (e.g., `app-7a8d9e1p-xyz123`) | Ordinal & predictable (e.g., `app-0`, `app-1`) |
| **Storage** | Shared PVC or stateless | Per-pod PVC via `volumeClaimTemplates` |
| **DNS discovery** | Service load-balances to any pod | Headless service + stable per-pod DNS |
| **Scale ordering** | Any order | Sequential (0→1→2 scale-up; 2→1→0 scale-down) |
| **Data persistence** | Pod replacement loses state | Pod replacement reattaches to same PVC |
| **Use case** | HTTP services, workers, replicas that are interchangeable | Databases, queues, systems requiring identity |

### 2. Resource Verification

**Complete resource output (`kubectl get po,sts,svc,pvc -n lab15`):**

```
NAME                            READY   STATUS    RESTARTS   AGE
pod/lab15-sts-devops-python-0   1/1     Running   0          2m
pod/lab15-sts-devops-python-1   1/1     Running   0          1m53s
pod/lab15-sts-devops-python-2   1/1     Running   0          1m44s

NAME                          READY   AGE
statefulset.apps/lab15-sts-devops-python   3/3     2m

NAME                                     TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE
service/lab15-sts-devops-python-headless ClusterIP   None           <none>        80/TCP    2m
service/lab15-sts-devops-python-service  ClusterIP   10.104.64.81   <none>        80/TCP    2m

NAME                                        STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/data-lab15-sts-devops-python-0   Bound    pvc-e103f3b7-dd1f-4d89-886a-a351798b7fac   100Mi      RWO            standard       2m
persistentvolumeclaim/data-lab15-sts-devops-python-1   Bound    pvc-5ab660ed-2a31-4345-977d-a77a1506606   100Mi      RWO            standard       1m53s
persistentvolumeclaim/data-lab15-sts-devops-python-2   Bound    pvc-9da171ea-f82c-43db-9170-20f93eb7dadd   100Mi      RWO            standard       1m44s
```

**Key observations:**
- Pods named with ordinal suffixes: `pod-0`, `pod-1`, `pod-2`
- StatefulSet shows 3/3 ready
- Two Services: headless (ClusterIP: None) and regular (ClusterIP: 10.104.64.81)
- One PVC per pod, all 100Mi, all Bound to volumes

### Network Identity Evidence

 **Stable DNS names:**
- Pods named with ordinal suffixes: `pod-0`, `pod-1`, `pod-2`
- StatefulSet shows 3/3 ready
- Two Services: headless (ClusterIP: None) and regular (ClusterIP: 10.104.64.81)
- One PVC per pod, all 100Mi, all Bound to volumes

### 3. Network Identity Evidence

**Stable pod DNS names verified:**

From within `lab15-sts-devops-python-0`:
```
getent hosts lab15-sts-devops-python-1.lab15-sts-devops-python-headless.lab15.svc.cluster.local
10.244.0.129    lab15-sts-devops-python-1.lab15-sts-devops-python-headless.lab15.svc.cluster.local
```

**DNS pattern demonstrated:**
- Pod-0 FQDN: `lab15-sts-devops-python-0.lab15-sts-devops-python-headless.lab15.svc.cluster.local`
- Pod-1 FQDN: `lab15-sts-devops-python-1.lab15-sts-devops-python-headless.lab15.svc.cluster.local`
- Pod-2 FQDN: `lab15-sts-devops-python-2.lab15-sts-devops-python-headless.lab15.svc.cluster.local`

**Key:** The headless Service (`clusterIP: None`) ensures CoreDNS publishes individual A records for each pod, enabling peers to discover and connect to specific replicas by name—critical for databases, Kafka, and distributed consensus systems.

### 4. Per-Pod Storage Evidence

**Initial state (all pods at 0 visits):**
```
Pod-0: {"visits":0,"file":"/data/visits"}
Pod-1: {"visits":0,"file":"/data/visits"}
Pod-2: {"visits":0,"file":"/data/visits"}
```

**After sending different numbers of requests:**
- Pod-0 received 5 requests
- Pod-1 received 3 requests  
- Pod-2 received 7 requests

**Updated state (each pod has independent count):**
```
Pod-0: {"visits":5,"file":"/data/visits"}
Pod-1: {"visits":3,"file":"/data/visits"}
Pod-2: {"visits":7,"file":"/data/visits"}
```

**Proof of isolation (all PVCs created by volumeClaimTemplates):**

| Pod | PVC Name | Capacity | Status |
|-----|----------|----------|--------|
| pod-0 | data-lab15-sts-devops-python-0 | 100Mi | Bound |
| pod-1 | data-lab15-sts-devops-python-1 | 100Mi | Bound |
| pod-2 | data-lab15-sts-devops-python-2 | 100Mi | Bound |

Each pod writes to `/data/visits` on its own PVC → each pod has an independent visits file. Running all three simultaneously proves **zero shared state** between replicas.

### 5. Persistence Test - Data Survives Pod Deletion

**Test procedure:**

1. **Record initial state** (pod-0 had 5 visits)
2. **Delete pod-0:** `kubectl delete pod lab15-sts-devops-python-0 -n lab15`
3. **StatefulSet automatically recreates it** with the same ordinal name
4. **Wait for pod-0 to be ready** (~10-15 seconds)
5. **Verify visit count restored**

**Results:**

| Stage | Pod-0 Visits |
|-------|-------------|
| Before deletion | 5 |
| After deletion & restart | 5 |

**StatefulSet behavior during deletion:**

```
State 1: Deleted pod/lab15-sts-devops-python-0
         (3/3 pods → 2/3 pods)

State 2: StatefulSet controller detects missing pod-0
         Creates replacement with same ordinal

State 3: Kubernetes schedules new pod-0 container
         Reattaches to PVC 'data-lab15-sts-devops-python-0'
         (PVC was never deleted, storage preserved)

State 4: new pod-0 starts, loads /data/visits → count = 5
         3/3 pods healthy
```

**Other pods unaffected:**
- Pod-1 visit count: 3 (unchanged)
- Pod-2 visit count: 7 (unchanged)

**Why this works:**
1. StatefulSet's `serviceName` points to headless service → **pod name is stable** (always `pod-0`)
2. `volumeClaimTemplates` creates `data-pod-0` → **storage name is stable** (tied to ordinal, not pod instance)
3. Even when pod-0 is replaced, the new pod gets the same name and PVC is reattached
4. Application reads `/data/visits` from the re-mounted PVC → **data is recovered**


