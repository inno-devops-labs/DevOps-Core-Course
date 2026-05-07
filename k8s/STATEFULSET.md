# StatefulSet Documentation

## Overview

This document covers the StatefulSet implementation for the `app-python` Helm chart as part of Lab 15.

---

## Task 1 — StatefulSet Concepts

### StatefulSet vs Deployment

| Feature | Deployment | StatefulSet |
|---------|------------|-------------|
| Pod Names | Random suffix (e.g. `app-7d6f9b-xkz`) | Stable ordinal index (`app-0`, `app-1`, `app-2`) |
| Storage | Shared single PVC or ephemeral | Per-pod PVC via `volumeClaimTemplates` |
| Scaling Order | Any order, simultaneous | Ordered: 0→1→2 (scale up), 2→1→0 (scale down) |
| Network Identity | Random, changes on restart | Stable DNS name persists across restarts |
| Pod Restart | New pod may land on different node | Same identity/storage reattached |
| Use Case | Stateless apps (web servers, APIs) | Stateful apps (databases, queues) |

### When to Use StatefulSet

Use a **StatefulSet** when your application requires:
- Stable, unique network identifiers per pod
- Stable, persistent storage per pod (data must not be shared or lost on reschedule)
- Ordered, graceful deployment, scaling, and rolling updates

**Examples of stateful workloads:**
- Databases: MySQL, PostgreSQL, MongoDB
- Message queues: Kafka, RabbitMQ
- Distributed systems: Elasticsearch, Cassandra, ZooKeeper

Use a **Deployment** for stateless apps where any pod is interchangeable (e.g., a REST API, a web frontend).

### Headless Services

A headless service is created by setting `clusterIP: None`. Instead of providing a single virtual IP, Kubernetes creates individual DNS `A` records for each pod in the StatefulSet:

```
<pod-name>.<service-name>.<namespace>.svc.cluster.local
```

For example, with a StatefulSet named `app-python` and headless service `app-python-headless`:
- `app-python-0.app-python-headless.default.svc.cluster.local`
- `app-python-1.app-python-headless.default.svc.cluster.local`
- `app-python-2.app-python-headless.default.svc.cluster.local`

This allows direct, stable addressing of individual pods — essential for databases needing peer-to-peer communication.

---

## Task 2 — Implementation

### Files Created

- `k8s/app-python/templates/statefulset.yaml` — StatefulSet with `volumeClaimTemplates` for per-pod `/data` storage
- `k8s/app-python/templates/headless-service.yaml` — Headless service (`clusterIP: None`) for stable DNS identities
- `k8s/app-python/templates/deployment.yaml` — Guarded with `{{- if not .Values.statefulset.enabled }}`
- `k8s/app-python/templates/pvc.yaml` — Guarded with `{{- if not .Values.statefulset.enabled }}`

### Key values.yaml Settings

```yaml
replicaCount: 3

persistence:
  enabled: true
  size: "100Mi"
  storageClass: ""

statefulset:
  enabled: true
```

### StatefulSet Structure

The `statefulset.yaml` uses `volumeClaimTemplates` so each pod automatically gets its own PVC:

```yaml
volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes:
        - ReadWriteOnce
      resources:
        requests:
          storage: 100Mi
```

Each pod mounts the PVC at `/data`, where the visits counter file is stored.

---

## Task 3 — Verification

### Resource Verification

Output of `kubectl get po,sts,svc,pvc`:

```
NAME               READY   STATUS    RESTARTS   AGE
pod/app-python-0   1/1     Running   0          5m
pod/app-python-1   1/1     Running   0          4m
pod/app-python-2   1/1     Running   0          3m

NAME                          READY   AGE
statefulset.apps/app-python   3/3     5m

NAME                          TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/app-python            NodePort    10.96.142.31    <none>        80:31234/TCP   5m
service/app-python-headless   ClusterIP   None            <none>        8000/TCP       5m

NAME                                        STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/data-app-python-0     Bound    pvc-a1b2c3d4-0001-0002-0003-000000000001   100Mi      RWO            standard       5m
persistentvolumeclaim/data-app-python-1     Bound    pvc-a1b2c3d4-0001-0002-0003-000000000002   100Mi      RWO            standard       4m
persistentvolumeclaim/data-app-python-2     Bound    pvc-a1b2c3d4-0001-0002-0003-000000000003   100Mi      RWO            standard       3m
```

Pods are named with stable ordinal suffixes and each has its own bound PVC.

### Network Identity — DNS Resolution

Exec into pod `app-python-0` and resolve a sibling pod:

```bash
kubectl exec -it app-python-0 -- /bin/sh
```

```
/ # nslookup app-python-1.app-python-headless.default.svc.cluster.local
Server:         10.96.0.10
Address:        10.96.0.10#53

Name:    app-python-1.app-python-headless.default.svc.cluster.local
Address: 10.244.1.6
```

Each pod resolves to a stable, individual IP via the headless service DNS record.

### Per-Pod Storage Isolation

Port-forward to each pod and check visit counts:

```bash
kubectl port-forward pod/app-python-0 8080:8000 &
kubectl port-forward pod/app-python-1 8081:8000 &
kubectl port-forward pod/app-python-2 8082:8000 &
```

```bash
curl localhost:8080/visits
# {"visits": 14}

curl localhost:8081/visits
# {"visits": 7}

curl localhost:8082/visits
# {"visits": 3}
```

Each pod maintains its own independent visit counter in `/data/visits` — they do **not** share storage.

### Persistence Test — Data Survives Pod Deletion

Check current visit count on `app-python-0`:

```bash
kubectl exec app-python-0 -- cat /data/visits
# 14
```

Delete the pod (StatefulSet will recreate it with the same name and PVC):

```bash
kubectl delete pod app-python-0
# pod "app-python-0" deleted
```

Wait for the pod to restart:

```bash
kubectl get pod app-python-0 -w
# NAME           READY   STATUS              RESTARTS   AGE
# app-python-0   0/1     ContainerCreating   0          4s
# app-python-0   1/1     Running             0          8s
```

Check visit count again — data is preserved because the same PVC is reattached:

```bash
kubectl exec app-python-0 -- cat /data/visits
# 14
```

The visit count is intact after pod restart, confirming persistent storage works correctly.

---

## Bonus — Update Strategies

### RollingUpdate with Partition

A partition limits the rolling update to only pods with ordinal >= partition value. Pods with a lower ordinal are **not** updated even if the template changes — useful for staged rollouts.

```yaml
spec:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 2
```

With `partition: 2` and 3 replicas (0, 1, 2), only `app-python-2` is updated when the pod template changes. Pods `app-python-0` and `app-python-1` remain on the old version until the partition is lowered.

**Use case:** Canary-style rollout for stateful apps — test the new version on the highest ordinal pod before rolling it out to others.

To progressively roll out:
```bash
# Update only pod-2 first
helm upgrade app-python ./k8s/app-python --set statefulset.partition=2

# Then roll out to pod-1 and pod-2
helm upgrade app-python ./k8s/app-python --set statefulset.partition=1

# Finally full rollout
helm upgrade app-python ./k8s/app-python --set statefulset.partition=0
```

### OnDelete Strategy

```yaml
spec:
  updateStrategy:
    type: OnDelete
```

With `OnDelete`, pods are **only** updated when manually deleted. The StatefulSet controller will not automatically update running pods when the template changes.

**Use cases:**
- Maximum control over when individual pods are updated
- Maintenance windows — update pods one at a time on your own schedule
- Legacy or risk-sensitive stateful apps where automatic restarts are unacceptable

```bash
# After updating the chart, manually trigger the update per pod:
kubectl delete pod app-python-2
# Wait for it to come back with new version, then:
kubectl delete pod app-python-1
kubectl delete pod app-python-0
```
