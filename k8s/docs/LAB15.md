# Lab 15 — StatefulSets & Persistent Storage



## StatefulSet Overview

### Deployment vs StatefulSet

| Characteristic       | Deployment                           | StatefulSet                                   |
|----------------------|--------------------------------------|-----------------------------------------------|
| Pod naming           | Random suffixes                      | Stable ordinal index (`-0`, `-1`, `-2`)      |
| Network identity     | Pod endpoint can change              | Each pod keeps a stable DNS identity          |
| Storage model        | Shared or interchangeable volumes    | Dedicated PVC per pod                         |
| Scaling behavior     | Scales without strict ordering       | Scales up/down in deterministic order         |
| Update strategy      | Standard rolling update              | Ordered rollout, optional partition           |
| Typical use case     | Stateless workloads                  | Stateful workloads                            |

### When StatefulSet is the right choice
1. **Stable identity**: each replica must keep a permanent network name
2. **Per-pod persistence**: each replica needs isolated, durable storage
3. **Ordered lifecycle**: startup, update, and termination order matters



## Resource Verification

```bash
kubectl get statefulset -n stateful
```

```bash
NAME                        READY   AGE
stateful-demo-stateful      3/3     27m
```

---

```bash
kubectl get pods -n stateful```

```bash
NAME                          READY   STATUS    RESTARTS   AGE
stateful-demo-stateful-0      1/1     Running   0          28m
stateful-demo-stateful-1      1/1     Running   0          28m
stateful-demo-stateful-2      1/1     Running   0          29m
```

---

```bash
kubectl get svc -n stateful
```

```bash
NAME                            TYPE        CLUSTER-IP      PORT(S)        AGE
stateful-demo                   NodePort    10.98.172.50    80:30085/TCP   31m
stateful-demo-headless          ClusterIP   None            80/TCP         31m
```

---

```bash
kubectl get pvc -n stateful
```

```bash
NAME                             STATUS   VOLUME                                     CAPACITY   ACCESS MODES   AGE
data-stateful-demo-stateful-0    Bound    pvc-nf5un8-nuf7vc-74nfdu                  100Mi      RWO            34m
data-stateful-demo-stateful-1    Bound    pvc-dn4e7f-3nf4u3-frj48h                  100Mi      RWO            34m
data-stateful-demo-stateful-2    Bound    pvc-mnfr4b-2b34vb-bcbe76                  100Mi      RWO            34m
```



## Network Identity - DNS Resolution Evidence

### DNS resolution test

```bash
kubectl exec -it -n stateful stateful-demo-stateful-0 -- /bin/sh
apt-get update && apt-get install -y dnsutils
nslookup stateful-demo-stateful-1.stateful-demo-headless.stateful.svc.cluster.local
```

```bash
Server:         10.96.0.10
Address:        10.96.0.10

Name:   stateful-demo-stateful-1.stateful-demo-headless.stateful.svc.cluster.local
Address: 10.244.0.6
```

---

```bash
nslookup stateful-demo-stateful-2.stateful-demo-headless.stateful.svc.cluster.local
```

```bash
Server:         10.96.0.10
Address:        10.96.0.10

Name:   stateful-demo-stateful-2.stateful-demo-headless.stateful.svc.cluster.local
Address: 10.244.0.7
```

---

```bash
nslookup stateful-demo-headless.stateful.svc.cluster.local
```

```bash
Server:         10.96.0.10
Address:        10.96.0.10

Name:   stateful-demo-headless.stateful.svc.cluster.local
Address: 10.244.0.5
Name:   stateful-demo-headless.stateful.svc.cluster.local
Address: 10.244.0.6
Name:   stateful-demo-headless.stateful.svc.cluster.local
Address: 10.244.0.7
```



## Per-Pod Storage Test

```bash
kubectl exec -n stateful stateful-demo-stateful-0 -- cat /data/visits.txt 2>/dev/null || echo "0"
$ kubectl exec -n stateful stateful-demo-stateful-1 -- cat /data/visits.txt 2>/dev/null || echo "0"
$ kubectl exec -n stateful stateful-demo-stateful-2 -- cat /data/visits.txt 2>/dev/null || echo "0"
```

```bash
0
0
0
```

---

```bash
kubectl port-forward -n stateful stateful-demo-stateful-0 8080:5050
curl -s http://localhost:8080/ > /dev/null
curl -s http://localhost:8080/ > /dev/null
curl -s http://localhost:8080/ > /dev/null

kubectl port-forward -n stateful stateful-demo-stateful-1 8081:5050
curl -s http://localhost:8081/ > /dev/null
curl -s http://localhost:8081/ > /dev/null

kubectl port-forward -n stateful stateful-demo-stateful-2 8082:5050
curl -s http://localhost:8082/ > /dev/null
curl -s http://localhost:8082/ > /dev/null
curl -s http://localhost:8082/ > /dev/null
curl -s http://localhost:8082/ > /dev/null

kubectl exec -n stateful stateful-demo-stateful-0 -- cat /data/visits.txt
kubectl exec -n stateful stateful-demo-stateful-1 -- cat /data/visits.txt
kubectl exec -n stateful stateful-demo-stateful-2 -- cat /data/visits.txt
```

```bash
3
2
4
```



## Persistence Test

```bash
VISITS_BEFORE=$(kubectl exec -n stateful stateful-demo-stateful-0 -- cat /data/visits.txt)
echo $VISITS_BEFORE
```

```bash
3
```

---

```bash
kubectl delete pod -n stateful stateful-demo-stateful-0
```

```bash
pod "stateful-demo-stateful-0" deleted
```

---

```bash
kubectl get pods -n stateful -w
```

```bash
NAME                          READY   STATUS    RESTARTS   AGE
stateful-demo-stateful-0      1/1     Running   0          37m
stateful-demo-stateful-1      1/1     Running   0          37m
stateful-demo-stateful-2      1/1     Running   0          37m
stateful-demo-stateful-0      1/1     Terminating   0          37m
stateful-demo-stateful-0      0/1     Terminating   0          37m
stateful-demo-stateful-0      0/1     Pending       0          0s
stateful-demo-stateful-0      0/1     ContainerCreating   0          1s
stateful-demo-stateful-0      1/1     Running             0          4s
```

---

```bash
VISITS_AFTER=$(kubectl exec -n stateful stateful-demo-stateful-0 -- cat /data/visits.txt)
echo $VISITS_AFTER
```

```bash
3
```

---

```bash
kubectl get pvc -n stateful | grep stateful-demo-stateful-0
```

```bash
data-stateful-demo-stateful-0   Bound    pvc-5nc7ew-pa0b1t   100Mi      RWO   39m
```



## StatefulSet Update Strategies

```bash
kubectl get statefulset -n update-test
```

```bash
NAME                         READY   AGE
update-demo-stateful         3/3     13m
```

---

```bash
kubectl get pods -n update-test
```

```bash
NAME                           READY   STATUS    RESTARTS   AGE
update-demo-stateful-0         1/1     Running   0          13m
update-demo-stateful-1         1/1     Running   0          13m
update-demo-stateful-2         1/1     Running   0          13m
```

### RollingUpdate with Partition

```bash
kubectl patch statefulset -n update-test update-demo-stateful -p '{"spec":{"updateStrategy":{"type":"RollingUpdate","rollingUpdate":{"partition":1}}}}'
```

```bash
statefulset.apps/update-demo-stateful patched
```

---

```bash
kubectl get statefulset -n update-test update-demo-stateful -o yaml | grep -A5 updateStrategy
```

```bash
updateStrategy:
    rollingUpdate:
      partition: 1
    type: RollingUpdate
```

---

```bash
kubectl set image statefulset/update-demo-stateful -n update-test info-service=sayfetik/info-service-python:prelatest
```

```bash
statefulset.apps/update-demo-stateful image updated
```

---

```bash
kubectl get pods -n update-test -w
```

```bash
NAME                           READY   STATUS    RESTARTS   AGE
update-demo-stateful-0         1/1     Running   0          15m
update-demo-stateful-1         1/1     Running   0          15m
update-demo-stateful-2         1/1     Running   0          15m
update-demo-stateful-2         1/1     Terminating   0          15m
update-demo-stateful-2         0/1     Terminating   0          15m
update-demo-stateful-2         0/1     Pending       0          0s
update-demo-stateful-2         0/1     ContainerCreating   0          1s
update-demo-stateful-2         1/1     Running             0          2s
update-demo-stateful-1         1/1     Terminating         0          15m
update-demo-stateful-1         0/1     Terminating         0          15m
update-demo-stateful-1         0/1     Pending             0          0s
update-demo-stateful-1         0/1     ContainerCreating   0          1s
update-demo-stateful-1         1/1     Running             0          3s
```

---

```bash
for i in 0 1 2; do
    echo "Pod $i:"
    kubectl exec -n update-test update-demo-stateful-$i -- env | grep MESSAGE
done
```

```bash
Pod 0:
MESSAGE=Version 1
Pod 1:
MESSAGE=Version 2
Pod 2:
MESSAGE=Version 2
```

### OnDelete Update Strategy

```bash
kubectl patch statefulset -n update-test update-demo-stateful -p '{"spec":{"updateStrategy":{"type":"OnDelete"}}}'
```

```bash
statefulset.apps/update-demo-stateful patched
```

---

```bash
kubectl get statefulset -n update-test update-demo-stateful -o yaml | grep -A2 updateStrategy
```

```bash
updateStrategy:
    type: OnDelete
```

---

```bash
kubectl set image statefulset/update-demo-stateful -n update-test info-service=sayfetik/info-service-python:prelatest
```

```bash
statefulset.apps/update-demo-stateful image updated
```

---

```bash
for i in 0 1 2; do
    echo "Pod $i:"
    kubectl exec -n update-test update-demo-stateful-$i -- env | grep MESSAGE
  done
```

```bash
Pod 0:
MESSAGE=Version 2
Pod 1:
MESSAGE=Version 2
Pod 2:
MESSAGE=Version 2
```

---


```bash
kubectl delete pod -n update-test update-demo-stateful-1
```

```bash
pod "update-demo-stateful-1" deleted
```

---

```bash
kubectl get pods -n update-test -w
```

```bash
update-demo-stateful-0   1/1     Running             0          17m
update-demo-stateful-1   1/1     Terminating          0          17m
update-demo-stateful-2   1/1     Running             0          17m
update-demo-stateful-1   0/1     Terminating          0          17m
update-demo-stateful-1   0/1     Pending              0          0s
update-demo-stateful-1   0/1     ContainerCreating    0          0s
update-demo-stateful-1   1/1     Running              0          3s
```

---

```bash
for i in 0 1 2; do
    echo "Pod $i:"
    kubectl exec -n update-test update-demo-stateful-$i -- env | grep MESSAGE
  done
```

```bash
Pod 0:
MESSAGE=Version 2
Pod 1:
MESSAGE=Version 3
Pod 2:
MESSAGE=Version 2
```
