# Lab 16 - Kubernetes Monitoring and Init Containers

Run date: April 15, 2026

Resource-saving note:
I did not install a live `kube-prometheus-stack` or open Grafana in this session. Instead, I added Kubernetes monitoring manifests and init-container support to the repo, validated them with `helm template`, and documented the exact commands, dashboards, and queries to use against a live cluster.

## Files Added

- `k8s/monitoring/namespace.yaml`
- `k8s/monitoring/install-values.yaml`
- `k8s/devops-info-service/templates/servicemonitor.yaml`
- `k8s/devops-info-service/values-monitoring-statefulset.yaml`
- `k8s/MONITORING.md`

Files updated:

- `k8s/devops-info-service/values.yaml`
- `k8s/devops-info-service/templates/_helpers.tpl`
- `k8s/devops-info-service/templates/deployment.yaml`
- `k8s/devops-info-service/templates/rollout.yaml`
- `k8s/devops-info-service/templates/statefulset.yaml`
- `k8s/argocd/application.yaml`
- `k8s/argocd/application-dev.yaml`
- `k8s/argocd/application-prod.yaml`
- `k8s/argocd/applicationset.yaml`

## Validation Summary

Monitoring chart metadata pulled from the current Helm repo:

```text
.\.tools\helm.exe show chart prometheus-community/kube-prometheus-stack
version: 83.4.2
appVersion: v0.90.1
```

Validation commands:

```text
.\.tools\helm.exe lint .\k8s\devops-info-service
.\.tools\helm.exe template devops-info-service .\k8s\devops-info-service
.\.tools\helm.exe template devops-info-service-monitoring .\k8s\devops-info-service -f .\k8s\devops-info-service\values-monitoring-statefulset.yaml --namespace stateful
.\.tools\helm.exe template monitoring prometheus-community/kube-prometheus-stack --namespace monitoring -f .\k8s\monitoring\install-values.yaml
```

Rendered monitoring stack excerpts confirm the expected core service names:

```yaml
name: monitoring-grafana
name: monitoring-kube-prometheus-alertmanager
name: monitoring-kube-prometheus-prometheus
```

Rendered install values confirmation:

```yaml
grafana:
  adminPassword: prom-operator

prometheus:
  prometheusSpec:
    retention: 10d
```

## Monitoring Stack Components

### Prometheus Operator

- manages the Prometheus, Alertmanager, ServiceMonitor, and PodMonitor custom resources
- turns declarative CRDs into running monitoring workloads
- removes the need to hand-write full Prometheus configs for every scrape target

### Prometheus

- scrapes metrics from Kubernetes components and application targets
- stores time series data
- answers PromQL queries for dashboards and alert rules

### Alertmanager

- receives alerts from Prometheus
- groups, deduplicates, and routes alerts
- provides the Alertmanager UI for active/silenced alerts

### Grafana

- visualizes Prometheus metrics through dashboards
- provides the easiest way to answer the cluster questions in this lab
- uses `admin / prom-operator` with the provided install values

### kube-state-metrics

- exports metrics based on Kubernetes object state
- useful for replicas, deployments, StatefulSets, PVCs, pod phases, and similar metadata-driven observations

### node-exporter

- exports host and node metrics
- useful for CPU, memory, filesystem, and network metrics per Kubernetes node

## Monitoring Stack Installation

Prepared namespace manifest:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: monitoring
```

Prepared installation values in `k8s/monitoring/install-values.yaml`:

```yaml
grafana:
  adminPassword: prom-operator

prometheus:
  prometheusSpec:
    retention: 10d
    serviceMonitorSelectorNilUsesHelmValues: true
    podMonitorSelectorNilUsesHelmValues: true

alertmanager:
  alertmanagerSpec:
    replicas: 1
```

Live install commands:

```powershell
kubectl apply -f .\k8s\monitoring\namespace.yaml
.\.tools\helm.exe repo add prometheus-community https://prometheus-community.github.io/helm-charts
.\.tools\helm.exe repo update
.\.tools\helm.exe upgrade --install monitoring prometheus-community/kube-prometheus-stack --namespace monitoring -f .\k8s\monitoring\install-values.yaml
kubectl get pods,svc -n monitoring
```

Prepared access commands:

```powershell
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093
kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090
```

## ServiceMonitor Integration

The app already exposed `/metrics` from Lab 8. Lab 16 adds a Kubernetes-native `ServiceMonitor`.

Prepared application values in `k8s/devops-info-service/values-monitoring-statefulset.yaml`:

```yaml
replicaCount: 3

statefulset:
  enabled: true

initContainers:
  enabled: true
  waitForService:
    host: monitoring-kube-prometheus-prometheus.monitoring.svc.cluster.local

serviceMonitor:
  enabled: true
```

Rendered ServiceMonitor excerpt:

```yaml
kind: ServiceMonitor
metadata:
  name: devops-info-service-monitoring
  labels:
    release: monitoring
spec:
  endpoints:
    - path: /metrics
      interval: "15s"
      scrapeTimeout: "10s"
```

Why the `release: monitoring` label matters:

- `kube-prometheus-stack` defaults to selecting ServiceMonitors associated with the Helm release
- using `release: monitoring` keeps target discovery explicit and compatible with the stack defaults

Prepared live verification:

```powershell
.\.tools\helm.exe upgrade --install devops-info-service-monitoring .\k8s\devops-info-service --namespace stateful --create-namespace -f .\k8s\devops-info-service\values-monitoring-statefulset.yaml
kubectl get servicemonitor -n stateful
kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090
```

Then verify in Prometheus UI:

- target should appear under discovered ServiceMonitors
- querying `up{namespace="stateful"}` should include the app target
- querying `http_requests_total` should return application metrics after traffic is generated

## Init Containers

The chart now supports two opt-in init container patterns:

- wait-for-service
- download-into-shared-volume

Rendered StatefulSet excerpt:

```yaml
kind: StatefulSet
spec:
  template:
    spec:
      initContainers:
        - name: wait-for-service
          image: "busybox:1.36"
          command:
            - sh
            - -c
            - until nslookup "monitoring-kube-prometheus-prometheus.monitoring.svc.cluster.local"; do sleep 2; done
        - name: init-download
          image: "busybox:1.36"
          command:
            - sh
            - -c
            - wget -O "/init-data/index.html" "https://example.com"
```

How the patterns work:

- `wait-for-service` blocks pod startup until DNS can resolve the Prometheus service
- `init-download` fetches a file into an `emptyDir` volume
- the main container mounts the same `emptyDir` at `/init-data`, so it can inspect the downloaded file

Prepared live verification:

```powershell
kubectl get pods -n stateful -w
kubectl logs devops-info-service-monitoring-0 -n stateful -c init-download
kubectl exec devops-info-service-monitoring-0 -n stateful -- cat /init-data/index.html
```

## Grafana Dashboard Answers

These answers depend on live cluster runtime data, so I did not fabricate numeric results. The correct dashboards and query paths are prepared below.

### 1. Pod Resources - CPU and Memory of the StatefulSet

Dashboard:

- `Kubernetes / Compute Resources / Pod`

How to answer:

- filter namespace `stateful`
- select pods `devops-info-service-monitoring-0`, `-1`, `-2`
- read CPU and memory panels for each pod

### 2. Namespace Analysis - Most and Least CPU in `default`

Dashboard:

- `Kubernetes / Compute Resources / Namespace (Pods)`

How to answer:

- filter namespace `default`
- sort or inspect pod CPU panels
- the highest line/bar is the most CPU-consuming pod
- the lowest non-zero line/bar is the least CPU-consuming pod

### 3. Node Metrics - Memory Usage and CPU Cores

Dashboard:

- `Node Exporter / Nodes`

How to answer:

- inspect memory usage percentage
- inspect used memory vs total memory
- inspect CPU core count and load panels

### 4. Kubelet - Number of Pods and Containers Managed

Dashboard:

- `Kubernetes / Kubelet`

How to answer:

- inspect kubelet workload and runtime panels
- note managed pod count and managed container count on the active node(s)

### 5. Network - Traffic for Pods in `default`

Dashboard:

- `Kubernetes / Compute Resources / Namespace (Pods)`
- or `Kubernetes / Compute Resources / Pod`

PromQL alternatives:

```promql
sum by (pod) (rate(container_network_receive_bytes_total{namespace="default"}[5m]))
sum by (pod) (rate(container_network_transmit_bytes_total{namespace="default"}[5m]))
```

### 6. Alerts - Number of Active Alerts

UI:

- Alertmanager UI via `http://127.0.0.1:9093`

How to answer:

- count currently firing alerts in Alertmanager
- compare with Grafana alert panels if enabled

## Live Dashboard Workflow

Prepared workflow:

```powershell
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
# login: admin / prom-operator
```

Then:

1. Open `Kubernetes / Compute Resources / Pod`
2. Open `Kubernetes / Compute Resources / Namespace (Pods)`
3. Open `Node Exporter / Nodes`
4. Open `Kubernetes / Kubelet`
5. Open Alertmanager via port-forward

Screenshots to capture in a live run:

- Grafana overview with the target dashboards loaded
- StatefulSet pod resource panels
- namespace CPU comparison
- node memory and CPU view
- kubelet dashboard
- Alertmanager active alerts

## Installation Evidence for a Live Run

Expected commands:

```powershell
kubectl get po,svc -n monitoring
kubectl get servicemonitor -n stateful
kubectl get po,sts,svc -n stateful
```

Expected resource families:

- Prometheus Operator
- Prometheus
- Alertmanager
- Grafana
- kube-state-metrics
- node-exporter
- the app StatefulSet
- the app ServiceMonitor

## Command Reference

Useful commands for the live lab run:

```powershell
kubectl apply -f .\k8s\monitoring\namespace.yaml
.\.tools\helm.exe upgrade --install monitoring prometheus-community/kube-prometheus-stack --namespace monitoring -f .\k8s\monitoring\install-values.yaml
.\.tools\helm.exe upgrade --install devops-info-service-monitoring .\k8s\devops-info-service --namespace stateful --create-namespace -f .\k8s\devops-info-service\values-monitoring-statefulset.yaml
kubectl get pods,svc -n monitoring
kubectl get po,sts,svc,servicemonitor -n stateful
kubectl logs devops-info-service-monitoring-0 -n stateful -c init-download
kubectl exec devops-info-service-monitoring-0 -n stateful -- cat /init-data/index.html
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093
kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090
```
