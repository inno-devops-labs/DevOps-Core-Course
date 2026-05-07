# Lab 15 - StatefulSets and Persistent Storage

## What I built

The Helm chart now supports the Python service as a StatefulSet for the Lab 15 stateful workload path:

- `templates/statefulset.yaml` renders the app as a Kubernetes `StatefulSet`
- `templates/headless-service.yaml` creates `devops-info-service-headless` with `clusterIP: None`
- the regular `templates/service.yaml` remains available for external access
- `volumeClaimTemplates` creates one `data-volume` PVC per pod
- `templates/rollout.yaml` remains in the chart for Lab 14, but it is disabled by the default Lab 15 values
- `values-statefulset.yaml` is the main Lab 15 values file
- `values-statefulset-partition.yaml` demonstrates a partitioned rolling update
- `values-statefulset-ondelete.yaml` demonstrates the `OnDelete` strategy

StatefulSet mode is enabled in `values.yaml` because Lab 15 focuses on stable pod identity and per-pod persistence. The canary and blue-green values files explicitly set `statefulset.enabled=false` so the older Rollout paths still render.

## StatefulSet overview

Use a StatefulSet when the application needs stable identity, stable storage, or ordered lifecycle operations. In this lab, each pod stores its visit counter in `/data/visits`, so a shared Deployment PVC would make replicas fight over the same file. The StatefulSet gives each replica an independent PVC.

| Capability | Deployment or Rollout | StatefulSet |
| --- | --- | --- |
| Pod name | ReplicaSet generated suffix | Stable ordinal suffix |
| Example pod | `devops-info-service-6d8d7b7d9c-k9r8p` | `devops-info-service-0` |
| Storage | Shared PVC or ephemeral volume | PVC per pod from `volumeClaimTemplates` |
| Network identity | Service load balancing | Pod DNS through a headless Service |
| Startup and shutdown | ReplicaSet controlled | Ordered by ordinal with `OrderedReady` |
| Best fit | Stateless HTTP apps and progressive delivery | Databases, queues, clustered systems, stateful app replicas |

The headless Service does not allocate a cluster IP. Instead, it creates DNS records for the selected pods:

```text
<pod-name>.<headless-service>.<namespace>.svc.cluster.local
```

For this release, the pattern is:

```text
devops-info-service-0.devops-info-service-headless.lab15.svc.cluster.local
devops-info-service-1.devops-info-service-headless.lab15.svc.cluster.local
devops-info-service-2.devops-info-service-headless.lab15.svc.cluster.local
```

## Install

```bash
helm upgrade --install devops-info-service k8s/devops-info-service \
  --namespace lab15 \
  --create-namespace \
  -f k8s/devops-info-service/values-statefulset.yaml \
  --set service.nodePort=30086 \
  --wait --timeout 300s
```

I used NodePort `30086` because the earlier lab namespaces already use `30080` through `30085`.

## Resource verification

```text
$ kubectl get po,sts,svc,pvc -n lab15 -o wide
NAME                        READY   STATUS    RESTARTS   AGE   IP            NODE                  NOMINATED NODE   READINESS GATES
pod/devops-info-service-0   1/1     Running   0          3m    10.244.0.40   lab13-control-plane   <none>           <none>
pod/devops-info-service-1   1/1     Running   0          4s    10.244.0.44   lab13-control-plane   <none>           <none>
pod/devops-info-service-2   1/1     Running   0          39s   10.244.0.43   lab13-control-plane   <none>           <none>

NAME                                   READY   AGE     CONTAINERS            IMAGES
statefulset.apps/devops-info-service   3/3     4m35s   devops-info-service   devops-info-service-python:lab12

NAME                                   TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)        AGE     SELECTOR
service/devops-info-service            NodePort    10.96.49.58   <none>        80:30086/TCP   4m22s   app.kubernetes.io/instance=devops-info-service,app.kubernetes.io/name=devops-info-service
service/devops-info-service-headless   ClusterIP   None          <none>        80/TCP         4m35s   app.kubernetes.io/instance=devops-info-service,app.kubernetes.io/name=devops-info-service

NAME                                                      STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE     VOLUMEMODE
persistentvolumeclaim/data-volume-devops-info-service-0   Bound    pvc-df9e3532-361b-47cf-a2c5-ffe690c0adc5   100Mi      RWO            standard       <unset>                 4m35s   Filesystem
persistentvolumeclaim/data-volume-devops-info-service-1   Bound    pvc-a3362908-8713-49a1-a3da-8bdf1e78e207   100Mi      RWO            standard       <unset>                 4m28s   Filesystem
persistentvolumeclaim/data-volume-devops-info-service-2   Bound    pvc-20c5d848-5ac6-436b-8b69-21166bec81ad   100Mi      RWO            standard       <unset>                 4m20s   Filesystem
```

The pod names have stable ordinal suffixes, and the PVC names include those same ordinals.

## Network identity

The pods expose their StatefulSet identity through `hostname` and `subdomain`:

```text
$ kubectl get pods -n lab15 -l app.kubernetes.io/instance=devops-info-service -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.hostname}{"\t"}{.spec.subdomain}{"\n"}{end}'
devops-info-service-0	devops-info-service-0	devops-info-service-headless
devops-info-service-1	devops-info-service-1	devops-info-service-headless
devops-info-service-2	devops-info-service-2	devops-info-service-headless
```

DNS resolution from inside `devops-info-service-0`:

```text
$ kubectl exec -n lab15 devops-info-service-0 -- python -c "import socket; names=['devops-info-service-0.devops-info-service-headless','devops-info-service-1.devops-info-service-headless','devops-info-service-2.devops-info-service-headless']; [print(name, socket.gethostbyname(name)) for name in names]"
devops-info-service-0.devops-info-service-headless 10.244.0.40
devops-info-service-1.devops-info-service-headless 10.244.0.44
devops-info-service-2.devops-info-service-headless 10.244.0.43
```

Pod 0 kept the same DNS name after deletion, even though its IP changed from `10.244.0.35` to `10.244.0.40`.

## Per-pod storage evidence

I called the root endpoint twice on pod 0, once on pod 1, and once on pod 2. Then I read `/visits` from each pod.

```text
$ kubectl exec -n lab15 devops-info-service-0 -- python -c "import json,urllib.request; print(json.load(urllib.request.urlopen('http://127.0.0.1:5000/visits'))['count'])"
2
$ kubectl exec -n lab15 devops-info-service-1 -- python -c "import json,urllib.request; print(json.load(urllib.request.urlopen('http://127.0.0.1:5000/visits'))['count'])"
1
$ kubectl exec -n lab15 devops-info-service-2 -- python -c "import json,urllib.request; print(json.load(urllib.request.urlopen('http://127.0.0.1:5000/visits'))['count'])"
1
```

The backing files confirm the same isolation:

```text
$ kubectl exec -n lab15 devops-info-service-0 -- cat /data/visits
2
$ kubectl exec -n lab15 devops-info-service-1 -- cat /data/visits
1
$ kubectl exec -n lab15 devops-info-service-2 -- cat /data/visits
1
```

The replicas are running the same image and chart release, but each pod has its own counter because each pod has its own PVC.

## Persistence test

Before deleting pod 0:

```text
$ kubectl exec -n lab15 devops-info-service-0 -- cat /data/visits
2
```

Delete only the pod:

```bash
kubectl delete pod -n lab15 devops-info-service-0
kubectl wait --for=condition=Ready pod/devops-info-service-0 -n lab15 --timeout=180s
```

After it came back:

```text
$ kubectl get pod devops-info-service-0 -n lab15 -o wide
NAME                    READY   STATUS    RESTARTS   AGE   IP            NODE                  NOMINATED NODE   READINESS GATES
devops-info-service-0   1/1     Running   0          5s    10.244.0.40   lab13-control-plane   <none>           <none>

$ kubectl exec -n lab15 devops-info-service-0 -- cat /data/visits
2
```

The pod was recreated with a new IP, but the ordinal identity and PVC stayed attached.

## Update strategy bonus

The default StatefulSet values use:

```yaml
statefulset:
  updateStrategy:
    type: RollingUpdate
    partition: null
```

### Partitioned RollingUpdate

Install the partitioned strategy and change the visible service version:

```bash
helm upgrade devops-info-service k8s/devops-info-service \
  --namespace lab15 \
  -f k8s/devops-info-service/values-statefulset-partition.yaml \
  --set service.nodePort=30086 \
  --set env.serviceVersion=1.0.1 \
  --wait --timeout 300s
```

Observed strategy:

```text
$ kubectl get sts devops-info-service -n lab15 -o jsonpath='{.spec.updateStrategy}{"\n"}'
{"rollingUpdate":{"maxUnavailable":1,"partition":2},"type":"RollingUpdate"}
```

Observed pod versions after the upgrade:

```text
$ kubectl get pods -n lab15 -o 'custom-columns=NAME:.metadata.name,CREATED:.metadata.creationTimestamp,SERVICE_VERSION:.spec.containers[0].env[2].value' --sort-by=.metadata.name
NAME                    CREATED                SERVICE_VERSION
devops-info-service-0   2026-05-07T12:14:50Z   1.0.0
devops-info-service-1   2026-05-07T12:13:22Z   1.0.0
devops-info-service-2   2026-05-07T12:15:37Z   1.0.1
```

With partition `2`, only ordinal `2` was updated. Ordinals `0` and `1` kept the previous pod template.

### OnDelete

Install the `OnDelete` strategy and change the service version:

```bash
helm upgrade devops-info-service k8s/devops-info-service \
  --namespace lab15 \
  -f k8s/devops-info-service/values-statefulset-ondelete.yaml \
  --set service.nodePort=30086 \
  --set env.serviceVersion=1.0.2
```

Observed strategy and pod versions immediately after the upgrade:

```text
$ kubectl get sts devops-info-service -n lab15 -o jsonpath='{.spec.updateStrategy}{"\n"}'
{"type":"OnDelete"}

$ kubectl get pods -n lab15 -o 'custom-columns=NAME:.metadata.name,CREATED:.metadata.creationTimestamp,SERVICE_VERSION:.spec.containers[0].env[2].value' --sort-by=.metadata.name
NAME                    CREATED                SERVICE_VERSION
devops-info-service-0   2026-05-07T12:14:50Z   1.0.0
devops-info-service-1   2026-05-07T12:13:22Z   1.0.0
devops-info-service-2   2026-05-07T12:15:37Z   1.0.1
```

No existing pod updated automatically. After manually deleting pod 1:

```text
$ kubectl delete pod -n lab15 devops-info-service-1
pod "devops-info-service-1" deleted

$ kubectl wait --for=condition=Ready pod/devops-info-service-1 -n lab15 --timeout=180s
pod/devops-info-service-1 condition met

$ kubectl get pods -n lab15 -o 'custom-columns=NAME:.metadata.name,CREATED:.metadata.creationTimestamp,SERVICE_VERSION:.spec.containers[0].env[2].value' --sort-by=.metadata.name
NAME                    CREATED                SERVICE_VERSION
devops-info-service-0   2026-05-07T12:14:50Z   1.0.0
devops-info-service-1   2026-05-07T12:16:27Z   1.0.2
devops-info-service-2   2026-05-07T12:15:37Z   1.0.1
```

`OnDelete` is useful when a stateful cluster needs explicit operator control over each member replacement.

## Validation

```text
$ helm lint k8s/devops-info-service
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```
