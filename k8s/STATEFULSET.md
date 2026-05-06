# Lab 15 — StatefulSets & Persistent Storage

This lab converts the `devops-info-service` Helm chart from a `Deployment` (Lab 12)
to a `StatefulSet` with stable network identities and per‑pod persistent storage,
then exercises the two non‑default update strategies (`partition` and `OnDelete`).

All commands were executed against a local `minikube` profile named `lab15`
(Kubernetes v1.35.1, Docker driver, default `standard` storage class).
Raw command output is preserved under `k8s/statefulset/evidence/`.

---

## 1. StatefulSet Overview

### Why StatefulSet vs Deployment

`Deployment` treats pods as fungible cattle: any pod can serve any traffic, any
PVC can be shared, and pod names contain a random hash. That breaks down for
workloads that need *identity* — databases that elect a leader, queues whose
brokers must rejoin under the same name, or a counter file that must follow a
specific replica through a restart.

`StatefulSet` provides three guarantees that `Deployment` does not:

| Guarantee                | Deployment                    | StatefulSet                                    |
|--------------------------|-------------------------------|------------------------------------------------|
| **Pod naming**           | `<name>-<rs-hash>-<random>`   | `<name>-0`, `<name>-1`, … (ordinal)            |
| **Network identity**     | Random IP, no per‑pod DNS     | `<pod>.<headless-svc>.<ns>.svc.cluster.local`  |
| **Storage**              | One shared PVC at most        | One PVC per pod via `volumeClaimTemplates`     |
| **Scaling order**        | Parallel                      | Ordered `0 → 1 → … → N` (or `Parallel` opt‑in) |
| **Update order**         | Driven by `RollingUpdate` RS  | Reverse ordinal, with `partition` gate         |

### Headless Service

A `Service` with `clusterIP: None` is "headless": kube‑proxy doesn't load‑balance
to it, and CoreDNS instead returns the **per‑pod A records** that the
StatefulSet controller registers. This is what gives `pod-0.<svc>` its stable
DNS name. Our chart keeps the regular `ClusterIP` service for app traffic
(`info-devops-info-service`) and adds a sibling headless service
(`info-devops-info-service-headless`) used purely for pod discovery.

### Use cases

Stateful workloads worth a `StatefulSet`: databases (Postgres, MySQL primary +
replicas, MongoDB replica sets), message brokers (Kafka, RabbitMQ clusters),
search and storage (Elasticsearch, Cassandra, etcd). Stateless apps stay on
`Deployment` (or, for progressive delivery, `Argo Rollout` from Lab 14).

---

## 2. Implementation

The chart toggles between Deployment, Rollout and StatefulSet via values flags
so the three controllers are mutually exclusive:

- `k8s/devops-info-service/templates/statefulset.yaml` — new
- `k8s/devops-info-service/templates/headless-service.yaml` — new
- `k8s/devops-info-service/templates/deployment.yaml` — gated `if not rollout.enabled and not statefulset.enabled`
- `k8s/devops-info-service/templates/pvc.yaml` — gated `if persistence.enabled and not statefulset.enabled` (StatefulSet manages its own PVCs via `volumeClaimTemplates`)
- `k8s/devops-info-service/values.yaml` — added `statefulset.{enabled,podManagementPolicy,updateStrategy}` (default off, keeps lab12–14 compatible)
- `k8s/devops-info-service/values-statefulset.yaml` — turn‑key values file for this lab

The StatefulSet uses a `volumeClaimTemplates` block named `data` mounted at
`/data`, which matches the `VISITS_FILE=/data/visits` env that the FastAPI app
already reads. No application code change was needed — the per‑pod PVC alone
is what gives each replica its own visit counter.

Install:

```bash
minikube start -p lab15 --driver=docker
eval "$(minikube -p lab15 docker-env)"
docker build -t devops-info-service:lab15 ./app_python
helm install info ./k8s/devops-info-service -f ./k8s/devops-info-service/values-statefulset.yaml
```

---

## 3. Resource Verification

`kubectl get po,sts,svc,pvc -l app.kubernetes.io/instance=info -o wide`
([raw evidence](statefulset/evidence/01-resources.txt)):

```
NAME                             READY   STATUS    RESTARTS   AGE   IP           NODE    NOMINATED NODE   READINESS GATES
pod/info-devops-info-service-0   1/1     Running   0          39s   10.244.0.5   lab15   <none>           <none>
pod/info-devops-info-service-1   1/1     Running   0          29s   10.244.0.6   lab15   <none>           <none>
pod/info-devops-info-service-2   1/1     Running   0          20s   10.244.0.7   lab15   <none>           <none>

NAME                                        READY   AGE   CONTAINERS            IMAGES
statefulset.apps/info-devops-info-service   3/3     39s   devops-info-service   devops-info-service:lab15

NAME                                        TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE   SELECTOR
service/info-devops-info-service            ClusterIP   10.106.247.32   <none>        80/TCP    39s   app.kubernetes.io/instance=info,app.kubernetes.io/name=devops-info-service
service/info-devops-info-service-headless   ClusterIP   None            <none>        80/TCP    39s   app.kubernetes.io/instance=info,app.kubernetes.io/name=devops-info-service

NAME                                                    STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE   VOLUMEMODE
persistentvolumeclaim/data-info-devops-info-service-0   Bound    pvc-8e96da3d-bcb2-46c5-8d21-bd6337765d3a   100Mi      RWO            standard       <unset>                 39s
persistentvolumeclaim/data-info-devops-info-service-1   Bound    pvc-09bfd21b-aa28-421d-814c-01e6bcca2a05   100Mi      RWO            standard       <unset>                 29s
persistentvolumeclaim/data-info-devops-info-service-2   Bound    pvc-5089c70a-0381-4444-baf2-40967480d705   100Mi      RWO            standard       <unset>                 20s
```

Notes:

- **Ordered start**: ages decrease by ~10s per ordinal — the controller waits
  for `pod-0` to be Ready before starting `pod-1`, etc. (`OrderedReady` policy).
- **Per‑pod PVCs**: claim names `data-<sts>-<n>` are auto‑generated from the
  `volumeClaimTemplates.name` plus the pod ordinal. Each is `Bound` to a unique
  PV.
- **Two services**: the regular `ClusterIP` service for app traffic; the
  `clusterIP: None` headless service for stable DNS records.

`kubectl describe sts info-devops-info-service`
([raw evidence](statefulset/evidence/06-sts-describe.txt)) confirms the
template, update strategy (`RollingUpdate`, partition 0), and the
`volumeClaimTemplates` definition.

---

## 4. Network Identity (DNS)

### From a throwaway `busybox` pod

`nslookup` against CoreDNS for the per‑pod FQDNs and the headless service
([raw evidence](statefulset/evidence/02-dns.txt)):

```
=== nslookup pod-0 ===
Name:    info-devops-info-service-0.info-devops-info-service-headless.default.svc.cluster.local
Address: 10.244.0.5

=== nslookup pod-1 ===
Name:    info-devops-info-service-1.info-devops-info-service-headless.default.svc.cluster.local
Address: 10.244.0.6

=== nslookup pod-2 ===
Name:    info-devops-info-service-2.info-devops-info-service-headless.default.svc.cluster.local
Address: 10.244.0.7

=== nslookup headless service (returns ALL pod IPs, no VIP) ===
Name:    info-devops-info-service-headless.default.svc.cluster.local
Address: 10.244.0.7
Address: 10.244.0.6
Address: 10.244.0.5

=== nslookup ClusterIP service (returns the VIP) ===
Name:    info-devops-info-service.default.svc.cluster.local
Address: 10.106.247.32
```

The headless lookup returns three A records (one per pod), while the regular
`ClusterIP` service returns the cluster VIP. That contrast is exactly what
makes a headless service useful for stateful peers: every replica can
enumerate the others.

### From inside `pod-0`

`kubectl exec info-devops-info-service-0 -- ...`
([raw evidence](statefulset/evidence/03-dns-from-pod.txt)):

```
=== hostname inside pod-0 ===
info-devops-info-service-0

=== getent hosts pod-1 / pod-2 ===
10.244.0.6      info-devops-info-service-1.info-devops-info-service-headless.default.svc.cluster.local
10.244.0.7      info-devops-info-service-2.info-devops-info-service-headless.default.svc.cluster.local

=== http GET pod-1:5000/health (pod-to-pod via stable DNS) ===
200 {"status":"healthy","timestamp":"2026-05-06T10:47:58.427571+00:00","uptime_seconds":89}

=== http GET pod-2:5000/health ===
200 {"status":"healthy","timestamp":"2026-05-06T10:47:58.724992+00:00","uptime_seconds":80}
```

Pod hostname matches the StatefulSet ordinal. Pod‑to‑pod traffic via the
stable DNS name reaches the right replica.

**DNS pattern:** `<pod-name>.<headless-service>.<namespace>.svc.cluster.local`.

---

## 5. Per‑Pod Storage Isolation

I generated a different number of root‑page hits per replica via three
parallel `kubectl port-forward`s (pod‑0 → 18080, pod‑1 → 18081, pod‑2 → 18082)
and `curl`d `/` 5×, 2×, 9× respectively. Then read `/visits` and the raw file
on disk
([raw evidence](statefulset/evidence/04-per-pod-visits.txt)):

```
=== Per-pod visit counts via /visits endpoint (no increment) ===
pod-0: {"visits":5,"file":"/data/visits"}
pod-1: {"visits":2,"file":"/data/visits"}
pod-2: {"visits":9,"file":"/data/visits"}

=== Direct file inspection (per-pod /data/visits backed by per-pod PVC) ===
pod-0 /data/visits: 5
pod-1 /data/visits: 2
pod-2 /data/visits: 9
```

Three different counts on the same `/data/visits` path = three independent
volumes. Under a `Deployment` with a single shared `ReadWriteOnce` PVC this
would be impossible (and only one pod could even mount it).

---

## 6. Persistence Across Pod Restart

Delete `pod-0`, let the controller recreate it, verify the counter survives
([raw evidence](statefulset/evidence/05-persistence.txt)):

```
=== Before deletion ===
pod-0 visits: 5
pod-0 PVC: pvc-8e96da3d-bcb2-46c5-8d21-bd6337765d3a
info-devops-info-service-0   1/1   Running   0   2m35s   10.244.0.5

=== Deleting pod info-devops-info-service-0 ===
pod "info-devops-info-service-0" deleted

=== After restart ===
info-devops-info-service-0   1/1   Running   0   9s    10.244.0.9
pod-0 PVC still: pvc-8e96da3d-bcb2-46c5-8d21-bd6337765d3a
pod-0 visits after restart: 5
pod-1 visits (unchanged):    2
pod-2 visits (unchanged):    9
```

What this proves:

- Pod IP changed (`10.244.0.5 → 10.244.0.9`) — pods are still ephemeral.
- DNS name (`info-devops-info-service-0`) and PVC binding
  (`pvc-8e96da3d…`) did **not** change — that's the StatefulSet identity guarantee.
- File contents on the re‑attached volume are byte‑identical (5).
- Pod‑1 and pod‑2 were untouched.

---

## 7. Bonus — Update Strategies

### 7a. Partitioned `RollingUpdate`

Updated `image.tag` to `lab15v2` and set `partition: 2`. Only pods with
ordinal `>= 2` should roll
([raw evidence](statefulset/evidence/07-bonus-partition.txt)):

```
=== Helm upgrade with image tag lab15v2 + partition=2 ===
Release "info" has been upgraded. Happy Helming!
partitioned roll out complete: 1 new pods have been updated...

=== Per-pod images ===
pod-0: devops-info-service:lab15
pod-1: devops-info-service:lab15
pod-2: devops-info-service:lab15v2

=== StatefulSet update strategy ===
{
    "rollingUpdate": { "maxUnavailable": 1, "partition": 2 },
    "type": "RollingUpdate"
}

=== Visit counts unaffected ===
pod-0: 5   pod-1: 2   pod-2: 9
```

Then lower the partition to 0 to finish the rollout
([raw evidence](statefulset/evidence/08-bonus-partition-complete.txt)):

```
partitioned roll out complete: 3 new pods have been updated...
pod-0: devops-info-service:lab15v2
pod-1: devops-info-service:lab15v2
pod-2: devops-info-service:lab15v2
Visit counts: 5 / 2 / 9   (PVCs persisted across the rollout)
```

**Use case.** Canary‑style rollout for stateful workloads: stage a new
template on the highest‑ordinal replica, validate it (often the last replica
is also the spare or asynchronous follower), then decrement the partition to
roll the rest. Combined with `maxUnavailable`, this gives controlled,
recoverable upgrades for things like database read replicas.

### 7b. `OnDelete`

Switched `updateStrategy.type` to `OnDelete` and changed the image tag again.
Pods should keep running the old template until *manually* deleted
([raw evidence](statefulset/evidence/09-bonus-ondelete.txt)):

```
=== Update strategy is now OnDelete ===
{ "type": "OnDelete" }

=== Pods STILL run lab15v2 — controller will not auto-replace them ===
pod-0: devops-info-service:lab15v2
pod-1: devops-info-service:lab15v2
pod-2: devops-info-service:lab15v2

=== Manually delete pod-1 only ===
pod "info-devops-info-service-1" deleted

=== After manual delete: only pod-1 picked up the new template ===
pod-0: devops-info-service:lab15v2
pod-1: devops-info-service:lab15      <-- only this one updated
pod-2: devops-info-service:lab15v2

Visit counts: 5 / 2 / 9   (still preserved)
```

**Use case.** Workloads where pod replacement is expensive or coordination is
non‑trivial — Kafka brokers that need a controlled leader transfer, Cassandra
nodes that need `nodetool drain`, primary databases that should only fail
over during a maintenance window. `OnDelete` hands replacement scheduling to
the operator (a human or a higher‑level operator/controller).

---

## Appendix — Evidence index

Raw command output is checked into `k8s/statefulset/evidence/`:

| File                           | What it shows                                               |
|--------------------------------|-------------------------------------------------------------|
| `01-resources.txt`             | `kubectl get po,sts,svc,pvc -l app.kubernetes.io/instance=info` |
| `02-dns.txt`                   | `nslookup` from a busybox pod (pod FQDNs + both services)   |
| `03-dns-from-pod.txt`          | `getent` + pod‑to‑pod HTTP from inside `pod-0`              |
| `04-per-pod-visits.txt`        | Distinct visit counts per pod (5 / 2 / 9)                   |
| `05-persistence.txt`           | Pod‑0 deleted; PVC re‑attaches, visits stay at 5            |
| `06-sts-describe.txt`          | `kubectl describe sts` (template + update strategy)         |
| `07-bonus-partition.txt`       | `partition: 2` — only pod‑2 rolls                           |
| `08-bonus-partition-complete.txt` | `partition: 0` — full rollout finishes                   |
| `09-bonus-ondelete.txt`        | `OnDelete` — only the pod you delete picks up the new spec  |

