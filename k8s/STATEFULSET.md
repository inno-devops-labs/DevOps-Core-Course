# Lab 15 - StatefulSets and Persistent Storage

## StatefulSet overview

A StatefulSet was added to the Helm chart instead of using the Rollout from lab 14. The reason is that the app needs per-pod storage for the visits counter, and each pod should have its own identity.

Deployments create pods with random names and they all share the same PVC. StatefulSets give each pod a name with an index. Each pod gets its own PVC through volumeClaimTemplates. Pods start and stop in order. Deployments are good for stateless apps. StatefulSets are for databases, message queues.

A headless service (`clusterIP: None`) is needed so each pod gets its own DNS record. The format is `<pod>.<headless-svc>.<namespace>.svc.cluster.local`.

## Resource verification

```
$ kubectl get po,sts,svc,pvc
NAME                            READY   STATUS    RESTARTS   AGE
pod/app-devops-info-service-0   1/1     Running   0          32s
pod/app-devops-info-service-1   1/1     Running   0          2m40s
pod/app-devops-info-service-2   1/1     Running   0          4m7s

NAME                                       READY   AGE
statefulset.apps/app-devops-info-service   3/3     17m

NAME                                       TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/app-devops-info-service            NodePort    10.100.81.198   <none>        80:30080/TCP   17m
service/app-devops-info-service-headless   ClusterIP   None            <none>        80/TCP         17m
service/kubernetes                         ClusterIP   10.96.0.1       <none>        443/TCP        42d

NAME                                                   STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/data-app-devops-info-service-0   Bound    pvc-2568d081-045c-4dae-8b3e-fb95c0365892   100Mi      RWO            standard       <unset>                 17m
persistentvolumeclaim/data-app-devops-info-service-1   Bound    pvc-dd96087c-ef71-4ccc-a447-42bfac27a5f2   100Mi      RWO            standard       <unset>                 17m
persistentvolumeclaim/data-app-devops-info-service-2   Bound    pvc-27890719-1656-44b9-b1fe-b7679c7a0784   100Mi      RWO            standard       <unset>                 17m
```

There are three pods with ordinal names, three PVCs (one per pod), and the headless service has clusterIP None.

## Network identity

DNS resolution from pod-0 to the other pods:

```
$ kubectl exec app-devops-info-service-0 -- python3 -c "import socket; print(socket.gethostbyname('app-devops-info-service-1.app-devops-info-service-headless.default.svc.cluster.local'))"
10.244.0.202

$ kubectl exec app-devops-info-service-0 -- python3 -c "import socket; print(socket.gethostbyname('app-devops-info-service-2.app-devops-info-service-headless.default.svc.cluster.local'))"
10.244.0.199
```

The DNS naming pattern is `<statefulset>-<ordinal>.<headless-service>.<namespace>.svc.cluster.local`.

## Per-pod storage

Each pod has its own PVC mounted at `/data` and keeps its own visit count:

```
$ for i in 0 1 2; do echo -n "pod-$i: "; kubectl exec app-devops-info-service-$i -- cat /data/visits; echo; done
pod-0: 3
pod-1: 5
pod-2: 7
```

The counts are different for each pod, which shows that the storage is isolated between pods.

## Persistence test

Check the visit count on pod-0, delete it, and check again after restart:

```
$ kubectl exec app-devops-info-service-0 -- cat /data/visits
3

$ kubectl delete pod app-devops-info-service-0
pod "app-devops-info-service-0" deleted

$ kubectl wait --for=condition=ready pod/app-devops-info-service-0 --timeout=60s
pod/app-devops-info-service-0 condition met

$ kubectl exec app-devops-info-service-0 -- cat /data/visits
3
```

The visit count is still 3 after the pod was deleted and recreated. The PVC stays bound when the pod is deleted and gets reattached to the new pod.

## Update strategies

StatefulSets have two update strategies:

- RollingUpdate (default) - pods are updated in reverse order (2, 1, 0). You can set a `partition` value so only pods with ordinal >= partition get updated. This is useful for testing updates on some pods first.
- OnDelete - pods only get the update when you manually delete them. This gives full control over which pods run which version.

The chart uses RollingUpdate with partition 0, so all pods get updated.

```yaml
statefulset:
  enabled: true
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 0
```

Setting `statefulset.enabled: false` disables the StatefulSet and headless service, and the Rollout and standalone PVC templates get used instead.
