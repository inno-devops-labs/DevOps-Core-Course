# Lab 15 — StatefulSets & Persistent Storage

This document contains the Lab 15 submission for StatefulSets: concepts, Helm implementation, and verification evidence (resources, DNS identity, per-pod storage isolation, persistence).

Environment used in this lab:

- Namespace: `lab15`
- Helm release: `devops-app-stateful`
- Workload: `StatefulSet/devops-app-stateful` with 3 replicas

## Task 1 — StatefulSet Concepts (Overview)

StatefulSets are used when each replica must keep a stable identity and stable storage.

Key guarantees (vs Deployment):

| Capability | Deployment | StatefulSet |
|---|---|---|
| Pod names | random suffix | stable ordinal (`-0`, `-1`, `-2`) |
| Network identity | changes on reschedule | stable DNS per pod via headless Service |
| Storage | usually shared / external | per-pod PVC via `volumeClaimTemplates` |
| Start/stop order | not guaranteed | ordered (can be controlled) |

Headless Service (`clusterIP: None`) is used with StatefulSets to create DNS records for each pod:

```text
<pod-name>.<headless-service>.<namespace>.svc.cluster.local
```

## Task 2 — Helm Implementation

Chart files:

- `k8s/devops-app/templates/statefulset.yaml`
- `k8s/devops-app/templates/headless-service.yaml`
- `k8s/devops-app/values-statefulset.yaml`

Important configuration:

- `statefulset.enabled: true`
- `headlessService.enabled: true`
- `rollouts.enabled: false` (Rollouts are not used in Lab 15)
- `persistence.enabled: true`
- `persistence.storageClass: standard`
- `podSecurityContext.fsGroup: 1000` (to allow writing into the mounted volume)

StatefulSet uses:

- `serviceName: devops-app-stateful-headless`
- `volumeClaimTemplates` to create one PVC per replica (`data-volume-...-0/1/2`)

## Task 2 — Resource Verification

### StatefulSet

```bash
kubectl get sts -n lab15
```

```text
NAME                READY   AGE
devops-app-stateful 3/3     30m
```

### Pods

```bash
kubectl get pods -n lab15 -o wide
```

```text
NAME                  READY   STATUS   RESTARTS   AGE   IP           NODE
devops-app-stateful-0 1/1     Running  0          11m   10.244.0.70   lab9-control-plane
devops-app-stateful-1 1/1     Running  0          3m    10.244.0.73   lab9-control-plane
devops-app-stateful-2 1/1     Running  0          28s   10.244.0.74   lab9-control-plane
```

### Services (external + headless)

```bash
kubectl get svc -n lab15
```

```text
NAME                         TYPE       CLUSTER-IP    PORT(S)
devops-app-stateful          ClusterIP  10.96.92.45   80/TCP
devops-app-stateful-headless ClusterIP  None          80/TCP
```

### PVCs (one per pod)

```bash
kubectl get pvc -n lab15
```

```text
NAME                              STATUS   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
data-volume-devops-app-stateful-0  Bound    100Mi      RWO            standard       30m
data-volume-devops-app-stateful-1  Bound    100Mi      RWO            standard       30m
data-volume-devops-app-stateful-2  Bound    100Mi      RWO            standard       30m
```

## Task 3 — Headless Service & Pod Identity

### DNS resolution (from inside the cluster)

Command (run from `devops-app-stateful-0`):

```bash
for i in 0 1 2; do
	kubectl exec -n lab15 devops-app-stateful-0 -- \
		python -c "import socket; print('devops-app-stateful-$i ->', socket.gethostbyname('devops-app-stateful-$i.devops-app-stateful-headless.lab15.svc.cluster.local'))"
done
```

Output:

```text
devops-app-stateful-0 -> 10.244.0.70
devops-app-stateful-1 -> 10.244.0.73
devops-app-stateful-2 -> 10.244.0.74
```

### Per-pod storage isolation

Each pod has its own PVC mounted at `/data`. To show isolation, each pod writes its own identity file on its own volume:

```bash
kubectl exec -n lab15 devops-app-stateful-0 -- sh -c 'echo "pod=$(hostname)" > /data/identity.txt'
kubectl exec -n lab15 devops-app-stateful-1 -- sh -c 'echo "pod=$(hostname)" > /data/identity.txt'
kubectl exec -n lab15 devops-app-stateful-2 -- sh -c 'echo "pod=$(hostname)" > /data/identity.txt'

kubectl exec -n lab15 devops-app-stateful-0 -- cat /data/identity.txt
kubectl exec -n lab15 devops-app-stateful-1 -- cat /data/identity.txt
kubectl exec -n lab15 devops-app-stateful-2 -- cat /data/identity.txt
```

Example output:

```text
pod=devops-app-stateful-0
pod=devops-app-stateful-1
pod=devops-app-stateful-2
```

## Task 3 — Persistence Test

Delete a single pod (NOT the StatefulSet) and verify that PVC-backed data remains after recreation.

### Example: `devops-app-stateful-2`

Write a marker file on `/data`:

```bash
kubectl exec -n lab15 devops-app-stateful-2 -- sh -c 'echo "marker-before-delete" >> /data/persist2.txt; cat /data/persist2.txt'
```

Delete the pod and wait until it becomes Ready again:

```bash
kubectl delete pod -n lab15 devops-app-stateful-2
kubectl wait -n lab15 --for=condition=ready pod/devops-app-stateful-2 --timeout=180s
```

Check the file after recreation:

```bash
kubectl exec -n lab15 devops-app-stateful-2 -- sh -c 'echo "after-recreate" >> /data/persist2.txt; cat /data/persist2.txt'
```

Output:

```text
marker-before-delete 2026-05-07T20:51:18+00:00
after-recreate 2026-05-07T20:52:21+00:00
```

## Bonus Task (not done)

Bonus tasks for update strategies (partition / OnDelete) were intentionally skipped.
