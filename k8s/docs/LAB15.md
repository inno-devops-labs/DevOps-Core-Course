# Kubernetes Lab 15 - StatefulSets and Persistent Storage

Lab 15 converts the Helm chart's default workload from a Deployment to a StatefulSet so the Lab 12 visits counter can demonstrate stable pod identity and per-pod persistent storage. I used a separate `lab15` namespace and a direct Helm release named `lab15`, leaving the Lab 13 ArgoCD applications untouched. Those ArgoCD applications still target branch `lab13`, so this Lab 15 chart default change does not affect them unless their target revision is changed later.

The chart is now version `0.7.0`. Default rendering creates a StatefulSet, a headless Service, the normal ClusterIP Service, and `volumeClaimTemplates`. Argo Rollouts mode still renders a Rollout and standalone PVC, and a Deployment fallback remains available with `statefulset.enabled=false` and `deployment.enabled=true`.

## StatefulSet Concepts

StatefulSets are useful when a workload needs identity or storage that belongs to a specific replica. Databases, queues, and distributed systems often need this. The Python app is not a database, but its `/data/visits` counter is a small, inspectable state file that makes the StatefulSet behavior easy to prove.

| Feature | Deployment | StatefulSet |
| --- | --- | --- |
| Pod names | Random ReplicaSet suffixes | Stable ordinal names such as `app-0` |
| Storage | Usually shared or manually named PVCs | Per-pod PVCs from `volumeClaimTemplates` |
| Scaling | Any order | Ordered by default |
| Network identity | Service load balancing hides individual pods | Pod DNS names are stable through the headless Service |
| Best use | Stateless apps and progressive delivery | Stateful replicas that need stable identity or storage |

A headless Service uses `clusterIP: None`. Instead of giving one virtual service IP, Kubernetes DNS publishes records for the selected pods. For this release the pattern is:

```text
<pod-name>.lab15-devops-app-py-headless.lab15.svc.cluster.local
```

## Chart Implementation

The main chart changes are:

- `templates/statefulset.yaml` renders the default `apps/v1 StatefulSet`.
- `templates/service-headless.yaml` renders `lab15-devops-app-py-headless` with `clusterIP: None`.
- `values-statefulset.yaml` sets `replicaCount: 3`, image tag `1.12`, and the default `RollingUpdate` strategy.
- The shared pod template mounts `data-volume` in all modes, but StatefulSet mode gets that volume from `volumeClaimTemplates`; Rollout and Deployment modes still use the standalone PVC.

The relevant values shape is:

```yaml
deployment:
  enabled: false

statefulset:
  enabled: true
  podManagementPolicy: OrderedReady
  revisionHistoryLimit: 5
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 0

persistence:
  enabled: true
  mountPath: /data
  accessModes:
    - ReadWriteOnce
  size: 100Mi
```

<details>
<summary>static Helm checks</summary>

```text
$ helm lint k8s/devops-app-py
==> Linting k8s/devops-app-py
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed

$ helm template lab15 k8s/devops-app-py --namespace lab15 -f k8s/devops-app-py/values-statefulset.yaml | rg "^kind:|serviceName:|volumeClaimTemplates:|clusterIP:|updateStrategy:|partition:"
kind: ServiceAccount
kind: Secret
kind: ConfigMap
kind: ConfigMap
kind: Service
  clusterIP: None
kind: Service
kind: StatefulSet
  serviceName: lab15-devops-app-py-headless
  updateStrategy:
      partition: 0
  volumeClaimTemplates:
kind: Job
kind: Job

$ helm template lab15-rollout k8s/devops-app-py --namespace lab15 -f k8s/devops-app-py/values-rollout-canary.yaml | rg "^kind:|claimName:|volumeClaimTemplates:"
kind: ServiceAccount
kind: Secret
kind: ConfigMap
kind: ConfigMap
kind: PersistentVolumeClaim
kind: Service
kind: Rollout
            claimName: lab15-rollout-devops-app-py-data
kind: Job
kind: Job

$ helm template lab15-deploy k8s/devops-app-py --namespace lab15 --set statefulset.enabled=false --set deployment.enabled=true | rg "^kind:|claimName:|volumeClaimTemplates:"
kind: ServiceAccount
kind: Secret
kind: ConfigMap
kind: ConfigMap
kind: PersistentVolumeClaim
kind: Service
kind: Deployment
            claimName: lab15-deploy-devops-app-py-data
kind: Job
kind: Job
```

</details>

## Cluster Setup

The saved Docker-backed `minikube` profile existed but was stopped. A normal restart recovered it; no profile deletion was needed. The `standard` storage class is the minikube hostPath provisioner, which is sufficient for this local StatefulSet lab.

<details>
<summary>cluster recovery and storage class</summary>

```text
$ minikube status -p minikube
minikube
type: Control Plane
host: Stopped
kubelet: Stopped
apiserver: Stopped
kubeconfig: Stopped


$ minikube start -p minikube --driver=docker
* minikube v1.38.1 on Arch
* Using the docker driver based on existing profile
* Starting "minikube" primary control-plane node in "minikube" cluster
* Pulling base image v0.0.50 ...
* Verifying Kubernetes components...
  - Using image gcr.io/k8s-minikube/storage-provisioner:v5
* Enabled addons: default-storageclass, storage-provisioner
* Done! kubectl is now configured to use "minikube" cluster and "default" namespace by default

$ kubectl get nodes -o wide
NAME       STATUS   ROLES           AGE   VERSION   INTERNAL-IP    EXTERNAL-IP   OS-IMAGE                         KERNEL-VERSION    CONTAINER-RUNTIME
minikube   Ready    control-plane   8d    v1.35.1   192.168.49.2   <none>        Debian GNU/Linux 12 (bookworm)   7.0.3-1-cachyos   docker://29.2.1

$ kubectl get storageclass
NAME                 PROVISIONER                RECLAIMPOLICY   VOLUMEBINDINGMODE   ALLOWVOLUMEEXPANSION   AGE
standard (default)   k8s.io/minikube-hostpath   Delete          Immediate           false                  8d

$ helm version --short
v4.1.4+g05fa379
```

</details>

After installation, the StatefulSet created three ordered pods and three automatically named PVCs:

<details>
<summary>StatefulSet, services, and PVCs</summary>

```text
$ kubectl wait --for=condition=Ready pod -l app.kubernetes.io/instance=lab15 -n lab15
pod/lab15-devops-app-py-0 condition met
pod/lab15-devops-app-py-1 condition met
pod/lab15-devops-app-py-2 condition met

$ kubectl get po,sts,svc,pvc -n lab15 -o wide
NAME                        READY   STATUS    RESTARTS   AGE   IP            NODE       NOMINATED NODE   READINESS GATES
pod/lab15-devops-app-py-0   1/1     Running   0          67s   10.244.0.65   minikube   <none>           <none>
pod/lab15-devops-app-py-1   1/1     Running   0          16s   10.244.0.66   minikube   <none>           <none>
pod/lab15-devops-app-py-2   1/1     Running   0          9s    10.244.0.67   minikube   <none>           <none>

NAME                                   READY   AGE   CONTAINERS      IMAGES
statefulset.apps/lab15-devops-app-py   3/3     67s   devops-app-py   localt0aster/devops-app-py:1.12

NAME                                   TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE   SELECTOR
service/lab15-devops-app-py-headless   ClusterIP   None           <none>        80/TCP    67s   app.kubernetes.io/instance=lab15,app.kubernetes.io/name=devops-app-py
service/lab15-devops-app-py-service    ClusterIP   10.96.64.122   <none>        80/TCP    67s   app.kubernetes.io/instance=lab15,app.kubernetes.io/name=devops-app-py

NAME                                                      STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE   VOLUMEMODE
persistentvolumeclaim/data-volume-lab15-devops-app-py-0   Bound    pvc-fb42ff13-ec37-4604-9833-84381c98e194   100Mi      RWO            standard       <unset>                 67s   Filesystem
persistentvolumeclaim/data-volume-lab15-devops-app-py-1   Bound    pvc-e2f72f28-1577-4b27-82b4-e5b0eb001d88   100Mi      RWO            standard       <unset>                 16s   Filesystem
persistentvolumeclaim/data-volume-lab15-devops-app-py-2   Bound    pvc-32239c77-37ff-4eb5-89a4-86f1be4a84e7   100Mi      RWO            standard       <unset>                 9s    Filesystem
```

</details>

## Network Identity

The application image includes BusyBox tooling, so I could run DNS checks directly from pod 0. Pod 1 and pod 2 both resolve through the headless Service using their stable ordinal DNS names.

<details>
<summary>pod DNS resolution</summary>

```text
$ kubectl exec -n lab15 lab15-devops-app-py-0 -- nslookup lab15-devops-app-py-1.lab15-devops-app-py-headless.lab15.svc.cluster.local
Server:		10.96.0.10
Address:	10.96.0.10:53


Name:	lab15-devops-app-py-1.lab15-devops-app-py-headless.lab15.svc.cluster.local
Address: 10.244.0.66


$ kubectl exec -n lab15 lab15-devops-app-py-0 -- nslookup lab15-devops-app-py-2.lab15-devops-app-py-headless.lab15.svc.cluster.local
Server:		10.96.0.10
Address:	10.96.0.10:53


Name:	lab15-devops-app-py-2.lab15-devops-app-py-headless.lab15.svc.cluster.local
Address: 10.244.0.67
```

</details>

## Per-Pod Storage

I port-forwarded each pod directly and hit `/` a different number of times. Each pod kept its own `/data/visits` file, proving that the PVCs are per ordinal rather than shared behind the normal Service.

<details>
<summary>per-pod visit counters</summary>

```text
$ kubectl port-forward pod/lab15-devops-app-py-0 -n lab15 18080:5000
$ kubectl port-forward pod/lab15-devops-app-py-1 -n lab15 18081:5000
$ kubectl port-forward pod/lab15-devops-app-py-2 -n lab15 18082:5000

$ curl -sS 127.0.0.1:18080/visits | jq .
{
  "visits": 0
}

$ curl -sS 127.0.0.1:18081/visits | jq .
{
  "visits": 0
}

$ curl -sS 127.0.0.1:18082/visits | jq .
{
  "visits": 0
}

$ curl -sS 127.0.0.1:18080/ >/dev/null

$ curl -sS 127.0.0.1:18080/ >/dev/null

$ curl -sS 127.0.0.1:18081/ >/dev/null

$ curl -sS 127.0.0.1:18082/ >/dev/null

$ curl -sS 127.0.0.1:18082/ >/dev/null

$ curl -sS 127.0.0.1:18082/ >/dev/null

$ curl -sS 127.0.0.1:18080/visits | jq .
{
  "visits": 2
}

$ curl -sS 127.0.0.1:18081/visits | jq .
{
  "visits": 1
}

$ curl -sS 127.0.0.1:18082/visits | jq .
{
  "visits": 3
}
```

</details>

Deleting pod 0 changed its IP address but preserved the visit count because the replacement pod reused `data-volume-lab15-devops-app-py-0`.

<details>
<summary>persistence after pod deletion</summary>

```text
$ kubectl exec -n lab15 lab15-devops-app-py-0 -- cat /data/visits
2

$ kubectl delete pod -n lab15 lab15-devops-app-py-0
pod "lab15-devops-app-py-0" deleted from lab15 namespace

$ kubectl wait --for=condition=Ready pod/lab15-devops-app-py-0 -n lab15
pod/lab15-devops-app-py-0 condition met

$ kubectl get pod -n lab15 lab15-devops-app-py-0 -o wide
NAME                    READY   STATUS    RESTARTS   AGE   IP            NODE       NOMINATED NODE   READINESS GATES
lab15-devops-app-py-0   1/1     Running   0          7s    10.244.0.68   minikube   <none>           <none>

$ kubectl exec -n lab15 lab15-devops-app-py-0 -- cat /data/visits
2
```

</details>

## Bonus - Update Strategies

With `RollingUpdate` and `partition: 2`, only pods with ordinal `>= 2` update. The annotation change below moved pod 2 to `partition-v2`; pods 0 and 1 stayed on `stateful-v1`.

<details>
<summary>partitioned RollingUpdate</summary>

```text
$ cat /tmp/lab15/partition.values.yaml
podAnnotations:
  lab15-version: partition-v2
statefulset:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 2

$ helm upgrade lab15 k8s/devops-app-py -n lab15 -f k8s/devops-app-py/values-statefulset.yaml -f /tmp/lab15/partition.values.yaml
Release "lab15" has been upgraded. Happy Helming!
NAME: lab15
LAST DEPLOYED: Thu May  7 20:22:57 2026
NAMESPACE: lab15
STATUS: deployed
REVISION: 3
DESCRIPTION: Upgrade complete
TEST SUITE: None
$ kubectl get pods -n lab15 -l app.kubernetes.io/instance=lab15 -o json | jq -r ...
lab15-devops-app-py-0	stateful-v1	2026-05-07T17:21:33Z
lab15-devops-app-py-1	stateful-v1	2026-05-07T17:19:58Z
lab15-devops-app-py-2	partition-v2	2026-05-07T17:22:07Z

$ kubectl get sts lab15-devops-app-py -n lab15 -o json | jq ...
{
  "currentRevision": "lab15-devops-app-py-5d8fd446ff",
  "updateRevision": "lab15-devops-app-py-5bb76d9794",
  "currentReplicas": 2,
  "updatedReplicas": 1,
  "readyReplicas": 3
}
```

</details>

`OnDelete` is useful when an operator wants to control exactly when each stateful replica restarts. After switching to `OnDelete`, no existing pod picked up `ondelete-v3`. Only the manually deleted ordinal 1 was recreated with the new annotation.

<details>
<summary>OnDelete update strategy</summary>

```text
$ cat /tmp/lab15/rolling-all.values.yaml
podAnnotations:
  lab15-version: partition-v2
statefulset:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 0

$ helm upgrade lab15 k8s/devops-app-py -n lab15 -f k8s/devops-app-py/values-statefulset.yaml -f /tmp/lab15/rolling-all.values.yaml
Release "lab15" has been upgraded. Happy Helming!
NAME: lab15
LAST DEPLOYED: Thu May  7 20:24:40 2026
NAMESPACE: lab15
STATUS: deployed
REVISION: 6
DESCRIPTION: Upgrade complete
TEST SUITE: None

$ kubectl get pods -n lab15 -l app.kubernetes.io/instance=lab15 -o json | jq -r ...
lab15-devops-app-py-0	partition-v2	2026-05-07T17:23:44Z
lab15-devops-app-py-1	partition-v2	2026-05-07T17:24:42Z
lab15-devops-app-py-2	partition-v2	2026-05-07T17:22:07Z

$ cat /tmp/lab15/ondelete.values.yaml
podAnnotations:
  lab15-version: ondelete-v3
statefulset:
  updateStrategy:
    type: OnDelete

$ helm upgrade lab15 k8s/devops-app-py -n lab15 -f k8s/devops-app-py/values-statefulset.yaml -f /tmp/lab15/ondelete.values.yaml
Release "lab15" has been upgraded. Happy Helming!
NAME: lab15
LAST DEPLOYED: Thu May  7 20:24:43 2026
NAMESPACE: lab15
STATUS: deployed
REVISION: 7
DESCRIPTION: Upgrade complete
TEST SUITE: None

$ kubectl get pods -n lab15 -l app.kubernetes.io/instance=lab15 -o json | jq -r ...
lab15-devops-app-py-0	partition-v2	2026-05-07T17:23:44Z
lab15-devops-app-py-1	partition-v2	2026-05-07T17:24:42Z
lab15-devops-app-py-2	partition-v2	2026-05-07T17:22:07Z

$ kubectl delete pod -n lab15 lab15-devops-app-py-1
pod "lab15-devops-app-py-1" deleted from lab15 namespace

$ kubectl wait --for=condition=Ready pod/lab15-devops-app-py-1 -n lab15
pod/lab15-devops-app-py-1 condition met

$ kubectl get pods -n lab15 -l app.kubernetes.io/instance=lab15 -o json | jq -r ...
lab15-devops-app-py-0	partition-v2	2026-05-07T17:23:44Z
lab15-devops-app-py-1	ondelete-v3	2026-05-07T17:25:15Z
lab15-devops-app-py-2	partition-v2	2026-05-07T17:22:07Z
```

</details>

## Final State

After the bonus tests, I restored the release to the default Lab 15 values: `RollingUpdate`, partition `0`, and `lab15-version=stateful-v1`. All three pods are ready and all three PVCs remain bound.

<details>
<summary>final healthy state</summary>

```text
$ kubectl wait --for=condition=Ready pod -l app.kubernetes.io/instance=lab15 -n lab15
pod/lab15-devops-app-py-0 condition met
pod/lab15-devops-app-py-1 condition met
pod/lab15-devops-app-py-2 condition met

$ kubectl get po,sts,svc,pvc -n lab15 -o wide
NAME                        READY   STATUS    RESTARTS   AGE   IP            NODE       NOMINATED NODE   READINESS GATES
pod/lab15-devops-app-py-0   1/1     Running   0          17s   10.244.0.77   minikube   <none>           <none>
pod/lab15-devops-app-py-1   1/1     Running   0          25s   10.244.0.76   minikube   <none>           <none>
pod/lab15-devops-app-py-2   1/1     Running   0          32s   10.244.0.75   minikube   <none>           <none>

NAME                                   READY   AGE    CONTAINERS      IMAGES
statefulset.apps/lab15-devops-app-py   3/3     7m1s   devops-app-py   localt0aster/devops-app-py:1.12

NAME                                   TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE    SELECTOR
service/lab15-devops-app-py-headless   ClusterIP   None           <none>        80/TCP    7m1s   app.kubernetes.io/instance=lab15,app.kubernetes.io/name=devops-app-py
service/lab15-devops-app-py-service    ClusterIP   10.96.64.122   <none>        80/TCP    7m1s   app.kubernetes.io/instance=lab15,app.kubernetes.io/name=devops-app-py

NAME                                                      STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE     VOLUMEMODE
persistentvolumeclaim/data-volume-lab15-devops-app-py-0   Bound    pvc-fb42ff13-ec37-4604-9833-84381c98e194   100Mi      RWO            standard       <unset>                 7m1s    Filesystem
persistentvolumeclaim/data-volume-lab15-devops-app-py-1   Bound    pvc-e2f72f28-1577-4b27-82b4-e5b0eb001d88   100Mi      RWO            standard       <unset>                 6m10s   Filesystem
persistentvolumeclaim/data-volume-lab15-devops-app-py-2   Bound    pvc-32239c77-37ff-4eb5-89a4-86f1be4a84e7   100Mi      RWO            standard       <unset>                 6m3s    Filesystem

$ kubectl get pods -n lab15 -l app.kubernetes.io/instance=lab15 -o json | jq -r ...
lab15-devops-app-py-0	stateful-v1	Running
lab15-devops-app-py-1	stateful-v1	Running
lab15-devops-app-py-2	stateful-v1	Running
```

</details>

The Lab 15 checklist is complete: StatefulSet guarantees are documented, the chart renders a StatefulSet with `volumeClaimTemplates`, the headless Service resolves pod identities, each pod has its own PVC-backed visit counter, pod deletion preserves data, and both bonus update strategies were implemented and verified.
