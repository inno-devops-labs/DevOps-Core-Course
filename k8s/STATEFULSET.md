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
