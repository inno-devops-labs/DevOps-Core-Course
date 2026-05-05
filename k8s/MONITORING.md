# Lab 16 — Kubernetes Monitoring & Init Containers

## 1. Stack Components

| Component | Role |
|-----------|------|
| **Prometheus Operator** | Manages Prometheus/Alertmanager CRDs. Watches `ServiceMonitor`, `PrometheusRule`, and `Alertmanager` objects and configures Prometheus automatically. |
| **Prometheus** | Time-series metrics database. Scrapes `/metrics` from targets defined by ServiceMonitors. Stores data locally and serves PromQL queries. |
| **Alertmanager** | Routes and deduplicates alerts fired by Prometheus. Sends notifications to Slack, email, PagerDuty, etc. Groups related alerts and applies silence rules. |
| **Grafana** | Visualization layer. Connects to Prometheus as data source; provides pre-built Kubernetes dashboards for CPU, memory, network, and pod stats. |
| **kube-state-metrics** | Exposes Kubernetes object state (Deployments, Pods, Nodes) as Prometheus metrics. Answers "how many replicas are ready?" rather than resource usage. |
| **node-exporter** | DaemonSet on every node. Exposes Linux kernel metrics: CPU, RAM, disk I/O, network, filesystem. Powers the Node Exporter dashboard in Grafana. |

### Installation

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.adminPassword=admin123 \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false
```

See [`monitoring/evidence/01-monitoring-stack.txt`](./monitoring/evidence/01-monitoring-stack.txt).

---

## 2. Installation Evidence

```
kubectl get po,svc -n monitoring
```

```
NAME                                                         READY   STATUS    RESTARTS
pod/alertmanager-monitoring-kube-prometheus-alertmanager-0   2/2     Running   0
pod/monitoring-grafana-6f988469b4-mr6h6                      3/3     Running   0
pod/monitoring-kube-prometheus-operator-54f68d65b4-hv6j5     1/1     Running   0
pod/monitoring-kube-state-metrics-5957bd45bc-zvtr7           1/1     Running   0
pod/monitoring-prometheus-node-exporter-nsskz                1/1     Running   0
pod/prometheus-monitoring-kube-prometheus-prometheus-0       2/2     Running   0

NAME                                              TYPE        CLUSTER-IP
service/monitoring-grafana                        ClusterIP   10.98.88.82
service/monitoring-kube-prometheus-alertmanager   ClusterIP   10.101.145.112
service/monitoring-kube-prometheus-prometheus     ClusterIP   10.103.143.145
service/monitoring-prometheus-node-exporter       ClusterIP   10.98.234.13
```

### Access

```bash
# Grafana
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
# Open http://localhost:3000, login: admin / admin123

# Prometheus
kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090

# Alertmanager
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093
```

---

## 3. Grafana Dashboard Exploration

### Q1: Pod Resources — StatefulSet CPU/Memory

**Dashboard:** `Kubernetes / Compute Resources / Namespace (Pods)` → namespace: `stateful-test`

Pods `devops-info-sts-0/1/2` each consume ~2-5 mCPU at idle. Memory ~35 MB RSS per pod.

### Q2: Namespace CPU Analysis — default namespace

**Dashboard:** `Kubernetes / Compute Resources / Namespace (Pods)` → namespace: `default`

- Most CPU: `devops-info` (3 replicas handling probe traffic)
- Least CPU: `init-download-demo` (sleeping, ~0 mCPU)

### Q3: Node Metrics

**Dashboard:** `Node Exporter / Nodes`

- Memory: ~2.1 GB used / 7.8 GB total (~27%)
- CPU: 1 core actively used (minikube single-node)

### Q4: Kubelet — Pods/Containers Managed

**Dashboard:** `Kubernetes / Kubelet`

- Pods managed: ~25
- Containers: ~40

### Q5: Network Traffic

**Dashboard:** `Kubernetes / Networking / Namespace (Pods)` → namespace: `default`

- Inbound: mainly kubelet probe traffic to `devops-info` pods (~1 KB/s)
- Outbound: minimal (JSON responses to probes)

### Q6: Alertmanager — Active Alerts

**Alertmanager UI** (`http://localhost:9093`):

- `Watchdog` alert active (always-on sentinel to confirm alerting pipeline works)
- No critical alerts

---

## 4. Init Containers

### Pattern 1: File Download

`k8s/init-containers/init-download.yaml` — downloads `https://example.com` into a shared `emptyDir` volume before the main container starts.

```
Init container output:
  Downloading example page...
  Download complete. File size: 528 bytes

Main container accessed the file:
  1 /data/index.html
  <!doctype html><html lang="en">...
```

Pod lifecycle: `Init:0/1` → `PodInitializing` → `Running`

See [`monitoring/evidence/02-init-containers.txt`](./monitoring/evidence/02-init-containers.txt).

### Pattern 2: Wait-for-Service

`k8s/init-containers/wait-for-service.yaml` — polls DNS for `devops-info.default.svc.cluster.local` every 2 s. Main container only starts after the service exists.

```
Waiting for devops-info service to be resolvable...
Service not ready yet, retrying in 2s...
...
Name: devops-info.default.svc.cluster.local
Address: 10.105.92.189
Service is ready! Starting main app.
```

**Verification:**
```bash
# Start demo pod before devops-info service exists
kubectl apply -f k8s/init-containers/wait-for-service.yaml
kubectl get pod wait-for-service-demo  # → Init:0/1

# Deploy the dependency
helm install devops-info k8s/helm/devops-info ...

# Pod automatically transitions to Running
kubectl get pod wait-for-service-demo  # → Running
```

---

## 5. Bonus — Custom Metrics & ServiceMonitor

### `/metrics` Endpoint

Added `prometheus-flask-exporter` to `app_python/app.py`:

```python
from prometheus_flask_exporter import PrometheusMetrics
metrics = PrometheusMetrics(app)
```

This auto-exposes `/metrics` with:
- `flask_http_request_total{method, path, status}` — request counter
- `flask_http_request_duration_seconds` — latency histogram
- Standard Python process metrics (CPU, memory, GC)

Example:
```
flask_http_request_duration_seconds_bucket{le="0.005",method="GET",path="/health",status="200"} 15.0
```

See [`monitoring/evidence/03-metrics.txt`](./monitoring/evidence/03-metrics.txt).

### ServiceMonitor

`templates/servicemonitor.yaml`:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: devops-info
  labels:
    release: monitoring
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: devops-info
  endpoints:
    - port: http
      path: /metrics
      interval: 15s
```

Enabled with `--set serviceMonitor.enabled=true`. Prometheus Operator watches this CRD and automatically adds the scrape target.

See [`monitoring/evidence/04-servicemonitor.txt`](./monitoring/evidence/04-servicemonitor.txt).
