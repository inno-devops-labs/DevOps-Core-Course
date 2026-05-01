# Lab 15 — StatefulSets & Persistent Storage

## 1. StatefulSet Overview

### Why StatefulSet?

StatefulSets are for applications that need:
- **Stable pod names** — `pod-0`, `pod-1`, `pod-2` (not random hashes)
- **Per-pod storage** — each pod gets its own PVC via `volumeClaimTemplates`
- **Ordered startup/shutdown** — pod-0 starts first, pod-2 shuts down first
- **Stable DNS** — `pod-0.headless-svc.namespace.svc.cluster.local`

### Deployment vs StatefulSet

| Feature | Deployment | StatefulSet |
|---------|------------|-------------|
| Pod names | Random suffix (`app-7d9f-xkz`) | Ordered index (`app-0`, `app-1`) |
| Storage | Shared PVC or none | Per-pod PVC via `volumeClaimTemplates` |
| Scaling order | Any order | Ordered (0→1→2 up, 2→1→0 down) |
| Network identity | Random | Stable DNS per pod |
| Use case | Stateless apps | Databases, queues, distributed systems |

### Headless Service

`clusterIP: None` — no load balancing, creates DNS A records per pod:
```
devops-sts-devops-info-service-0.devops-sts-devops-info-service-headless.default.svc.cluster.local
devops-sts-devops-info-service-1.devops-sts-devops-info-service-headless.default.svc.cluster.local
devops-sts-devops-info-service-2.devops-sts-devops-info-service-headless.default.svc.cluster.local
```

---

## 2. Resource Verification

```
$ kubectl get po,sts,svc,pvc

NAME                                   READY   STATUS    AGE
pod/devops-sts-devops-info-service-0   1/1     Running   72s
pod/devops-sts-devops-info-service-1   1/1     Running   63m
pod/devops-sts-devops-info-service-2   1/1     Running   62m

NAME                                              READY   AGE
statefulset.apps/devops-sts-devops-info-service   3/3     63m

NAME                                              TYPE        CLUSTER-IP     PORT(S)
service/devops-sts-devops-info-service            NodePort    10.105.88.57   80:30080/TCP
service/devops-sts-devops-info-service-headless   ClusterIP   None           80/TCP

NAME                                                        STATUS   CAPACITY   ACCESS MODES
persistentvolumeclaim/data-devops-sts-devops-info-service-0 Bound    100Mi      RWO
persistentvolumeclaim/data-devops-sts-devops-info-service-1 Bound    100Mi      RWO
persistentvolumeclaim/data-devops-sts-devops-info-service-2 Bound    100Mi      RWO
```

Each pod has its own PVC — `data-<name>-0`, `data-<name>-1`, `data-<name>-2`.

---

## 3. Network Identity — DNS Resolution

```bash
$ kubectl exec devops-sts-devops-info-service-0 -- python3 -c \
  "import socket; print(socket.gethostbyname(
    'devops-sts-devops-info-service-1.devops-sts-devops-info-service-headless.default.svc.cluster.local'
  ))"
10.244.0.5
```

Pod-0 can resolve pod-1 by stable DNS name → IP `10.244.0.5`.

---

## 4. Per-Pod Storage Evidence

Each pod maintains its own visit counter in its own PVC:

```bash
$ for pod in 0 1 2; do
    echo -n "pod-$pod visits: "
    kubectl exec devops-sts-devops-info-service-$pod -- sh -c 'cat /data/visits'
  done

pod-0 visits: 18
pod-1 visits: 21
pod-2 visits: 13
```

Pods have different counts — storage is isolated per pod.

---

## 5. Persistence Test

```bash
# Before deletion
$ kubectl exec devops-sts-devops-info-service-0 -- sh -c 'cat /data/visits'
18

# Delete pod
$ kubectl delete pod devops-sts-devops-info-service-0
pod "devops-sts-devops-info-service-0" deleted

# Pod restarts automatically (StatefulSet controller)
$ kubectl get pod devops-sts-devops-info-service-0
NAME                               READY   STATUS    RESTARTS   AGE
devops-sts-devops-info-service-0   1/1     Running   0          30s

# After restart — same PVC reattached
$ kubectl exec devops-sts-devops-info-service-0 -- sh -c 'cat /data/visits'
18   ✅ data survived pod deletion
```

---

## Bonus — Update Strategies

### Partitioned Rolling Update

```bash
kubectl patch statefulset devops-sts-devops-info-service --type=json \
  -p='[{"op":"replace","path":"/spec/updateStrategy/rollingUpdate/partition","value":2}]'
```

With `partition: 2` — only pods with ordinal **>= 2** get updated.
Pods 0 and 1 keep the old version. Useful for canary-style StatefulSet updates.

```yaml
updateStrategy:
  type: RollingUpdate
  rollingUpdate:
    partition: 2
```

### OnDelete Strategy

```yaml
updateStrategy:
  type: OnDelete
```

Pods only update when **manually deleted**. Gives full control over when each pod restarts.
Use case: databases where you want to control exactly when each replica restarts.

### Comparison

| Strategy | When pods update | Use case |
|----------|-----------------|---------|
| RollingUpdate (default) | Automatically, ordered | Standard updates |
| RollingUpdate + partition | Only pods >= partition | Canary-style staged rollout |
| OnDelete | Only when manually deleted | Full manual control |
