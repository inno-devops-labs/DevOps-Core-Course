# Lab 15: StatefulSets & Persistent Storage

## 1. StatefulSet Overview

StatefulSet is used when each replica needs a stable identity and its own persistent storage. In this lab the Python application keeps a visits counter in `/data/visits`, so StatefulSet is a better fit than Deployment when each replica must keep a separate counter.

Main differences from Deployment:

- Deployment creates interchangeable pods with random suffixes
- StatefulSet creates ordered pods: `app-0`, `app-1`, `app-2`
- Deployment usually shares one PVC or uses stateless pods
- StatefulSet creates one PVC per pod through `volumeClaimTemplates`
- Deployment scales and replaces pods in any order
- StatefulSet uses ordered creation, update, and termination by default
- StatefulSet pods get stable DNS names through a headless service

Examples of workloads that need StatefulSet behavior:

- PostgreSQL, MySQL, MongoDB, Kafka, Elasticsearch


## 2. Implementation

The Helm chart keeps the Lab 14 `rollout.yaml` for progressive delivery and adds a separate StatefulSet mode controlled by values.

New templates:

- `k8s/devops-python/templates/statefulset.yaml`
- `k8s/devops-python/templates/headless-service.yaml`

New values files:

- `k8s/devops-python/values-statefulset.yaml`
- `k8s/devops-python/values-statefulset-partition.yaml`
- `k8s/devops-python/values-statefulset-ondelete.yaml`

StatefulSet mode is enabled with:

```yaml
workload:
  type: statefulset
```

The StatefulSet points to the headless service:

```yaml
spec:
  serviceName: lab15-stateful-devops-python-headless
  replicas: 3
  podManagementPolicy: OrderedReady
```

Each pod gets its own PVC from `volumeClaimTemplates`:

```yaml
volumeClaimTemplates:
  - metadata:
      name: data-volume
    spec:
      accessModes:
        - ReadWriteOnce
      resources:
        requests:
          storage: 100Mi
```


## 3. Deployment Verification

The namespace and Helm release were created:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab15 λ kubectl create namespace lab15
namespace/lab15 created
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab15 λ helm upgrade --install lab15-stateful k8s/devops-python -n lab15 -f k8s/devops-python/values-statefulset.yaml --timeout 10m
Release "lab15-stateful" does not exist. Installing it now.
NAME: lab15-stateful
LAST DEPLOYED: Sat Apr 25 16:32:46 2026
NAMESPACE: lab15
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
```

After switching the release to the local `lab15` image, the StatefulSet rolled out successfully:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab15 λ helm upgrade lab15-stateful k8s/devops-python -n lab15 -f k8s/devops-python/values-statefulset.yaml --timeout 10m
Release "lab15-stateful" has been upgraded. Happy Helming!
NAME: lab15-stateful
LAST DEPLOYED: Sat Apr 25 16:45:41 2026
NAMESPACE: lab15
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
TEST SUITE: None
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab15 λ kubectl rollout status statefulset/lab15-stateful-devops-python -n lab15 --timeout=300s
statefulset rolling update complete 3 pods at revision lab15-stateful-devops-python-68f678c6cd...
```

Resource verification:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab15 λ kubectl get po,sts,svc,pvc -n lab15 -l app.kubernetes.io/instance=lab15-stateful
NAME                                 READY   STATUS    RESTARTS   AGE
pod/lab15-stateful-devops-python-0   1/1     Running   0          5m56s
pod/lab15-stateful-devops-python-1   1/1     Running   0          39s
pod/lab15-stateful-devops-python-2   1/1     Running   0          80s

NAME                                            READY   AGE
statefulset.apps/lab15-stateful-devops-python   3/3     22m

NAME                                            TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/lab15-stateful-devops-python            NodePort    10.105.188.156   <none>        80:32150/TCP   22m
service/lab15-stateful-devops-python-headless   ClusterIP   None             <none>        80/TCP         22m

NAME                                                               STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/data-volume-lab15-stateful-devops-python-0   Bound    pvc-6b91f75d-e02c-49ae-b077-7b322561a154   100Mi      RWO            standard       <unset>                 22m
persistentvolumeclaim/data-volume-lab15-stateful-devops-python-1   Bound    pvc-f2a1ddc3-2b1d-412e-b7de-8e7a1a391088   100Mi      RWO            standard       <unset>                 22m
persistentvolumeclaim/data-volume-lab15-stateful-devops-python-2   Bound    pvc-7d027d30-93b2-4241-b23a-850805afe452   100Mi      RWO            standard       <unset>                 21m
```

This confirms:

- stable pod names with ordinal suffixes
- one StatefulSet with 3 ready replicas
- external NodePort service for normal access
- headless service with `CLUSTER-IP: None`
- one PVC per pod


## 4. Network Identity

The headless service is named `lab15-stateful-devops-python-headless`.

DNS naming pattern:

```text
<pod-name>.<headless-service>.<namespace>.svc.cluster.local
```

Examples:

```text
lab15-stateful-devops-python-0.lab15-stateful-devops-python-headless.lab15.svc.cluster.local
lab15-stateful-devops-python-1.lab15-stateful-devops-python-headless.lab15.svc.cluster.local
lab15-stateful-devops-python-2.lab15-stateful-devops-python-headless.lab15.svc.cluster.local
```

DNS resolution from pod `0` to pod `1`:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab15 λ kubectl exec lab15-stateful-devops-python-0 -n lab15 -- getent hosts lab15-stateful-devops-python-1.lab15-stateful-devops-python-headless.lab15.svc.cluster.local
Defaulted container "app" out of: app, volume-permissions (init)
10.244.1.43     lab15-stateful-devops-python-1.lab15-stateful-devops-python-headless.lab15.svc.cluster.local
```

DNS resolution from pod `0` to pod `2`:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab15 λ kubectl exec lab15-stateful-devops-python-0 -n lab15 -- getent hosts lab15-stateful-devops-python-2.lab15-stateful-devops-python-headless.lab15.svc.cluster.local
Defaulted container "app" out of: app, volume-permissions (init)
10.244.1.44     lab15-stateful-devops-python-2.lab15-stateful-devops-python-headless.lab15.svc.cluster.local
```


## 5. Per-Pod Storage Evidence

Each pod was accessed through a direct pod port-forward:

```bash
kubectl port-forward pod/lab15-stateful-devops-python-0 -n lab15 15250:5000
kubectl port-forward pod/lab15-stateful-devops-python-1 -n lab15 15251:5000
kubectl port-forward pod/lab15-stateful-devops-python-2 -n lab15 15252:5000
```

The root endpoint was called a different number of times per pod:

- pod `0`: 2 requests
- pod `1`: 1 request
- pod `2`: 3 requests

The `/visits` endpoint returned different values for each pod:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab15 λ curl -s http://127.0.0.1:15250/visits
{"file":"/data/visits","visits":2}
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab15 λ curl -s http://127.0.0.1:15251/visits
{"file":"/data/visits","visits":1}
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab15 λ curl -s http://127.0.0.1:15252/visits
{"file":"/data/visits","visits":3}
```

The files inside the pods matched the endpoint output:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab15 λ kubectl exec lab15-stateful-devops-python-0 -n lab15 -- cat /data/visits
Defaulted container "app" out of: app, volume-permissions (init)
2
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab15 λ kubectl exec lab15-stateful-devops-python-1 -n lab15 -- cat /data/visits
Defaulted container "app" out of: app, volume-permissions (init)
1
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab15 λ kubectl exec lab15-stateful-devops-python-2 -n lab15 -- cat /data/visits
Defaulted container "app" out of: app, volume-permissions (init)
3
```

This proves that each pod has isolated persistent storage.


## 6. Persistence Test

Before deletion, pod `0` had this value:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab15 λ kubectl exec lab15-stateful-devops-python-0 -n lab15 -- cat /data/visits
Defaulted container "app" out of: app, volume-permissions (init)
2
```

The pod was deleted directly:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab15 λ kubectl delete pod lab15-stateful-devops-python-0 -n lab15
pod "lab15-stateful-devops-python-0" deleted from lab15 namespace
```

StatefulSet recreated the same ordinal:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab15 λ kubectl wait pod/lab15-stateful-devops-python-0 -n lab15 --for=condition=Ready --timeout=180s
pod/lab15-stateful-devops-python-0 condition met
```

The pod got a new IP but kept the same name and PVC:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab15 λ kubectl get pod lab15-stateful-devops-python-0 -n lab15 -o wide
NAME                             READY   STATUS    RESTARTS   AGE   IP            NODE       NOMINATED NODE   READINESS GATES
lab15-stateful-devops-python-0   1/1     Running   0          22s   10.244.1.48   minikube   <none>           <none>
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab15 λ kubectl get pvc data-volume-lab15-stateful-devops-python-0 -n lab15
NAME                                         STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
data-volume-lab15-stateful-devops-python-0   Bound    pvc-6b91f75d-e02c-49ae-b077-7b322561a154   100Mi      RWO            standard       <unset>                 16m
```

The visit count was preserved:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab15 λ kubectl exec lab15-stateful-devops-python-0 -n lab15 -- cat /data/visits
Defaulted container "app" out of: app, volume-permissions (init)
2
```


## 7. Update Strategy Bonus

### Partitioned Rolling Update

The partitioned values file uses `partition: 2`.

```yaml
statefulset:
  updateStrategy:
    type: RollingUpdate
    partition: 2
```

The release was updated:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab15 λ helm upgrade lab15-stateful k8s/devops-python -n lab15 -f k8s/devops-python/values-statefulset-partition.yaml --timeout 10m
Release "lab15-stateful" has been upgraded. Happy Helming!
NAME: lab15-stateful
LAST DEPLOYED: Sat Apr 25 16:49:38 2026
NAMESPACE: lab15
STATUS: deployed
REVISION: 3
DESCRIPTION: Upgrade complete
TEST SUITE: None
```

Only one pod was updated because only ordinal `2` is greater than or equal to the partition.

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab15 λ kubectl rollout status statefulset/lab15-stateful-devops-python -n lab15 --timeout=180s
partitioned roll out complete: 1 new pods have been updated...
```

Replica revisions after the partitioned update:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab15 λ kubectl get pods -n lab15 -l app.kubernetes.io/instance=lab15-stateful -o 'custom-columns=NAME:.metadata.name,REVISION:.metadata.labels.controller-revision-hash,READY:.status.containerStatuses[0].ready'
NAME                             REVISION                                  READY
lab15-stateful-devops-python-0   lab15-stateful-devops-python-68f678c6cd   true
lab15-stateful-devops-python-1   lab15-stateful-devops-python-68f678c6cd   true
lab15-stateful-devops-python-2   lab15-stateful-devops-python-58ccd655bb   true
```

Environment values confirmed the same result:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab15 λ kubectl exec lab15-stateful-devops-python-0 -n lab15 -- printenv APP_ENV
Defaulted container "app" out of: app, volume-permissions (init)
statefulset
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab15 λ kubectl exec lab15-stateful-devops-python-2 -n lab15 -- printenv APP_ENV
Defaulted container "app" out of: app, volume-permissions (init)
statefulset-partition
```

### OnDelete Strategy

The OnDelete values file uses:

```yaml
statefulset:
  updateStrategy:
    type: OnDelete
```

The release was updated:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab15 λ helm upgrade lab15-stateful k8s/devops-python -n lab15 -f k8s/devops-python/values-statefulset-ondelete.yaml --timeout 10m
Release "lab15-stateful" has been upgraded. Happy Helming!
NAME: lab15-stateful
LAST DEPLOYED: Sat Apr 25 16:50:56 2026
NAMESPACE: lab15
STATUS: deployed
REVISION: 4
DESCRIPTION: Upgrade complete
TEST SUITE: None
```

The StatefulSet accepted the OnDelete strategy:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab15 λ kubectl get statefulset lab15-stateful-devops-python -n lab15 -o jsonpath='{.spec.updateStrategy.type}{"\n"}'
OnDelete
```

Pods were not recreated automatically after the Helm upgrade:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab15 λ kubectl get pods -n lab15 -l app.kubernetes.io/instance=lab15-stateful -o 'custom-columns=NAME:.metadata.name,REVISION:.metadata.labels.controller-revision-hash,READY:.status.containerStatuses[0].ready'
NAME                             REVISION                                  READY
lab15-stateful-devops-python-0   lab15-stateful-devops-python-68f678c6cd   true
lab15-stateful-devops-python-1   lab15-stateful-devops-python-68f678c6cd   true
lab15-stateful-devops-python-2   lab15-stateful-devops-python-58ccd655bb   true
```

After manually deleting pod `1`, only that pod moved to the OnDelete revision:

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab15 λ kubectl delete pod lab15-stateful-devops-python-1 -n lab15
pod "lab15-stateful-devops-python-1" deleted from lab15 namespace
```

```bash
s3rap1s in ~/devops/DevOps-Core-Course on lab15 λ kubectl exec lab15-stateful-devops-python-1 -n lab15 -- printenv APP_ENV
Defaulted container "app" out of: app, volume-permissions (init)
statefulset-ondelete
```

OnDelete is useful when an operator wants exact manual control over which stateful replicas restart and when. This is common for databases or clustered systems where each member should be drained, checked, or promoted manually.
