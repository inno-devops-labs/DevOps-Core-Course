# StatefulSets & Persistent Storage

StatefulSet conversion of the `app-python` Helm chart with stable network
identity, headless Service, and per-pod persistent storage via
`volumeClaimTemplates`.

## Contents

1. [Concepts](#1-concepts)
2. [Chart Layout](#2-chart-layout)
3. [Install](#3-install)
4. [Resource Verification](#4-resource-verification)
5. [Network Identity](#5-network-identity)
6. [Per-Pod Storage](#6-per-pod-storage)
7. [Persistence Test](#7-persistence-test)
8. [CLI Reference](#8-cli-reference)

---

## 1. Concepts

### StatefulSet Guarantees

| Guarantee | What it means |
|-----------|---------------|
| Stable network identity | Pod gets an ordinal name (`<sts>-0`, `<sts>-1`, …) and a stable DNS record `<pod>.<headless-svc>.<ns>.svc.cluster.local`. The name and DNS survive reschedule. |
| Stable persistent storage | Each pod owns a PVC created from `volumeClaimTemplates`. When pod-N restarts, it re-attaches to the same PVC. PVCs are not deleted with the pod. |
| Ordered lifecycle | Pods are created `0 → 1 → 2`; each waits for the previous to be `Ready` (with `OrderedReady`). Scale-down and rolling updates run in reverse order, `N-1 → 0`. |

### Deployment vs StatefulSet

| Feature | Deployment | StatefulSet |
|---------|------------|-------------|
| Pod names | `app-<hash>-<rand>` | `app-0`, `app-1`, `app-2` (ordinal) |
| Storage | Single shared PVC, or none | One PVC per pod via `volumeClaimTemplates` |
| Scale order | Parallel, any order | Ordered (`0 → 1 → 2`, reverse on scale-down) |
| Network ID | Random; reach via Service VIP | Stable DNS per pod (via headless Service) |
| Update strategy | `RollingUpdate` / `Recreate` | `RollingUpdate` (with `partition`) / `OnDelete` |
| Use case | Stateless web apps, APIs | Databases, Kafka, Elasticsearch, Cassandra, Zookeeper |

Stateful workloads typically need both *which* replica they are
(leader/follower election, shard ownership) and *their* data on every
restart — that is the gap StatefulSet fills.

### Headless Service

A regular Service has a `clusterIP` and load-balances to the set of
ready endpoints. A **headless** Service sets `clusterIP: None`, so it
gets no VIP. Its DNS query returns the A records of every backing pod,
and the StatefulSet controller additionally publishes per-pod DNS
records:

```
<pod-name>.<headless-svc>.<namespace>.svc.cluster.local
e.g.  lab15-app-python-1.lab15-app-python-headless.lab15.svc.cluster.local
```

This is what gives StatefulSet pods their stable, addressable identity.
The headless Service and the regular Service can coexist — the regular
Service is still useful for client traffic that wants load balancing.

---

## 2. Chart Layout

| File | Purpose |
|------|---------|
| `templates/statefulset.yaml` | Rendered when `statefulset.enabled: true` |
| `templates/deployment.yaml` | Rendered when `statefulset.enabled: false` and `rollout.enabled: false` |
| `templates/rollout.yaml` | Rendered when `rollout.enabled: true` (Lab 14) |
| `templates/service.yaml` | Standard Service for external/internal traffic |
| `templates/service-headless.yaml` | Headless Service (`clusterIP: None`), only with StatefulSet |
| `templates/pvc.yaml` | Standalone PVC, suppressed when StatefulSet is enabled |
| `values.yaml` | Defaults (StatefulSet disabled) |
| `values-statefulset.yaml` | Overlay enabling StatefulSet with 3 replicas |

The chart renders exactly one workload — Deployment, Rollout, or
StatefulSet — based on flags, never two simultaneously. The standalone
PVC is suppressed when the StatefulSet path is active because per-pod
PVCs are now created by `volumeClaimTemplates`.

The `statefulset` block in `values.yaml`:

```yaml
statefulset:
  enabled: false
  replicas: 3
  podManagementPolicy: OrderedReady
  updateStrategy:
    type: RollingUpdate
  persistence:
    size: 100Mi
    storageClass: ""
```

Key fields in `templates/statefulset.yaml`:

```yaml
spec:
  serviceName: {{ include "app-python.fullname" . }}-headless
  replicas:    {{ .Values.statefulset.replicas }}
  podManagementPolicy: {{ .Values.statefulset.podManagementPolicy }}
  ...
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: [ "ReadWriteOnce" ]
        resources:
          requests:
            storage: {{ .Values.statefulset.persistence.size }}
```

Each pod mounts its `data` PVC at `/data`, which is where the Python app
writes its visits counter (`VISITS_FILE_PATH=/data/visits`,
`app_python/config.py:10`).

---

## 3. Install

```bash
kubectl create namespace lab15
helm install lab15 k8s/app-python \
  -n lab15 \
  -f k8s/app-python/values-statefulset.yaml
kubectl -n lab15 rollout status statefulset/lab15-app-python
```

Expected: `statefulset rolling update complete 3 pods at revision …`.

---

## 4. Resource Verification

```
$ kubectl -n lab15 get sts,po,svc,pvc
NAME                                READY   AGE
statefulset.apps/lab15-app-python   3/3     2m1s

NAME                     READY   STATUS    RESTARTS   AGE
pod/lab15-app-python-0   1/1     Running   0          23s
pod/lab15-app-python-1   1/1     Running   0          81s
pod/lab15-app-python-2   1/1     Running   0          74s

NAME                                TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)   AGE
service/lab15-app-python            ClusterIP   10.109.233.193   <none>        80/TCP    2m1s
service/lab15-app-python-headless   ClusterIP   None             <none>        80/TCP    2m1s

NAME                                            STATUS   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/data-lab15-app-python-0   Bound    100Mi      RWO            standard       2m1s
persistentvolumeclaim/data-lab15-app-python-1   Bound    100Mi      RWO            standard       81s
persistentvolumeclaim/data-lab15-app-python-2   Bound    100Mi      RWO            standard       74s
```

Three pods with ordinal names (`-0`, `-1`, `-2`), three PVCs (one per
pod, named `data-<sts>-<ordinal>` from the `volumeClaimTemplates` entry
named `data`), one regular Service for traffic, and one headless Service
(`CLUSTER-IP: None`) for stable per-pod DNS.

---

## 5. Network Identity

Pod hostnames match the StatefulSet ordinal:

```
$ for i in 0 1 2; do kubectl -n lab15 exec lab15-app-python-$i -- hostname; done
lab15-app-python-0
lab15-app-python-1
lab15-app-python-2
```

The image lacks `nslookup`/`dig`, so DNS is resolved with Python's
`socket` module from inside `lab15-app-python-0`:

```
$ kubectl -n lab15 exec lab15-app-python-0 -- python3 -c \
    "import socket; print(socket.gethostbyname('lab15-app-python-1.lab15-app-python-headless'))"
10.244.0.6

$ kubectl -n lab15 exec lab15-app-python-0 -- python3 -c \
    "import socket; print(socket.gethostbyname('lab15-app-python-2.lab15-app-python-headless'))"
10.244.0.7
```

Resolving the headless Service itself returns the IPs of all backing
pods (no VIP):

```
$ kubectl -n lab15 exec lab15-app-python-0 -- python3 -c \
    "import socket; print(socket.getaddrinfo('lab15-app-python-headless', None))"
[(... ('10.244.0.5', 0)),    # pod-0
 (... ('10.244.0.7', 0)),    # pod-2
 (... ('10.244.0.6', 0)),    # pod-1
 ...]
```

DNS naming pattern:

```
<pod-name>.<headless-service>.<namespace>.svc.cluster.local
lab15-app-python-1.lab15-app-python-headless.lab15.svc.cluster.local
```

---

## 6. Per-Pod Storage

Each pod gets its own PVC at `/data`. To prove isolation, port-forward
to each pod **directly** (bypassing the load-balancing Service) and hit
`/` a different number of times:

```
=== pod-0: GET / 5 times ===
200 200 200 200 200
=== pod-1: GET / 2 times ===
200 200
=== pod-2: GET / 0 times ===

=== visit counts (read via /visits, no increment) ===
pod-0: {"visits":5}
pod-1: {"visits":2}
pod-2: {"visits":0}
```

Counters diverge: each replica has its own `/data/visits` file backed
by its own PVC. Storage is **not** shared across replicas.

---

## 7. Persistence Test

Capture pod-0's visit count, delete the pod, wait for the StatefulSet
controller to recreate it, and re-read:

```
=== before delete: pod-0 /data/visits ===
5

=== deleting pod lab15-app-python-0 ===
pod "lab15-app-python-0" deleted from lab15 namespace

=== waiting for restart ===
Waiting for 1 pods to be ready...
statefulset rolling update complete 3 pods at revision lab15-app-python-6bc97546cf...

=== after restart: pod-0 /data/visits ===
5

=== via /visits endpoint ===
pod-0 after delete: {"visits":5}
```

The new pod is named `lab15-app-python-0` (same name) and re-attaches
to the same PVC `data-lab15-app-python-0`. The visit count of **5**
survives the restart — data is persistent.

---

## 8. CLI Reference

### Inspection

```bash
kubectl -n lab15 get sts,po,svc,pvc
kubectl -n lab15 describe sts lab15-app-python
kubectl -n lab15 get pvc -l app.kubernetes.io/instance=lab15
```

### Per-Pod Access

```bash
kubectl -n lab15 port-forward pod/lab15-app-python-0 8080:8000
curl localhost:8080/         # increment
curl localhost:8080/visits   # read
```

### DNS Resolution

```bash
kubectl -n lab15 exec lab15-app-python-0 -- python3 -c \
  "import socket; print(socket.gethostbyname('lab15-app-python-1.lab15-app-python-headless'))"
```

### Scale Up / Down

```bash
kubectl -n lab15 scale sts lab15-app-python --replicas=5    # adds pod-3, pod-4
kubectl -n lab15 scale sts lab15-app-python --replicas=2    # removes pod-2 (reverse order)
```

Note: scaling down does **not** delete the PVCs; they remain so the
data survives a re-scale-up to the same ordinals.

### Cleanup

```bash
helm uninstall lab15 -n lab15
kubectl -n lab15 delete pvc -l app.kubernetes.io/instance=lab15
kubectl delete namespace lab15
```

`helm uninstall` removes the StatefulSet, Pods, and Services, but
PVCs created by `volumeClaimTemplates` are intentionally retained;
delete them explicitly when the data is no longer needed.
