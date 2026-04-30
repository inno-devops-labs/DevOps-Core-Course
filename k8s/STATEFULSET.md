# Lab 15 - StatefulSets and Persistent Storage

## StatefulSet Overview

This lab converts the Python visits-counter workload to a Kubernetes
`StatefulSet`. The chart still keeps the Lab 14 `rollout.yaml` template for
reference, but the Lab 15 default is:

```yaml
statefulset:
  enabled: true
rollout:
  enabled: false
replicaCount: 3
```

A StatefulSet is the right controller when the application needs stable identity
and storage. Each replica gets a deterministic pod name, an ordinal, stable DNS,
and its own PersistentVolumeClaim. A Deployment is still better for stateless
web replicas because pods are interchangeable, update quickly, and usually do
not need per-replica storage.

Key differences:

| Feature | Deployment | StatefulSet |
| --- | --- | --- |
| Pod identity | Random ReplicaSet suffix | Stable ordinal names such as `devops-info-python-0` |
| Network identity | Service load balances interchangeable pods | Headless Service exposes direct pod DNS |
| Storage | Shared PVC or ephemeral volume | One PVC per pod from `volumeClaimTemplates` |
| Scaling order | Any order | Ordered by default, `0 -> 1 -> 2` |
| Update order | ReplicaSet rolling update | Highest ordinal down to lowest, with optional partition |

Stateful workload examples include PostgreSQL, MySQL, MongoDB, Kafka,
RabbitMQ, Elasticsearch, Cassandra, and application replicas that own local
state that must survive pod rescheduling.

## Helm Implementation

Added chart files:

- `k8s/python-app/templates/statefulset.yaml`
- `k8s/python-app/templates/headless-service.yaml`
- `k8s/python-app/values-statefulset-partition.yaml`
- `k8s/python-app/values-statefulset-ondelete.yaml`

The StatefulSet uses the headless Service name in `spec.serviceName`:

```yaml
serviceName: devops-info-python-headless
```

The headless Service sets `clusterIP: None`, so Kubernetes creates DNS records
for the individual pods:

```text
devops-info-python-0.devops-info-python-headless.lab15.svc.cluster.local
devops-info-python-1.devops-info-python-headless.lab15.svc.cluster.local
devops-info-python-2.devops-info-python-headless.lab15.svc.cluster.local
```

The app Service `devops-info-python` remains as the regular ClusterIP endpoint
for load-balanced access. The headless Service exists for direct pod identity.

Per-pod storage is created by this `volumeClaimTemplates` entry:

```yaml
volumeClaimTemplates:
  - metadata:
      name: data-volume
    spec:
      accessModes:
        - "ReadWriteOnce"
      resources:
        requests:
          storage: "100Mi"
```

Kubernetes creates claims named:

```text
data-volume-devops-info-python-0
data-volume-devops-info-python-1
data-volume-devops-info-python-2
```

## Validation

Static Helm validation:

```text
$ helm lint k8s/python-app
==> Linting k8s/python-app
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

Rendered StatefulSet checks:

```text
$ helm template devops-info-python k8s/python-app --namespace dev \
  -f k8s/python-app/values-statefulset-partition.yaml | \
  rg -n "kind: StatefulSet|updateStrategy|partition|serviceName|volumeClaimTemplates|clusterIP"
94:  clusterIP: None
130:kind: StatefulSet
141:  serviceName: devops-info-python-headless
145:  updateStrategy:
147:      partition: 2
243:  volumeClaimTemplates:
```

For runtime testing I built the current local Python application into Minikube
as `devops-info-service:lab15` because the already-published
`ellilin/devops-info-service:latest` image in this environment did not include
the Lab 12 `/visits` endpoint. The chart itself remains image-configurable:

```bash
minikube image build -t devops-info-service:lab15 app_python

helm upgrade --install devops-info-python k8s/python-app \
  --namespace lab15 --create-namespace \
  --set image.repository=devops-info-service \
  --set image.tag=lab15 \
  --set image.pullPolicy=IfNotPresent
```

## Resource Verification

After deployment:

```text
$ kubectl get po,sts,svc,pvc -n lab15 -o wide
NAME                       READY   STATUS    RESTARTS   AGE   IP            NODE
pod/devops-info-python-0   1/1     Running   0          50s   10.244.0.97   minikube
pod/devops-info-python-1   1/1     Running   0          86s   10.244.0.96   minikube
pod/devops-info-python-2   1/1     Running   0          43m   10.244.0.95   minikube

NAME                                  READY   AGE   CONTAINERS           IMAGES
statefulset.apps/devops-info-python   3/3     47m   devops-info-python   devops-info-service:lab15

NAME                                  TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)
service/devops-info-python            ClusterIP   10.97.218.51   <none>        80/TCP
service/devops-info-python-headless   ClusterIP   None           <none>        80/TCP

NAME                                                     STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS
persistentvolumeclaim/data-volume-devops-info-python-0   Bound    pvc-8c7e677b-15ea-442a-a935-e2cc03288dbc   100Mi      RWO            standard
persistentvolumeclaim/data-volume-devops-info-python-1   Bound    pvc-144f9a75-3e4e-4529-905d-f02707a84603   100Mi      RWO            standard
persistentvolumeclaim/data-volume-devops-info-python-2   Bound    pvc-a1814115-118a-4882-8e7f-6149fa035358   100Mi      RWO            standard
```

The first rollout showed the default `OrderedReady` behavior. Pod 1 was created
only after pod 0 became ready, and pod 2 only after pod 1.

```text
$ kubectl rollout status statefulset/devops-info-python -n lab15 --timeout=240s
Waiting for 2 pods to be ready...
Waiting for 1 pods to be ready...
partitioned roll out complete: 3 new pods have been updated...
```

## Network Identity

DNS resolution from pod 0:

```text
$ kubectl exec -n lab15 devops-info-python-0 -- python -c '... socket.gethostbyname(...) ...'
devops-info-python-0.devops-info-python-headless -> 10.244.0.97
devops-info-python-1.devops-info-python-headless -> 10.244.0.96
devops-info-python-2.devops-info-python-headless -> 10.244.0.95
```

The pattern is:

```text
<pod-name>.<headless-service>.<namespace>.svc.cluster.local
```

For this release:

```text
devops-info-python-1.devops-info-python-headless.lab15.svc.cluster.local
```

## Per-Pod Storage Evidence

Each pod was accessed through its own loopback interface from inside the pod.
Pod 0 received one root request, pod 1 received two, and pod 2 received three.
Each pod wrote to its own `/data/visits` file on its own PVC:

```text
$ kubectl exec -n lab15 devops-info-python-0 -- python -c '... one request ...'
{"file":"/data/visits","visits":1}
1

$ kubectl exec -n lab15 devops-info-python-1 -- python -c '... two requests ...'
{"file":"/data/visits","visits":2}
2

$ kubectl exec -n lab15 devops-info-python-2 -- python -c '... three requests ...'
{"file":"/data/visits","visits":3}
3
```

Different counts prove that the replicas are isolated and not sharing one PVC.

## Persistence Test

Before deletion, pod 1 had visits count `2`:

```text
$ kubectl exec -n lab15 devops-info-python-1 -- cat /data/visits
2

$ kubectl get pod devops-info-python-1 -n lab15 -o jsonpath='{.metadata.uid}{"\n"}{.status.podIP}{"\n"}'
fee709b7-ad6e-4d65-8722-68ad033f820b
10.244.0.96
```

After deleting only the pod, the StatefulSet recreated `devops-info-python-1`
with a new UID and IP, but it reused
`data-volume-devops-info-python-1` and preserved the counter:

```text
$ kubectl delete pod -n lab15 devops-info-python-1
pod "devops-info-python-1" deleted

$ kubectl wait --for=condition=Ready pod/devops-info-python-1 -n lab15 --timeout=180s
pod/devops-info-python-1 condition met

$ kubectl exec -n lab15 devops-info-python-1 -- cat /data/visits
2

$ kubectl exec -n lab15 devops-info-python-1 -- python -c '... GET /visits ...'
{"file":"/data/visits","visits":2}

$ kubectl get pod devops-info-python-1 -n lab15 -o jsonpath='{.metadata.uid}{"\n"}{.status.podIP}{"\n"}'
499ae416-e437-4151-859e-ba402fae67b9
10.244.0.98
```

## Bonus: Update Strategies

### Partitioned Rolling Update

`k8s/python-app/values-statefulset-partition.yaml` configures:

```yaml
statefulset:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 2
```

With three replicas, only pods with ordinal `>= 2` update automatically.

Command:

```bash
helm upgrade --install devops-info-python k8s/python-app \
  --namespace lab15 \
  -f k8s/python-app/values-statefulset-partition.yaml \
  --set image.repository=devops-info-service \
  --set image.tag=lab15 \
  --set image.pullPolicy=IfNotPresent \
  --set env.RELEASE_TRACK=partition-v2
```

Evidence:

```text
$ kubectl rollout status statefulset/devops-info-python -n lab15 --timeout=180s
Waiting for partitioned roll out to finish: 0 out of 1 new pods have been updated...
partitioned roll out complete: 1 new pods have been updated...

$ kubectl get sts devops-info-python -n lab15 -o jsonpath='{.spec.updateStrategy.type}{" partition="}{.spec.updateStrategy.rollingUpdate.partition}{"\n"}'
RollingUpdate partition=2

$ kubectl exec -n lab15 devops-info-python-0 -- printenv RELEASE_TRACK
stable
$ kubectl exec -n lab15 devops-info-python-1 -- printenv RELEASE_TRACK
stable
$ kubectl exec -n lab15 devops-info-python-2 -- printenv RELEASE_TRACK
partition-v2

$ kubectl get pods -n lab15 -l app.kubernetes.io/instance=devops-info-python \
  -o 'custom-columns=NAME:.metadata.name,REVISION:.metadata.labels.controller-revision-hash,IP:.status.podIP' \
  --sort-by=.metadata.name
NAME                   REVISION                        IP
devops-info-python-0   devops-info-python-854b989f69   10.244.0.97
devops-info-python-1   devops-info-python-854b989f69   10.244.0.98
devops-info-python-2   devops-info-python-867474d67    10.244.0.99
```

Use cases: staged database upgrades, shard-by-shard validation, and controlled
rollouts where lower ordinals are leaders or primary replicas that should be
updated last.

### OnDelete

`k8s/python-app/values-statefulset-ondelete.yaml` configures:

```yaml
statefulset:
  updateStrategy:
    type: OnDelete
    rollingUpdate: null
```

`rollingUpdate: null` is required because Helm merges values maps; without it,
the base `rollingUpdate.partition` would still render and Kubernetes rejects
`rollingUpdate` settings when `type: OnDelete`.

Command:

```bash
helm upgrade --install devops-info-python k8s/python-app \
  --namespace lab15 \
  -f k8s/python-app/values-statefulset-ondelete.yaml \
  --set image.repository=devops-info-service \
  --set image.tag=lab15 \
  --set image.pullPolicy=IfNotPresent \
  --set env.RELEASE_TRACK=ondelete-v3
```

After the upgrade, no existing pod changed:

```text
$ kubectl get sts devops-info-python -n lab15 -o jsonpath='{.spec.updateStrategy.type}{"\n"}'
OnDelete

$ kubectl exec -n lab15 devops-info-python-0 -- printenv RELEASE_TRACK
stable
$ kubectl exec -n lab15 devops-info-python-1 -- printenv RELEASE_TRACK
stable
$ kubectl exec -n lab15 devops-info-python-2 -- printenv RELEASE_TRACK
partition-v2
```

After manually deleting pod 0, only that pod recreated from the new template:

```text
$ kubectl delete pod -n lab15 devops-info-python-0
pod "devops-info-python-0" deleted

$ kubectl wait --for=condition=Ready pod/devops-info-python-0 -n lab15 --timeout=180s
pod/devops-info-python-0 condition met

$ kubectl exec -n lab15 devops-info-python-0 -- printenv RELEASE_TRACK
ondelete-v3
$ kubectl exec -n lab15 devops-info-python-1 -- printenv RELEASE_TRACK
stable
$ kubectl exec -n lab15 devops-info-python-2 -- printenv RELEASE_TRACK
partition-v2

$ kubectl get pods -n lab15 -l app.kubernetes.io/instance=devops-info-python \
  -o 'custom-columns=NAME:.metadata.name,REVISION:.metadata.labels.controller-revision-hash,IP:.status.podIP' \
  --sort-by=.metadata.name
NAME                   REVISION                        IP
devops-info-python-0   devops-info-python-b46fb4ccb    10.244.0.100
devops-info-python-1   devops-info-python-854b989f69   10.244.0.98
devops-info-python-2   devops-info-python-867474d67    10.244.0.99
```

Use cases: maintenance windows, operator-driven database upgrades, manual
leader/follower replacement, and workloads that need explicit application-level
coordination before each replica restarts.
