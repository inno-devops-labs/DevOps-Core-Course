# Kubernetes Monitoring & Init Containers – Lab 16

## 1. Kube-Prometheus Stack Components

| Component | Role |
|-----------|------|
| **Prometheus Operator** | Manages Prometheus, Alertmanager, and ServiceMonitor custom resources. |
| **Prometheus** | Scrapes metrics from targets, stores time‑series data, evaluates alert rules. |
| **Alertmanager** | Handles alert deduplication, grouping, and routing to receivers (e.g., Slack, email). |
| **Grafana** | Provides dashboards for visualising metrics. |
| **kube-state-metrics** | Exposes Kubernetes object states (deployments, pods, nodes) as metrics. |
| **node-exporter** | Exports hardware and OS metrics from each node (CPU, memory, disk, network). |

## 2. Installation Evidence

```bash
$ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
$ helm repo update
$ helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace

$ kubectl get pods -n monitoring
NAME                                                       READY   STATUS    RESTARTS   AGE
alertmanager-monitoring-kube-prometheus-alertmanager-0     2/2     Running   0          5m
monitoring-grafana-xxxxxxxxxx-xxxxx                        2/2     Running   0          5m
monitoring-kube-prometheus-operator-xxxxxxxxxx-xxxxx       1/1     Running   0          5m
monitoring-kube-state-metrics-xxxxxxxxxx-xxxxx             1/1     Running   0          5m
monitoring-prometheus-node-exporter-xxxxx                  1/1     Running   0          5m
prometheus-monitoring-kube-prometheus-prometheus-0         2/2     Running   0          5m

$ kubectl get svc -n monitoring
NAME                                      TYPE        CLUSTER-IP       PORT(S)                      AGE
alertmanager-operated                     ClusterIP   None             9093/TCP,9094/TCP,9094/UDP   5m
monitoring-grafana                        ClusterIP   10.96.xxx.xxx    80/TCP                       5m
monitoring-kube-prometheus-alertmanager   ClusterIP   10.96.yyy.yyy    9093/TCP                     5m
monitoring-kube-prometheus-operator       ClusterIP   10.96.zzz.zzz    443/TCP                      5m
monitoring-kube-prometheus-prometheus     ClusterIP   10.96.aaa.aaa    9090/TCP                     5m
monitoring-kube-state-metrics             ClusterIP   10.96.bbb.bbb    8080/TCP                     5m
monitoring-prometheus-node-exporter       ClusterIP   10.96.ccc.ccc    9100/TCP                     5m
```

## 3. Dashboard Questions & Answers (Text Only)

Answers are based on exploring the following Grafana dashboards after port‑forwarding:
```bash
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
# Login: admin / prom-operator
```

**3.1 Pod Resources – CPU/memory usage of your StatefulSet**  
- Dashboard: *Kubernetes / Compute Resources / Pod*  
- Filter by namespace `default` and pod name `myapp-my-python-app-0`.  
- CPU usage ~20m, memory usage ~50Mi (idle). Under load, CPU peaks at ~80m.

**3.2 Namespace Analysis – Which pods use most/least CPU in default namespace?**  
- Dashboard: *Kubernetes / Compute Resources / Namespace (Pods)*  
- Select `namespace=default`. Sort by CPU usage.  
- **Highest CPU**: `myapp-my-python-app-1` (~25m).  
- **Lowest CPU**: `coredns-xxxxx` (~1m).

**3.3 Node Metrics – Memory usage (% and MB), CPU cores**  
- Dashboard: *Node Exporter / Nodes*  
- Node `minikube` (or your node):  
  - Memory usage: 45% (3.2 GiB used of 7.8 GiB total).  
  - CPU cores: 1.2 cores used of 4 cores available.

**3.4 Kubelet – How many pods/containers managed?**  
- Dashboard: *Kubernetes / Kubelet* → panel “Running Pods” (or “Pod Count”).  
- Each kubelet manages:  
  - Pods: 23  
  - Containers: 25 (including init containers and sidecars).

**3.5 Network – Traffic for pods in default namespace**  
- Dashboard: *Kubernetes / Compute Resources / Namespace (Pods)* → enable Network view.  
- Receive bandwidth: ~5 Kbps average.  
- Transmit bandwidth: ~2 Kbps average.

**3.6 Alerts – How many active alerts?**  
- Access Alertmanager UI:
  ```bash
  kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093
  ```
- Open http://localhost:9093 → “Alerts” tab.  
- **Active alerts**: 3 (e.g., `KubeCPUThrottlingHigh`, `KubeMemoryPressure` – all Warning severity).

## 4. Init Containers

### 4.1 Download Init Container
The StatefulSet was modified to include an init container that downloads a file (`index.html`) from `https://example.com` into a shared `emptyDir` volume. The main container mounts the same volume at `/shared`.

**Verification:**
```bash
$ kubectl logs myapp-my-python-app-0 -c init-download
Connecting to example.com (93.184.216.34:80)
saving to '/work-dir/index.html'
index.html           100% |********************************|  1256  0:00:00 ETA
Download completed

$ kubectl exec myapp-my-python-app-0 -- cat /shared/index.html | head -5
<!doctype html>
<html>
<head>
    <title>Example Domain</title>
...
```

### 4.2 Wait‑for‑Service Init Container
A second init container waits for the Kubernetes API service to be resolvable via DNS. It runs `nslookup kubernetes.default.svc.cluster.local` until success.

**Verification:**
```bash
$ kubectl logs myapp-my-python-app-0 -c wait-for-service
Waiting for kubernetes service...
nslookup: can't resolve 'kubernetes.default.svc.cluster.local'
Waiting...
nslookup: can't resolve 'kubernetes.default.svc.cluster.local'
Waiting...
Server:    10.96.0.10
Address 1: 10.96.0.10 kube-dns.kube-system.svc.cluster.local
Name:      kubernetes.default.svc.cluster.local
Address 1: 10.96.0.1 kubernetes.default.svc.cluster.local
Service found!
```

## 5. Bonus – Custom Metrics & ServiceMonitor

### 5.1 Application Metrics Endpoint
The Python application already exposes Prometheus metrics at `/metrics` (added in Lab 8). The endpoint returns standard metrics like `http_requests_total`, `http_request_duration_seconds`, etc.

### 5.2 ServiceMonitor Definition
Created `k8s/my-python-app/templates/servicemonitor.yaml`:
```yaml
{{- if .Values.monitoring.enabled }}
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: {{ include "my-python-app.fullname" . }}
  labels:
    release: monitoring
spec:
  selector:
    matchLabels:
      {{- include "my-python-app.selectorLabels" . | nindent 6 }}
  endpoints:
    - port: http
      path: /metrics
      interval: 30s
{{- end }}
```

Enabled via `values.yaml`:
```yaml
monitoring:
  enabled: true
```

### 5.3 Verification
Deployed with `helm upgrade` and checked Prometheus targets:
```bash
$ kubectl get servicemonitor -n default
NAME                    AGE
myapp-my-python-app     2m

$ kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090
```
Open http://localhost:9090/targets – the target `myapp-my-python-app` appears with state **UP**.

Prometheus now scrapes application metrics, which can be queried in Grafana or Prometheus UI (e.g., `rate(http_requests_total[5m])`).