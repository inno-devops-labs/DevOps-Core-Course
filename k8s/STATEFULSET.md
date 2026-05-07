# Lab 15: StatefulSets & Persistent Storage

## 1. StatefulSet overview

In this lab I changed my application from `Deployment` to `StatefulSet`.

A `Deployment` is good for stateless apps. A `StatefulSet` is better when pods need:

- stable names
- stable network identity
- separate storage for each pod

This is useful for:

- databases
- message brokers
- distributed systems

### Deployment vs StatefulSet

| Feature | Deployment | StatefulSet |
|---|---|---|
| Pod name | random suffix | fixed index like `pod-0`, `pod-1` |
| Storage | shared or external | one PVC for each pod |
| Network identity | not stable | stable DNS name |
| Update order | no strict order | ordered |

### Headless Service

I added a headless service with:

```yaml
clusterIP: None
```

This service gives direct DNS names for StatefulSet pods.

DNS format:

```text
<pod-name>.<headless-service>.<namespace>.svc.cluster.local
```

Example from this lab:

```text
devops-info-sts-devops-info-service-1.devops-info-sts-devops-info-service-headless
```

## 2. What I changed in the Helm chart

Chart path:

```text
k8s/devops-info-service
```

I added these files:

- `templates/statefulset.yaml`
- `templates/service-headless.yaml`
- `values-statefulset.yaml`
- `values-statefulset-partition.yaml`
- `values-statefulset-ondelete.yaml`

I also updated these files:

- `templates/deployment.yaml`
- `templates/pvc.yaml`
- `templates/_helpers.tpl`
- `values.yaml`

### Main idea

- normal `Deployment` works only when `statefulset.enabled=false`
- normal single PVC is disabled in StatefulSet mode
- StatefulSet uses `volumeClaimTemplates`
- each pod gets its own PVC automatically
- external access still uses the normal service
- pod-to-pod access uses the headless service

## 3. Validation commands

I checked the chart with:

```bash
helm lint k8s/devops-info-service
helm template devops-info k8s/devops-info-service -f k8s/devops-info-service/values-statefulset.yaml
```

I deployed StatefulSet with:

```bash
helm upgrade --install devops-info-sts k8s/devops-info-service \
  -f k8s/devops-info-service/values.yaml \
  -f k8s/devops-info-service/values-statefulset.yaml
```

For live testing in Minikube I used a local image, because the old public image did not have the `/visits` endpoint:

```bash
docker build -t devops-info-local:lab15 Lab-1/app_python
minikube image load devops-info-local:lab15

helm upgrade devops-info-sts k8s/devops-info-service \
  -f k8s/devops-info-service/values.yaml \
  -f k8s/devops-info-service/values-statefulset.yaml \
  --set image.repository=devops-info-local \
  --set image.tag=lab15 \
  --set image.pullPolicy=IfNotPresent
```

## 4. Resource verification

I checked only the resources for this release:

```powershell
PS> kubectl get po,sts,svc,pvc -l app.kubernetes.io/instance=devops-info-sts
NAME                                        READY   STATUS    RESTARTS   AGE
pod/devops-info-sts-devops-info-service-0   1/1     Running   0          56m
pod/devops-info-sts-devops-info-service-1   1/1     Running   0          58m
pod/devops-info-sts-devops-info-service-2   1/1     Running   0          50m

NAME                                                   READY   AGE
statefulset.apps/devops-info-sts-devops-info-service   3/3     61m

NAME                                                   TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/devops-info-sts-devops-info-service            NodePort    10.100.170.224   <none>        80:32191/TCP   61m
service/devops-info-sts-devops-info-service-headless   ClusterIP   None             <none>        80/TCP         61m

NAME                                                                      STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/data-volume-devops-info-sts-devops-info-service-0   Bound    pvc-885e0ece-3c03-42a7-bdae-1a2c06bdb6d6   100Mi      RWO            standard       <unset>                 61m
persistentvolumeclaim/data-volume-devops-info-sts-devops-info-service-1   Bound    pvc-95e44a87-cc02-46d5-a85b-1d137b2fc133   100Mi      RWO            standard       <unset>                 61m
persistentvolumeclaim/data-volume-devops-info-sts-devops-info-service-2   Bound    pvc-e2680a75-f981-4ac2-8a58-3d8fd37da441   100Mi      RWO            standard       <unset>                 61m
```

This proves:

- StatefulSet is running
- pod names are stable: `-0`, `-1`, `-2`
- headless service exists
- each pod has its own PVC

## 5. Network identity

I tested DNS from pod `0` to pod `1`:

```powershell
PS> kubectl exec devops-info-sts-devops-info-service-0 -- python -c "import socket; print(socket.gethostbyname('devops-info-sts-devops-info-service-1.devops-info-sts-devops-info-service-headless'))"
10.244.0.56
```

This proves the headless service DNS works.

## 6. Per-pod storage

I sent a different number of requests to each pod and checked `/visits`.

```powershell
PS> kubectl exec devops-info-sts-devops-info-service-0 -- python -c "import urllib.request; [urllib.request.urlopen('http://127.0.0.1:5000/').read() for _ in range(2)]; print(urllib.request.urlopen('http://127.0.0.1:5000/visits').read().decode())"
{"count":4,"storage_path":"/data/visits"}

PS> kubectl exec devops-info-sts-devops-info-service-1 -- python -c "import urllib.request; [urllib.request.urlopen('http://127.0.0.1:5000/').read() for _ in range(4)]; print(urllib.request.urlopen('http://127.0.0.1:5000/visits').read().decode())"
{"count":8,"storage_path":"/data/visits"}

PS> kubectl exec devops-info-sts-devops-info-service-2 -- python -c "import urllib.request; [urllib.request.urlopen('http://127.0.0.1:5000/').read() for _ in range(6)]; print(urllib.request.urlopen('http://127.0.0.1:5000/visits').read().decode())"
{"count":12,"storage_path":"/data/visits"}
```

This proves each pod has separate data.

- pod `0` has `4`
- pod `1` has `8`
- pod `2` has `12`

If storage was shared, the values would be the same.

## 7. Persistence test

First I checked the value inside pod `0`:

```powershell
PS> kubectl exec devops-info-sts-devops-info-service-0 -- cat /data/visits
4
```

Then I deleted only the pod:

```powershell
PS> kubectl delete pod devops-info-sts-devops-info-service-0
pod "devops-info-sts-devops-info-service-0" deleted from default namespace
```

I waited until the pod was ready again:

```powershell
PS> kubectl wait --for=condition=ready pod/devops-info-sts-devops-info-service-0 --timeout=180s
pod/devops-info-sts-devops-info-service-0 condition met
```

After restart I checked the file again:

```powershell
PS> kubectl exec devops-info-sts-devops-info-service-0 -- cat /data/visits
4
```

The value stayed the same.

This proves:

- the pod was recreated
- the data was not lost
- the same PVC was reused

## 8. Bonus: update strategies

### RollingUpdate with partition

I also added support for:

```yaml
statefulset:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 2
```

This strategy updates only pods with ordinal index greater than or equal to the partition value.

In this case, Kubernetes can update pod `2` first and keep pods `0` and `1` unchanged.

### OnDelete

I added support for:

```yaml
statefulset:
  updateStrategy:
    type: OnDelete
```

With `OnDelete`, pods are not updated automatically.

They are updated only after manual deletion.

During testing I found one template problem: `rollingUpdate` must not be rendered when strategy type is `OnDelete`. I fixed this in `templates/statefulset.yaml`.

## 9. Useful commands

```bash
# validate chart
helm lint k8s/devops-info-service
helm template devops-info k8s/devops-info-service -f k8s/devops-info-service/values-statefulset.yaml

# deploy
helm upgrade --install devops-info-sts k8s/devops-info-service \
  -f k8s/devops-info-service/values.yaml \
  -f k8s/devops-info-service/values-statefulset.yaml

# check resources
kubectl get po,sts,svc,pvc -l app.kubernetes.io/instance=devops-info-sts

# check DNS
kubectl exec devops-info-sts-devops-info-service-0 -- python -c "import socket; print(socket.gethostbyname('devops-info-sts-devops-info-service-1.devops-info-sts-devops-info-service-headless'))"

# check visits
kubectl exec devops-info-sts-devops-info-service-0 -- cat /data/visits
kubectl exec devops-info-sts-devops-info-service-0 -- python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5000/visits').read().decode())"

# persistence test
kubectl delete pod devops-info-sts-devops-info-service-0
kubectl wait --for=condition=ready pod/devops-info-sts-devops-info-service-0 --timeout=180s
kubectl exec devops-info-sts-devops-info-service-0 -- cat /data/visits
```

## 10. Result

Lab 15 is complete.

I implemented and tested:

- StatefulSet
- headless service
- one PVC for each pod
- stable pod DNS
- separate storage for each replica
- data persistence after pod deletion
- bonus update strategies
