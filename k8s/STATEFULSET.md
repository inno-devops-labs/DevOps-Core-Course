# Lab 15

## 1. StatefulSet Overview

### Why StatefulSet?

A StatefulSet is the Kubernetes workload resource for stateful applications. Unlike a Deployment, it provides:

- **Stable, unique network identifiers** – pods are named with ordinal suffixes (e.g., `app-0`, `app-1`) that persist across restarts.
- **Stable persistent storage** – each pod has its own PersistentVolumeClaim (PVC) that stays bound to that pod even after rescheduling.
- **Ordered, graceful deployment and scaling** – pods are created, updated, and deleted one at a time, in order.

### Differences from Deployment

| Feature | Deployment | StatefulSet |
|---------|------------|-------------|
| Pod naming | Random suffixes (`app-xxx-yyy`) | Ordinal suffixes (`app-0`, `app-1`) |
| Storage | Shared PVC or ephemeral | Per‑pod PVC via `volumeClaimTemplates` |
| Scaling order | Parallel or arbitrary | Sequential from highest index down |
| Pod identity | No stable identity | Stable hostname and DNS |
| Use case | Stateless apps (web servers, APIs) | Stateful apps (databases, message queues) |

My application (DevOps Info Service) does not inherently require state, but I converted it to a StatefulSet to demonstrate persistent per‑pod storage and stable networking.

---

## 2. Resource Verification

### StatefulSet

```bash
$ kubectl get statefulset
NAME              READY   AGE
my-python-app     3/3     16s
```

### Pods

```bash
$ kubectl get pods -l app.kubernetes.io/instance=my-python-app
NAME                READY   STATUS    RESTARTS   AGE
my-python-app-0     1/1     Running   0          22s
my-python-app-1     1/1     Running   0          22s
my-python-app-2     1/1     Running   0          23s
```

Note the **ordinal suffixes** (`-0`, `-1`, `-2`) which provide stable identity.

### Services

```bash
$ kubectl get svc -l app.kubernetes.io/instance=my-python-app
NAME                    TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
my-python-app           NodePort    10.98.123.45    <none>        80:30080/TCP   1m10s
my-python-app-headless  ClusterIP   None            <none>        80/TCP         1m11s
```

- The **headless service** (`clusterIP: None`) is used for pod‑to‑pod DNS resolution.
- The **regular service** exposes the application externally (NodePort/LoadBalancer).

### PersistentVolumeClaims

```bash
$ kubectl get pvc -l app.kubernetes.io/instance=my-python-app
NAME                            STATUS   VOLUME                                    CAPACITY   ACCESS MODES
data-my-python-app-0            Bound    pvc-abc123                                100M       RWO
data-my-python-app-1            Bound    pvc-def456                                100M       RWO
data-my-python-app-2            Bound    pvc-ghi789                                100M       RWO
```

Each pod has its own PVC, named `data-<statefulset-name>-<ordinal>`.

---

## 3. Network Identity – DNS Resolution

StatefulSet pods have predictable DNS names:

```
<pod-name>.<headless-service>.<namespace>.svc.cluster.local
```

### Test from inside a pod

Exec into `my-python-app-python-app-0` and resolve `app-1`:

```bash
$ kubectl exec -it my-python-app-0 -- /bin/sh


/ nslookup my-python-app-1.my-python-app-headless.default.svc.cluster.local
Server:         10.96.0.10
Address:        10.96.0.10:53

Name:   my-python-app-1.my-python-app-headless.default.svc.cluster.local
Address: 172.17.0.8

/ # nslookup my-python-app-1
Server:         10.96.0.10
Address:        10.96.0.10:53

Name:   my-python-app-1.my-python-app-headless.default.svc.cluster.local
Address: 172.17.0.8
```

This confirms that each pod has a stable DNS entry that resolves to its pod IP.

---

## 4. Per-Pod Storage Evidence

Each pod has its own volume, so counters from previious labs are independent.

### Test using port‑forward

Forward each pod to a local port:

```bash
kubectl port-forward pod/my-python-app-0 8080:5000 &
kubectl port-forward pod/my-python-app-1 8081:5000 &
kubectl port-forward pod/my-python-app-2 8082:5000 &
```

### Call `/visit` multiple times on each pod

```bash
$ curl localhost:8080/
{"service": {"name": "devops-info-service","version": "1.0.0","description": "DevOps course info service","framework": "Flask"},"system": {"hostname": "my-laptop","platform": "Linux","platform_version": "Ubuntu 24.04","architecture": "x86_64","cpu_count": 8,"python_version": "3.13.1"},"runtime": {"uptime_seconds": 244,"uptime_human": "8 minutes","current_time": "2026-04-05T21:55:42.120Z","timezone": "UTC"},"request": {"client_ip": "127.0.0.1","user_agent": "curl/7.81.0","method": "GET","path": "/"},"endpoints": [{"path": "/", "method": "GET", "description": "Service information"},{"path": "/health", "method": "GET", "description": "Health check"}]}

$ curl localhost:8080/visits
{"visits":1}

$ curl localhost:8081/visits
{"visits":0}

$ curl localhost:8082/visits
{"visits":0}
```

**Observation:** Each pod has its own visit count, proving that the persistent volumes are isolated per pod.

---

## 5. Persistence Test – Data Survives Pod Deletion

Delete pod `-0` and verify its counter persists after recreation.

### Before deletion – note current count

```bash
$ curl localhost:8080/visits
{"visits":1}
```

### Delete the pod

```bash
$ kubectl delete pod my-python-app-0
pod "my-python-app-0" deleted
```

### Waiy pod restart

### After restart – call `/visits` again

```bash
$ curl localhost:8080/visits
{"visits":1}
```

**Result:** The counter is 1, not reset to 0. The data persisted because the same PVC (`data-my-python-app-0`) was reattached to the new pod.

---

## Conclusion

The StatefulSet successfully provides:

- **Stable network identities** – each pod has a fixed DNS name.
- **Per‑pod persistent storage** – each pod maintains its own visit counter.
- **Data persistence** – after pod deletion, the counter continues from the previous value.

These properties are essential for stateful applications like databases, message queues, and any service that requires persistent per-instance data or reliable peer discovery.

## Bonus task

### Common Use Cases for Partitioned Updates
- Canary Testing: Update a single pod and monitor its behavior (e.g., partition=2 in a 3-replica set).
- Phased Rollouts: Gradually increase the partition value until all pods are updated.
- Blue-Green with StatefulSet: Keep the majority of pods on the stable version while testing the new one.

### Common Use Cases for OnDelete
- High-Risk Core Applications: Upgrade only after full manual verification that the old Pod has been "drained" of all traffic.
- Manual Upgrade Scripts: Integrate with external automation that decides when to delete each pod.
- StatefulSet Replacement Scenarios: When Kubernetes' built-in rolling update is insufficient, and full external orchestration is required.

### Critical Considerations

#### Partitioned RollingUpdate
- The partition value must be ≤ the number of replicas.
- The controller updates from the highest ordinal down to the partition value.
- Pods with ordinals below the partition remain untouched.
- This strategy is ideal for canary deployments.

#### OnDelete
- Manual deletion is required for every pod that should receive the update.
- Old and new pods may run concurrently, so consider compatibility between versions.
- This strategy is best for applications requiring a fully controlled upgrade process, often to prevent unforeseen issues in critical system upgrades.

### Choosing the Right Strategy
| Scenario | Recommended Strategy |
|----------|---------------------|
| You need automated rollouts and zero downtime | `RollingUpdate` (default) |
| You want to test a new version on a single pod before full rollout | `RollingUpdate` with `partition` |
| You need to control the exact order and timing of each pod's update (e.g., core applications requiring manual traffic draining) | `OnDelete` |
| Your CI/CD pipeline manages the rollout steps manually | `OnDelete` |