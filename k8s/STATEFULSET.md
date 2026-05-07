# StatefulSets & Persistent Storage

This document captures the Lab 15 implementation for `k8s/devops-info-service` and the bonus task for StatefulSet update strategies.

## 1. Why StatefulSet

StatefulSet is the right controller when each pod must keep a stable identity and its own persistent data. In this chart that matters because the Flask service stores its visit counter in `/data/visits`, and for Lab 15 each replica must keep an isolated counter instead of sharing a single PVC.

Key differences from Deployment:

| Feature | Deployment | StatefulSet |
|---------|------------|-------------|
| Pod identity | Ephemeral pod names with random suffixes | Stable ordinal names like `app-0`, `app-1`, `app-2` |
| Storage | Usually one shared PVC or no PVC | One PVC per pod via `volumeClaimTemplates` |
| Startup/scaling | Unordered | Ordered by default |
| DNS | Service VIP only | Stable pod DNS through a headless Service |

Typical StatefulSet workloads include PostgreSQL, MySQL, MongoDB, Kafka, RabbitMQ, Elasticsearch, and Cassandra.

## 2. What Was Implemented

The Helm chart now supports a dedicated StatefulSet mode without breaking the earlier Deployment and Argo Rollouts modes:

- `templates/statefulset.yaml`: new StatefulSet resource with `serviceName`, ordered identity, and `volumeClaimTemplates`
- `templates/service.yaml`: new headless Service rendered alongside the regular Service when StatefulSet mode is enabled
- `templates/pvc.yaml`: disabled automatically in StatefulSet mode so that storage comes from `volumeClaimTemplates`
- `templates/deployment.yaml` and `templates/rollout.yaml`: guarded so only one workload mode renders at a time
- `values-statefulset.yaml`: main Lab 15 profile
- `values-statefulset-update.yaml`: reproducible template change for update-strategy tests
- `values-statefulset-partition.yaml`: bonus partitioned rolling update overlay
- `values-statefulset-ondelete.yaml`: bonus OnDelete overlay

## 3. Main StatefulSet Profile

Use this profile for the base lab:

```bash
helm upgrade --install lab15-sts k8s/devops-info-service \
  -n stateful --create-namespace \
  -f k8s/devops-info-service/values-statefulset.yaml
```

The profile enables:

- `replicaCount: 3`
- `statefulset.enabled: true`
- headless Service `lab15-sts-devops-info-service-headless`
- `volumeClaimTemplates` with claim name `data-volume`
- per-pod storage at `/data`

Rendered StatefulSet properties verified locally:

```bash
helm lint k8s/devops-info-service
helm template lab15-sts k8s/devops-info-service \
  -n stateful \
  -f k8s/devops-info-service/values-statefulset.yaml
```

Confirmed in the rendered manifest:

- `kind: StatefulSet`
- `serviceName: lab15-sts-devops-info-service-headless`
- `podManagementPolicy: OrderedReady`
- `volumeClaimTemplates[].metadata.name: data-volume`
- `clusterIP: None` on the headless Service

## 4. Resource Verification

Live verification was completed in a local `kind-lab15` cluster running inside Lima.

```bash
$ kubectl get po,sts,svc,pvc -n stateful -o wide
NAME                                  READY   STATUS    IP            NODE
lab15-sts-devops-info-service-0       1/1     Running   10.244.0.8    lab15-control-plane
lab15-sts-devops-info-service-1       1/1     Running   10.244.0.14   lab15-control-plane
lab15-sts-devops-info-service-2       1/1     Running   10.244.0.20   lab15-control-plane

NAME                                             READY   AGE
statefulset.apps/lab15-sts-devops-info-service   3/3     3m42s

NAME                                             TYPE        CLUSTER-IP    PORT(S)
service/lab15-sts-devops-info-service            NodePort    10.96.99.26   80:30092/TCP
service/lab15-sts-devops-info-service-headless   ClusterIP   None          80/TCP

NAME                                                                STATUS   CAPACITY
data-volume-lab15-sts-devops-info-service-0                         Bound    100Mi
data-volume-lab15-sts-devops-info-service-1                         Bound    100Mi
data-volume-lab15-sts-devops-info-service-2                         Bound    100Mi
```

## 5. Network Identity

StatefulSet pods resolve through the headless Service with this DNS format:

```text
<statefulset-pod-name>.<headless-service>.<namespace>.svc.cluster.local
```

For this lab:

```text
lab15-sts-devops-info-service-1.lab15-sts-devops-info-service-headless.stateful.svc.cluster.local
```

Verification output:

```bash
$ kubectl run dns-test --rm -i --restart=Never --image=busybox:1.36 -n stateful -- \
  nslookup lab15-sts-devops-info-service-1.lab15-sts-devops-info-service-headless.stateful.svc.cluster.local
Name: lab15-sts-devops-info-service-1.lab15-sts-devops-info-service-headless.stateful.svc.cluster.local
Address: 10.244.0.14

$ kubectl run dns-test --rm -i --restart=Never --image=busybox:1.36 -n stateful -- \
  nslookup lab15-sts-devops-info-service-2.lab15-sts-devops-info-service-headless.stateful.svc.cluster.local
Name: lab15-sts-devops-info-service-2.lab15-sts-devops-info-service-headless.stateful.svc.cluster.local
Address: 10.244.0.20
```

## 6. Per-Pod Storage Isolation

Each pod mounts its own PVC at `/data`, and the persisted file `/data/visits` stayed isolated per replica. I incremented pod `-0` twice, pod `-1` once, and pod `-2` three times by calling the local HTTP endpoint inside each pod.

```bash
$ kubectl exec -n stateful lab15-sts-devops-info-service-0 -- python -c '... GET /visits ...'
{"count":2,"file_path":"/data/visits",...}

$ kubectl exec -n stateful lab15-sts-devops-info-service-1 -- python -c '... GET /visits ...'
{"count":1,"file_path":"/data/visits",...}

$ kubectl exec -n stateful lab15-sts-devops-info-service-2 -- python -c '... GET /visits ...'
{"count":3,"file_path":"/data/visits",...}

$ kubectl exec -n stateful lab15-sts-devops-info-service-0 -- cat /data/visits
2
$ kubectl exec -n stateful lab15-sts-devops-info-service-1 -- cat /data/visits
1
$ kubectl exec -n stateful lab15-sts-devops-info-service-2 -- cat /data/visits
3
```

This proves that increments on one pod do not affect the other pods.

## 7. Persistence Test

Persistence was verified by deleting only pod `lab15-sts-devops-info-service-0`:

```bash
$ kubectl exec -n stateful lab15-sts-devops-info-service-0 -- cat /data/visits
2

$ kubectl delete pod lab15-sts-devops-info-service-0 -n stateful
pod "lab15-sts-devops-info-service-0" deleted

$ kubectl wait --for=condition=Ready pod/lab15-sts-devops-info-service-0 -n stateful --timeout=180s
pod/lab15-sts-devops-info-service-0 condition met

$ kubectl exec -n stateful lab15-sts-devops-info-service-0 -- cat /data/visits
2
```

The pod came back with the same ordinal name and kept the same persisted counter value.

## 8. Bonus Task: Update Strategies

### 8.1 Partitioned Rolling Update

I verified the partitioned update in a dedicated namespace `stateful-partition` with release `lab15-partition`. The overlay sets:

```yaml
statefulset:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 2
```

Observed behavior with `replicaCount: 3`:

```bash
$ kubectl rollout status statefulset/lab15-partition-devops-info-service -n stateful-partition
partitioned roll out complete: 1 new pods have been updated...

$ kubectl get pods -n stateful-partition
lab15-partition-devops-info-service-0   Running   AGE 5m40s
lab15-partition-devops-info-service-1   Running   AGE 5m28s
lab15-partition-devops-info-service-2   Running   AGE   39s

$ kubectl exec -n stateful-partition lab15-partition-devops-info-service-0 -- printenv | grep -E 'SERVICE_VERSION|RELEASE_TRACK'
SERVICE_VERSION=1.0.0-stateful
RELEASE_TRACK=stateful

$ kubectl exec -n stateful-partition lab15-partition-devops-info-service-1 -- printenv | grep -E 'SERVICE_VERSION|RELEASE_TRACK'
SERVICE_VERSION=1.0.0-stateful
RELEASE_TRACK=stateful

$ kubectl exec -n stateful-partition lab15-partition-devops-info-service-2 -- printenv | grep -E 'SERVICE_VERSION|RELEASE_TRACK'
SERVICE_VERSION=1.1.0-stateful
RELEASE_TRACK=stateful-v2
```

This proves that only pod `-2` updated, while pods `-0` and `-1` stayed on the old revision.

### 8.2 OnDelete Strategy

I verified `OnDelete` in a dedicated namespace `stateful-ondelete` with release `lab15-ondelete`. The overlay sets:

```yaml
statefulset:
  updateStrategy:
    type: OnDelete
```

Observed behavior:

```bash
$ kubectl exec -n stateful-ondelete lab15-ondelete-devops-info-service-0 -- printenv | grep -E 'SERVICE_VERSION|RELEASE_TRACK'
SERVICE_VERSION=1.0.0-stateful
RELEASE_TRACK=stateful

$ kubectl exec -n stateful-ondelete lab15-ondelete-devops-info-service-1 -- printenv | grep -E 'SERVICE_VERSION|RELEASE_TRACK'
SERVICE_VERSION=1.0.0-stateful
RELEASE_TRACK=stateful

$ kubectl exec -n stateful-ondelete lab15-ondelete-devops-info-service-2 -- printenv | grep -E 'SERVICE_VERSION|RELEASE_TRACK'
SERVICE_VERSION=1.0.0-stateful
RELEASE_TRACK=stateful

$ kubectl delete pod lab15-ondelete-devops-info-service-2 -n stateful-ondelete
pod "lab15-ondelete-devops-info-service-2" deleted

$ kubectl wait --for=condition=Ready pod/lab15-ondelete-devops-info-service-2 -n stateful-ondelete --timeout=180s
pod/lab15-ondelete-devops-info-service-2 condition met

$ kubectl exec -n stateful-ondelete lab15-ondelete-devops-info-service-2 -- printenv | grep -E 'SERVICE_VERSION|RELEASE_TRACK'
SERVICE_VERSION=1.1.0-stateful
RELEASE_TRACK=stateful-v2
```

Pods `-0` and `-1` stayed on the old revision, and pod `-2` switched only after manual deletion, which matches the `OnDelete` behavior.

Use cases for `OnDelete`:

- coordinated updates where each replica must be drained manually
- stateful systems that need operator supervision
- maintenance windows where automatic rollout is undesirable

## 9. Files Added for Lab 15

- `k8s/devops-info-service/templates/statefulset.yaml`
- `k8s/devops-info-service/values-statefulset.yaml`
- `k8s/devops-info-service/values-statefulset-update.yaml`
- `k8s/devops-info-service/values-statefulset-partition.yaml`
- `k8s/devops-info-service/values-statefulset-ondelete.yaml`
- `k8s/STATEFULSET.md`
