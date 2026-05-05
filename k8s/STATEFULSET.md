# Lab 15 — StatefulSets & Persistent Storage

In this lab, I converted my Helm-based application from a Deployment approach to a StatefulSet approach with per-pod persistent storage. I also verified DNS identity, storage isolation, and data persistence after pod restart

##  StatefulSet Overview (and difference from Deployment)

I used StatefulSet because this workload needs stable pod identity and persistent per-pod data (`/data/visits`)

### StatefulSet guarantees I used
- Stable pod names: `...-0`, `...-1`, `...-2`
- Stable storage per pod via `volumeClaimTemplates`
- Ordered pod creation and management
- Predictable DNS records through a headless service

### Deployment vs StatefulSet (my understanding)
- Deployment pods are interchangeable and usually stateless
- StatefulSet pods are not interchangeable: each pod has identity and its own PVC
- Deployment is best for stateless web/API workloads
- StatefulSet is best for databases, queues, clustered systems, and any pod-specific data

### Headless service
I created a headless service (`clusterIP: None`) for direct pod addressing:
- `<pod-name>.<headless-service>.<namespace>.svc.cluster.local`

In my case:
- `lab15-devops-info-service-1.lab15-devops-info-service-headless.default.svc.cluster.local`

---

##  What I changed in Helm chart

I implemented Task 2 by updating the chart in `k8s/devops-info-service`:

- Added `templates/statefulset.yml`
  - `spec.serviceName` points to headless service
  - `volumeClaimTemplates` creates one PVC per pod
  - StatefulSet `updateStrategy` is configurable from values
- Added `templates/headless-service.yml`
  - `clusterIP: None`
- Updated `templates/deployment.yml`
  - Deployment now renders only if `statefulset.enabled=false`
- Updated `templates/pvc.yml`
  - Single shared PVC renders only for non-StatefulSet mode
- Updated `values.yaml`
  - Added `statefulset` section
  - Enabled StatefulSet mode for this lab

---

##  Resource verification (`kubectl get po,sts,svc,pvc`)

Command:
```bash
kubectl get po,sts,svc,pvc
```

Output:
```text
NAME                                                          READY   STATUS    RESTARTS        AGE
pod/devops-info-service-devops-info-service-957c798cb-2bnw8   1/1     Running   1 (9m39s ago)   4d21h
pod/devops-info-service-devops-info-service-957c798cb-8fwtl   1/1     Running   1 (9m39s ago)   4d21h
pod/devops-info-service-devops-info-service-957c798cb-blhvz   1/1     Running   1 (9m39s ago)   4d21h
pod/devops-info-service-devops-info-service-957c798cb-pcp9f   1/1     Running   1 (9m39s ago)   4d21h
pod/devops-info-service-devops-info-service-957c798cb-rng4q   1/1     Running   1 (9m39s ago)   4d21h
pod/lab15-devops-info-service-0                               1/1     Running   0               2m59s
pod/lab15-devops-info-service-1                               1/1     Running   0               5m14s
pod/lab15-devops-info-service-2                               1/1     Running   0               55s

NAME                                         READY   AGE
statefulset.apps/lab15-devops-info-service   3/3     9m

NAME                                              TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service-devops-info-service   ClusterIP   10.102.80.47    <none>        5000/TCP       4d21h
service/kubernetes                                ClusterIP   10.96.0.1       <none>        443/TCP        4d23h
service/lab15-devops-info-service                 NodePort    10.103.113.58   <none>        80:30080/TCP   9m
service/lab15-devops-info-service-headless        ClusterIP   None            <none>        80/TCP         9m

NAME                                                                 STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/data-volume-lab15-devops-info-service-0        Bound    pvc-bcb25762-4145-466b-8527-a52769915a35   100Mi      RWO            standard       <unset>                 9m
persistentvolumeclaim/data-volume-lab15-devops-info-service-1        Bound    pvc-6f042c81-4dd7-429a-816c-623d95947d1d   100Mi      RWO            standard       <unset>                 5m14s
persistentvolumeclaim/data-volume-lab15-devops-info-service-2        Bound    pvc-c94ce363-91fc-45ad-baa8-1715050a84e5   100Mi      RWO            standard       <unset>                 5m5s
persistentvolumeclaim/devops-info-service-devops-info-service-data   Bound    pvc-403c90d1-43fc-4e4e-9400-18d6c7a8f70b   100Mi      RWO            standard       <unset>                 4d22h
```

Result: StatefulSet is running with ordered pods (`0..2`) and each pod has its own PVC

---

##  Network identity (DNS test)

Command:
```bash
kubectl exec lab15-devops-info-service-0 -- sh -c 'nslookup lab15-devops-info-service-1.lab15-devops-info-service-headless || getent hosts lab15-devops-info-service-1.lab15-devops-info-service-headless'
```

Output:
```text
sh: 1: nslookup: not found
10.244.0.43     lab15-devops-info-service-1.lab15-devops-info-service-headless.default.svc.cluster.local
```

Result: DNS resolution works through the headless service; each pod has a stable name

---

##  Per-pod storage isolation evidence

To prove isolation, I generated different traffic levels in each pod and checked `/visits`

### Pod `-0`
```bash
kubectl exec lab15-devops-info-service-0 -- python -c "import urllib.request; [urllib.request.urlopen('http://localhost:5000/').read() for _ in range(2)]; print(urllib.request.urlopen('http://localhost:5000/visits').read().decode())"
```
Output:
```text
{"description":"Number of requests to root endpoint","endpoint":"/","visits":2}
```

### Pod `-1`
```bash
kubectl exec lab15-devops-info-service-1 -- python -c "import urllib.request; [urllib.request.urlopen('http://localhost:5000/').read() for _ in range(5)]; print(urllib.request.urlopen('http://localhost:5000/visits').read().decode())"
```
Output:
```text
{"description":"Number of requests to root endpoint","endpoint":"/","visits":5}
```

### Pod `-2`
```bash
kubectl exec lab15-devops-info-service-2 -- python -c "import urllib.request; [urllib.request.urlopen('http://localhost:5000/').read() for _ in range(8)]; print(urllib.request.urlopen('http://localhost:5000/visits').read().decode())"
```
Output:
```text
{"description":"Number of requests to root endpoint","endpoint":"/","visits":8}
```

Result: each pod keeps its own independent counter, so storage is isolated per replica

---

##  Persistence test (data survives pod deletion)

Command:
```bash
echo 'before:' \
&& kubectl exec lab15-devops-info-service-0 -- python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:5000/visits').read().decode())" \
&& kubectl delete pod lab15-devops-info-service-0 \
&& kubectl wait --for=condition=Ready pod/lab15-devops-info-service-0 --timeout=180s \
&& echo 'after:' \
&& kubectl exec lab15-devops-info-service-0 -- python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:5000/visits').read().decode())"
```

Output:
```text
before:
{"description":"Number of requests to root endpoint","endpoint":"/","visits":2}

pod "lab15-devops-info-service-0" deleted
pod/lab15-devops-info-service-0 condition met
after:
{"description":"Number of requests to root endpoint","endpoint":"/","visits":2}
```

Result: the value remained `2` after pod recreation, so data persisted through PVC

---

## Bonus — Update strategies

I also tested both bonus scenarios

### A) RollingUpdate with partition

I applied:
```bash
helm upgrade lab15 ./k8s/devops-info-service \
  --set statefulset.updateStrategy.type=RollingUpdate \
  --set statefulset.updateStrategy.rollingUpdate.partition=2 \
  --set appConfig.logLevel=DEBUG
```

Verification:
```bash
kubectl get sts lab15-devops-info-service -o jsonpath='{.spec.updateStrategy.type}{" partition="}{.spec.updateStrategy.rollingUpdate.partition}{"\n"}'
kubectl get sts lab15-devops-info-service -o jsonpath='{.status.currentRevision}{" -> "}{.status.updateRevision}{"; updatedReplicas="}{.status.updatedReplicas}{"\n"}'
```

Output:
```text
RollingUpdate partition=2
lab15-devops-info-service-678957c5fc -> lab15-devops-info-service-846bff8cc4; updatedReplicas=
```

Interpretation: with partition `2`, lower ordinals were not auto-updated

### B) OnDelete strategy

I applied:
```bash
helm upgrade lab15 ./k8s/devops-info-service \
  --set statefulset.updateStrategy.type=OnDelete \
  --set appConfig.logLevel=WARNING
```

Before manual deletion:
```text
OnDelete
lab15-devops-info-service-678957c5fc -> lab15-devops-info-service-7b688cd857
NAME                          REV
lab15-devops-info-service-0   lab15-devops-info-service-678957c5fc
lab15-devops-info-service-1   lab15-devops-info-service-678957c5fc
lab15-devops-info-service-2   lab15-devops-info-service-678957c5fc
```

After deleting only pod `-2`:
```bash
kubectl delete pod lab15-devops-info-service-2
kubectl wait --for=condition=Ready pod/lab15-devops-info-service-2 --timeout=180s
kubectl get pods -l app.kubernetes.io/instance=lab15 -o custom-columns=NAME:.metadata.name,REV:.metadata.labels.controller-revision-hash --sort-by=.metadata.name
```

Output:
```text
NAME                          REV
lab15-devops-info-service-0   lab15-devops-info-service-678957c5fc
lab15-devops-info-service-1   lab15-devops-info-service-678957c5fc
lab15-devops-info-service-2   lab15-devops-info-service-7b688cd857
```

Interpretation: with `OnDelete`, pods update only when I manually recreate them

