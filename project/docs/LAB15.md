# Lab 15 — StatefulSets & Persistent Storage

This document covers the StatefulSet extension of the `devops-info-service` Helm chart. The full operator runbook (install, demos, evidence, troubleshooting) lives in **[`k8s/STATEFULSET.md`](../k8s/STATEFULSET.md)**; this report summarises decisions and points to the evidence.

Course lab spec: [`labs/lab15.md`](../../labs/lab15.md) (repository root).

---

## Objectives

- Add a third workload mode to the chart (alongside Lab 13 `Deployment` and Lab 14 `Rollout`): a `StatefulSet` with stable per-pod identity and per-pod persistent storage.
- Introduce a headless Service (`clusterIP: None`) so each pod gets a stable DNS name.
- Replace the single shared PVC with `volumeClaimTemplates` so every replica owns its own volume.
- Verify ordered startup, per-pod storage isolation, and data survival across pod deletion.
- (Bonus) Demonstrate the two `updateStrategy` modes: `RollingUpdate` with `partition`, and `OnDelete`.

---

## Chart changes

```
k8s/devops-info-service/
├── values.yaml                          # +statefulset.* block (default statefulset.enabled: false)
└── templates/
    ├── deployment.yaml                  # guard now: not rollout AND not statefulset
    ├── rollout.yaml                     # guard now: rollout AND not statefulset
    ├── pvc.yaml                         # guard now: persistence AND not statefulset
    ├── statefulset.yaml                 # NEW — apps/v1 StatefulSet with volumeClaimTemplates
    └── headless-service.yaml            # NEW — clusterIP: None for stable pod DNS
```

### Key design decisions

| Decision | Reason |
|----------|--------|
| Single `statefulset.enabled` toggle in `values.yaml`, mirroring `rollout.enabled` | One chart, three render shapes (Deployment / Rollout / StatefulSet). Lab 13/14/15 install commands all target the same chart directory. |
| Both `deployment.yaml` and `rollout.yaml` get an extra `(not .Values.statefulset.enabled)` guard | Exactly one workload controller renders at a time, never zero, never two. |
| The standalone `pvc.yaml` is **disabled** when `statefulset.enabled=true` | `volumeClaimTemplates` issue one PVC per ordinal automatically; a separate top-level PVC would just be orphaned. |
| `podManagementPolicy: OrderedReady` rendered explicitly | Lab requires the ordered scale-up demo. Same as the Kubernetes default, but explicit is documentation. |
| `publishNotReadyAddresses: true` on the headless Service | DNS resolves to a pod as soon as it starts (before readiness passes) — important for clustered apps that bootstrap via peer discovery (Kafka, Cassandra). |
| `updateStrategy.rollingUpdate.partition` defaults to `0` | All ordinals update by default; bonus demo flips it to `2` to pin pods 0 and 1. |

---

## StatefulSet Fundamentals (Task 1)

| Feature | Deployment | StatefulSet |
|---------|------------|-------------|
| Pod names | Random suffix (`app-abc12-xyz9`) | Ordinal (`app-0`, `app-1`, `app-2`) |
| Storage | One shared PVC (RWO ⇒ 1 replica) | Per-pod PVC via `volumeClaimTemplates` |
| Scale ordering | Parallel | Ordered (`-0` ready before `-1`) |
| Network identity | None — only Service DNS | Stable per-pod DNS via headless Service |
| Best for | Stateless web/API | Databases, queues, distributed systems (PostgreSQL, Kafka, Elasticsearch, Cassandra) |

A **headless Service** is a `Service` with `clusterIP: None`. Instead of a virtual IP, CoreDNS returns one A record per Ready endpoint, and the StatefulSet controller registers a per-pod subdomain: `<pod>.<headless-svc>.<ns>.svc.cluster.local`. That's how `lab15-devops-info-service-0` becomes routable by name regardless of its pod IP.

---

## Convert Deployment to StatefulSet (Task 2)

```yaml
# values.yaml — new block (default disabled)
statefulset:
  enabled: false
  replicas: 3
  storage:
    size: 100Mi
    storageClass: ""        # "" = cluster default
    accessMode: ReadWriteOnce
  updateStrategy:
    type: RollingUpdate     # RollingUpdate | OnDelete
    rollingUpdate:
      partition: 0
```

```bash
helm install lab15 ./k8s/devops-info-service \
  --set statefulset.enabled=true \
  --set statefulset.replicas=3
```

See runbook §2 (chart layout) and §3 (resource verification) for the rendered StatefulSet, both Services, three Pods, and three Bound PVCs.

---

## Headless Service & Pod Identity (Task 3)

```bash
kubectl run dns-debug --image=busybox:1.36 --restart=Never --command -- \
  sh -c 'nslookup lab15-devops-info-service-headless'

nslookup lab15-devops-info-service-0.lab15-devops-info-service-headless.default.svc.cluster.local
```

The bulk headless query returns three A records (one per Ready pod); each `<pod>.<headless-svc>` FQDN resolves to exactly the matching pod IP. See runbook §4.

Per-pod storage isolation is shown by writing distinct values into each pod's `/data/visits` and reading them back; the values stay isolated. See runbook §5.

Persistence across pod deletion is shown by capturing pod-1's PVC UID before delete and after — the pod UID changes, the PVC UID does not, the counter value survives. See runbook §6.

---

## Bonus — Update Strategies (2.5 pts)

`partition=N` updates only pods with ordinal ≥ N. The demo sets `partition=2`, patches the pod template, and shows that **only pod-2** receives a new UID and the new label — pods 0 and 1 stay on the old spec.

`OnDelete` disables automatic rollouts entirely. After a spec change, all pods keep their UIDs; only when the operator runs `kubectl delete pod -0` does that pod pick up the new spec, leaving 1 and 2 untouched. Useful for clustered apps where rollout order must be driven by external logic.

See runbook §7 for both demos with `kubectl patch` + UID/label tables.

---

## Task mapping

| Lab task | Points | Manifests / commands |
|----------|--------|----------------------|
| StatefulSet concepts | 2 pts | [comparison table](#statefulset-fundamentals-task-1) + runbook §1 |
| Convert Deployment to StatefulSet | 3 pts | `templates/statefulset.yaml`, `templates/headless-service.yaml`, `statefulset.*` values block — runbook §2–§3 |
| Headless Service & pod identity | 3 pts | `nslookup` evidence (runbook §4), per-pod `/data/visits` isolation (runbook §5), persistence after pod delete (runbook §6) |
| Documentation | 2 pts | this report + [`k8s/STATEFULSET.md`](../k8s/STATEFULSET.md) |
| Bonus — update strategies | 2.5 pts | `updateStrategy` block in `templates/statefulset.yaml`; partition + OnDelete demos in runbook §7 |

---

## Local verification (no cluster)

```bash
cd project/k8s/devops-info-service

helm lint .
helm lint . --set statefulset.enabled=true

helm template lab15 . | grep -E '^kind:'                                # → Deployment (default, no StatefulSet)
helm template lab15 . --set rollout.enabled=true | grep -E '^kind:'     # → Rollout (no Deployment)
helm template lab15 . --set statefulset.enabled=true | grep -E '^kind:' # → StatefulSet + 2 Services (no Deployment, no Rollout, no standalone PVC)

helm template lab15 . --set statefulset.enabled=true | grep -c 'volumeClaimTemplates'  # → 1
```

All four assertions pass on `feat/lab15`.

---

## Further reading

- Operator runbook: [`k8s/STATEFULSET.md`](../k8s/STATEFULSET.md)
- Lab 14 (Rollouts): [`docs/LAB14.md`](LAB14.md)
- Lab 12 (ConfigMaps & PVC base): [`docs/LAB12.md`](LAB12.md)
- Helm chart: [`k8s/devops-info-service/`](../k8s/devops-info-service/)
- Lecture notes: [`lectures/lec15.md`](../../lectures/lec15.md)
- [StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
- [Headless Services](https://kubernetes.io/docs/concepts/services-networking/service/#headless-services)
- [Volume claim templates](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/#volume-claim-templates)
- [StatefulSet update strategies](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/#update-strategies)
