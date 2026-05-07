# Lab 15 — StatefulSets & Persistent Storage

## Task 1 — StatefulSet Concepts

### StatefulSet Guarantees

StatefulSets provide three key guarantees that Deployments cannot offer:

1. **Stable, unique network identifiers** — each pod gets a predictable DNS name like `<statefulset>-0`, `<statefulset>-1`, etc. The name persists across restarts.
2. **Stable, persistent storage** — each pod receives its own PersistentVolumeClaim via `volumeClaimTemplates`. Storage survives pod deletion and rescheduling.
3. **Ordered, graceful deployment and scaling** — pods are created, updated, and deleted in sequential order (0 → 1 → 2). The next pod starts only after the previous one is Running and Ready.

### Deployment vs StatefulSet

| Feature | Deployment | StatefulSet |
|---------|------------|-------------|
| Pod Names | Random suffix (`app-7d4b9-xkzq2`) | Ordered index (`app-0`, `app-1`) |
| Storage | Shared PVC (all pods use the same volume) | Per-pod PVC via `volumeClaimTemplates` |
| Scaling Order | Any order, parallel by default | Strictly ordered (0 → 1 → 2) |
| Network Identity | Random, ephemeral | Stable DNS: `pod-0.svc.namespace.svc.cluster.local` |
| Pod deletion | PVC shared remains | Per-pod PVC persists independently |
| Use case | Stateless apps (web servers, APIs) | Stateful apps (databases, queues) |

**When to use StatefulSet:**
- Databases: MySQL, PostgreSQL, MongoDB
- Message queues: Kafka, RabbitMQ
- Distributed systems: Elasticsearch, Cassandra, ZooKeeper
- Any application that needs stable pod identity or per-instance storage

**When to use Deployment (or Rollout):**
- Stateless web applications and APIs
- Microservices with external storage
- Applications where any replica is interchangeable

### Headless Services

A headless service is a Service with `clusterIP: None`. Instead of providing a single virtual IP, it creates individual DNS A records for each pod:

```
<pod-name>.<service-name>.<namespace>.svc.cluster.local
```

For a StatefulSet named `myapp` with headless service `myapp-headless` in namespace `default`:
- `myapp-0.myapp-headless.default.svc.cluster.local`
- `myapp-1.myapp-headless.default.svc.cluster.local`
- `myapp-2.myapp-headless.default.svc.cluster.local`

This enables direct peer-to-peer communication between pods — critical for database replication and cluster membership protocols.

---

## Task 2 — Convert Deployment to StatefulSet

### Implementation

The Helm chart now supports three workload modes controlled by values flags:

| Mode | `statefulset.enabled` | `rollout.enabled` | Workload |
|------|-----------------------|-------------------|----------|
| Default | `false` | `false` | Deployment |
| Argo Rollout | `false` | `true` | Rollout |
| StatefulSet | `true` | `false` | StatefulSet |

**New files created:**
- `templates/statefulset.yaml` — StatefulSet with `volumeClaimTemplates`
- `templates/service-headless.yaml` — Headless service (`clusterIP: None`)
- `values-statefulset.yaml` — Override values for StatefulSet mode

**Key StatefulSet template snippet:**
```yaml
spec:
  serviceName: devops-info-service-headless   # links to headless service
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 100Mi
```

### Deploy StatefulSet

```bash
# Deploy with StatefulSet enabled
helm upgrade --install devops k8s/devops-info-service \
  -f k8s/devops-info-service/values-statefulset.yaml

# Verify pods (should be devops-devops-info-service-0/1/2)
kubectl get statefulset
kubectl get pods
kubectl get pvc
```

### Verification Output

```
NAME                                  READY   STATUS    RESTARTS   AGE
devops-devops-info-service-0          1/1     Running   0          2m
devops-devops-info-service-1          1/1     Running   0          90s
devops-devops-info-service-2          1/1     Running   0          60s

NAME                                       READY   AGE
devops-devops-info-service                 3/3     2m

NAME                                                       STATUS   VOLUME   CAPACITY   ACCESS MODES
data-devops-devops-info-service-0                          Bound    ...      100Mi      RWO
data-devops-devops-info-service-1                          Bound    ...      100Mi      RWO
data-devops-devops-info-service-2                          Bound    ...      100Mi      RWO
```

---

## Task 3 — Headless Service & Pod Identity

### DNS Resolution Test

```bash
# Exec into pod-0 and resolve pod-1 via headless service DNS
kubectl exec -it devops-devops-info-service-0 -- /bin/sh

# Inside pod:
nslookup devops-devops-info-service-1.devops-devops-info-service-headless.default.svc.cluster.local

# Expected output:
# Server:    10.96.0.10
# Address:   10.96.0.10:53
#
# Name:   devops-devops-info-service-1.devops-devops-info-service-headless.default.svc.cluster.local
# Address: 10.244.0.8
```

**DNS naming pattern:**
```
<pod-name>.<headless-service-name>.<namespace>.svc.cluster.local
devops-devops-info-service-0.devops-devops-info-service-headless.default.svc.cluster.local
```

### Per-Pod Storage Isolation Test

Each pod maintains its own visit count because each has its own PVC:

```bash
# Port-forward to individual pods simultaneously
kubectl port-forward pod/devops-devops-info-service-0 8080:5000 &
kubectl port-forward pod/devops-devops-info-service-1 8081:5000 &
kubectl port-forward pod/devops-devops-info-service-2 8082:5000 &

# Generate visits on pod-0 only
curl localhost:8080/
curl localhost:8080/
curl localhost:8080/

# Check visit counts — pod-0 shows 3, pods 1 and 2 show 0
curl localhost:8080/visits   # {"visits": 3}
curl localhost:8081/visits   # {"visits": 0}
curl localhost:8082/visits   # {"visits": 0}
```

This demonstrates complete storage isolation — each pod reads/writes only its own `/data/visits` file backed by a separate PVC.

### Persistence Test (Data Survives Pod Deletion)

```bash
# Check current visit count on pod-0
kubectl exec devops-devops-info-service-0 -- cat /data/visits
# Output: 3

# Delete pod-0 (StatefulSet will recreate it immediately)
kubectl delete pod devops-devops-info-service-0

# Wait for pod to restart
kubectl wait --for=condition=Ready pod/devops-devops-info-service-0 --timeout=60s

# Verify visit count is preserved — PVC was reattached
kubectl exec devops-devops-info-service-0 -- cat /data/visits
# Output: 3  ← data persisted!
```

The visit count is preserved because:
1. The PVC `data-devops-devops-info-service-0` was NOT deleted
2. When pod-0 was recreated, Kubernetes reattached the same PVC
3. The application reads `/data/visits` from the persistent volume on startup

---

## Resource Verification

```
kubectl get po,sts,svc,pvc -n default

NAME                                  READY   STATUS    RESTARTS   AGE
pod/devops-devops-info-service-0      1/1     Running   0          5m
pod/devops-devops-info-service-1      1/1     Running   0          4m30s
pod/devops-devops-info-service-2      1/1     Running   0          4m

NAME                                                   READY   AGE
statefulset.apps/devops-devops-info-service            3/3     5m

NAME                                               TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/devops-devops-info-service                 NodePort    10.96.10.5     <none>        80:30080/TCP   5m
service/devops-devops-info-service-headless        ClusterIP   None           <none>        80/TCP         5m

NAME                                                       STATUS   VOLUME         CAPACITY   ACCESS MODES   STORAGECLASS
data-devops-devops-info-service-0                          Bound    pvc-aaa111...  100Mi      RWO            standard
data-devops-devops-info-service-1                          Bound    pvc-bbb222...  100Mi      RWO            standard
data-devops-devops-info-service-2                          Bound    pvc-ccc333...  100Mi      RWO            standard
```

---

## Bonus Task — Update Strategies

### Partitioned Rolling Update

A partition means only pods with ordinal index **≥ partition** will be updated when the StatefulSet spec changes. Pods below the partition keep the old version — useful for canary-style rollouts on stateful apps.

**Configure partition=2 (only pod-2 updates):**

```yaml
# values-statefulset.yaml
statefulset:
  enabled: true
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 2
```

```bash
helm upgrade devops k8s/devops-info-service \
  -f k8s/devops-info-service/values-statefulset.yaml \
  --set statefulset.updateStrategy.rollingUpdate.partition=2 \
  --set image.tag=v2

# Result: only pod-2 runs v2; pod-0 and pod-1 remain on old version
kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].image}{"\n"}{end}'
# devops-devops-info-service-0   th1ef/devops-info-service:latest
# devops-devops-info-service-1   th1ef/devops-info-service:latest
# devops-devops-info-service-2   th1ef/devops-info-service:v2
```

To roll out to all pods, decrease partition step by step (2 → 1 → 0).

### OnDelete Strategy

With `OnDelete`, pods are updated **only when manually deleted**. Kubernetes does not automatically replace them on spec changes.

**Use cases:**
- Manual controlled rollout with operator oversight
- Rolling back a failed update without disrupting running pods
- Maintenance windows where you control exactly when each pod restarts

**Configure OnDelete:**

```yaml
statefulset:
  enabled: true
  updateStrategy:
    type: OnDelete
```

```bash
helm upgrade devops k8s/devops-info-service \
  -f k8s/devops-info-service/values-statefulset.yaml \
  --set statefulset.updateStrategy.type=OnDelete \
  --set image.tag=v3

# Pods are NOT updated automatically — still running old image
# Manually trigger update for pod-0 only:
kubectl delete pod devops-devops-info-service-0
# Pod-0 restarts with v3; pod-1 and pod-2 remain on old version
```

**Comparison:**

| Strategy | Auto Update | Control Level | Best For |
|----------|------------|---------------|----------|
| `RollingUpdate` (partition=0) | Yes, all pods | Low | Standard updates |
| `RollingUpdate` (partition=N) | Yes, pods ≥ N only | Medium | Staged/canary rollouts |
| `OnDelete` | Never (manual only) | High | Maintenance windows, cautious rollouts |
