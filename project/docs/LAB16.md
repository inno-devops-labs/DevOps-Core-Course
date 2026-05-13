# Lab 16 — Kubernetes Monitoring & Init Containers

This document covers the monitoring and init-container extensions of the `devops-info-service` Helm chart. The full operator runbook (install, demos, evidence, troubleshooting) lives in **[`k8s/MONITORING.md`](../k8s/MONITORING.md)**; this report summarises decisions and points to the evidence.

Course lab spec: [`labs/lab16.md`](../../labs/lab16.md) (repository root).

---

## Objectives

- Install **kube-prometheus-stack** (Prometheus Operator + Prometheus + Alertmanager + Grafana + kube-state-metrics + node-exporter) and document each component's role.
- Answer six concrete questions about cluster and workload state — using the PromQL behind the Grafana panels.
- Implement two init-container patterns on the existing chart: **download to shared volume** and **wait for a dependency service**.
- (Bonus) Expose the app's `/metrics` (already done — `prometheus_client` in the FastAPI app) and add a chart-managed **ServiceMonitor** so Prometheus discovers and scrapes it.

---

## Chart changes

```
k8s/devops-info-service/
├── values.yaml                          # +initContainers.* and +monitoring.serviceMonitor.* blocks
└── templates/
    ├── _helpers.tpl                     # +3 helpers (initContainers / initContainerVolumes / initContainerVolumeMounts)
    ├── deployment.yaml                  # 3 splices: initContainers + workdir volume + workdir mount
    ├── rollout.yaml                     # same 3 splices
    ├── statefulset.yaml                 # same 3 splices
    └── servicemonitor.yaml              # NEW — monitoring.coreos.com/v1 ServiceMonitor (bonus)
```

### Key design decisions

| Decision | Reason |
|----------|--------|
| Init containers expressed as named-template **helpers** in `_helpers.tpl`, included by each workload | Three workload templates (`deployment`, `rollout`, `statefulset`) share the same pod spec shape. Defining init logic once in `_helpers.tpl` and including it from each template avoids three drifting copies. |
| Two independently-gated init patterns (`initContainers.download.enabled`, `initContainers.waitForService.enabled`) | The lab demands two demos; making them independently toggleable lets each demo show its pattern in isolation (rather than always running both). |
| `initContainers.enabled` master switch | Off by default. Lab 12–15 install paths render byte-identical YAML; no surprise behavior. |
| `workdir` volume only renders when `download.enabled=true` | `wait-for-service` doesn't need shared storage; declaring an unused `emptyDir` would be noise. |
| `monitoring.serviceMonitor.releaseLabel` defaults to `monitoring` | kube-prometheus-stack's Prometheus selects ServiceMonitors by `release: <install-name>`. The default chart install is named `monitoring`, so this works out of the box. |
| kube-prometheus-stack installed as a **separate** Helm release in the `monitoring` namespace, not as a chart dependency | The stack is cluster-wide infrastructure shared by every app. Bundling it into the app chart would couple lifecycles incorrectly and bloat installs. |

---

## Kube-Prometheus Stack (Task 1)

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace --wait --timeout 5m
```

Six workloads come up: prometheus-operator, prometheus-0, alertmanager-0, grafana, kube-state-metrics, node-exporter (DaemonSet). All nine default scrape targets (apiserver, coredns, kubelet, kube-state-metrics, the four self-monitoring jobs, node-exporter) report `up`.

See runbook §1 for component descriptions in own words, §2 for the install output, and §3 for resource & target evidence.

---

## Grafana Dashboard Exploration (Task 2)

Each lab question answered via the PromQL the Grafana panel runs. Full JSON output in runbook §4.

| # | Question | Answer (this cluster) |
|---|---|---|
| 1 | CPU/memory of our 3 StatefulSet pods | All three at **~0.0043 cores** CPU, **~47 MiB** working-set memory each |
| 2 | Top/bottom CPU pods in `default` ns | All three lab15 pods — `default` ns has no other pods, so top-3 = bottom-3 |
| 3 | Node: memory %, memory used, CPU cores | **22.5 %** memory used, **3 605.8 MiB**, **12 cores** |
| 4 | Kubelet running pods / containers | **24 pods**, **28 running containers** (+3 created, +4 exited) |
| 5 | Network traffic | **RX 56 KB/s, TX 123 KB/s** node-level (per-pod `container_network_*` not exported on this cgroup-v2 cluster — see runbook §4 note) |
| 6 | Active firing alerts | **1** — `Watchdog`, severity=none (kube-prometheus-stack's always-firing canary) |

---

## Init Containers (Task 3)

Two patterns demonstrated on the Lab 15 StatefulSet via the new helpers:

- **`init-download`** — busybox `wget` fetches a file into an `emptyDir` mounted at `/work-dir`; the main container reads the file at the same path. Demo: downloads `k8s.io/kubernetes/master/README.md` (4387 bytes), `kubectl logs ... -c init-download` shows the transfer, `kubectl exec ... -- head /work-dir/index.html` shows the main container reading it.
- **`init-wait-for-service`** — busybox `nc -z <svc> <port>` loops with `sleep 2` and a `timeoutSeconds` deadline. Demo recorded in two halves: pointed at `notyet.default.svc.cluster.local:80` the pod is stuck on `Init:0/1` for 3+ minutes with the retry loop visible in logs; re-pointed at `monitoring-kube-prometheus-prometheus.monitoring.svc:9090` (real service), the init exits `Completed` (exit 0) and the pod transitions to `Running` within 15 s.

See runbook §5 (download) and §6 (wait-for-service).

---

## Bonus — Custom Metrics & ServiceMonitor (2.5 pts)

App-side: `/metrics` endpoint already wired in [`app_python/app/app.py:167`](../app_python/app/app.py#L167) using `prometheus_client`. Metrics exposed: `http_requests_total{method,endpoint,status}`, `http_request_duration_seconds`, `http_requests_in_progress`, `devops_info_endpoint_calls{endpoint}`, `devops_info_system_collection_seconds`.

Chart-side: new [`templates/servicemonitor.yaml`](../k8s/devops-info-service/templates/servicemonitor.yaml) — `ServiceMonitor` CRD with `release: monitoring` label and port `http` / path `/metrics` selector. Renders only when `monitoring.serviceMonitor.enabled=true`.

Evidence (runbook §7): three pod scrape endpoints `up` in Prometheus, `sum(http_requests_total{status="200"})` = 107 across all pods, `devops_info_endpoint_calls_total` breaks down by `/` (10) and `/health` (97).

---

## Task mapping

| Lab task | Points | Manifests / commands |
|----------|--------|----------------------|
| Kube-Prometheus stack | 2 pts | `helm install monitoring prometheus-community/kube-prometheus-stack` — runbook §1–§3 |
| Grafana dashboard exploration | 3 pts | Six PromQL queries against Prometheus HTTP API — runbook §4 |
| Init containers | 3 pts | `_helpers.tpl` init helpers, `initContainers.*` values, splices into Deployment/Rollout/StatefulSet — runbook §5, §6 |
| Documentation | 2 pts | this report + [`k8s/MONITORING.md`](../k8s/MONITORING.md) |
| Bonus — custom metrics & ServiceMonitor | 2.5 pts | `templates/servicemonitor.yaml`, `/metrics` already in app — runbook §7 |

---

## Local verification (no cluster)

```bash
cd project/k8s/devops-info-service

helm lint .
helm lint . --set initContainers.enabled=true
helm lint . --set statefulset.enabled=true,initContainers.enabled=true
helm lint . --set monitoring.serviceMonitor.enabled=true

helm template t .                                                              | grep -c 'kind: ServiceMonitor'    # → 0
helm template t . --set monitoring.serviceMonitor.enabled=true                 | grep -c 'kind: ServiceMonitor'    # → 1
helm template t . --set initContainers.enabled=true                            | grep -c 'name: init-download'     # → 1
helm template t . --set initContainers.enabled=true                            | grep -c 'name: init-wait-for-service' # → 1
helm template t .                                                              | grep -c '^      initContainers:'  # → 0
helm template t . --set statefulset.enabled=true,initContainers.enabled=true   | grep -c '^      initContainers:'  # → 1
helm template t . --set initContainers.enabled=true,initContainers.download.enabled=false | grep -c 'name: workdir' # → 0
```

All seven assertions pass on `feat/lab15`.

---

## Further reading

- Operator runbook: [`k8s/MONITORING.md`](../k8s/MONITORING.md)
- Lab 15 (StatefulSet base): [`docs/LAB15.md`](LAB15.md)
- Helm chart: [`k8s/devops-info-service/`](../k8s/devops-info-service/)
- Lecture notes: [`lectures/lec16.md`](../../lectures/lec16.md)
- [kube-prometheus-stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
- [Prometheus](https://prometheus.io/docs/)
- [Grafana](https://grafana.com/docs/)
- [Init Containers](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/)
- [ServiceMonitor (Prometheus Operator)](https://prometheus-operator.dev/docs/user-guides/getting-started/)
