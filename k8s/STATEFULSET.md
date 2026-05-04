# Lab 15 — StatefulSets & Persistent Storage

## StatefulSet Overview

### Why StatefulSet

StatefulSet required when each pod needs a stable identity and its own persistent storage. It guarantees ordered startup/termination and stable DNS names, which is critical for stateful workloads and for verifying per-pod data isolation.


### differences from Deployment

- Pod names are stable and ordered (e.g., app-0, app-1) instead of random suffixes.
- Storage is per-pod via volumeClaimTemplates instead of shared/ephemeral volumes.
- Scaling and rollout are ordered and deterministic rather than parallel by default.
- Each pod gets a stable DNS name through a headless Service.


## Resource Verification

```bash
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl get po,sts,svc,pvc
NAME                        READY   STATUS      RESTARTS   AGE
pod/devops-info-service-0   1/1     Running     0          13h
pod/devops-info-service-1   1/1     Running     0          13h
pod/devops-info-service-2   1/1     Running     0          13h

NAME                                   READY   AGE
statefulset.apps/devops-info-service   3/3     14h

NAME                                   TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service            NodePort    10.108.23.137   <none>        80:30080/TCP   14h
service/devops-info-service-headless   ClusterIP   None            <none>        80/TCP         14h
service/kubernetes                     ClusterIP   10.96.0.1       <none>        443/TCP        22d

NAME                                                      STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/data-volume-devops-info-service-0   Bound    pvc-3c8cec6b-beef-4f4c-8213-d0b083d9bf4c   100Mi      RWO            standard       <unset>                 14h
persistentvolumeclaim/data-volume-devops-info-service-1   Bound    pvc-02ca4960-33f4-449b-b69a-b2532c6b72db   100Mi      RWO            standard       <unset>                 14h
persistentvolumeclaim/data-volume-devops-info-service-2   Bound    pvc-d4f5d7df-406f-457a-a104-79a6a087833b   100Mi      RWO            standard       <unset>                 14h
```

## Network Identity

Pods do not include `nslookup`, so I ran a temporary utility pod and performed the DNS checks from there.

```bash
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl exec -it bb -- nslookup devops-info-service-0.devops-info-service-headless.default.svc.cluster.local
Server:         10.96.0.10
Address:        10.96.0.10:53


Name:   devops-info-service-0.devops-info-service-headless.default.svc.cluster.local
Address: 10.244.0.236

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl exec -it bb -- nslookup devops-info-service-1.devops-info-service-headless.default.svc.cluster.local
Server:         10.96.0.10
Address:        10.96.0.10:53

Name:   devops-info-service-1.devops-info-service-headless.default.svc.cluster.local
Address: 10.244.0.240

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl exec -it bb -- nslookup devops-info-service-2.devops-info-service-headless.default.svc.cluster.local
Server:         10.96.0.10
Address:        10.96.0.10:53

Name:   devops-info-service-2.devops-info-service-headless.default.svc.cluster.local
Address: 10.244.0.241
```

## Per-Pod Storage Evidence - Different visit counts per pod

```bash
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ curl localhost:8080/
...

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ curl localhost:8080/visits
{"visits":1}

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ curl localhost:8081/
...

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ curl localhost:8081/visits
{"visits":1}

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ curl localhost:8081/
...

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ curl localhost:8081/
...

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ curl localhost:8081/visits
{"visits":3}

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ curl localhost:8080/visits
{"visits":1}

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl exec devops-info-service-0 -- cat /data/visits
1

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl exec devops-info-service-1 -- cat /data/visits
3
```

## Persistence Test

```bash
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl exec devops-info-service-0 -- cat /data/visits
1

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl delete pod devops-info-service-0
pod "devops-info-service-0" deleted from default namespace

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl get pods -w
NAME                    READY   STATUS    RESTARTS   AGE
devops-info-service-0   1/1     Running   0          10s
devops-info-service-1   1/1     Running   0          3m12s
devops-info-service-2   1/1     Running   0          3m52s

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl exec devops-info-service-0 -- cat /data/visits
1
```