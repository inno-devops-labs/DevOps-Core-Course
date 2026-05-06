## StatefulSet overview vs Deployment

StatefulSets are meant for applications that need:

- **Stable network identity** - predictable pod names and stable DNS under a headless Service.
- **Stable storage** - one PersistentVolumeClaim per pod via `volumeClaimTemplates`, bound for the lifetime of that ordinal.
- **Ordered operations** - create, scale, and terminate pods in a defined order.

**Deployment vs StatefulSet**

| Aspect            | Deployment                         | StatefulSet                                       |
|-------------------|------------------------------------|---------------------------------------------------|
| Pod names         | Random suffix                      | Stable ordinal suffix                             |
| PVC pattern       | Often one shared PVC or none       | Per-pod PVC from templates                        |
| Scaling order     | Not ordered                        | Ordered (e.g. scale up 0->1->2, scale down reverse) |
| Service discovery | Usually via ClusterIP/LoadBalancer | Headless Service gives per-pod DNS                |

**When to use which**

- **Deployment** - stateless HTTP APIs, workers that do not store instance-local data on disk.
- **StatefulSet** - databases, Kafka/ZooKeeper-style clusters, or any workload where each replica must keep its own data volume and address.

**Headless Service**

A headless Service does not allocate a virtual IP for load-balancing. 
Instead, the cluster DNS publishes **A/AAAA records for each backend Pod**. For StatefulSets, each pod is reachable at:

`<statefulset-pod-name>.<headless-service-name>.<namespace>.svc.cluster.local`

Short names inside the same namespace often resolve as `<pod-name>.<headless-service-name>`.

---

## Chart configuration

The `devops-info-service` Helm chart supports switching between Deployment and StatefulSet:

- `values.yaml` -> `statefulset.enabled: true` enables `templates/statefulset.yaml` and `templates/service-headless.yaml`.
- When StatefulSet mode is on, the chart **does not** render the standalone `pvc.yaml`,  storage comes from `volumeClaimTemplates` on the StatefulSet.
- Update behaviour is controlled by `statefulset.updateStrategy`.

For **per-pod visit counts** using the application’s `/visits` endpoint and `/data/visits` file, 
the container image must include the current FastAPI app from `app_python/`. 
The published image referenced by default `values.yaml` may lag behind the repo,
for lab verification a local image was built from `app_python/Dockerfile`, loaded into Minikube, and deployed with:

- `image.repository=devops-lab15`, `image.tag=local`, `image.pullPolicy=Never`.

---

## Resource verification

```text
$ kubectl get po,sts,svc,pvc -l app.kubernetes.io/instance=lab15

NAME                              READY   STATUS    RESTARTS   AGE
pod/lab15-devops-info-service-0   1/1     Running   0          17s
pod/lab15-devops-info-service-1   1/1     Running   0          2m11s

NAME                                         READY   AGE
statefulset.apps/lab15-devops-info-service   2/2     14m

NAME                                         TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/lab15-devops-info-service            NodePort    10.110.126.255   <none>        80:30080/TCP   14m
service/lab15-devops-info-service-headless   ClusterIP   None             <none>        80/TCP         14m

NAME                                                     STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/data-lab15-devops-info-service-0   Bound    pvc-03aaf303-b069-4d7f-a9a0-c1f1d340cbac   100Mi      RWO            standard       14m
persistentvolumeclaim/data-lab15-devops-info-service-1   Bound    pvc-94aa52d6-2ca7-4ca7-90e4-900aa1157438   100Mi      RWO            standard       12m
```

---

## Network identity

```text
$ kubectl run dns-check2 --rm -i --restart=Never --image=busybox:1.36 -- \
    nslookup lab15-devops-info-service-1.lab15-devops-info-service-headless.default.svc.cluster.local

Server:		10.96.0.10
Address:	10.96.0.10:53

Name:	lab15-devops-info-service-1.lab15-devops-info-service-headless.default.svc.cluster.local
Address: 10.244.0.11

pod "dns-check2" deleted from default namespace
```

---

## Per-pod storage isolation

Traffic was sent **directly to each pod** with `kubectl port-forward` to separate local ports. `GET /` increments the on-disk counter for that pod only.

```text
--- /visits per pod ---
pod-0: {"visits":6}
pod-1: {"visits":3}

--- file /data/visits ---
6
3
```

---

## Persistence after pod deletion

```text
--- count before delete pod-0 ---
pod-0 visits file: 6

pod "lab15-devops-info-service-0" deleted

--- count after pod-0 restart ---
6
```

The visit count **survived** pod replacement, confirming data lives on the PVC, not on the container filesystem.