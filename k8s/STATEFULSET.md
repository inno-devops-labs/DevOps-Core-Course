# Lab 15

## StatefulSet Overview

- Purpose: manage stateful applications that need stable network IDs and persistent per-pod storage.

### Key differences vs Deployment

- Identity
  - StatefulSet: each pod gets a stable, unique hostname (ordinal) and predictable DNS name (pod-0, pod-1...).
  - Deployment: pods are interchangeable; no stable per-pod identity.

- Storage
  - StatefulSet: supports volumeClaimTemplates so each pod gets its own persistent volume (mapped by ordinal).
  - Deployment: PVCs must be managed manually; pods don’t get automatic per-pod PVs.

- Ordering & lifecycle
  - StatefulSet: ordered, graceful pod creation, scaling, rolling updates, and termination (respecting ordinals).
  - Deployment: parallel, unordered pod creation/termination for speed.

- Network & discovery
  - StatefulSet: designed to work with a headless Service for stable DNS-based discovery.
  - Deployment: typically fronted by a ClusterIP/Service load balancer; no per-pod DNS identity.

- Use cases
  - StatefulSet: databases, distributed systems, apps needing sticky identity.
  - Deployment: stateless web services, APIs, workers that can be scaled/replaced freely.


## Resource Verification

Output of kubectl get po,sts,svc,pvc

```bash
kubectl get svc

NAME                     TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
kubernetes               ClusterIP   10.96.0.1       <none>        443/TCP        17m
myapp-mychart-headless   ClusterIP   None            <none>        80/TCP         3m9s

kubectl get statefulset

NAME            READY   AGE
myapp-mychart   3/3     96s

kubectl get pods
NAME                             READY   STATUS    RESTARTS   AGE
myapp-mychart-0  1/1     Running   0          96s
myapp-mychart-1   1/1     Running   0          96s
myapp-mychart-2   1/1     Running   0          96s

kubectl get pvc

NAME                   STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
data-myapp-mychart-0   Bound    pvc-24939609-c8ee-4b3d-b75f-c00101172b1f   100Mi      RWO            standard       <unset>                 96s
data-myapp-mychart-1   Bound    pvc-a5e89bec-01fd-487d-b9a4-9cbc609f3606   100Mi      RWO            standard       <unset>                 83s
data-myapp-mychart-2   Bound    pvc-d2b4f3b8-9062-4a78-9ca0-20827a61e3f6   100Mi      RWO            standard       <unset>                 70s

```

Network Identity - DNS resolution outputs

```bash
# Inside pod
nonroot@myapp-mychart-0:/app$ getent hosts myapp-mychart-1.myapp-mychart-headless.default.svc.cluster.local
10.244.0.13     myapp-mychart-1.myapp-mychart-headless.default.svc.cluster.local
```

Per-Pod Storage Evidence - Different visit counts per pod

```bash
curl localhost:8081/visits
{"visits":169,"timestamp":"2026-05-07T19:02:56.771901+00:00"}

curl localhost:8082/visits
{"visits":179,"timestamp":"2026-05-07T19:02:54.913873+00:00"}
```

Persistence Test - Data survives pod deletion

```bash
$ kubectl exec myapp-mychart-0 -- cat /data/visits.json
{
  "count": 204
}
$ kubectl delete pod myapp-mychart-0 
pod "myapp-mychart-0" deleted from default namespace

$ kubectl exec myapp-mychart-0 -- cat /data/visits.json
{
  "count": 205
}
```
