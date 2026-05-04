# Lab 15 — StatefulSets & Persistent Storage

## 1. StatefulSet Overview

### Why StatefulSet?

| Feature | Deployment | StatefulSet |
|---------|-----------|-------------|
| Pod names | Random suffix (`pod-7d8f4`) | Stable ordinals (`pod-0`, `pod-1`) |
| Storage | Shared PVC or ephemeral | Per-pod PVC via `volumeClaimTemplates` |
| Scaling order | Any order, parallel | Ordered: 0→1→2 (scale up), reverse (scale down) |
| Network identity | Random DNS/IP | Stable DNS: `pod-0.svc-headless.ns.svc.cluster.local` |
| Update order | All pods simultaneously | Ordered: highest ordinal first |

**Use StatefulSet for:**
- Databases (MySQL, PostgreSQL, MongoDB, Redis)
- Message queues (Kafka, RabbitMQ)
- Distributed systems requiring leader election (Elasticsearch, ZooKeeper)
- Any app that writes unique state per-instance

**Use Deployment/Rollout for:**
- Stateless web services, APIs
- Workers that read from a shared queue
- Apps where any pod is interchangeable

### Headless Service

A `Service` with `clusterIP: None` creates individual DNS `A` records per pod instead of a single virtual IP:

```
devops-info-sts-0.devops-info-sts-headless.stateful-test.svc.cluster.local
devops-info-sts-1.devops-info-sts-headless.stateful-test.svc.cluster.local
devops-info-sts-2.devops-info-sts-headless.stateful-test.svc.cluster.local
```

This lets clients connect to a *specific* pod — essential for leader-follower replication.

---

## 2. Resource Verification

```
kubectl get po,sts,svc,pvc -n stateful-test
```

```
NAME                    READY   STATUS    RESTARTS   AGE
pod/devops-info-sts-0   1/1     Running   0          ...
pod/devops-info-sts-1   1/1     Running   0          ...
pod/devops-info-sts-2   1/1     Running   0          ...

NAME                               READY   AGE
statefulset.apps/devops-info-sts   3/3     ...

NAME                               TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
service/devops-info-sts            ClusterIP   10.104.x.x   <none>        80/TCP    ...
service/devops-info-sts-headless   ClusterIP   None         <none>        80/TCP    ...

NAME                                           STATUS   CAPACITY   ACCESS MODES
persistentvolumeclaim/data-devops-info-sts-0   Bound    50Mi       RWO
persistentvolumeclaim/data-devops-info-sts-1   Bound    50Mi       RWO
persistentvolumeclaim/data-devops-info-sts-2   Bound    50Mi       RWO
```

See [`statefulset/evidence/01-resources.txt`](./statefulset/evidence/01-resources.txt).

Each pod automatically received its own `data-devops-info-sts-N` PVC from `volumeClaimTemplates`.

---

## 3. Network Identity — DNS Resolution

From inside `devops-info-sts-0`:

```python
import socket
socket.gethostbyname('devops-info-sts-1.devops-info-sts-headless.stateful-test.svc.cluster.local')
# → 10.244.0.112
```

Results:
```
devops-info-sts-0 → 10.244.0.118
devops-info-sts-1 → 10.244.0.119
devops-info-sts-2 → 10.244.0.115
```

Each pod resolves to its own stable IP. See [`statefulset/evidence/02-dns.txt`](./statefulset/evidence/02-dns.txt).

---

## 4. Per-Pod Storage Evidence

Each pod maintains an independent visit counter stored at `/data/visits`.

```
Pod 0: {"visits":5}   ← received 5 direct hits
Pod 1: {"visits":3}   ← untouched by pod-0's traffic
Pod 2: {"visits":1}   ← untouched by pod-0's traffic
```

See [`statefulset/evidence/03-per-pod-storage.txt`](./statefulset/evidence/03-per-pod-storage.txt).

If pods shared a PVC (Deployment behaviour), all three would show the same count.

---

## 5. Persistence Test

```bash
# Record pod-0 count
kubectl exec devops-info-sts-0 -n stateful-test -- cat /data/visits
# 5

# Delete pod-0
kubectl delete pod devops-info-sts-0 -n stateful-test

# StatefulSet recreates it with the same name and the same PVC
# Wait for Running...
kubectl exec devops-info-sts-0 -n stateful-test -- cat /data/visits
# 5  ← preserved
```

See [`statefulset/evidence/04-persistence.txt`](./statefulset/evidence/04-persistence.txt).

---

## 6. Bonus — Update Strategies

### Partitioned Rolling Update

```yaml
spec:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 2
```

Only pods with ordinal **≥ partition** are updated. Pods below the partition keep running the old version.

Test: set `partition: 2`, then push a new image (`v4`). Only `devops-info-sts-2` restarted with `v4`; `sts-0` and `sts-1` kept `latest`.

```
devops-info-sts-0: merkulovlr05/devops-info:latest   ← unchanged
devops-info-sts-1: merkulovlr05/devops-info:latest   ← unchanged
devops-info-sts-2: merkulovlr05/devops-info:v4       ← updated (ordinal 2 >= partition 2)
```

See [`statefulset/evidence/05-partition-update.txt`](./statefulset/evidence/05-partition-update.txt).

**Use case:** Canary-style testing on a single replica before rolling out to the rest of the cluster.

### OnDelete Strategy

```yaml
spec:
  updateStrategy:
    type: OnDelete
```

Pods are **only** updated when manually deleted. The StatefulSet controller does not touch running pods automatically.

Test: push new spec image `v2`, wait 10 s — running pods still show their previous images. Only after `kubectl delete pod devops-info-sts-N` does that pod restart with the new image.

See [`statefulset/evidence/06-ondeletestrategy.txt`](./statefulset/evidence/06-ondeletestrategy.txt).

**Use case:** Applications where an operator must explicitly choose when each instance upgrades (e.g., database replicas needing manual data migration before upgrade).

---

## 7. Implementation

Charts in `k8s/helm/devops-info/`. Enable with:

```bash
helm upgrade --install devops-info-sts k8s/helm/devops-info -n stateful-test \
  -f k8s/helm/devops-info/values-statefulset.yaml \
  --set service.type=ClusterIP
```

Key templates:
- `templates/statefulset.yaml` — StatefulSet with `volumeClaimTemplates`
- `templates/headless-service.yaml` — `clusterIP: None` headless service
- `values-statefulset.yaml` — overrides enabling statefulset mode
