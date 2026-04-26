# StatefulSets & Persistent Storage (Lab 15)

This document covers the non-bonus Lab 15 scope:
- StatefulSet concepts and differences from Deployment
- StatefulSet implementation in the Helm chart
- Headless Service and stable pod identity verification
- Per-pod storage isolation and persistence validation

## 1. StatefulSet Overview

StatefulSet is used when an application instance must keep:
- a stable pod identity (`<name>-0`, `<name>-1`, `<name>-2`)
- stable network DNS names
- persistent per-pod storage across pod restarts/re-scheduling

For this lab, StatefulSet is a better fit than Deployment because each replica needs its own persistent data file.

### Deployment vs StatefulSet

| Feature | Deployment | StatefulSet |
|---|---|---|
| Pod names | Random suffix | Stable ordinal suffix (`-0`, `-1`, `-2`) |
| Storage | Shared/independent PVC handling | Per-pod PVC via `volumeClaimTemplates` |
| Network identity | Pod IP changes, no stable pod DNS identity | Stable pod DNS identity through headless service |
| Scaling behavior | Unordered | Ordered by default (`OrderedReady`) |

### Headless Service

A headless service (`clusterIP: None`) is created for StatefulSet:
- service name: `devops-stateful-devops-info-service-headless`
- DNS pattern:
  - `<pod-name>.<headless-service>`
  - `<pod-name>.<headless-service>.<namespace>.svc.cluster.local`

## 2. Implementation Details

### Helm chart changes

Implemented in `k8s/devops-info-service`:

1. Added `templates/statefulset.yaml`
   - `kind: StatefulSet`
   - `serviceName` points to headless service
   - `volumeClaimTemplates` for per-pod PVC provisioning
2. Updated `templates/service.yaml`
   - existing service kept for app access
   - added headless service with `clusterIP: None` when StatefulSet mode is enabled
3. Updated render guards:
   - Deployment renders only when both Rollout and StatefulSet are disabled
   - Rollout renders only when StatefulSet is disabled
   - standalone PVC template is disabled in StatefulSet mode (PVCs are created from template)
4. Added `values-statefulset.yaml`
   - enables StatefulSet
   - disables Rollout
   - uses persistent storage and ClusterIP service

### StatefulSet profile

```yaml
rollout:
  enabled: false

statefulset:
  enabled: true
  podManagementPolicy: OrderedReady
  headlessServiceSuffix: headless

persistence:
  enabled: true
  accessMode: ReadWriteOnce
  size: 100Mi
```

## 3. Resource Verification

Deployment command:

```bash
kubectl create namespace lab15 --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install devops-stateful k8s/devops-info-service \
  -n lab15 \
  -f k8s/devops-info-service/values-statefulset.yaml
kubectl rollout status statefulset/devops-stateful-devops-info-service -n lab15
kubectl get po,sts,svc,pvc -n lab15
```

Observed output:

```text
NAME                                        READY   STATUS    RESTARTS   AGE
pod/devops-stateful-devops-info-service-0   1/1     Running   0          37s
pod/devops-stateful-devops-info-service-1   1/1     Running   0          24s
pod/devops-stateful-devops-info-service-2   1/1     Running   0          12s

NAME                                                   READY   AGE
statefulset.apps/devops-stateful-devops-info-service   3/3     37s

NAME                                                   TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
service/devops-stateful-devops-info-service            ClusterIP   10.98.147.168   <none>        80/TCP    37s
service/devops-stateful-devops-info-service-headless   ClusterIP   None             <none>        80/TCP    37s

NAME                                                                      STATUS   CAPACITY   ACCESS MODES
persistentvolumeclaim/data-volume-devops-stateful-devops-info-service-0   Bound    100Mi      RWO
persistentvolumeclaim/data-volume-devops-stateful-devops-info-service-1   Bound    100Mi      RWO
persistentvolumeclaim/data-volume-devops-stateful-devops-info-service-2   Bound    100Mi      RWO
```

Validation points:
- pods have ordinal names (`-0`, `-1`, `-2`)
- headless service exists (`clusterIP: None`)
- each pod has its own PVC

## 4. Network Identity (DNS)

DNS resolution test from pod-0:

```bash
kubectl exec -n lab15 devops-stateful-devops-info-service-0 -- python -c \
"import socket;print('pod1',socket.gethostbyname('devops-stateful-devops-info-service-1.devops-stateful-devops-info-service-headless.lab15.svc.cluster.local'));print('pod2',socket.gethostbyname('devops-stateful-devops-info-service-2.devops-stateful-devops-info-service-headless.lab15.svc.cluster.local'))"
```

Observed output:

```text
pod1 10.244.0.149
pod2 10.244.0.150
```

App identity check from each pod:

```bash
kubectl exec -n lab15 devops-stateful-devops-info-service-0 -- python -c \
"import json,urllib.request;d=json.loads(urllib.request.urlopen('http://127.0.0.1:5001/').read().decode());print(d['system']['hostname'])"
kubectl exec -n lab15 devops-stateful-devops-info-service-1 -- python -c \
"import json,urllib.request;d=json.loads(urllib.request.urlopen('http://127.0.0.1:5001/').read().decode());print(d['system']['hostname'])"
```

Observed output:

```text
devops-stateful-devops-info-service-0
devops-stateful-devops-info-service-1
```

## 5. Per-Pod Storage Evidence

Different values were written into each pod’s persistent visits file:

```bash
kubectl exec -n lab15 devops-stateful-devops-info-service-0 -- sh -c 'echo 31 > ${VISITS_FILE:-/data/visits}'
kubectl exec -n lab15 devops-stateful-devops-info-service-1 -- sh -c 'echo 7 > ${VISITS_FILE:-/data/visits}'
kubectl exec -n lab15 devops-stateful-devops-info-service-2 -- sh -c 'echo 2 > ${VISITS_FILE:-/data/visits}'

kubectl exec -n lab15 devops-stateful-devops-info-service-0 -- sh -c 'echo -n "pod-0: "; cat ${VISITS_FILE:-/data/visits}'
kubectl exec -n lab15 devops-stateful-devops-info-service-1 -- sh -c 'echo -n "pod-1: "; cat ${VISITS_FILE:-/data/visits}'
kubectl exec -n lab15 devops-stateful-devops-info-service-2 -- sh -c 'echo -n "pod-2: "; cat ${VISITS_FILE:-/data/visits}'
```

Observed output:

```text
pod-0: 31
pod-1: 7
pod-2: 2
```

This confirms each pod uses independent persistent storage.

## 6. Persistence Test

Pod deletion test:

```bash
kubectl delete pod -n lab15 devops-stateful-devops-info-service-0
kubectl wait --for=condition=ready pod/devops-stateful-devops-info-service-0 -n lab15 --timeout=180s
kubectl exec -n lab15 devops-stateful-devops-info-service-0 -- sh -c 'echo -n "pod-0: "; cat ${VISITS_FILE:-/data/visits}'
```

Observed output:

```text
pod-0: 31
```

Result: data persisted after pod recreation, proving StatefulSet + PVC persistence behavior.
