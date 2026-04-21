# Lab 15 — StatefulSets & Persistent Storage

## 1. StatefulSet Overview

In this lab, the application was migrated from a stateless controller model to a **StatefulSet**. The goal was to provide stable pod identities and persistent per-pod storage for the visits counter.

### Why StatefulSet

A `Deployment` is appropriate for stateless workloads, where pods are interchangeable and do not need stable identities or dedicated storage. A `StatefulSet` is appropriate when each replica must keep:

- a stable pod name
- a stable network identity
- its own persistent volume
- ordered startup and termination behavior

### Deployment vs StatefulSet

| Feature | Deployment | StatefulSet |
|---|---|---|
| Pod names | Random suffixes | Stable ordinal names (`python-app-0`, `python-app-1`, ...) |
| Network identity | No stable per-pod DNS | Stable DNS names through headless service |
| Storage | Usually shared or external | Dedicated PVC per pod via `volumeClaimTemplates` |
| Startup/scaling order | Unordered | Ordered |
| Typical use cases | Stateless web apps, APIs | Databases, queues, replicated stateful services |

### Headless Service

A headless service was created using:

```yaml
clusterIP: None
```

This allows Kubernetes DNS to create records for each pod in the StatefulSet, so pods can be reached directly by stable names such as:

```text
python-app-1.python-app-headless.default.svc.cluster.local
```

---

## 2. Resource Verification

The chart was deployed successfully and the StatefulSet created three pods and three PVCs.

### Command

```bash
kubectl get po,sts,svc,pvc
```

### Output

```text
NAME                                        READY   STATUS    RESTARTS        AGE
pod/python-app-0                            1/1     Running   0               2m38s
pod/python-app-1                            1/1     Running   0               2m25s
pod/python-app-2                            1/1     Running   0               2m18s
pod/vault-0                                 1/1     Running   3 (3m45s ago)   13d
pod/vault-agent-injector-848dd747d7-h2pmn   1/1     Running   3 (3m45s ago)   13d

NAME                          READY   AGE
statefulset.apps/python-app   3/3     2m38s
statefulset.apps/vault        1/1     13d

NAME                               TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)             AGE
service/kubernetes                 ClusterIP   10.96.0.1        <none>        443/TCP             27d
service/python-app                 NodePort    10.111.193.121   <none>        80:30080/TCP        2m38s
service/python-app-headless        ClusterIP   None             <none>        80/TCP              2m38s
service/vault                      ClusterIP   10.110.135.153   <none>        8200/TCP,8201/TCP   13d
service/vault-agent-injector-svc   ClusterIP   10.105.78.81     <none>        443/TCP             13d
service/vault-internal             ClusterIP   None             <none>        8200/TCP,8201/TCP   13d

NAME                                      STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/data-python-app-0   Bound    pvc-8e4c76bf-5306-4c64-888b-f921f1d126b7   100Mi      RWO            standard       <unset>                 2m38s
persistentvolumeclaim/data-python-app-1   Bound    pvc-fa9568a4-3c82-43fe-bf81-de11c7bf0a1c   100Mi      RWO            standard       <unset>                 2m25s
persistentvolumeclaim/data-python-app-2   Bound    pvc-833ffc9b-d44e-4833-932a-28f1450893d4   100Mi      RWO            standard       <unset>                 2m18s
```

### Verification summary

- `python-app` StatefulSet is ready with **3/3 replicas**.
- Pod names follow the stable ordinal pattern:
  - `python-app-0`
  - `python-app-1`
  - `python-app-2`
- A headless service exists:
  - `python-app-headless`
- A regular service exists for client access:
  - `python-app`
- Each pod received its own dedicated PVC:
  - `data-python-app-0`
  - `data-python-app-1`
  - `data-python-app-2`

---

## 3. Network Identity

Stable DNS names were verified from inside the cluster.

### Commands

```bash
getent hosts python-app-1.python-app-headless
getent hosts python-app-2.python-app-headless
```

### Output

```text
10.244.0.146    python-app-1.python-app-headless.default.svc.cluster.local
10.244.0.147    python-app-2.python-app-headless.default.svc.cluster.local
```

### Conclusion

The headless service correctly provides per-pod DNS resolution. This confirms the stable network identity guarantee of StatefulSets.

---

## 4. Per-Pod Storage Evidence

The application increments a visit counter stored in `/data/visits`. Since `/data` is backed by a dedicated PVC per pod, each replica should maintain its own independent counter.

### Initial per-pod checks

```bash
curl localhost:8080/
curl localhost:8080/visits

curl localhost:8081/
curl localhost:8081/visits

curl localhost:8082/
curl localhost:8082/visits
```

Each pod responded with its own hostname:

- `python-app-0`
- `python-app-1`
- `python-app-2`

and each one used:

```text
"file":"/data/visits"
```

### Isolation proof

Extra requests were sent only to `python-app-0`:

```bash
curl localhost:8080/
curl localhost:8080/
curl localhost:8080/visits

curl localhost:8081/visits
curl localhost:8082/visits
```

### Output

```text
python-app-0 -> {"visits":3,"file":"/data/visits"}
python-app-1 -> {"visits":1,"file":"/data/visits"}
python-app-2 -> {"visits":1,"file":"/data/visits"}
```

### Conclusion

The counter increased only on `python-app-0`, while `python-app-1` and `python-app-2` kept their previous values. This proves that each pod has isolated persistent storage.

---

## 5. Persistence Test

The next step was to verify that data survives pod deletion.

### Value before deletion

```bash
kubectl exec python-app-0 -- cat /data/visits
```

### Output

```text
3
```

### Pod deletion

```bash
kubectl delete pod python-app-0
```

Kubernetes recreated the pod automatically because it is managed by a StatefulSet.

### Value after recreation

```bash
kubectl exec python-app-0 -- cat /data/visits
```

### Output

```text
3
```

### Conclusion

The visit counter remained unchanged after pod deletion and recreation. This confirms that the data is stored on the pod’s persistent volume and survives container and pod restarts.

---

## 6. Final Result

The lab objectives were completed successfully:

- StatefulSet guarantees were studied and documented
- The application was deployed as a StatefulSet
- A headless service was created and verified
- Per-pod PVCs were created automatically using `volumeClaimTemplates`
- Stable DNS identities were verified
- Per-pod storage isolation was demonstrated
- Persistence after pod deletion was demonstrated

The bonus task on update strategies was intentionally not implemented.
