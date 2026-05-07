# StatefulSet Implementation

## 1. StatefulSet Overview

### Why StatefulSet?

StatefulSets are used for stateful applications that require:
- **Stable, unique network identifiers** — Each pod gets a predictable DNS name (e.g., `my-python-app-0`, `my-python-app-1`)
- **Stable, persistent storage** — Each pod gets its own PVC that persists across pod rescheduling
- **Ordered, graceful deployment and scaling** — Pods are created/updated/deleted in order (0→1→2)

### StatefulSet vs Deployment

| Feature | Deployment | StatefulSet |
|---------|------------|-------------|
| Pod Names | Random suffix (e.g., `app-7b9f6d8`) | Ordered index (e.g., `app-0`, `app-1`) |
| Storage | Shared PVC | Per-pod PVC via volumeClaimTemplates |
| Scaling | Any order, parallel | Ordered (0→1→2) |
| Network ID | Random, changes on reschedule | Stable DNS name per pod |
| Pod Replacement | New pod with new identity | Same pod identity is recreated |
| Update Strategy | RollingUpdate, Recreate | RollingUpdate (ordered), OnDelete |

### When to Use Each

- **Deployment**: Stateless web servers, APIs, microservices where any pod can handle any request
- **StatefulSet**: Databases (MySQL, PostgreSQL, MongoDB), message queues (Kafka, RabbitMQ), distributed systems (Elasticsearch, Cassandra) — any workload needing stable identity or persistent per-pod data

## 2. Resource Verification

Deployed with:
```bash
helm install my-python-app ./my-python-app -n default
```

```bash
$ kubectl get po,sts,svc,pvc
NAME                     READY   STATUS    RESTARTS   AGE
my-python-app-0           1/1     Running   0          23m
my-python-app-1           1/1     Running   0          22m
my-python-app-2           1/1     Running   0          22m

NAME                                READY   AGE
statefulset.apps/my-python-app      3/3     23m

NAME                             TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)   AGE
service/my-python-app             ClusterIP   10.96.142.18     <none>        80/TCP    23m
service/my-python-app-headless    ClusterIP   None             <none>        80/TCP    23m

NAME                                            STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/data-my-python-app-0       Bound    pvc-03abb321-a062-4d7f-816c-623d95947d1d   1Gi        RWO            standard       23m
persistentvolumeclaim/data-my-python-app-1       Bound    pvc-403c52d1-42fc-4e4e-a9a0-c1f1d340cbac   1Gi        RWO            standard       22m
persistentvolumeclaim/data-my-python-app-2       Bound    pvc-2f041b81-4bc7-429a-9400-18d6c7a8f70b   1Gi        RWO            standard       22m
```


## 3. Network Identity

### Headless Service

The headless service (`clusterIP: None`) creates DNS records for each pod:

- `my-python-app-0.my-python-app-headless.default.svc.cluster.local`
- `my-python-app-1.my-python-app-headless.default.svc.cluster.local`
- `my-python-app-2.my-python-app-headless.default.svc.cluster.local`

### DNS Resolution Test

```bash
$ kubectl exec -it my-python-app-0 -- /bin/sh

Server:    10.96.0.10
Address 1: 10.96.0.10 kube-dns.kube-system.svc.cluster.local

Name:      my-python-app-1.my-python-app-headless
Address 1: 10.244.1.5 my-python-app-1.my-python-app-headless.default.svc.cluster.local

/
Server:    10.96.0.10
Address 1: 10.96.0.10 kube-dns.kube-system.svc.cluster.local

Name:      my-python-app-2.my-python-app-headless
Address 1: 10.244.2.3 my-python-app-2.my-python-app-headless.default.svc.cluster.local
```

Each pod has a stable DNS name that resolves directly to its IP, enabling direct pod-to-pod communication.

## 4. Per-Pod Storage Evidence

Each pod maintains its own independent visit counter stored in its dedicated PVC:

```bash
$ kubectl port-forward pod/my-python-app-0 8080:8000 &
$ kubectl port-forward pod/my-python-app-1 8081:8000 &
$ kubectl port-forward pod/my-python-app-2 8082:8000 &

$ curl localhost:8080/visits
{"visits": 5}

$ curl localhost:8081/visits
{"visits": 3}

$ curl localhost:8082/visits
{"visits": 7}
```

The different visit counts demonstrate that each pod has its own isolated storage — requests to pod-0 don't affect pod-1 or pod-2's data.

## 5. Persistence Test

Visit counts survive pod deletion because PVCs are not deleted when a StatefulSet pod is removed:

```bash
$ kubectl exec my-python-app-0 -- cat /data/visits
5

$ kubectl delete pod my-python-app-0
pod "my-python-app-0" deleted

# Wait for pod to be recreated by StatefulSet controller
$ kubectl get pod my-python-app-0
NAME               READY   STATUS    RESTARTS   AGE
my-python-app-0     1/1     Running   0          2m

$ curl localhost:8080/visits
{"visits": 5}
```

The visit count (5) is preserved after pod deletion and recreation, confirming that persistent storage is not tied to the pod lifecycle but to the StatefulSet's volumeClaimTemplates.
