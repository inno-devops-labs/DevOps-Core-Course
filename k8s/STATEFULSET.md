# StatefulSets & Persistent Storage — Lab 15

## Table of Contents

- [1. StatefulSet Overview](#1-statefulset-overview)
- [2. Chart Changes](#2-chart-changes)
- [3. Deploy & Resource Verification](#3-deploy--resource-verification)
- [4. Network Identity — Headless Service & DNS](#4-network-identity--headless-service--dns)
- [5. Per-Pod Storage Isolation](#5-per-pod-storage-isolation)
- [6. Persistence Across Pod Restarts](#6-persistence-across-pod-restarts)
- [7. Bonus — Update Strategies](#7-bonus--update-strategies)
- [8. Cleanup & Reproduction](#8-cleanup--reproduction)

---

## 1. StatefulSet Overview

`Deployment` and `Rollout` (Lab 14) are the right tool for **stateless**
workloads: pods are interchangeable, any replica can serve any request,
and the underlying storage (if any) is either ephemeral or a single
shared `PersistentVolumeClaim`.

A `StatefulSet` is designed for workloads that need **identity**:

1. **Stable network identity.** Pods are named with an ordinal
   (`devops-app-0`, `devops-app-1`, ...) and get a deterministic DNS
   record through a companion *headless* `Service`
   (`<pod>.<headless-svc>.<ns>.svc.cluster.local`).
2. **Stable, per-pod storage.** Each pod gets its own
   `PersistentVolumeClaim`, provisioned from a
   `volumeClaimTemplate` and bound to the ordinal — PVC
   `data-devops-app-0` always reattaches to pod `devops-app-0`,
   even after the pod is deleted and rescheduled.
3. **Ordered lifecycle.** With the default
   `podManagementPolicy: OrderedReady`, pods start in order
   `0 → 1 → 2` and terminate in reverse. Scaling and rolling updates
   respect the same ordering.

### When to use which

| Concern | `Deployment` / `Rollout` | `StatefulSet` |
|---------|--------------------------|---------------|
| Pod name | `<name>-<rs>-<rand>` | `<name>-<ordinal>` |
| Network identity | Load-balanced via Service VIP | Stable per-pod DNS via headless Service |
| Storage | Shared PVC (or ephemeral) | One PVC per pod via `volumeClaimTemplates` |
| Startup/teardown | Any order, parallel | Ordered (0 → N-1), reverse on teardown |
| Update | RollingUpdate or canary/blue-green | `RollingUpdate` (with `partition`) or `OnDelete` |
| Fit | REST APIs, workers, stateless web | Databases, Kafka brokers, Elasticsearch, anything with per-instance on-disk state |

> Rule of thumb: if two replicas can write to the **same** PVC without
> corrupting it, you don't need a StatefulSet. If each replica needs
> its own disk that must survive a reschedule, you do.

### Headless Services and DNS

A regular `Service` has a `ClusterIP` VIP and CoreDNS publishes a
single A record pointing at it; traffic is load-balanced across all
Ready endpoints.

A **headless** Service is declared with `clusterIP: None`. There is
no VIP; instead, CoreDNS publishes:

- an A record per endpoint under the Service's name (round-robin);
- for each Pod of a StatefulSet that owns the Service via
  `spec.serviceName`, a **stable per-pod A record**:

```
<pod-name>.<headless-service>.<namespace>.svc.cluster.local
```

So clients inside the cluster can address a specific replica by name
— which is exactly how peers in distributed systems (etcd, Kafka,
Cassandra) discover each other.

---

## 2. Chart Changes

The existing `devops-app` Helm chart now supports a StatefulSet mode
behind a single feature flag, so the same chart covers Labs 10-15:

| File | Purpose |
|------|---------|
| `k8s/devops-app/templates/statefulset.yaml` | StatefulSet manifest; rendered only when `statefulset.enabled=true`. Mounts `volumeClaimTemplates` into the container instead of a chart-managed PVC. |
| `k8s/devops-app/templates/headless-service.yaml` | Headless `Service` with `clusterIP: None`, referenced from `spec.serviceName`. |
| `k8s/devops-app/templates/deployment.yaml` | Gate tightened to `and (not rollouts.enabled) (not statefulset.enabled)` — only one workload resource is ever rendered. |
| `k8s/devops-app/templates/rollout.yaml` | Same: suppressed when `statefulset.enabled=true`. |
| `k8s/devops-app/templates/pvc.yaml` | The shared PVC from Lab 12 is suppressed in StatefulSet mode — each pod's PVC is created from the `volumeClaimTemplates` block instead. |
| `k8s/devops-app/values.yaml` | New `statefulset.*` block (disabled by default). |
| `k8s/devops-app/values-statefulset.yaml` | Turn-key override to switch the chart into StatefulSet mode. |

The three "workload modes" are mutually exclusive:

```
statefulset.enabled=true      -> StatefulSet + headless Service
rollouts.enabled=true         -> Argo Rollout  (Lab 14)
otherwise                     -> Deployment    (Labs 10-13)
```

Key excerpts from `statefulset.yaml`:

```yaml
apiVersion: apps/v1
kind: StatefulSet
spec:
  serviceName: {{ include "devops-app.fullname" . }}-headless
  replicas: {{ .Values.replicaCount }}
  podManagementPolicy: {{ .Values.statefulset.podManagementPolicy | default "OrderedReady" }}
  updateStrategy:
    {{- toYaml .Values.statefulset.updateStrategy | nindent 4 }}
  template:
    spec:
      containers:
        - name: {{ .Chart.Name }}
          volumeMounts:
            - name: {{ .Values.statefulset.volumeClaimTemplate.name | default "data" }}
              mountPath: {{ .Values.persistence.mountPath | default "/data" }}
  volumeClaimTemplates:
    - metadata:
        name: {{ .Values.statefulset.volumeClaimTemplate.name | default "data" }}
      spec:
        accessModes:
          {{- toYaml (.Values.statefulset.volumeClaimTemplate.accessModes | default (list "ReadWriteOnce")) | nindent 10 }}
        resources:
          requests:
            storage: {{ .Values.statefulset.volumeClaimTemplate.size | default .Values.persistence.size | default "100Mi" }}
```

`headless-service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "devops-app.fullname" . }}-headless
spec:
  clusterIP: None
  publishNotReadyAddresses: true   # peers discoverable while still initialising
  selector:
    {{- include "devops-app.selectorLabels" . | nindent 4 }}
  ports:
    - name: http
      port: {{ .Values.statefulset.headlessService.port | default .Values.service.port }}
      targetPort: {{ .Values.statefulset.headlessService.targetPort | default .Values.service.targetPort }}
```

`publishNotReadyAddresses: true` is a StatefulSet-specific best
practice: peers in clustered systems need to find each other
*before* they become Ready, otherwise the cluster never bootstraps.

### Values used for this lab

`k8s/devops-app/values-statefulset.yaml`:

```yaml
replicaCount: 3

rollouts:
  enabled: false

statefulset:
  enabled: true
  podManagementPolicy: OrderedReady
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 0
  volumeClaimTemplate:
    name: data
    accessModes: [ReadWriteOnce]
    size: 100Mi
    storageClass: ""          # use cluster default (standard on minikube/kind)
  headlessService:
    port: 80
    targetPort: 8000
```

---

## 3. Deploy & Resource Verification

Deploy into a dedicated namespace:

```bash
kubectl create ns lab15
helm upgrade --install devops-app ./k8s/devops-app \
  -n lab15 \
  -f ./k8s/devops-app/values.yaml \
  -f ./k8s/devops-app/values-statefulset.yaml \
  --set vault.enabled=false \
  --wait --timeout 240s
```

`kubectl get po,sts,svc,pvc -n lab15`:

```text
NAME               READY   STATUS    RESTARTS   AGE
pod/devops-app-0   1/1     Running   0          77s
pod/devops-app-1   1/1     Running   0          66s
pod/devops-app-2   1/1     Running   0          54s

NAME                          READY   AGE
statefulset.apps/devops-app   3/3     77s

NAME                          TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-app-headless   ClusterIP   None            <none>        80/TCP         77s
service/devops-app-service    NodePort    10.96.205.183   <none>        80:30815/TCP   72s

NAME                                      STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/data-devops-app-0   Bound    pvc-958b4079-...                           100Mi      RWO            standard       77s
persistentvolumeclaim/data-devops-app-1   Bound    pvc-b680e049-...                           100Mi      RWO            standard       66s
persistentvolumeclaim/data-devops-app-2   Bound    pvc-14a302d9-...                           100Mi      RWO            standard       54s
```

Observations:

- Pod names carry the ordinal suffix (`-0`, `-1`, `-2`).
- Pods become Ready strictly in order (ages 77s / 66s / 54s — ~11s
  between each, confirming `podManagementPolicy: OrderedReady`).
- One PVC per pod, bound automatically. Each PVC is named
  `<volumeClaimTemplate.name>-<statefulset>-<ordinal>`.
- The headless service has `CLUSTER-IP: None`; the regular Service
  still exposes the app externally via NodePort.

---

## 4. Network Identity — Headless Service & DNS

DNS check from a throwaway busybox pod in the same namespace:

```bash
kubectl run -n lab15 --rm -it --restart=Never \
  --image=busybox:1.36 dns-test --command -- sh
```

Per-pod A records:

```text
/ # nslookup devops-app-0.devops-app-headless.lab15.svc.cluster.local
Server:		10.96.0.10
Address:	10.96.0.10:53
Name:	devops-app-0.devops-app-headless.lab15.svc.cluster.local
Address: 10.244.0.65

/ # nslookup devops-app-1.devops-app-headless.lab15.svc.cluster.local
Name:	devops-app-1.devops-app-headless.lab15.svc.cluster.local
Address: 10.244.0.62

/ # nslookup devops-app-2.devops-app-headless.lab15.svc.cluster.local
Name:	devops-app-2.devops-app-headless.lab15.svc.cluster.local
Address: 10.244.0.64
```

SRV record on the headless service — all three pods are advertised:

```text
/ # nslookup -type=SRV devops-app-headless.lab15.svc.cluster.local
devops-app-headless.lab15.svc.cluster.local	service = 0 33 8000 devops-app-1.devops-app-headless.lab15.svc.cluster.local
devops-app-headless.lab15.svc.cluster.local	service = 0 33 8000 devops-app-2.devops-app-headless.lab15.svc.cluster.local
devops-app-headless.lab15.svc.cluster.local	service = 0 33 8000 devops-app-0.devops-app-headless.lab15.svc.cluster.local
```

Takeaways:

- Each pod's A record points **at its own Pod IP**, not at a
  Service VIP. That IP belongs to `devops-app-<N>` and nothing else.
- The DNS name is stable across pod restarts and reschedules —
  only the underlying IP changes.
- For a clustered peer ("tell pod-2 to follow pod-0"), the headless
  DNS name is the correct identifier to configure in the client; the
  IP must never be hard-coded.

---

## 5. Per-Pod Storage Isolation

The app increments an on-disk counter (`/data/visits`) on every
`GET /` and returns the current count on `GET /visits`. Because each
pod mounts **its own** PVC, the counters are independent.

Hit each pod a different number of times (3 / 5 / 7) via a
curl-capable pod that addresses them by their headless DNS name:

```bash
kubectl run -n lab15 --rm -i --restart=Never \
  --image=curlimages/curl:8.10.1 curl-test --command -- sh -c '
for i in 1 2 3;          do curl -s devops-app-0.devops-app-headless.lab15.svc.cluster.local:8000/ > /dev/null; done
for i in 1 2 3 4 5;      do curl -s devops-app-1.devops-app-headless.lab15.svc.cluster.local:8000/ > /dev/null; done
for i in 1 2 3 4 5 6 7;  do curl -s devops-app-2.devops-app-headless.lab15.svc.cluster.local:8000/ > /dev/null; done
for p in devops-app-0 devops-app-1 devops-app-2; do
  echo -n "$p : "; curl -s $p.devops-app-headless.lab15.svc.cluster.local:8000/visits; echo
done'
```

Result:

```text
devops-app-0 : {"visits": 3}
devops-app-1 : {"visits": 5}
devops-app-2 : {"visits": 7}
```

Same numbers on disk, read through `kubectl exec`:

```bash
$ for p in devops-app-0 devops-app-1 devops-app-2; do
    echo -n "$p /data/visits = "; kubectl exec -n lab15 $p -- cat /data/visits; echo
  done
devops-app-0 /data/visits = 3
devops-app-1 /data/visits = 5
devops-app-2 /data/visits = 7
```

If the PVCs were shared, hitting **any** pod would increment a single
counter and all three numbers would be equal. The fact that they
diverge is the observable proof of per-pod isolation.

---

## 6. Persistence Across Pod Restarts

Delete pod-1 and verify its counter survives:

```bash
$ kubectl exec -n lab15 devops-app-1 -- cat /data/visits
5

$ kubectl delete pod -n lab15 devops-app-1
pod "devops-app-1" deleted from lab15 namespace

$ kubectl wait --for=condition=Ready pod/devops-app-1 -n lab15 --timeout=90s
pod/devops-app-1 condition met

$ kubectl exec -n lab15 devops-app-1 -- cat /data/visits
5

$ kubectl get pod devops-app-1 -n lab15 -o wide
NAME           READY   STATUS    RESTARTS   AGE   IP            NODE
devops-app-1   1/1     Running   0          5s    10.244.0.68   lab13-control-plane
```

What happened:

- The StatefulSet controller detected the missing pod-1 and
  recreated it **with the same name**.
- Because pod-1's identity is fixed to ordinal 1, the controller
  reattached the existing `data-devops-app-1` PVC to the new pod.
- The underlying `PersistentVolume` was never deleted, so
  `/data/visits` still contained `5`.
- Only the Pod IP changed (`10.244.0.62` → `10.244.0.68`), but the
  DNS name `devops-app-1.devops-app-headless…` resolves to the new
  IP — i.e. the network identity is stable even though the IP is not.

This is the guarantee that makes StatefulSets viable for databases:
when a pod goes away, its data comes back with it.

---

## 7. Bonus — Update Strategies

StatefulSets support two `updateStrategy` types:

### 7.1 `RollingUpdate` with `partition`

```yaml
spec:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 2          # only ordinal >= 2 gets the new template
```

Semantics: when the template changes, the controller **only**
updates pods with `ordinal >= partition`. Pods with smaller
ordinals stay on the old `controller-revision-hash` until `partition`
is lowered.

This is how a StatefulSet does canaries — promote a single replica
first, observe, then lower the partition to roll out more.

Demonstration — set `partition: 2`, then change the pod template
(`kubectl set env statefulset/devops-app ROLL=v2`):

```text
NAME           READY   STATUS    RESTARTS   AGE    CONTROLLER-REVISION-HASH
devops-app-0   1/1     Running   0          3m     devops-app-5dccff74bf   # old
devops-app-1   1/1     Running   0          66s    devops-app-5dccff74bf   # old
devops-app-2   1/1     Running   0          20s    devops-app-79b5488cb6   # NEW
```

`kubectl get sts devops-app -n lab15 -o jsonpath=…`:

```text
currentRevision: devops-app-5dccff74bf
updateRevision:  devops-app-79b5488cb6
partition:       2
```

Only pod-2 has rolled to `updateRevision`. The StatefulSet reports
both revisions concurrently — this is exactly what you'd observe
mid-canary in production.

Lowering `partition: 1` would next update pod-1 (and only pod-1);
`partition: 0` finishes the rollout.

### 7.2 `OnDelete`

```yaml
spec:
  updateStrategy:
    type: OnDelete
```

Semantics: the controller **never** recreates a pod to pick up a
template change. Operators pick the moment of each individual update
by deleting pods manually.

Demonstration — switch to `OnDelete` and change the template again:

```bash
$ kubectl patch statefulset -n lab15 devops-app --type=json \
    -p='[{"op":"replace","path":"/spec/updateStrategy","value":{"type":"OnDelete"}}]'
statefulset.apps/devops-app patched

$ kubectl set env -n lab15 statefulset/devops-app ROLL=v3
statefulset.apps/devops-app env updated
```

Ten seconds later — nothing moved; all three pods are still on
their previous revisions:

```text
NAME           READY   STATUS    RESTARTS   AGE      CONTROLLER-REVISION-HASH
devops-app-0   1/1     Running   0          3m22s    devops-app-5dccff74bf
devops-app-1   1/1     Running   0          88s      devops-app-5dccff74bf
devops-app-2   1/1     Running   0          42s      devops-app-79b5488cb6
```

Manually delete pod-0 — it picks up the new revision as it restarts:

```text
$ kubectl delete pod -n lab15 devops-app-0
$ kubectl get pods -n lab15 -L controller-revision-hash
NAME           READY   STATUS    RESTARTS   AGE    CONTROLLER-REVISION-HASH
devops-app-0   1/1     Running   0          9s     devops-app-8f6bbccc    # NEW
devops-app-1   1/1     Running   0          2m8s   devops-app-5dccff74bf
devops-app-2   1/1     Running   0          82s    devops-app-79b5488cb6
```

### When to use which

| Strategy | Good fit |
|----------|----------|
| `RollingUpdate` (partition=0) | Normal case — e.g. a schema-compatible app upgrade across all replicas. |
| `RollingUpdate` (partition>0) | Canary within a StatefulSet: upgrade the highest-ordinal replica first, validate, then lower the partition step by step. |
| `OnDelete` | Workloads where downtime must be scheduled (Kafka/ZooKeeper upgrades, DB major-version bumps); the operator coordinates backup/leader-election around each pod delete. |

> Unlike `Deployment`/`Rollout`, StatefulSets have **no** Blue-Green
> or weighted-traffic strategy — replicas are not interchangeable,
> so progressive delivery is always about picking *which ordinal*
> rolls next, not about routing traffic.

---

## 8. Cleanup & Reproduction

Cleanup:

```bash
helm uninstall devops-app -n lab15
kubectl delete ns lab15
```

Reproduce end-to-end:

```bash
# 1. Deploy
kubectl create ns lab15
helm upgrade --install devops-app ./k8s/devops-app \
  -n lab15 \
  -f ./k8s/devops-app/values.yaml \
  -f ./k8s/devops-app/values-statefulset.yaml \
  --set vault.enabled=false \
  --wait --timeout 240s

# 2. Resource sanity
kubectl get po,sts,svc,pvc -n lab15

# 3. Identity
kubectl run -n lab15 --rm -it --restart=Never --image=busybox:1.36 dns-test \
  --command -- nslookup devops-app-0.devops-app-headless.lab15.svc.cluster.local

# 4. Per-pod counters via headless DNS
kubectl run -n lab15 --rm -i --restart=Never --image=curlimages/curl:8.10.1 c \
  --command -- sh -c 'for p in devops-app-0 devops-app-1 devops-app-2; do
    curl -s $p.devops-app-headless.lab15.svc.cluster.local:8000/ > /dev/null
    echo -n "$p : "; curl -s $p.devops-app-headless.lab15.svc.cluster.local:8000/visits; echo
  done'

# 5. Persistence
kubectl delete pod -n lab15 devops-app-1
kubectl wait --for=condition=Ready pod/devops-app-1 -n lab15 --timeout=90s
kubectl exec -n lab15 devops-app-1 -- cat /data/visits

# 6. Partition rollout
kubectl patch statefulset -n lab15 devops-app \
  -p '{"spec":{"updateStrategy":{"type":"RollingUpdate","rollingUpdate":{"partition":2}}}}'
kubectl set env -n lab15 statefulset/devops-app ROLL=v2
kubectl get pods -n lab15 -L controller-revision-hash
```

> All commands above were executed against the `kind-lab13`
> cluster used in Labs 13-14 (single control-plane node with the
> `standard` StorageClass provided by
> `local-path-provisioner`). The chart's `storageClass: ""`
> intentionally falls back to whatever the cluster marks as default,
> so the same commands work on `minikube` unchanged.
