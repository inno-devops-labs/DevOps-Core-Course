# StatefulSet Implementation Overview

## Why StatefulSet Was Used

A StatefulSet was chosen because the application stores a per-pod visit counter in persistent storage. This behavior requires each replica to have:

- a stable pod identity;
- its own dedicated storage;
- predictable DNS naming;
- persistence across pod recreation.

A Deployment is better suited for stateless replicas, while a StatefulSet is appropriate when each replica owns its own state.

## Differences from Deployment

| Feature | Deployment | StatefulSet |
|---|---|---|
| Pod names | Random suffixes | Stable ordinal names (`app-python-0`, `app-python-1`, `app-python-2`) |
| Storage | Usually shared or external | Dedicated PVC per pod |
| Network identity | Ephemeral | Stable DNS through headless service |
| Scaling order | Unordered | Ordered |
| Typical use | Stateless workloads | Stateful workloads |

## Resource Verification

The rendered Helm manifest and deployed resources confirm the StatefulSet design:

- `kind: StatefulSet` is present in the rendered manifest;
- `clusterIP: None` is present for the headless service;
- `volumeClaimTemplates` is present to generate PVCs per replica.

After installation, the following resource pattern was observed in `default` namespace:

- `StatefulSet/app-python`
- pods `app-python-0`, `app-python-1`, `app-python-2`
- PVCs `data-app-python-0`, `data-app-python-1`, `data-app-python-2`
- regular service `app-python`
- headless service `app-python-headless`

## Network Identity

DNS resolution was tested from inside `app-python-0`. The following names resolved successfully:

- `app-python-1.app-python-headless.default.svc.cluster.local`
- `app-python-2.app-python-headless.default.svc.cluster.local`

This demonstrates the StatefulSet DNS pattern:

```text
<pod-name>.<headless-service>.<namespace>.svc.cluster.local
```

## Per-Pod Storage Evidence

Direct access to each pod via port-forward showed different visit counters:

- `app-python-0` → `2`
- `app-python-1` → `0`
- `app-python-2` → `1`

The same values were confirmed by reading `/data/visits` inside each pod. This proves that storage is isolated on a per-pod basis.

## Persistence Test

`app-python-0` was deleted manually. After Kubernetes recreated the pod, the file `/data/visits` was read again and still contained `2`.

This confirms that the StatefulSet keeps data on persistent storage rather than inside the temporary container filesystem.
