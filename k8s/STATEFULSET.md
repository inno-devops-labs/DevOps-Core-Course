# Lab 15 - StatefulSets and Persistent Storage

This document describes the StatefulSet implementation for the
`devops-info-chart` Helm chart.

Repository chart path:

- Helm chart: `k8s/devops-info-chart`
- StatefulSet values: `k8s/devops-info-chart/values-statefulset.yaml`
- Partitioned update values: `k8s/devops-info-chart/values-statefulset-partition.yaml`
- OnDelete update values: `k8s/devops-info-chart/values-statefulset-ondelete.yaml`

## 1. StatefulSet Overview

StatefulSets are used when replicas are not interchangeable. They provide:

- stable pod names: `<statefulset-name>-0`, `<statefulset-name>-1`, ...
- stable DNS through a headless service
- separate persistent storage for every pod through `volumeClaimTemplates`
- ordered startup, update, and termination by default

This lab keeps the regular Service for external access and adds a headless
Service for direct pod identity.

| Feature | Deployment | StatefulSet |
| --- | --- | --- |
| Pod names | Random ReplicaSet suffix | Stable ordinal suffix |
| Storage | Shared or manually attached PVC | One PVC per pod |
| Network identity | Service load balances to any pod | Pod DNS name is stable |
| Scaling | Pods can start in any order | Ordered by ordinal by default |
| Best for | Stateless APIs and workers | Databases, queues, clustered apps |

Use a Deployment or Rollout for the stateless API delivery path. Use a
StatefulSet when the application must keep stable identity and per-replica data.

## 2. Helm Implementation

StatefulSet mode is enabled with:

```bash
helm upgrade --install devops-info k8s/devops-info-chart \
  -n lab15 \
  -f k8s/devops-info-chart/values-statefulset.yaml \
  --set service.type=ClusterIP \
  --set image.tag=lab15 \
  --set image.pullPolicy=Always
```

When `statefulset.enabled=true`:

- `templates/statefulset.yaml` renders instead of `templates/deployment.yaml`
- `templates/rollout.yaml` is disabled
- `templates/pvc.yaml` is disabled because PVCs are created by
  `volumeClaimTemplates`
- `templates/service-headless.yaml` creates the governing headless Service

Important rendered resources:

```text
Namespace:    lab15
Service:      devops-info-devops-info-chart
Headless:     devops-info-devops-info-chart-headless
StatefulSet:  devops-info-devops-info-chart
Pods:         devops-info-devops-info-chart-0
              devops-info-devops-info-chart-1
              devops-info-devops-info-chart-2
PVCs:         data-volume-devops-info-devops-info-chart-0
              data-volume-devops-info-devops-info-chart-1
              data-volume-devops-info-devops-info-chart-2
```

## 3. Resource Verification

Deploy and wait for the StatefulSet:

```bash
helm upgrade --install devops-info k8s/devops-info-chart \
  -n lab15 \
  -f k8s/devops-info-chart/values-statefulset.yaml \
  --set service.type=ClusterIP \
  --set image.tag=lab15 \
  --set image.pullPolicy=Always

kubectl rollout status statefulset/devops-info-devops-info-chart -n lab15
```

Verify resources:

```bash
kubectl get po,sts,svc,pvc -n lab15 -l app.kubernetes.io/instance=devops-info
```

Actual result on Docker Desktop Kubernetes:

```text
pod/devops-info-devops-info-chart-0   1/1   Running   0   61s
pod/devops-info-devops-info-chart-1   1/1   Running   0   45s
pod/devops-info-devops-info-chart-2   1/1   Running   0   33s

statefulset.apps/devops-info-devops-info-chart   3/3

service/devops-info-devops-info-chart            ClusterIP   10.101.78.99   80/TCP
service/devops-info-devops-info-chart-headless   ClusterIP   None           80/TCP

persistentvolumeclaim/data-volume-devops-info-devops-info-chart-0   Bound   100Mi   hostpath
persistentvolumeclaim/data-volume-devops-info-devops-info-chart-1   Bound   100Mi   hostpath
persistentvolumeclaim/data-volume-devops-info-devops-info-chart-2   Bound   100Mi   hostpath
```

Actual pod IPs:

```text
devops-info-devops-info-chart-0   10.1.0.80
devops-info-devops-info-chart-1   10.1.0.81
devops-info-devops-info-chart-2   10.1.0.82
```

## 4. Network Identity

DNS pattern:

```text
<pod-name>.<headless-service>.<namespace>.svc.cluster.local
```

For this release in the `lab15` namespace:

```text
devops-info-devops-info-chart-0.devops-info-devops-info-chart-headless.lab15.svc.cluster.local
devops-info-devops-info-chart-1.devops-info-devops-info-chart-headless.lab15.svc.cluster.local
devops-info-devops-info-chart-2.devops-info-devops-info-chart-headless.lab15.svc.cluster.local
```

Resolve another pod from pod `0` using Python, which is already present in the
application image:

```bash
kubectl exec -n lab15 devops-info-devops-info-chart-0 -- \
  python -c "import socket; print(socket.gethostbyname('devops-info-devops-info-chart-1.devops-info-devops-info-chart-headless.lab15.svc.cluster.local'))"
```

Alternative DNS check with a temporary BusyBox pod:

```bash
kubectl run dns-check --rm -it --restart=Never --image=busybox:1.36 -- \
  nslookup devops-info-devops-info-chart-1.devops-info-devops-info-chart-headless.lab15.svc.cluster.local
```

Actual result:

```text
devops-info-devops-info-chart-1.devops-info-devops-info-chart-headless.lab15.svc.cluster.local -> 10.1.0.81
devops-info-devops-info-chart-0 FQDN -> devops-info-devops-info-chart-0.devops-info-devops-info-chart-headless.lab15.svc.cluster.local
```

## 5. Per-Pod Storage Evidence

Each pod mounts its own PVC at `/data`. The app is configured with
`VISITS_FILE=/data/visits`, so counters are isolated per pod.

The live run uses `vladimirzhidkov/devops-info-service:lab15`, which exposes
both `/health` and `/visits`.

Open three port-forwards in separate terminals:

```bash
kubectl port-forward -n lab15 pod/devops-info-devops-info-chart-0 8080:5000
kubectl port-forward -n lab15 pod/devops-info-devops-info-chart-1 8081:5000
kubectl port-forward -n lab15 pod/devops-info-devops-info-chart-2 8082:5000
```

Generate different counters:

```bash
curl http://localhost:8080/
curl http://localhost:8080/
curl http://localhost:8081/

curl http://localhost:8080/visits
curl http://localhost:8081/visits
curl http://localhost:8082/visits
```

Actual HTTP result:

```text
pod-0: {"visits":4}
pod-1: {"visits":2}
pod-2: {"visits":0}
```

Direct file check, if needed:

```bash
kubectl exec -n lab15 devops-info-devops-info-chart-0 -- cat /data/visits
kubectl exec -n lab15 devops-info-devops-info-chart-1 -- cat /data/visits
kubectl exec -n lab15 devops-info-devops-info-chart-2 -- sh -c "cat /data/visits 2>/dev/null || echo 0"
```

Actual file result:

```text
pod-0: 4
pod-1: 2
pod-2: 0
```

The values differ because every pod writes to a different PVC.

Application health was also verified from inside pod `0`:

```bash
kubectl exec -n lab15 devops-info-devops-info-chart-0 -- \
  python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:5000/health').read().decode())"
```

Actual result:

```json
{"status":"healthy","timestamp":"2026-05-03T21:18:19.053Z","uptime_seconds":117}
```

## 6. Persistence Test

Record the current counter for pod `0`:

```bash
kubectl exec -n lab15 devops-info-devops-info-chart-0 -- cat /data/visits
```

Delete only the pod, not the StatefulSet or PVC:

```bash
kubectl delete pod -n lab15 devops-info-devops-info-chart-0
kubectl wait --for=condition=ready pod/devops-info-devops-info-chart-0 -n lab15 --timeout=120s
```

Check the counter again:

```bash
kubectl exec -n lab15 devops-info-devops-info-chart-0 -- cat /data/visits
```

Actual result:

```text
pod "devops-info-devops-info-chart-0" deleted
pod/devops-info-devops-info-chart-0 condition met
before={"visits":4}
after={"visits":4}
```

The value was preserved. Kubernetes recreated the pod with the
same name and reattached the same PVC:

```text
data-volume-devops-info-devops-info-chart-0
```

## 7. Bonus - Update Strategies

### Partitioned RollingUpdate

With `replicaCount: 3` and `partition: 2`, only pods with ordinal `>= 2` update.
This allows testing a new version on the highest ordinal first.

```bash
helm upgrade devops-info k8s/devops-info-chart \
  -n lab15 \
  -f k8s/devops-info-chart/values-statefulset.yaml \
  -f k8s/devops-info-chart/values-statefulset-partition.yaml \
  --set service.type=ClusterIP \
  --set image.tag=lab02

kubectl get pods -n lab15 -l app.kubernetes.io/instance=devops-info \
  -o custom-columns=NAME:.metadata.name,IMAGE:.spec.containers[0].image
```

Actual result:

```text
devops-info-devops-info-chart-0   vladimirzhidkov/devops-info-service:latest
devops-info-devops-info-chart-1   vladimirzhidkov/devops-info-service:latest
devops-info-devops-info-chart-2   vladimirzhidkov/devops-info-service:lab02
```

Lower the partition to continue the rollout:

```bash
helm upgrade devops-info k8s/devops-info-chart \
  -n lab15 \
  -f k8s/devops-info-chart/values-statefulset.yaml \
  --set service.type=ClusterIP \
  --set statefulset.updateStrategy.rollingUpdate.partition=1 \
  --set image.tag=lab02
```

### OnDelete

With `OnDelete`, Kubernetes records the new pod template but does not restart
pods automatically. Each pod updates only after manual deletion.

```bash
helm upgrade devops-info k8s/devops-info-chart \
  -n lab15 \
  -f k8s/devops-info-chart/values-statefulset.yaml \
  -f k8s/devops-info-chart/values-statefulset-ondelete.yaml \
  --set service.type=ClusterIP \
  --set image.tag=latest

kubectl delete pod -n lab15 devops-info-devops-info-chart-2
kubectl wait --for=condition=ready pod/devops-info-devops-info-chart-2 -n lab15 --timeout=120s
```

Use OnDelete for workloads where an operator must control the exact restart
order, such as databases with manual failover or strict maintenance windows.

Actual OnDelete test:

```text
Before manual delete:
devops-info-devops-info-chart-0   vladimirzhidkov/devops-info-service:latest
devops-info-devops-info-chart-1   vladimirzhidkov/devops-info-service:latest
devops-info-devops-info-chart-2   vladimirzhidkov/devops-info-service:lab02

After manual delete:
devops-info-devops-info-chart-0   vladimirzhidkov/devops-info-service:latest
devops-info-devops-info-chart-1   vladimirzhidkov/devops-info-service:latest
devops-info-devops-info-chart-2   vladimirzhidkov/devops-info-service:latest
```

## 8. Cleanup

Delete the release:

```bash
helm uninstall devops-info
```

StatefulSet PVCs are intentionally retained by Kubernetes. Delete them manually
only when the stored data is no longer needed:

```bash
kubectl delete pvc -l app.kubernetes.io/instance=devops-info
```
