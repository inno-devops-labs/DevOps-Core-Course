# Lab 15 — StatefulSets & Persistent Storage

**Student**: Selivanov George  
**Date**: May 7, 2026

## 1) StatefulSet Concepts

StatefulSet is used when pods need:
- Stable pod identity (`name-0`, `name-1`, `name-2`)
- Stable storage per pod (own PVC for each replica)
- Ordered create/update/delete behavior

Deployment vs StatefulSet:

| Feature | Deployment | StatefulSet |
|---|---|---|
| Pod identity | Ephemeral/random suffix | Stable ordinal name |
| Storage | Usually shared/one PVC pattern | Per-pod PVC via template |
| Scale/update order | Unordered | Ordered by ordinal |
| Typical workloads | Stateless APIs/web | DBs, queues, clustered systems |

Headless Service (`clusterIP: None`) is required so each pod gets resolvable DNS:
- `python-app-devops-python-app-0.python-app-devops-python-app-headless.devops-python-app.svc.cluster.local`
- `python-app-devops-python-app-1.python-app-devops-python-app-headless.devops-python-app.svc.cluster.local`

## 2) Implementation (Helm)

Implemented in chart `k8s/devops-python-app`:
- Added `templates/statefulset.yaml`
- Added `templates/service-headless.yaml`
- Kept normal service for app access
- Added statefulset configuration and update strategy options used by `volumeClaimTemplates`

Used values:

```yaml
replicaCount: 3
statefulset:
  enabled: true
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 0
persistence:
  enabled: true
  size: 100Mi
  storageClass: ""
  accessMode: ReadWriteOnce
  mountPath: /data
```

Deploy:

```bash
helm dependency update k8s/devops-python-app
helm upgrade --install python-app k8s/devops-python-app \
  --namespace devops-python-app --create-namespace \
  --set statefulset.enabled=true \
  --set rollout.enabled=false \
  --set image.repository=ge0s1/devops-python-app \
  --set image.tag=lab15 \
  --set image.pullPolicy=IfNotPresent
kubectl rollout status statefulset/python-app-devops-python-app -n devops-python-app --timeout=240s
kubectl get po,sts,svc,pvc -n devops-python-app -l app.kubernetes.io/instance=python-app -o wide
```

Evidence:

```text
NAME                                            READY   STATUS    RESTARTS   AGE   IP           NODE                       NOMINATED NODE   READINESS GATES
pod/python-app-devops-python-app-0               1/1     Running   0          12s   10.1.0.15    devops-lab-control-plane   <none>           <none>
pod/python-app-devops-python-app-1               1/1     Running   0          22s   10.1.0.16    devops-lab-control-plane   <none>           <none>
pod/python-app-devops-python-app-2               1/1     Running   0          32s   10.1.0.17    devops-lab-control-plane   <none>           <none>

NAME                                                    READY   AGE     CONTAINERS              IMAGES
statefulset.apps/python-app-devops-python-app            3/3     2m59s   devops-python-app       ge0s1/devops-python-app:lab15

NAME                                                        TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE     SELECTOR
service/python-app-devops-python-app-headless               ClusterIP   None            <none>        80/TCP      2m59s   app.kubernetes.io/instance=python-app,app.kubernetes.io/name=devops-python-app
service/python-app-devops-python-app-service                NodePort    10.100.50.30    <none>        80:30080/TCP 2m59s   app.kubernetes.io/instance=python-app,app.kubernetes.io/name=devops-python-app

NAME                                                              STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE     VOLUMEMODE
persistentvolumeclaim/app-data-python-app-devops-python-app-0     Bound    pvc-8a3b7c2d-5501-49e2-9912-fc45e1d7a3b2   100Mi      RWO            standard       <unset>                 2m59s   Filesystem
persistentvolumeclaim/app-data-python-app-devops-python-app-1     Bound    pvc-6f9e4a1c-7822-4b03-8d55-ba12c8f4e901   100Mi      RWO            standard       <unset>                 2m47s   Filesystem
persistentvolumeclaim/app-data-python-app-devops-python-app-2     Bound    pvc-3d5b2e7a-9104-41f6-a33c-8790d2e5b8c4   100Mi      RWO            standard       <unset>                 2m35s   Filesystem
```

## 3) Network Identity (Headless DNS)

Commands:

```bash
kubectl exec python-app-devops-python-app-0 -n devops-python-app -- python -c "import socket; print('pod1', socket.gethostbyname('python-app-devops-python-app-1.python-app-devops-python-app-headless.devops-python-app.svc.cluster.local')); print('pod2', socket.gethostbyname('python-app-devops-python-app-2.python-app-devops-python-app-headless.devops-python-app.svc.cluster.local'))"
```

Evidence:

```text
pod1 10.1.0.16
pod2 10.1.0.17
```

## 4) Per-Pod Storage Isolation

Test by calling each pod locally from inside the pod:

```bash
kubectl exec python-app-devops-python-app-0 -n devops-python-app -- python -c "import urllib.request; [urllib.request.urlopen('http://127.0.0.1:5000/').read() for _ in range(3)]; print(urllib.request.urlopen('http://127.0.0.1:5000/visits').read().decode())"
kubectl exec python-app-devops-python-app-1 -n devops-python-app -- python -c "import urllib.request; [urllib.request.urlopen('http://127.0.0.1:5000/').read() for _ in range(5)]; print(urllib.request.urlopen('http://127.0.0.1:5000/visits').read().decode())"
kubectl exec python-app-devops-python-app-2 -n devops-python-app -- python -c "import urllib.request; [urllib.request.urlopen('http://127.0.0.1:5000/').read() for _ in range(2)]; print(urllib.request.urlopen('http://127.0.0.1:5000/visits').read().decode())"
```

Evidence:

```text
{"visits":3,"visits_file":"/data/visits"}
{"visits":5,"visits_file":"/data/visits"}
{"visits":2,"visits_file":"/data/visits"}
```

Conclusion: each pod has isolated counter data (separate PVC).

## 5) Persistence Test

Commands:

```bash
kubectl exec python-app-devops-python-app-0 -n devops-python-app -- cat /data/visits
kubectl delete pod python-app-devops-python-app-0 -n devops-python-app
kubectl wait --for=condition=Ready pod/python-app-devops-python-app-0 -n devops-python-app --timeout=180s
kubectl exec python-app-devops-python-app-0 -n devops-python-app -- cat /data/visits
```

Evidence:

```text
before:
3
pod "python-app-devops-python-app-0" deleted from devops-python-app namespace
pod/python-app-devops-python-app-0 condition met
after:
3
```

Conclusion: data persists across pod recreation because PVC is retained and reattached.

## 6) Bonus — Update Strategies

### Partitioned rolling update

```yaml
updateStrategy:
  type: RollingUpdate
  rollingUpdate:
    partition: 2
```

Result:
- Only pods with ordinal `>= 2` update first.
- Useful for canarying on highest ordinal replicas.

```bash
helm upgrade python-app k8s/devops-python-app \
  --namespace devops-python-app --reuse-values \
  --set image.tag=lab15p \
  --set statefulset.updateStrategy.rollingUpdate.partition=2
kubectl rollout status statefulset/python-app-devops-python-app -n devops-python-app -w
```

Evidence:

```text
Waiting for partitioned roll out to finish: 0 out of 1 new pods have been updated...
partitioned roll out complete: 1 new pods have been updated...
NAME                                         IMAGE                            READY
python-app-devops-python-app-0               ge0s1/devops-python-app:lab15    true
python-app-devops-python-app-1               ge0s1/devops-python-app:lab15    true
python-app-devops-python-app-2               ge0s1/devops-python-app:lab15p   true
```

### OnDelete strategy

```yaml
updateStrategy:
  type: OnDelete
```

Result:
- Pods are updated only when manually deleted.
- Useful for strict maintenance windows and controlled failover.

```bash
helm upgrade python-app k8s/devops-python-app \
  --namespace devops-python-app --reuse-values \
  --set image.tag=lab15od \
  --set statefulset.updateStrategy.type=OnDelete
kubectl get pods -n devops-python-app -l app.kubernetes.io/instance=python-app -o custom-columns=NAME:.metadata.name,IMAGE:.spec.containers[0].image,READY:.status.conditions[?(@.type=='Ready')].status
kubectl delete pod python-app-devops-python-app-2 -n devops-python-app
kubectl wait --for=condition=Ready pod/python-app-devops-python-app-2 -n devops-python-app --timeout=180s
kubectl get pods -n devops-python-app -l app.kubernetes.io/instance=python-app -o custom-columns=NAME:.metadata.name,IMAGE:.spec.containers[0].image,READY:.status.conditions[?(@.type=='Ready')].status
```

Evidence:

```text
after upgrade (before delete):
NAME                                         IMAGE                            READY
python-app-devops-python-app-0               ge0s1/devops-python-app:lab15    true
python-app-devops-python-app-1               ge0s1/devops-python-app:lab15    true
python-app-devops-python-app-2               ge0s1/devops-python-app:lab15p   true
pod "python-app-devops-python-app-2" deleted from devops-python-app namespace
pod/python-app-devops-python-app-2 condition met
after manual delete:
NAME                                         IMAGE                            READY
python-app-devops-python-app-0               ge0s1/devops-python-app:lab15    true
python-app-devops-python-app-1               ge0s1/devops-python-app:lab15    true
python-app-devops-python-app-2               ge0s1/devops-python-app:lab15od  true
```

## 7) Useful Commands

```bash
kubectl get statefulset,pods,pvc -n devops-python-app
kubectl describe statefulset python-app-devops-python-app -n devops-python-app
kubectl get pod python-app-devops-python-app-0 -n devops-python-app -o yaml | grep claimName
kubectl delete pod python-app-devops-python-app-0 -n devops-python-app
kubectl rollout status statefulset/python-app-devops-python-app -n devops-python-app
```
