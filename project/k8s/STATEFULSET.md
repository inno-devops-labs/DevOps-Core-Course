# Lab 15 — StatefulSets and Persistent Storage

Overview, design decisions, and evidence: **[`docs/LAB15.md`](../docs/LAB15.md)**.

This document is the operator runbook — install commands, verification, troubleshooting.

## 1. Overview

The chart now has a `statefulset.enabled` toggle that swaps the workload kind from `Deployment` (Lab 13) or `Rollout` (Lab 14) to a `StatefulSet`. Two new templates are added:

- `templates/statefulset.yaml` — `apps/v1 StatefulSet` with `volumeClaimTemplates` (per-pod PVC instead of the shared one).
- `templates/headless-service.yaml` — `Service` with `clusterIP: None` for stable per-pod DNS.

The standalone `templates/pvc.yaml` is bypassed when `statefulset.enabled=true` — `volumeClaimTemplates` produces one PVC per ordinal automatically.

| Feature | Deployment | StatefulSet |
|---|---|---|
| Pod names | Random suffix | Ordinal (`-0`, `-1`, `-2`) |
| Storage | One shared PVC | One PVC per pod |
| Scale order | Parallel | Ordered (`-0` ready before `-1`) |
| Network ID | Only Service DNS | Per-pod DNS via headless Service |

## 2. Chart layout

| Path | Role |
|---|---|
| `k8s/devops-info-service/templates/statefulset.yaml` | StatefulSet manifest (gated by `statefulset.enabled`) |
| `k8s/devops-info-service/templates/headless-service.yaml` | Headless Service (gated by `statefulset.enabled`) |
| `k8s/devops-info-service/templates/deployment.yaml` | Now `if not rollout AND not statefulset` |
| `k8s/devops-info-service/templates/rollout.yaml` | Now `if rollout AND not statefulset` |
| `k8s/devops-info-service/templates/pvc.yaml` | Now `if persistence AND not statefulset` |
| `k8s/devops-info-service/values.yaml` | `+statefulset.{enabled,replicas,storage,updateStrategy}` |

### Install

```bash
helm install lab15 ./k8s/devops-info-service \
  --set statefulset.enabled=true \
  --set statefulset.replicas=3
```

## 3. Resource verification

```bash
kubectl get sts,svc,pods,pvc -l app.kubernetes.io/instance=lab15
```

```
NAME                                         READY   AGE
statefulset.apps/lab15-devops-info-service   3/3     78s

NAME                                         TYPE        CLUSTER-IP        EXTERNAL-IP   PORT(S)        AGE
service/lab15-devops-info-service            NodePort    192.168.194.227   <none>        80:30080/TCP   78s
service/lab15-devops-info-service-headless   ClusterIP   None              <none>        80/TCP         78s

NAME                              READY   STATUS    RESTARTS   AGE
pod/lab15-devops-info-service-0   1/1     Running   0          78s
pod/lab15-devops-info-service-1   1/1     Running   0          64s
pod/lab15-devops-info-service-2   1/1     Running   0          47s

NAME                                                            STATUS   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
pvc/visits-data-lab15-devops-info-service-0                     Bound    100Mi      RWO            local-path     78s
pvc/visits-data-lab15-devops-info-service-1                     Bound    100Mi      RWO            local-path     64s
pvc/visits-data-lab15-devops-info-service-2                     Bound    100Mi      RWO            local-path     47s
```

Note the staggered AGE — pods come up `-0 → -1 → -2` with `OrderedReady`.

```bash
kubectl describe sts lab15-devops-info-service | grep -A2 -E 'Replicas:|Update Strategy:|Pod Management Policy:'
```

```
Replicas:           3 desired | 3 total
Update Strategy:    RollingUpdate
  Partition:        0
Pods Status:        3 Running / 0 Waiting / 0 Succeeded / 0 Failed
```

## 4. Network identity

Verify DNS from inside the cluster:

```bash
kubectl run dns-debug --image=busybox:1.36 --restart=Never --command -- \
  sh -c 'nslookup lab15-devops-info-service-headless'
kubectl logs dns-debug ; kubectl delete pod dns-debug
```

```
Name:	lab15-devops-info-service-headless.default.svc.cluster.local
Address: 192.168.194.18
Address: 192.168.194.16
Address: 192.168.194.14
```

Per-pod FQDN (use full form — short `<pod>.<svc>` requires search-domain trickery):

```
nslookup lab15-devops-info-service-0.lab15-devops-info-service-headless.default.svc.cluster.local
  → 192.168.194.14
nslookup lab15-devops-info-service-1.lab15-devops-info-service-headless.default.svc.cluster.local
  → 192.168.194.16
nslookup lab15-devops-info-service-2.lab15-devops-info-service-headless.default.svc.cluster.local
  → 192.168.194.18
```

## 5. Per-pod storage evidence

The image `peplxx/devops-info-service:latest` does not currently expose a `/visits` HTTP endpoint, so isolation is demonstrated by writing distinct values directly to each pod's `/data/visits` (the same path the chart wires via `VISITS_FILE=/data/visits`).

```bash
kubectl exec lab15-devops-info-service-0 -- sh -c 'echo 5 > /data/visits'
kubectl exec lab15-devops-info-service-1 -- sh -c 'echo 2 > /data/visits'
kubectl exec lab15-devops-info-service-2 -- sh -c 'echo 8 > /data/visits'

for i in 0 1 2; do
  echo "pod-$i: $(kubectl exec lab15-devops-info-service-$i -- cat /data/visits)"
done
```

```
pod-0: 5
pod-1: 2
pod-2: 8
```

`/data` is a real PV, not `emptyDir`:

```bash
kubectl exec lab15-devops-info-service-0 -- sh -c 'df -h /data'
```

```
Filesystem      Size  Used Avail Use% Mounted on
/dev/vdb1       492G   11G  482G   3% /data
```

## 6. Persistence test

```bash
echo "BEFORE: $(kubectl exec lab15-devops-info-service-1 -- cat /data/visits)"
kubectl get pvc visits-data-lab15-devops-info-service-1 -o jsonpath='PVC UID: {.metadata.uid}{"\n"}'

kubectl delete pod lab15-devops-info-service-1
kubectl wait --for=condition=Ready pod/lab15-devops-info-service-1 --timeout=120s

echo "AFTER:  $(kubectl exec lab15-devops-info-service-1 -- cat /data/visits)"
kubectl get pvc visits-data-lab15-devops-info-service-1 -o jsonpath='PVC UID: {.metadata.uid}{"\n"}'
```

```
BEFORE: 2
PVC UID: 96c3b773-4786-46d0-9724-8462f2f48d2f

(deleted pod-1)

AFTER:  2
PVC UID: 96c3b773-4786-46d0-9724-8462f2f48d2f   ← same volume reattached
```

Counter value `2` survives a pod restart; the StatefulSet reattaches the **same** PVC to the recreated pod.

## 7. Bonus — Update strategies

### `RollingUpdate` with `partition`

```bash
helm upgrade lab15 ./k8s/devops-info-service \
  --set statefulset.enabled=true \
  --set statefulset.replicas=3 \
  --set statefulset.updateStrategy.type=RollingUpdate \
  --set statefulset.updateStrategy.rollingUpdate.partition=2

kubectl patch sts lab15-devops-info-service --type=json \
  -p='[{"op":"add","path":"/spec/template/metadata/labels/lab15-rev","value":"v2"}]'

sleep 25
kubectl get pods -l app.kubernetes.io/instance=lab15 \
  -o custom-columns=NAME:.metadata.name,UID:.metadata.uid,LAB15_REV:.metadata.labels.lab15-rev
```

```
NAME                          UID                                    LAB15_REV
lab15-devops-info-service-0   df6713ab-c788-4054-a7be-9c56693e676d   <none>     ← unchanged
lab15-devops-info-service-1   f441269d-9451-4e60-bea5-49f7e827aefb   <none>     ← unchanged
lab15-devops-info-service-2   9cdb79b3-f9d5-48c6-8499-1385b35df688   v2         ← updated
```

Only pods with ordinal `≥ partition` (i.e. `≥ 2`) updated. Drop `partition` to `0` to release the rest.

### `OnDelete`

```bash
helm upgrade lab15 ./k8s/devops-info-service \
  --set statefulset.enabled=true \
  --set statefulset.replicas=3 \
  --set statefulset.updateStrategy.type=OnDelete

kubectl patch sts lab15-devops-info-service --type=json \
  -p='[{"op":"add","path":"/spec/template/metadata/labels/lab15-rev","value":"v3"}]'

sleep 15
kubectl get pods -l app.kubernetes.io/instance=lab15 \
  -o custom-columns=NAME:.metadata.name,UID:.metadata.uid,LAB15_REV:.metadata.labels.lab15-rev
```

```
NAME                          UID                                    LAB15_REV
lab15-devops-info-service-0   df6713ab-c788-4054-a7be-9c56693e676d   <none>     ← no auto-update
lab15-devops-info-service-1   f441269d-9451-4e60-bea5-49f7e827aefb   <none>     ← no auto-update
lab15-devops-info-service-2   9cdb79b3-f9d5-48c6-8499-1385b35df688   v2         ← still on v2
```

Spec changed but no pod was recreated. Manual delete drives the rollout:

```bash
kubectl delete pod lab15-devops-info-service-0
kubectl wait --for=condition=Ready pod/lab15-devops-info-service-0 --timeout=60s
```

```
lab15-devops-info-service-0   4371cbda-409a-497d-8e95-717f67eab64b   v3   ← picked up new spec
lab15-devops-info-service-1   f441269d-9451-4e60-bea5-49f7e827aefb   <none>
lab15-devops-info-service-2   9cdb79b3-f9d5-48c6-8499-1385b35df688   v2
```

## 8. Cleanup

```bash
helm uninstall lab15
kubectl delete pvc -l app.kubernetes.io/instance=lab15
```

`helm uninstall` removes the StatefulSet, both Services, the ConfigMaps and Secret. It does **not** delete PVCs created by `volumeClaimTemplates` — that is intentional (data preservation), but for a fresh demo run, drop them explicitly with the second command.

## 9. Troubleshooting

### Install fails with `provided port is already allocated`

A previous release (often `app` from Labs 12–14) owns NodePort 30080. Either uninstall it (`helm uninstall app`) or override the port (`--set service.nodePort=30081`).

### Per-pod DNS resolves on the FQDN but not on the short form

`<pod>.<headless-svc>` only resolves when the client pod's `/etc/resolv.conf` includes the right `search` domain (the chart's app pods do; ad-hoc `kubectl run busybox` pods may not). Use the full `<pod>.<svc>.<ns>.svc.cluster.local` form to be safe.

### `kubectl exec` reports `cat: /data/visits: No such file or directory`

The file is created on first write. Run the seed `kubectl exec ... -- sh -c 'echo N > /data/visits'` first, then `cat` it.
