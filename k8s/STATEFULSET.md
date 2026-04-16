# StatefulSet — Lab 15

## StatefulSet Overview

A StatefulSet is like a Deployment, but for apps that need to remember who they are. It gives each pod a stable name, stable storage, and a stable DNS address. When the pod restarts, it gets the same name and connects to the same storage — nothing is lost.

### Key Differences: Deployment vs StatefulSet

| Feature | Deployment | StatefulSet |
|---------|------------|-------------|
| Pod names | Random suffix (pod-abc12) | Ordered index (pod-0, pod-1) |
| Storage | Shared PVC or ephemeral | Per-pod PVC via volumeClaimTemplates |
| Scaling order | Any order | Ordered (0 → 1 → 2) |
| Network identity | Random DNS | Stable DNS per pod |
| Use case | Stateless apps | Databases, queues, stateful apps |

### When to use StatefulSet
- Databases (MySQL, PostgreSQL, MongoDB)
- Message brokers (Kafka, RabbitMQ)
- Distributed storage (Elasticsearch, Cassandra)
- Any app that needs to remember state across restarts

### Headless Service
A headless service has `clusterIP: None`. Instead of routing traffic to any pod, it creates individual DNS records for each pod:

```
pod-0.service-headless.namespace.svc.cluster.local
pod-1.service-headless.namespace.svc.cluster.local
```

This lets you connect directly to a specific pod — useful for databases where you need to know which node is the primary.

---

## Resource Verification

Output of `kubectl get po,sts,svc,pvc`:

```
NAME                                                    READY   STATUS    RESTARTS   AGE
pod/sts-app-devops-info-service-0                       1/1     Running   0          22s
pod/sts-app-devops-info-service-1                       1/1     Running   0          7m45s
pod/sts-app-devops-info-service-2                       1/1     Running   0          14s

NAME                                           READY   AGE
statefulset.apps/sts-app-devops-info-service   3/3     7m52s

NAME                                           TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/sts-app-devops-info-service            ClusterIP   10.96.242.131   <none>        80/TCP         7m52s
service/sts-app-devops-info-service-headless   ClusterIP   None            <none>        80/TCP         7m52s

NAME                                                        STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/data-sts-app-devops-info-service-0    Bound    pvc-e477e6de-3b24-4c87-82d2-91043df7e4af   100Mi      RWO            standard       8m17s
persistentvolumeclaim/data-sts-app-devops-info-service-1    Bound    pvc-bfb75883-7ec6-4d58-8604-1d31b951806f   100Mi      RWO            standard       7m45s
persistentvolumeclaim/data-sts-app-devops-info-service-2    Bound    pvc-611f410d-8666-45f0-bd5b-f6c86c8be2f5   100Mi      RWO            standard       7m32s
```

Pods are named `sts-app-devops-info-service-0/1/2` — ordered, stable names. Each pod has its own PVC (`data-sts-app-devops-info-service-0/1/2`).

---

## Network Identity — DNS Resolution

Tested DNS from inside pod-0 using Python:

```bash
kubectl exec sts-app-devops-info-service-0 -- python3 -c \
  "import socket; print(socket.gethostbyname('sts-app-devops-info-service-1.sts-app-devops-info-service-headless'))"
# Output: 10.244.0.105
```

Pod-0 successfully resolved pod-1's address via the headless service DNS. The pattern is:
```
<pod-name>.<headless-service-name>.<namespace>.svc.cluster.local
```

Each pod gets its own stable DNS record that always points to the same pod.

---

## Per-Pod Storage Evidence

Each pod has its own storage — visits on pod-0 don't affect pod-1 or pod-2.

```bash
# Increment visits only on pod-0 (via port-forward to port 8083)
curl localhost:8083/           # visit 1
curl localhost:8083/           # visit 2
curl localhost:8083/           # visit 3

# Check each pod separately
curl localhost:8083/visits     # Pod 0: {"visits": 3}
curl localhost:8081/visits     # Pod 1: {"visits": 0}
curl localhost:8082/visits     # Pod 2: {"visits": 0}
```

Pod-0 had 3 visits while pods 1 and 2 had 0 — full storage isolation per pod.

---

## Persistence Test

Data survives pod deletion and restart.

```bash
# Before deletion
curl localhost:8083/visits
# {"visits": 3}

kubectl delete pod sts-app-devops-info-service-0
# pod deleted, StatefulSet creates a new pod-0 with the same PVC

# After pod restarts
curl localhost:8083/visits
# {"visits": 3}   <- same count, data was not lost
```

The StatefulSet reattached the same PVC (`data-sts-app-devops-info-service-0`) to the new pod, so the visit count survived.

---

## Bonus — Update Strategies

### Partitioned Rolling Update

You can update only pods with ordinal index >= partition. Pods below the partition stay at the old version.

```yaml
updateStrategy:
  type: RollingUpdate
  rollingUpdate:
    partition: 2
```

Tested with `helm upgrade --set statefulset.partition=2 --set image.tag=v2`:

```
sts-app-devops-info-service-0: devops-info-service:latest   # not updated (ordinal 0 < 2)
sts-app-devops-info-service-1: devops-info-service:latest   # not updated (ordinal 1 < 2)
sts-app-devops-info-service-2: devops-info-service:v2       # updated (ordinal 2 >= 2)
```

Use case: canary testing — deploy new version to one pod and monitor it before rolling out to all pods.

### OnDelete Strategy

With OnDelete, pods are only updated when you manually delete them. The StatefulSet will NOT automatically restart pods after a config change.

```yaml
updateStrategy:
  type: OnDelete
```

Tested: after upgrading to `image.tag=v3` with OnDelete, all pods kept their old images. Only after manually deleting pod-0 did it restart with the new `v3` image. Pods 1 and 2 stayed unchanged until deleted manually.

Use case: maximum control over when updates happen — useful for critical stateful apps where you want to test one pod before touching others.
