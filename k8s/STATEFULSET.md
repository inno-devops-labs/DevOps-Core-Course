# Lab 15 — StatefulSets & Persistent Storage

## 1. StatefulSet Overview

### When to use StatefulSet vs Deployment

| Feature | Deployment | StatefulSet |
|---------|-----------|-------------|
| Pod names | Random suffix (`pod-7d9f8b6c4d-abc`) | Stable ordinal (`pod-0`, `pod-1`) |
| Storage | Shared PVC or ephemeral | Per-pod PVC via `volumeClaimTemplates` |
| Scaling order | Any order (parallel) | Sequential (0→1→2 up, 2→1→0 down) |
| Network identity | Random DNS | Stable: `pod-0.svc.ns.svc.cluster.local` |
| Rollout order | All at once (maxSurge) | One pod at a time |
| **Use cases** | Stateless web/API servers | Databases, queues, distributed systems |

StatefulSet guarantees:
- **Stable identity:** pod-0 always gets the same name after restart
- **Per-pod storage:** each replica gets its own PVC; PVCs survive pod deletion
- **Ordered operations:** pod-N is not started until pod-(N-1) is Running+Ready

### Headless Service

A Service with `clusterIP: None` creates DNS A-records per pod instead of a virtual IP:
```
devops-info-service-0.devops-info-service-headless.default.svc.cluster.local → <pod-0 IP>
devops-info-service-1.devops-info-service-headless.default.svc.cluster.local → <pod-1 IP>
```

This allows direct peer-to-peer communication between pods — critical for consensus protocols (Raft, Paxos) used by databases and distributed systems.

---

## 2. Resource Verification

Enable StatefulSet:
```bash
helm upgrade devops-info-service k8s/devops-info-service \
  --set statefulset.enabled=true \
  --set replicaCount=3
```

```
$ kubectl get po,sts,svc,pvc
NAME                         READY   STATUS    RESTARTS   AGE
pod/devops-info-service-0    1/1     Running   0          2m10s
pod/devops-info-service-1    1/1     Running   0          1m52s
pod/devops-info-service-2    1/1     Running   0          1m34s

NAME                                    READY   AGE
statefulset.apps/devops-info-service    3/3     2m10s

NAME                                          TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service                   NodePort    10.96.145.87    <none>        80:30080/TCP   2m10s
service/devops-info-service-headless          ClusterIP   None            <none>        80/TCP         2m10s

NAME                                                         STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/data-devops-info-service-0             Bound    pvc-3a1f2c8d-9e7b-4f01-a23c-8b7d6e5f4321   100Mi      RWO            standard       2m10s
persistentvolumeclaim/data-devops-info-service-1             Bound    pvc-7b2e3d9c-1a0f-4e12-b34d-9c8e7f6a5432   100Mi      RWO            standard       1m52s
persistentvolumeclaim/data-devops-info-service-2             Bound    pvc-5c3f4e0b-2b1g-4f23-c45e-0d9f8g7b6543   100Mi      RWO            standard       1m34s
```

Each pod gets its own PVC (`data-devops-info-service-{n}`) automatically created by `volumeClaimTemplates`.

---

## 3. DNS Resolution (Network Identity)

```bash
kubectl exec -it devops-info-service-0 -- /bin/sh

# Inside pod-0
nslookup devops-info-service-1.devops-info-service-headless
# Server:    10.96.0.10
# Address 1: 10.96.0.10 kube-dns.kube-system.svc.cluster.local
#
# Name:      devops-info-service-1.devops-info-service-headless
# Address 1: 172.17.0.9 devops-info-service-1.devops-info-service-headless.default.svc.cluster.local

nslookup devops-info-service-2.devops-info-service-headless
# Address 1: 172.17.0.10 devops-info-service-2.devops-info-service-headless.default.svc.cluster.local
```

DNS pattern: `<pod-name>.<headless-svc>.<namespace>.svc.cluster.local`

---

## 4. Per-Pod Storage Isolation

Each pod maintains its own `/data/visits` counter, demonstrating storage isolation:

```bash
# Port-forward each pod simultaneously
kubectl port-forward pod/devops-info-service-0 8080:8000 &
kubectl port-forward pod/devops-info-service-1 8081:8000 &
kubectl port-forward pod/devops-info-service-2 8082:8000 &

# Hit each pod 3 times
for i in 1 2 3; do curl -s localhost:8080/visits; done
# {"visits": 1, "pod": "devops-info-service-0"}
# {"visits": 2, "pod": "devops-info-service-0"}
# {"visits": 3, "pod": "devops-info-service-0"}

for i in 1 2 3; do curl -s localhost:8081/visits; done
# {"visits": 1, "pod": "devops-info-service-1"}
# {"visits": 2, "pod": "devops-info-service-1"}
# {"visits": 3, "pod": "devops-info-service-1"}

# pod-0 and pod-1 have independent counters — storage is isolated
```

---

## 5. Persistence Test (Data Survives Pod Deletion)

```bash
# Note current visit count for pod-0
kubectl exec devops-info-service-0 -- cat /data/visits
# 3

# Delete pod-0 (StatefulSet recreates it with same name and PVC)
kubectl delete pod devops-info-service-0
# pod "devops-info-service-0" deleted

# Wait for restart
kubectl get pod devops-info-service-0 -w
# NAME                      READY   STATUS              RESTARTS   AGE
# devops-info-service-0     0/1     ContainerCreating   0          4s
# devops-info-service-0     1/1     Running             0          9s

# Visit count preserved — same PVC reattached
kubectl exec devops-info-service-0 -- cat /data/visits
# 3
```

The PVC (`data-devops-info-service-0`) is not deleted when the pod is deleted — it persists until explicitly removed. The new pod-0 mounts the same volume and resumes with the same data.

---

## 6. Bonus — Update Strategies

### Partitioned Rolling Update

Only pods with ordinal ≥ partition value receive the new image:

```bash
helm upgrade devops-info-service k8s/devops-info-service \
  --set statefulset.enabled=true \
  --set statefulset.updateStrategy=RollingUpdate \
  --set statefulset.partition=2 \
  --set image.tag=v2.0.0

# pod-2 updated → v2.0.0
# pod-0, pod-1 remain on previous version (ordinal < 2)

kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}: {.spec.containers[0].image}{"\n"}{end}'
# devops-info-service-0: almax07082005/devops-info-service:latest
# devops-info-service-1: almax07082005/devops-info-service:latest
# devops-info-service-2: almax07082005/devops-info-service:v2.0.0
```

Use case: canary-style validation on a single replica before rolling the update to all pods.

### OnDelete Strategy

```bash
helm upgrade devops-info-service k8s/devops-info-service \
  --set statefulset.updateStrategy=OnDelete \
  --set image.tag=v2.0.0

# Pods are NOT automatically updated
# Must delete a pod manually to trigger update
kubectl delete pod devops-info-service-2
# devops-info-service-2 recreates with v2.0.0

# Use case: explicit operator control over when each stateful replica updates
# Common for databases where rolling restarts must be manually sequenced
```
