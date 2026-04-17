# StatefulSet and Persistent Storage (Lab 15)

## 1. StatefulSet concepts 

### Guarantees 

| Guarantee         | Meaning                                                                                                                  |
|-------------------|--------------------------------------------------------------------------------------------------------------------------|
| Stable network ID | Each pod is reachable at `<sts-name>-<ordinal>.<headless-svc>.<ns>.svc.cluster.local`.                                   |
| Stable storage    | `volumeClaimTemplates` bind one PVC per pod identity (ordinal); data follows the pod name.                               |
| Ordered ops       | Default `OrderedReady`: create/scale/delete pods in index order; optional `Parallel` in chart via `podManagementPolicy`. |

### Deployment vs StatefulSet

| Aspect        | Deployment / Rollout                   | StatefulSet                                        |
|---------------|----------------------------------------|----------------------------------------------------|
| Pod naming    | Random suffix                          | Fixed ordinal (`app-0`, `app-1`, …)                |
| Storage       | Often one shared PVC or none           | Per-pod PVC from `volumeClaimTemplates`            |
| Scaling order | Any                                    | Ordered (or parallel if configured)                |
| Use when      | Stateless HTTP APIs, canary/blue-green | Databases, brokers, nodes needing stable ID + disk |

### Headless Service (`clusterIP: None`)

- No single cluster IP; Endpoints expose **per-pod** records.
- DNS (CoreDNS): `pod-name` as a hostname under the headless Service FQDN resolves to that pod’s IP(s).
- This chart adds `service-headless.yaml` (`*-headless`) and sets `spec.serviceName` on the StatefulSet to that Service name.

---

## Implementation

### Container image
Chart files:

| File                                                      | Role                                                                                                 |
|-----------------------------------------------------------|------------------------------------------------------------------------------------------------------|
| `k8s/devops-info-service/templates/statefulset.yaml`      | StatefulSet with `volumeClaimTemplates` (`data`), same pod spec as Rollout (env, probes, mounts).    |
| `k8s/devops-info-service/templates/service-headless.yaml` | Headless Service (`clusterIP: None`) for stable DNS.                                                 |
| `k8s/devops-info-service/templates/service.yaml`          | Unchanged external/service IP access (ClusterIP/NodePort/LB).                                        |
| `k8s/devops-info-service/templates/rollout.yaml`          | Rendered only when `statefulset.enabled=false` (kept for Lab 14).                                    |
| `k8s/devops-info-service/templates/pvc.yaml`              | Rendered only when `persistence.enabled` and **not** StatefulSet (shared PVC path for Rollout mode). |

Values: `statefulset.enabled` (default `true`), `statefulset.updateStrategy`, `persistence.size` / `persistence.storageClass`.

Example install (cluster used for evidence: Minikube, namespace `lab15`; ClusterIP chosen to avoid NodePort collisions with other workloads):

```bash
helm upgrade --install lab15-ss ./k8s/devops-info-service -n lab15 --create-namespace \
  --set service.type=ClusterIP
```

---

## 2. Resource verification 

Commands:

```bash
kubectl get po,sts,svc,pvc -n lab15
```

Output:

```
NAME                                 READY   STATUS    RESTARTS   AGE
pod/lab15-ss-devops-info-service-0   1/1     Running   0          12s
pod/lab15-ss-devops-info-service-1   1/1     Running   0          54s
pod/lab15-ss-devops-info-service-2   1/1     Running   0          97s

NAME                                            READY   AGE
statefulset.apps/lab15-ss-devops-info-service   3/3     29m

NAME                                            TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
service/lab15-ss-devops-info-service            ClusterIP   10.107.239.67   <none>        80/TCP    29m
service/lab15-ss-devops-info-service-headless   ClusterIP   None            <none>        80/TCP    29m

NAME                                                        STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/data-lab15-ss-devops-info-service-0   Bound    pvc-67305bd5-331c-4077-aad6-b4c7465c3434   100Mi      RWO            standard       <unset>                 29m
persistentvolumeclaim/data-lab15-ss-devops-info-service-1   Bound    pvc-45abba23-93a2-436b-8d3d-59637eed05ee   100Mi      RWO            standard       <unset>                 29m
persistentvolumeclaim/data-lab15-ss-devops-info-service-2   Bound    pvc-6cb40aa4-a300-4019-9f24-84419ece9ee9   100Mi      RWO            standard       <unset>                 29m
```

---

## 3. Network identity — DNS

**Pattern:** `<statefulset-pod>.<headless-service>.<namespace>.svc.cluster.local`

Commands:

```bash
kubectl exec -n lab15 lab15-ss-devops-info-service-0 -- getent hosts \
  lab15-ss-devops-info-service-1.lab15-ss-devops-info-service-headless.lab15.svc.cluster.local
```

Output:

```
10.244.0.114    lab15-ss-devops-info-service-1.lab15-ss-devops-info-service-headless.lab15.svc.cluster.local
```

**Cross-pod HTTP reachability** (from `lab15-ss-devops-info-service-0`, port `5000` = `containerPort`):

```bash
kubectl exec -n lab15 lab15-ss-devops-info-service-0 -- python3 -c "
import urllib.request
h='lab15-ss-devops-info-service-headless.lab15.svc.cluster.local'
for i in range(3):
  u=f'http://lab15-ss-devops-info-service-{i}.{h}:5000/health'
  print(i, urllib.request.urlopen(u).status)
"
```

Output:

```
0 200
1 200
2 200
```

---

## 4. Per-pod storage isolation

The Helm chart mounts persistent storage at `/data` with `VISITS_FILE=/data/visits`. The published image exposes **`GET /visits`** (JSON: `visits`, `storage_file`) and increments the counter on **`GET /`**.

Commands (from `lab15-ss-devops-info-service-0`, targeting each ordinal over the **headless** DNS name; counters reset to `0` on disk first):

```bash
NS=lab15
STS=lab15-ss-devops-info-service
H="${STS}-headless.${NS}.svc.cluster.local"
for i in 0 1 2; do kubectl exec -n "$NS" "${STS}-$i" -- sh -c 'echo 0 > /data/visits'; done

kubectl exec -n "$NS" "${STS}-0" -- python3 -c "
import json, urllib.request
h = 'lab15-ss-devops-info-service-headless.lab15.svc.cluster.local'
STS = 'lab15-ss-devops-info-service'
def url(i, path): return f'http://{STS}-{i}.{h}:5000{path}'
for _ in range(5): urllib.request.urlopen(url(0, '/'))
for _ in range(2): urllib.request.urlopen(url(1, '/'))
for _ in range(3): urllib.request.urlopen(url(2, '/'))
for i in range(3):
    d = json.load(urllib.request.urlopen(url(i, '/visits')))
    print('pod-%d' % i, d)
"
```

Output:

```
pod-0 {'storage_file': '/data/visits', 'visits': 5}
pod-1 {'storage_file': '/data/visits', 'visits': 2}
pod-2 {'storage_file': '/data/visits', 'visits': 3}
```

Each pod maintains its own counter on its own PVC.

---

## 5. Persistence after pod delete

Same counter as in section 4 (`visits: 5` on `pod-0`), then delete **only** the pod (not the StatefulSet).

Commands:

```bash
NS=lab15
STS=lab15-ss-devops-info-service
H="${STS}-headless.${NS}.svc.cluster.local"
kubectl exec -n "$NS" "${STS}-0" -- python3 -c "import json,urllib.request; u='http://${STS}-0.${H}:5000/visits'; print('before', json.load(urllib.request.urlopen(u)))"
kubectl delete pod -n "$NS" "${STS}-0" --wait=true
kubectl wait -n "$NS" "pod/${STS}-0" --for=condition=ready --timeout=120s
kubectl exec -n "$NS" "${STS}-0" -- python3 -c "import json,urllib.request; u='http://${STS}-0.${H}:5000/visits'; print('after', json.load(urllib.request.urlopen(u)))"
```

Output:

```
before {'storage_file': '/data/visits', 'visits': 5}
pod "lab15-ss-devops-info-service-0" deleted
pod/lab15-ss-devops-info-service-0 condition met
after {'storage_file': '/data/visits', 'visits': 5}
```

The StatefulSet recreated `lab15-ss-devops-info-service-0` and reattached PVC `data-lab15-ss-devops-info-service-0`; the visit count persisted.

---

## 6. Bonus — update strategies

### 6.1 Partitioned rolling update

With `updateStrategy.type=RollingUpdate` and `rollingUpdate.partition=N`, only pods with **ordinal ≥ N** receive the new revision first.

Commands used:

```bash
helm upgrade lab15-ss ./k8s/devops-info-service -n lab15 \
  --set service.type=ClusterIP \
  --set image.tag=latest \
  --set statefulset.updateStrategy.rollingUpdate.partition=2
kubectl get pods -n lab15 -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].image}{"\n"}{end}'
```

Output:

```
lab15-ss-devops-info-service-0        gghost1/devops-lab-app-python:1.0.0
lab15-ss-devops-info-service-1        gghost1/devops-lab-app-python:1.0.0
lab15-ss-devops-info-service-2        gghost1/devops-lab-app-python:latest
```

Ordinals `0` and `1` stayed on `1.0.0`; ordinal `2` moved to `latest`, consistent with `partition: 2`. (Tags `1.0.0` and `latest` refer to the same image build; rolling newer ordinals first is visible as different **tag strings** on the pod specs.)

### 6.2 `OnDelete` strategy

Set in values (or `--set`):

```yaml
statefulset:
  updateStrategy:
    type: OnDelete
```

Rendered manifest contains only `type: OnDelete` (no `rollingUpdate`). New pod template applies **only after** a pod is deleted manually.

**Use cases:** strict operator-controlled rollout, risky migrations where you must verify each member before restarting the next, or pairing with external orchestration.
