# StatefulSet Implementation — Lab 15

## StatefulSet Overview

### Why StatefulSet?

StatefulSets are the right controller when an application needs **stable identity** and/or **per-instance persistent storage**. The visits counter service is a perfect example: each pod must maintain its own independent counter that survives restarts.

### Differences from Deployment

| Feature | Deployment | StatefulSet |
|---------|------------|-------------|
| **Pod Names** | Random suffix (`pod-7d9f4-xkz2p`) | Ordered index (`pod-0`, `pod-1`, `pod-2`) |
| **Storage** | Shared PVC or no PVC | Per-pod PVC via `volumeClaimTemplates` |
| **Scaling order** | Any order, parallel | Ordered: 0→1→2 (scale up), 2→1→0 (scale down) |
| **Network identity** | Random DNS, changes on restart | Stable DNS: `pod-0.svc.ns.svc.cluster.local` |
| **Update order** | All at once (surge/unavailable) | Reverse ordinal: N-1 → 0 |
| **PVC lifecycle** | PVC deleted with pod | PVC **retained** when pod is deleted |
| **Use cases** | Stateless web apps, APIs | Databases, queues, distributed systems |

### When to Use StatefulSet

- **Databases**: MySQL, PostgreSQL, MongoDB — need stable identity for replication
- **Message queues**: Kafka, RabbitMQ — brokers need stable hostnames for cluster formation
- **Distributed systems**: Elasticsearch, Cassandra, ZooKeeper — consensus requires stable peers
- **Any app** that writes per-instance state to disk (like this visits counter)

### Headless Service (`clusterIP: None`)

A regular Service creates a virtual IP (ClusterIP) and load-balances across pods. A **headless service** skips the VIP entirely — DNS queries return individual pod IPs directly.

Each StatefulSet pod gets a stable, predictable DNS A-record:
```
<pod-name>.<service-name>.<namespace>.svc.cluster.local
```

---

## Resource Verification

Output of `kubectl get po,sts,svc,pvc -l app.kubernetes.io/instance=python-app`:

```
NAME                              READY   STATUS    RESTARTS       AGE
pod/python-app-0                  1/1     Running   0              99s
pod/python-app-1                  1/1     Running   0              6m45s
pod/python-app-2                  1/1     Running   0              7m17s

NAME                          READY   AGE
statefulset.apps/python-app   3/3     31m

NAME                          TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/python-app-headless   ClusterIP   None            <none>        80/TCP         32m
service/python-app-svc        NodePort    10.101.122.42   <none>        80:30085/TCP   31m

NAME                                      STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/data-python-app-0   Bound    pvc-e4683ab0-d91c-47fc-a8d6-23787efba9c2   100Mi      RWO            standard       31m
persistentvolumeclaim/data-python-app-1   Bound    pvc-85119a17-20ea-4429-9405-0c32eded5bd4   100Mi      RWO            standard       17m
persistentvolumeclaim/data-python-app-2   Bound    pvc-cbb8a5a8-5dc2-47a2-9a5c-6267f3cf17b5   100Mi      RWO            standard       16m
```

**Key observations:**
- Pods are named with ordinal suffixes: `python-app-0`, `python-app-1`, `python-app-2`
- StatefulSet shows `3/3 READY`
- Each pod has its own PVC: `data-python-app-0`, `data-python-app-1`, `data-python-app-2`
- Headless service has `ClusterIP: None` — no virtual IP, direct pod DNS
- Regular NodePort service still exists for external access

---

## Network Identity

DNS resolution test executed from inside `python-app-0` using Python's `socket` module (the container image does not include `nslookup`):

```bash
kubectl exec python-app-0 -- python3 -c "
import socket
for pod in ['python-app-0', 'python-app-1', 'python-app-2']:
    fqdn = f'{pod}.python-app-headless.default.svc.cluster.local'
    ip = socket.gethostbyname(fqdn)
    print(f'{fqdn} -> {ip}')
"
```

**Output:**
```
python-app-0.python-app-headless.default.svc.cluster.local -> 10.244.0.56
python-app-1.python-app-headless.default.svc.cluster.local -> 10.244.0.55
python-app-2.python-app-headless.default.svc.cluster.local -> 10.244.0.54
```

**DNS naming pattern:**
```
<pod-name>.<headless-service-name>.<namespace>.svc.cluster.local
```

Each pod resolves to a **unique, stable IP** that maps directly to that pod — not a load-balanced VIP. This is what enables peer-to-peer communication in clustered databases and distributed systems.

---

## Per-Pod Storage Evidence

Each pod writes to `/data/visits` on its own dedicated PVC. The files are completely isolated — writing to pod-0's PVC has no effect on pod-1 or pod-2.

**Setup:** Different visit counts written to each pod:
```bash
kubectl exec python-app-0 -- python3 -c "open('/data/visits','w').write('5')"
kubectl exec python-app-1 -- python3 -c "open('/data/visits','w').write('3')"
kubectl exec python-app-2 -- python3 -c "open('/data/visits','w').write('1')"
```

**Verification — each pod sees only its own data:**
```bash
$ kubectl exec python-app-0 -- cat /data/visits
5
$ kubectl exec python-app-1 -- cat /data/visits
3
$ kubectl exec python-app-2 -- cat /data/visits
1
```

**Cross-check from pod-0 — cannot see pod-1's or pod-2's data:**
```bash
$ kubectl exec python-app-0 -- python3 -c "
import os
print('pod-0 sees /data/visits =', open('/data/visits').read())
print('pod-0 /data contents:', os.listdir('/data'))
"
pod-0 sees /data/visits = 5
pod-0 /data contents: ['visits']
```

**PVC-to-pod mapping** (auto-created by `volumeClaimTemplates`):

| Pod | PVC | PV |
|-----|-----|----|
| `python-app-0` | `data-python-app-0` | `pvc-e4683ab0-d91c-47fc-a8d6-23787efba9c2` |
| `python-app-1` | `data-python-app-1` | `pvc-85119a17-20ea-4429-9405-0c32eded5bd4` |
| `python-app-2` | `data-python-app-2` | `pvc-cbb8a5a8-5dc2-47a2-9a5c-6267f3cf17b5` |

---

## Persistence Test

**Before deletion — record pod-0's visit count:**
```bash
$ kubectl exec python-app-0 -- cat /data/visits
5
```

**Delete pod-0:**
```bash
$ kubectl delete pod python-app-0
pod "python-app-0" deleted from default namespace
```

**Wait for StatefulSet to recreate pod-0:**
```bash
$ kubectl wait --for=condition=Ready pod/python-app-0 --timeout=120s
pod/python-app-0 condition met
```

**After restart — data is preserved:**
```bash
$ kubectl exec python-app-0 -- cat /data/visits
5
```

**Other pods unaffected:**
```bash
$ kubectl exec python-app-1 -- cat /data/visits
3
$ kubectl exec python-app-2 -- cat /data/visits
1
```

**Why this works:** When a StatefulSet pod is deleted, Kubernetes recreates it with the **same name** (`python-app-0`) and **reattaches the same PVC** (`data-python-app-0`). The PVC is never deleted when a pod is deleted — only when the StatefulSet itself is deleted (and even then, PVCs are retained by default via the `Retain` reclaim policy).

---

## Bonus — Update Strategies

### Partitioned Rolling Update

A partition value `N` means: **only pods with ordinal ≥ N are updated**. Pods with ordinal < N keep the old version. This enables staged/canary rollouts for stateful apps.

**Configuration in [`statefulset.yaml`](python-app/templates/statefulset.yaml):**
```yaml
updateStrategy:
  type: RollingUpdate
  rollingUpdate:
    partition: 2   # Only pod-2 updates; pod-0 and pod-1 stay on old version
```

**Helm upgrade with partition=2:**
```bash
helm upgrade python-app ./k8s/python-app \
  --set statefulset.enabled=true \
  --set statefulset.updateStrategy.rollingUpdate.partition=2
```

**Verified in cluster:**
```bash
$ kubectl get sts python-app -o jsonpath='{.spec.updateStrategy}' | python3 -m json.tool
{
    "rollingUpdate": {
        "maxUnavailable": 1,
        "partition": 2
    },
    "type": "RollingUpdate"
}
```

**Use case:** Deploy a new database version to pod-2 first. Verify it works. Then lower partition to 1 (pod-1 updates). Then to 0 (pod-0 updates). This gives full control over the rollout pace.

### OnDelete Strategy

```yaml
updateStrategy:
  type: OnDelete
```

With `OnDelete`, pods are **never automatically updated**. A pod only gets the new spec when it is **manually deleted**. The StatefulSet controller then recreates it with the new template.

**Use cases:**
- **Databases with manual failover**: Control exactly when each replica restarts (e.g., promote a replica to primary first, then restart the old primary)
- **Maintenance windows**: Update pods one at a time during scheduled downtime
- **Testing**: Verify the new version on one pod before touching others

**Example workflow:**
```bash
# Update image in StatefulSet (pods don't restart yet)
helm upgrade python-app ./k8s/python-app --set image.tag="2.0"

# Manually trigger update of pod-2 only
kubectl delete pod python-app-2
# pod-2 restarts with new image; pod-0 and pod-1 still run old image

# After verification, update pod-1
kubectl delete pod python-app-1
```
