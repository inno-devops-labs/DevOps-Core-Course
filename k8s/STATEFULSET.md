# Lab 15 — StatefulSets & Persistent Storage 

---

## 1. StatefulSet overview 

### Why a StatefulSet

StatefulSets are for applications that need **stable identity**, **ordered lifecycle**, and **dedicated persistent storage per replica**. The controller gives:

1. **Stable, unique network identifiers** — Pods are named `<statefulset-name>-0`, `-1`, `-2`, … and keep the same identity across reschedules.
2. **Stable storage** — With `volumeClaimTemplates`, each ordinal gets its own PVC (e.g. `data-<sts-name>-0`) that is reattached to the same ordinal after delete/recreate.
3. **Ordered deployment and scaling** — Default `OrderedReady` starts and terminates pods in order (highest index down on scale-in).

### Deployment vs StatefulSet

| Aspect | Deployment | StatefulSet |
|--------|------------|-------------|
| Pod names | Random suffix | Stable ordinal (`app-0`, `app-1`) |
| PVC pattern | Often one shared PVC or none | Per-pod PVCs via `volumeClaimTemplates` |
| Scaling order | Any order | Typically ordered (0 → 1 → 2) |
| Stable DNS | Via Service only | Per-pod records when using a headless Service |

**Use a Deployment** for stateless HTTP APIs, workers, and anything that does not require stable pod hostname or dedicated disk per replica.

**Use a StatefulSet** for databases, Kafka, ZooKeeper-style coordination, or any app that stores identity-specific data on disk and expects a stable hostname.

### Headless Service (`clusterIP: None`)

A headless Service has **no ClusterIP**. DNS returns **A/AAAA records for each ready Pod** (when `publishNotReadyAddresses` is false; with `true`, not-ready pods are included too).

For a StatefulSet `myapp` and headless Service `myapp-headless` in namespace `prod`, pod `myapp-1` is typically reachable as: `myapp-1.myapp-headless.prod.svc.cluster.local`

The StatefulSet’s `spec.serviceName` must match the headless Service so the control plane wires identity and DNS consistently.

---

## 2. Chart changes (Task 2)

Files added or updated:

| File | Purpose |
|------|---------|
| `templates/statefulset.yaml` | StatefulSet with `serviceName`, pod template aligned with the app, `volumeClaimTemplates` for `/data` |
| `templates/service-headless.yaml` | `clusterIP: None`, same selectors as the main Service |
| `templates/_helpers.tpl` | `devops-info-service.headlessServiceName` helper |
| `values.yaml` | `statefulset.enabled` and `statefulset.podManagementPolicy` |
| `values-statefulset.yaml` | Lab profile: `statefulset.enabled: true`, `rollout.enabled: false`, `replicaCount: 3` |
| `templates/deployment.yaml` | Renders only if **neither** Rollout nor StatefulSet mode |
| `templates/rollout.yaml` | Renders only if Rollout enabled **and** StatefulSet disabled |
| `templates/pvc.yaml` | Standalone PVC only when **not** using StatefulSet (per-pod PVCs come from the StatefulSet) |

The main **NodePort/ClusterIP Service** is unchanged for external access; the headless Service is for **in-cluster pod-to-pod** DNS.

### Install

```bash
kubectl create namespace lab15 --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install lab15 k8s/devops-info-service \
  --namespace lab15 \
  -f k8s/devops-info-service/values-statefulset.yaml
```

**`GET /visits`:** The default chart image may not include Lab 12’s visits endpoint. Build from `app_python/`, load into minikube, then upgrade with a local tag and **`image.pullPolicy: Never`**:

```bash
docker build -t devops-info-service:lab15 app_python
minikube image load devops-info-service:lab15
helm upgrade --install lab15 k8s/devops-info-service \
  --namespace lab15 \
  -f k8s/devops-info-service/values-statefulset.yaml \
  --set service.nodePort=30085 \
  --set image.repository=devops-info-service \
  --set image.tag=lab15 \
  --set image.pullPolicy=Never
```

### Helm lint 

```text
$ helm lint k8s/devops-info-service -f k8s/devops-info-service/values-statefulset.yaml
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### Rendered StatefulSet excerpt (`helm template`, captured)

```bash
helm template lab15 k8s/devops-info-service \
  -f k8s/devops-info-service/values-statefulset.yaml \
  --show-only templates/statefulset.yaml
```

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: lab15-devops-info-service
spec:
  serviceName: lab15-devops-info-service-headless
  replicas: 3
  podManagementPolicy: OrderedReady
  # ... pod template with volumeMount name: data ...
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes:
          - ReadWriteOnce
        resources:
          requests:
            storage: 100Mi
```

Headless Service (same render):

```yaml
spec:
  clusterIP: None
  publishNotReadyAddresses: true
  selector:
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: lab15
```

---

## 3. Resource verification (Task 4)

Wait until the StatefulSet finishes its ordered rollout, then list objects:

```bash
kubectl rollout status statefulset/lab15-devops-info-service -n lab15
kubectl get po,sts,svc,pvc -n lab15
```

### Captured output 

`kubectl rollout status`:

```text
partitioned roll out complete: 3 new pods have been updated...
```

`kubectl get po,sts,svc,pvc -n lab15`:

```text
NAME                              READY   STATUS    RESTARTS   AGE
pod/lab15-devops-info-service-0   1/1     Running   0          38s
pod/lab15-devops-info-service-1   1/1     Running   0          65s
pod/lab15-devops-info-service-2   1/1     Running   0          96s

NAME                                         READY   AGE
statefulset.apps/lab15-devops-info-service   3/3     6m55s

NAME                                           TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/lab15-devops-info-service              NodePort    10.103.24.247  <none>        80:30085/TCP   6m55s
service/lab15-devops-info-service-headless     ClusterIP   None           <none>        80/TCP         6m55s

NAME                                                        STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/data-lab15-devops-info-service-0      Bound    pvc-06c298e0-eed0-4ecb-af81-bb51a627fddc   100Mi      RWO            standard       6m55s
persistentvolumeclaim/data-lab15-devops-info-service-1      Bound    pvc-33f0d6b6-d948-4ea0-ac80-244012c80182   100Mi      RWO            standard       6m31s
persistentvolumeclaim/data-lab15-devops-info-service-2      Bound    pvc-7267784d-69dc-4fa0-8bdd-710ebd5c2850   100Mi      RWO            standard       6m3s
```

Ordinal pod names (`…-0`, `…-1`, `…-2`), one StatefulSet, two Services (NodePort **30085** was used because **30080** was already taken elsewhere), three **Bound** PVCs `data-<statefulset>-<ordinal>`.

---

## 4. Network identity - DNS 

### Naming pattern

For StatefulSet `<sts>` and headless Service `<headless>` in namespace `<ns>`:

`<pod-hostname>.<headless-service>.<namespace>.svc.cluster.local`

Short form inside the same namespace: `<pod-hostname>.<headless-service>`.

### Commands to run

**Non-interactive DNS check** (BusyBox pod; FQDN form):

```bash
kubectl run -n lab15 dns-lab15-verify --rm --attach --restart=Never \
  --image=docker.io/busybox:1.36 \
  --overrides='{"spec":{"activeDeadlineSeconds":120}}' -- \
  nslookup lab15-devops-info-service-1.lab15-devops-info-service-headless.lab15.svc.cluster.local
```

### Captured `nslookup` output 

```text
Server:		10.96.0.10
Address:	10.96.0.10:53


Name:	lab15-devops-info-service-1.lab15-devops-info-service-headless.lab15.svc.cluster.local
Address: 10.244.0.110

pod "dns-lab15-verify" deleted from lab15 namespace
```

The **Address** matches pod `lab15-devops-info-service-1`’s Pod IP at the time of the test, confirming the headless Service DNS pattern.

---

## 5. Per-pod storage isolation 

The app increments the counter on `GET /` and exposes `GET /visits` (read-only). With **three replicas** and **three PVCs**, each pod has its **own** `/data/visits`.

Hit **`/`** a different number of times per pod, then read `/visits` via port-forward to **each** pod (not only via the Service, which load-balances):

```bash
kubectl port-forward -n lab15 pod/lab15-devops-info-service-0 8080:5000 &
kubectl port-forward -n lab15 pod/lab15-devops-info-service-1 8081:5000 &
curl -sS http://127.0.0.1:8080/ >/dev/null
curl -sS http://127.0.0.1:8080/ >/dev/null
curl -sS http://127.0.0.1:8081/ >/dev/null
curl -sS http://127.0.0.1:8080/visits
curl -sS http://127.0.0.1:8081/visits
```

### Captured `curl` output 

After two `GET /` on pod-0 and one `GET /` on pod-1 (same logic; local ports **18080** / **18081** were used in the capture run):

```text
=== After traffic: pod-0 (two GET /) ===
{"visits":2,"path":"/data/visits"}
=== After traffic: pod-1 (one GET /) ===
{"visits":1,"path":"/data/visits"}
```

Different `visits` values show each pod’s **own** PVC-backed `/data/visits`.

---

## 6. Persistence after pod delete 

Record the on-disk value, delete **only the Pod** (not the StatefulSet), wait for recreation, confirm the file matches.

```bash
kubectl exec -n lab15 lab15-devops-info-service-0 -- cat /data/visits
kubectl delete pod -n lab15 lab15-devops-info-service-0
kubectl wait -n lab15 pod/lab15-devops-info-service-0 --for=condition=Ready --timeout=120s
kubectl exec -n lab15 lab15-devops-info-service-0 -- cat /data/visits
```

**Captured persistence check** (minikube): counter on disk was **2** before deleting only pod `lab15-devops-info-service-0`, and **2** again after the pod was recreated and became Ready (same PVC `data-lab15-devops-info-service-0`).

```text
=== Before delete ===
2
pod "lab15-devops-info-service-0" deleted from lab15 namespace
pod/lab15-devops-info-service-0 condition met
=== After pod-0 recreated ===
2
```


The replacement pod for ordinal **0** reuses PVC **`data-lab15-devops-info-service-0`**, so the on-disk counter is preserved.

---

## 8. Switching back to Rollouts

If both `rollout.enabled` and `statefulset.enabled` are `true`, the chart **does not render the Rollout** and installs the **StatefulSet** only (StatefulSet takes precedence).

For progressive delivery again, use default `values.yaml` (`rollout.enabled: true`, `statefulset.enabled: false`) or install without `values-statefulset.yaml`, and set `statefulset.enabled: false` explicitly if you toggled it on.

