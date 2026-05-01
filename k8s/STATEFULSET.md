# Lab 15 — StatefulSets and Persistent Storage

## 1. StatefulSet concepts

Stateful workloads need guarantees that Deployments do not provide.  
`StatefulSet` is used when each replica must keep identity and storage across restarts.

### Why StatefulSet

- **Stable pod names:** pods are ordinal and predictable (`app-0`, `app-1`, `app-2`).
- **Stable network identity:** each pod has a stable DNS name when used with a headless Service.
- **Per-pod persistent storage:** each pod gets its own PVC, not a shared anonymous volume.
- **Ordered operations:** creation, scaling, and updates are controlled in ordinal order.

### Deployment vs StatefulSet

| Feature | Deployment | StatefulSet |
|---|---|---|
| Pod naming | Random suffix | Stable ordinal (`-0`, `-1`, `-2`) |
| Pod identity | Ephemeral | Stable |
| Storage model | Usually shared/external | Per-pod PVC via `volumeClaimTemplates` |
| Scaling behavior | Parallel/unordered | Ordered by ordinal |
| Typical workloads | Stateless APIs/web | Databases, queues, clustered stateful systems |

### Headless Service (`clusterIP: None`)

A headless Service does not provide a virtual ClusterIP.  
Instead, Kubernetes DNS returns direct pod records, enabling addressing by stable names:

- `<statefulset>-0.<headless-service>.<namespace>.svc.cluster.local`
- `<statefulset>-1.<headless-service>.<namespace>.svc.cluster.local`

This is required for many distributed systems that need direct peer-to-peer addressing.

### When to use what

- Use **Deployment** for stateless services where pod identity does not matter.
- Use **StatefulSet** when each replica must keep unique identity/data.

Examples for StatefulSet:

- PostgreSQL / MySQL / MongoDB
- Kafka / RabbitMQ
- Elasticsearch / Cassandra / ZooKeeper-like clustered systems

---

## 2. Resource verification

The chart was deployed as release `lab15-stateful` in namespace `lab15` using `values-statefulset.yaml`.

```bash
helm upgrade --install lab15-stateful ./k8s/devops-info-service \
  -n lab15 --create-namespace \
  -f ./k8s/devops-info-service/values-statefulset.yaml \
  --set image.repository=devops-info-service \
  --set image.tag=lab12 \
  --set image.pullPolicy=IfNotPresent
```

Result:

```text
Release "lab15-stateful" does not exist. Installing it now.
NAME: lab15-stateful
NAMESPACE: lab15
STATUS: deployed
REVISION: 1
```

StatefulSet status:

```bash
kubectl get statefulset -n lab15
```

```text
NAME                                 READY   AGE
lab15-stateful-devops-info-service   3/3     65s
```

Pods (stable ordinal identity):

```bash
kubectl get pods -n lab15 -o wide
```

```text
NAME                                   READY   STATUS    RESTARTS   AGE   IP             NODE
lab15-stateful-devops-info-service-0   1/1     Running   0          71s   10.244.0.200   minikube
lab15-stateful-devops-info-service-1   1/1     Running   0          27s   10.244.0.201   minikube
lab15-stateful-devops-info-service-2   1/1     Running   0          21s   10.244.0.202   minikube
```

Services (regular + headless):

```bash
kubectl get svc -n lab15
```

```text
NAME                                          TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
lab15-stateful-devops-info-service            NodePort    10.111.120.138   <none>        80:30089/TCP   77s
lab15-stateful-devops-info-service-headless   ClusterIP   None             <none>        80/TCP         77s
```

PersistentVolumeClaims (one PVC per pod):

```bash
kubectl get pvc -n lab15
```

```text
NAME                                               STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
data-volume-lab15-stateful-devops-info-service-0   Bound    pvc-9f705a3d-8868-4ca7-9725-6675030b3791   100Mi      RWO            standard       82s
data-volume-lab15-stateful-devops-info-service-1   Bound    pvc-2ea58824-131d-406c-8af9-f7167a041116   100Mi      RWO            standard       38s
data-volume-lab15-stateful-devops-info-service-2   Bound    pvc-5a05e793-2416-41d0-a9fa-0e717cb17b7c   100Mi      RWO            standard       32s
```

Pod names confirm predictable StatefulSet identity:

```bash
kubectl get pods -n lab15 -o name
```

```text
pod/lab15-stateful-devops-info-service-0
pod/lab15-stateful-devops-info-service-1
pod/lab15-stateful-devops-info-service-2
```

---

## 3. Persistence validation (StatefulSet behavior)

To verify per-pod persistent storage, different values were written into each pod's `/data/visits` file.

```bash
kubectl exec -n lab15 lab15-stateful-devops-info-service-0 -- sh -c 'echo 100 > /data/visits && cat /data/visits'
kubectl exec -n lab15 lab15-stateful-devops-info-service-1 -- sh -c 'echo 200 > /data/visits && cat /data/visits'
kubectl exec -n lab15 lab15-stateful-devops-info-service-2 -- sh -c 'echo 300 > /data/visits && cat /data/visits'
```

```text
100
200
300
```

Then pod `lab15-stateful-devops-info-service-1` was deleted and recreated by StatefulSet.

```bash
kubectl delete pod -n lab15 lab15-stateful-devops-info-service-1
kubectl rollout status statefulset/lab15-stateful-devops-info-service -n lab15
```

```text
pod "lab15-stateful-devops-info-service-1" deleted
statefulset rolling update complete 2 pods at revision lab15-stateful-devops-info-service-86b85468f7...
```

After recreation, the same value was still present in the file:

```bash
kubectl exec -n lab15 lab15-stateful-devops-info-service-1 -- cat /data/visits
```

```text
200
```

PVC bindings remained stable and bound for each ordinal pod:

```bash
kubectl get pvc -n lab15
```

```text
NAME                                               STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
data-volume-lab15-stateful-devops-info-service-0   Bound    pvc-9f705a3d-8868-4ca7-9725-6675030b3791   100Mi      RWO            standard       8m46s
data-volume-lab15-stateful-devops-info-service-1   Bound    pvc-2ea58824-131d-406c-8af9-f7167a041116   100Mi      RWO            standard       8m2s
data-volume-lab15-stateful-devops-info-service-2   Bound    pvc-5a05e793-2416-41d0-a9fa-0e717cb17b7c   100Mi      RWO            standard       7m56s
```

Conclusion: StatefulSet preserved data across pod recreation, and each pod retained its own dedicated persistent volume.

---

## 4. Final summary

This lab migrated the application from a stateless deployment model to a StatefulSet-based model.

Implemented Kubernetes objects and behavior:

- `StatefulSet` with stable ordinal pod identities.
- Headless service (`clusterIP: None`) for stable DNS records.
- `volumeClaimTemplates` for automatic per-pod PVC provisioning.
- Persistent application state stored in `/data/visits`.

Observed results:

- Pods were created with predictable names (`-0`, `-1`, `-2`).
- A dedicated PVC was created and bound for each pod.
- Data written to a specific pod remained available after pod recreation.
- StatefulSet reconciliation restored deleted pods while keeping data consistency.

Operational commands used for validation:

```bash
kubectl get statefulset -n lab15
kubectl get pods -n lab15 -o wide
kubectl get svc -n lab15
kubectl get pvc -n lab15
kubectl rollout status statefulset/lab15-stateful-devops-info-service -n lab15
```

Final conclusion: Task requirements for StatefulSet deployment, stable identity, headless networking, and persistent per-pod storage were successfully met.
