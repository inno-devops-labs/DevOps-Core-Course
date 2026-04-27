# Lab 15 — StatefulSets & Persistent Storage

## 1. StatefulSet Overview

### Why StatefulSet
I used StatefulSet because this workload needs:
- Stable pod identity (`pod-0`, `pod-1`, `pod-2`)
- Stable per-pod storage
- Predictable ordered lifecycle

### Deployment vs StatefulSet

| Feature | Deployment | StatefulSet |
|---|---|---|
| Pod names | Random suffix | Stable ordinal (`-0`, `-1`, `-2`) |
| Network identity | Not stable | Stable DNS per pod |
| Storage | Shared/external claim patterns | Dedicated PVC per pod (`volumeClaimTemplates`) |
| Scale/update ordering | Unordered/parallel | Ordered by pod ordinal |
| Best fit | Stateless APIs/web apps | Stateful workloads (DB, queues, clustered nodes) |

### Implemented chart resources
- `templates/statefulset.yaml` with `serviceName` and `volumeClaimTemplates`
- `templates/service-headless.yaml` with `clusterIP: None`
- Existing regular Service kept for access
- Stateful mode enabled via `values-statefulset.yaml`

## 2. Resource Verification

Command:

```bash
kubectl get po,sts,svc,pvc -n dev
```

Output:

```text

NAME                                READY   STATUS    RESTARTS   AGE
pod/devops-info-sts-devops-info-0   1/1     Running   0          4m12s
pod/devops-info-sts-devops-info-1   1/1     Running   0          6m53s
pod/devops-info-sts-devops-info-2   1/1     Running   0          7m1s

NAME                                           READY   AGE
statefulset.apps/devops-info-sts-devops-info   3/3     14m

NAME                                           TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)        AGE
service/devops-info-sts-devops-info            NodePort    10.96.39.18   <none>        80:30082/TCP   14m
service/devops-info-sts-devops-info-headless   ClusterIP   None          <none>        80/TCP         14m

NAME                                                              STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/data-volume-devops-info-sts-devops-info-0   Bound    pvc-d4306088-9e56-4ce8-a1b5-7501327d007a   100Mi      RWO            standard       <unset>                 14m
persistentvolumeclaim/data-volume-devops-info-sts-devops-info-1   Bound    pvc-009e6b8d-5957-44ca-b0fc-3a1c94620525   100Mi      RWO            standard       <unset>                 14m
persistentvolumeclaim/data-volume-devops-info-sts-devops-info-2   Bound    pvc-8e3a2e11-e30b-4e8d-8ff0-ea6e7af97eb4   100Mi      RWO            standard       <unset>                 13m
```

Verification points:
- StatefulSet resource exists
- Headless service exists (`CLUSTER-IP: None`)
- Per-pod PVC naming pattern is correct (`data-volume-<sts-name>-<ordinal>`)

## 3. Network Identity

Commands:

```bash
kubectl exec -n dev -it devops-info-sts-devops-info-0 -- \
  sh -c 'getent hosts devops-info-sts-devops-info-1.devops-info-sts-devops-info-headless'

kubectl exec -n dev -it devops-info-sts-devops-info-0 -- \
  sh -c 'getent hosts devops-info-sts-devops-info-2.devops-info-sts-devops-info-headless'
```

Output:

```text
10.244.0.10  devops-info-sts-devops-info-1.devops-info-sts-devops-info-headless.dev.svc.cluster.local
10.244.0.12  devops-info-sts-devops-info-2.devops-info-sts-devops-info-headless.dev.svc.cluster.local
```

Conclusion:
- Pod DNS identity is stable and follows StatefulSet + headless service naming.

## 4. Per-Pod Storage Evidence

Port-forwards:

```bash
kubectl port-forward -n dev pod/devops-info-sts-devops-info-0 8080:5000
kubectl port-forward -n dev pod/devops-info-sts-devops-info-1 8081:5000
kubectl port-forward -n dev pod/devops-info-sts-devops-info-2 8082:5000
```

Initial visits per pod:

```text
curl -s http://127.0.0.1:8080/visits
{"visits":0,"file_path":"/data/visits","timestamp":"2026-04-27T19:29:55.376022Z"}

curl -s http://127.0.0.1:8081/visits
{"visits":0,"file_path":"/data/visits","timestamp":"2026-04-27T19:30:00.862458Z"}

curl -s http://127.0.0.1:8082/visits
{"visits":0,"file_path":"/data/visits","timestamp":"2026-04-27T19:30:05.571929Z"}
```

Traffic sent only to pod `-0`:

```text
curl -s http://127.0.0.1:8080/
curl -s http://127.0.0.1:8080/
```

Visits after traffic:

```text
curl -s http://127.0.0.1:8080/visits
{"visits":2,"file_path":"/data/visits","timestamp":"2026-04-27T19:30:23.861230Z"}

curl -s http://127.0.0.1:8081/visits
{"visits":0,"file_path":"/data/visits","timestamp":"2026-04-27T19:30:29.050428Z"}

curl -s http://127.0.0.1:8082/visits
{"visits":0,"file_path":"/data/visits","timestamp":"2026-04-27T19:30:32.653343Z"}
```

Conclusion:
- Counters differ across pods, proving isolated per-pod storage.

## 5. Persistence Test

Commands:

```bash
kubectl exec -n dev devops-info-sts-devops-info-0 -- cat /data/visits
kubectl delete pod -n dev devops-info-sts-devops-info-0
kubectl wait --for=condition=ready pod/devops-info-sts-devops-info-0 -n dev --timeout=180s
kubectl exec -n dev devops-info-sts-devops-info-0 -- cat /data/visits
```

Output:

```text
$ kubectl exec -n dev devops-info-sts-devops-info-0 -- cat /data/visits
2

$ kubectl delete pod -n dev devops-info-sts-devops-info-0
pod "devops-info-sts-devops-info-0" deleted from dev namespace

$ kubectl wait --for=condition=ready pod/devops-info-sts-devops-info-0 -n dev --timeout=180s
pod/devops-info-sts-devops-info-0 condition met

$ kubectl exec -n dev devops-info-sts-devops-info-0 -- cat /data/visits
2
```

Conclusion:
- Data survived pod recreation, so persistent volume binding works correctly for StatefulSet pod `-0`.

## 6. Answers to Lab Questions

### Task 1 — StatefulSet Concepts

**Q: What StatefulSet guarantees?**  
A: StatefulSet guarantees stable pod identity, stable per-pod persistent storage, and ordered pod operations (creation/termination by ordinal).

**Q: What is the key difference between Deployment and StatefulSet?**  
A: Deployment is designed for stateless replicas with interchangeable pods; StatefulSet is designed for stateful replicas where each pod keeps stable identity and storage.

**Q: When should Deployment be used instead of StatefulSet?**  
A: Use Deployment for stateless web/API services where any replica can serve any request and pod identity is not important.

**Q: When should StatefulSet be used instead of Deployment?**  
A: Use StatefulSet for databases, brokers, and clustered systems that require stable hostnames, predictable ordering, and dedicated persistent volumes per replica.

**Q: Examples of stateful workloads?**  
A: PostgreSQL/MySQL/MongoDB, Kafka/RabbitMQ, Elasticsearch/Cassandra.

**Q: What is a headless Service (`clusterIP: None`)?**  
A: A Service without a virtual cluster IP that publishes DNS records for individual pod endpoints.

**Q: How does DNS work with StatefulSet in this lab?**  
A: Each pod is reachable via `<pod-name>.<headless-service>` (and full FQDN in-cluster), which resolves to that pod's IP.
