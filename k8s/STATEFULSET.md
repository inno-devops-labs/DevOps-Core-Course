# Lab 15

## 1. StatefulSet Overview

StatefulSets allows replicas have their own identity and resources (like database and similar things) without sharing it with other replicas.

## 2. Resource Verification

```bash
$ helm install myapp devops-info-chart/ -n dev
NAME: myapp
LAST DEPLOYED: Mon Apr 27 22:07:43 2026
NAMESPACE: dev
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None

$ kubectl get statefulset -n dev
NAME                READY   AGE
myapp-devops-info   3/3     11m

$ kubectl get pods -n dev
NAME                  READY   STATUS    RESTARTS   AGE
myapp-devops-info-0   1/1     Running   0          11m
myapp-devops-info-1   1/1     Running   0          11m
myapp-devops-info-2   1/1     Running   0          11m

$ kubectl get pvc -n dev
NAME                       STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
data-myapp-devops-info-0   Bound    pvc-6952dcb6-1d37-4160-8969-416b686306b4   100Mi      RWO            hostpath       <unset>                 11m
data-myapp-devops-info-1   Bound    pvc-ff229660-60e9-4627-acf0-0f24d3bdbb1f   100Mi      RWO            hostpath       <unset>                 11m
data-myapp-devops-info-2   Bound    pvc-9e36555b-acea-4de5-b84d-35b083c8bf44   100Mi      RWO            hostpath       <unset>                 11m
```

## 3. Network Identity

```bash
$ kubectl exec -it myapp-devops-info-0 -n dev -- python -c \
"import socket; print('pod1', socket.gethostbyname('myapp-devops-info-1.myapp-devops-info-headless.dev.svc.cluster.local'))"\
pod1 10.1.1.24
```

After visits on port forwarded servers:

```bash
kubectl port-forward pod/myapp-devops-info-0 -n dev 8080:8000
kubectl port-forward pod/myapp-devops-info-1 -n dev 8081:8000
```

## 4. Per-Pod Storage Evidence

```bash
$ curl localhost:8080/visits
{"visits":1}

$ curl localhost:8081/visits
{"visits":2}
```

They show different numbers because of different storages.

## 5. Persistence Test

Pod deletion doesn't affect result:

```bash
$ kubectl exec myapp-devops-info-0 -n dev -- cat /data/visits
1

$ kubectl delete pod myapp-devops-info-0 -n dev
pod "myapp-devops-info-0" deleted from dev namespace

# Wait for restart

$ kubectl exec myapp-devops-info-0 -n dev -- cat /data/visits
1
```

## 6. Update Strategies

Update strategy `RollingUpdate` will automatically update pods with ordinal `>= [partition]`. Works well for staged updated for cluster services.
Update strategy `OnDelete` will update pods only on manual deletion. Works well if update needs approval before releasing.
