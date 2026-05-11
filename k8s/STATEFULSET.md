# StatefulSets & Persistent Storage — Lab 15

## StatefulSet Overview

### Why StatefulSet?

StatefulSets are used for applications that require:

* Stable pod names and identities
* Persistent storage for each pod
* Ordered deployment and scaling
* Stable DNS records

Unlike Deployments or Rollouts, StatefulSets guarantee that each pod keeps the same identity after restarts.

Typical use cases:

* PostgreSQL
* MySQL
* MongoDB
* Kafka
* Elasticsearch
* RabbitMQ

---

## Deployment vs StatefulSet

| Feature          | Deployment         | StatefulSet                |
| ---------------- | ------------------ | -------------------------- |
| Pod Names        | Random suffix      | Stable ordinal names       |
| Storage          | Shared or external | Per-pod persistent storage |
| Scaling          | Parallel           | Ordered                    |
| Network Identity | Dynamic            | Stable DNS names           |
| Use Case         | Stateless apps     | Stateful apps              |

Example:

Deployment pod names:

```bash
myapp-6f5b7d6c7d-x9p2k
```

StatefulSet pod names:

```bash
myapp-dev-0
myapp-dev-1
myapp-dev-2
```

---

# Headless Service

A headless service is a Kubernetes Service with:

```yaml
clusterIP: None
```

This allows direct DNS resolution to StatefulSet pods.

Example DNS pattern:

```text
<pod-name>.<headless-service>.<namespace>.svc.cluster.local
```

Example:

```text
myapp-dev-0.myapp-dev-headless.dev.svc.cluster.local
```

---

# StatefulSet Implementation

## StatefulSet Features Implemented

* StatefulSet controller
* Headless service
* PersistentVolumeClaim templates
* Stable pod identities
* Persistent storage
* Helm integration
* ArgoCD deployment

---

# Resource Verification

## StatefulSet

```bash
kubectl get sts -n dev
```

Example output:

```bash
NAME        READY   AGE
myapp-dev   3/3     10m
```

---

## Pods

```bash
kubectl get pods -n dev -o wide
```

Example output:

```bash
NAME          READY   STATUS    RESTARTS   AGE
myapp-dev-0   1/1     Running   0          10m
myapp-dev-1   1/1     Running   0          10m
myapp-dev-2   1/1     Running   0          10m
```

This confirms stable pod identities.

---

## Services

```bash
kubectl get svc -n dev
```

Example output:

```bash
NAME                    TYPE        CLUSTER-IP   PORT(S)
myapp-dev               NodePort    10.x.x.x     80:xxxxx/TCP
myapp-dev-headless      ClusterIP   None         80/TCP
```

This confirms that the headless service was created successfully.

---

## PersistentVolumeClaims

```bash
kubectl get pvc -n dev
```

Example output:

```bash
NAME                         STATUS   VOLUME
myapp-dev-data-myapp-dev-0   Bound    pvc-xxxxx
myapp-dev-data-myapp-dev-1   Bound    pvc-yyyyy
myapp-dev-data-myapp-dev-2   Bound    pvc-zzzzz
```

Each pod receives its own persistent volume.

---

# DNS Resolution Test

A temporary BusyBox pod was used for DNS testing.

Command:

```bash
kubectl run dns-test \
  -n dev \
  --image=busybox:1.36 \
  --rm -it --restart=Never -- sh
```

Inside the container:

```bash
nslookup myapp-dev-1.myapp-dev-headless.dev.svc.cluster.local
```

Expected result:

```bash
Name: myapp-dev-1.myapp-dev-headless.dev.svc.cluster.local
Address: <pod-ip>
```

This demonstrates stable DNS identities for StatefulSet pods.

---

# Per-Pod Storage Isolation

Each StatefulSet pod stores its own visit counter in persistent storage.

Port-forward commands:

```bash
kubectl port-forward pod/myapp-dev-0 -n dev 8080:5000
kubectl port-forward pod/myapp-dev-1 -n dev 8081:5000
kubectl port-forward pod/myapp-dev-2 -n dev 8082:5000
```

Testing:

```bash
curl http://localhost:8080/visits
curl http://localhost:8081/visits
curl http://localhost:8082/visits
```

Example:

```text
pod-0 -> visits: 3
pod-1 -> visits: 7
pod-2 -> visits: 1
```

This proves storage isolation between pods.

---

# Persistence Test

Visit counters were stored inside persistent volumes.

Check stored data:

```bash
kubectl exec -it myapp-dev-0 -n dev -- cat /data/visits
```

Delete pod:

```bash
kubectl delete pod myapp-dev-0 -n dev
```

Wait for recreation:

```bash
kubectl get pods -n dev -w
```

Verify persistence:

```bash
kubectl exec -it myapp-dev-0 -n dev -- cat /data/visits
```

The visit counter remained unchanged after pod recreation.

This confirms persistent storage functionality.

---

# Update Strategies (Bonus)

## RollingUpdate with Partition

Configured:

```yaml
updateStrategy:
  type: RollingUpdate
  rollingUpdate:
    partition: 2
```

Behavior:

* Only pods with ordinal >= 2 are updated automatically
* Lower ordinal pods remain untouched
* Useful for controlled rollouts of stateful workloads

---

## OnDelete Strategy

Alternative strategy:

```yaml
updateStrategy:
  type: OnDelete
```

Behavior:

* Pods update only after manual deletion
* Useful for databases and critical stateful systems
* Gives operators full control over restarts

---

# ArgoCD Deployment

Application was deployed using ArgoCD.

Sync command:

```bash
argocd app sync myapp-dev --prune
```

Final application status:

```bash
Sync Status: Synced
Health Status: Healthy
```

---

# Conclusion

In this lab:

* Deployment/Rollout was converted to StatefulSet
* Stable pod identities were implemented
* Headless service was configured
* Per-pod persistent storage was configured
* DNS-based pod discovery was tested
* Persistent data survived pod recreation
* ArgoCD successfully managed StatefulSet deployment

The application now behaves as a proper stateful Kubernetes workload.