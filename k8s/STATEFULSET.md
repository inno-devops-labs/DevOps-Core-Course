# StatefulSet Lab

## 1) StatefulSet Overview

StatefulSet is used when workload instances need stable identity and dedicated storage.

Deployment vs StatefulSet:

| Feature | Deployment | StatefulSet |
|---|---|---|
| Pod names | random suffix | ordered (`-0`, `-1`, ...) |
| Storage | shared/static PVC usage | per-pod PVC via `volumeClaimTemplates` |
| Startup/scale order | not guaranteed | ordered by ordinal |
| Network identity | dynamic | stable DNS per pod |

Use Deployment for stateless apps.  
Use StatefulSet for databases, queues, and any workload with pod-specific state.

## 2) Resource Verification

```bash
kubectl get po,sts,svc,pvc -n statefulset-lab
```

```text
NAME                                 READY   STATUS    RESTARTS   AGE
pod/pythonapp-stateful-pythonapp-0   1/1     Running   0          16s
pod/pythonapp-stateful-pythonapp-1   1/1     Running   0          79s

NAME                                            READY   AGE
statefulset.apps/pythonapp-stateful-pythonapp   2/2     88s

NAME                                            TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
service/pythonapp-stateful-pythonapp            ClusterIP   10.111.50.149   <none>        80/TCP    88s
service/pythonapp-stateful-pythonapp-headless   ClusterIP   None            <none>        80/TCP    88s

NAME                                                               STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/data-volume-pythonapp-stateful-pythonapp-0   Bound    pvc-783d1bc5-bb6a-4487-a31b-6911b371c856   100Mi      RWO            standard       88s
persistentvolumeclaim/data-volume-pythonapp-stateful-pythonapp-1   Bound    pvc-e0537fc5-d577-4a1a-92f3-31a469f37634   100Mi      RWO            standard       79s
```

## 3) Network Identity

Headless service (`clusterIP: None`) provides stable per-pod DNS:

Pattern:
- `<statefulset-pod>.<headless-service>.<namespace>.svc.cluster.local`

DNS resolution test:

```bash
kubectl exec -n statefulset-lab pythonapp-stateful-pythonapp-0 -- python -c "import socket; print(socket.gethostbyname('pythonapp-stateful-pythonapp-1.pythonapp-stateful-pythonapp-headless.statefulset-lab.svc.cluster.local'))"
```

```text
10.244.0.239
```

## 4) Per-Pod Storage Evidence

Traffic sent to each pod directly:

```bash
kubectl port-forward pod/pythonapp-stateful-pythonapp-0 -n statefulset-lab 18090:5000
kubectl port-forward pod/pythonapp-stateful-pythonapp-1 -n statefulset-lab 18091:5000
```

Then:

```bash
Invoke-WebRequest http://localhost:18090/
Invoke-WebRequest http://localhost:18090/
Invoke-WebRequest http://localhost:18091/
Invoke-WebRequest http://localhost:18090/visits
Invoke-WebRequest http://localhost:18091/visits
```

```text
{"visits":2}
{"visits":1}
```

Different counters confirm isolated per-pod storage.

## 5) Persistence Test

Before pod deletion:

```bash
kubectl exec -n statefulset-lab pythonapp-stateful-pythonapp-0 -- cat /data/visits
```

```text
2
```

Delete pod and wait for recreation:

```bash
kubectl delete pod -n statefulset-lab pythonapp-stateful-pythonapp-0
kubectl wait --for=condition=ready pod/pythonapp-stateful-pythonapp-0 -n statefulset-lab --timeout=120s
kubectl exec -n statefulset-lab pythonapp-stateful-pythonapp-0 -- cat /data/visits
```

```text
2
```

Visit data persisted after pod restart, confirming PVC reattachment for the same ordinal pod.

