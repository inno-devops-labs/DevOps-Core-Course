# Lab 15 — StatefulSets and persistent storage

This document covers StatefulSet guarantees, how the `devops-info` Helm chart switches between Argo Rollouts and a StatefulSet, and verification on a live cluster.

**Evidence note:** Commands in sections 2–5 were run **2026-05-01** on minikube **`lab09`**, release **`lab15`** in namespace **`lab15`**.

## 1. StatefulSet overview

### 1.1 Guarantees (why StatefulSet exists)

A StatefulSet gives workloads that need stable identity and durable data:

- **Stable network IDs:** Pods are named `<statefulset>-0`, `<statefulset>-1`, … and keep those identities across rescheduling (the ordinal is stable).
- **Stable storage:** With `volumeClaimTemplates`, each ordinal gets its own PVC that stays bound to that identity (`data-volume-<sts>-0`, etc.).
- **Ordered lifecycle:** Default `podManagementPolicy: OrderedReady` scales and rolls pods in order (handy for clustered software that cares about startup order). `Parallel` relaxes that.

### 1.2 Deployment / Rollout vs StatefulSet

| Concern | Deployment / Rollout | StatefulSet |
|--------|----------------------|-------------|
| Pod names | Random suffix | Stable ordinal suffix |
| Storage | Typically one shared PVC or none | Per-pod PVCs via templates |
| Scaling order | Simultaneous / surge-based | Ordered by default (0 → 1 → 2) |
| Stable DNS per pod | Not built-in | Via headless Service |

Use **Deployments or Rollouts** for stateless HTTP services and progressive delivery. Use **StatefulSets** when each replica needs its own disk and/or a predictable hostname (databases, Kafka, etcd-like patterns).

### 1.3 Headless Services (`clusterIP: None`)

A headless Service does not allocate a single virtual IP for load balancing. Instead, the Kubernetes DNS publishes **one A/AAAA record per ready endpoint** (pod), so clients can resolve individual pods.

For a StatefulSet pod, the usual pattern is:

`<pod-name>.<headless-service>.<namespace>.svc.cluster.local`

Example for this lab:

`lab15-devops-info-1.lab15-devops-info-headless.lab15.svc.cluster.local`

The chart keeps the existing **NodePort/ClusterIP Service** for normal traffic while adding **`<fullname>-headless`** for stable per-pod DNS.

## 2. Helm wiring

- **`templates/statefulset.yaml`** — StatefulSet mirroring the Rollout pod template, with `serviceName` pointing at the headless Service and `volumeClaimTemplates` when `persistence.enabled` is true.
- **`templates/service-headless.yaml`** — Headless Service; rendered only when `statefulset.enabled` is true.
- **`templates/rollout.yaml`** — Rendered only when `statefulset.enabled` is false (default Lab 14 behavior).
- **`templates/pvc.yaml`** — Shared PVC for Rollout mode only; omitted in StatefulSet mode (PVCs come from templates).

Toggle StatefulSet mode via `values.yaml` → `statefulset.enabled`, or use the overlay:

```bash
helm upgrade --install lab15 ./k8s/devops-info \
  -n lab15 --create-namespace \
  -f k8s/devops-info/values-statefulset.yaml
```

Configurable knobs (see `values.yaml`): `statefulset.podManagementPolicy`, `statefulset.updateStrategy.type` (`RollingUpdate` or `OnDelete`), and `rollingUpdate.partition` when using `RollingUpdate`.

## 3. Resource verification

After install:

```bash
kubectl get po,sts,svc,pvc -n lab15
```

```text
NAME                      READY   STATUS    RESTARTS   AGE
pod/lab15-devops-info-0   1/1     Running   0          12s
pod/lab15-devops-info-1   1/1     Running   0          73s
pod/lab15-devops-info-2   1/1     Running   0          68s

NAME                                 READY   AGE
statefulset.apps/lab15-devops-info   3/3     78s

NAME                                 TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/lab15-devops-info            NodePort    10.110.162.197   <none>        80:31354/TCP   78s
service/lab15-devops-info-headless   ClusterIP   None             <none>        80/TCP         78s

NAME                                                    STATUS   VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS
persistentvolumeclaim/data-volume-lab15-devops-info-0   Bound    ...      100Mi      RWO            standard
persistentvolumeclaim/data-volume-lab15-devops-info-1   Bound    ...      100Mi      RWO            standard
persistentvolumeclaim/data-volume-lab15-devops-info-2   Bound    ...      100Mi      RWO            standard
```

Pods use ordinal names; each pod has its own PVC bound to `standard` storage on this cluster.

## 4. Network identity (DNS)

From `lab15-devops-info-0`, resolving another pod via the headless Service:

```bash
kubectl exec -n lab15 lab15-devops-info-0 -- \
  getent hosts lab15-devops-info-1.lab15-devops-info-headless.lab15.svc.cluster.local
```

```text
10.244.0.76     lab15-devops-info-1.lab15-devops-info-headless.lab15.svc.cluster.local
```

That matches CoreDNS naming: `<statefulset-pod>.<headless-svc>.<namespace>.svc.cluster.local`.

## 5. Per-pod storage and persistence

The app stores visit counts in `VISITS_FILE` (`/data/visits`, see `_helpers.tpl`). Traffic to `/` increments the counter; `GET /visits` reads it.

Driving different counts **inside each pod** (localhost avoids going through the Service):

```bash
# Example: 2, 5, and 1 visits on pods 0, 1, 2
kubectl exec -n lab15 lab15-devops-info-0 -- python -c "
import urllib.request
for _ in range(2): urllib.request.urlopen('http://127.0.0.1:5000/')
print(urllib.request.urlopen('http://127.0.0.1:5000/visits').read().decode())
"
kubectl exec -n lab15 lab15-devops-info-1 -- python -c "
import urllib.request
for _ in range(5): urllib.request.urlopen('http://127.0.0.1:5000/')
print(urllib.request.urlopen('http://127.0.0.1:5000/visits').read().decode())
"
kubectl exec -n lab15 lab15-devops-info-2 -- python -c "
import urllib.request
urllib.request.urlopen('http://127.0.0.1:5000/')
print(urllib.request.urlopen('http://127.0.0.1:5000/visits').read().decode())
"
```

Observed JSON:

```text
{"visits":2}
{"visits":5}
{"visits":1}
```

So each replica maintains **isolated** persistent state.

**Pod deletion (STS keeps PVC):**

```bash
kubectl exec -n lab15 lab15-devops-info-0 -- cat /data/visits
kubectl delete pod -n lab15 lab15-devops-info-0
kubectl wait -n lab15 pod/lab15-devops-info-0 --for=condition=Ready --timeout=120s
kubectl exec -n lab15 lab15-devops-info-0 -- cat /data/visits
kubectl exec -n lab15 lab15-devops-info-0 -- python -c "
import urllib.request
print(urllib.request.urlopen('http://127.0.0.1:5000/visits').read().decode())
"
```

Observed before delete, after reschedule, and via HTTP:

```text
2
2
{"visits":2}
```

The ordinal-0 PVC was reused, so the counter survived replacing only the Pod.

## 6. Bonus — update strategies

### 6.1 Partitioned rolling update

With `updateStrategy.type: RollingUpdate` and `rollingUpdate.partition: N`, only pods with **ordinal ≥ N** receive the new pod template during a rollout; ordinals `< N` stay on the old revision until you lower the partition. Useful for canarying stateful upgrades (e.g., upgrade followers before the leader).

Set in `values.yaml`:

```yaml
statefulset:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 2   # example: only pod-2 updates first (with 3 replicas)
```

### 6.2 OnDelete

With `type: OnDelete`, the StatefulSet controller does **not** automatically recreate pods when the template changes. You delete pods manually to pick up the new spec — maximum control, common when upgrades must be sequenced by an operator or runbooks.

```yaml
statefulset:
  updateStrategy:
    type: OnDelete
```

Typical use cases: coordinated database upgrades, version skew experiments, or when automation deletes pods one node at a time.

---

## References

- [StatefulSet](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
- [Headless Services](https://kubernetes.io/docs/concepts/services-networking/service/#headless-services)
- [StatefulSet update strategies](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/#update-strategies)
