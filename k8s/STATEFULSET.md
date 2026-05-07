# Lab 15 - StatefulSets and Persistent Storage

## StatefulSet Overview

This lab uses a `StatefulSet` for `devops-info-service` because the application now stores a visit counter on disk. A `Deployment` is still the right default for stateless replicas because pods can be created, deleted, and replaced in any order with random names. A `StatefulSet` is a better fit when each replica needs a stable identity and its own storage.

Key differences:

| Capability | Deployment | StatefulSet |
| --- | --- | --- |
| Pod names | Random suffixes, such as `app-7d9c8d9b9f-xq42m` | Ordered names, such as `app-0`, `app-1`, `app-2` |
| Network identity | Service load balances across interchangeable pods | Each pod gets stable DNS through a headless Service |
| Storage | Usually shared or ephemeral | One PVC per pod from `volumeClaimTemplates` |
| Scaling order | Any order | Ordered by default, `0 -> 1 -> 2` on scale up |
| Common workloads | Web APIs, workers, frontends | Databases, queues, clustered systems, per-replica state |

The chart keeps the external Service for normal access and adds a headless Service with `clusterIP: None` for stable pod DNS:

```text
<pod-name>.<headless-service>.<namespace>.svc.cluster.local
lab15-devops-info-service-0.lab15-devops-info-service-headless.default.svc.cluster.local
```

## Implementation

Files added or updated:

- `app_python/app.py` adds a file-backed visits counter and `/visits`.
- `app_python/Dockerfile.lab15` builds the Lab 15 image from the existing Lab 9 image and copies in the updated app.
- `app_python/tests/test_get_visits.py` verifies the counter endpoint and persisted file.
- `k8s/devops-info-service/templates/statefulset.yaml` renders the StatefulSet.
- `k8s/devops-info-service/templates/headless-service.yaml` renders the headless Service.
- `k8s/devops-info-service/templates/deployment.yaml` remains available when `workload.type=Deployment`.
- `k8s/devops-info-service/values.yaml` configures `workload`, `statefulset`, and `persistence`.

The default Lab 15 chart renders:

```yaml
workload:
  type: StatefulSet

replicaCount: 3

persistence:
  mountPath: /data
  accessModes:
    - ReadWriteOnce
  size: 100Mi
  storageClass: ""

statefulset:
  podManagementPolicy: OrderedReady
  updateStrategy:
    type: RollingUpdate
    partition: 0
```

## Resource Verification

Render check:

```bash
helm template lab15 k8s/devops-info-service --dependency-update
```

Important rendered resources:

```text
ServiceAccount/lab15-devops-info-service
Secret/lab15-devops-info-service-secret
Service/lab15-devops-info-service
Service/lab15-devops-info-service-headless clusterIP=None
StatefulSet/lab15-devops-info-service replicas=3 serviceName=lab15-devops-info-service-headless
volumeClaimTemplates: data, ReadWriteOnce, 100Mi
```

Live verification commands:

```bash
helm upgrade --install lab15 k8s/devops-info-service --dependency-update
kubectl get po,sts,svc,pvc -l app.kubernetes.io/instance=lab15
```

Actual output:

```text
NAME                              READY   STATUS    RESTARTS   AGE   IP            NODE
pod/lab15-devops-info-service-0   1/1     Running   0          56s   10.244.0.15   lab10-control-plane
pod/lab15-devops-info-service-1   1/1     Running   0          45s   10.244.0.17   lab10-control-plane
pod/lab15-devops-info-service-2   1/1     Running   0          34s   10.244.0.19   lab10-control-plane

NAME                                         READY   AGE   CONTAINERS            IMAGES
statefulset.apps/lab15-devops-info-service   3/3     56s   devops-info-service   devops-info-service:lab15

NAME                                         TYPE        CLUSTER-IP      PORT(S)
service/lab15-devops-info-service            NodePort    10.96.105.195  80:30095/TCP
service/lab15-devops-info-service-headless   ClusterIP   None           80/TCP

NAME                                      STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS
data-lab15-devops-info-service-0          Bound    pvc-6dca7af4-3fb0-49de-9bc8-d6d84e97ca28   100Mi      RWO            standard
data-lab15-devops-info-service-1          Bound    pvc-9e48ee8a-e960-4ecd-9b6e-4fa9777076f8   100Mi      RWO            standard
data-lab15-devops-info-service-2          Bound    pvc-1a9b88ed-7f78-4e91-86f2-55ca54805d9e   100Mi      RWO            standard
```

## Network Identity

DNS test:

```bash
kubectl exec -it lab15-devops-info-service-0 -- nslookup lab15-devops-info-service-1.lab15-devops-info-service-headless
kubectl exec -it lab15-devops-info-service-0 -- nslookup lab15-devops-info-service-2.lab15-devops-info-service-headless.default.svc.cluster.local
```

Actual result:

```text
lab15-devops-info-service-1.lab15-devops-info-service-headless -> 10.244.0.17
lab15-devops-info-service-2.lab15-devops-info-service-headless.default.svc.cluster.local -> 10.244.0.19
```

The stable naming pattern is:

```text
<statefulset-name>-<ordinal>.<headless-service-name>.<namespace>.svc.cluster.local
```

## Per-Pod Storage Evidence

Forward each pod independently:

```bash
kubectl port-forward pod/lab15-devops-info-service-0 8080:5000
kubectl port-forward pod/lab15-devops-info-service-1 8081:5000
kubectl port-forward pod/lab15-devops-info-service-2 8082:5000
```

Generate different counts:

```bash
curl http://127.0.0.1:8080/
curl http://127.0.0.1:8080/
curl http://127.0.0.1:8081/
curl http://127.0.0.1:8082/visits
curl http://127.0.0.1:8080/visits
curl http://127.0.0.1:8081/visits
```

Actual evidence:

```text
pod/lab15-devops-info-service-0 /visits -> {"visits":2,"file":"/data/visits","hostname":"lab15-devops-info-service-0"}
pod/lab15-devops-info-service-1 /visits -> {"visits":1,"file":"/data/visits","hostname":"lab15-devops-info-service-1"}
pod/lab15-devops-info-service-2 /visits -> {"visits":0,"file":"/data/visits","hostname":"lab15-devops-info-service-2"}
```

PVC file checks:

```bash
kubectl exec lab15-devops-info-service-0 -- cat /data/visits
kubectl exec lab15-devops-info-service-1 -- cat /data/visits
kubectl exec lab15-devops-info-service-2 -- sh -c 'cat /data/visits 2>/dev/null || echo 0'
```

Actual PVC file values:

```text
lab15-devops-info-service-0 /data/visits=2
lab15-devops-info-service-1 /data/visits=1
lab15-devops-info-service-2 /data/visits=0
```

## Persistence Test

Record the count, delete only the pod, then verify the replacement pod keeps the same ordinal and mounted PVC:

```bash
kubectl exec lab15-devops-info-service-0 -- cat /data/visits
kubectl delete pod lab15-devops-info-service-0
kubectl rollout status statefulset/lab15-devops-info-service
kubectl exec lab15-devops-info-service-0 -- cat /data/visits
```

Actual evidence:

```text
before=2
pod "lab15-devops-info-service-0" deleted
pod/lab15-devops-info-service-0 condition met
after=2
lab15-devops-info-service-0   1/1   Running   0   7s   10.244.0.20   lab10-control-plane
```

The PVC name stays `data-lab15-devops-info-service-0`, so the replacement pod receives the same persisted `/data/visits` file.

## Bonus - Update Strategies

Partitioned rolling update is configured through values:

```bash
helm upgrade --install lab15 k8s/devops-info-service \
  --set statefulset.updateStrategy.type=RollingUpdate \
  --set statefulset.updateStrategy.partition=2
```

With `partition=2`, only pods with ordinal `>= 2` update automatically. For three replicas, `lab15-devops-info-service-2` updates while `-0` and `-1` stay on the old revision.

Actual partition verification:

```text
statefulset.apps/lab15-devops-info-service patched
strategy=RollingUpdate partition=2

before_partition_change
lab15-devops-info-service-0   lab15-devops-info-service-5ff5585dd8
lab15-devops-info-service-1   lab15-devops-info-service-6bf494649f
lab15-devops-info-service-2   lab15-devops-info-service-579bc898c9

after_partition_template_patch
current=lab15-devops-info-service-5ff5585dd8 update=lab15-devops-info-service-8648fc7569
lab15-devops-info-service-0   lab15-devops-info-service-5ff5585dd8
lab15-devops-info-service-1   lab15-devops-info-service-6bf494649f
lab15-devops-info-service-2   lab15-devops-info-service-8648fc7569
```

`OnDelete` strategy is also supported:

```bash
helm upgrade --install lab15 k8s/devops-info-service \
  --set statefulset.updateStrategy.type=OnDelete
kubectl delete pod lab15-devops-info-service-2
```

With `OnDelete`, StatefulSet pods do not update just because the template changes. Each pod updates only after it is manually deleted. This is useful for stateful systems that require operator-controlled restarts, quorum checks, or manual data migration between replicas.

Actual OnDelete verification:

```text
statefulset.apps/lab15-devops-info-service patched
strategy=OnDelete

before_ondelete_change
lab15-devops-info-service-0   lab15-devops-info-service-5ff5585dd8
lab15-devops-info-service-1   lab15-devops-info-service-5ff5585dd8
lab15-devops-info-service-2   lab15-devops-info-service-579bc898c9

after_ondelete_template_patch
current=lab15-devops-info-service-5ff5585dd8 update=lab15-devops-info-service-6bf494649f
lab15-devops-info-service-0   lab15-devops-info-service-5ff5585dd8
lab15-devops-info-service-1   lab15-devops-info-service-5ff5585dd8
lab15-devops-info-service-2   lab15-devops-info-service-579bc898c9

pod "lab15-devops-info-service-1" deleted
pod/lab15-devops-info-service-1 condition met

after_delete_pod_1
lab15-devops-info-service-0   lab15-devops-info-service-5ff5585dd8
lab15-devops-info-service-1   lab15-devops-info-service-6bf494649f
lab15-devops-info-service-2   lab15-devops-info-service-579bc898c9
```
