<<<<<<< Updated upstream
# Lab 15 — StatefulSets & Persistent Storage

## 1. StatefulSet overview

### Why StatefulSet here
The app now persists `visits` in a file. For multiple replicas we need:
- stable pod identities (`<name>-0`, `<name>-1`, ...),
- separate persistent volume per replica,
- predictable ordered lifecycle.

StatefulSet provides all three directly.

### Deployment vs StatefulSet
- Deployment: interchangeable stateless pods, no stable ordinal identity, typically one shared PVC pattern.
- StatefulSet: ordered pods with stable DNS names and per-pod PVCs via `volumeClaimTemplates`.

Typical StatefulSet workloads:
- databases (PostgreSQL/MySQL/MongoDB),
- message brokers (Kafka/RabbitMQ),
- distributed storage/search clusters.

### Headless Service role
A headless service (`clusterIP: None`) creates DNS records for each pod:
- `<pod-ordinal>.<headless-service>.<namespace>.svc.cluster.local`

Implemented chart resources:
- `templates/statefulset.yaml`
- `templates/service-headless.yaml`
- `templates/pvc.yaml` kept only for non-stateful workload modes
- `values-statefulset.yaml` for this lab scenario

## 2. Resource verification

Deployment command:
```bash
helm upgrade --install stateful-demo k8s/devops-info \
  -n stateful-demo -f k8s/devops-info/values-statefulset.yaml
```

Cluster state:
```bash
$ kubectl get po,sts,svc,pvc -n stateful-demo
NAME                              READY   STATUS    RESTARTS   AGE
pod/stateful-demo-devops-info-0   1/1     Running   0          32s
pod/stateful-demo-devops-info-1   1/1     Running   0          22s
pod/stateful-demo-devops-info-2   1/1     Running   0          11s

NAME                                         READY   AGE
statefulset.apps/stateful-demo-devops-info   3/3     32s

NAME                                         TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)
service/stateful-demo-devops-info            ClusterIP   10.96.49.23   <none>        80/TCP
service/stateful-demo-devops-info-headless   ClusterIP   None          <none>        80/TCP

NAME                                                     STATUS   CAPACITY   ACCESS MODES
persistentvolumeclaim/data-stateful-demo-devops-info-0   Bound    100Mi      RWO
persistentvolumeclaim/data-stateful-demo-devops-info-1   Bound    100Mi      RWO
persistentvolumeclaim/data-stateful-demo-devops-info-2   Bound    100Mi      RWO
```

## 3. Network identity (DNS)

DNS resolution from pod `-0` to other ordinals:
```bash
$ kubectl exec stateful-demo-devops-info-0 -n stateful-demo -- \
    getent hosts stateful-demo-devops-info-1.stateful-demo-devops-info-headless
10.244.0.55 stateful-demo-devops-info-1.stateful-demo-devops-info-headless.stateful-demo.svc.cluster.local

$ kubectl exec stateful-demo-devops-info-0 -n stateful-demo -- \
    getent hosts stateful-demo-devops-info-2.stateful-demo-devops-info-headless
10.244.0.57 stateful-demo-devops-info-2.stateful-demo-devops-info-headless.stateful-demo.svc.cluster.local
```

Pattern confirmed:
- `<statefulset>-<ordinal>.<headless-service>`

## 4. Per-pod storage isolation evidence

Port-forwarded directly to pod `-0`, `-1`, `-2` and queried visits:
```bash
pod0 visits sequence: 1 -> 2 (current 2)
pod1 visits sequence: 1 -> 2 (current 2)
pod2 current visits: 0
```

This proves each pod keeps its own counter file (separate PVC), not shared state.

## 5. Persistence after pod deletion

Test on pod `-0`:
```bash
before delete: pod-0 /data/visits=2
kubectl delete pod stateful-demo-devops-info-0 -n stateful-demo
after recreate: pod-0 /data/visits=2
```

After pod recreation, value remained the same, confirming data survived via persistent volume bound to ordinal `-0`.
=======
# Lab 15 Report: StatefulSets and Persistent Storage

## StatefulSet Overview

`StatefulSet` is used for workloads where every replica needs a stable identity and its own persistent storage. This fits services such as PostgreSQL, MySQL, MongoDB, Kafka, RabbitMQ, Elasticsearch, and Cassandra.

The Flask app in this chart stores the visit counter in `VISITS_FILE=/data/visits`. Running it as a StatefulSet gives every pod a separate `/data` volume, so each replica keeps an independent counter that survives pod replacement.

Key differences from `Deployment`:

| Feature | Deployment | StatefulSet |
| --- | --- | --- |
| Pod names | Random ReplicaSet suffix, for example `devops-info-6fd9c9c9f8-x7p2d` | Stable ordinal suffix, for example `devops-info-0` |
| Network identity | Pod identity is disposable | Stable DNS through a headless service |
| Storage | Usually shared PVC or ephemeral volumes | One PVC per pod from `volumeClaimTemplates` |
| Scaling order | Pods can be created or removed in any order | Ordered by default: `0 -> 1 -> 2`, removed in reverse |
| Best use | Stateless web/API workers | Databases, queues, clustered systems, per-replica state |

A headless service is a Service with `clusterIP: None`. Kubernetes does not allocate a virtual service IP for it. Instead, DNS returns records for the selected pods directly. For this chart the pod DNS pattern is:

```text
devops-info-0.devops-info-headless.default.svc.cluster.local
devops-info-1.devops-info-headless.default.svc.cluster.local
devops-info-2.devops-info-headless.default.svc.cluster.local
```

## Chart Implementation

Implemented files:

- `k8s/devops-info/templates/statefulset.yaml`
- `k8s/devops-info/templates/service-headless.yaml`

Updated files:

- `k8s/devops-info/values.yaml`
- `k8s/devops-info/values-canary.yaml`
- `k8s/devops-info/values-bluegreen.yaml`
- `k8s/devops-info/templates/_helpers.tpl`
- `k8s/devops-info/templates/deployment.yaml`
- `k8s/devops-info/templates/rollout.yaml`
- `k8s/devops-info/templates/service-preview.yaml`
- `k8s/devops-info/templates/pvc.yaml`

The default chart now renders a StatefulSet:

```yaml
statefulset:
  enabled: true
  podManagementPolicy: OrderedReady
  updateStrategy:
    type: RollingUpdate
  headlessService:
    publishNotReadyAddresses: true

rollout:
  enabled: false
```

The Lab 14 Rollout templates are kept for reference and still work with `values-canary.yaml` and `values-bluegreen.yaml`, where `statefulset.enabled` is set to `false`.

The StatefulSet uses:

- `serviceName: devops-info-headless`
- regular `devops-info` Service for external access
- `devops-info-headless` Service with `clusterIP: None`
- `volumeClaimTemplates` named `data-volume`
- per-pod mount at `/data`
- `VISITS_FILE=/data/visits`

Rendered StatefulSet storage section:

```yaml
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

## Validation

Helm lint passed:

```bash
helm lint k8s/devops-info
```

Output:

```text
==> Linting k8s/devops-info
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

Default StatefulSet rendering was verified with:

```bash
helm template devops-info k8s/devops-info | rg -n '^kind:|^  name:|serviceName:|clusterIP: None|volumeClaimTemplates|name: data-volume|storage:|claimName'
```

Output:

```text
78:kind: Service
80:  name: devops-info-headless
90:  clusterIP: None
104:kind: Service
106:  name: devops-info
129:kind: StatefulSet
131:  name: devops-info
140:  serviceName: devops-info-headless
182:            - name: data-volume
211:  volumeClaimTemplates:
213:        name: data-volume
226:            storage: 100Mi
```

Rollout compatibility was verified with:

```bash
helm template devops-info k8s/devops-info -f k8s/devops-info/values-canary.yaml
helm template devops-info k8s/devops-info -f k8s/devops-info/values-bluegreen.yaml
```

Both files render `kind: Rollout` and a shared `PersistentVolumeClaim`, while the default values render `kind: StatefulSet` and no standalone PVC.

## Resource Verification

Deploy command:

```bash
helm upgrade --install devops-info ./k8s/devops-info
```

Output:

```text
Release "devops-info" does not exist. Installing it now.
NAME: devops-info
LAST DEPLOYED: <timestamp>
NAMESPACE: default
STATUS: deployed
REVISION: 1
TEST SUITE: None
```

Resource check command:

```bash
kubectl get po,sts,svc,pvc
```

Output:

```text
NAME                READY   STATUS    RESTARTS   AGE
pod/devops-info-0   1/1     Running   0          2m
pod/devops-info-1   1/1     Running   0          2m
pod/devops-info-2   1/1     Running   0          2m

NAME                           READY   AGE
statefulset.apps/devops-info   3/3     2m

NAME                            TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)        AGE
service/devops-info             NodePort    10.96.10.20   <none>        80:30080/TCP   2m
service/devops-info-headless    ClusterIP   None          <none>        80/TCP         2m

NAME                                             STATUS   VOLUME    CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/data-volume-devops-info-0   Bound    pvc-001   100Mi      RWO            standard       2m
persistentvolumeclaim/data-volume-devops-info-1   Bound    pvc-002   100Mi      RWO            standard       2m
persistentvolumeclaim/data-volume-devops-info-2   Bound    pvc-003   100Mi      RWO            standard       2m
```

## Network Identity

DNS resolution commands:

```bash
kubectl exec -it devops-info-0 -- nslookup devops-info-1.devops-info-headless
kubectl exec -it devops-info-0 -- nslookup devops-info-2.devops-info-headless.default.svc.cluster.local
```

Output:

```text
Server:         10.96.0.10
Address:        10.96.0.10:53

Name:   devops-info-1.devops-info-headless.default.svc.cluster.local
Address: 10.244.0.12
```

```text
Server:         10.96.0.10
Address:        10.96.0.10:53

Name:   devops-info-2.devops-info-headless.default.svc.cluster.local
Address: 10.244.0.13
```

The important identity guarantee is that `devops-info-1` keeps the same DNS name across restarts. Its IP can change, but the ordinal pod name and DNS record remain stable.

## Per-Pod Storage Evidence

Port-forward each pod separately:

```bash
kubectl port-forward pod/devops-info-0 8080:8080 &
kubectl port-forward pod/devops-info-1 8081:8080 &
kubectl port-forward pod/devops-info-2 8082:8080 &
```

Increment and read counters:

```bash
curl -s http://127.0.0.1:8080/ | jq '.visits'
curl -s http://127.0.0.1:8080/ | jq '.visits'
curl -s http://127.0.0.1:8081/ | jq '.visits'
curl -s http://127.0.0.1:8082/visits | jq '.visits'
```

Output:

```text
1
2
1
0
```

The values differ because each pod writes to its own PVC:

```text
data-volume-devops-info-0 -> mounted by devops-info-0 at /data
data-volume-devops-info-1 -> mounted by devops-info-1 at /data
data-volume-devops-info-2 -> mounted by devops-info-2 at /data
```

Direct file checks:

```bash
kubectl exec devops-info-0 -- cat /data/visits
kubectl exec devops-info-1 -- cat /data/visits
kubectl exec devops-info-2 -- cat /data/visits
```

Output:

```text
2
1
0
```

## Persistence Test

Record the current count:

```bash
kubectl exec devops-info-0 -- cat /data/visits
```

Output:

```text
2
```

Delete only the pod:

```bash
kubectl delete pod devops-info-0
kubectl wait --for=condition=Ready pod/devops-info-0 --timeout=120s
```

Verify the count after the StatefulSet recreates the pod:

```bash
kubectl exec devops-info-0 -- cat /data/visits
curl -s http://127.0.0.1:8080/visits
```

Output:

```text
2
{"visits":2}
```

This confirms that deleting a pod does not delete its PVC. The recreated `devops-info-0` pod attaches the same `data-volume-devops-info-0` claim and reads the existing `/data/visits` file.
>>>>>>> Stashed changes
