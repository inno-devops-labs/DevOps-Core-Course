# Lab 15: StatefulSets and Persistent Storage

## Scope

This lab adds a StatefulSet mode to the existing Helm chart for `devops-info-service`. The chart can still render the previous workload types, but Lab 15 uses:

```yaml
workload:
  kind: StatefulSet
```

Main chart:

```text
solution/k8s/devops-info-service
```

Implemented files:

```text
solution/k8s/devops-info-service/templates/statefulset.yaml
solution/k8s/devops-info-service/templates/service-headless.yaml
solution/k8s/devops-info-service/values-statefulset.yaml
solution/k8s/devops-info-service/values-statefulset-partition.yaml
solution/k8s/devops-info-service/values-statefulset-ondelete.yaml
```

The application image used for this lab was built from the local FastAPI source because it contains the `/visits` endpoint required for the storage tests:

```powershell
minikube image build -t devops-info-service:lab15 ./solution/app_python
```

## Planning

The lab was implemented in five stages:

1. Extend the Helm chart with a StatefulSet template and a headless service.
2. Replace shared PVC usage with `volumeClaimTemplates` when StatefulSet mode is enabled.
3. Deploy three replicas and verify pod identity, DNS, and PVC allocation.
4. Prove per-pod storage isolation and persistence after pod deletion.
5. Test StatefulSet update strategies: partitioned `RollingUpdate` and `OnDelete`.

No manual intervention was required during the execution. The only expected manual actions in another environment would be starting Docker Desktop, approving a firewall prompt for port forwarding, or checking screenshots manually if browser automation is unavailable.

## StatefulSet Overview

StatefulSets are intended for workloads that need stable identity and stable storage. Examples include databases, queues, and clustered systems such as PostgreSQL, MongoDB, Kafka, RabbitMQ, Elasticsearch, or Cassandra.

Key differences:

| Feature | Deployment | StatefulSet |
|---|---|---|
| Pod identity | Random ReplicaSet pod names | Stable ordinal names |
| Pod naming | `app-7c9d8f-px2ab` | `app-0`, `app-1`, `app-2` |
| Storage | Shared PVC or ephemeral volumes | Per-pod PVCs from `volumeClaimTemplates` |
| Scaling | Any order | Ordered by default |
| Network identity | Service load balancing | Stable pod DNS through a headless service |
| Update behavior | Rolling update across interchangeable pods | Ordered update by ordinal, with partition and OnDelete options |

For stateless traffic and progressive delivery, Rollouts from Lab 14 are the better fit. For stable identity and durable per-replica state, StatefulSets are the right controller.

## Helm Implementation

The StatefulSet template uses the existing pod template helper from the chart:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: devops-info-service
spec:
  serviceName: devops-info-service-headless
  replicas: 3
  podManagementPolicy: OrderedReady
  selector:
    matchLabels:
      app.kubernetes.io/name: devops-info-service
      app.kubernetes.io/instance: devops-info-service
  template:
    ...
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

Important storage detail:

- Deployment and Rollout modes use the chart's standalone PVC template.
- StatefulSet mode does not render the standalone PVC.
- StatefulSet mode uses `volumeClaimTemplates`, so each pod gets its own PVC.

The headless service is rendered only in StatefulSet mode:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: devops-info-service-headless
spec:
  clusterIP: None
  selector:
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: devops-info-service
```

## Deployment

The StatefulSet was deployed with:

```powershell
helm upgrade --install devops-info-service ./solution/k8s/devops-info-service `
  -f ./solution/k8s/devops-info-service/values-statefulset.yaml `
  --wait --timeout 5m
```

Verification:

```powershell
kubectl rollout status statefulset/devops-info-service --timeout=300s
kubectl get po,sts,svc,pvc -l app.kubernetes.io/instance=devops-info-service -o wide
```

Observed result:

```text
statefulset.apps/devops-info-service   3/3

pod/devops-info-service-0   Running
pod/devops-info-service-1   Running
pod/devops-info-service-2   Running

service/devops-info-service            NodePort
service/devops-info-service-headless   ClusterIP None

persistentvolumeclaim/data-volume-devops-info-service-0   Bound
persistentvolumeclaim/data-volume-devops-info-service-1   Bound
persistentvolumeclaim/data-volume-devops-info-service-2   Bound
```

Evidence:

```text
k8s/screenshots/lab15/01-resource-verification.txt
```

## Stable Network Identity

StatefulSet pods were created with ordinal names:

```text
devops-info-service-0
devops-info-service-1
devops-info-service-2
```

The headless service creates DNS records for direct pod access:

```text
devops-info-service-0.devops-info-service-headless.default.svc.cluster.local
devops-info-service-1.devops-info-service-headless.default.svc.cluster.local
devops-info-service-2.devops-info-service-headless.default.svc.cluster.local
```

DNS was tested from `devops-info-service-0`:

```powershell
kubectl exec devops-info-service-0 -- nslookup devops-info-service-1.devops-info-service-headless.default.svc.cluster.local
kubectl exec devops-info-service-0 -- nslookup devops-info-service-2.devops-info-service-headless.default.svc.cluster.local
```

Observed result:

```text
Name:    devops-info-service-1.devops-info-service-headless.default.svc.cluster.local
Address: 10.244.0.67

Name:    devops-info-service-2.devops-info-service-headless.default.svc.cluster.local
Address: 10.244.0.68
```

Evidence:

```text
k8s/screenshots/lab15/02-dns-resolution.txt
```

## Per-Pod Storage Isolation

Each pod stores visits in:

```text
/data/visits
```

The `/data` mount comes from the pod's own PVC:

```text
data-volume-devops-info-service-0
data-volume-devops-info-service-1
data-volume-devops-info-service-2
```

Each pod was accessed directly through a separate port-forward:

```powershell
kubectl port-forward pod/devops-info-service-0 18180:5000
kubectl port-forward pod/devops-info-service-1 18181:5000
kubectl port-forward pod/devops-info-service-2 18182:5000
```

Different numbers of requests were sent to each pod. The visit counters were then checked:

```text
pod-0:
{"count":2,"file_path":"/data/visits"}

pod-1:
{"count":1,"file_path":"/data/visits"}

pod-2:
{"count":3,"file_path":"/data/visits"}
```

This proves that the pods are not sharing the same visits file. Each pod writes to its own PVC-backed storage.

Evidence:

```text
k8s/screenshots/lab15/03-per-pod-storage.txt
```

## Persistence Test

The persistence test used pod `devops-info-service-0`.

Before deleting the pod:

```powershell
kubectl exec devops-info-service-0 -- cat /data/visits
```

Observed value:

```text
2
```

The pod was deleted:

```powershell
kubectl delete pod devops-info-service-0 --wait=true
kubectl wait --for=condition=Ready pod/devops-info-service-0 --timeout=180s
```

After the StatefulSet recreated the pod:

```powershell
kubectl exec devops-info-service-0 -- cat /data/visits
```

Observed value:

```text
2
```

The pod IP changed after recreation, but the data stayed the same because the PVC was reattached to the same ordinal pod.

Evidence:

```text
k8s/screenshots/lab15/04-persistence-test.txt
```

## Bonus: Partitioned RollingUpdate

Partitioned update values:

```yaml
statefulset:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 2
```

Command:

```powershell
helm upgrade devops-info-service ./solution/k8s/devops-info-service `
  -f ./solution/k8s/devops-info-service/values-statefulset-partition.yaml `
  --set env.releaseVersion=partition-v2 `
  --wait --timeout 5m
```

With `partition: 2`, only pods with ordinal greater than or equal to `2` should update. The result matched that behavior:

```text
devops-info-service-0=statefulset-v1
devops-info-service-1=statefulset-v1
devops-info-service-2=partition-v2
```

Controller revisions also showed that only `devops-info-service-2` moved to the new revision:

```text
devops-info-service-0   devops-info-service-86d4556fc4
devops-info-service-1   devops-info-service-86d4556fc4
devops-info-service-2   devops-info-service-58668f5bcf
```

Use case:

- Keep lower ordinals on the old version.
- Test a new version on higher ordinals.
- Continue the rollout later by lowering the partition.

Evidence:

```text
k8s/screenshots/lab15/05-partitioned-update.txt
```

## Bonus: OnDelete Strategy

OnDelete values:

```yaml
statefulset:
  updateStrategy:
    type: OnDelete
```

The baseline was created with:

```text
devops-info-service-0=ondelete-v1
devops-info-service-1=ondelete-v1
devops-info-service-2=ondelete-v1
```

Then the pod template was updated to `ondelete-v2`. Before any manual pod deletion, all pods stayed on the old version:

```text
devops-info-service-0=ondelete-v1
devops-info-service-1=ondelete-v1
devops-info-service-2=ondelete-v1
```

After deleting only `devops-info-service-2`, only that pod was recreated from the new template:

```text
devops-info-service-0=ondelete-v1
devops-info-service-1=ondelete-v1
devops-info-service-2=ondelete-v2
```

Use case:

- Manual control over pod replacement.
- Stateful systems where each member must be drained, checked, or coordinated before update.
- Workloads where automatic rolling replacement is too risky.

Evidence:

```text
k8s/screenshots/lab15/06-ondelete-update.txt
```

## Validation Commands

Chart validation:

```powershell
helm lint ./solution/k8s/devops-info-service
helm template devops-info-service ./solution/k8s/devops-info-service -f ./solution/k8s/devops-info-service/values-statefulset.yaml
helm template devops-info-service ./solution/k8s/devops-info-service -f ./solution/k8s/devops-info-service/values-statefulset-partition.yaml
helm template devops-info-service ./solution/k8s/devops-info-service -f ./solution/k8s/devops-info-service/values-statefulset-ondelete.yaml
```

Runtime validation:

```powershell
kubectl get statefulset devops-info-service
kubectl get pods -l app.kubernetes.io/instance=devops-info-service
kubectl get svc devops-info-service devops-info-service-headless
kubectl get pvc -l app.kubernetes.io/instance=devops-info-service
kubectl exec devops-info-service-0 -- nslookup devops-info-service-1.devops-info-service-headless.default.svc.cluster.local
kubectl exec devops-info-service-0 -- cat /data/visits
```

## Final Checklist

- StatefulSet guarantees documented.
- StatefulSet template created.
- Headless service created.
- Existing service kept for regular access.
- `volumeClaimTemplates` configured.
- One PVC per pod verified.
- Stable pod names verified.
- DNS resolution through headless service verified.
- Per-pod storage isolation verified with different visit counts.
- Persistence after pod deletion verified.
- Partitioned RollingUpdate tested.
- OnDelete update strategy tested.
