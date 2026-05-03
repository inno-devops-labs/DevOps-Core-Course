# StatefulSets & Persistent Storage (Lab 15)

The Helm chart in [`python-app/`](python-app/) now supports a StatefulSet
deployment with per-pod PVCs and a headless Service alongside the existing
Deployment / Argo Rollout modes (chosen via `statefulset.enabled`,
`rollout.enabled`).

Deploy the StatefulSet variant:

```bash
kubectl create namespace lab15
helm install python-sts k8s/python-app \
  -f k8s/python-app/values-statefulset.yaml \
  -n lab15
```

---

## 1. StatefulSet Overview

### Guarantees

- **Stable, unique network identity** — pods get ordinal names (`<sts>-0`,
  `<sts>-1`, …) and per-pod DNS records under the headless Service
  (`<pod>.<headless-svc>.<ns>.svc.cluster.local`).
- **Stable persistent storage** — each pod gets its own PVC produced from
  `volumeClaimTemplates`. The PVC survives pod deletion and is re-attached to
  the replacement pod with the same ordinal.
- **Ordered deployment / scaling / termination** — under the default
  `OrderedReady` policy pods are created/updated `0 → 1 → 2` and torn down in
  reverse, each waiting for the previous to be Ready.

### Deployment vs StatefulSet

| Feature      | Deployment                | StatefulSet                                  |
|--------------|---------------------------|-----------------------------------------------|
| Pod names    | random suffix             | ordinal: `pod-0`, `pod-1`, `pod-2`            |
| Identity     | interchangeable           | sticky per ordinal                            |
| Storage      | one shared PVC (or none)  | one PVC per pod (via `volumeClaimTemplates`)  |
| Scaling      | parallel, any order       | ordered (default) or parallel (`Parallel`)    |
| Network DNS  | only via Service VIP      | per-pod DNS via headless Service              |

Use a **Deployment** for stateless, interchangeable replicas (web frontends,
stateless APIs). Use a **StatefulSet** for workloads that need stable identity
and per-pod persistent storage: databases (PostgreSQL, MySQL, MongoDB),
message brokers (Kafka, RabbitMQ), distributed stores (Cassandra,
Elasticsearch, etcd, Zookeeper).

### Headless Service

A Service with `clusterIP: None` does not get a virtual IP or kube-proxy
load-balancing. Instead, CoreDNS returns:

- one A record per ready pod for the service name itself, and
- one A record per pod at `<pod-name>.<service-name>.<ns>.svc.cluster.local`
  (because the StatefulSet sets each pod's `subdomain` to `serviceName`).

This is what gives StatefulSet pods individually addressable, stable DNS
names — which is how clients of stateful systems target a specific replica
(primary vs replica, shard owner, etc.).

---

## 2. Resource Verification

`kubectl get po,sts,svc,pvc -n lab15 -o wide`:

```
NAME                          READY   STATUS    RESTARTS   AGE     IP            NODE
pod/python-sts-python-app-0   1/1     Running   0          23s     10.244.1.82   minikube
pod/python-sts-python-app-1   1/1     Running   0          3m19s   10.244.1.78   minikube
pod/python-sts-python-app-2   1/1     Running   0          3m14s   10.244.1.79   minikube

NAME                                     READY   AGE     CONTAINERS   IMAGES
statefulset.apps/python-sts-python-app   3/3     3m27s   python-app   karishka1222/devops-python-app:latest

NAME                                     TYPE        CLUSTER-IP     PORT(S)    SELECTOR
service/python-sts-python-app            ClusterIP   10.109.65.74   80/TCP     app.kubernetes.io/instance=python-sts,app.kubernetes.io/name=python-app
service/python-sts-python-app-headless   ClusterIP   None           5000/TCP   app.kubernetes.io/instance=python-sts,app.kubernetes.io/name=python-app

NAME                                                 STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS
persistentvolumeclaim/data-python-sts-python-app-0   Bound    pvc-6baa91f5-6d02-4299-b9cb-49a4a46e71ca   100Mi      RWO            standard
persistentvolumeclaim/data-python-sts-python-app-1   Bound    pvc-3c04f636-7f22-471d-920a-f94d74ba19d9   100Mi      RWO            standard
persistentvolumeclaim/data-python-sts-python-app-2   Bound    pvc-0315049b-8d67-40f8-94cb-e354c704cf52   100Mi      RWO            standard
```

Notes:

- The headless service has `CLUSTER-IP=None` (as required).
- Each pod owns its own PVC (`data-<sts>-0|1|2`), produced from the
  `volumeClaimTemplates` on the StatefulSet.

Pod -> PVC binding:

```
POD                       VOLUME-CLAIM
python-sts-python-app-0   data-python-sts-python-app-0
python-sts-python-app-1   data-python-sts-python-app-1
python-sts-python-app-2   data-python-sts-python-app-2
```

---

## 3. Network Identity (DNS)

Run a debug pod in the namespace and resolve pod-level DNS:

```bash
kubectl run dns-test --rm -it --restart=Never --image=busybox:1.36 -n lab15 -- sh
```

`/etc/resolv.conf` inside the pod:

```
nameserver 10.96.0.10
search lab15.svc.cluster.local svc.cluster.local cluster.local
options ndots:5
```

Headless service returns A records of all ready pods:

```
$ nslookup python-sts-python-app-headless.lab15.svc.cluster.local
Name:	python-sts-python-app-headless.lab15.svc.cluster.local
Address: 10.244.1.76
Name:	python-sts-python-app-headless.lab15.svc.cluster.local
Address: 10.244.1.79
Name:	python-sts-python-app-headless.lab15.svc.cluster.local
Address: 10.244.1.78
```

Per-pod stable DNS names:

```
$ nslookup python-sts-python-app-0.python-sts-python-app-headless.lab15.svc.cluster.local
Name:	python-sts-python-app-0.python-sts-python-app-headless.lab15.svc.cluster.local
Address: 10.244.1.76

$ nslookup python-sts-python-app-1.python-sts-python-app-headless.lab15.svc.cluster.local
Name:	python-sts-python-app-1.python-sts-python-app-headless.lab15.svc.cluster.local
Address: 10.244.1.78

$ nslookup python-sts-python-app-2.python-sts-python-app-headless.lab15.svc.cluster.local
Name:	python-sts-python-app-2.python-sts-python-app-headless.lab15.svc.cluster.local
Address: 10.244.1.79
```

DNS pattern: `<pod-ordinal>.<headless-service>.<namespace>.svc.cluster.local`.

---

## 4. Per-Pod Storage Evidence

The app's `VISITS_FILE` env var points to `/data/visits`, which is mounted
from each pod's own PVC. Hitting each pod through a separate port-forward:

```bash
kubectl port-forward -n lab15 pod/python-sts-python-app-0 18080:5000 &
kubectl port-forward -n lab15 pod/python-sts-python-app-1 18081:5000 &
kubectl port-forward -n lab15 pod/python-sts-python-app-2 18082:5000 &
```

Hit pod-0 five times, pod-1 three times, pod-2 once, then read `/visits`
on each:

```
$ for i in 1 2 3 4 5; do curl -s http://localhost:18080/ \
    | jq -r '"hostname=\(.system.hostname) visits=\(.visits)"'; done
hostname=python-sts-python-app-0 visits=1
hostname=python-sts-python-app-0 visits=2
hostname=python-sts-python-app-0 visits=3
hostname=python-sts-python-app-0 visits=4
hostname=python-sts-python-app-0 visits=5

$ for i in 1 2 3; do curl -s http://localhost:18081/ \
    | jq -r '"hostname=\(.system.hostname) visits=\(.visits)"'; done
hostname=python-sts-python-app-1 visits=1
hostname=python-sts-python-app-1 visits=2
hostname=python-sts-python-app-1 visits=3

$ curl -s http://localhost:18082/ \
    | jq -r '"hostname=\(.system.hostname) visits=\(.visits)"'
hostname=python-sts-python-app-2 visits=1

$ curl -s http://localhost:18080/visits
{"visits":5}
$ curl -s http://localhost:18081/visits
{"visits":3}
$ curl -s http://localhost:18082/visits
{"visits":1}
```

The counters diverge — proving each pod writes to its own PVC (no shared
volume, no cross-pod state leakage).

---

## 5. Persistence Test

```bash
$ kubectl exec -n lab15 python-sts-python-app-0 -- cat /data/visits
5
$ kubectl get pvc -n lab15 data-python-sts-python-app-0 -o jsonpath='{.spec.volumeName}'
pvc-6baa91f5-6d02-4299-b9cb-49a4a46e71ca

$ kubectl delete pod -n lab15 python-sts-python-app-0
pod "python-sts-python-app-0" deleted

$ kubectl wait --for=condition=ready pod/python-sts-python-app-0 -n lab15
pod/python-sts-python-app-0 condition met

$ kubectl get pod -n lab15 python-sts-python-app-0 -o wide
NAME                      READY   STATUS    RESTARTS   AGE   IP            NODE
python-sts-python-app-0   1/1     Running   0          10s   10.244.1.82   minikube

$ kubectl get pvc -n lab15 data-python-sts-python-app-0 -o jsonpath='{.spec.volumeName}'
pvc-6baa91f5-6d02-4299-b9cb-49a4a46e71ca   # same volume

$ kubectl exec -n lab15 python-sts-python-app-0 -- cat /data/visits
5                                          # counter preserved
```

Pod `-0` came back with a new pod IP but kept the same name, the same PVC
(`pvc-6baa91f5-…`), and the same visit count. Other pods were untouched
(`pod-1=3`, `pod-2=1`).

---

## Bonus — Update Strategies

### Partitioned RollingUpdate

Trigger: bump `resources.limits.memory` `256Mi → 300Mi` with
`statefulset.updateStrategy.rollingUpdate.partition=2`.

```bash
helm upgrade python-sts k8s/python-app \
  -f k8s/python-app/values-statefulset.yaml -n lab15 \
  --set statefulset.updateStrategy.rollingUpdate.partition=2 \
  --set resources.limits.memory=300Mi
```

Effective strategy:

```json
{
  "rollingUpdate": { "maxUnavailable": 1, "partition": 2 },
  "type": "RollingUpdate"
}
```

Result — only the pod with ordinal `>= 2` was rolled:

```
$ kubectl get pods -n lab15 \
    -o custom-columns='POD:.metadata.name,MEM-LIMIT:.spec.containers[0].resources.limits.memory'
POD                       MEM-LIMIT
python-sts-python-app-0   256Mi
python-sts-python-app-1   256Mi
python-sts-python-app-2   300Mi
```

Pods 0 and 1 still run the old template (256Mi); only pod-2 picked up the
new 300Mi limit.

Use case: canary a new version on the highest ordinals only (e.g. one shard
out of N), validate, then lower `partition` to roll out further. Setting
`partition=0` rolls all replicas.

### OnDelete

Trigger: switch the strategy and bump memory `300Mi → 350Mi`.

```bash
helm upgrade python-sts k8s/python-app \
  -f k8s/python-app/values-statefulset.yaml -n lab15 \
  --set statefulset.updateStrategy.type=OnDelete \
  --set statefulset.updateStrategy.rollingUpdate=null \
  --set resources.limits.memory=350Mi
```

The StatefulSet's pod template now declares 350Mi, but no pod is recreated
automatically:

```
$ kubectl get sts -n lab15 python-sts-python-app -o jsonpath='{.spec.updateStrategy}'
{"type":"OnDelete"}

$ kubectl get sts -n lab15 python-sts-python-app \
    -o jsonpath='{.spec.template.spec.containers[0].resources.limits.memory}'
350Mi

$ kubectl get pods -n lab15 \
    -o custom-columns='POD:.metadata.name,MEM-LIMIT:.spec.containers[0].resources.limits.memory'
POD                       MEM-LIMIT
python-sts-python-app-0   256Mi
python-sts-python-app-1   256Mi
python-sts-python-app-2   300Mi
```

All three pods still run their previous templates — Kubernetes did not
restart anything on its own. Deleting `pod-2` manually lets the StatefulSet
recreate it with the new template:

```
$ kubectl delete pod -n lab15 python-sts-python-app-2
pod "python-sts-python-app-2" deleted

$ kubectl get pods -n lab15 \
    -o custom-columns='POD:.metadata.name,MEM-LIMIT:.spec.containers[0].resources.limits.memory'
POD                       MEM-LIMIT
python-sts-python-app-0   256Mi
python-sts-python-app-1   256Mi
python-sts-python-app-2   350Mi

$ kubectl exec -n lab15 python-sts-python-app-2 -- cat /data/visits
1
```

Pod-2 came back on the new template (350Mi) and reused its PVC, so the
visit counter (`1`) was preserved.

Use cases for OnDelete:

- The operator (human or controller) decides when to roll a pod — useful for
  databases that need a manual leader-handoff before restart.
- Custom orchestrators (Kafka/Cassandra operators) that drain or rebalance
  before recreating a replica.
- Maintenance windows where Kubernetes must not initiate restarts on its own.

---

## Cleanup

```bash
helm uninstall python-sts -n lab15
kubectl delete pvc -l app.kubernetes.io/instance=python-sts -n lab15  # PVCs are kept by default
kubectl delete namespace lab15
```
