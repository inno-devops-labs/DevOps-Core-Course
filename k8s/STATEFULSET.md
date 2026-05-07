# Lab 15: StatefulSets & Persistent Storage

## 1. Why StatefulSet

`Deployment` is still the right controller for stateless replicas, but this lab needed pod identity and one PVC per replica. That is exactly the StatefulSet use case.

Key guarantees I used:

- stable pod names: `...-0`, `...-1`, `...-2`
- stable DNS records through a headless service
- one persistent volume claim per pod via `volumeClaimTemplates`
- ordered creation and updates

### Deployment vs StatefulSet

| Feature | Deployment | StatefulSet |
|---|---|---|
| Pod names | random suffix | stable ordinal suffix |
| Storage | usually shared or external | per-pod PVC |
| Network identity | ephemeral | stable DNS name |
| Scaling/update order | not ordered | ordered by ordinal |
| Best for | stateless web/API | databases, queues, clustered services |

Typical stateful workloads:

- PostgreSQL / MySQL
- MongoDB
- Kafka / RabbitMQ
- Elasticsearch / Cassandra

### Headless service

For direct pod addressing I added a headless service with `clusterIP: None`.

DNS pattern:

```text
<pod-name>.<headless-service>.<namespace>.svc.cluster.local
```

For this release:

```text
devops-info-sts-devops-info-service-1.devops-info-sts-devops-info-service-headless.default.svc.cluster.local
```

## 2. Chart changes

Chart path: `k8s/devops-info-service`

I added:

- `templates/statefulset.yaml`
- `templates/service-headless.yaml`
- `values-statefulset.yaml`
- `values-statefulset-partition.yaml`
- `values-statefulset-ondelete.yaml`

I also changed existing templates:

- `templates/deployment.yaml` now renders only when `statefulset.enabled=false` and `rollout.enabled=false`
- `templates/pvc.yaml` is skipped for StatefulSet mode because storage is created by `volumeClaimTemplates`
- `templates/_helpers.tpl` got a helper for the headless service name

### StatefulSet mode

Stateful mode is enabled with:

```yaml
statefulset:
  enabled: true
```

The normal service is still kept for application access, and the new headless service is used only for stable pod DNS.

### Update strategies

Bonus values files:

- `values-statefulset-partition.yaml` -> `RollingUpdate` with `partition: 2`
- `values-statefulset-ondelete.yaml` -> `OnDelete`

While testing `OnDelete` I found a template bug: `rollingUpdate` was still rendered together with `type: OnDelete`. I fixed `templates/statefulset.yaml` so `rollingUpdate` is emitted only for `type: RollingUpdate`.

## 3. Deployment

I validated the chart with:

```bash
helm lint k8s/devops-info-service
helm template devops-info k8s/devops-info-service -f k8s/devops-info-service/values-statefulset.yaml
```

For live verification in Minikube I deployed a separate release:

```bash
helm upgrade --install devops-info-sts k8s/devops-info-service \
  -f k8s/devops-info-service/values.yaml \
  -f k8s/devops-info-service/values-statefulset.yaml
```

The published image `linktur/devops-lab2:v1` did not expose `/visits`, so for StatefulSet validation I built the current app from `Lab-1/app_python` and upgraded the release to a local image:

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

Rendered StatefulSet resources:

- `StatefulSet/devops-info-sts-devops-info-service`
- `Service/devops-info-sts-devops-info-service`
- `Service/devops-info-sts-devops-info-service-headless`
- `PVC/data-volume-devops-info-sts-devops-info-service-{0,1,2}`

Live cluster output:

```powershell
PS> kubectl get po,sts,svc,pvc -l app.kubernetes.io/instance=devops-info-sts -o wide
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

This confirms the required StatefulSet behavior:

- ordered pod names `-0/-1/-2`
- separate PVC per pod
- dedicated headless service

## 5. Network identity

DNS resolution from pod `-0`:

```powershell
PS> kubectl exec devops-info-sts-devops-info-service-0 -- python -c "import socket; print(socket.gethostbyname('devops-info-sts-devops-info-service-1.devops-info-sts-devops-info-service-headless'))"
10.244.0.56
```

This proves the stable naming pattern works: `pod-0` can resolve `pod-1` through the headless service DNS name.

## 6. Per-pod storage isolation

I generated different numbers of requests on each pod and then checked `/visits` locally inside each container:

```powershell
PS> kubectl exec devops-info-sts-devops-info-service-0 -- python -c "import urllib.request; [urllib.request.urlopen('http://127.0.0.1:5000/').read() for _ in range(2)]; print(urllib.request.urlopen('http://127.0.0.1:5000/visits').read().decode())"
{"count":4,"storage_path":"/data/visits"}

PS> kubectl exec devops-info-sts-devops-info-service-1 -- python -c "import urllib.request; [urllib.request.urlopen('http://127.0.0.1:5000/').read() for _ in range(4)]; print(urllib.request.urlopen('http://127.0.0.1:5000/visits').read().decode())"
{"count":8,"storage_path":"/data/visits"}

PS> kubectl exec devops-info-sts-devops-info-service-2 -- python -c "import urllib.request; [urllib.request.urlopen('http://127.0.0.1:5000/').read() for _ in range(6)]; print(urllib.request.urlopen('http://127.0.0.1:5000/visits').read().decode())"
{"count":12,"storage_path":"/data/visits"}
```

That is the expected isolation: each pod writes to its own PVC, so counters do not overlap.

## 7. Persistence after pod deletion

Before deleting pod `-0`:

```powershell
PS> kubectl exec devops-info-sts-devops-info-service-0 -- cat /data/visits
4
```

Delete only the pod:

```bash
kubectl delete pod devops-info-sts-devops-info-service-0
```

After recreation:

```powershell
PS> kubectl wait --for=condition=ready pod/devops-info-sts-devops-info-service-0 --timeout=180s
pod/devops-info-sts-devops-info-service-0 condition met

PS> kubectl exec devops-info-sts-devops-info-service-0 -- cat /data/visits
4
```

Even after the pod was deleted and recreated:

- pod name stayed the same
- counter value stayed the same

That confirms persistent storage survived pod deletion.

## 8. Bonus: update strategies

### 8.1 RollingUpdate with partition

I enabled:

```yaml
statefulset:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 2
```

Rendered verification:

```powershell
PS> kubectl get statefulset devops-info-sts-devops-info-service -o jsonpath="{.spec.updateStrategy.type}{' partition='}{.spec.updateStrategy.rollingUpdate.partition}{'\n'}"
RollingUpdate partition=2
```

After upgrading image tag to `lab15b`, only pod `-2` moved to the new controller revision:

```powershell
PS> kubectl get statefulset devops-info-sts-devops-info-service -o jsonpath="image={.spec.template.spec.containers[0].image}{' current='}{.status.currentRevision}{' update='}{.status.updateRevision}{' updated='}{.status.updatedReplicas}{'\n'}"
image=devops-info-local:lab15b current=devops-info-sts-devops-info-service-5dd88876fc update=devops-info-sts-devops-info-service-5bbd84576c updated=1

PS> kubectl get pod devops-info-sts-devops-info-service-2 -o yaml
metadata:
  labels:
    controller-revision-hash: devops-info-sts-devops-info-service-5bbd84576c
spec:
  containers:
  - image: devops-info-local:lab15b
```

Use case: update only the highest ordinals first, keep lower ordinals untouched until manual verification is done.

### 8.2 OnDelete

I enabled:

```yaml
statefulset:
  updateStrategy:
    type: OnDelete
```

After upgrading to tag `lab15c`, the StatefulSet got a new `updateRevision`, but existing pods were not restarted automatically:

```powershell
PS> kubectl get statefulset devops-info-sts-devops-info-service -o jsonpath="type={.spec.updateStrategy.type}{' image='}{.spec.template.spec.containers[0].image}{' current='}{.status.currentRevision}{' update='}{.status.updateRevision}{' updated='}{.status.updatedReplicas}{'\n'}"
type=OnDelete image=devops-info-local:lab15c current=devops-info-sts-devops-info-service-5dd88876fc update=devops-info-sts-devops-info-service-c85c88b54 updated=

PS> kubectl get pods -l app.kubernetes.io/instance=devops-info-sts -o jsonpath="{range .items[*]}{.metadata.name}{'  rev='}{.metadata.labels.controller-revision-hash}{'  spec='}{.spec.containers[0].image}{'\n'}{end}"
devops-info-sts-devops-info-service-0  rev=devops-info-sts-devops-info-service-5dd88876fc  spec=devops-info-local:lab15
devops-info-sts-devops-info-service-1  rev=devops-info-sts-devops-info-service-5dd88876fc  spec=devops-info-local:lab15
devops-info-sts-devops-info-service-2  rev=devops-info-sts-devops-info-service-5bbd84576c  spec=devops-info-local:lab15b
```

Then I deleted only pod `-2`, and it came back on the new revision:

```bash
kubectl delete pod devops-info-sts-devops-info-service-2
```

```powershell
PS> kubectl get pods -l app.kubernetes.io/instance=devops-info-sts -o jsonpath="{range .items[*]}{.metadata.name}{'  rev='}{.metadata.labels.controller-revision-hash}{'  spec='}{.spec.containers[0].image}{'  created='}{.metadata.creationTimestamp}{'\n'}{end}"
devops-info-sts-devops-info-service-0  rev=devops-info-sts-devops-info-service-5dd88876fc  spec=devops-info-local:lab15   created=2026-05-07T17:10:19Z
devops-info-sts-devops-info-service-1  rev=devops-info-sts-devops-info-service-5dd88876fc  spec=devops-info-local:lab15   created=2026-05-07T17:08:11Z
devops-info-sts-devops-info-service-2  rev=devops-info-sts-devops-info-service-c85c88b54   spec=devops-info-local:lab15c  created=2026-05-07T17:13:35Z
```

Use case: tightly controlled updates where an operator or automation explicitly decides when each replica should restart.

## 9. Commands reference

```bash
# Chart validation
helm lint k8s/devops-info-service
helm template devops-info k8s/devops-info-service -f k8s/devops-info-service/values-statefulset.yaml

# Deploy StatefulSet
helm upgrade --install devops-info-sts k8s/devops-info-service \
  -f k8s/devops-info-service/values.yaml \
  -f k8s/devops-info-service/values-statefulset.yaml

# Check resources
kubectl get po,sts,svc,pvc -l app.kubernetes.io/instance=devops-info-sts
kubectl describe pod devops-info-sts-devops-info-service-0
kubectl describe pvc data-volume-devops-info-sts-devops-info-service-0

# DNS / identity
kubectl exec devops-info-sts-devops-info-service-0 -- python -c "import socket; print(socket.gethostbyname('devops-info-sts-devops-info-service-1.devops-info-sts-devops-info-service-headless'))"

# Storage isolation
kubectl exec devops-info-sts-devops-info-service-0 -- python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5000/visits').read().decode())"

# Persistence
kubectl delete pod devops-info-sts-devops-info-service-0
kubectl exec devops-info-sts-devops-info-service-0 -- cat /data/visits
```
