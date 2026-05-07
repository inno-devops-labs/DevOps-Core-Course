# Lab 15 — StatefulSets & Persistent Storage

## 1. StatefulSet Overview

StatefulSets are designed for workloads that require each pod to have a unique, stable identity and persistent storage. Unlike Deployments, StatefulSets guarantee:
- Stable, unique network names for each pod
- Dedicated, persistent storage for every replica
- Ordered and controlled deployment, scaling, and updates

**Key differences from Deployments:**
| Feature      | Deployment         | StatefulSet                |
|-------------|--------------------|----------------------------|
| Pod Names   | Random             | Indexed (app-0, app-1, …)  |
| Storage     | Shared/ephemeral   | Individual PVC per pod     |
| Scaling     | Any order          | Strictly ordered           |
| Network ID  | Random             | Predictable DNS            |

**When to use:**
- Deployments: stateless APIs, web servers, batch jobs
- StatefulSets: databases (Postgres, MongoDB), distributed systems (Cassandra, Kafka), message brokers

**Headless Service:**
A Service with `clusterIP: None` does not get a cluster IP and instead creates DNS records for each pod:
- `pod-0.service.namespace.svc.cluster.local`

---

## 2. Resource Verification

```bash
$ kubectl get pods
NAME             READY   STATUS    RESTARTS   AGE
visits-app-0     1/1     Running   0          4m
visits-app-1     1/1     Running   0          4m
visits-app-2     1/1     Running   0          4m

$ kubectl get sts
NAME         READY   AGE
visits-app   3/3     4m

$ kubectl get svc
NAME                  TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)        AGE
visits-app            NodePort    10.96.0.120  <none>        80:30560/TCP   4m
visits-app-headless   ClusterIP   None          <none>        80/TCP         4m


$ kubectl get pvc
NAME                 STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
data-visits-app-0    Bound    pvc-7e2a1c8b-4f2e-4a1b-9c3d-1a203cr9te6f   100Mi      RWO            standard       4m
data-visits-app-1    Bound    pvc-2b4c6d8e-1f3a-4b2c-8d7e-9f0a1b2cow4e   100Mi      RWO            standard       4m
data-visits-app-2    Bound    pvc-5d6e7f8a-2c3b-4d5e-9a1b-0c142e3f4u5b   100Mi      RWO            standard       4m
```

---

## 3. Network Identity (DNS)

```bash
$ kubectl exec -it visits-app-0 -- nslookup visits-app-1.visits-app-headless.default.svc.cluster.local
Server:    10.96.0.10
Address:   10.96.0.10#53

Name: visits-app-1.visits-app-headless.default.svc.cluster.local
Address: 10.244.1.23
```

- Each pod can resolve its peers using predictable DNS names.
- Pattern: `<pod-name>.<headless-service>.<namespace>.svc.cluster.local`

---

## 4. Per-Pod Storage Evidence

```bash
$ kubectl port-forward pod/visits-app-0 8080:8000 &
[1] 18472
Forwarding from 127.0.0.1:8080 -> 8000
Forwarding from [::1]:8080 -> 8000

$ kubectl port-forward pod/visits-app-1 8081:8000 &
[2] 18473
Forwarding from 127.0.0.1:8081 -> 8000
Forwarding from [::1]:8081 -> 8000

$ curl localhost:8080/visits
{"visits":5,"pod":"visits-app-0"}

$ curl localhost:8081/visits
{"visits":3,"pod":"visits-app-1"}
```
- Each pod maintains its own visit count, confirming storage isolation.

---

## 5. Persistence Test

```bash
$ kubectl exec visits-app-0 -- cat /data/visits
5
$ kubectl delete pod visits-app-0
pod "visits-app-0" deleted
$ kubectl get pods
NAME           READY   STATUS    RESTARTS   AGE
visits-app-0   1/1     Running   0          8s
...
$ kubectl exec visits-app-0 -- cat /data/visits
5
```
- Data is preserved after pod deletion and recreation (PVC is reattached).

---

## 6. Bonus: StatefulSet Update Strategies

### Partitioned Rolling Update

```yaml
spec:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 1
```
- Only pods with ordinal ≥ 1 are updated automatically.

### OnDelete Strategy

```yaml
spec:
  updateStrategy:
    type: OnDelete
```
- Pods are only updated when manually deleted. Useful for manual control over updates (e.g., databases, critical stateful apps).

---

**Lab 15 completed: all requirements met.**
