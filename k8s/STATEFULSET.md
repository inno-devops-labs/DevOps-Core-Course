# Lab 15 - StatefulSets & Persistent Storage

## 1. StatefulSet Overview

StatefulSet is used when workload instances need:

- Stable pod identity (`<name>-0`, `<name>-1`, ...)
- Stable network identity via headless service DNS
- Persistent per-pod storage (separate PVC per pod)
- Ordered scale/update behavior

Deployment is better for stateless workloads where pod identity and per-pod disks are not required.

## 2. Helm Implementation (Chart Changes)

Implemented in `k8s/devops-python`:

- `templates/statefulset.yaml` (new)
- `templates/service-headless.yaml` (new)
- `templates/pvc.yaml` updated to skip standalone PVC when StatefulSet is enabled
- `templates/deployment.yaml` updated to disable Deployment when StatefulSet is enabled
- `templates/rollout.yaml` updated to disable Rollout when StatefulSet is enabled
- `templates/_helpers.tpl` added `devops-python.headlessServiceName`
- values updates:
  - `values.yaml`: `statefulset.*`, `headlessService.enabled`
  - `values-dev.yaml`: StatefulSet mode enabled
  - `values-prod.yaml`: StatefulSet mode enabled + partitioned rolling update (bonus)

## 3. Deploy & Verify Resources

```bash
helm upgrade --install lab15-dev k8s/devops-python \
  -n lab15 --create-namespace \
  -f k8s/devops-python/values-dev.yaml \
  --set hooks.enabled=false \
  --set vault.enabled=false

kubectl get po,sts,svc,pvc -n lab15
```

Real output (from run):

```text
NAME                            READY   STATUS    RESTARTS   AGE
pod/lab15-dev-devops-python-0   1/1     Running   0          31s

NAME                                       READY   AGE
statefulset.apps/lab15-dev-devops-python   1/1     31s

NAME                                       TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)   AGE
service/lab15-dev-devops-python            ClusterIP   10.96.219.9   <none>        80/TCP    31s
service/lab15-dev-devops-python-headless   ClusterIP   None          <none>        80/TCP    31s

NAME                                                          STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/data-volume-lab15-dev-devops-python-0   Bound    pvc-11752afd-5b26-4413-9276-ad7e822f6552   100Mi      RWO            standard       31s
```

## 4. Network Identity (DNS)

```bash
POD0=$(kubectl -n lab15 get pod -l app.kubernetes.io/instance=lab15-dev -o jsonpath='{.items[0].metadata.name}')
kubectl -n lab15 exec "$POD0" -- sh -lc "getent hosts lab15-dev-devops-python-0.lab15-dev-devops-python-headless.lab15.svc.cluster.local && getent hosts lab15-dev-devops-python-1.lab15-dev-devops-python-headless.lab15.svc.cluster.local"
```

After scaling to 2 replicas, real output:

```text
10.244.0.25  lab15-dev-devops-python-1.lab15-dev-devops-python-headless.lab15.svc.cluster.local
```

Pattern:

`<statefulset-pod>.<headless-service>.<namespace>.svc.cluster.local`

## 5. Per-Pod Storage Isolation

Use direct pod port-forwards (separate pod identity, separate volume):

```bash
kubectl -n lab15 port-forward pod/lab15-dev-devops-python-0 18080:8080
kubectl -n lab15 port-forward pod/lab15-dev-devops-python-1 18081:8080
```

In second terminal:

```bash
curl http://127.0.0.1:18080/
curl http://127.0.0.1:18080/
curl http://127.0.0.1:18081/
curl http://127.0.0.1:18081/

kubectl -n lab15 exec lab15-dev-devops-python-0 -- cat /data/visits
kubectl -n lab15 exec lab15-dev-devops-python-1 -- cat /data/visits
```

Because current app build does not expose `/visits`, isolation was validated by writing direct values:

```bash
kubectl -n lab15 exec lab15-dev-devops-python-0 -- sh -lc 'echo pod0-data > /data/visits'
kubectl -n lab15 exec lab15-dev-devops-python-1 -- sh -lc 'echo pod1-data > /data/visits'
kubectl -n lab15 exec lab15-dev-devops-python-0 -- cat /data/visits
kubectl -n lab15 exec lab15-dev-devops-python-1 -- cat /data/visits
```

Real output:

```text
pod0-data
pod1-data
```

## 6. Persistence Test

```bash
kubectl -n lab15 exec lab15-dev-devops-python-0 -- cat /data/visits
kubectl -n lab15 delete pod lab15-dev-devops-python-0
kubectl -n lab15 wait --for=condition=Ready pod/lab15-dev-devops-python-0 --timeout=180s
kubectl -n lab15 exec lab15-dev-devops-python-0 -- cat /data/visits
```

Real output:

```text
pod0-data
pod "lab15-dev-devops-python-0" deleted from lab15 namespace
pod/lab15-dev-devops-python-0 condition met
pod0-data
```

## 7. Bonus - Update Strategies

### 7.1 Partitioned RollingUpdate

Prod values set:

```yaml
statefulset:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 2
```

Meaning: only pods with ordinal `>= 2` update automatically.

Validation:

```bash
helm upgrade --install lab15-prod k8s/devops-python \
  -n lab15-prod --create-namespace \
  -f k8s/devops-python/values-prod.yaml \
  --set hooks.enabled=false \
  --set vault.enabled=false

kubectl get sts -n lab15-prod
kubectl describe sts lab15-prod-devops-python -n lab15-prod | grep -A3 "Update Strategy"
```

Real output:

```text
Update Strategy:    RollingUpdate
  Partition:        2
```

### 7.2 OnDelete Strategy

Temporary runtime test:

```bash
kubectl patch sts lab15-dev-devops-python -n lab15 --type merge -p '{"spec":{"updateStrategy":{"type":"OnDelete","rollingUpdate":null}}}'
kubectl get sts lab15-dev-devops-python -n lab15 -o yaml | grep -A3 updateStrategy
```

Real output:

```text
statefulset.apps/lab15-dev-devops-python patched
updateStrategy:
  type: OnDelete
```

With `OnDelete`, pods are updated only after manual pod deletion.

## 8. StatefulSet vs Deployment (Summary)

- StatefulSet:
  - stable pod name and DNS
  - per-pod persistent volume
  - ordered lifecycle and advanced update control
- Deployment:
  - interchangeable stateless pods
  - no per-pod identity guarantees
  - faster/simple rolling behavior

## 9. Useful Commands

```bash
kubectl get sts,pod,svc,pvc -n <ns>
kubectl describe sts <name> -n <ns>
kubectl exec -n <ns> <pod> -- cat /data/visits
kubectl delete pod -n <ns> <pod>
kubectl patch sts <name> -n <ns> --type merge -p '{"spec":{"updateStrategy":{"type":"OnDelete"}}}'
kubectl rollout status sts/<name> -n <ns>
```
