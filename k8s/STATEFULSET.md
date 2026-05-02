# Lab 15 Report - StatefulSets and Persistent Storage

## Introduction

In this lab I changed my Helm chart from a stateless deployment style to a StatefulSet-based deployment. The main reason is that my application now has a persistent visits counter stored in a file, so each pod should have its own storage and stable network identity.

I also verified that:

- pods get stable names
- every pod gets its own PVC
- pods can resolve each other through the headless service
- the visit counter is different for each pod
- the data stays after deleting a pod

For the bonus part, I also checked partitioned rolling updates and the `OnDelete` strategy.

## What I Changed in the Chart

For this lab I updated the chart in `k8s/myapp`.

Main changes:

- added `templates/statefulset.yaml`
- added `templates/headless-service.yaml`
- added values file `values-statefulset.yaml`
- added bonus values files for partitioned update and `OnDelete`
- kept `rollout.yaml` for reference from the previous lab
- made sure `deployment.yml` and shared `pvc.yaml` are not used when StatefulSet mode is enabled

I also added a helper for the headless service name in `_helpers.tpl`.

One important note: the Docker Hub `latest` image did not have the `/visits` endpoint from the updated app code, so for this lab I built the current image from my repository and used tag `zsalavat/devops-info-service-python:lab15` inside minikube.

Build and deploy commands:

```bash
minikube image build -t zsalavat/devops-info-service-python:lab15 ./app_python

kubectl create namespace lab15 --dry-run=client -o yaml | kubectl apply -f -

helm upgrade --install lab15 ./k8s/myapp -n lab15 \
  -f ./k8s/myapp/values.yaml \
  -f ./k8s/myapp/values-statefulset.yaml
```

## Stage 1 - Why I Used StatefulSet

I used StatefulSet because my application is no longer fully stateless. The app writes the visits counter into `/data/visits`, so every pod should keep its own file. If I used a normal Deployment with one shared PVC, the pods would not be isolated the way the task requires.

Difference between Deployment and StatefulSet:

| Feature | Deployment | StatefulSet |
|---|---|---|
| Pod names | Random suffix | Stable ordered names like `pod-0`, `pod-1`, `pod-2` |
| Storage | Usually shared or external | Separate PVC for each pod |
| Network identity | No stable per-pod DNS | Stable DNS name for every pod |
| Scaling order | Not guaranteed | Ordered |
| Best use case | Stateless apps | Databases, queues, apps with state |

I also used a headless service. A headless service means `clusterIP: None`. It does not load balance to one virtual IP. Instead, Kubernetes creates DNS records for each pod directly. This is needed so StatefulSet pods can reach each other with stable names.

In my case the DNS pattern is:

`lab15-myapp-<ordinal>.lab15-myapp-headless.lab15.svc.cluster.local`

## Stage 2 - Resource Verification

After deployment I checked all important resources.

Command:

```bash
kubectl get po,sts,svc,pvc -n lab15 -o wide
```

Output:

```text
NAME                READY   STATUS    RESTARTS   AGE     IP             NODE       NOMINATED NODE   READINESS GATES
pod/lab15-myapp-0   1/1     Running   0          5m20s   10.244.0.194   minikube   <none>           <none>
pod/lab15-myapp-1   1/1     Running   0          7m14s   10.244.0.192   minikube   <none>           <none>
pod/lab15-myapp-2   1/1     Running   0          7m50s   10.244.0.191   minikube   <none>           <none>

NAME                           READY   AGE   CONTAINERS   IMAGES
statefulset.apps/lab15-myapp   3/3     11m   myapp        zsalavat/devops-info-service-python:lab15

NAME                           TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE   SELECTOR
service/lab15-myapp-headless   ClusterIP   None            <none>        80/TCP    11m   app.kubernetes.io/instance=lab15,app.kubernetes.io/name=myapp
service/lab15-myapp-service    ClusterIP   10.98.199.216   <none>        80/TCP    11m   app.kubernetes.io/instance=lab15,app.kubernetes.io/name=myapp

NAME                                              STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE   VOLUMEMODE
persistentvolumeclaim/data-volume-lab15-myapp-0   Bound    pvc-2ed08174-728d-4a65-8746-5abc25b23f0f   100Mi      RWO            standard       <unset>                 11m   Filesystem
persistentvolumeclaim/data-volume-lab15-myapp-1   Bound    pvc-b8feacc6-bbb5-4d8e-a4ad-c38c21a23e9e   100Mi      RWO            standard       <unset>                 11m   Filesystem
persistentvolumeclaim/data-volume-lab15-myapp-2   Bound    pvc-cfcff9c0-b842-40de-a566-65751c65fc07   100Mi      RWO            standard       <unset>                 11m   Filesystem
```

From this output I can see that:

- the chart created a `StatefulSet`
- I have three pods with stable names: `lab15-myapp-0`, `lab15-myapp-1`, `lab15-myapp-2`
- the headless service was created correctly
- the normal service for application access is also present
- each pod got its own PVC automatically

## Stage 3 - Network Identity Test

Next I checked pod DNS resolution from inside the cluster.

Command:

```bash
kubectl exec -n lab15 lab15-myapp-0 -- /bin/sh -c \
  "hostname && \
   getent hosts lab15-myapp-1.lab15-myapp-headless && \
   getent hosts lab15-myapp-2.lab15-myapp-headless && \
   getent hosts lab15-myapp-1.lab15-myapp-headless.lab15.svc.cluster.local"
```

Output:

```text
lab15-myapp-0
10.244.0.192    lab15-myapp-1.lab15-myapp-headless.lab15.svc.cluster.local
10.244.0.191    lab15-myapp-2.lab15-myapp-headless.lab15.svc.cluster.local
10.244.0.192    lab15-myapp-1.lab15-myapp-headless.lab15.svc.cluster.local
```

This shows that the pods have stable DNS names and can be resolved through the headless service. That is one of the main guarantees of StatefulSet.

## Stage 4 - Per-Pod Storage Evidence

After that I tested whether each pod keeps its own visit counter.

To do this, I sent a different number of requests to each pod through its own DNS name.

Command:

```bash
kubectl exec -n lab15 lab15-myapp-0 -- /bin/sh -c \
  "curl -s http://lab15-myapp-0.lab15-myapp-headless:5000/ >/dev/null && \
   curl -s http://lab15-myapp-1.lab15-myapp-headless:5000/ >/dev/null && \
   curl -s http://lab15-myapp-1.lab15-myapp-headless:5000/ >/dev/null && \
   curl -s http://lab15-myapp-2.lab15-myapp-headless:5000/ >/dev/null && \
   curl -s http://lab15-myapp-2.lab15-myapp-headless:5000/ >/dev/null && \
   curl -s http://lab15-myapp-2.lab15-myapp-headless:5000/ >/dev/null && \
   curl -s http://lab15-myapp-0.lab15-myapp-headless:5000/visits && printf '\n' && \
   curl -s http://lab15-myapp-1.lab15-myapp-headless:5000/visits && printf '\n' && \
   curl -s http://lab15-myapp-2.lab15-myapp-headless:5000/visits && printf '\n'"
```

Output:

```text
{"count":1,"storage_file":"/data/visits"}

{"count":2,"storage_file":"/data/visits"}

{"count":3,"storage_file":"/data/visits"}
```

Then I checked the file directly in every pod.

Commands:

```bash
kubectl exec -n lab15 lab15-myapp-0 -- cat /data/visits
kubectl exec -n lab15 lab15-myapp-1 -- cat /data/visits
kubectl exec -n lab15 lab15-myapp-2 -- cat /data/visits
```

Output:

```text
1
2
3
```

This proves that the storage is isolated per pod. If they were sharing the same storage, the values would be the same.

## Stage 5 - Persistence Test

The last mandatory test was to check if the data survives after deleting a pod.

I deleted only pod `lab15-myapp-0`, not the whole StatefulSet.

Commands:

```bash
OLD_UID=$(kubectl get pod -n lab15 lab15-myapp-0 -o jsonpath='{.metadata.uid}')
BEFORE=$(kubectl exec -n lab15 lab15-myapp-0 -- cat /data/visits)

kubectl delete pod -n lab15 lab15-myapp-0 --wait=true
kubectl wait --for=condition=Ready pod/lab15-myapp-0 -n lab15 --timeout=600s

NEW_UID=$(kubectl get pod -n lab15 lab15-myapp-0 -o jsonpath='{.metadata.uid}')
AFTER=$(kubectl exec -n lab15 lab15-myapp-0 -- cat /data/visits)
kubectl exec -n lab15 lab15-myapp-0 -- curl -s http://127.0.0.1:5000/visits
```

Output:

```text
{"count":1,"storage_file":"/data/visits"}

before_uid=a90c8bdb-80e6-4e1a-9af8-f40fe32d3bc7
after_uid=62673701-5ccc-4c5f-b3f0-f25807035f18
before_count=1
after_count=1
```

The pod UID changed, so Kubernetes really recreated the pod. But the visit count stayed the same. This means the data was stored in the PVC and was mounted again into the new pod.

So the persistence test passed.

## Bonus Task - Update Strategies

For the bonus task I used a separate release in namespace `lab15-bonus` so that I would not break my main verification from the mandatory part.

Initial deployment:

```bash
kubectl create namespace lab15-bonus --dry-run=client -o yaml | kubectl apply -f -

helm upgrade --install lab15-bonus ./k8s/myapp -n lab15-bonus \
  -f ./k8s/myapp/values.yaml \
  -f ./k8s/myapp/values-statefulset.yaml
```

### Bonus Part 1 - Partitioned Rolling Update

For this test I set `partition: 2`.

Command:

```bash
helm upgrade lab15-bonus ./k8s/myapp -n lab15-bonus \
  -f ./k8s/myapp/values.yaml \
  -f ./k8s/myapp/values-statefulset.yaml \
  -f ./k8s/myapp/values-statefulset-partition.yaml \
  --set config.logLevel=DEBUG
```

Output:

```text
strategy=RollingUpdate partition=2
currentRevision=lab15-bonus-myapp-dcf45d847
updateRevision=lab15-bonus-myapp-5cc45589c8
currentReplicas=2
updatedReplicas=1
lab15-bonus-myapp-0   lab15-bonus-myapp-dcf45d847   zsalavat/devops-info-service-python:lab15
lab15-bonus-myapp-1   lab15-bonus-myapp-dcf45d847   zsalavat/devops-info-service-python:lab15
lab15-bonus-myapp-2   lab15-bonus-myapp-5cc45589c8   zsalavat/devops-info-service-python:lab15
```

From this result I can see that only pod `2` was updated. Pods `0` and `1` stayed on the previous revision. So the partition worked correctly.

This kind of strategy can be useful when I want to update only higher ordinal pods first.

### Bonus Part 2 - OnDelete Strategy

After that I tested `OnDelete`.

Command:

```bash
helm upgrade lab15-bonus ./k8s/myapp -n lab15-bonus \
  -f ./k8s/myapp/values.yaml \
  -f ./k8s/myapp/values-statefulset.yaml \
  -f ./k8s/myapp/values-statefulset-ondelete.yaml \
  --set config.logLevel=WARNING
```

State right after upgrade:

```text
after_upgrade
strategy=OnDelete
currentRevision=lab15-bonus-myapp-5cc45589c8
updateRevision=lab15-bonus-myapp-5b887477f
updatedReplicas=
readyReplicas=3
lab15-bonus-myapp-0   lab15-bonus-myapp-5cc45589c8
lab15-bonus-myapp-1   lab15-bonus-myapp-5cc45589c8
lab15-bonus-myapp-2   lab15-bonus-myapp-5cc45589c8
```

Here I can see that the new revision exists, but none of the pods updated automatically.

Then I manually deleted one pod.

State after manual deletion:

```text
after_manual_delete
strategy=OnDelete
currentRevision=lab15-bonus-myapp-5cc45589c8
updateRevision=lab15-bonus-myapp-5b887477f
updatedReplicas=1
readyReplicas=3
lab15-bonus-myapp-0   lab15-bonus-myapp-5cc45589c8
lab15-bonus-myapp-1   lab15-bonus-myapp-5cc45589c8
lab15-bonus-myapp-2   lab15-bonus-myapp-5b887477f
```

After deletion only one pod moved to the new revision. So `OnDelete` also worked as expected.

This strategy is useful when updates should happen only under manual control.

## Validation

I also checked that the Helm chart is valid and that the application tests still pass.

Commands used:

```bash
helm lint ./k8s/myapp -f ./k8s/myapp/values.yaml -f ./k8s/myapp/values-statefulset.yaml

helm lint ./k8s/myapp -f ./k8s/myapp/values.yaml -f ./k8s/myapp/values-statefulset.yaml -f ./k8s/myapp/values-statefulset-ondelete.yaml
```

Application test result:

```text
............                                                             [100%]
12 passed, 1 warning in 0.19s
```

## Conclusion

In this lab I successfully converted my Helm chart to use a StatefulSet. I created a headless service, configured per-pod persistent storage with `volumeClaimTemplates`, and verified stable pod identity and persistence.

The main results are:

- StatefulSet deployed successfully
- each pod has stable name and DNS identity
- each pod has its own PVC
- each pod keeps its own visit count
- data survives pod deletion
- bonus update strategies were also tested successfully

So the requirements of Lab 15 were completed.
