# StatefulSet Implementation

## Overview

StatefulSets manage stateful applications with stable network identities and per-pod persistent storage. Unlike Deployments, StatefulSets guarantee ordered pod naming (pod-0, pod-1, pod-2), individual persistent volumes per pod, and stable DNS names via headless services.

**When to use StatefulSet:**
- Databases (MySQL, PostgreSQL, MongoDB)
- Message queues (Kafka, RabbitMQ)
- Distributed systems (Elasticsearch, Cassandra)

**When to use Deployment:**
- Stateless applications
- Pods can scale in any order
- Shared storage is acceptable

---

## Implementation

### 1. StatefulSet Template

[statefulset.yaml](../devops-info/templates/statefulset.yaml) created with the following key features:
- `serviceName: devops-info-headless` — links to headless service for stable DNS
- `volumeClaimTemplates` — automatically creates an individual PVC for each pod
- Ordered pod naming: app-0, app-1, app-2

### 2. Headless Service

[headless-service.yaml](../devops-info/templates/headless-service.yaml) created with:
- `clusterIP: None` — creates DNS records for each individual pod
- DNS pattern: `pod-N.svc-name.namespace.svc.cluster.local`
- `publishNotReadyAddresses: true` — ensures DNS is available even during pod startup

### 3. Values Config

```yaml
persistence:
  enabled: true
  size: 100Mi
  mountPath: /data

replicaCount: 3
```

---

## Verification

### Pod Status
```bash
kubectl get statefulset,pods,svc,pvc -n default
```

Output:
- StatefulSet: 3/3 ready
- Pods: app-0, app-1, app-2 (ordered)
- Services: app (ClusterIP), app-headless (None)
- PVCs: data-app-0, data-app-1, data-app-2 (per-pod)

### DNS Resolution Test

Execute into a pod to verify DNS resolution:
```bash
kubectl exec -it devops-info-0 -- nslookup devops-info-1.devops-info-headless
```

Result: Resolves pod-1 name to its IP address, confirming stable DNS identity.

### Per-Pod Storage Isolation

Port-forward each pod and verify independent storage:
```bash
kubectl port-forward pod/devops-info-0 8080:8000 &
kubectl port-forward pod/devops-info-1 8081:8000 &
kubectl port-forward pod/devops-info-2 8082:8000 &

curl localhost:8080/visits
curl localhost:8081/visits
curl localhost:8082/visits
```

Each pod maintains its own independent visit counter, demonstrating per-pod storage isolation.

### Persistence Test

Verify storage persistence after pod deletion:
```bash
# Check initial visit count
kubectl exec devops-info-0 -- cat /data/visits
# Result: 181 visits

# Delete the pod
kubectl delete pod devops-info-0

# Wait for restart (~15 seconds)

# Check visit count after restart
kubectl exec devops-info-0 -- cat /data/visits
# Result: 181 visits (data persisted)
```

Data survives pod deletion and restart ✓

---

## Deployment and Verification

```bash
helm upgrade --install devops-info k8s/devops-info
kubectl get statefulset,pods,svc,pvc -n default
```

**Current cluster state:**
```
NAME                           READY   AGE
statefulset.apps/devops-info   3/3     9m45s

NAME                               READY   STATUS    RESTARTS   AGE
pod/devops-info-0                  1/1     Running   0          6m53s
pod/devops-info-1                  1/1     Running   0          9m35s
pod/devops-info-2                  1/1     Running   0          9m24s
pod/devops-info-6f64c4c87b-42rdz   1/1     Running   0          9m44s
pod/devops-info-6f64c4c87b-8wgzc   1/1     Running   0          9m44s
pod/devops-info-6f64c4c87b-w7hlv   1/1     Running   0          9m44s

NAME                           TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
service/devops-info            ClusterIP   10.96.100.241   <none>        80/TCP    9m45s
service/devops-info-headless   ClusterIP   None            <none>        80/TCP    9m45s
service/devops-info-preview    ClusterIP   10.96.187.95    <none>        80/TCP    9m45s
service/kubernetes             ClusterIP   10.96.0.1       <none>        443/TCP   42d

NAME                                       STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/data-devops-info-0   Bound    pvc-bdd1051c-132c-4d86-8a62-d53df3fb1d02   100Mi      RWO            standard       9m45s
persistentvolumeclaim/data-devops-info-1   Bound    pvc-c15eb3ab-117a-43bf-9826-3abfbce160d8   100Mi      RWO            standard       9m35s
persistentvolumeclaim/data-devops-info-2   Bound    pvc-024a0785-5fdf-481a-9f26-8b612436854f   100Mi      RWO            standard       9m24s
persistentvolumeclaim/devops-info-data     Bound    pvc-cda25d3a-b259-4ad8-a96f-19610aa777ee   100Mi      RWO            standard       9m45s
```

### Network Identity — DNS Resolution Test

```bash
kubectl exec devops-info-0 -- getent hosts devops-info-1.devops-info-headless.default.svc.cluster.local
```

**Output:**
```
10.244.0.48  devops-info-1.devops-info-headless.default.svc.cluster.local
```

**Evidence:** Pod-to-pod DNS resolution works. devops-info-1 resolves to stable IP (10.244.0.48).  

### Per-Pod Storage Isolation — Visit Counts Evidence

```bash
kubectl exec devops-info-0 -- cat /data/visits
kubectl exec devops-info-1 -- cat /data/visits
kubectl exec devops-info-2 -- cat /data/visits
```

**Output:**
```
Pod 0: 172
Pod 1: 171
Pod 2: 175
```

**Evidence:** Each pod has its own counter and PVC-backed storage.  

### Persistence Test — Data Survives Pod Deletion

**Before deletion:**
```bash
kubectl exec devops-info-0 -- cat /data/visits
# Output: 181
```

**After restart:**
```bash
kubectl exec devops-info-0 -- cat /data/visits
# Output: 181
```

**Evidence:** Pod data persisted across restart. The PVC kept the visit count.  

### StatefulSet Ordering — Guaranteed Stable Identity

```bash
kubectl get statefulset devops-info -o yaml | grep -A 5 serviceName
```

**Output:**
```yaml
spec:
  serviceName: devops-info-headless
  replicas: 3
  ordinals:
    start: 0
```

**Evidence:** serviceName links to headless service. Pods are created in order: devops-info-0, devops-info-1, devops-info-2.  

### RollingUpdate with Partition

Update only pods with ordinal >= 2:
```yaml
updateStrategy:
  type: RollingUpdate
  rollingUpdate:
    partition: 2
```

Use case: canary update (test pod-2 first, manual promote).

### OnDelete Strategy

Update only on manual delete:
```yaml
updateStrategy:
  type: OnDelete
```

Use case: zero-downtime (delete one, update, restart).

---

## Key Differences: StatefulSet vs Deployment

| Feature | Deployment | StatefulSet |
|---------|-----------|-------------|
| Pod names | random suffix | ordered (pod-0, pod-1) |
| Storage | shared PVC | per-pod PVC |
| Scaling | any order | ordered (0→1→2) |
| Network ID | ephemeral DNS | stable DNS |
| Use case | stateless | stateful |

---


