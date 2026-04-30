# Lab 15 - StatefulSets and Persistent Storage

Validated on `2026-05-01` with:

- `helm v4.1.3+gc94d381`
- `kubectl v1.35.3`
- `kind v0.31.0`
- Kubernetes node `lab13-control-plane` on `v1.35.0`

Environment note:

- The host kubeconfig pointed at a stale forwarded API endpoint, so live validation used `docker exec lab13-control-plane ... --kubeconfig=/etc/kubernetes/admin.conf`.
- Helm rendered manifests on the host, then the rendered YAML was applied inside the kind control-plane container.

## 1. StatefulSet Overview

A StatefulSet is the correct controller when each replica needs a stable identity and its own durable storage. This lab uses it for the visits-counter API so every pod has:

- a stable ordinal name: `devops-info-0`, `devops-info-1`, `devops-info-2`
- a stable DNS identity through the headless service
- a dedicated PVC created from `volumeClaimTemplates`
- ordered startup and replacement through `podManagementPolicy: OrderedReady`

Key differences from the previous Deployment/Rollout shape:

| Capability | Deployment or Rollout | StatefulSet |
| --- | --- | --- |
| Pod names | ReplicaSet hash and random suffix | Stable ordinal suffix |
| Network identity | Service load balances across interchangeable pods | Pod DNS names are stable |
| Storage | Shared PVC or ephemeral volume unless managed separately | One PVC per pod from a template |
| Scaling | Pods may start or stop in any order | Ordered by default |
| Best fit | Stateless APIs and progressive delivery | Databases, queues, clustered systems, per-replica state |

The chart still keeps `rollout.yaml` and `deployment.yaml` for reference and fallback, but lab 15 defaults to `statefulset.enabled=true` and `rollout.enabled=false`.

Implemented files:

- `k8s/devops-info/templates/statefulset.yaml`
- `k8s/devops-info/templates/headless-service.yaml`
- `k8s/devops-info/templates/pvc.yaml`
- `k8s/devops-info/templates/deployment.yaml`
- `k8s/devops-info/templates/rollout.yaml`
- `k8s/devops-info/templates/analysis-template.yaml`
- `k8s/devops-info/templates/preview-service.yaml`
- `k8s/devops-info/templates/_helpers.tpl`
- `k8s/devops-info/values.yaml`
- `k8s/devops-info/values-statefulset-partition.yaml`
- `k8s/devops-info/values-statefulset-ondelete.yaml`

## 2. Implementation

The default chart now renders a StatefulSet:

```bash
helm template devops-info k8s/devops-info \
  -n devops-lab15 \
  --set hooks.preInstall.enabled=false \
  --set hooks.postInstall.enabled=false
```

Important rendered fields:

```yaml
kind: StatefulSet
spec:
  serviceName: devops-info-headless
  replicas: 3
  podManagementPolicy: OrderedReady
  updateStrategy:
    type: RollingUpdate
  volumeClaimTemplates:
    - metadata:
        name: data-volume
      spec:
        accessModes:
          - ReadWriteOnce
        resources:
          requests:
            storage: 100Mi
```

The headless service is separate from the normal service:

```yaml
kind: Service
metadata:
  name: devops-info-headless
spec:
  clusterIP: None
  publishNotReadyAddresses: true
```

The regular `devops-info` service remains in place for load-balanced access to the app.

The old standalone PVC template is guarded so it is only rendered for Deployment/Rollout mode. StatefulSet mode uses `volumeClaimTemplates` instead, producing PVCs named:

```text
data-volume-devops-info-0
data-volume-devops-info-1
data-volume-devops-info-2
```

## 3. Resource Verification

Install command used for validation:

```bash
docker exec lab13-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf \
  create namespace devops-lab15 --dry-run=client -o yaml |
docker exec -i lab13-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf apply -f -

helm template devops-info k8s/devops-info -n devops-lab15 \
  --set hooks.preInstall.enabled=false \
  --set hooks.postInstall.enabled=false |
docker exec -i lab13-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf \
  apply -n devops-lab15 -f -
```

Rollout status:

```text
statefulset rolling update complete 3 pods at revision devops-info-86d87cc4dc...
```

Resource output:

```text
NAME                READY   STATUS    RESTARTS   AGE   IP            NODE
pod/devops-info-0   1/1     Running   0          59s   10.244.0.21   lab13-control-plane
pod/devops-info-1   1/1     Running   0          44s   10.244.0.23   lab13-control-plane
pod/devops-info-2   1/1     Running   0          24s   10.244.0.25   lab13-control-plane

NAME                           READY   AGE   CONTAINERS    IMAGES
statefulset.apps/devops-info   3/3     59s   devops-info   ebortsov/devops-info:1.0.0

NAME                           TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)
service/devops-info            ClusterIP   10.96.203.39   <none>        80/TCP
service/devops-info-headless   ClusterIP   None           <none>        80/TCP

NAME                                              STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS
persistentvolumeclaim/data-volume-devops-info-0   Bound    pvc-c2b81d8a-65b4-4fd9-89c8-0e40ce738f74   100Mi      RWO            standard
persistentvolumeclaim/data-volume-devops-info-1   Bound    pvc-d701f1d8-30ee-4602-aa4a-272c23e9158e   100Mi      RWO            standard
persistentvolumeclaim/data-volume-devops-info-2   Bound    pvc-68e3a4fd-4c8a-4e35-90f9-e0cdcfd6f364   100Mi      RWO            standard
```

## 4. Network Identity

Headless service endpoints:

```text
NAME                   ENDPOINTS
devops-info-headless   10.244.0.21:5000,10.244.0.23:5000,10.244.0.25:5000
```

DNS resolution from `devops-info-0`:

```bash
kubectl -n devops-lab15 exec devops-info-0 -- python -c \
  "import socket; names=['devops-info-0.devops-info-headless','devops-info-1.devops-info-headless','devops-info-2.devops-info-headless']; [print(f'{n} -> {socket.gethostbyname(n)}') for n in names]"
```

Output:

```text
devops-info-0.devops-info-headless -> 10.244.0.21
devops-info-1.devops-info-headless -> 10.244.0.23
devops-info-2.devops-info-headless -> 10.244.0.25
```

Full DNS pattern:

```text
<pod-name>.<headless-service>.<namespace>.svc.cluster.local
devops-info-0.devops-info-headless.devops-lab15.svc.cluster.local
```

## 5. Per-Pod Storage Evidence

Each pod was accessed directly through localhost inside the pod. Different request counts were sent to each replica.

`devops-info-0`:

```text
{"visits":1,"path":"/data/visits","timestamp":"2026-04-30T21:48:23.010752+00:00"}
```

`devops-info-1`:

```text
{"visits":2,"path":"/data/visits","timestamp":"2026-04-30T21:48:22.983475+00:00"}
```

`devops-info-2`:

```text
{"visits":3,"path":"/data/visits","timestamp":"2026-04-30T21:48:23.069252+00:00"}
```

PVC-backed files confirmed the same isolated values:

```text
devops-info-0 /data/visits: 1
devops-info-1 /data/visits: 2
devops-info-2 /data/visits: 3
```

This proves each pod writes to a different PVC instead of sharing one counter file.

## 6. Persistence Test

Before deletion:

```text
devops-info-0 /data/visits: 1
PVC: data-volume-devops-info-0 -> pvc-c2b81d8a-65b4-4fd9-89c8-0e40ce738f74
```

Delete only the pod:

```bash
kubectl -n devops-lab15 delete pod devops-info-0
kubectl -n devops-lab15 wait --for=condition=Ready pod/devops-info-0 --timeout=180s
```

After recreation:

```text
NAME            READY   STATUS    RESTARTS   AGE   IP
devops-info-0   1/1     Running   0          13s   10.244.0.26

data-volume-devops-info-0   Bound   pvc-c2b81d8a-65b4-4fd9-89c8-0e40ce738f74   100Mi   RWO   standard
```

The pod IP changed, but the PVC stayed the same and the counter survived:

```text
cat /data/visits
1

GET /visits
{"visits":1,"path":"/data/visits","timestamp":"2026-04-30T21:48:52.346607+00:00"}
```

## 7. Bonus - Update Strategies

### Partitioned RollingUpdate

The chart supports partitioned updates through `values-statefulset-partition.yaml`:

```yaml
statefulset:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 2
```

Applied with:

```bash
helm template devops-info k8s/devops-info -n devops-lab15 \
  -f k8s/devops-info/values-statefulset-partition.yaml \
  --set env.SERVICE_VERSION=1.0.1 \
  --set hooks.preInstall.enabled=false \
  --set hooks.postInstall.enabled=false |
docker exec -i lab13-control-plane kubectl --kubeconfig=/etc/kubernetes/admin.conf \
  apply -n devops-lab15 -f -
```

StatefulSet strategy and revisions:

```text
{"rollingUpdate":{"maxUnavailable":1,"partition":2},"type":"RollingUpdate"}
currentRevision: devops-info-86d87cc4dc
updateRevision:  devops-info-6cc9db7cc4
```

Only pod ordinal `2` updated because `partition: 2` updates pods with ordinal greater than or equal to `2`:

```text
devops-info-0 SERVICE_VERSION=1.0.0
devops-info-1 SERVICE_VERSION=1.0.0
devops-info-2 SERVICE_VERSION=1.0.1
```

### OnDelete

The chart also supports `OnDelete` through `values-statefulset-ondelete.yaml`:

```yaml
statefulset:
  updateStrategy:
    type: OnDelete
```

Applied with `SERVICE_VERSION=1.0.2`, existing pods did not update automatically:

```text
{"type":"OnDelete"}
currentRevision: devops-info-86d87cc4dc
updateRevision:  devops-info-7f8b798fbf

devops-info-0 SERVICE_VERSION=1.0.0
devops-info-1 SERVICE_VERSION=1.0.0
devops-info-2 SERVICE_VERSION=1.0.1
```

After manually deleting `devops-info-1`, only that pod recreated on the new revision:

```text
devops-info-1 SERVICE_VERSION=1.0.2
devops-info-1 /data/visits: 2

NAME            REVISION                 READY
devops-info-0   devops-info-86d87cc4dc   true
devops-info-1   devops-info-7f8b798fbf   true
devops-info-2   devops-info-6cc9db7cc4   true
```

`OnDelete` is useful when an operator must control each replacement manually, such as database upgrades, quorum-sensitive systems, or migrations that require external checks between pod restarts.
