# Lab 15: StatefulSet

Source chart: `lab15c/k8s/devops-info`

## Why StatefulSet

Use StatefulSet when each pod needs:
- a stable name (`devops-info-0`, `devops-info-1`, `devops-info-2`);
- its own persistent volume;
- predictable startup/update order.

Use Deployment/Rollout for stateless apps.

## What was added

- `templates/statefulset.yaml`
  - headless service link: `serviceName: devops-info-headless`
  - per-pod storage via `volumeClaimTemplates`
  - update strategy settings:
    - `statefulset.updateStrategy.type`
    - `statefulset.updateStrategy.rollingUpdate.partition`
- `templates/service-headless.yaml` with `clusterIP: None`
- values profiles:
  - `values-statefulset.yaml`
  - `values-statefulset-partition.yaml`
  - `values-statefulset-ondelete.yaml`

Rendering rules:
- `deployment.yaml` runs only when `rollouts.enabled=false` and `statefulset.enabled=false`
- `rollout.yaml` runs only when `rollouts.enabled=true` and `statefulset.enabled=false`
- `pvc.yaml` is disabled in StatefulSet mode

## Deploy

```powershell
helm upgrade --install devops-info .\lab15c\k8s\devops-info -n default `
  -f .\lab15c\k8s\devops-info\values-statefulset.yaml
```

## Verify resources

```powershell
kubectl get po,sts,svc,pvc -n default
```

Expected:
- StatefulSet `devops-info` with 3/3 ready;
- pods `devops-info-0..2`;
- services `devops-info` and `devops-info-headless`;
- PVCs `data-devops-info-0..2`.

## Verify DNS identity

```powershell
kubectl exec -it devops-info-0 -n default -- nslookup devops-info-1.devops-info-headless
kubectl exec -it devops-info-0 -n default -- nslookup devops-info-2.devops-info-headless
```

## Verify per-pod storage isolation

```powershell
kubectl port-forward pod/devops-info-0 -n default 8080:5000
kubectl port-forward pod/devops-info-1 -n default 8081:5000
curl http://localhost:8080/visits
curl http://localhost:8080/visits
curl http://localhost:8081/visits
```

`8080` and `8081` should show different counters.

## Verify persistence

```powershell
kubectl exec devops-info-0 -n default -- cat /data/visits
kubectl delete pod devops-info-0 -n default
kubectl wait --for=condition=Ready pod/devops-info-0 -n default --timeout=120s
kubectl exec devops-info-0 -n default -- cat /data/visits
```

Counter value should be preserved after restart.

## Bonus: update strategies

### Partitioned rolling update

```powershell
helm upgrade devops-info .\lab15c\k8s\devops-info -n default `
  -f .\lab15c\k8s\devops-info\values-statefulset.yaml `
  -f .\lab15c\k8s\devops-info\values-statefulset-partition.yaml `
  --set image.tag=lab15-partition-1
```

With `partition: 2`, only `devops-info-2` updates automatically.

### OnDelete

```powershell
helm upgrade devops-info .\lab15c\k8s\devops-info -n default `
  -f .\lab15c\k8s\devops-info\values-statefulset.yaml `
  -f .\lab15c\k8s\devops-info\values-statefulset-ondelete.yaml `
  --set image.tag=lab15-ondelete-1
```

Pods update only after manual delete:

```powershell
kubectl delete pod devops-info-2 -n default
kubectl delete pod devops-info-1 -n default
kubectl delete pod devops-info-0 -n default
```
