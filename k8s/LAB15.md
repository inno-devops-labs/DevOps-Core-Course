# Lab 15 — StatefulSets & Persistent Storage

## 1. StatefulSet Concepts

### When to Use StatefulSet vs Deployment

| Feature | Deployment | StatefulSet |
|---------|------------|-------------|
| Pod names | Random suffix (`pod-7f4d9c-xyz`) | Ordered index (`pod-0`, `pod-1`, `pod-2`) |
| Storage | Shared PVC or none | Per-pod PVC via `volumeClaimTemplates` |
| Scaling order | Any order, simultaneous | Sequential: 0 → 1 → 2 (scale up), 2 → 1 → 0 (scale down) |
| Network identity | Random (changes on restart) | Stable DNS: `pod-0.svc.ns.svc.cluster.local` |
| Pod identity survives restart | No | Yes — same ordinal, same PVC |

**Use StatefulSet for:**
- Databases (PostgreSQL, MySQL, MongoDB, Redis)
- Message brokers (Kafka, RabbitMQ)
- Distributed systems (Elasticsearch, Cassandra, ZooKeeper)
- Any app that must remember state per-instance across restarts

**Use Deployment / Rollout for:**
- Stateless web apps and APIs
- Workers that read from external storage
- Anything where all pods are interchangeable

### Headless Service

A Service with `clusterIP: None` does not provide load-balancing. Instead, DNS returns an A-record for **each pod individually**:

```
python-app-sts-0.python-app-headless.default.svc.cluster.local → <Pod-0 IP>
python-app-sts-1.python-app-headless.default.svc.cluster.local → <Pod-1 IP>
python-app-sts-2.python-app-headless.default.svc.cluster.local → <Pod-2 IP>
```

This lets clients (or pods) address specific instances directly — essential for leader election and replication protocols.

---

## 2. StatefulSet Implementation

### Templates Added

- `k8s/devops-python-chart/templates/statefulset.yaml` — StatefulSet with `volumeClaimTemplates`
- `k8s/devops-python-chart/templates/service-headless.yaml` — Headless service (`clusterIP: None`)

Enable the StatefulSet (disabled by default so it doesn't conflict with the Rollout):

```bash
helm upgrade --install python-app ./k8s/devops-python-chart \
  --set statefulset.enabled=true \
  --set replicaCount=3 \
  --set persistence.size=100Mi
```

### Verify Deployment

```bash
kubectl get statefulset
# NAME                  READY   AGE
# python-app-sts        3/3     45s

kubectl get pods
# NAME                    READY   STATUS    RESTARTS
# python-app-sts-0        1/1     Running   0
# python-app-sts-1        1/1     Running   0
# python-app-sts-2        1/1     Running   0

kubectl get pvc
# NAME                         STATUS   VOLUME              CAPACITY
# data-python-app-sts-0        Bound    pvc-xxx             100Mi
# data-python-app-sts-1        Bound    pvc-yyy             100Mi
# data-python-app-sts-2        Bound    pvc-zzz             100Mi

kubectl get svc
# NAME                         TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)
# python-app                   NodePort    10.x.x.x      <none>        80:30080/TCP
# python-app-headless          ClusterIP   None          <none>        80/TCP
```

Each pod automatically receives its own PVC (`data-<podname>`) via `volumeClaimTemplates`. The main service still routes external traffic normally; the headless service provides stable DNS for inter-pod communication.

---

## 3. Network Identity & Per-Pod Storage

### DNS Resolution Test

```bash
# Exec into pod-0 and resolve other pods via the headless service:
kubectl exec -it python-app-sts-0 -- /bin/sh

# Inside the pod:
nslookup python-app-sts-1.python-app-headless.default.svc.cluster.local
# Server: 10.96.0.10
# Address: 10.96.0.10#53
# Name:   python-app-sts-1.python-app-headless.default.svc.cluster.local
# Address: 172.17.0.8

nslookup python-app-sts-2.python-app-headless.default.svc.cluster.local
# Name:   python-app-sts-2.python-app-headless.default.svc.cluster.local
# Address: 172.17.0.9
```

**Result:** Each pod is individually addressable via a stable DNS name. The address does not change across pod restarts, which is essential for cluster membership protocols.

### Per-Pod Storage Isolation Test

Each pod writes to `/data` — its own PVC. Port-forwarding to individual pods shows independent visit counters:

```bash
kubectl port-forward pod/python-app-sts-0 8080:5001 &
kubectl port-forward pod/python-app-sts-1 8081:5001 &
kubectl port-forward pod/python-app-sts-2 8082:5001 &

# Send requests to each pod individually:
curl localhost:8080/visits   # pod-0: visits=5
curl localhost:8081/visits   # pod-1: visits=0   (different PVC)
curl localhost:8082/visits   # pod-2: visits=0   (different PVC)
```

**Result:** Each pod maintains its own independent visit count because each is backed by a separate PVC. Unlike a Deployment where all pods share a single PVC (or use `ReadWriteMany`), a StatefulSet guarantees storage isolation per pod.

### Persistence Test — Data Survives Pod Deletion

```bash
# Check current visit count on pod-0:
kubectl exec python-app-sts-0 -- cat /data/visits
# 5

# Delete pod-0 (not the StatefulSet):
kubectl delete pod python-app-sts-0

# Kubernetes immediately recreates pod-0 with the SAME ordinal and SAME PVC:
kubectl get pods -w
# python-app-sts-0   0/1   Terminating    → ContainerCreating → Running

# Check visit count after restart:
kubectl exec python-app-sts-0 -- cat /data/visits
# 5   ← preserved!
```

**Result:** The PVC `data-python-app-sts-0` is not deleted when the pod is deleted. The new pod-0 mounts the same PVC and finds the data intact. This is the core guarantee of StatefulSets — persistent identity and storage across restarts.

---

## 4. Bonus — Update Strategies

### Partitioned Rolling Update

The `partition` value controls which pods receive an update. Only pods with ordinal index **≥ partition** are updated:

```bash
# Update only pod-2 (index >= 2), leave pod-0 and pod-1 on old version:
helm upgrade python-app ./k8s/devops-python-chart \
  --set statefulset.enabled=true \
  --set statefulset.partition=2 \
  --set image.tag=v2.0.0

# pod-2 gets updated; pod-0 and pod-1 keep the old image
kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].image}{"\n"}{end}'
# python-app-sts-0   mirana18/devops-info-service:latest
# python-app-sts-1   mirana18/devops-info-service:latest
# python-app-sts-2   mirana18/devops-info-service:v2.0.0
```

**Use case:** Canary-style updates for stateful apps — validate the new version on one pod before rolling it out to all.

### OnDelete Strategy

With `OnDelete`, pods are updated only when manually deleted:

```yaml
updateStrategy:
  type: OnDelete
```

```bash
# Update is applied only when you explicitly delete a pod:
kubectl delete pod python-app-sts-1
# pod-1 restarts with new image; pod-0 and pod-2 remain unchanged

# Full control over the update sequence — useful when each pod
# requires manual drain/backup steps before upgrading.
```

**Use case:** Databases or caches where each node requires a manual pre-update procedure (e.g., snapshot, leader step-down) before the pod is safely restarted.

---

## 5. Summary

StatefulSets solve the fundamental problem of identity for stateful applications in Kubernetes:

1. **Stable pod names** (`pod-0`, `pod-1`, `pod-2`) allow consistent configuration (e.g., replica sets, cluster membership).
2. **Per-pod PVCs** via `volumeClaimTemplates` ensure each instance has private, durable storage.
3. **Headless service** enables direct DNS-based addressing of individual pods.
4. **Ordered lifecycle** guarantees safe scaling and startup sequencing for distributed systems.

Use StatefulSets alongside Rollouts (Lab 14) — Rollouts handle progressive delivery for stateless services, StatefulSets manage identity and storage for stateful ones. They are complementary, not competing tools.
