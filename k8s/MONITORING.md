# Lab 16 - Kubernetes Monitoring and Init Containers

This document describes the monitoring setup for the Kubernetes labs and the
init container implementation in `devops-info-chart`.

Cluster used for verification:

- context: `docker-desktop`
- monitoring namespace: `monitoring`
- application namespace: `lab15`
- application release: `devops-info`
- application image: `vladimirzhidkov/devops-info-service:lab15`

## 1. Stack Components

| Component | Role |
| --- | --- |
| Prometheus Operator | Reconciles Prometheus, Alertmanager, ServiceMonitor, and rule CRDs. |
| Prometheus | Stores and queries time-series metrics scraped from Kubernetes and apps. |
| Alertmanager | Receives firing alerts from Prometheus and routes/deduplicates them. |
| Grafana | Visualizes metrics with dashboards. |
| kube-state-metrics | Exposes Kubernetes object state such as pods, PVCs, and StatefulSets. |
| node-exporter | Exposes node CPU, memory, filesystem, and network metrics. |

## 2. Installation

The stack was installed with Helm:

```powershell
$helmRoot = Join-Path $env:TEMP 'helm-cache-lab16'
$env:HELM_REPOSITORY_CONFIG = Join-Path $helmRoot 'repositories.yaml'
$env:HELM_REPOSITORY_CACHE = Join-Path $helmRoot 'cache'

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts --force-update
helm repo update prometheus-community

helm upgrade --install monitoring prometheus-community/kube-prometheus-stack `
  --namespace monitoring `
  --create-namespace `
  --kube-context docker-desktop `
  --set grafana.adminPassword=prom-operator `
  --set prometheus-node-exporter.hostRootFsMount.enabled=false `
  --wait `
  --timeout 300s
```

The `prometheus-node-exporter.hostRootFsMount.enabled=false` override is needed
on Docker Desktop because root mount propagation is not available there.

Actual pods:

```text
alertmanager-monitoring-kube-prometheus-alertmanager-0   2/2   Running
monitoring-grafana-79f98585fc-c8mns                      3/3   Running
monitoring-kube-prometheus-operator-679597dd8f-9dqmr     1/1   Running
monitoring-kube-state-metrics-8554644d7b-9m5jz           1/1   Running
monitoring-prometheus-node-exporter-v22w6                1/1   Running
prometheus-monitoring-kube-prometheus-prometheus-0       2/2   Running
```

Actual services:

```text
monitoring-grafana                        ClusterIP   10.104.152.228   80/TCP
monitoring-kube-prometheus-alertmanager   ClusterIP   10.100.68.247    9093/TCP,8080/TCP
monitoring-kube-prometheus-prometheus     ClusterIP   10.98.101.84     9090/TCP,8080/TCP
monitoring-kube-state-metrics             ClusterIP   10.107.94.163    8080/TCP
monitoring-prometheus-node-exporter       ClusterIP   10.98.163.155    9100/TCP
```

Access commands:

```powershell
kubectl --context docker-desktop port-forward svc/monitoring-grafana -n monitoring 3000:80
kubectl --context docker-desktop port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090
kubectl --context docker-desktop port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093
```

Grafana login:

- username: `admin`
- password: `prom-operator`

## 3. Application Monitoring

The application already exposes `/metrics` through `prometheus-client`.
`values-monitoring.yaml` enables the chart's `ServiceMonitor`:

```powershell
helm upgrade devops-info k8s/devops-info-chart `
  -n lab15 `
  --kube-context docker-desktop `
  -f k8s/devops-info-chart/values-statefulset.yaml `
  -f k8s/devops-info-chart/values-monitoring.yaml `
  --set service.type=ClusterIP `
  --set image.tag=lab15 `
  --set image.pullPolicy=Always `
  --wait `
  --timeout 240s
```

ServiceMonitor verification:

```text
lab15   devops-info-devops-info-chart   2m7s
```

Prometheus target verification:

```text
up{namespace="lab15", service="devops-info-devops-info-chart", pod="devops-info-devops-info-chart-0"} => 1
up{namespace="lab15", service="devops-info-devops-info-chart", pod="devops-info-devops-info-chart-1"} => 1
up{namespace="lab15", service="devops-info-devops-info-chart", pod="devops-info-devops-info-chart-2"} => 1
```

Custom metrics query:

```promql
devops_info_endpoint_calls_total{namespace="lab15"}
```

Actual result:

```text
pod devops-info-devops-info-chart-0 endpoint="/health" => 115
pod devops-info-devops-info-chart-1 endpoint="/health" => 118
pod devops-info-devops-info-chart-2 endpoint="/health" => 124
pod devops-info-devops-info-chart-0 endpoint="/"       => 1
```

## 4. Dashboard Answers

The same information is visible in Grafana dashboards such as
`Kubernetes / Compute Resources / Namespace (Pods)`, `Node Exporter / Nodes`,
and `Kubernetes / Kubelet`. The values below were captured from Prometheus.

### 1. Pod Resources for StatefulSet

CPU usage:

```promql
sum by (pod) (
  rate(container_cpu_usage_seconds_total{namespace="lab15",pod=~"devops-info.*"}[1m])
)
```

Actual result:

```text
devops-info-devops-info-chart-0 => 0.001883 cores
devops-info-devops-info-chart-1 => 0.002390 cores
devops-info-devops-info-chart-2 => 0.001741 cores
```

Memory working set:

```promql
sum by (pod) (
  container_memory_working_set_bytes{namespace="lab15",pod=~"devops-info.*"}
)
```

Actual result:

```text
devops-info-devops-info-chart-0 => 40,759,296 bytes (~38.9 MiB)
devops-info-devops-info-chart-1 => 40,611,840 bytes (~38.7 MiB)
devops-info-devops-info-chart-2 => 44,814,336 bytes (~42.7 MiB)
```

### 2. Default Namespace CPU

Query:

```promql
topk(5, sum by (pod) (rate(container_cpu_usage_seconds_total{namespace="default"}[1m])))
bottomk(5, sum by (pod) (rate(container_cpu_usage_seconds_total{namespace="default"}[1m])))
```

Actual result:

```text
Most CPU:
devops-info-devops-info-chart-f78997555-4dk94 => 0.002134 cores
devops-info-devops-info-chart-f78997555-j5zf5 => 0.002040 cores
devops-info-devops-info-chart-f78997555-6chlp => 0.001747 cores

Least CPU:
devops-info-devops-info-chart-f78997555-6chlp => 0.001747 cores
devops-info-devops-info-chart-f78997555-j5zf5 => 0.002040 cores
devops-info-devops-info-chart-f78997555-4dk94 => 0.002134 cores
```

Only three application pods were running in the `default` namespace during the
query, so the top and bottom lists contain the same pods in opposite order.

### 3. Node Metrics

Queries:

```promql
node_memory_MemTotal_bytes
100 * (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)
count(count by (cpu) (node_cpu_seconds_total{mode="idle"}))
```

Actual result:

```text
Node memory total: 7,902,425,088 bytes (~7,536 MiB)
Node memory used: 67.80% (~5,110 MiB)
CPU cores: 16
```

### 4. Kubelet

Queries:

```promql
kubelet_running_pods
kubelet_running_containers
```

Actual result:

```text
Running pods: 34
Containers running: 38
Containers exited: 37
Containers created: 1
Containers unknown: 1
```

### 5. Network

Query:

```promql
sum by (pod) (
  rate(container_network_receive_bytes_total{namespace="default"}[1m])
  +
  rate(container_network_transmit_bytes_total{namespace="default"}[1m])
)
```

Actual result: no current per-pod network traffic sample was returned for the
`default` namespace at query time. This is expected for an idle namespace with
no active requests during the one-minute window.

### 6. Alerts

Query:

```promql
ALERTS{alertstate="firing"}
```

Actual result:

```text
Active firing alerts: 2
Watchdog severity=none
etcdInsufficientMembers severity=critical
```

`Watchdog` is expected in kube-prometheus-stack. The etcd alert is typical for
local Docker Desktop clusters where some control-plane scrape endpoints are not
exposed like a production cluster.

## 5. Init Containers

`values-monitoring.yaml` enables two init containers:

- `wait-for-service`: waits for `kubernetes.default.svc.cluster.local`
- `init-download`: downloads `http://example.com` into a shared `emptyDir`

The main app mounts the same `emptyDir` at `/init-data`.

Wait-for-service proof:

```text
Server:  10.96.0.10
Address: 10.96.0.10:53

Name: kubernetes.default.svc.cluster.local
Address: 10.96.0.1

kubernetes.default.svc.cluster.local is available
```

Download proof:

```text
Connecting to example.com (172.66.147.243:80)
saving to '/work-dir/index.html'
index.html 100% |********************************| 528
'/work-dir/index.html' saved
```

Main container proof:

```bash
kubectl --context docker-desktop exec -n lab15 devops-info-devops-info-chart-0 -- \
  sh -c "ls -l /init-data && head -n 3 /init-data/index.html"
```

Actual result:

```text
total 4
-rw-r--r-- 1 root root 528 May  3 21:27 index.html
<!doctype html><html lang="en"><head><title>Example Domain</title>...
```

## 6. Commands Reference

```powershell
kubectl --context docker-desktop get pods -n monitoring
kubectl --context docker-desktop get po,sts,svc,pvc,servicemonitor -n lab15
kubectl --context docker-desktop logs -n lab15 devops-info-devops-info-chart-0 -c wait-for-service
kubectl --context docker-desktop logs -n lab15 devops-info-devops-info-chart-0 -c init-download
kubectl --context docker-desktop exec -n monitoring prometheus-monitoring-kube-prometheus-prometheus-0 -c prometheus -- promtool query instant http://localhost:9090 up
```

## 7. Notes

The Prometheus chart repository cache was stored in a local temporary Helm
directory because the default Helm repository path under `AppData\Roaming` was
not writable from this session.
