# Lab 15

## 1. StatefulSet Overview

Stateful applications (databases, message queues, etc.) need stable network identities and per‑pod persistent storage.  
A Deployment gives random pod names and shared storage, while a StatefulSet provides:

- Ordinal, predictable pod names (`<name>-0`, `<name>-1`, …)
- Ordered startup and shutdown
- Unique PersistentVolumeClaims (PVCs) per pod via `volumeClaimTemplates`
- Stable DNS names via a Headless Service

**Key differences from Deployment:**

| Feature        | Deployment                         | StatefulSet                         |
|----------------|------------------------------------|-------------------------------------|
| Pod names      | Random suffix                      | Ordinal indices (`‑0`, `‑1`)        |
| Storage        | Manual PVC or shared volume        | Automatic per‑pod PVCs              |
| Scaling order  | Any order                          | Sequential (0→1→2, reverse on down) |
| Network ID     | Random cluster IP only             | Stable DNS record per pod           |
| Use case       | Stateless apps (web servers)       | Stateful apps (Kafka, MySQL, etc.)  |

---

## 2. Resource Verification

After deploying the StatefulSet, the following resources exist in the `dev` namespace:

```bash
$ kubectl get po,sts,svc,pvc -n dev
NAME                              READY   STATUS    RESTARTS   AGE
pod/python-app-dev-simple-app-0   1/1     Running   0          4m32s
pod/python-app-dev-simple-app-1   1/1     Running   0          10m

NAME                                         READY   AGE
statefulset.apps/python-app-dev-simple-app   2/2     3d23h

NAME                                         TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/python-app-dev-simple-app            NodePort    10.106.117.188   <none>        80:32680/TCP   5d22h
service/python-app-dev-simple-app-headless   ClusterIP   None             <none>        80/TCP         3d23h

NAME                                                     STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/data-python-app-dev-simple-app-0   Bound    pvc-dc809eac-6b33-4313-bd6b-1e9c23392860   100Mi      RWO            standard       <unset>                 3d23h
persistentvolumeclaim/data-python-app-dev-simple-app-1   Bound    pvc-1af57860-efb0-4a93-912c-0af419542b74   100Mi      RWO            standard       <unset>                 10m
persistentvolumeclaim/python-app-dev-simple-app-data     Bound    pvc-5e206c20-2037-4ca6-a905-112a6f2ea0a0   100Mi      RWO            standard       <unset>                 9d
```

---

## 3. Network Identity

A **Headless Service** (`clusterIP: None`) creates a DNS A record for each ready pod.  

Tested from a temporary `busybox` pod:

```bash
$ kubectl run dns-test --image=busybox --rm -it --restart=Never -n dev -- nslookup python-app-dev-simple-app-1.python-app-dev-simple-app-headless.dev.svc.cluster.local

Server:         10.96.0.10
Address:        10.96.0.10:53


Name:   python-app-dev-simple-app-1.python-app-dev-simple-app-headless.dev.svc.cluster.local
Address: 10.244.1.105

pod "dns-test" deleted from dev namespace
```

## 4. Per‑Pod Storage Evidence && Persistence Test

Each pod mounts its own PVC at `/data`. To show isolation, the application’s `/visit` endpoint was queried on both pods.

```bash
$ kubectl port-forward pod/python-app-dev-simple-app-0 -n dev 8080:8000 & &
kubectl port-forward pod/python-app-dev-simple-app-1 -n dev 8081:8000 &
[1] 29029
[2] 29030


$ curl http://localhost:8080/visit
{"visits":1}

$ curl http://localhost:8080/visit
{"visits":2}

$ curl http://localhost:8080/visit
{"visits":3}

$ curl http://localhost:8081/visit
{"visits":1}

$ curl http://localhost:8081/visit
{"visits":2}

$ kubectl delete pod python-app-dev-simple-app-0 -n devapp-0 -n dev
pod "python-app-dev-simple-app-0" deleted from dev namespace

$ kubectl get pods -n dev -w
NAME                          READY   STATUS    RESTARTS   AGE
python-app-dev-simple-app-0   1/1     Running   0          9s
python-app-dev-simple-app-1   1/1     Running   0          6m7s

$ curl http://localhost:8080/visits
{"visits":3}
```