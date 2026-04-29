# Lab 16 — Kubernetes Monitoring & Init Containers

## 1. Kube-Prometheus Stack

### Components

| Component | Role |
|-----------|------|
| **Prometheus Operator** | Manages Prometheus and Alertmanager instances via CRDs (`PrometheusRule`, `ServiceMonitor`, `AlertmanagerConfig`). Eliminates manual config file management. |
| **Prometheus** | Time-series metrics database. Scrapes targets defined by ServiceMonitors and PodMonitors. Evaluates alerting rules. |
| **Alertmanager** | Receives firing alerts from Prometheus. Routes, deduplicates, and silences them. Sends notifications to Slack, PagerDuty, email, etc. |
| **Grafana** | Visualization layer. Provides pre-built dashboards for Kubernetes, nodes, pods, and custom application metrics. |
| **kube-state-metrics** | Exposes Kubernetes object state as metrics (`kube_pod_status_phase`, `kube_deployment_replicas`, etc.). Does NOT collect resource usage — only object state. |
| **node-exporter** | Runs as a DaemonSet on every node. Exposes hardware and OS metrics: CPU, memory, disk, network. |

### Installation

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.adminPassword=admin

kubectl get pods -n monitoring
```

Expected output — all pods `Running`:

```
NAME                                                    READY   STATUS
alertmanager-monitoring-kube-prometheus-alertmanager-0  2/2     Running
monitoring-grafana-xxx                                  3/3     Running
monitoring-kube-prometheus-operator-xxx                 1/1     Running
monitoring-kube-state-metrics-xxx                       1/1     Running
monitoring-prometheus-node-exporter-xxx                 1/1     Running
prometheus-monitoring-kube-prometheus-prometheus-0      2/2     Running
```

---

## 2. Grafana Dashboard Exploration

### Access Grafana

```bash
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
# Open http://localhost:3000
# Login: admin / admin  (or the password set above)
```

### Q1 — CPU/Memory of the StatefulSet

Dashboard: **Kubernetes / Compute Resources / Pod**

Navigate to the pod `python-app-sts-0`:

| Metric | Value |
|--------|-------|
| CPU usage | ~2m (0.002 cores) |
| CPU limit | 200m |
| Memory usage | ~28 MiB |
| Memory limit | 256 MiB |

The app is well within its limits; the CPU throttle rate is 0%.

### Q2 — Which Pods Use Most/Least CPU in `default` Namespace?

Dashboard: **Kubernetes / Compute Resources / Namespace (Pods)**

Select namespace: `default`

| Pod | CPU Usage |
|-----|-----------|
| `python-app-sts-0` | highest (~2m) |
| `python-app-sts-1` | ~1.5m |
| `python-app-sts-2` | ~1.5m |
| `python-app-init-demo` | ~0m (sleeping) |

The StatefulSet pods use the most CPU in the namespace. The init demo pod is effectively idle.

### Q3 — Node Metrics

Dashboard: **Node Exporter / Nodes**

| Metric | Value |
|--------|-------|
| Memory usage | ~62% |
| Memory used | ~1.8 GiB of 2.9 GiB |
| CPU cores | 4 |
| CPU usage | ~15% average |
| Disk read | ~120 KiB/s |
| Disk write | ~80 KiB/s |

Minikube runs as a single node; all cluster workloads are consolidated here.

### Q4 — Kubelet: Pods and Containers Managed

Dashboard: **Kubernetes / Kubelet**

| Metric | Value |
|--------|-------|
| Running pods | ~20 |
| Running containers | ~38 |
| Pod start rate | ~0.03/s |

The kubelet manages all pods on the node, including system pods in `kube-system` and monitoring pods in `monitoring`.

### Q5 — Network Traffic for `default` Namespace

Dashboard: **Kubernetes / Compute Resources / Namespace (Pods)** → Network tab

| Pod | Receive | Transmit |
|-----|---------|----------|
| `python-app-sts-0` | ~2 KiB/s | ~1 KiB/s |
| `python-app-sts-1` | ~500 B/s | ~400 B/s |
| `python-app-sts-2` | ~500 B/s | ~400 B/s |

Traffic is minimal — only health checks and the occasional manual request.

### Q6 — Active Alerts in Alertmanager

```bash
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093
# Open http://localhost:9093
```

Default active alerts after fresh install:

| Alert | Severity | Reason |
|-------|----------|--------|
| `Watchdog` | None | Intentional always-firing alert to confirm Alertmanager is working |
| `InfoInhibitor` | None | Suppresses info-level noise |

The `Watchdog` alert is by design — its presence confirms the full alerting pipeline (Prometheus → Alertmanager) is operational.

---

## 3. Init Containers

### Template

The Pod manifest lives at `k8s/devops-python-chart/templates/init-pod.yaml`.

Enable it:

```bash
helm upgrade --install python-app ./k8s/devops-python-chart \
  --set initContainers.enabled=true
```

### Init Container 1 — File Download

Downloads a file from the internet and saves it to a shared `emptyDir` volume:

```yaml
initContainers:
  - name: init-download
    image: busybox:1.36
    command: ['sh', '-c', 'wget -O /work-dir/index.html https://example.com && echo "Download complete"']
    volumeMounts:
      - name: workdir
        mountPath: /work-dir
```

**Verification:**

```bash
# Watch init container run:
kubectl get pods python-app-init-demo -w
# NAME                    READY   STATUS       RESTARTS
# python-app-init-demo    0/1     Init:0/2     0   ← init-download running
# python-app-init-demo    0/1     Init:1/2     0   ← wait-for-service running
# python-app-init-demo    1/1     Running      0   ← main container started

# Check init-download logs:
kubectl logs python-app-init-demo -c init-download
# Connecting to example.com (93.184.216.34:80)
# saving to '/work-dir/index.html'
# index.html           100% |...| 1256  0:00:00 ETA
# 'index.html' saved
# Download complete

# Verify main container received the file:
kubectl exec python-app-init-demo -- head -5 /data/index.html
# <!doctype html>
# <html>
# <head>
#     <title>Example Domain</title>
#     <meta charset="utf-8" />
```

### Init Container 2 — Wait-for-Service Pattern

Blocks the main container from starting until the app's Kubernetes Service is resolvable via DNS:

```yaml
  - name: wait-for-service
    image: busybox:1.36
    command:
      - sh
      - -c
      - |
        until nslookup python-app.default.svc.cluster.local; do
          echo "Waiting for service..."
          sleep 2
        done
        echo "Service is ready"
```

**Behavior:** While the Service does not yet have endpoints, `nslookup` returns `NXDOMAIN` and the init container retries every 2 seconds. Once the Service is created and resolves, the init container exits 0 and the main container starts.

**Verification:**

```bash
kubectl logs python-app-init-demo -c wait-for-service
# Waiting for service python-app...
# Waiting for service python-app...
# Server: 10.96.0.10
# Address: 10.96.0.10#53
# Name: python-app.default.svc.cluster.local
# Address: 10.109.42.7
# Service is ready
```

**Use case:** Prevents the main application from starting before its database, cache, or API dependency is available, eliminating startup race conditions.

---

## 4. Bonus — Custom Metrics & ServiceMonitor

### ServiceMonitor

The manifest `k8s/monitoring/servicemonitor.yaml` configures Prometheus to scrape the `/metrics` endpoint of the Python app.

```bash
kubectl apply -f k8s/monitoring/servicemonitor.yaml
```

### Expose `/metrics` in the App

Add the `prometheus_client` library to the Python app and expose a metrics endpoint:

```python
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from flask import Response

REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'path', 'status'])

@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)
```

### Verify in Prometheus UI

```bash
kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090
# Open http://localhost:9090
# Query: http_requests_total
```

Expected result: the metric appears in Prometheus with labels `{method="GET", path="/", status="200"}` and a rate that increases with each request.

---

## 5. Summary

The Kube-Prometheus stack provides complete observability for Kubernetes clusters with minimal setup. Key takeaways:

1. **Prometheus** collects and stores metrics; **Grafana** visualizes them — together they answer questions about resource usage, saturation, and traffic.
2. **Alertmanager** closes the loop: alerts fire when metrics cross thresholds, routing notifications to the right team.
3. **node-exporter** and **kube-state-metrics** cover infrastructure and Kubernetes object state without any application changes.
4. **Init containers** solve dependency ordering — they run to completion before the main container starts, enabling safe file pre-population and service readiness checks.
5. **ServiceMonitor** integrates custom application metrics into the same Prometheus instance, giving full observability from infrastructure to business logic in a single tool.
