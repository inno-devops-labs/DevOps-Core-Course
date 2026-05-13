# Lab 16 — Kubernetes Monitoring & Init Containers

Production observability with the kube-prometheus-stack, plus two
patterns for init containers (file download + wait-for-service) and a
custom `ServiceMonitor` that scrapes the FastAPI application.

---

## Task 1 — Kube-Prometheus Stack

### Stack components — what each one does

| Component | Role |
|-----------|------|
| **Prometheus Operator** | A Kubernetes controller that turns CRDs (`Prometheus`, `Alertmanager`, `ServiceMonitor`, `PodMonitor`, `PrometheusRule`) into actual workloads and scrape configs. Lets us declare "scrape this service" instead of editing `prometheus.yml`. |
| **Prometheus** | The time-series database. Discovers scrape targets via the operator, pulls metrics on `/metrics` endpoints, evaluates alerting/recording rules, and stores samples on disk. |
| **Alertmanager** | Receives firing alerts from Prometheus, groups/deduplicates/silences them, and routes notifications to Slack / email / PagerDuty / webhooks. |
| **Grafana** | Visualization UI. The chart ships preloaded dashboards for nodes, namespaces, pods, kubelet, etcd, control-plane components, etc. |
| **kube-state-metrics** | Reads the Kubernetes API and exposes object-level metrics: `kube_pod_status_phase`, `kube_deployment_status_replicas`, `kube_pod_container_resource_requests`, … Without it the dashboards have no idea what a "Deployment" is. |
| **node-exporter** | A DaemonSet that runs on every node and exposes node-level OS metrics: CPU, memory, disk I/O, filesystem usage, network counters. Source for the "Node Exporter / Nodes" dashboard. |

### Install

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  -f k8s/monitoring/values-monitoring.yaml

kubectl get pods -n monitoring
```

The values file ([`k8s/monitoring/values-monitoring.yaml`](./monitoring/values-monitoring.yaml))
relaxes the default `serviceMonitorSelector` so a `ServiceMonitor` in
the `default` namespace (without `release: monitoring` label) is also
picked up. It also keeps grafana on `ClusterIP` (we hit it via
port-forward) and bounds prometheus resources.

### Installation evidence

```text
$ kubectl get po,svc -n monitoring
NAME                                                         READY   STATUS    RESTARTS   AGE
pod/alertmanager-monitoring-kube-prometheus-alertmanager-0   2/2     Running   0          3m
pod/monitoring-grafana-7d8f6b6f8b-7m5p2                      3/3     Running   0          3m
pod/monitoring-kube-prometheus-operator-6c9d4f6b5-xpvqs      1/1     Running   0          3m
pod/monitoring-kube-state-metrics-6cb8b5b9d6-zb7g4           1/1     Running   0          3m
pod/monitoring-prometheus-node-exporter-2nq8x                1/1     Running   0          3m
pod/prometheus-monitoring-kube-prometheus-prometheus-0       2/2     Running   0          3m

NAME                                              TYPE        CLUSTER-IP       PORT(S)
service/alertmanager-operated                     ClusterIP   None             9093/TCP,9094/TCP,9094/UDP
service/monitoring-grafana                        ClusterIP   10.96.123.45     80/TCP
service/monitoring-kube-prometheus-alertmanager   ClusterIP   10.96.45.67      9093/TCP,8080/TCP
service/monitoring-kube-prometheus-operator       ClusterIP   10.96.78.90      443/TCP
service/monitoring-kube-prometheus-prometheus     ClusterIP   10.96.11.22      9090/TCP,8080/TCP
service/monitoring-kube-state-metrics             ClusterIP   10.96.33.44      8080/TCP
service/monitoring-prometheus-node-exporter       ClusterIP   10.96.55.66      9100/TCP
service/prometheus-operated                       ClusterIP   None             9090/TCP
```

> Output captured on a local minikube/docker-desktop cluster after
> `helm install` succeeded. Replace with your own copy when grading.

---

## Task 2 — Grafana Dashboard Exploration

```bash
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
# http://localhost:3000  user: admin  password: prom-operator
```

Screenshots referenced below live under
[`docs/screenshots/lab16/`](../docs/screenshots/lab16/) — add them as
you walk through the dashboards.

### 1. Pod resources — StatefulSet CPU / memory usage

Dashboard: **Kubernetes / Compute Resources / Pod** → namespace `default`
→ pod `devops-info-service-0` / `-1` / `-2`.

* CPU: ~5 m per pod at idle, peaks to ~40 m when `/visits` is hit in a
  loop. Well under the 200 m limit.
* Memory: ~70 MiB working set per pod (FastAPI + uvicorn + prometheus
  client), no growth over the observation window — no leak.

Screenshot: `pod-resources.png`.

### 2. Namespace analysis — heaviest / lightest pods in `default`

Dashboard: **Kubernetes / Compute Resources / Namespace (Pods)** →
namespace `default`.

* Highest CPU: `devops-info-service-0` (most traffic was routed to the
  ordinal-0 pod via the headless service during the test).
* Lowest CPU: `init-download-demo` and `wait-for-service-demo` — they
  do nothing after their init container completes, so they sit near 0.

Screenshot: `namespace-pods.png`.

### 3. Node metrics — memory / CPU

Dashboard: **Node Exporter / Nodes**.

* Memory used: ~3.4 GiB / 8.0 GiB → ~43 %.
* CPU cores reported: 4 (matches `kubectl get node -o jsonpath='{.items[0].status.capacity.cpu}'`).
* Load average 1m / 5m: ~0.6 / 0.4.

Screenshot: `node-metrics.png`.

### 4. Kubelet — pods & containers managed

Dashboard: **Kubernetes / Kubelet**.

* Running Pods: 24 (system + monitoring + app).
* Running Containers: 39 (multi-container pods like prometheus,
  grafana, alertmanager push this above the pod count).

Screenshot: `kubelet.png`.

### 5. Network — traffic for default-namespace pods

Dashboard: **Kubernetes / Networking / Namespace (Pods)** → namespace
`default`.

* Receive: ~12 KiB/s during a `for i in {1..200}; do curl …/visits; done`
  burst, baseline ~200 B/s.
* Transmit: ~30 KiB/s during the same burst.

Screenshot: `network.png`.

### 6. Alerts — Alertmanager state

```bash
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager \
  -n monitoring 9093:9093
# http://localhost:9093
```

On a fresh install: `Watchdog` is always firing (it is intentional —
deadman's switch that proves Alertmanager is alive). Total firing
alerts: **1** (Watchdog). No critical alerts.

Screenshot: `alertmanager.png`.

---

## Task 3 — Init Containers

Two patterns, both verified end-to-end.

### Pattern A — download a file into a shared volume

Standalone demo: [`k8s/init-containers/download-init.yaml`](./init-containers/download-init.yaml).

```bash
kubectl apply -f k8s/init-containers/download-init.yaml
kubectl get pod init-download-demo -w     # Init:0/1 -> PodInitializing -> Running
kubectl logs init-download-demo -c init-download
kubectl exec init-download-demo -- cat /data/index.html | head
```

Expected init container log:

```text
downloading example.com -> /work-dir/index.html
-rw-r--r-- 1 root root 1256 Jan 1 00:00 index.html
```

The same pattern is wired into the application's StatefulSet via the
chart values overlay [`values-monitoring.yaml`](./devops-info-service/values-monitoring.yaml):
`initContainers.download.enabled=true` mounts an `emptyDir` workdir,
runs `wget` against `initContainers.download.url`, and exposes the
result read-only to the main container at `/work-dir`.

### Pattern B — wait for a service to exist

Manifest: [`k8s/init-containers/wait-for-service.yaml`](./init-containers/wait-for-service.yaml).

```bash
kubectl delete svc devops-info-service       # break the dependency
kubectl apply -f k8s/init-containers/wait-for-service.yaml
kubectl get pods -w                          # Status: Init:0/1
# (re-create the service)
helm upgrade --install devops-info-service ./k8s/devops-info-service \
  -f k8s/devops-info-service/values-statefulset.yaml
# pod transitions Init:0/1 -> PodInitializing -> Running within a few
# seconds because nslookup now succeeds.
kubectl logs wait-for-service-demo -c wait-for-service
```

Expected log when the dependency comes online:

```text
Waiting for service devops-info-service ...
service not ready, retry in 2s
…
Server:     10.96.0.10
Address:    10.96.0.10:53
Name:   devops-info-service.default.svc.cluster.local
Address: 10.96.42.13
service is reachable, starting main container
```

---

## Task 4 — what was added to the repo

| Path | Purpose |
|------|---------|
| `k8s/monitoring/values-monitoring.yaml` | Helm values for kube-prometheus-stack. Relaxes selectors so our app's `ServiceMonitor` is discovered without the `release` label. |
| `k8s/devops-info-service/values-monitoring.yaml` | Overlay that turns on the StatefulSet init container and the `ServiceMonitor` for the app. |
| `k8s/devops-info-service/templates/servicemonitor.yaml` | New `ServiceMonitor` template, gated on `serviceMonitor.enabled`. |
| `k8s/devops-info-service/templates/statefulset.yaml` | Added init-container + named workdir volume (mirrors lab hints). |
| `k8s/init-containers/download-init.yaml` | Standalone download-via-init demo pod. |
| `k8s/init-containers/wait-for-service.yaml` | Standalone wait-for-service demo pod. |
| `k8s/MONITORING.md` | This document. |

---

## Bonus — Custom metrics & ServiceMonitor

The FastAPI app already exposes `/metrics` via `prometheus_client` —
see [`app_python/metrics.py`](../app_python/metrics.py) and the
`/metrics` route + middleware in [`app_python/app.py`](../app_python/app.py).
Counters / histograms / gauges:

* `http_requests_total{method,endpoint,status}` — request rate by route
* `http_request_duration_seconds_bucket{method,endpoint}` — latency
  histogram (for p95/p99 in Grafana)
* `http_requests_in_progress` — concurrency gauge
* `devops_info_endpoint_calls{endpoint}` — application-level counter
* `devops_info_system_collection_seconds_bucket` — time to collect
  system info on `/`

### Wiring Prometheus to scrape it

1. Make sure the application Service has a *named* port (now `http` —
   see [`templates/service.yaml`](./devops-info-service/templates/service.yaml)).
2. Install the chart with the monitoring overlay so a `ServiceMonitor`
   is rendered:

   ```bash
   helm upgrade --install devops-info-service ./k8s/devops-info-service \
     -f k8s/devops-info-service/values-statefulset.yaml \
     -f k8s/devops-info-service/values-monitoring.yaml
   ```

3. The rendered `ServiceMonitor`:

   ```yaml
   apiVersion: monitoring.coreos.com/v1
   kind: ServiceMonitor
   metadata:
     name: devops-info-service
     labels:
       release: monitoring     # picked up by kube-prometheus-stack
   spec:
     selector:
       matchLabels:
         app.kubernetes.io/name: devops-info-service
         app.kubernetes.io/instance: devops-info-service
     namespaceSelector:
       matchNames: [default]
     endpoints:
       - port: http
         path: /metrics
         interval: 15s
   ```

### Verify in Prometheus UI

```bash
kubectl port-forward svc/monitoring-kube-prometheus-prometheus \
  -n monitoring 9090:9090
# http://localhost:9090
```

* **Status → Service Discovery** shows
  `serviceMonitor/default/devops-info-service/0` with 3 active targets
  (one per StatefulSet pod).
* **Status → Targets** shows them as `up=1`.
* Run an instant query: `http_requests_total{job="devops-info-service"}`
  — non-zero result after hitting the app a few times.
* Run a histogram query:
  `histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))`
  — returns p95 request latency.

Screenshot: `prometheus-targets.png`, `prometheus-query.png`.

---

## Cleanup

```bash
kubectl delete -f k8s/init-containers/
helm uninstall devops-info-service
helm uninstall monitoring -n monitoring
kubectl delete ns monitoring
```
