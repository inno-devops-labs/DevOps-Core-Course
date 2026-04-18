# Lab 15 - StatefulSets and Persistent Storage

This lab converts the Helm-based Python application from a rollout-oriented workload to a StatefulSet with stable pod identities and per-pod persistent storage.

## 1. Why StatefulSet

### Deployment vs StatefulSet

| Feature | Deployment / Rollout | StatefulSet |
| --- | --- | --- |
| Pod identity | Ephemeral pod names with random suffixes | Stable ordinal pod names like `python-app-sts-0` |
| Storage | Usually shared or externally managed | One PVC per pod via `volumeClaimTemplates` |
| Scaling behavior | Pods can start and stop in any order | Ordered creation and termination |
| DNS | Service-level load balancing | Stable pod DNS through a headless Service |

### When to use which

- Use a `Deployment` or `Rollout` for stateless web applications where any replica can serve any request.
- Use a `StatefulSet` when each replica must keep its own identity or data.
- Common StatefulSet workloads include PostgreSQL, MySQL, Kafka, MongoDB, RabbitMQ, Elasticsearch, and Cassandra.

### Headless Service

The chart now creates a headless Service with `clusterIP: None`:

- regular Service: `python-app-sts`
- headless Service: `python-app-sts-headless`

That headless Service gives each pod a stable DNS record in the form:

- `python-app-sts-0.python-app-sts-headless`
- `python-app-sts-1.python-app-sts-headless`
- `python-app-sts-2.python-app-sts-headless`

## 2. Helm Chart Changes

The chart in `k8s/python-app` was updated as follows:

- Added `templates/statefulset.yaml`
- Added `templates/headless-service.yaml`
- Added `workload.type: statefulset` as the default in `values.yaml`
- Kept `templates/rollout.yaml` for reference, but render it only when `workload.type=rollout`
- Switched persistence for StatefulSet mode to `volumeClaimTemplates`
- Kept the regular Service for external access

Stateful storage is configured from values:

```yaml
workload:
  type: statefulset

persistence:
  enabled: true
  mountPath: /data
  accessMode: ReadWriteOnce
  size: 100Mi
  storageClass: ""
  claimName: data-volume
```

## 3. Deployment Notes

On April 18, 2026 there was no active Kubernetes context on this machine, so I started a fresh Minikube cluster:

```bash
minikube start --driver=docker
```

The image configured in `values.yaml` pointed to `s1mphonia/devops-core-course-python-app:latest`, but that published tag did not include the repo's current `/visits` endpoint and file-backed counter. To verify Lab 15 against the checked-in app code, I built the local image into Minikube and upgraded the release to use it:

```bash
minikube image build -t python-app-lab15:local app_python
helm upgrade --install python-app-sts ./k8s/python-app \
  -f k8s/python-app/values.yaml \
  --set image.repository=python-app-lab15 \
  --set image.tag=local \
  --wait --timeout 5m
```

External access check:

```bash
$ minikube service python-app-sts --url
http://127.0.0.1:55515

$ curl -s http://127.0.0.1:55515/health
{"status":"healthy","timestamp":"2026-04-18T17:36:55.242045+00:00","uptime_seconds":202}
```

## 4. Resource Verification

Final steady-state output:

```bash
$ kubectl get po,sts,svc,pvc -o wide
NAME                   READY   STATUS    RESTARTS   AGE    IP            NODE       NOMINATED NODE   READINESS GATES
pod/python-app-sts-0   1/1     Running   0          109s   10.244.0.10   minikube   <none>           <none>
pod/python-app-sts-1   1/1     Running   0          30s    10.244.0.11   minikube   <none>           <none>
pod/python-app-sts-2   1/1     Running   0          3m8s   10.244.0.8    minikube   <none>           <none>

NAME                              READY   AGE   CONTAINERS   IMAGES
statefulset.apps/python-app-sts   3/3     7m    python-app   python-app-lab15:local

NAME                              TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE     SELECTOR
service/kubernetes                ClusterIP   10.96.0.1       <none>        443/TCP        7m35s   <none>
service/python-app-sts            NodePort    10.111.169.83   <none>        80:30080/TCP   7m      app.kubernetes.io/instance=python-app-sts,app.kubernetes.io/name=python-app
service/python-app-sts-headless   ClusterIP   None            <none>        80/TCP         7m      app.kubernetes.io/instance=python-app-sts,app.kubernetes.io/name=python-app

NAME                                                 STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE     VOLUMEMODE
persistentvolumeclaim/data-volume-python-app-sts-0   Bound    pvc-5838eb7e-ac5f-45c9-97a4-f2718b0c54e4   100Mi      RWO            standard       <unset>                 7m      Filesystem
persistentvolumeclaim/data-volume-python-app-sts-1   Bound    pvc-85d80dbe-4b19-48e4-b8f1-1ad9e7a9861f   100Mi      RWO            standard       <unset>                 6m35s   Filesystem
persistentvolumeclaim/data-volume-python-app-sts-2   Bound    pvc-64926a65-3174-4ae6-8074-d265c7056f68   100Mi      RWO            standard       <unset>                 6m23s   Filesystem
```

What this proves:

- pod names use stable ordinals
- the headless Service is present with `clusterIP: None`
- each pod got its own PVC automatically

## 5. Network Identity

DNS resolution was tested from inside `python-app-sts-0`:

```bash
$ kubectl exec python-app-sts-0 -- python -c "import socket; targets=['python-app-sts-0.python-app-sts-headless','python-app-sts-1.python-app-sts-headless','python-app-sts-2.python-app-sts-headless']; [print(f'{name} -> {socket.gethostbyname(name)}') for name in targets]"
python-app-sts-0.python-app-sts-headless -> 10.244.0.10
python-app-sts-1.python-app-sts-headless -> 10.244.0.11
python-app-sts-2.python-app-sts-headless -> 10.244.0.8
```

This confirms the StatefulSet DNS pattern:

- `<pod-name>.<headless-service-name>`

## 6. Per-Pod Storage Isolation

I accessed each pod directly through its own loopback interface so the requests would not be mixed by the Service. I intentionally generated a different number of visits on each pod.

Visit counts:

```bash
$ kubectl exec python-app-sts-0 -- python -c "import urllib.request; [urllib.request.urlopen('http://127.0.0.1:8000/').read() for _ in range(1)]; print(urllib.request.urlopen('http://127.0.0.1:8000/visits').read().decode())"
{"visits":1,"visits_file":"/data/visits"}

$ kubectl exec python-app-sts-1 -- python -c "import urllib.request; [urllib.request.urlopen('http://127.0.0.1:8000/').read() for _ in range(2)]; print(urllib.request.urlopen('http://127.0.0.1:8000/visits').read().decode())"
{"visits":2,"visits_file":"/data/visits"}

$ kubectl exec python-app-sts-2 -- python -c "import urllib.request; [urllib.request.urlopen('http://127.0.0.1:8000/').read() for _ in range(3)]; print(urllib.request.urlopen('http://127.0.0.1:8000/visits').read().decode())"
{"visits":3,"visits_file":"/data/visits"}
```

Stored files on each pod:

```bash
$ kubectl exec python-app-sts-0 -- cat /data/visits
1

$ kubectl exec python-app-sts-1 -- cat /data/visits
2

$ kubectl exec python-app-sts-2 -- cat /data/visits
3
```

This demonstrates that each pod writes to its own PVC-backed file and does not share the counter with other replicas.

## 7. Persistence After Pod Deletion

I deleted only pod `python-app-sts-1`, not the StatefulSet:

```bash
$ kubectl delete pod python-app-sts-1
pod "python-app-sts-1" deleted

$ kubectl wait --for=condition=ready pod/python-app-sts-1 --timeout=180s
pod/python-app-sts-1 condition met
```

After recreation, the same PVC was still attached:

```bash
$ kubectl get pvc data-volume-python-app-sts-1 -o wide
NAME                           STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE     VOLUMEMODE
data-volume-python-app-sts-1   Bound    pvc-85d80dbe-4b19-48e4-b8f1-1ad9e7a9861f   100Mi      RWO            standard       <unset>                 5m50s   Filesystem
```

The visit counter persisted across the restart:

```bash
$ kubectl exec python-app-sts-1 -- cat /data/visits
2

$ kubectl exec python-app-sts-1 -- python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/visits').read().decode())"
{"visits":2,"visits_file":"/data/visits"}
```

This confirms the key StatefulSet guarantee: deleting a pod does not delete its per-pod persistent volume claim or its stored data.
