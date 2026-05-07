# Lab 15 — StatefulSet documentation

## 1. StatefulSet overview

**Why StatefulSet:** workloads that need **stable pod names and DNS**, **ordered** scale and rollouts, and **dedicated persistent volume per replica** (via `volumeClaimTemplates`) instead of one shared PVC for all pods.

**Deployment vs StatefulSet:**

| | Deployment | StatefulSet |
|---|------------|-------------|
| Pod identity | Random pod name suffix | Fixed ordinals (`name-0`, `name-1`, …) |
| Storage | Often one PVC or `emptyDir` | Per-pod PVC from templates |
| Scaling | Unordered | Ordered by default |
| Networking | Via Service endpoints | Headless Service (`clusterIP: None`) + pod DNS |

**When to use which:** **Deployment** — stateless HTTP APIs, workers. **StatefulSet** — databases, Kafka, Elasticsearch, and similar systems where each replica must keep **its own data** and **stable address**.

**Headless service:** `clusterIP: None` does not provide a single virtual IP for the set. With a selector matching the StatefulSet pods, Kubernetes DNS exposes records so each pod is reachable as  
`<pod-name>.<headless-service-name>.<namespace>.svc.cluster.local`  
(for example: `devops-info-service-0.devops-info-service-headless.default.svc.cluster.local`).

---

## 2. Resource verification

Command:

```bash
kubectl get po,sts,svc,pvc -n default -l app.kubernetes.io/instance=lab15
```

Output:

```
NAME                        READY   STATUS    RESTARTS   AGE
pod/devops-info-service-0   1/1     Running   0          6m19s
pod/devops-info-service-1   1/1     Running   0          6m12s

NAME                                   READY   AGE
statefulset.apps/devops-info-service   2/2     6m19s

NAME                                   TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service            NodePort    10.110.215.189   <none>        80:32756/TCP   6m19s
service/devops-info-service-headless   ClusterIP   None             <none>        80/TCP         6m19s

NAME                                               STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/data-devops-info-service-0   Bound    pvc-9f510e37-a729-4eb8-8a16-7f977387680d   100Mi      RWO            standard       <unset>                 6m19s
persistentvolumeclaim/data-devops-info-service-1   Bound    pvc-dda5b136-1be6-469d-9452-f2d78926c48f   100Mi      RWO            standard       <unset>                 6m12s
```

---

## 3. Network identity (DNS)

`nslookup` is not installed in the application image; resolution was checked with **`getent hosts`**.

Command:

```bash
kubectl exec -it devops-info-service-0 -n default -- getent hosts devops-info-service-1.devops-info-service-headless.default.svc.cluster.local
```

DNS naming pattern: `<pod>.<headless-service>.<namespace>.svc.cluster.local`.

Output:

```
10.244.0.136    devops-info-service-1.devops-info-service-headless.default.svc.cluster.local
```

---

## 4. Per-pod storage (visit counter isolation)

**Image:** The workload uses a local build **from `app_python/`** (`devops-info-service:lab12`), loaded into **minikube** (`eval $(minikube docker-env); docker build ...`) and deployed with Helm:

`helm upgrade --install lab15 . -n default -f values-lab15-statefulset.yaml --set image.repository=devops-info-service --set image.tag=lab12 --set image.pullPolicy=Never`

Commands (two terminals for port-forward, one for `curl` / `kubectl exec`):

```bash
kubectl port-forward -n default pod/devops-info-service-0 8080:5000
kubectl port-forward -n default pod/devops-info-service-1 8081:5000
kubectl rollout status statefulset/devops-info-service -n default
```

```bash
kubectl exec -n default devops-info-service-0 -- curl -s http://127.0.0.1:5000/visits
curl -s http://127.0.0.1:8080/visits
curl -s http://127.0.0.1:8081/visits
curl -s http://127.0.0.1:8080/
curl -s http://127.0.0.1:8081/
curl -s http://127.0.0.1:8080/visits
curl -s http://127.0.0.1:8081/visits
kubectl exec -n default devops-info-service-0 -- cat /data/visits
kubectl exec -n default devops-info-service-1 -- cat /data/visits
```

**Evidence — HTTP:** Initial checks:

```text
{"visits":0,"file":"/data/visits"}
```

After `GET /` on **8080** (pod-0) and **8081** (pod-1), JSON on `/` shows `system.hostname` **`devops-info-service-0`** vs **`devops-info-service-1`** and `visits.total` **1** on each pod. Final `GET /visits`:

```text
{"visits":1,"file":"/data/visits"}
```

(on both ports in this run — expected after **one** root hit per pod).

**Evidence — files on disk (separate PVC per pod):**

```text
# devops-info-service-0
1
# devops-info-service-1
1
```

Each pod reads **its own** `/data/visits` on **its own** PVC (`data-devops-info-service-0` / `...-1`). With asymmetric load (e.g. five `curl`/`GET /` to **8080** only), counts on the two pods **diverge**; here both show `1` because traffic was symmetric.

---

## 5. Persistence after pod deletion

Commands:

```bash
kubectl exec -n default devops-info-service-0 -- cat /data/visits
kubectl delete pod devops-info-service-0 -n default
kubectl wait --for=condition=ready pod/devops-info-service-0 -n default --timeout=120s
kubectl exec -n default devops-info-service-0 -- cat /data/visits
```

**Output:** Counter **before** delete: **`1`**. Pod recreated by StatefulSet; same ordinal **`devops-info-service-0`** reattached to **`data-devops-info-service-0`**. Counter **after** delete: **`1`** (unchanged — persistence OK).

```text
1
pod "devops-info-service-0" deleted from default namespace
pod/devops-info-service-0 condition met
1
```
