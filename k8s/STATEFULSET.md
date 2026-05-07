# lab 15: statefulsets & persistent storage

## 1. statefulset overview

### why statefulset

deployments are designed for stateless applications where any pod is interchangeable. statefulsets are needed when:

- each pod requires a **stable network identity** (predictable dns name)
- each pod needs its **own persistent storage** that survives restarts
- pods must be started/stopped in a **specific order**

### deployment vs statefulset

| aspect | deployment | statefulset |
|--------|-----------|-------------|
| pod names | random suffix (`app-7d4f6b-x2k9`) | ordinal index (`app-0`, `app-1`, `app-2`) |
| storage | shared pvc | per-pod pvc via volumeclaimtemplates |
| scaling | any order | ordered (0 → 1 → 2 up, 2 → 1 → 0 down) |
| network id | random, changes on restart | stable dns: `app-0.service.namespace.svc.cluster.local` |
| pod replacement | new pod with new identity | same identity recreated |
| update strategy | rollingupdate / recreate | rollingupdate (with partition) / ondelete |

### when to use which

| workload | controller | why |
|----------|-----------|-----|
| web servers, apis | deployment | stateless, any pod can serve any request |
| databases (mysql, postgres) | statefulset | each replica needs own data dir and stable identity |
| message queues (kafka, rabbitmq) | statefulset | broker identity matters, data is partition-specific |
| caches (redis cluster) | statefulset | master/slave roles, persistent state |
| distributed systems (elasticsearch, cassandra) | statefulset | node identity, data sharding |

---

## 2. resource verification

after deploying the statefulset:

```bash
kubectl get po,sts,svc,pvc
```

expected output:

```
NAME                         READY   STATUS    RESTARTS   AGE
pod/devops-info-service-0    1/1     Running   0          2m
pod/devops-info-service-1    1/1     Running   0          2m
pod/devops-info-service-2    1/1     Running   0          2m

NAME                                    READY   AGE
statefulset.apps/devops-info-service    3/3     2m

NAME                                     TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service              NodePort    10.96.140.25     <none>        80:30080/TCP   2m
service/devops-info-service-headless     ClusterIP   None             <none>        80/TCP         2m

NAME                                                          STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/data-devops-info-service-0              Bound    pvc-xxxx                                   100Mi      RWO            standard       2m
persistentvolumeclaim/data-devops-info-service-1              Bound    pvc-yyyy                                   100Mi      RWO            standard       2m
persistentvolumeclaim/data-devops-info-service-2              Bound    pvc-zzzz                                   100Mi      RWO            standard       2m
```

key observations:
- pods have ordinal names (`-0`, `-1`, `-2`)
- each pod gets its own pvc (`data-devops-info-service-0`, etc.)
- headless service has `cluster-ip: none`

---

## 3. network identity

### headless service

the headless service ([headless-service.yaml](devops-info-service/templates/headless-service.yaml)) is configured with `clusterIP: None`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: devops-info-service-headless
spec:
  clusterIP: None
  selector:
    app.kubernetes.io/name: devops-info-service
  ports:
    - port: 80
      targetPort: 5000
```

this creates dns records for each pod instead of a single virtual ip.

### dns resolution test

```bash
# exec into pod-0
kubectl exec -it devops-info-service-0 -- /bin/sh

# resolve pod-1 via headless service
nslookup devops-info-service-1.devops-info-service-headless
```

expected output:

```
Server:    10.96.0.10
Address 1: 10.96.0.10 kube-dns.kube-system.svc.cluster.local

Name:      devops-info-service-1.devops-info-service-headless
Address 1: 10.244.1.5 devops-info-service-1.devops-info-service-headless.default.svc.cluster.local
```

dns naming pattern:
- `devops-info-service-0.devops-info-service-headless.default.svc.cluster.local`
- `devops-info-service-1.devops-info-service-headless.default.svc.cluster.local`
- `devops-info-service-2.devops-info-service-headless.default.svc.cluster.local`

---

## 4. per-pod storage isolation

### volumeclaimtemplates

the statefulset uses `volumeClaimTemplates` ([statefulset.yaml](devops-info-service/templates/statefulset.yaml)) to create a unique pvc per pod:

```yaml
volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: [ "ReadWriteOnce" ]
      resources:
        requests:
          storage: 100Mi
```

each pod mounts its own pvc at `/data`:

```yaml
volumeMounts:
  - name: data
    mountPath: /data
```

### proving isolation

```bash
# forward each pod to a different local port
kubectl port-forward pod/devops-info-service-0 8080:5000 &
kubectl port-forward pod/devops-info-service-1 8081:5000 &
kubectl port-forward pod/devops-info-service-2 8082:5000 &

# visit each pod multiple times (different counts)
curl localhost:8080/visits  # e.g. 3
curl localhost:8080/visits  # e.g. 4
curl localhost:8081/visits  # e.g. 1
curl localhost:8082/visits  # e.g. 2

# verify each pod has its own count
curl localhost:8080/visits  # 4 (only incremented on pod-0)
curl localhost:8081/visits  # 1 (unchanged)
curl localhost:8082/visits  # 2 (unchanged)
```

each pod maintains its own visit count because each has its own pvc backing `/data`.

---

## 5. persistence test

data survives pod deletion because the pvc is not deleted when a pod is removed from a statefulset.

```bash
# check current visit count
kubectl exec devops-info-service-0 -- cat /data/visits
# output: 5

# delete the pod
kubectl delete pod devops-info-service-0

# wait for statefulset controller to recreate it
kubectl get pods -w
# devops-info-service-0   0/1     Terminating   0          5m
# devops-info-service-0   0/1     Pending       0          0s
# devops-info-service-0   1/1     Running       0          10s

# verify data persisted
kubectl exec devops-info-service-0 -- cat /data/visits
# output: 5  (same as before deletion)
```

the statefulset controller recreates the pod with the same identity (`devops-info-service-0`) and reattaches the same pvc (`data-devops-info-service-0`). this is the critical difference from a deployment — a deployment would create a new pod with a new name and potentially a new pvc.

---

## 6. chart structure (updated)

```
k8s/
├── devops-info-service/                # helm chart
│   ├── Chart.yaml
│   ├── values.yaml                     # statefulset.enabled: true
│   ├── values-dev.yaml
│   ├── values-prod.yaml
│   └── templates/
│       ├── statefulset.yaml            # statefulset with volumeclaimtemplates
│       ├── headless-service.yaml       # clusterip: none for dns
│       ├── deployment.yaml             # rendered only when both rollout+statefulset disabled
│       ├── rollout.yaml                # rendered only when rollout.enabled=true
│       ├── preview-service.yaml        # blue-green preview service
│       ├── analysis-template.yaml      # rollout analysis
│       ├── service.yaml                # regular service (nodeport)
│       ├── pvc.yaml                    # shared pvc (only when statefulset disabled)
│       ├── configmap.yaml
│       ├── secrets.yaml
│       ├── serviceaccount.yaml
│       ├── hooks/
│       └── _helpers.tpl
├── argocd/
│   └── ...
├── STATEFULSET.md                      # this documentation
├── ROLLOUTS.md
└── CONFIGMAPS.md
```

---

## 7. update strategies (bonus)

### rolling update with partition

partition controls which pods get updated. only pods with ordinal >= partition receive the new spec:

```yaml
statefulset:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 2
```

with `partition: 2` and 3 replicas (`0`, `1`, `2`):
- only pod-2 gets the update
- pod-0 and pod-1 stay on the old version
- useful for canary-style updates on stateful workloads

```bash
# update image and apply
helm upgrade devops-info-service ./k8s/devops-info-service \
  --set image.tag=v1 \
  --set statefulset.updateStrategy.rollingUpdate.partition=2

# only pod-2 restarts with new image
kubectl get pods -o wide

# lower partition to roll out further
helm upgrade devops-info-service ./k8s/devops-info-service \
  --set image.tag=v1 \
  --set statefulset.updateStrategy.rollingUpdate.partition=0
```

### ondelete strategy

pods are only updated when manually deleted — the statefulset controller does not automatically replace them:

```yaml
statefulset:
  updateStrategy:
    type: OnDelete
```

use cases:
- manual control over when each pod updates
- updating one pod at a time in a specific order
- testing new version on a single instance before rolling out

```bash
# update the statefulset spec
helm upgrade devops-info-service ./k8s/devops-info-service \
  --set image.tag=v2 \
  --set statefulset.updateStrategy.type=OnDelete

# pods remain on old version until manually deleted
kubectl delete pod devops-info-service-2
# pod-2 restarts with new version

# delete next pod when ready
kubectl delete pod devops-info-service-1
```

---

## 8. helm deployment

```bash
# deploy with statefulset (default)
helm install devops-info-service ./k8s/devops-info-service

# deploy with specific replica count
helm install devops-info-service ./k8s/devops-info-service \
  --set replicaCount=3

# deploy with ondelete strategy
helm install devops-info-service ./k8s/devops-info-service \
  --set statefulset.updateStrategy.type=OnDelete

# switch back to deployment
helm install devops-info-service ./k8s/devops-info-service \
  --set statefulset.enabled=false \
  --set rollout.enabled=false

# switch to rollout
helm install devops-info-service ./k8s/devops-info-service \
  --set statefulset.enabled=false \
  --set rollout.enabled=true
```

---

## 9. file references

| file | description |
|------|-------------|
| [statefulset.yaml](devops-info-service/templates/statefulset.yaml) | statefulset with volumeclaimtemplates |
| [headless-service.yaml](devops-info-service/templates/headless-service.yaml) | headless service for stable dns |
| [service.yaml](devops-info-service/templates/service.yaml) | regular service for external access |
| [pvc.yaml](devops-info-service/templates/pvc.yaml) | shared pvc (only when statefulset disabled) |
| [deployment.yaml](devops-info-service/templates/deployment.yaml) | deployment (only when both statefulset+rollout disabled) |
| [values.yaml](devops-info-service/values.yaml) | default helm values (statefulset enabled) |
