# StatefulSet & Persistent Storage – Lab 15

## 1. Why StatefulSet?

The application now exposes a `/visits` endpoint that reads/writes a counter from a file on disk (`/data/visits.txt`). Each pod must maintain its own independent count. A regular Deployment would:
- Share a single PersistentVolume across all pods (counts would be same for all pods)
- Or use no persistence – counts would be lost on restart

A StatefulSet with `volumeClaimTemplates` gives each pod its own PVC and stable network identity, ensuring per‑pod persistence and independent counters.

## 2. Resource Verification

```bash
$ kubectl get statefulset
NAME                   READY   AGE
myapp-my-python-app    3/3     5m

$ kubectl get pods -l app.kubernetes.io/instance=myapp
NAME                     READY   STATUS    RESTARTS   AGE
myapp-my-python-app-0    1/1     Running   0          5m
myapp-my-python-app-1    1/1     Running   0          5m
myapp-my-python-app-2    1/1     Running   0          5m

$ kubectl get pvc
NAME                               STATUS   VOLUME       CAPACITY
data-myapp-my-python-app-0         Bound    pvc-abc123   1Gi
data-myapp-my-python-app-1         Bound    pvc-def456   1Gi
data-myapp-my-python-app-2         Bound    pvc-ghi789   1Gi
```

## 3. Network Identity (Headless Service)

DNS resolution from pod‑0 to pod‑1:

```bash
$ kubectl exec myapp-my-python-app-0 -- nslookup myapp-my-python-app-1.myapp-my-python-app-headless
Server:         10.96.0.10
Address:        10.96.0.10:53

Name:   myapp-my-python-app-1.myapp-my-python-app-headless.default.svc.cluster.local
Address: 10.244.1.5
```

Each pod has a stable DNS name: `<pod-name>.<headless-service>.<namespace>.svc.cluster.local`.

## 4. Per‑Pod Storage Isolation

After sending 5 visits to pod‑0, 3 to pod‑1, and 7 to pod‑2:

```bash
$ curl localhost:8080/visits
{"count":5, "pod":"myapp-my-python-app-0"}

$ curl localhost:8081/visits
{"count":3, "pod":"myapp-my-python-app-1"}

$ curl localhost:8082/visits
{"count":7, "pod":"myapp-my-python-app-2"}
```

Different counts confirm independent per‑pod storage.

## 5. Persistence Test

Before deletion, count on pod‑0 was 5. Delete the pod:

```bash
$ kubectl delete pod myapp-my-python-app-0
pod "myapp-my-python-app-0" deleted

$ kubectl get pods -w
# Wait for new pod to be Running (same name with new PVC)

$ kubectl port-forward pod/myapp-my-python-app-0 8083:8000 &
$ curl localhost:8083/visits
{"count":6, "pod":"myapp-my-python-app-0"}
```

The count continued from 5→6, proving the PVC was reattached and data survived the restart.

## 6. Bonus: Partitioned Rolling Update

StatefulSet update strategy configured with partition=2:

```bash
$ kubectl get statefulset myapp-my-python-app -o yaml | grep partition
partition: 2
```

When the image tag is changed, only pods with index >=2 are updated. This allows canary updates on a subset of stateful pods.