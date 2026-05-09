# Lab 15 — StatefulSets & persistent storage

This chart can run the Python app as an **Argo Rollout** (Lab 14, default) or a **StatefulSet** (Lab 15) via `workload.kind`.

## Why StatefulSet?

StatefulSets give **stable pod names** (`<release>-devops-python-0`, `-1`, …), **ordered** start/terminate, and **per-pod** persistent volumes via **`volumeClaimTemplates`**. Use them for workloads that need identity and dedicated disk (databases, Kafka, etc.). For **stateless** HTTP apps and **canary/blue-green**, prefer a **Rollout** or Deployment.

| | Rollout / Deployment | StatefulSet |
|---|---------------------|-------------|
| Pod names | Random suffix | Stable ordinal |
| Storage | Often one shared PVC or ephemeral | **Per-pod** PVC from templates |
| Scale | Any order | Typically ordered (0→1→2) |
| DNS | Via Service only | **Headless** Service → per-pod A records |

## Install as StatefulSet

```bash
helm upgrade --install myapp ./k8s/devops-python -n default --create-namespace \
  -f k8s/devops-python/values-statefulset.yaml
```

Or set `workload.kind: statefulSet` in your own values file.

**Templates involved:**

- `templates/statefulset.yaml` — `serviceName` points at the headless service
- `templates/service-headless.yaml` — `clusterIP: None`, same selectors as pods
- `templates/service.yaml` — unchanged **client** Service (NodePort/ClusterIP) for load-balanced access

When `workload.kind` is `statefulSet`, the chart does **not** render the single shared `PersistentVolumeClaim` used by the Rollout path; storage is **only** from **`volumeClaimTemplates`** (name `visits-data`), one PVC per pod.

## Verify resources

```bash
kubectl get sts,po,svc,pvc -l app.kubernetes.io/instance=<release>
```

Expect PVCs named `visits-data-<statefulset>-0`, `visits-data-<statefulset>-1`, …

## Headless DNS

Pattern:

`<pod-name>.<headless-service>.<namespace>.svc.cluster.local`

Example (release `myapp`, name `myapp-devops-python`):

- Pods: `myapp-devops-python-0`, `myapp-devops-python-1`
- Headless Service: `myapp-devops-python-headless`
- Pod 0 resolves pod 1:  
  `nslookup myapp-devops-python-1.myapp-devops-python-headless.default.svc.cluster.local`

`publishNotReadyAddresses: true` allows DNS records even before pods are Ready (use with care in production).

## Per-pod visit counter (Lab 12 app)

Each pod mounts **its own** volume at `/data`, so **`GET /visits`** reflects **only that pod’s** file.

**Example:**

```bash
kubectl port-forward pod/myapp-devops-python-0 8080:5000 &
kubectl port-forward pod/myapp-devops-python-1 8081:5000 &
curl -s localhost:8080/visits
curl -s http://localhost:8081/visits
```

Hit `/` several times on each port-forward (or use the main Service and rely on load balancing) to show **different** totals per pod when addressed directly.

## Persistence after deleting a pod

```bash
kubectl exec myapp-devops-python-0 -- cat /data/visits
kubectl delete pod myapp-devops-python-0
# wait for pod 0 to recreate
kubectl exec myapp-devops-python-0 -- cat /data/visits
```

The ordinal **0** is reattached to the **same** PVC; the counter file should match the pre-delete value.

## Bonus — update strategies

**Partitioned rolling update** (`values-statefulset-partition.yaml`):

- `updateStrategy.rollingUpdate.partition: N` — during an image/config change, only pods with **ordinal ≥ N** receive the new revision until you lower or remove the partition.

**OnDelete** (`values-statefulset-ondelete.yaml`):

- `updateStrategy.type: OnDelete` — the controller does not restart pods automatically; delete a pod manually to apply the new template. Useful for strict operational control; slower and easy to forget.

Combine with the main StatefulSet values file:

```bash
helm upgrade --install myapp ./k8s/devops-python \
  -f k8s/devops-python/values-statefulset.yaml \
  -f k8s/devops-python/values-statefulset-partition.yaml
```

## References

- [StatefulSet](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)  
- [Headless Services](https://kubernetes.io/docs/concepts/services-networking/service/#headless-services)  
- [VolumeClaimTemplates](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/#volume-claim-templates)  

## Evidence checklist (for your report)

- `kubectl get sts,po,svc,pvc` output  
- DNS lookup from inside a pod  
- Different `/visits` (or `/data/visits`) per ordinal  
- Same count on pod `*-0` after delete/recreate  
