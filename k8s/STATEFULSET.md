# Lab 15 - StatefulSets and Persistent Storage

Run date: April 15, 2026

Resource-saving note:
I did not start a Kubernetes cluster for this run. Instead, I added a switchable StatefulSet path to the Helm chart, validated the manifests with `helm lint` and `helm template`, and documented the exact commands for live verification of DNS identity, per-pod storage, and persistence.

## Files Added

- `k8s/devops-info-service/templates/statefulset.yaml`
- `k8s/devops-info-service/templates/headless-service.yaml`
- `k8s/devops-info-service/values-statefulset.yaml`
- `k8s/devops-info-service/values-statefulset-partitioned.yaml`
- `k8s/devops-info-service/values-statefulset-ondelete.yaml`
- `k8s/STATEFULSET.md`

Files updated:

- `k8s/devops-info-service/templates/NOTES.txt`
- `k8s/devops-info-service/templates/_helpers.tpl`
- `k8s/devops-info-service/templates/deployment.yaml`
- `k8s/devops-info-service/templates/rollout.yaml`
- `k8s/devops-info-service/templates/pvc.yaml`
- `k8s/devops-info-service/values.yaml`
- `k8s/argocd/application.yaml`
- `k8s/argocd/application-dev.yaml`
- `k8s/argocd/application-prod.yaml`
- `k8s/argocd/applicationset.yaml`

## Validation Summary

Chart validation:

```text
.\.tools\helm.exe lint .\k8s\devops-info-service
1 chart(s) linted, 0 chart(s) failed

.\.tools\helm.exe template devops-info-service .\k8s\devops-info-service
.\.tools\helm.exe template devops-info-service-stateful .\k8s\devops-info-service -f .\k8s\devops-info-service\values-statefulset.yaml --namespace stateful
.\.tools\helm.exe template devops-info-service-stateful .\k8s\devops-info-service -f .\k8s\devops-info-service\values-statefulset-partitioned.yaml --namespace stateful
.\.tools\helm.exe template devops-info-service-stateful .\k8s\devops-info-service -f .\k8s\devops-info-service\values-statefulset-ondelete.yaml --namespace stateful
```

Meaning:

- default Deployment mode still renders
- Rollout mode from Lab 14 still renders
- StatefulSet mode and both bonus strategy profiles also render

## StatefulSet Overview

Why StatefulSet is the correct workload type here:

- each replica needs stable identity
- each replica needs its own persistent volume
- scaling and updates should happen in a predictable order

Key difference from Deployment:

- Deployments are best for stateless replicas behind a shared Service
- StatefulSets give pods stable ordinal names such as `pod-0`, `pod-1`, `pod-2`
- each pod receives its own PVC from `volumeClaimTemplates`
- DNS identity is stable because the StatefulSet uses a headless Service

Examples of real StatefulSet workloads:

- PostgreSQL
- MySQL
- MongoDB
- Kafka
- Elasticsearch

## Implementation

StatefulSet profile:

```yaml
replicaCount: 3

service:
  type: ClusterIP

statefulset:
  enabled: true

env:
  appEnv: statefulset
  appRegion: lab15
```

Rendered base StatefulSet excerpt:

```yaml
kind: Service
metadata:
  name: devops-info-service-stateful-headless
spec:
  clusterIP: None
  publishNotReadyAddresses: true
---
kind: StatefulSet
metadata:
  name: devops-info-service-stateful
spec:
  serviceName: devops-info-service-stateful-headless
  replicas: 3
  podManagementPolicy: OrderedReady
  volumeClaimTemplates:
    - metadata:
        name: data-volume
      spec:
        resources:
          requests:
            storage: 100Mi
```

What this proves:

- the chart now renders a headless Service for stable DNS
- the StatefulSet points to that service through `serviceName`
- each pod gets its own PVC based on the `data-volume` claim template
- `podManagementPolicy: OrderedReady` preserves ordered startup and scale behavior

Why this does not conflict with Lab 12:

- the old single-PVC path is still used for Deployment mode
- the StatefulSet path bypasses that guard and creates one PVC per replica
- multi-replica persistence is therefore valid again

## Headless Service and DNS Identity

DNS pattern for the rendered release:

```text
devops-info-service-stateful-0.devops-info-service-stateful-headless.stateful.svc.cluster.local
devops-info-service-stateful-1.devops-info-service-stateful-headless.stateful.svc.cluster.local
devops-info-service-stateful-2.devops-info-service-stateful-headless.stateful.svc.cluster.local
```

Prepared live DNS test:

```powershell
.\.tools\helm.exe upgrade --install devops-info-service-stateful .\k8s\devops-info-service --namespace stateful --create-namespace -f .\k8s\devops-info-service\values-statefulset.yaml
kubectl exec -it devops-info-service-stateful-0 -n stateful -- nslookup devops-info-service-stateful-1.devops-info-service-stateful-headless
kubectl exec -it devops-info-service-stateful-0 -n stateful -- nslookup devops-info-service-stateful-2.devops-info-service-stateful-headless
```

Expected result:

- each pod resolves the other pods by ordinal name through the headless Service
- the DNS names remain stable even if a specific pod is recreated

## Per-Pod Storage Isolation

Prepared live per-pod verification:

```powershell
kubectl port-forward pod/devops-info-service-stateful-0 18080:8000 -n stateful
kubectl port-forward pod/devops-info-service-stateful-1 18081:8000 -n stateful
kubectl port-forward pod/devops-info-service-stateful-2 18082:8000 -n stateful
```

Then query each pod separately:

```powershell
Invoke-RestMethod http://127.0.0.1:18080/
Invoke-RestMethod http://127.0.0.1:18081/
Invoke-RestMethod http://127.0.0.1:18082/
Invoke-RestMethod http://127.0.0.1:18080/visits
Invoke-RestMethod http://127.0.0.1:18081/visits
Invoke-RestMethod http://127.0.0.1:18082/visits
```

Expected result:

- each pod increments only its own `/data/visits` file
- visit counts diverge over time because storage is isolated per ordinal pod
- this is the opposite of the shared single-PVC deployment design from Lab 12

## Persistence Test

Prepared live persistence test:

```powershell
kubectl exec devops-info-service-stateful-0 -n stateful -- cat /data/visits
kubectl delete pod devops-info-service-stateful-0 -n stateful
kubectl get pods -n stateful -w
kubectl exec devops-info-service-stateful-0 -n stateful -- cat /data/visits
```

Expected result:

- pod `0` is recreated with the same ordinal name
- the same PVC reattaches to pod `0`
- the visits file survives pod recreation

This is the key StatefulSet guarantee:

- stable pod identity
- stable volume identity
- stable network identity

## Bonus - Update Strategies

### Partitioned Rolling Update

Bonus profile:

```yaml
statefulset:
  enabled: true
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 2
```

Rendered excerpt:

```yaml
updateStrategy:
  type: RollingUpdate
  rollingUpdate:
    partition: 2
```

Meaning:

- only pods with ordinal `>= 2` update automatically
- lower ordinals remain on the old revision until the partition changes

Prepared live command:

```powershell
.\.tools\helm.exe upgrade --install devops-info-service-stateful .\k8s\devops-info-service --namespace stateful --create-namespace -f .\k8s\devops-info-service\values-statefulset-partitioned.yaml
kubectl rollout status statefulset/devops-info-service-stateful -n stateful
```

### OnDelete Strategy

Bonus profile:

```yaml
statefulset:
  enabled: true
  updateStrategy:
    type: OnDelete
```

Rendered excerpt:

```yaml
updateStrategy:
  type: OnDelete
```

Meaning:

- Kubernetes does not automatically replace pods with the new template
- each pod updates only when it is manually deleted

Useful when:

- operators want precise control over upgrade timing
- stateful applications need manual checks between pod restarts

Prepared live command:

```powershell
.\.tools\helm.exe upgrade --install devops-info-service-stateful .\k8s\devops-info-service --namespace stateful --create-namespace -f .\k8s\devops-info-service\values-statefulset-ondelete.yaml
kubectl delete pod devops-info-service-stateful-2 -n stateful
kubectl delete pod devops-info-service-stateful-1 -n stateful
kubectl delete pod devops-info-service-stateful-0 -n stateful
```

## Resource Verification for a Live Run

Commands:

```powershell
kubectl get po,sts,svc,pvc -n stateful
kubectl describe statefulset devops-info-service-stateful -n stateful
```

What should appear:

- one StatefulSet
- one normal Service for access
- one headless Service for DNS identity
- three pods with ordinal suffixes
- three PVCs, one per pod

## Command Reference

Useful commands for the live lab run:

```powershell
.\.tools\helm.exe upgrade --install devops-info-service-stateful .\k8s\devops-info-service --namespace stateful --create-namespace -f .\k8s\devops-info-service\values-statefulset.yaml
kubectl get po,sts,svc,pvc -n stateful
kubectl exec -it devops-info-service-stateful-0 -n stateful -- nslookup devops-info-service-stateful-1.devops-info-service-stateful-headless
kubectl port-forward pod/devops-info-service-stateful-0 18080:8000 -n stateful
kubectl port-forward pod/devops-info-service-stateful-1 18081:8000 -n stateful
kubectl port-forward pod/devops-info-service-stateful-2 18082:8000 -n stateful
kubectl exec devops-info-service-stateful-0 -n stateful -- cat /data/visits
kubectl delete pod devops-info-service-stateful-0 -n stateful
```
