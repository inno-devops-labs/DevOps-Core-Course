# Lab 15: StatefulSet

## Overview

For Lab 15, the Helm chart now renders a `StatefulSet` by default instead of an Argo `Rollout`. The rollout templates from Lab 14 are still in the chart, but they are disabled unless `rollout.enabled=true`.

This is the right fit for the lab because the application now keeps state in a file at `/data/visits`, and each pod needs:

- a stable ordinal name such as `lab15-stateful-devops-info-service-0`
- a stable DNS record through a headless service
- its own persistent volume claim created from `volumeClaimTemplates`

Compared with a `Deployment` or `Rollout`:

- `StatefulSet` is better when pod identity and storage matter.
- `Deployment` is better for interchangeable stateless replicas.
- `Rollout` is best when release strategy is the main concern, such as canary or blue-green promotion.

## What Changed

- `app_python/src/app.py`
  - `GET /` now increments a file-backed counter and returns it in the response.
  - `GET /visits` returns the persisted count without incrementing it.
  - visits are stored in `VISITS_FILE`, which defaults to `/data/visits`
  - missing or invalid counter files safely fall back to `0`
- `k8s/devops-info-service/templates/statefulset.yaml`
  - new default workload
- `k8s/devops-info-service/templates/headless-service.yaml`
  - new service with `clusterIP: None`
- `k8s/devops-info-service/values.yaml`
  - default service type changed to `ClusterIP`
  - persistence enabled by default
  - `rollout.enabled: false`
- `k8s/devops-info-service/values-stateful-partition.yaml`
  - bonus partitioned rolling update demo
- `k8s/devops-info-service/values-stateful-ondelete.yaml`
  - bonus `OnDelete` demo

## Static Verification

Unit tests:

```bash
.venv/bin/pytest app_python/tests -q
...................                                                      [100%]
19 passed in 1.20s
```

Helm lint:

```bash
helm lint k8s/devops-info-service
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

Default chart render:

```bash
helm template lab15-stateful k8s/devops-info-service | rg -n "^kind: (StatefulSet|Rollout|AnalysisTemplate)$|clusterIP: None|volumeClaimTemplates|type: ClusterIP"
52:  clusterIP: None
78:  type: ClusterIP
91:kind: StatefulSet
191:  volumeClaimTemplates:
```

Partition override render:

```bash
helm template lab15-stateful k8s/devops-info-service -f k8s/devops-info-service/values-stateful-partition.yaml | rg -n "^kind: StatefulSet$|partition: 2|clusterIP: None|^kind: Rollout$"
52:  clusterIP: None
91:kind: StatefulSet
111:      partition: 2
```

OnDelete override render:

```bash
helm template lab15-stateful k8s/devops-info-service -f k8s/devops-info-service/values-stateful-ondelete.yaml | rg -n "^kind: StatefulSet$|type: OnDelete|clusterIP: None|^kind: Rollout$"
52:  clusterIP: None
91:kind: StatefulSet
109:    type: OnDelete
```

## Live Deployment

Image build and install:

```bash
docker build -t devops-info-service:lab15 ./app_python
minikube image load devops-info-service:lab15
helm upgrade --install lab15-stateful k8s/devops-info-service -n lab15-stateful --create-namespace --wait --wait-for-jobs --timeout 5m
```

Cluster state after install:

```bash
kubectl get po,sts,svc,pvc -n lab15-stateful
NAME                                       READY   STATUS    RESTARTS   AGE
pod/lab15-stateful-devops-info-service-0   1/1     Running   0          51s
pod/lab15-stateful-devops-info-service-1   1/1     Running   0          44s
pod/lab15-stateful-devops-info-service-2   1/1     Running   0          37s

NAME                                                  READY   AGE
statefulset.apps/lab15-stateful-devops-info-service   3/3     51s

NAME                                                  TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
service/lab15-stateful-devops-info-service            ClusterIP   10.104.122.56   <none>        80/TCP    51s
service/lab15-stateful-devops-info-service-headless   ClusterIP   None            <none>        80/TCP    51s

NAME                                                              STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/data-lab15-stateful-devops-info-service-0   Bound    pvc-e150f739-c77c-458a-843e-f3c5633c7b39   100Mi      RWO            standard       <unset>                 51s
persistentvolumeclaim/data-lab15-stateful-devops-info-service-1   Bound    pvc-c3416b00-709a-4249-983c-0dd3a6ed0c93   100Mi      RWO            standard       <unset>                 44s
persistentvolumeclaim/data-lab15-stateful-devops-info-service-2   Bound    pvc-028238e0-651e-4ef0-ba24-7967566bc9b4   100Mi      RWO            standard       <unset>                 37s
```

This shows the StatefulSet guarantees that the pods come up as `-0`, `-1`, and `-2`, and that each ordinal gets its own PVC.

## Stable DNS Identity

The headless service gives each pod a resolvable identity:

```bash
kubectl exec -n lab15-stateful lab15-stateful-devops-info-service-0 -- python -c "import socket; host='lab15-stateful-devops-info-service-1.lab15-stateful-devops-info-service-headless.lab15-stateful.svc.cluster.local'; print(host, socket.gethostbyname(host))"
lab15-stateful-devops-info-service-1.lab15-stateful-devops-info-service-headless.lab15-stateful.svc.cluster.local 10.244.0.49
```

The mounted counter location is the expected persistent path:

```bash
kubectl exec -n lab15-stateful lab15-stateful-devops-info-service-0 -- python -c "import os; print(os.environ['VISITS_FILE'])"
/data/visits
```

## Per-Pod Visit Isolation

I port-forwarded directly to pod `-0` and pod `-1` so I could hit them independently:

```bash
kubectl port-forward -n lab15-stateful pod/lab15-stateful-devops-info-service-0 18080:5000
kubectl port-forward -n lab15-stateful pod/lab15-stateful-devops-info-service-1 18081:5000
```

Before any traffic, both pods started with their own `0` count:

```bash
curl -s http://127.0.0.1:18080/visits
{"file":"/data/visits","visits":0}

curl -s http://127.0.0.1:18081/visits
{"file":"/data/visits","visits":0}
```

Then I hit `/` three times on pod `-0` and once on pod `-1`. The relevant response fields show independent state:

```bash
curl -s http://127.0.0.1:18080/
{"service":{"version":"1.0.0-stateful"},"system":{"hostname":"lab15-stateful-devops-info-service-0"},"visits":{"count":3,"file":"/data/visits"}, ...}

curl -s http://127.0.0.1:18081/
{"service":{"version":"1.0.0-stateful"},"system":{"hostname":"lab15-stateful-devops-info-service-1"},"visits":{"count":1,"file":"/data/visits"}, ...}
```

Playwright screenshots:

- [pod-0-visits.png](screenshots/lab15/pod-0-visits.png)
- [pod-1-visits.png](screenshots/lab15/pod-1-visits.png)

## Persistence After Pod Recreation

Before deleting pod `-0`, its counter was:

```bash
curl -s http://127.0.0.1:18080/visits
{"file":"/data/visits","visits":3}
```

After deleting the pod, the StatefulSet recreated ordinal `0` on the same PVC:

```bash
kubectl delete pod -n lab15-stateful lab15-stateful-devops-info-service-0
kubectl wait --for=condition=Ready pod/lab15-stateful-devops-info-service-0 -n lab15-stateful --timeout=180s
kubectl get pvc -n lab15-stateful data-lab15-stateful-devops-info-service-0 -o wide
NAME                                        STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE     VOLUMEMODE
data-lab15-stateful-devops-info-service-0   Bound    pvc-e150f739-c77c-458a-843e-f3c5633c7b39   100Mi      RWO            standard       <unset>                 2m27s   Filesystem
```

After reconnecting to the recreated pod, the counter was still `3`:

```bash
kubectl port-forward -n lab15-stateful pod/lab15-stateful-devops-info-service-0 18082:5000
curl -s http://127.0.0.1:18082/visits
{"file":"/data/visits","visits":3}
```

Playwright screenshot:

- [pod-0-visits-after-restart.png](screenshots/lab15/pod-0-visits-after-restart.png)

## Bonus: Partitioned Rolling Update

I upgraded the release with the partition override:

```bash
helm upgrade lab15-stateful k8s/devops-info-service -n lab15-stateful -f k8s/devops-info-service/values-stateful-partition.yaml --wait --wait-for-jobs --timeout 5m
```

The StatefulSet strategy changed to `RollingUpdate` with `partition=2`:

```bash
kubectl get sts lab15-stateful-devops-info-service -n lab15-stateful -o jsonpath='{.spec.updateStrategy.type}{" partition="}{.spec.updateStrategy.rollingUpdate.partition}{" currentRevision="}{.status.currentRevision}{" updateRevision="}{.status.updateRevision}{"\n"}'
RollingUpdate partition=2 currentRevision=lab15-stateful-devops-info-service-5545cbf5cb updateRevision=lab15-stateful-devops-info-service-799f88fd85
```

Only ordinal `2` picked up the new version automatically:

```bash
for pod in 0 1 2; do printf "pod-%s " "$pod"; kubectl exec -n lab15-stateful lab15-stateful-devops-info-service-$pod -- printenv DEVOPS_SERVICE_VERSION; done
pod-0 1.0.0-stateful
pod-1 1.0.0-stateful
pod-2 1.1.0-partition
```

Pod start times confirm that only pod `-2` was recreated:

```bash
kubectl get pods -n lab15-stateful -o custom-columns=NAME:.metadata.name,START:.status.startTime,IP:.status.podIP
NAME                                   START                  IP
lab15-stateful-devops-info-service-0   2026-05-07T18:35:36Z   10.244.0.52
lab15-stateful-devops-info-service-1   2026-05-07T18:33:16Z   10.244.0.49
lab15-stateful-devops-info-service-2   2026-05-07T18:36:55Z   10.244.0.53
```

## Bonus: OnDelete Strategy

Then I upgraded the release again with the `OnDelete` override:

```bash
helm upgrade lab15-stateful k8s/devops-info-service -n lab15-stateful -f k8s/devops-info-service/values-stateful-ondelete.yaml --wait --wait-for-jobs --timeout 5m
```

The StatefulSet accepted the new template, but did not restart any pods on its own:

```bash
kubectl get sts lab15-stateful-devops-info-service -n lab15-stateful -o jsonpath='{.spec.updateStrategy.type}{" currentRevision="}{.status.currentRevision}{" updateRevision="}{.status.updateRevision}{"\n"}'
OnDelete currentRevision=lab15-stateful-devops-info-service-5545cbf5cb updateRevision=lab15-stateful-devops-info-service-75fbddf976
```

Versions stayed unchanged until a manual deletion:

```bash
for pod in 0 1 2; do printf "pod-%s " "$pod"; kubectl exec -n lab15-stateful lab15-stateful-devops-info-service-$pod -- printenv DEVOPS_SERVICE_VERSION; done
pod-0 1.0.0-stateful
pod-1 1.0.0-stateful
pod-2 1.1.0-partition
```

After deleting only pod `-1`, only that pod adopted `1.2.0-ondelete`:

```bash
kubectl delete pod -n lab15-stateful lab15-stateful-devops-info-service-1

for pod in 0 1 2; do printf "pod-%s " "$pod"; kubectl exec -n lab15-stateful lab15-stateful-devops-info-service-$pod -- printenv DEVOPS_SERVICE_VERSION; done
pod-0 1.0.0-stateful
pod-1 1.2.0-ondelete
pod-2 1.1.0-partition
```

The recreated pod `-1` also got a new start time and UID:

```bash
kubectl get pods -n lab15-stateful -o custom-columns=NAME:.metadata.name,START:.status.startTime,UID:.metadata.uid
NAME                                   START                  UID
lab15-stateful-devops-info-service-0   2026-05-07T18:35:36Z   c2bba02f-d175-44d0-9cfa-2a5ea3400cc9
lab15-stateful-devops-info-service-1   2026-05-07T18:38:36Z   812ab0b9-37a7-457d-b34a-cd2b5091815f
lab15-stateful-devops-info-service-2   2026-05-07T18:36:55Z   3239430d-51ed-45a2-a14d-d4a33a2279df
```

I then manually recreated the remaining outdated pods so the namespace finished in a fully converged state:

```bash
for pod in 0 1 2; do printf "pod-%s " "$pod"; kubectl exec -n lab15-stateful lab15-stateful-devops-info-service-$pod -- printenv DEVOPS_SERVICE_VERSION; done
pod-0 1.2.0-ondelete
pod-1 1.2.0-ondelete
pod-2 1.2.0-ondelete
```

Final resource state:

```bash
kubectl get po,sts,svc,pvc -n lab15-stateful
NAME                                       READY   STATUS    RESTARTS   AGE
pod/lab15-stateful-devops-info-service-0   1/1     Running   0          19s
pod/lab15-stateful-devops-info-service-1   1/1     Running   0          2m23s
pod/lab15-stateful-devops-info-service-2   1/1     Running   0          80s

NAME                                                  READY   AGE
statefulset.apps/lab15-stateful-devops-info-service   3/3     7m50s

NAME                                                  TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
service/lab15-stateful-devops-info-service            ClusterIP   10.104.122.56   <none>        80/TCP    7m50s
service/lab15-stateful-devops-info-service-headless   ClusterIP   None            <none>        80/TCP    7m50s

NAME                                                              STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/data-lab15-stateful-devops-info-service-0   Bound    pvc-e150f739-c77c-458a-843e-f3c5633c7b39   100Mi      RWO            standard       <unset>                 7m50s
persistentvolumeclaim/data-lab15-stateful-devops-info-service-1   Bound    pvc-c3416b00-709a-4249-983c-0dd3a6ed0c93   100Mi      RWO            standard       <unset>                 7m43s
persistentvolumeclaim/data-lab15-stateful-devops-info-service-2   Bound    pvc-028238e0-651e-4ef0-ba24-7967566bc9b4   100Mi      RWO            standard       <unset>                 7m36s
```

## Result

Lab 15 is complete:

- the chart is StatefulSet-first
- the app persists visit counts per pod at `/data/visits`
- `/visits` exposes the current persisted value
- each pod gets its own PVC and stable network identity
- visit counts survive pod recreation
- the bonus `partition` and `OnDelete` strategies are both implemented and verified
