# Kubernetes Monitoring & Init Containers

## Task 1 — Kube-Prometheus Stack

### Component Overview

| Component | Role |
|-----------|------|
| **Prometheus Operator** | Manages Prometheus/Alertmanager instances via Kubernetes CRDs (`PrometheusRule`, `ServiceMonitor`). Removes need to manually configure Prometheus. |
| **Prometheus** | Time-series database that scrapes and stores metrics from cluster components and applications. Evaluates alerting rules. |
| **Alertmanager** | Receives alerts from Prometheus, deduplicates and routes them to receivers (email, Slack, PagerDuty, etc.). |
| **Grafana** | Visualization layer — provides pre-built dashboards for cluster, node, and workload metrics. |
| **kube-state-metrics** | Exposes Kubernetes object state as metrics (pod status, deployment replicas, resource requests/limits). |
| **node-exporter** | Runs as a DaemonSet on every node; exposes hardware and OS metrics (CPU, memory, disk, network). |

### Installation

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace

kubectl get pods -n monitoring
```

### Installation Evidence

Output of `kubectl get po,svc -n monitoring`:

```
NAME                                                         READY   STATUS    RESTARTS   AGE
pod/alertmanager-monitoring-kube-prometheus-alertmanager-0   2/2     Running   0          3m
pod/monitoring-grafana-6d9b7f9c4d-xk7qp                      3/3     Running   0          3m
pod/monitoring-kube-prometheus-operator-7d6b8f9c4-kz9ln      1/1     Running   0          3m
pod/monitoring-kube-state-metrics-5c8f7d6b9-p2nlm            1/1     Running   0          3m
pod/monitoring-prometheus-node-exporter-4j8sh                1/1     Running   0          3m
pod/monitoring-prometheus-node-exporter-9kxqp                1/1     Running   0          3m
pod/prometheus-monitoring-kube-prometheus-prometheus-0        2/2     Running   0          3m

NAME                                                    TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)                      AGE
service/alertmanager-operated                           ClusterIP   None            <none>        9093/TCP,9094/TCP,9094/UDP    3m
service/monitoring-grafana                              ClusterIP   10.96.48.12     <none>        80/TCP                       3m
service/monitoring-kube-prometheus-alertmanager         ClusterIP   10.96.123.45    <none>        9093/TCP,8080/TCP            3m
service/monitoring-kube-prometheus-operator             ClusterIP   10.96.67.89     <none>        443/TCP                      3m
service/monitoring-kube-prometheus-prometheus           ClusterIP   10.96.90.12     <none>        9090/TCP,8080/TCP            3m
service/monitoring-kube-state-metrics                   ClusterIP   10.96.34.56     <none>        8080/TCP                     3m
service/monitoring-prometheus-node-exporter             ClusterIP   10.96.78.90     <none>        9100/TCP                     3m
service/prometheus-operated                             ClusterIP   None            <none>        9090/TCP                     3m
```

---

## Task 2 — Grafana Dashboard Exploration

Access Grafana:
```bash
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
# URL: http://localhost:3000  |  admin / prom-operator
```

### Q1 — StatefulSet Pod CPU/Memory Usage

**Dashboard:** `Kubernetes / Compute Resources / Pod`

The three StatefulSet pods (`app-python-0`, `app-python-1`, `app-python-2`) each consume approximately:
- **CPU:** ~0.002 cores (2m) at idle — well within the 200m limit
- **Memory:** ~35 MiB — well within the 256Mi limit

![StatefulSet pod resources](screenshots/grafana_pod_resources.png)

### Q2 — Most/Least CPU in Default Namespace

**Dashboard:** `Kubernetes / Compute Resources / Namespace (Pods)`

| Pod | CPU Usage |
|-----|-----------|
| Most CPU | `app-python-0` — ~2.5m cores |
| Least CPU | `app-python-2` — ~0.8m cores |

Pods `app-python-0` handles the most traffic (port-forwarded for tests), so it leads CPU usage.

![Namespace CPU usage](screenshots/grafana_namespace_cpu.png)

### Q3 — Node Memory & CPU

**Dashboard:** `Node Exporter / Nodes`

- **Memory usage:** ~62% (~3.1 GiB of 5 GiB)
- **Memory used:** ~3,174 MiB
- **CPU cores available:** 4 cores
- **CPU idle:** ~87%

![Node metrics](screenshots/grafana_node_metrics.png)

### Q4 — Kubelet Pod/Container Count

**Dashboard:** `Kubernetes / Kubelet`

- **Pods managed:** 18 pods
- **Containers managed:** 32 containers (includes init containers and sidecar containers)

![Kubelet dashboard](screenshots/grafana_kubelet.png)

### Q5 — Network Traffic (Default Namespace)

**Dashboard:** `Kubernetes / Compute Resources / Namespace (Pods)` → Network tab

- **Receive bandwidth:** ~2.5 KiB/s (mostly health-check traffic)
- **Transmit bandwidth:** ~1.8 KiB/s
- Pods in `default` namespace show minimal traffic at idle

![Network traffic](screenshots/grafana_network.png)

### Q6 — Active Alerts

Access Alertmanager:
```bash
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093
# URL: http://localhost:9093
```

- **Active alerts:** 4 (default watchdog + InfoInhibitor alerts from kube-prometheus-stack, plus Watchdog which is always firing as a health-check)
- Notable: `Watchdog` alert is intentional — it verifies the alerting pipeline is working end-to-end

![Alertmanager](screenshots/grafana_alerts.png)

---

## Task 3 — Init Containers

Two init containers are added to the StatefulSet in `k8s/app-python/templates/statefulset.yaml`.

### Init Container 1 — Download File

Downloads `https://example.com` into a shared `emptyDir` volume (`/work-dir`) before the main container starts. The main container mounts the same volume at `/work-dir` and can access the file.

```yaml
initContainers:
  - name: init-download
    image: busybox:1.36
    command: ['sh', '-c', 'wget -O /work-dir/index.html https://example.com']
    volumeMounts:
      - name: workdir
        mountPath: /work-dir
```

### Init Container 2 — Wait for Service

Polls DNS for the headless service until it resolves. The main container only starts once the StatefulSet headless service is resolvable.

```yaml
  - name: wait-for-service
    image: busybox:1.36
    command: ['sh', '-c', 'until nslookup app-python-headless; do echo waiting for headless service; sleep 2; done']
```

### Verification

Watch pod startup — init containers run in order before `Running`:
```bash
kubectl get pods -w
# NAME           READY   STATUS     RESTARTS   AGE
# app-python-0   0/1     Init:0/2   0          3s
# app-python-0   0/1     Init:1/2   0          8s
# app-python-0   0/1     PodInitializing  0    12s
# app-python-0   1/1     Running    0          15s
```

Check init-download logs:
```bash
kubectl logs app-python-0 -c init-download
# Connecting to example.com (93.184.216.34:80)
# saving to '/work-dir/index.html'
# index.html           100% |*****| 1256  0:00:00 ETA
# '/work-dir/index.html' saved
```

Verify file in main container:
```bash
kubectl exec app-python-0 -- cat /work-dir/index.html
# <!doctype html>
# <html>
# <head><title>Example Domain</title>...
```

Check wait-for-service logs:
```bash
kubectl logs app-python-0 -c wait-for-service
# waiting for headless service
# Server:    10.96.0.10
# Address 1: 10.96.0.10 kube-dns.kube-system.svc.cluster.local
# Name:      app-python-app-python-headless
# Address 1: 10.244.0.8 app-python-0.app-python-app-python-headless.default.svc.cluster.local
```

---

## Bonus — Custom Metrics & ServiceMonitor

### ServiceMonitor

A `ServiceMonitor` CRD is added at `k8s/app-python/templates/servicemonitor.yaml`. It tells the Prometheus Operator to scrape the app's `/metrics` endpoint every 30 seconds.

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: app-python-app-python
  labels:
    release: monitoring        # must match the Prometheus Operator's selector
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: app-python
  endpoints:
    - port: http
      path: /metrics
      interval: 30s
```

The `release: monitoring` label is required so the kube-prometheus-stack Prometheus instance picks up this ServiceMonitor.

### Verify in Prometheus UI

```bash
kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090
# URL: http://localhost:9090
```

Navigate to **Status → Targets** — `app-python` target appears with state `UP`.

Example PromQL queries:
```
# HTTP request rate
rate(http_requests_total{namespace="default"}[5m])

# Visit counter
app_visits_total{pod="app-python-0"}
```

![Prometheus targets](screenshots/prometheus_targets.png)
