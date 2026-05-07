# Lab 15 Report — StatefulSets & Persistent Storage

## 1. Overview

Lab 15 adds a StatefulSet mode to the existing `k8s/devops-info` Helm chart.

The chart now supports three workload modes:

- `Deployment` by default
- `Rollout` for progressive delivery from Lab 14
- `StatefulSet` for stable identity and per-pod storage

Relevant files:

```text
k8s/devops-info/
├── templates/
│   ├── headless-service.yaml
│   └── statefulset.yaml
├── values-statefulset.yaml
├── values-statefulset-partition.yaml
└── values-statefulset-ondelete.yaml
```

The default chart behavior is unchanged. StatefulSet mode is enabled only when:

```yaml
statefulset:
  enabled: true
```

## 2. StatefulSet Concepts

### 2.1 StatefulSet guarantees

StatefulSets are useful when an application needs stable identity and storage. A StatefulSet provides:

- stable pod names: `app-0`, `app-1`, `app-2`
- stable DNS names through a headless service
- one persistent volume claim per pod through `volumeClaimTemplates`
- ordered creation, update, and termination by default

This is different from a Deployment, where pods are replaceable and their names are generated with random suffixes.

### 2.2 Deployment vs StatefulSet

| Feature | Deployment | StatefulSet |
|---|---|---|
| Pod names | Random ReplicaSet suffix | Stable ordinal suffix |
| Pod identity | Disposable | Stable |
| Storage | Shared PVC or ephemeral volumes | Per-pod PVCs |
| Scaling order | No stable order guarantee | Ordered by ordinal by default |
| DNS | Service-level load balancing | Pod-level DNS through headless service |
| Typical use | Stateless web apps | Databases, queues, clustered systems |

For the `devops-info` app, StatefulSet is useful for the visits counter because each pod writes to its own `/data/visits` file.

### 2.3 Headless service

A headless service is a Service with:

```yaml
clusterIP: None
```

It does not allocate a virtual ClusterIP for load balancing. Instead, Kubernetes DNS returns pod IPs directly.

For this lab:

```text
lab15-devops-info-0.lab15-devops-info-headless.lab15.svc.cluster.local
lab15-devops-info-1.lab15-devops-info-headless.lab15.svc.cluster.local
lab15-devops-info-2.lab15-devops-info-headless.lab15.svc.cluster.local
```

## 3. Implementation

### 3.1 StatefulSet template

Created:

```text
k8s/devops-info/templates/statefulset.yaml
```

Important fields:

```yaml
apiVersion: apps/v1
kind: StatefulSet
spec:
  serviceName: lab15-devops-info-headless
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
        storageClassName: "standard"
```

The `data-volume` claim template matches the container mount:

```yaml
volumeMounts:
  - name: data-volume
    mountPath: /data
```

### 3.2 Headless service

Created:

```text
k8s/devops-info/templates/headless-service.yaml
```

Rendered service:

```yaml
kind: Service
metadata:
  name: lab15-devops-info-headless
spec:
  clusterIP: None
```

The regular NodePort service remains available for external access.

### 3.3 Values file

Main lab values:

```text
k8s/devops-info/values-statefulset.yaml
```

Key settings:

```yaml
fullnameOverride: lab15-devops-info
replicaCount: 3

image:
  repository: app_python-devops-info
  tag: latest
  pullPolicy: IfNotPresent

service:
  type: NodePort
  nodePort: 30089

statefulset:
  enabled: true
  podManagementPolicy: OrderedReady

persistence:
  enabled: true
  accessMode: ReadWriteOnce
  size: 100Mi
  storageClass: standard
  mountPath: /data
```

The local image `app_python-devops-info:latest` was used because it includes the `/visits` endpoint needed for the storage checks.

## 4. Deployment

The local image was already present and then loaded into the kind node:

```bash
kind load docker-image app_python-devops-info:latest --name devops-lab
```

Install command:

```bash
kubectl create namespace lab15

helm upgrade --install lab15 k8s/devops-info \
  -n lab15 \
  -f k8s/devops-info/values-statefulset.yaml
```

Rollout status:

```bash
$ kubectl rollout status statefulset/lab15-devops-info -n lab15 --timeout=240s
statefulset rolling update complete 3 pods at revision lab15-devops-info-697d89dcf8
```

Helm lint:

```bash
$ helm lint k8s/devops-info -f k8s/devops-info/values-statefulset.yaml
==> Linting k8s/devops-info
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

Render checks:

```bash
$ helm template lab15 k8s/devops-info -n lab15 \
  -f k8s/devops-info/values-statefulset.yaml \
  --show-only templates/statefulset.yaml

kind: StatefulSet
serviceName: lab15-devops-info-headless
type: RollingUpdate
image: "app_python-devops-info:latest"
volumeClaimTemplates:
storageClassName: "standard"
```

```bash
$ helm template lab15 k8s/devops-info -n lab15 \
  -f k8s/devops-info/values-statefulset.yaml \
  --show-only templates/headless-service.yaml

kind: Service
name: lab15-devops-info-headless
clusterIP: None
```

## 5. Resource Verification

```bash
$ kubectl get po,sts,svc,pvc -n lab15 -o wide
```

Output:

```text
pod/lab15-devops-info-0   1/1   Running   10.244.0.54
pod/lab15-devops-info-1   1/1   Running   10.244.0.53
pod/lab15-devops-info-2   1/1   Running   10.244.0.52

statefulset.apps/lab15-devops-info   3/3   app_python-devops-info:latest

service/lab15-devops-info            NodePort    80:30089/TCP
service/lab15-devops-info-headless   ClusterIP   None   80/TCP

persistentvolumeclaim/data-volume-lab15-devops-info-0   Bound   100Mi   RWO   standard
persistentvolumeclaim/data-volume-lab15-devops-info-1   Bound   100Mi   RWO   standard
persistentvolumeclaim/data-volume-lab15-devops-info-2   Bound   100Mi   RWO   standard
```

PVC verification:

```bash
$ kubectl get pvc -n lab15 \
  -o 'custom-columns=NAME:.metadata.name,STATUS:.status.phase,VOLUME:.spec.volumeName,CAPACITY:.status.capacity.storage,ACCESS:.status.accessModes[0],STORAGECLASS:.spec.storageClassName'

NAME                              STATUS   VOLUME                                     CAPACITY   ACCESS          STORAGECLASS
data-volume-lab15-devops-info-0   Bound    pvc-e7f33e9f-f69e-4701-8f31-ed719d8217b1   100Mi      ReadWriteOnce   standard
data-volume-lab15-devops-info-1   Bound    pvc-84436681-f135-406f-8de1-b0d0ecc8deb6   100Mi      ReadWriteOnce   standard
data-volume-lab15-devops-info-2   Bound    pvc-8c4a0376-a490-46c4-a0da-78a1a74454a2   100Mi      ReadWriteOnce   standard
```

Each pod has its own PVC.

## 6. Network Identity

Pod identity:

```bash
$ kubectl get pods -n lab15 -l app.kubernetes.io/instance=lab15 \
  -o custom-columns=NAME:.metadata.name,HOSTNAME:.spec.hostname,SUBDOMAIN:.spec.subdomain,PHASE:.status.phase

NAME                  HOSTNAME              SUBDOMAIN                    PHASE
lab15-devops-info-0   lab15-devops-info-0   lab15-devops-info-headless   Running
lab15-devops-info-1   lab15-devops-info-1   lab15-devops-info-headless   Running
lab15-devops-info-2   lab15-devops-info-2   lab15-devops-info-headless   Running
```

FQDN from pod `0`:

```bash
$ kubectl exec -n lab15 lab15-devops-info-0 -- hostname -f
lab15-devops-info-0.lab15-devops-info-headless.lab15.svc.cluster.local
```

DNS resolution from pod `0` to pod `1`:

```bash
$ kubectl exec -n lab15 lab15-devops-info-0 -- \
  getent hosts lab15-devops-info-1.lab15-devops-info-headless.lab15.svc.cluster.local

10.244.0.43 lab15-devops-info-1.lab15-devops-info-headless.lab15.svc.cluster.local
```

DNS resolution from pod `0` to pod `2`:

```bash
$ kubectl exec -n lab15 lab15-devops-info-0 -- \
  getent hosts lab15-devops-info-2.lab15-devops-info-headless.lab15.svc.cluster.local

10.244.0.45 lab15-devops-info-2.lab15-devops-info-headless.lab15.svc.cluster.local
```

Headless service DNS returns all pod IPs:

```bash
$ kubectl exec -n lab15 lab15-devops-info-0 -- \
  getent hosts lab15-devops-info-headless.lab15.svc.cluster.local

10.244.0.43 lab15-devops-info-headless.lab15.svc.cluster.local
10.244.0.41 lab15-devops-info-headless.lab15.svc.cluster.local
10.244.0.45 lab15-devops-info-headless.lab15.svc.cluster.local
```

This confirms stable pod DNS through the headless service.

## 7. Per-Pod Storage Isolation

Port-forward commands used for direct pod access:

```bash
kubectl port-forward -n lab15 pod/lab15-devops-info-0 5010:5002
kubectl port-forward -n lab15 pod/lab15-devops-info-1 5011:5002
kubectl port-forward -n lab15 pod/lab15-devops-info-2 5012:5002
```

Initial counts:

```bash
$ curl -sS http://127.0.0.1:5010/visits
{"count":0,"storage_file":"/data/visits"}

$ curl -sS http://127.0.0.1:5011/visits
{"count":0,"storage_file":"/data/visits"}

$ curl -sS http://127.0.0.1:5012/visits
{"count":0,"storage_file":"/data/visits"}
```

Then different numbers of requests were sent to each pod:

```bash
for i in 1 2 3; do curl -sS http://127.0.0.1:5010/ >/dev/null; done
for i in 1 2; do curl -sS http://127.0.0.1:5011/ >/dev/null; done
curl -sS http://127.0.0.1:5012/ >/dev/null
```

Counts after requests:

```bash
$ curl -sS http://127.0.0.1:5010/visits
{"count":3,"storage_file":"/data/visits"}

$ curl -sS http://127.0.0.1:5011/visits
{"count":2,"storage_file":"/data/visits"}

$ curl -sS http://127.0.0.1:5012/visits
{"count":1,"storage_file":"/data/visits"}
```

File values inside the pods:

```bash
$ kubectl exec -n lab15 lab15-devops-info-0 -- cat /data/visits
3

$ kubectl exec -n lab15 lab15-devops-info-1 -- cat /data/visits
2

$ kubectl exec -n lab15 lab15-devops-info-2 -- cat /data/visits
1
```

This proves each pod writes to its own persistent volume.

## 8. Persistence Test

Before deleting pod `0`, its stored value was:

```bash
$ kubectl exec -n lab15 lab15-devops-info-0 -- cat /data/visits
3
```

Deleted only the pod:

```bash
$ kubectl delete pod -n lab15 lab15-devops-info-0
pod "lab15-devops-info-0" deleted from lab15 namespace
```

Waited for the replacement pod:

```bash
$ kubectl wait -n lab15 --for=condition=Ready pod/lab15-devops-info-0 --timeout=180s
pod/lab15-devops-info-0 condition met
```

The pod came back with the same StatefulSet name:

```bash
$ kubectl get pod lab15-devops-info-0 -n lab15 -o wide
lab15-devops-info-0   1/1   Running   10.244.0.49
```

The PVC stayed bound:

```bash
$ kubectl get pvc data-volume-lab15-devops-info-0 -n lab15 -o wide
data-volume-lab15-devops-info-0   Bound   pvc-e7f33e9f-f69e-4701-8f31-ed719d8217b1   100Mi   RWO   standard
```

The data survived:

```bash
$ kubectl exec -n lab15 lab15-devops-info-0 -- cat /data/visits
3
```

## 9. Bonus — Update Strategies

### 9.1 Partitioned RollingUpdate

Partitioned strategy:

```yaml
updateStrategy:
  type: RollingUpdate
  rollingUpdate:
    partition: 2
```

Configured live:

```bash
kubectl patch statefulset lab15-devops-info -n lab15 --type merge \
  -p '{"spec":{"updateStrategy":{"type":"RollingUpdate","rollingUpdate":{"partition":2}}}}'

kubectl set env statefulset/lab15-devops-info -n lab15 APP_REVISION=partition-v1
```

Result:

```bash
$ kubectl exec -n lab15 lab15-devops-info-0 -- printenv APP_REVISION
stateful-v2-visits

$ kubectl exec -n lab15 lab15-devops-info-1 -- printenv APP_REVISION
stateful-v2-visits

$ kubectl exec -n lab15 lab15-devops-info-2 -- printenv APP_REVISION
partition-v1
```

Only pod `2` updated because the partition was `2`. Pods with ordinals lower than the partition stayed on the previous revision.

### 9.2 OnDelete

OnDelete strategy:

```yaml
updateStrategy:
  type: OnDelete
```

Configured live:

```bash
kubectl patch statefulset lab15-devops-info -n lab15 --type merge \
  -p '{"spec":{"updateStrategy":{"type":"OnDelete","rollingUpdate":null}}}'

kubectl set env statefulset/lab15-devops-info -n lab15 APP_REVISION=ondelete-v1
```

After changing the template, pods did not update automatically:

```bash
$ kubectl exec -n lab15 lab15-devops-info-0 -- printenv APP_REVISION
stateful-v2-visits

$ kubectl exec -n lab15 lab15-devops-info-1 -- printenv APP_REVISION
stateful-v2-visits

$ kubectl exec -n lab15 lab15-devops-info-2 -- printenv APP_REVISION
partition-v1
```

Then pod `1` was deleted manually:

```bash
$ kubectl delete pod -n lab15 lab15-devops-info-1
pod "lab15-devops-info-1" deleted from lab15 namespace

$ kubectl wait -n lab15 --for=condition=Ready pod/lab15-devops-info-1 --timeout=180s
pod/lab15-devops-info-1 condition met
```

Only the deleted pod picked up the new template:

```bash
$ kubectl exec -n lab15 lab15-devops-info-0 -- printenv APP_REVISION
stateful-v2-visits

$ kubectl exec -n lab15 lab15-devops-info-1 -- printenv APP_REVISION
ondelete-v1

$ kubectl exec -n lab15 lab15-devops-info-2 -- printenv APP_REVISION
partition-v1
```

This strategy is useful when stateful workloads must be restarted manually and one instance at a time.

After the bonus test, the StatefulSet was returned to a regular `RollingUpdate` and all pods were reconciled to one final revision:

```bash
$ kubectl get sts lab15-devops-info -n lab15 \
  -o jsonpath='{.spec.updateStrategy.type} {.status.readyReplicas} {.status.currentReplicas} {.status.updatedReplicas} {.status.currentRevision} {.status.updateRevision}'

RollingUpdate 3 3 3 lab15-devops-info-697d89dcf8 lab15-devops-info-697d89dcf8

$ for p in 0 1 2; do kubectl exec -n lab15 lab15-devops-info-$p -- printenv APP_REVISION; done
stateful-final
stateful-final
stateful-final
```

## 10. Final Status

Final runtime state:

```bash
$ kubectl get po,sts,svc,pvc -n lab15 -o wide

pod/lab15-devops-info-0   1/1   Running
pod/lab15-devops-info-1   1/1   Running
pod/lab15-devops-info-2   1/1   Running

statefulset.apps/lab15-devops-info   3/3

service/lab15-devops-info            NodePort    80:30089/TCP
service/lab15-devops-info-headless   ClusterIP   None   80/TCP

persistentvolumeclaim/data-volume-lab15-devops-info-0   Bound   100Mi
persistentvolumeclaim/data-volume-lab15-devops-info-1   Bound   100Mi
persistentvolumeclaim/data-volume-lab15-devops-info-2   Bound   100Mi
```

Checklist:

| Requirement | Status |
|---|---|
| StatefulSet guarantees documented | Done |
| Deployment vs StatefulSet compared | Done |
| StatefulSet template created | Done |
| Headless service created | Done |
| VolumeClaimTemplates configured | Done |
| Per-pod PVCs verified | Done |
| DNS resolution tested | Done |
| Per-pod storage isolation proven | Done |
| Persistence after pod deletion tested | Done |
| Partitioned RollingUpdate tested | Done |
| OnDelete strategy tested | Done |

