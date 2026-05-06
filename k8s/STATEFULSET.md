# Lab 15 - StatefulSets and Persistent Storage

## 1) StatefulSet overview

StatefulSet is used for workloads where each replica must keep a stable identity and dedicated persistent storage.

### Why StatefulSet here

- The visits counter stores data on disk (`/data`), so each replica needs its own volume.
- Pod identity must be stable (`<name>-0`, `<name>-1`, ...), which allows direct DNS addressing.
- Pod rollout and scaling behavior is predictable (ordered start/stop when using `OrderedReady`).

### Deployment/Rollout vs StatefulSet


| Feature        | Deployment / Rollout                    | StatefulSet                                   |
| -------------- | --------------------------------------- | --------------------------------------------- |
| Pod identity   | Ephemeral names with random suffixes    | Stable ordinal names (`app-0`, `app-1`)       |
| Storage        | Shared PVC or ephemeral volume patterns | Per-pod PVC via `volumeClaimTemplates`        |
| Scale behavior | Unordered                               | Ordered by ordinal (`0 -> 1 -> 2`) by default |
| DNS            | Service-level only                      | Per-pod DNS through headless Service          |
| Typical use    | Stateless web/API                       | Databases, queues, clustered stateful apps    |


### Headless Service and DNS

- A headless Service has `clusterIP: None`.
- Kubernetes publishes DNS A records for each pod behind the StatefulSet:
  - `<sts-pod-name>.<headless-service>.<namespace>.svc.cluster.local`

Example:

- `myrelease-mychart-0.myrelease-mychart-headless.default.svc.cluster.local`

---

## 2) Implemented chart changes

- Added `templates/statefulset.yaml` with:
  - `serviceName` -> `<fullname>-headless`
  - `volumeClaimTemplates` for per-pod `data` PVC
  - Configurable `podManagementPolicy` and `updateStrategy`
- Added `templates/service-headless.yaml` (`clusterIP: None`).
- Kept external access service in `templates/service.yaml`.
- Gated `templates/rollout.yaml` so it renders only when `workload.kind != statefulset`.
- Updated `templates/pvc.yaml` so shared PVC is not rendered in StatefulSet mode.
- Added StatefulSet-related values in `values.yaml`.

Switch to StatefulSet mode:

```bash
helm upgrade --install myapp ./k8s/mychart \
  --set workload.kind=statefulset \
  --set replicaCount=3 \
  --set persistence.enabled=true \
  --set persistence.size=100Mi
```

---

## 3) Resource verification

Command used:

```bash
kubectl get po,sts,svc,pvc -n lab15-stateful
```

Actual output:

```text
NAME                  READY   STATUS    RESTARTS   AGE
pod/lab15-mychart-0   1/1     Running   0          26s
pod/lab15-mychart-1   1/1     Running   0          19s
pod/lab15-mychart-2   1/1     Running   0          12s

NAME                             READY   AGE
statefulset.apps/lab15-mychart   3/3     26s

NAME                             TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)    AGE
service/lab15-mychart            ClusterIP   10.108.245.235   <none>        8080/TCP   26s
service/lab15-mychart-headless   ClusterIP   None             <none>        8080/TCP   26s

NAME                                         STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/data-lab15-mychart-0   Bound    pvc-49fb0d99-e997-41e3-9c3b-21947341bef7   100Mi      RWO            hostpath       <unset>                 26s
persistentvolumeclaim/data-lab15-mychart-1   Bound    pvc-546aad9e-2980-4af2-a243-b8ce7c005d3b   100Mi      RWO            hostpath       <unset>                 19s
persistentvolumeclaim/data-lab15-mychart-2   Bound    pvc-99a68562-20b7-4e2f-bd55-53b8eb66566c   100Mi      RWO            hostpath       <unset>                 12s
```

Validation:

- StatefulSet is `3/3 Ready`.
- Pod names are stable ordinals (`-0`, `-1`, `-2`).
- Headless service has `CLUSTER-IP None`.
- One PVC is created and bound per pod.

---

## 4) Network identity test

Command used (self-contained, always executable):

```bash
kubectl delete pod -n lab15-stateful dnsutils --ignore-not-found
kubectl run -n lab15-stateful dnsutils --image=busybox:1.36 --restart=Never -- sleep 3600
kubectl wait -n lab15-stateful --for=condition=Ready pod/dnsutils --timeout=120s
kubectl exec -n lab15-stateful dnsutils -- nslookup lab15-mychart-1.lab15-mychart-headless.lab15-stateful.svc.cluster.local
kubectl delete pod -n lab15-stateful dnsutils --wait=true
```

Actual output:

```text
Server:		10.96.0.10
Address:	10.96.0.10:53

Name:	lab15-mychart-1.lab15-mychart-headless.lab15-stateful.svc.cluster.local
Address: 10.1.2.10
```

Validation:

- Pod-specific DNS resolves correctly through the headless service.
- Naming pattern confirmed: `<pod>.<headless-service>.<namespace>.svc.cluster.local`.

---

## 5) Per-pod storage isolation test

Command used (self-contained, always executable):

```bash
kubectl delete pod -n lab15-stateful curlpod --ignore-not-found
kubectl run -n lab15-stateful curlpod --image=curlimages/curl:8.7.1 --restart=Never -- sleep 3600
kubectl wait -n lab15-stateful --for=condition=Ready pod/curlpod --timeout=120s

# Initial values
kubectl exec -n lab15-stateful curlpod -- sh -lc "curl -s http://lab15-mychart-0.lab15-mychart-headless.lab15-stateful.svc.cluster.local:5000/visits"
kubectl exec -n lab15-stateful curlpod -- sh -lc "curl -s http://lab15-mychart-1.lab15-mychart-headless.lab15-stateful.svc.cluster.local:5000/visits"
kubectl exec -n lab15-stateful curlpod -- sh -lc "curl -s http://lab15-mychart-2.lab15-mychart-headless.lab15-stateful.svc.cluster.local:5000/visits"

# Different traffic per pod
kubectl exec -n lab15-stateful curlpod -- sh -lc "for i in 1 2 3; do curl -s -o /dev/null http://lab15-mychart-0.lab15-mychart-headless.lab15-stateful.svc.cluster.local:5000/; done"
kubectl exec -n lab15-stateful curlpod -- sh -lc "for i in 1 2 3 4 5; do curl -s -o /dev/null http://lab15-mychart-1.lab15-mychart-headless.lab15-stateful.svc.cluster.local:5000/; done"
kubectl exec -n lab15-stateful curlpod -- sh -lc "for i in 1 2; do curl -s -o /dev/null http://lab15-mychart-2.lab15-mychart-headless.lab15-stateful.svc.cluster.local:5000/; done"

# Final values
kubectl exec -n lab15-stateful curlpod -- sh -lc "curl -s http://lab15-mychart-0.lab15-mychart-headless.lab15-stateful.svc.cluster.local:5000/visits"
kubectl exec -n lab15-stateful curlpod -- sh -lc "curl -s http://lab15-mychart-1.lab15-mychart-headless.lab15-stateful.svc.cluster.local:5000/visits"
kubectl exec -n lab15-stateful curlpod -- sh -lc "curl -s http://lab15-mychart-2.lab15-mychart-headless.lab15-stateful.svc.cluster.local:5000/visits"

kubectl delete pod -n lab15-stateful curlpod --wait=true
```

Actual output:

```text
Initial visits:
{"visits":0}
{"visits":0}
{"visits":0}

Generate different traffic per pod
Visits after traffic:
{"visits":3}
{"visits":5}
{"visits":2}
```

Validation:

- Each pod maintains an independent counter value.
- Storage is isolated per pod (different values after different request volumes).

---

## 6) Persistence test

Command used:

```bash
kubectl exec -n lab15-stateful lab15-mychart-0 -- cat /data/visits
kubectl delete pod -n lab15-stateful lab15-mychart-0
kubectl wait -n lab15-stateful --for=condition=Ready pod/lab15-mychart-0 --timeout=180s
kubectl exec -n lab15-stateful lab15-mychart-0 -- cat /data/visits
```

Actual output:

```text
Before pod delete: 3
pod "lab15-mychart-0" deleted
pod/lab15-mychart-0 condition met
After pod recreate: 3
```

Validation:

- The value before and after pod recreation is the same.
- Data persisted in PVC and survived pod deletion.

---

## 7) Bonus - update strategies

### Partitioned rolling update

```yaml
statefulset:
  updateStrategy:
    type: RollingUpdate
    partition: 2
```

Behavior:

- Only pods with ordinal `>= 2` update automatically.
- Lower ordinals remain on old revision until partition is lowered.

### OnDelete strategy

```yaml
statefulset:
  updateStrategy:
    type: OnDelete
```

Behavior:

- Template changes do not restart pods automatically.
- Pod updates happen only when each pod is manually deleted.

Useful for strict, operator-controlled update flows in sensitive stateful systems.