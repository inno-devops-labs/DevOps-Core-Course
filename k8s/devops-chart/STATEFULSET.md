# Lab 15 — StatefulSets & Persistent Storage

## Overview

In this lab, a Kubernetes Deployment was converted into a StatefulSet in order to provide stable pod identities and persistent per-pod storage. A headless Service was also configured to enable direct DNS-based communication between pods.

The application used in this lab was the `devops-info-service` Flask application with a persistent visits counter stored inside mounted volumes.

## Task 1 — StatefulSet Concepts

### StatefulSet Guarantees

StatefulSets provide several guarantees that regular Deployments do not:

- Stable and unique pod names
- Stable persistent storage for every pod
- Ordered pod startup and termination
- Stable network identities

Examples of stateful workloads include:

- PostgreSQL
- MySQL
- MongoDB
- Kafka
- Elasticsearch

### StatefulSet vs Deployment

| Feature | Deployment | StatefulSet |
|---|---|---|
| Pod names | Random suffixes | Stable ordered names |
| Storage | Shared or external | Per-pod persistent storage |
| Scaling | Parallel | Ordered |
| Network identity | Dynamic | Stable DNS |
| Typical use | Stateless apps | Stateful apps |

### Headless Service

A headless Service was configured using:

```yaml
clusterIP: None
```

This allows Kubernetes to create DNS records for every StatefulSet pod:

```text
devops-stateful-devops-chart-0.devops-stateful-devops-chart-headless
devops-stateful-devops-chart-1.devops-stateful-devops-chart-headless
devops-stateful-devops-chart-2.devops-stateful-devops-chart-headless
```

## Task 2 — StatefulSet Implementation

### StatefulSet Configuration

A new `statefulset.yaml` template was created in the Helm chart.

Key features:

- `serviceName` configured for headless service
- `volumeClaimTemplates` used for automatic PVC creation
- Persistent storage mounted to `/data`
- Stable pod naming

### Headless Service

A dedicated headless Service was created:

```yaml
clusterIP: None
```

The existing NodePort service was kept for external access.

### Resource Verification

```bash
kubectl get po,sts,svc,pvc -n stateful-lab
```

Screenshot: `docs/screenshots/15-1-resources.png`

## Task 3 — Headless Service & Pod Identity

### DNS Resolution Test

DNS resolution was tested using a temporary BusyBox pod.

Command:

```bash
kubectl run dns-test -n stateful-lab \
  --image=busybox:1.36 \
  --restart=Never \
  --rm -it \
  -- nslookup devops-stateful-devops-chart-1.devops-stateful-devops-chart-headless
```

Result:

```text
Name: devops-stateful-devops-chart-1.devops-stateful-devops-chart-headless.stateful-lab.svc.cluster.local
Address: 10.96.0.10
```

This confirmed that every StatefulSet pod has a stable DNS identity.

### Per-Pod Storage Isolation

Separate port-forwards were created for all three pods:

```bash
kubectl port-forward pod/devops-stateful-devops-chart-0 -n stateful-lab 8180:5000
kubectl port-forward pod/devops-stateful-devops-chart-1 -n stateful-lab 8181:5000
kubectl port-forward pod/devops-stateful-devops-chart-2 -n stateful-lab 8182:5000
```

Screenshot: `docs/screenshots/15-2-curls.png`

This proves that every pod has isolated persistent storage.

### Persistence Test

The visits file was checked before pod deletion:

```bash
kubectl exec devops-stateful-devops-chart-0 -n stateful-lab -- cat /data/visits
```

Output:

```text
2
```

The pod was deleted:

```bash
kubectl delete pod devops-stateful-devops-chart-0 -n stateful-lab
```

After Kubernetes recreated the pod, the visits file was checked again:

```bash
kubectl exec devops-stateful-devops-chart-0 -n stateful-lab -- cat /data/visits
```

Output:

```text
2
```

Screenshot: `docs/screenshots/15-3-visits.png`

The data persisted successfully after pod recreation because the PVC remained attached to the StatefulSet pod.

## Conclusion

In this lab:

- A Deployment was successfully converted into a StatefulSet
- A headless Service was configured
- Stable pod identities were verified
- Per-pod PVCs were automatically provisioned
- Independent persistent storage was demonstrated
- Persistent data survived pod recreation

This lab demonstrated the key advantages of StatefulSets for stateful Kubernetes workloads.