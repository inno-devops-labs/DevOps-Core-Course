# LAB15 - StatefulSets & Persistent Storage

Cluster: `minikube`  
Namespace: `stateful-lab15`  
Release: `sts-lab`

## 1. StatefulSet Overview

StatefulSets were used because this lab requires:

- stable pod identity (`pod-0`, `pod-1`, `pod-2`)
- stable per-pod storage (one PVC per pod)
- ordered rollout/scale behavior

### Deployment vs StatefulSet

| Feature | Deployment | StatefulSet |
|---------|------------|-------------|
| Pod identity | Ephemeral/random suffix | Stable ordinal (`name-0`, `name-1`) |
| Storage | Usually shared/static PVC | Per-pod PVC via `volumeClaimTemplates` |
| Ordering | No identity ordering guarantee | Ordered creation/update/termination |
| Service discovery | Service-level only | Pod-level DNS with headless service |

### Headless Service

A headless service (`clusterIP: None`) was added:

- `sts-lab-devops-info-headless`
- enables direct DNS records per pod:
  - `<statefulset>-<ordinal>.<headless-service>.<namespace>.svc.cluster.local`

## 2. Implementation

### Helm templates added/updated

- `k8s/devops-info/templates/statefulset.yaml` (new)
- `k8s/devops-info/templates/service-headless.yaml` (new)
- `k8s/devops-info/templates/deployment.yaml` (deployment disabled when statefulset enabled)
- `k8s/devops-info/templates/pvc.yaml` (shared PVC disabled for statefulset mode)
- `k8s/devops-info/templates/_helpers.tpl` (headless service helper)
- `k8s/devops-info/values.yaml` (statefulset config block)
- `k8s/devops-info/values-statefulset.yaml` (lab-specific values)

### StatefulSet key points

- `kind: StatefulSet`
- `spec.serviceName: sts-lab-devops-info-headless`
- `volumeClaimTemplates` creates one PVC per pod (`data-volume-*`)
- external service kept (`sts-lab-devops-info`, `NodePort`)

## 3. Resource Verification

Command:

```bash
kubectl get po,sts,svc,pvc -n stateful-lab15
```

Output:

```text
NAME                        READY   STATUS    RESTARTS   AGE
pod/sts-lab-devops-info-0   1/1     Running   0          ...
pod/sts-lab-devops-info-1   1/1     Running   0          ...
pod/sts-lab-devops-info-2   1/1     Running   0          ...

NAME                                   READY   AGE
statefulset.apps/sts-lab-devops-info   3/3     ...

NAME                                   TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
service/sts-lab-devops-info            NodePort    10.99.241.30   <none>        80:30084/TCP   ...
service/sts-lab-devops-info-headless   ClusterIP   None           <none>        80/TCP         ...

NAME                                                      STATUS   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/data-volume-sts-lab-devops-info-0   Bound    100Mi      RWO            standard       ...
persistentvolumeclaim/data-volume-sts-lab-devops-info-1   Bound    100Mi      RWO            standard       ...
persistentvolumeclaim/data-volume-sts-lab-devops-info-2   Bound    100Mi      RWO            standard       ...
```

## 4. Network Identity (DNS)

Command (from pod-0):

```bash
kubectl exec -n stateful-lab15 sts-lab-devops-info-0 -- \
  python -c "import socket; hosts=['sts-lab-devops-info-0.sts-lab-devops-info-headless.stateful-lab15.svc.cluster.local','sts-lab-devops-info-1.sts-lab-devops-info-headless.stateful-lab15.svc.cluster.local','sts-lab-devops-info-2.sts-lab-devops-info-headless.stateful-lab15.svc.cluster.local']; [print(h,'->',socket.gethostbyname(h)) for h in hosts]"
```

Output:

```text
sts-lab-devops-info-0.sts-lab-devops-info-headless.stateful-lab15.svc.cluster.local -> 10.244.0.72
sts-lab-devops-info-1.sts-lab-devops-info-headless.stateful-lab15.svc.cluster.local -> 10.244.0.71
sts-lab-devops-info-2.sts-lab-devops-info-headless.stateful-lab15.svc.cluster.local -> 10.244.0.70
```

DNS naming pattern validated:

- `<statefulset>-0.<headless-service>.<namespace>.svc.cluster.local`
- `<statefulset>-1.<headless-service>.<namespace>.svc.cluster.local`
- `<statefulset>-2.<headless-service>.<namespace>.svc.cluster.local`

## 5. Per-Pod Storage Evidence

Requests sent:

- pod-0: 2 hits to `/`
- pod-1: 1 hit to `/`
- pod-2: 1 hit to `/`

Visits endpoint results:

```text
pod0_visits={"visits":2}
pod1_visits={"visits":1}
pod2_visits={"visits":1}
```

Backed file values:

```text
pod0_file=2
pod1_file=1
pod2_file=1
```

This proves each pod has isolated persistent data, not shared counter state.

## 6. Persistence Test (Pod Deletion)

Command sequence:

```bash
kubectl exec -n stateful-lab15 sts-lab-devops-info-0 -- cat /data/visits
kubectl delete pod -n stateful-lab15 sts-lab-devops-info-0
kubectl wait --for=condition=Ready pod/sts-lab-devops-info-0 -n stateful-lab15 --timeout=300s
kubectl exec -n stateful-lab15 sts-lab-devops-info-0 -- cat /data/visits
```

Observed:

```text
pod0_before=2
pod0_after=2
```

Result: data persisted through pod recreation because pod-0 reused its own PVC.

