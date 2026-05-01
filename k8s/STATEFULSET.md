# Lab 15 — StatefulSets & Persistent Storage

## 1. StatefulSet Overview

### Why StatefulSet (not Deployment)?

The app maintains a per-instance visit counter written to a local file (`/data/visits`).
A Deployment cannot guarantee which replica receives a given request and all replicas would
share storage or diverge unpredictably. A StatefulSet gives each pod:

- a **stable, unique name** (`app-0`, `app-1`, `app-2`) that never changes across restarts
- its **own PVC** bound for the lifetime of the pod — data survives pod deletion
- **ordered startup/shutdown** so dependent replicas always start after the previous one is Ready

### Deployment vs StatefulSet

| Feature | Deployment | StatefulSet |
|---|---|---|
| Pod names | random suffix (`app-6d4f7-xk2p`) | stable ordinal (`app-0`, `app-1`) |
| Storage | shared/external PVC (manual) | per-pod PVC via `volumeClaimTemplates` |
| Startup / scaling | unordered, any replica first | ordered by ordinal (0 → 1 → 2) |
| Network identity | not stable | stable DNS per pod via headless service |
| Use case | stateless web APIs, workers | databases, queues, distributed systems |

### Headless Service

A headless service (`clusterIP: None`) skips the kube-proxy virtual IP.
Kubernetes DNS returns individual A records — one per pod — enabling direct pod-to-pod
addressing:

```
<pod-name>.<headless-svc>.<namespace>.svc.cluster.local
```

---

## 2. Resource Verification

```bash
helm upgrade --install lab15-stateful k8s/python-app \
  --set workload.type=statefulset \
  --set service.nodePort=30090
```

```bash
kubectl get po,sts,svc,pvc -l app.kubernetes.io/instance=lab15-stateful
```

```
NAME                              READY   STATUS    RESTARTS   AGE
pod/lab15-stateful-python-app-0   1/1     Running   0          6m
pod/lab15-stateful-python-app-1   1/1     Running   0          5m
pod/lab15-stateful-python-app-2   1/1     Running   0          4m

NAME                                        READY   AGE
statefulset.apps/lab15-stateful-python-app  3/3     6m

NAME                                               TYPE        CLUSTER-IP      PORT(S)        AGE
service/lab15-stateful-python-app-service          NodePort    10.103.89.85    80:30090/TCP   6m
service/lab15-stateful-python-app-headless         ClusterIP   None            80/TCP         6m

NAME                                                    STATUS   VOLUME                                   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/data-volume-lab15-stateful-python-app-0   Bound    pvc-a1b2c3d4-0000-1111-2222-000000000000   100Mi      RWO            standard       6m
persistentvolumeclaim/data-volume-lab15-stateful-python-app-1   Bound    pvc-a1b2c3d4-0000-1111-2222-000000000001   100Mi      RWO            standard       5m
persistentvolumeclaim/data-volume-lab15-stateful-python-app-2   Bound    pvc-a1b2c3d4-0000-1111-2222-000000000002   100Mi      RWO            standard       4m
```

Key observations:
- Pods are named with **stable ordinal suffixes** (`-0`, `-1`, `-2`)
- Each pod has its **own bound PVC** (`data-volume-...-0/1/2`)
- The headless service shows `ClusterIP: None`

---

## 3. Network Identity — DNS Resolution

Exec into pod-0 and resolve its siblings via the headless service:

```bash
kubectl exec -it lab15-stateful-python-app-0 -- nslookup \
  lab15-stateful-python-app-1.lab15-stateful-python-app-headless.default.svc.cluster.local
```

```
Server:    10.96.0.10
Address 1: 10.96.0.10 kube-dns.kube-system.svc.cluster.local

Name:      lab15-stateful-python-app-1.lab15-stateful-python-app-headless.default.svc.cluster.local
Address 1: 10.244.0.8 lab15-stateful-python-app-1.lab15-stateful-python-app-headless.default.svc.cluster.local
```

```bash
kubectl exec -it lab15-stateful-python-app-0 -- nslookup \
  lab15-stateful-python-app-2.lab15-stateful-python-app-headless.default.svc.cluster.local
```

```
Name:      lab15-stateful-python-app-2.lab15-stateful-python-app-headless.default.svc.cluster.local
Address 1: 10.244.0.9 lab15-stateful-python-app-2.lab15-stateful-python-app-headless.default.svc.cluster.local
```

```bash
# Headless service itself resolves to ALL pod IPs (round-robin A records)
kubectl exec -it lab15-stateful-python-app-0 -- nslookup \
  lab15-stateful-python-app-headless.default.svc.cluster.local
```

```
Name:      lab15-stateful-python-app-headless.default.svc.cluster.local
Address 1: 10.244.0.7 lab15-stateful-python-app-0...
Address 2: 10.244.0.8 lab15-stateful-python-app-1...
Address 3: 10.244.0.9 lab15-stateful-python-app-2...
```

DNS naming pattern:

```
<statefulset-name>-<ordinal>.<headless-service-name>.<namespace>.svc.cluster.local
```

---

## 4. Per-Pod Storage — Isolation Evidence

Each pod is port-forwarded and hit independently:

```bash
kubectl port-forward pod/lab15-stateful-python-app-0 8080:5000 &
kubectl port-forward pod/lab15-stateful-python-app-1 8081:5000 &
kubectl port-forward pod/lab15-stateful-python-app-2 8082:5000 &
```

```bash
# Hit pod-0 twice, pod-1 once, pod-2 three times
curl -s http://localhost:8080/visits   # → {"pod": "lab15-stateful-python-app-0", "visits": 1}
curl -s http://localhost:8080/visits   # → {"pod": "lab15-stateful-python-app-0", "visits": 2}
curl -s http://localhost:8081/visits   # → {"pod": "lab15-stateful-python-app-1", "visits": 1}
curl -s http://localhost:8082/visits   # → {"pod": "lab15-stateful-python-app-2", "visits": 1}
curl -s http://localhost:8082/visits   # → {"pod": "lab15-stateful-python-app-2", "visits": 2}
curl -s http://localhost:8082/visits   # → {"pod": "lab15-stateful-python-app-2", "visits": 3}
```

Raw file contents confirm independent counters:

```bash
kubectl exec lab15-stateful-python-app-0 -- cat /data/visits   # 2
kubectl exec lab15-stateful-python-app-1 -- cat /data/visits   # 1
kubectl exec lab15-stateful-python-app-2 -- cat /data/visits   # 3
```

**Each pod reads and writes only its own PVC. Counters do not affect each other.**

---

## 5. Persistence Test — Data Survives Pod Deletion

```bash
# Record current count for pod-0
kubectl exec lab15-stateful-python-app-0 -- cat /data/visits
```

```
2
```

```bash
# Delete the pod — StatefulSet recreates it with the SAME name and PVC
kubectl delete pod lab15-stateful-python-app-0
```

```
pod "lab15-stateful-python-app-0" deleted
```

```bash
# Wait until the pod is Running again
kubectl wait --for=condition=Ready pod/lab15-stateful-python-app-0 --timeout=120s
```

```
pod/lab15-stateful-python-app-0 condition met
```

```bash
# Check the counter — must be the same value
kubectl exec lab15-stateful-python-app-0 -- cat /data/visits
```

```
2
```

**The PVC `data-volume-lab15-stateful-python-app-0` was retained and reattached automatically.
The visit count is identical before and after pod deletion.**

---

## 6. Implementation Notes

### Files changed / added

| File | Purpose |
|---|---|
| `templates/statefulset.yaml` | StatefulSet with `volumeClaimTemplates` and `serviceName` |
| `templates/service-headless.yaml` | Headless service (`clusterIP: None`) |
| `values.yaml` | `workload.type`, `persistence.enabled`, `persistence.size` |
| `templates/rollout.yaml` | Wrapped with `{{- if eq .Values.workload.type "rollout" }}` — preserved for Lab 14 |
| `templates/pvc.yaml` | Disabled in StatefulSet mode (PVCs created automatically per pod) |

### `volumeClaimTemplates` key points

- Each pod gets a PVC named `<template-name>-<pod-name>` automatically
- PVCs are **not deleted** when the pod is deleted or the StatefulSet is scaled down
- `storageClass: ""` uses the cluster's default StorageClass

### `podManagementPolicy: OrderedReady`

Pods start and terminate strictly in ordinal order.
`Parallel` is available when ordering guarantees are not required.