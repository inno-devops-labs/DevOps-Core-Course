# Lab 15 - StatefulSets and Persistent Storage

## Submission Status

Lab 15 is complete and verified with text terminal evidence. Screenshots are not required because the report includes exact commands and outputs for resource creation, DNS resolution, per-pod PVC isolation, persistence after pod deletion, and the bonus update strategies.

Completed checklist:

- StatefulSet guarantees documented.
- Helm chart renders `StatefulSet` instead of `Deployment` or `Rollout` in Lab 15 mode.
- Headless Service is created with `clusterIP: None`.
- Each StatefulSet pod receives an individual PVC through `volumeClaimTemplates`.
- DNS identity was tested with a fully qualified StatefulSet pod name.
- Per-pod storage isolation was proven with different `/data/visits` values.
- Persistence was proven by deleting pod `-0` and reading the same visit count after recreation.
- Bonus update strategies were implemented and rendered: partitioned `RollingUpdate` and `OnDelete`.

## Implementation Summary

The Helm chart now supports a StatefulSet deployment mode for the visits counter application. The Lab 14 Argo Rollout templates remain in the chart for progressive delivery work, while Lab 15 is enabled with the dedicated values file:

```bash
helm upgrade --install devops-info-stateful k8s/devops-info-service \
  --namespace lab15 \
  --create-namespace \
  -f k8s/devops-info-service/values-statefulset.yaml
```

Implemented files:

- [`devops-info-service/templates/statefulset.yaml`](devops-info-service/templates/statefulset.yaml)
- [`devops-info-service/templates/headless-service.yaml`](devops-info-service/templates/headless-service.yaml)
- [`devops-info-service/values-statefulset.yaml`](devops-info-service/values-statefulset.yaml)
- [`devops-info-service/values.yaml`](devops-info-service/values.yaml)
- [`devops-info-service/templates/_helpers.tpl`](devops-info-service/templates/_helpers.tpl)
- [`devops-info-service/templates/NOTES.txt`](devops-info-service/templates/NOTES.txt)

The StatefulSet profile disables the Rollout path and renders:

```text
kind: ServiceAccount
kind: Service
kind: Service
kind: StatefulSet
```

No standalone `PersistentVolumeClaim`, `Deployment`, or `Rollout` is rendered in StatefulSet mode. Storage comes from `volumeClaimTemplates`, so each pod gets its own PVC.

## StatefulSet Overview

A Deployment is best for interchangeable stateless pods. Its pods have generated names, can be replaced in any order, and usually share the same service identity. A StatefulSet is best when each replica needs a stable identity and stable storage.

Key differences:

| Feature | Deployment or Rollout | StatefulSet |
| --- | --- | --- |
| Pod names | Random ReplicaSet suffix | Stable ordinal names like `app-0`, `app-1`, `app-2` |
| Network identity | Service-level load balancing | Per-pod DNS through a headless Service |
| Storage | Shared PVC or ephemeral volumes | One PVC per pod from `volumeClaimTemplates` |
| Scaling | Pods can appear in any order | Ordered by default, `0 -> 1 -> 2` |
| Updates | Optimized for stateless rollout traffic | Preserves identity and storage during updates |

StatefulSet examples include PostgreSQL, MySQL, MongoDB, Kafka, RabbitMQ, Elasticsearch, Cassandra, and any workload where each replica owns data.

## Headless Service

The chart creates a headless Service with `clusterIP: None`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: devops-info-stateful-devops-info-service-headless
spec:
  clusterIP: None
```

The StatefulSet points `spec.serviceName` at that headless Service:

```yaml
spec:
  serviceName: devops-info-stateful-devops-info-service-headless
  replicas: 3
```

DNS pattern:

```text
<pod-name>.<headless-service>.<namespace>.svc.cluster.local
```

For this release:

```text
devops-info-stateful-devops-info-service-0.devops-info-stateful-devops-info-service-headless.lab15.svc.cluster.local
devops-info-stateful-devops-info-service-1.devops-info-stateful-devops-info-service-headless.lab15.svc.cluster.local
devops-info-stateful-devops-info-service-2.devops-info-stateful-devops-info-service-headless.lab15.svc.cluster.local
```

## Persistent Storage

The app stores its visit counter at `/data/visits` through the existing `VISITS_FILE=/data/visits` ConfigMap value. In StatefulSet mode, the pod mounts `app-data` at `/data`, and `app-data` is supplied by `volumeClaimTemplates`:

```yaml
volumeClaimTemplates:
  - metadata:
      name: app-data
    spec:
      accessModes:
        - ReadWriteOnce
      resources:
        requests:
          storage: 100Mi
```

Kubernetes creates one PVC per pod:

```text
app-data-devops-info-stateful-devops-info-service-0
app-data-devops-info-stateful-devops-info-service-1
app-data-devops-info-stateful-devops-info-service-2
```

Deleting a pod does not delete its PVC, so the replacement pod with the same ordinal remounts the same data.

## Resource Verification

Local Helm validation was executed on May 7, 2026:

```bash
helm lint k8s/devops-info-service
```

Output:

```text
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

Dry-run install was executed:

```bash
helm install --dry-run --debug devops-info-stateful k8s/devops-info-service \
  -n lab15 \
  --create-namespace \
  -f k8s/devops-info-service/values-statefulset.yaml
```

Important output:

```text
NAME: devops-info-stateful
NAMESPACE: lab15
STATUS: pending-install
REVISION: 1
DESCRIPTION: Dry run complete
```

Rendered StatefulSet proof:

```bash
helm template devops-info-stateful k8s/devops-info-service \
  -n lab15 \
  -f k8s/devops-info-service/values-statefulset.yaml \
  --show-only templates/statefulset.yaml
```

Important output:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: devops-info-stateful-devops-info-service
spec:
  serviceName: devops-info-stateful-devops-info-service-headless
  replicas: 3
  podManagementPolicy: OrderedReady
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 0
  volumeClaimTemplates:
    - metadata:
        name: app-data
      spec:
        accessModes:
          - ReadWriteOnce
        resources:
          requests:
            storage: 100Mi
```

Rendered headless Service proof:

```bash
helm template devops-info-stateful k8s/devops-info-service \
  -n lab15 \
  -f k8s/devops-info-service/values-statefulset.yaml \
  --show-only templates/headless-service.yaml
```

Important output:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: devops-info-stateful-devops-info-service-headless
spec:
  clusterIP: None
  selector:
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: devops-info-stateful
```

## Minikube Repair

The old local minikube profile was corrupted, so it was recreated before running the lab. Initial failure:

```text
X Exiting due to K8S_APISERVER_MISSING: wait 6m0s for node: wait for apiserver proc: apiserver process never appeared
failed to run Kubelet: unable to load bootstrap kubeconfig: stat /etc/kubernetes/bootstrap-kubelet.conf: no such file or directory
```

The profile was recreated:

```bash
minikube delete
minikube start --driver=docker
```

Successful start output:

```text
* Configuring bridge CNI (Container Networking Interface) ...
* Verifying Kubernetes components...
  - Using image gcr.io/k8s-minikube/storage-provisioner:v5
* Enabled addons: storage-provisioner, default-storageclass
* Done! kubectl is now configured to use "minikube" cluster and "default" namespace by default
```

Cluster status:

```bash
minikube status
```

Output:

```text
minikube
type: Control Plane
host: Running
kubelet: Running
apiserver: Running
kubeconfig: Configured
```

Node and storage verification:

```bash
kubectl get nodes
kubectl get storageclass
```

Output:

```text
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   8s    v1.35.1

NAME                 PROVISIONER                RECLAIMPOLICY   VOLUMEBINDINGMODE   ALLOWVOLUMEEXPANSION   AGE
standard (default)   k8s.io/minikube-hostpath   Delete          Immediate           false                  5s
```

## Live Cluster Verification

The StatefulSet release was installed on May 7, 2026:

```bash
helm upgrade --install devops-info-stateful k8s/devops-info-service \
  --namespace lab15 \
  --create-namespace \
  -f k8s/devops-info-service/values-statefulset.yaml \
  --wait \
  --timeout 5m
```

Output:

```text
Release "devops-info-stateful" does not exist. Installing it now.
NAME: devops-info-stateful
LAST DEPLOYED: Thu May  7 23:37:54 2026
NAMESPACE: lab15
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
```

Helm release verification:

```bash
helm list -n lab15
```

Output:

```text
NAME                 NAMESPACE  REVISION  UPDATED                                  STATUS    CHART                       APP VERSION
devops-info-stateful lab15      1         2026-05-07 23:37:54.389294531 +0300 MSK  deployed  devops-info-service-0.2.0  1.0.0
```

Resource verification:

```bash
kubectl get po,sts,svc,pvc -n lab15
```

Output:

```text
NAME                                             READY   STATUS    RESTARTS   AGE
pod/devops-info-stateful-devops-info-service-0   1/1     Running   0          65s
pod/devops-info-stateful-devops-info-service-1   1/1     Running   0          51s
pod/devops-info-stateful-devops-info-service-2   1/1     Running   0          37s

NAME                                                        READY   AGE
statefulset.apps/devops-info-stateful-devops-info-service   3/3     65s

NAME                                                        TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
service/devops-info-stateful-devops-info-service            ClusterIP   10.107.125.83   <none>        80/TCP    65s
service/devops-info-stateful-devops-info-service-headless   ClusterIP   None            <none>        80/TCP    65s

NAME                                                                        STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/app-data-devops-info-stateful-devops-info-service-0   Bound    pvc-bbda46bd-330c-4b6d-b202-f4b18be333e3   100Mi      RWO            standard       <unset>                 65s
persistentvolumeclaim/app-data-devops-info-stateful-devops-info-service-1   Bound    pvc-9e91a004-5224-4777-8d4a-93f1197a5133   100Mi      RWO            standard       <unset>                 51s
persistentvolumeclaim/app-data-devops-info-stateful-devops-info-service-2   Bound    pvc-fbc8c099-47e1-488b-aed3-0426ef58f23e   100Mi      RWO            standard       <unset>                 37s
```

## Network Identity Verification

Use pod-to-pod DNS through the headless Service:

```bash
kubectl exec -n lab15 devops-info-stateful-devops-info-service-0 -- \
  python -c 'import socket; name="devops-info-stateful-devops-info-service-1.devops-info-stateful-devops-info-service-headless.lab15.svc.cluster.local"; print(name); print(socket.gethostbyname_ex(name))'
```

Output:

```text
devops-info-stateful-devops-info-service-1.devops-info-stateful-devops-info-service-headless.lab15.svc.cluster.local
('devops-info-stateful-devops-info-service-1.devops-info-stateful-devops-info-service-headless.lab15.svc.cluster.local', [], ['10.244.0.5'])
```

The lookup proves the stable network identity for pod ordinal `1`. The fully qualified form is:

```text
devops-info-stateful-devops-info-service-1.devops-info-stateful-devops-info-service-headless.lab15.svc.cluster.local
```

## Per-Pod Storage Evidence

Each pod was called directly from inside its own container so the request increments only that pod's mounted visits file:

```bash
kubectl exec -n lab15 devops-info-stateful-devops-info-service-0 -- \
  python -c 'import json, urllib.request; url="http://127.0.0.1:5000/"; print(json.load(urllib.request.urlopen(url))["visits"]["count"]); print(json.load(urllib.request.urlopen(url))["visits"]["count"])'

kubectl exec -n lab15 devops-info-stateful-devops-info-service-1 -- \
  python -c 'import json, urllib.request; url="http://127.0.0.1:5000/"; print(json.load(urllib.request.urlopen(url))["visits"]["count"])'

kubectl exec -n lab15 devops-info-stateful-devops-info-service-2 -- \
  python -c 'import json, urllib.request; url="http://127.0.0.1:5000/"; print(json.load(urllib.request.urlopen(url))["visits"]["count"]); print(json.load(urllib.request.urlopen(url))["visits"]["count"]); print(json.load(urllib.request.urlopen(url))["visits"]["count"])'
```

Outputs:

```text
pod-0:
1
2

pod-1:
1

pod-2:
1
2
3
```

Then inspect each visits file:

```bash
kubectl exec -n lab15 devops-info-stateful-devops-info-service-0 -- cat /data/visits
kubectl exec -n lab15 devops-info-stateful-devops-info-service-1 -- cat /data/visits
kubectl exec -n lab15 devops-info-stateful-devops-info-service-2 -- cat /data/visits
```

Output:

```text
pod-0:
2

pod-1:
1

pod-2:
3
```

Different counts prove per-pod storage isolation.

## Persistence Test

Delete one pod, not the StatefulSet:

```bash
kubectl exec -n lab15 devops-info-stateful-devops-info-service-0 -- cat /data/visits
kubectl delete pod -n lab15 devops-info-stateful-devops-info-service-0
kubectl wait --for=condition=Ready pod/devops-info-stateful-devops-info-service-0 -n lab15 --timeout=120s
kubectl exec -n lab15 devops-info-stateful-devops-info-service-0 -- cat /data/visits
```

Output:

```text
2
pod "devops-info-stateful-devops-info-service-0" deleted from lab15 namespace
pod/devops-info-stateful-devops-info-service-0 condition met
2
```

The value before and after deletion is the same because pod `-0` remounted PVC `app-data-devops-info-stateful-devops-info-service-0`.

The recreated pod has a new pod IP, while the PVC name and stored data remained stable:

```bash
kubectl get pod devops-info-stateful-devops-info-service-0 -n lab15 -o wide
kubectl get pvc app-data-devops-info-stateful-devops-info-service-0 -n lab15
```

Output:

```text
NAME                                         READY   STATUS    RESTARTS   AGE   IP           NODE
devops-info-stateful-devops-info-service-0   1/1     Running   0          56s   10.244.0.8   minikube

NAME                                                  STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
app-data-devops-info-stateful-devops-info-service-0   Bound    pvc-bbda46bd-330c-4b6d-b202-f4b18be333e3   100Mi      RWO            standard       <unset>                 4m34s
```

## Bonus - Update Strategies

Partitioned rolling update is configurable:

```bash
helm template devops-info-stateful k8s/devops-info-service \
  -n lab15 \
  -f k8s/devops-info-service/values-statefulset.yaml \
  --set statefulset.updateStrategy.rollingUpdate.partition=2 \
  --show-only templates/statefulset.yaml
```

Output:

```text
19:  updateStrategy:
20:    type: RollingUpdate
22:      partition: 2
```

With `partition: 2`, only pods with ordinal `>= 2` update automatically. For a three-replica StatefulSet, that means only pod `-2` updates.

`OnDelete` is also supported:

```bash
helm template devops-info-stateful k8s/devops-info-service \
  -n lab15 \
  -f k8s/devops-info-service/values-statefulset.yaml \
  --set statefulset.updateStrategy.type=OnDelete \
  --show-only templates/statefulset.yaml
```

Output:

```text
19:  updateStrategy:
20:    type: OnDelete
```

`OnDelete` is useful for stateful systems where an operator wants to update each replica manually after checking replication health, backups, or quorum.

## Final Checklist

| Requirement | Evidence |
| --- | --- |
| StatefulSet guarantees documented | `StatefulSet Overview` section |
| `statefulset.yaml` created | `devops-info-service/templates/statefulset.yaml` |
| `volumeClaimTemplates` configured | Rendered StatefulSet proof and live PVC output |
| Headless Service created | `devops-info-service/templates/headless-service.yaml` and live service output |
| Per-pod PVCs verified | `kubectl get po,sts,svc,pvc -n lab15` output |
| DNS resolution tested | `socket.gethostbyname_ex(...)` output for pod `-1` |
| Per-pod storage isolation proven | `/data/visits` values `2`, `1`, `3` |
| Persistence test passed | Pod `-0` deleted, recreated, and `/data/visits` stayed `2` |
| Bonus partitioned rolling update | Rendered `partition: 2` |
| Bonus `OnDelete` strategy | Rendered `type: OnDelete` |
