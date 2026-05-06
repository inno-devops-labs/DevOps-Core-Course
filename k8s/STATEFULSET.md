# StatefulSet Implementation

## Overview

StatefulSets are Kubernetes controllers designed for stateful applications.

Unlike Deployments, StatefulSets provide:

- Stable pod identities
- Stable network names
- Persistent storage per pod
- Ordered deployment and scaling


# StatefulSet vs Deployment

| Feature | Deployment | StatefulSet |
|---|---|---|
| Pod Names | Random | Stable |
| Storage | Shared/Ephemeral | Persistent per pod |
| Scaling | Parallel | Ordered |
| Identity | Unstable | Stable |
| Typical Usage | Stateless apps | Databases, queues |


# Why StatefulSet Was Used

This application stores visit counters independently for each pod.

Each pod requires:

- its own persistent storage
- stable DNS identity
- predictable pod naming

StatefulSet satisfies these requirements.


# Headless Service

A headless service was created using:

```yaml
clusterIP: None
```
This allows direct DNS resolution for each pod.

DNS pattern:
```
<pod-name>.<headless-service-name>
```
Example:
```
python-app-release-0.python-app-release-headless
```
## Resource Verification
## Pods
```
$ kubectl get pods

NAME                    READY   STATUS
python-app-release-0    1/1     Running
python-app-release-1    1/1     Running
python-app-release-2    1/1     Running
```
## StatefulSet
```
$ kubectl get sts

NAME                READY   AGE
python-app-release  3/3     5m
```
## Services
```
$ kubectl get svc

NAME                                TYPE        CLUSTER-IP
python-app-service                  NodePort    10.96.10.5
python-app-release-headless         ClusterIP   None
```
## PersistentVolumeClaims
```
$ kubectl get pvc

NAME                                      STATUS
app-storage-python-app-release-0          Bound
app-storage-python-app-release-1          Bound
app-storage-python-app-release-2          Bound
```
## DNS Resolution Test

DNS resolution between pods was verified.

Command:
```
kubectl exec -it python-app-release-0 -- nslookup python-app-release-1.python-app-release-headless
```
Output:
```
Name: python-app-release-1.python-app-release-headless
Address: 10.244.0.12
```
## Per-Pod Storage Isolation

Each pod stores visit counter independently.

Example:
```
python-app-release-0 -> visits: 12
python-app-release-1 -> visits: 4
python-app-release-2 -> visits: 19
```
This demonstrates storage isolation.

## Persistence Verification

Pod was deleted manually:
```
kubectl delete pod python-app-release-1
```
After recreation, visit counter remained unchanged.

Before deletion:
```
visits: 7
```
After recreation:
```
visits: 7
```
This confirms persistence via PersistentVolumeClaims.

## Update Strategies
### RollingUpdate with Partition

Configuration:
```
updateStrategy:
  type: RollingUpdate
  rollingUpdate:
    partition: 1
```
Behavior:

- only pods with ordinal >= 1 are updated

### OnDelete Strategy

Configuration:
```
updateStrategy:
  type: OnDelete
```
Behavior:

- pods update only after manual deletion

## Conclusion

StatefulSet successfully provided:

- stable pod identities
- stable DNS names
- persistent per-pod storage
- ordered deployment and scaling

The application now preserves state across pod restarts.