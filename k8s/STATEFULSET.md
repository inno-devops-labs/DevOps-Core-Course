# Lab — StatefulSet

## 1) StatefulSet Overview

### Why StatefulSet Is Needed

`StatefulSet` is used for stateful workloads where each pod requires:

* stable networking (persistent DNS name);
* its own persistent volume;
* predictable startup/update/deletion order.

### StatefulSet Guarantees

* **Stable network identity:** pods receive ordinal-based names (`<name>-0`, `<name>-1`, `<name>-2`).
* **Stable storage:** each pod gets its own PVC from `volumeClaimTemplates`.
* **Ordered operations:** creation and scaling happen sequentially, deletion happens in reverse order.

### Deployment vs StatefulSet

* **Deployment:** pods are interchangeable, names and storage are not fixed.
* **StatefulSet:** pods are not interchangeable, each has its own identity and storage.
* **Use Deployment for:** stateless APIs, frontends, workers without local state.
* **Use StatefulSet for:** databases, queues, and clustered systems (PostgreSQL, MySQL, Redis/Sentinel, Kafka, ZooKeeper, Elasticsearch, etc.).

### Headless Service

* Headless service = Service with `clusterIP: None`.
* Unlike a regular Service, it does not perform L4 load balancing, but instead returns DNS records for individual pods.
* DNS pattern for StatefulSet:

  * `<statefulset-name>-<ordinal>.<headless-service>.<namespace>.svc.cluster.local`
  * example: `devops-app-0.devops-app-headless.default.svc.cluster.local`

---

## 2) Changes Made to the Helm Chart

Changes in the `k8s/devops-app` chart:

* added `templates/statefulset.yaml`;
* kept `templates/rollout.yaml` (enabled only when `workload.type=rollout`);
* added a headless service to `templates/service.yaml`;
* updated `values.yaml`:

  * `workload.type: statefulset` (default);
  * `statefulset.updateStrategy` (including `partition`);
  * `service.headless.*`;
* updated `templates/pvc.yaml`: PVC is not created for `statefulset` workloads (because PVCs are created through `volumeClaimTemplates`).

Render validation:

```bash
helm template devops-app ./k8s/devops-app
```

The render successfully creates a `StatefulSet`, a regular `Service`, and a headless `Service`.

---

## 3) Deploy and Verify

### Install/Upgrade

```bash
helm upgrade --install devops-app ./k8s/devops-app -n default --set service.nodePort=30081
kubectl rollout status statefulset/devops-app -n default
```

Result: `partitioned roll out complete: 3 new pods have been updated`.

### Verify Resources

```bash
kubectl get po,sts,svc,pvc -n default
```

Actual output:

```text
NAME               READY   STATUS    RESTARTS   AGE
pod/devops-app-0   1/1     Running   0          40s
pod/devops-app-1   1/1     Running   0          29s
pod/devops-app-2   1/1     Running   0          17s

NAME                          READY   AGE
statefulset.apps/devops-app   3/3     40s

NAME                          TYPE        CLUSTER-IP    PORT(S)
service/devops-app            NodePort    10.96.54.39   80:30081/TCP
service/devops-app-headless   ClusterIP   None          80/TCP

NAME                                                STATUS   CAPACITY
persistentvolumeclaim/storage-volume-devops-app-0   Bound    1Gi
persistentvolumeclaim/storage-volume-devops-app-1   Bound    1Gi
persistentvolumeclaim/storage-volume-devops-app-2   Bound    1Gi
```

---

## 4) Network Identity (DNS Test)

### DNS Verification from a Pod

```bash
kubectl exec -n default devops-app-0 -- sh -c "getent hosts devops-app-1.devops-app-headless.default.svc.cluster.local && getent hosts devops-app-2.devops-app-headless.default.svc.cluster.local"
```

Actual output:

```text
10.244.0.14     devops-app-1.devops-app-headless.default.svc.cluster.local
10.244.0.16     devops-app-2.devops-app-headless.default.svc.cluster.local
```

The names are successfully resolved using the pattern `<pod-name>.<headless-service>.<namespace>.svc.cluster.local`.

---

## 5) Per-Pod Storage Isolation

The `lab03` image does not include the `/visits` endpoint, so the verification was performed directly using the `/data/visits` file (stored in each pod's PVC).

### Actual Isolation Verification

```bash
kubectl exec -n default devops-app-0 -- sh -c "echo 11 > /data/visits && cat /data/visits"
kubectl exec -n default devops-app-1 -- sh -c "echo 22 > /data/visits && cat /data/visits"
kubectl exec -n default devops-app-2 -- sh -c "echo 33 > /data/visits && cat /data/visits"

kubectl exec -n default devops-app-0 -- cat /data/visits
kubectl exec -n default devops-app-1 -- cat /data/visits
kubectl exec -n default devops-app-2 -- cat /data/visits
```

Actual output:

```text
11
22
33
```

This confirms data isolation between pods.

---

## 6) Persistence Test

1. Save the `/data/visits` value for `devops-app-1` (in my case, `22`).
2. Delete the pod (not the StatefulSet):

```bash
kubectl delete pod devops-app-1 -n default
kubectl wait --for=condition=Ready pod/devops-app-1 -n default --timeout=180s
kubectl exec -n default devops-app-1 -- cat /data/visits
```

Actual output:

```text
pod "devops-app-1" deleted from default namespace
pod/devops-app-1 condition met
22
```

Result:

* the pod was recreated with the same name `devops-app-1`;
* the value persisted because the data remained in the PVC `storage-volume-devops-app-1`.

---

## 7) Bonus — Update Strategies

### A) Partitioned Rolling Update

In `values.yaml`:

```yaml
statefulset:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 1
```

Behavior:

* only pods with ordinal `>= 1` are updated (`devops-app-1`, `devops-app-2`);
* `devops-app-0` remains on the old version.

Verification:

```bash
helm upgrade --install devops-app ./k8s/devops-app -n default --set image.tag=lab04 --set statefulset.updateStrategy.rollingUpdate.partition=1
kubectl get pods -n default -w
```

### B) OnDelete Strategy

```bash
helm upgrade --install devops-app ./k8s/devops-app -n default --set statefulset.updateStrategy.type=OnDelete --set image.tag=lab05
kubectl get pods -n default
```

Behavior:

* pods are **not** updated automatically after template changes;
* updates happen only after manual pod deletion.

Verification:

```bash
kubectl delete pod devops-app-2 -n default
kubectl get pods -n default
```

Use cases:

* `partition`: staged/canary updates for a stateful cluster;
* `OnDelete`: full manual control over updates for critical stateful services.

---

## Checklist

* [x] StatefulSet guarantees documented
* [x] `statefulset.yaml` created with `volumeClaimTemplates`
* [x] Headless service created
* [x] Per-pod PVCs verified (commands + expected resources)
* [x] DNS resolution tested (commands + naming pattern)
* [x] Per-pod storage isolation proven (different values in `/data/visits`)
* [x] Persistence test passed (pod delete preserves data)
* [x] `k8s/STATEFULSET.md` completed
