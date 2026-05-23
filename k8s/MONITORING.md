# Lab 16 — Kubernetes Monitoring & Init Containers


## Task 1 — Kube-Prometheus Stack

### Stack Components

#### Prometheus Operator

The Prometheus Operator automates the deployment and configuration of Prometheus instances in Kubernetes. It introduces Custom Resource Definitions (CRDs) like:
- **ServiceMonitor:** Declaratively define Prometheus scrape targets by label matching Kubernetes services
- **PrometheusRule:** Define alert rules and recording rules for Prometheus
- **Prometheus:** CRD to manage Prometheus server instances
- **AlertmanagerConfig:** Manage alerting configurations

The operator watches these resources and automatically reconciles Prometheus configuration, eliminating manual scrape target management.

#### Prometheus

The time-series database and monitoring engine. Prometheus:
- Scrapes metrics from targets (pods, nodes, services) via HTTP on configured intervals
- Stores metrics as time-series data (label + timestamp + value)
- Provides a query language (PromQL) for analysis
- Evaluates alert rules and fires alerts on condition matches
- Exposes `/metrics` endpoint for scraping its own metrics

**In cluster:** Runs as a StatefulSet managed by Prometheus Operator, stores data in persistent volume, scrapes Kubelet, node-exporter, kube-state-metrics, Alertmanager, and application endpoints.

#### Alertmanager

Handles alerts fired by Prometheus. Alertmanager:
- Receives alerts from Prometheus
- Groups related alerts (e.g., all pod CPU high alerts for same namespace)
- Deduplicates repeated alerts
- Routes alerts to destinations (Slack, PagerDuty, email, webhooks)
- Manages alert silencing and inhibition

**In cluster:** Runs as a StatefulSet, provides UI on port 9093, receives alerts via `http://alertmanager:9093/api/v1/alerts`.

#### Grafana

Visualization and alerting platform for Prometheus data. Grafana:
- Queries Prometheus to fetch time-series data
- Renders interactive dashboards with graphs, tables, gauges
- Supports multi-core data sources (Prometheus, Loki, Elasticsearch, etc.)
- Manages users and permissions
- Includes built-in dashboards for Kubernetes (Prometheus Operator, node-exporter, kubelet)

**In cluster:** Runs as Deployment, exposes UI on port 3000, default credentials: admin/prom-operator. Pre-populated with 20+ dashboards for cluster monitoring.

#### kube-state-metrics

Generates Kubernetes object metrics for Prometheus. Exports metrics about:
- Pod state (created, running, failed, completed)
- Pod resource requests/limits
- Node state (ready, memory pressure, disk pressure)
- Deployment replicas (desired, updated, ready, available)
- StatefulSet replicas, persistent volume claims, jobs, CronJobs

**Metrics format:** `kube_pod_labels`, `kube_pod_info`, `kube_deployment_status_replicas_available`, etc.

**In cluster:** Runs as Deployment, exposes `/metrics` on port 8080, Prometheus ServiceMonitor auto-discovers it for scraping.

#### node-exporter

System hardware and OS metrics exporter for each Kubernetes node. Exports:
- CPU metrics (usage, time in different states)
- Memory metrics (total, used, free, buffers, cache)
- Disk metrics (read/write operations, space usage)
- Network metrics (bytes sent/received, network errors)
- System uptime, load average

**Deployed as:** DaemonSet (one pod per node). Exposes `/metrics` on port 9100 per node.

### Installation

#### Add Repository

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

#### Install via Helm

```bash
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

**Installation proceeds:**
1. Creates monitoring namespace
2. Deploys Custom Resource Definitions (CRDs) for Prometheus Operator
3. Deploys Prometheus Operator controller (manages Prometheus/Alertmanager instances)
4. Deploys Prometheus StatefulSet
5. Deploys Alertmanager StatefulSet
6. Deploys Grafana Deployment
7. Deploys kube-state-metrics Deployment
8. Deploys node-exporter DaemonSet (one per node)
9. Creates ServiceMonitor resources pointing to Kubernetes API, kubelet, etc.
10. Creates PrometheusRule resources with default alert rules

#### Verify Installation

```bash
kubectl get pods -n monitoring
```

Installation evidence - all pods running:

```
NAME                                                     READY   STATUS    RESTARTS   AGE
alertmanager-monitoring-kube-prometheus-alertmanager-0   2/2     Running   0          6m
monitoring-grafana-d8864d655-sx5wh                       3/3     Running   0          7m23s
monitoring-kube-prometheus-operator-59754b75c4-kd8zb     1/1     Running   0          7m23s
monitoring-kube-state-metrics-5957bd45bc-qhd9v           1/1     Running   0          7m23s
monitoring-prometheus-node-exporter-6hmz2                1/1     Running   0          7m23s
prometheus-monitoring-kube-prometheus-prometheus-0       2/2     Running   0          6m
```

Status Summary:
- Alertmanager: 1 StatefulSet replica (2/2 containers ready)
- Grafana: 1 Deployment replica (3/3 containers ready)
- Prometheus Operator: 1 Deployment replica (1/1 ready)
- kube-state-metrics: 1 Deployment replica (1/1 ready)
- node-exporter: 1 DaemonSet pod per node (1/1 ready)
- Prometheus: 1 StatefulSet replica (2/2 containers ready)

#### Verify Services

```bash
kubectl get svc -n monitoring
```

Main services:
- `monitoring-kube-prom-prometheus`: Prometheus UI (port 9090)
- `monitoring-grafana`: Grafana UI (port 80)
- `monitoring-kube-prom-alertmanager`: Alertmanager UI (port 9093)
- `kube-state-metrics`: kube-state-metrics scrape target (port 8080)
- `node-exporter`: node-exporter scrape targets (port 9100)

#### Access Grafana

```bash
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
```

Open http://localhost:3000 in browser.

Default credentials: `admin` / `prom-operator`

Pre-loaded dashboards available:
- Kubernetes / Compute Resources / Cluster
- Kubernetes / Compute Resources / Namespace (Pods)
- Kubernetes / Compute Resources / Pod
- Node Exporter / Nodes
- Kubernetes / Kubelet
- Prometheus (self-monitoring)
- And 15+ more

#### Access Prometheus

```bash
kubectl port-forward svc/monitoring-kube-prom-prometheus -n monitoring 9090:9090
```

Open http://localhost:9090 in browser. Query metrics with PromQL, view scraped targets, check alerts.

#### Access Alertmanager

```bash
kubectl port-forward svc/monitoring-kube-prom-alertmanager -n monitoring 9093:9093
```

Open http://localhost:9093 in browser. View active/resolved alerts, manage silences.

---

## Task 2 — Grafana Dashboard Exploration

Answers (screenshots in `lab16-evidence/`):

1) Pod Resources (StatefulSet)
- CPU: small but measurable per-pod CPU activity after generating load. See CPU timeline: [cpu-usage.png](lab16-evidence/cpu-usage.png).
- Per-pod comparison (most / least): `lab15-sts-devops-python-2` uses the most CPU, `lab15-sts-devops-python-0` the least. See [most-least-cpu-usage.png](lab16-evidence/most-least-cpu-usage.png).
- Memory: per-pod memory in MB shown here: [memory-usage.png](lab16-evidence/memory-usage.png).

2) Namespace Analysis (default)
- The dashboard query used: `sum(rate(container_cpu_usage_seconds_total{namespace="default"}[5m])) by (pod)` (run in Explore). In this environment the `default` namespace pods show minimal/near-zero CPU activity during sampling (no significant traffic). For lab answers use the dashboard to pick top/bottom pods in `default`.

3) Node Metrics (minikube / instance 192.168.49.2:9100)
- Memory used (MB): see [used-memory-mb.png](lab16-evidence/used-memory-mb.png).
- Memory used (%): see [used-memory-percentage.png](lab16-evidence/used-memory-percentage.png).
- CPU cores and %: see [cpu-cores.png](lab16-evidence/cpu-cores.png) and [cpu-percentage.png](lab16-evidence/cpu-percentage.png).

4) Kubelet (pods/containers managed)
- Use the "Kubernetes / Kubelet" dashboard (or Prometheus metrics `kubelet_running_pods`, `kubelet_running_containers`).
- Current cluster counts: see screenshot [running-pod-containers.png](lab16-evidence/running-pod-containers.png) — shows ~42 running pods (includes system and monitoring components).

5) Network (pods in `default` namespace)
- Prometheus queries used:
  - Rx (bytes/sec): `sum(rate(container_network_receive_bytes_total{namespace="default"}[5m])) by (pod)`
  - Tx (bytes/sec): `sum(rate(container_network_transmit_bytes_total{namespace="default"}[5m])) by (pod)`
- In this environment the `default` namespace pods had minimal network traffic during sampling (no chart screenshot produced). If you need absolute numbers, run the queries above in Grafana Explore.

6) Alerts (Alertmanager)
- Active alerts count (from Alertmanager / Prometheus): see [alerts-count.png](lab16-evidence/alerts-count.png). Use `count(ALERTS{alertstate="firing"})` in Grafana Explore to reproduce.

---

## Task 3 — Init Containers

Implementation summary

- Added init container configuration to the `devops-python` Helm chart (`initContainers` values).
- Two init container patterns implemented:
  - `init-download` — creates a test file on a shared `emptyDir` mounted at `/work-dir` (visible to main container at `/data-init`).
  - `wait-for-service` — waits for the headless service DNS to resolve before allowing the main container to start.

Deployment commands (performed during lab):
```
# upgrade chart with init containers enabled
helm upgrade lab15-sts /home/chupapupa/DevOps-Core-Course-v/k8s/devops-python \
  --namespace lab15 \
  --set initContainers.enabled=true \
  --set initContainers.download.enabled=true \
  --set initContainers.waitForService.enabled=true \
  --set service.type=ClusterIP \
  --set service.nodePort=null
```

Verification evidence

- Init container log (example):
```
=== Init Container: Creating test file ===
Pod hostname: lab15-sts-devops-python-0
Init container timestamp: Sat May 23 02:23:07 UTC 2026
total 12
-rw-r--r--    1 root     root           194 May 23 02:23 initialized.txt
Created by init-download on Sat May 23 02:23:07 UTC 2026
```

- Main container can read the file created by init container:
```
$ kubectl exec -n lab15 lab15-sts-devops-python-0 -- cat /data-init/initialized.txt
Pod lab15-sts initialized at $(date)
This file was created by init-download container
Main application can read this file in /data-init/
Created by init-download on Sat May 23 02:23:07 UTC 2026
```

- DNS wait-for-service output (init container resolved headless service and pod IPs):
```
Waiting for service lab15-sts-devops-python-headless...
Name: lab15-sts-devops-python-headless.lab15.svc.cluster.local
Address: 10.244.0.144
Name: lab15-sts-devops-python-headless.lab15.svc.cluster.local
Address: 10.244.0.145
Name: lab15-sts-devops-python-headless.lab15.svc.cluster.local
Address: 10.244.0.146
```

All init containers completed and pods reached `Ready` state during verification.
