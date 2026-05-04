# Lab 15 — StatefulSets & Persistent Storage

## 1. StatefulSet Overview

This lab demonstrates how to run a stateful application in Kubernetes using a StatefulSet, Headless Service, and per-pod PersistentVolumeClaims.

Unlike Deployments or Rollouts, StatefulSets are used when an application needs:

- stable pod names
- stable network identities
- stable persistent storage per replica
- ordered pod creation and termination

Examples of workloads that benefit from StatefulSets include:

- databases such as PostgreSQL, MySQL, MongoDB
- message brokers such as Kafka or RabbitMQ
- distributed systems such as Cassandra or Elasticsearch

## 2. StatefulSet vs Deployment

| Feature | Deployment | StatefulSet |
|---|---|---|
| Pod names | Random suffixes | Stable ordinal names |
| Pod identity | Disposable | Stable |
| Storage | Shared or manually attached PVC | Per-pod PVC via `volumeClaimTemplates` |
| Scaling | Pods can be created/deleted in any order | Pods are created in ordered sequence |
| Networking | Normal Service load-balances across pods | Headless Service enables stable pod DNS |
| Best use case | Stateless applications | Stateful applications |

A Deployment is better for stateless workloads where any pod can replace another pod.

A StatefulSet is better when each replica needs its own identity and its own persistent data.

---

## 3. Helm Chart Changes

For this lab, the previous Rollout-based workload was disabled and a StatefulSet was added.

New templates added:

```text
app-python-chart/templates/statefulset.yaml
app-python-chart/templates/service-headless.yaml
```

The Rollout file was kept separately for reference:

```text
app-python-chart/disabled/rollout.yaml
```

## 4. StatefulSet Configuration

The StatefulSet uses the existing application container but attaches a per-pod persistent volume through `volumeClaimTemplates`.

Key StatefulSet fields:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: app-python-app-python-chart
spec:
  serviceName: app-python-app-python-chart-headless
  replicas: 3
```

The `serviceName` points to the headless service. This allows Kubernetes to create stable DNS names for each StatefulSet pod.

## 5. VolumeClaimTemplates

Each pod gets its own PVC automatically through:

```yaml
volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Mi
```

The application mounts this per-pod volume at:

```text
/data
```

The visits counter file is stored at:

```text
/data/visits
```

---

## 6. Headless Service

A headless service was created:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: app-python-app-python-chart-headless
spec:
  clusterIP: None
```

A headless service does not allocate a normal cluster IP. Instead, it creates DNS records that point directly to individual pods.

This enables stable DNS names such as:

```text
app-python-app-python-chart-0.app-python-app-python-chart-headless.default.svc.cluster.local
app-python-app-python-chart-1.app-python-app-python-chart-headless.default.svc.cluster.local
app-python-app-python-chart-2.app-python-app-python-chart-headless.default.svc.cluster.local
```

The existing NodePort service was kept for external access:

```text
app-python-app-python-chart   NodePort   80:30008/TCP
```

---

## 7. Resource Verification

The chart was validated successfully:

```bash
helm lint app-python-chart
```

Output:

```text
==> Linting app-python-chart
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

The rendered chart contains:

```text
kind: Service
name: app-python-app-python-chart-headless
clusterIP: None

kind: Service
name: app-python-app-python-chart

kind: StatefulSet
name: app-python-app-python-chart

volumeClaimTemplates:
  - metadata:
      name: data
```

## 8. StatefulSet Deployment Verification

The StatefulSet was deployed successfully:

```bash
kubectl get statefulset
kubectl get pods
kubectl get pvc
```

Output:

```text
NAME                          READY   AGE
app-python-app-python-chart   3/3     4m10s
```

Pods:

```text
NAME                            READY   STATUS    RESTARTS   AGE
app-python-app-python-chart-0   1/1     Running   0          4m11s
app-python-app-python-chart-1   1/1     Running   0          4m10s
app-python-app-python-chart-2   1/1     Running   0          4m9s
```

PVCs:

```text
NAME                                 STATUS   CAPACITY   ACCESS MODES   STORAGECLASS
data-app-python-app-python-chart-0   Bound    100Mi      RWO            standard
data-app-python-app-python-chart-1   Bound    100Mi      RWO            standard
data-app-python-app-python-chart-2   Bound    100Mi      RWO            standard
```

This proves that each StatefulSet pod received its own persistent volume.

---

## 9. Network Identity Test

Services:

```bash
kubectl get svc
```

Output:

```text
NAME                                   TYPE        CLUSTER-IP      PORT(S)
app-python-app-python-chart            NodePort    10.109.102.55   80:30008/TCP
app-python-app-python-chart-headless   ClusterIP   None            80/TCP
kubernetes                             ClusterIP   10.96.0.1       443/TCP
```

DNS configuration inside pod `app-python-app-python-chart-0`:

```bash
kubectl exec -it app-python-app-python-chart-0 -- cat /etc/resolv.conf
```

Output:

```text
nameserver 10.96.0.10
search default.svc.cluster.local svc.cluster.local cluster.local
options ndots:5
```

DNS resolution from pod `-0` to pod `-1`:

```bash
kubectl exec -it app-python-app-python-chart-0 -- getent hosts app-python-app-python-chart-1.app-python-app-python-chart-headless
```

Output:

```text
10.244.0.26 app-python-app-python-chart-1.app-python-app-python-chart-headless.default.svc.cluster.local
```

DNS resolution from pod `-0` to pod `-2`:

```bash
kubectl exec -it app-python-app-python-chart-0 -- getent hosts app-python-app-python-chart-2.app-python-app-python-chart-headless
```

Output:

```text
10.244.0.27 app-python-app-python-chart-2.app-python-app-python-chart-headless.default.svc.cluster.local
```

This confirms stable network identity through the headless service.

---

## 10. Per-Pod Storage Isolation

To prove that each pod has its own storage, different values were written to `/data/visits` inside each pod:

```bash
kubectl exec app-python-app-python-chart-0 -- sh -c 'echo 10 > /data/visits'
kubectl exec app-python-app-python-chart-1 -- sh -c 'echo 20 > /data/visits'
kubectl exec app-python-app-python-chart-2 -- sh -c 'echo 30 > /data/visits'
```

Then the values were read back:

```bash
kubectl exec app-python-app-python-chart-0 -- cat /data/visits
kubectl exec app-python-app-python-chart-1 -- cat /data/visits
kubectl exec app-python-app-python-chart-2 -- cat /data/visits
```

Output:

```text
10
20
30
```

This proves storage isolation:

- pod `-0` has value `10`
- pod `-1` has value `20`
- pod `-2` has value `30`

Each pod stores data in its own PVC.

---

## 11. Persistence Test

Pod `app-python-app-python-chart-1` was deleted and recreated by the StatefulSet controller.

After the pod came back, the stored value was checked again:

```bash
kubectl exec app-python-app-python-chart-1 -- cat /data/visits
```

Output:

```text
20
```

The pod was recreated with the same stable name:

```text
app-python-app-python-chart-1   1/1   Running
```

The PVC remained bound:

```text
data-app-python-app-python-chart-1   Bound   100Mi   RWO   standard
```

This proves that data survived pod deletion and restart.

---

## 12. Final Result

By the end of this lab, the following were successfully implemented and verified:

- StatefulSet created from Helm chart
- headless service created with `clusterIP: None`
- stable pod names verified:
  - `app-python-app-python-chart-0`
  - `app-python-app-python-chart-1`
  - `app-python-app-python-chart-2`
- per-pod PVCs created using `volumeClaimTemplates`
- stable DNS resolution tested through headless service
- storage isolation proven with different `/data/visits` values per pod
- persistence proven after deleting and recreating one pod

This confirms that StatefulSets are suitable for workloads that need stable identity and persistent per-replica storage.
