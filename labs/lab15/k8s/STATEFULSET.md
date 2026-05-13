# Lab 15 — StatefulSets & Persistent Storage

## 1. StatefulSet Overview

This lab demonstrates how to run a stateful application in Kubernetes using a StatefulSet, a headless Service, and per-pod persistent storage.

StatefulSets are useful when applications require:

- stable pod names
- stable network identity
- persistent storage per pod
- ordered startup and scaling
- predictable pod replacement

Examples of workloads that commonly use StatefulSets:

- PostgreSQL
- MySQL
- MongoDB
- Kafka
- Elasticsearch
- Cassandra

---

## 2. Deployment vs StatefulSet

| Feature | Deployment | StatefulSet |
|---|---|---|
| Pod names | Random suffix | Stable ordinal names |
| Example pod name | app-7f9c8d9f9-x7abc | app-0 |
| Storage | Usually shared or external PVC | Per-pod PVC via volumeClaimTemplates |
| Network identity | Not stable | Stable DNS name |
| Scaling order | Not guaranteed | Ordered by default |
| Use case | Stateless apps | Stateful apps |

For stateless applications, Deployments or Rollouts are usually better.  
For applications that need stable identity and storage, StatefulSets are the correct choice.

---

## 3. Headless Service

A headless Service was created for the StatefulSet.

A headless Service uses:

```yaml
clusterIP: None
```

This allows Kubernetes DNS to create stable DNS records for each StatefulSet pod.

DNS pattern:

```text
<pod-name>.<headless-service-name>.<namespace>.svc.cluster.local
```

Example:

```text
stateful-app-devops-info-service-1.stateful-app-devops-info-service-headless.stateful.svc.cluster.local
```

---

## 4. StatefulSet Implementation

A StatefulSet template was created in the Helm chart.

Important configuration:

```yaml
apiVersion: apps/v1
kind: StatefulSet
spec:
  serviceName: stateful-app-devops-info-service-headless
  replicas: 3
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes:
          - ReadWriteOnce
        resources:
          requests:
            storage: 1Gi
```

Each pod gets its own PVC automatically.

The application mounts the per-pod volume at:

```text
/data
```

---

## 5. Resource Verification

Command:

```bash
kubectl get sts,pods,pvc,svc -n stateful
```

Output:

```text
NAME                                                READY   AGE
statefulset.apps/stateful-app-devops-info-service   3/3     33m

NAME                                     READY   STATUS    RESTARTS   AGE
pod/stateful-app-devops-info-service-0   1/1     Running   0          33m
pod/stateful-app-devops-info-service-1   1/1     Running   0          32m
pod/stateful-app-devops-info-service-2   1/1     Running   0          32m

NAME                                                            STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS
persistentvolumeclaim/data-stateful-app-devops-info-service-0   Bound    pvc-8acb1088-b559-4b56-8520-a63b7c34cc8c   1Gi        RWO            standard
persistentvolumeclaim/data-stateful-app-devops-info-service-1   Bound    pvc-2f8ace49-d53e-468b-acd4-bb226a9d6a17   1Gi        RWO            standard
persistentvolumeclaim/data-stateful-app-devops-info-service-2   Bound    pvc-20e2b47b-4934-4f4f-822b-a5246fe185f0   1Gi        RWO            standard

NAME                                                TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)
service/stateful-app-devops-info-service            NodePort    10.96.20.243   <none>        80:31129/TCP
service/stateful-app-devops-info-service-headless   ClusterIP   None           <none>        80/TCP
```

This confirms:

- StatefulSet is running
- pods have stable ordinal names
- each pod has its own PVC
- headless Service exists

---

## 6. Stable Network Identity

DNS resolution was tested from inside `stateful-app-devops-info-service-0`.

Command:

```bash
kubectl exec -it -n stateful stateful-app-devops-info-service-0 -- sh
```

Inside the pod:

```sh
getent hosts stateful-app-devops-info-service-1.stateful-app-devops-info-service-headless
getent hosts stateful-app-devops-info-service-2.stateful-app-devops-info-service-headless
```

Output:

```text
10.244.0.22 stateful-app-devops-info-service-1.stateful-app-devops-info-service-headless.stateful.svc.cluster.local
10.244.0.24 stateful-app-devops-info-service-2.stateful-app-devops-info-service-headless.stateful.svc.cluster.local
```

This proves that StatefulSet pods have stable DNS names through the headless Service.

---

## 7. Per-Pod Storage Isolation

Each StatefulSet pod received its own persistent volume.

Test data was written into pod-specific storage.

Commands:

```bash
kubectl exec -n stateful stateful-app-devops-info-service-0 -- sh -c 'echo pod-0-data > /data/visits'
kubectl exec -n stateful stateful-app-devops-info-service-1 -- sh -c 'echo pod-1-data > /data/visits'
```

Verification:

```bash
kubectl exec -n stateful stateful-app-devops-info-service-0 -- cat /data/visits
kubectl exec -n stateful stateful-app-devops-info-service-1 -- cat /data/visits
```

Output:

```text
pod-0-data
pod-1-data
```

This proves that each pod has isolated storage.

---

## 8. Persistence Test

Pod `stateful-app-devops-info-service-0` was deleted to verify that its persistent data survives pod recreation.

Command:

```bash
kubectl delete pod -n stateful stateful-app-devops-info-service-0
kubectl get pods -n stateful -w
```

Output:

```text
pod "stateful-app-devops-info-service-0" deleted from stateful namespace

NAME                                 READY   STATUS              RESTARTS   AGE
stateful-app-devops-info-service-0   0/1     ContainerCreating   0          0s
stateful-app-devops-info-service-1   1/1     Running             0          37m
stateful-app-devops-info-service-2   1/1     Running             0          37m
stateful-app-devops-info-service-0   0/1     Running             0          1s
stateful-app-devops-info-service-0   1/1     Running             0          12s
```

After the pod was recreated, the data was still present:

```bash
kubectl exec -n stateful stateful-app-devops-info-service-0 -- cat /data/visits
```

Output:

```text
pod-0-data
```

This proves that StatefulSet storage persists across pod deletion and recreation.

---

## 9. Application Access

The application was also tested through direct pod access using port-forwarding.

Example:

```bash
kubectl port-forward -n stateful pod/stateful-app-devops-info-service-0 8080:5000
kubectl port-forward -n stateful pod/stateful-app-devops-info-service-1 8081:5000
```

Testing:

```bash
curl localhost:8080
curl localhost:8081
```

The responses showed different hostnames:

```text
stateful-app-devops-info-service-0
stateful-app-devops-info-service-1
```

This confirms stable identity per pod.

---

## 10. Challenges and Solutions

### Extra PVC from previous Helm template

The chart still had an old `pvc.yaml` from the previous labs.  
This created an unnecessary pending PVC.

Solution:

- disabled the old standalone PVC template
- used StatefulSet `volumeClaimTemplates` instead

### Preview Service from Lab 14

The chart still had the blue-green preview service from Lab 14.

Solution:

- disabled the preview service for the StatefulSet lab
- kept only the standard Service and the headless Service

### Visits file was not created automatically

The current application image did not automatically create `/data/visits`.

Solution:

- manually wrote test data to `/data/visits`
- verified per-pod isolation and persistence using files inside each pod-specific PVC

---

## 11. Summary

This lab successfully demonstrated StatefulSets and persistent storage in Kubernetes.

Completed:

- StatefulSet created
- headless Service created
- stable pod names verified
- stable DNS names verified
- per-pod PVCs created
- storage isolation tested
- persistence after pod deletion tested

StatefulSets are the correct Kubernetes controller when workloads require stable identity and persistent per-pod storage.
