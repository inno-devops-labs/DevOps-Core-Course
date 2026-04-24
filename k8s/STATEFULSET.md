# Lab 15 - StatefulSet Implementation

## 1) StatefulSet Overview

StatefulSet is used here because the app stores visit counters in `/data/visits`, so each replica needs:

- Stable identity (`<name>-0`, `<name>-1`, ...)
- Stable storage per pod (dedicated PVC per ordinal)
- Ordered lifecycle behavior for scaling and replacement

### Deployment vs StatefulSet

| Feature | Deployment | StatefulSet |
|---|---|---|
| Pod identity | Ephemeral names with random suffix | Stable ordinal names (`app-0`, `app-1`) |
| Storage model | Usually shared/external storage | Per-pod PVC via `volumeClaimTemplates` |
| Pod DNS | Service-level only | Per-pod DNS with headless service |
| Scale/update order | Unordered | Ordered, identity-preserving |
| Typical workloads | Stateless APIs, web frontends | Databases, queues, shard/replica systems |

Use Deployment/Rollout for stateless apps and progressive delivery. Use StatefulSet for workloads where pod identity and disk state must persist.

## 2) Chart Changes Implemented

Implemented in Helm chart:

- Added `k8s/templates/statefulset.yaml`
  - Uses `serviceName: <fullname>-headless`
  - Preserves existing probes/env/config/secret/vault integration
  - Mounts `/data` from per-pod claim `data`
  - Defines `volumeClaimTemplates` controlled by:
    - `persistence.size`
    - `persistence.storageClass`

- Added `k8s/templates/headless-service.yaml`
  - `clusterIP: None`
  - Same selector labels as workload pods

- Kept existing external `k8s/templates/service.yaml`
  - Still used for regular app access

- Gated workload rendering by values:
  - Added `workload.kind` (default `statefulset`) in:
    - `k8s/values.yaml`
    - `k8s/values-dev.yaml`
    - `k8s/values-prod.yaml`
  - Set `workload.kind: rollout` in `k8s/values-bluegreen.yaml` to keep Lab 14 flow usable

- Prevented PVC conflict:
  - `k8s/templates/pvc.yaml` now renders only when workload is not StatefulSet

## 3) Resource Verification

Run:

```bash
helm lint ./k8s
helm template lab15 ./k8s > /tmp/lab15-render.yaml
kubectl get po,sts,svc,pvc
```

Actual outputs captured:

```text
==> Linting ./k8s
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

Cluster runtime verification:

```text
NAME                        READY   STATUS    RESTARTS   AGE
pod/lab15-my-python-app-0   1/1     Running   0          38s
pod/lab15-my-python-app-1   1/1     Running   0          32s
pod/lab15-my-python-app-2   1/1     Running   0          24s
pod/lab15-my-python-app-3   1/1     Running   0          16s
pod/lab15-my-python-app-4   1/1     Running   0          10s

NAME                                   TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/lab15-my-python-app            NodePort    10.100.17.222   <none>        80:31448/TCP   38s
service/lab15-my-python-app-headless   ClusterIP   None            <none>        80/TCP         38s

NAME                                   READY   AGE
statefulset.apps/lab15-my-python-app   5/5     38s

NAME                                               STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/data-lab15-my-python-app-0   Bound    pvc-c0a4df84-d5f9-4162-8dad-2d104f999878   100Mi      RWO            standard       38s
persistentvolumeclaim/data-lab15-my-python-app-1   Bound    pvc-e9daaa62-46e9-4b02-975c-9627b3883411   100Mi      RWO            standard       32s
persistentvolumeclaim/data-lab15-my-python-app-2   Bound    pvc-4d29300c-623e-4ded-9fee-fa5c2a5fe676   100Mi      RWO            standard       24s
persistentvolumeclaim/data-lab15-my-python-app-3   Bound    pvc-b343f07c-31a9-4526-adff-bf7674ddecbd   100Mi      RWO            standard       16s
persistentvolumeclaim/data-lab15-my-python-app-4   Bound    pvc-127a7e87-6472-49b8-9a0d-efb67356c3b7   100Mi      RWO            standard       10s
```

Rendered manifest confirms:

- `kind: StatefulSet` named `lab15-my-python-app`
- `spec.serviceName: lab15-my-python-app-headless`
- Headless service with `clusterIP: None`
- `volumeClaimTemplates` present with `storage: 100Mi`
- Main external service remains present for app access

## 4) Network Identity (Headless DNS)

Run:

```bash
kubectl exec lab15-my-python-app-0 -- sh -c 'nslookup lab15-my-python-app-1.lab15-my-python-app-headless || getent hosts lab15-my-python-app-1.lab15-my-python-app-headless'
kubectl exec lab15-my-python-app-0 -- sh -c 'nslookup lab15-my-python-app-2.lab15-my-python-app-headless || getent hosts lab15-my-python-app-2.lab15-my-python-app-headless'
```

Output:

```text
sh: 1: nslookup: not found
10.244.0.67     lab15-my-python-app-1.lab15-my-python-app-headless.default.svc.cluster.local
sh: 1: nslookup: not found
10.244.0.68     lab15-my-python-app-2.lab15-my-python-app-headless.default.svc.cluster.local
```

DNS naming pattern:

`<statefulset-pod-name>.<headless-service-name>.<namespace>.svc.cluster.local`

Examples:

- `lab15-my-python-app-1.lab15-my-python-app-headless.default.svc.cluster.local`
- `lab15-my-python-app-2.lab15-my-python-app-headless.default.svc.cluster.local`

## 5) Per-Pod Storage Isolation Evidence

Executed requests directly inside individual pods:

```bash
kubectl exec lab15-my-python-app-0 -- sh -c 'python - <<\"PY\"
import urllib.request
for _ in range(3):
    urllib.request.urlopen(\"http://127.0.0.1:8000/\").read()
print(urllib.request.urlopen(\"http://127.0.0.1:8000/visits\").read().decode())
PY'
```

Equivalent checks were run for pod-1 (1 request) and pod-2 (5 requests), then raw stored files were read.

Output:

```text
{"visits":3}
{"visits":1}
{"visits":5}

pod-0 /data/visits: 3
pod-1 /data/visits: 1
pod-2 /data/visits: 5
pod-3 /data/visits: 0
pod-4 /data/visits: 0
```

Because each pod has its own PVC, increments are isolated and not shared.

## 6) Persistence Test (Delete Pod, Keep Data)

Check stored value, delete one pod, re-check:

```bash
kubectl exec lab15-my-python-app-0 -- cat /data/visits
kubectl delete pod lab15-my-python-app-0
kubectl wait --for=condition=ready pod/lab15-my-python-app-0 --timeout=240s
kubectl exec lab15-my-python-app-0 -- cat /data/visits
```

Output:

```text
before delete pod-0 /data/visits: 3
pod "lab15-my-python-app-0" deleted from default namespace
pod/lab15-my-python-app-0 condition met
after restart pod-0 /data/visits: 3
```

Data survived pod deletion and restart, confirming persistent per-pod storage.
