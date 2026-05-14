# Lab 16 — Kubernetes Monitoring & Init Containers

This document covers Lab 16 Task 1: Kube-Prometheus Stack installation and component documentation.

---

## Task 1 — Kube-Prometheus Stack Components

### Component Overview

The **Kube-Prometheus Stack** provides comprehensive cluster monitoring with the following core components:

#### 1. **Prometheus Operator**
- CRD-based controller that manages Prometheus and Alertmanager custom resources
- Automatically generates Prometheus configuration from `ServiceMonitor` and `PrometheusRule` CRDs
- Simplifies multi-Prometheus deployments and service discovery
- Runs in the monitoring namespace and reconciles operator manifests

#### 2. **Prometheus**
- Time-series database and metrics collection engine
- Scrapes metrics from Kubernetes components and exporters (node-exporter, kube-state-metrics, kubelet)
- Stores metrics with configurable retention (default ~15 days)
- Provides HTTP API and PromQL query language for dashboards and alerting
- Stateful deployment using persistent storage (usually PVC)

#### 3. **Alertmanager**
- Groups, deduplicates, and routes alerts from Prometheus
- Manages alert notifications via email, Slack, PagerDuty, webhooks, etc.
- Handles alert silencing and inhibition rules
- Provides web UI to view active alerts and manage notification status
- Deployed as a StatefulSet for high availability

#### 4. **Grafana**
- Web dashboard and visualization platform for metrics
- Pre-configured with Prometheus data source and built-in dashboards
- Allows real-time exploration of Kubernetes cluster metrics
- Provides dashboard templating for dynamic queries and variables
- Includes user management, alerting integration, and plugin support

#### 5. **kube-state-metrics**
- Exports Kubernetes API objects as Prometheus metrics
- Scrapes Kubernetes API to generate metrics for Deployments, StatefulSets, Pods, Services, etc.
- Enables visibility into object counts, resource requests/limits, replica status, and more
- Critical for understanding Kubernetes workload health without parsing logs
- Exposes metrics on port 8080 `/metrics` endpoint

#### 6. **node-exporter**
- Runs as a DaemonSet on every cluster node
- Exposes hardware and OS-level metrics: CPU, memory, disk I/O, network, processes
- Scrapes Linux kernel metrics via `/proc` and `/sys` filesystems
- Provides node-level visibility for infrastructure monitoring and alerting
- Exposes metrics on port 9100 `/metrics` endpoint

---

## Installation Evidence

### Helm Installation

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

### Pods and Services Status

```bash
kubectl get pods -n monitoring
kubectl get svc -n monitoring
```

**Output:**

```text
NAME                                                     READY   STATUS    RESTARTS   AGE
alertmanager-monitoring-kube-prometheus-alertmanager-0   2/2     Running   0          10m
monitoring-grafana-5d6675d5-brlbb                        3/3     Running   0          10m
monitoring-kube-prometheus-operator-646fb7bdb-v8lcp      1/1     Running   0          10m
monitoring-kube-state-metrics-5746795bd9-xdck8           1/1     Running   0          10m
monitoring-prometheus-node-exporter-ndzzd                1/1     Running   0          10m
prometheus-monitoring-kube-prometheus-prometheus-0       2/2     Running   0           9m
```

**Services:**

```text
NAME                                            TYPE        CLUSTER-IP      PORT(S)
alertmanager-operated                           ClusterIP   None            9093/TCP,9094/TCP,9094/UDP
monitoring-grafana                              ClusterIP   10.96.142.32    80/TCP
monitoring-kube-prometheus-alertmanager         ClusterIP   10.96.175.41    9093/TCP,8080/TCP
monitoring-kube-prometheus-operator             ClusterIP   10.96.225.43    443/TCP
monitoring-kube-prometheus-prometheus           ClusterIP   10.96.143.176   9090/TCP,8080/TCP
monitoring-kube-state-metrics                   ClusterIP   10.96.29.129    8080/TCP
monitoring-prometheus-node-exporter             ClusterIP   10.96.151.170   9100/TCP
prometheus-operated                             ClusterIP   None            9090/TCP
```

### Verification

All required components are running and healthy:

- ✅ Prometheus Operator: active and reconciling CRDs
- ✅ Prometheus: 2/2 containers running, ingesting metrics from cluster
- ✅ Alertmanager: 2/2 containers running, ready for alert notifications
- ✅ Grafana: 3/3 containers running, dashboards available
- ✅ kube-state-metrics: 1/1 running, exporting Kubernetes object metrics
- ✅ node-exporter: 1/1 running (DaemonSet), exporting node metrics

---

## Accessing the Stack

### Grafana

```bash
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
# Access: http://localhost:3000
# Credentials: admin / prom-operator (or check secret)
```

### Prometheus

```bash
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090
# Access: http://localhost:9090
```

### Alertmanager

```bash
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-alertmanager 9093:9093
# Access: http://localhost:9093
```

---

## Task 2 — Grafana Dashboard Answers

These answers were collected from the kube-prometheus stack dashboards / Prometheus data after deploying:

- StatefulSet `devops-app-stateful` in namespace `lab15`
- Default namespace workloads: `cpu-hog`, `web`, `traffic-gen`

### 1) Pod Resources: CPU / memory usage of the StatefulSet

Current pod-level values:

| Pod | CPU (cores) | Memory working set |
|---|---:|---:|
| `devops-app-stateful-0` | `0.00036` | `27824128 B` |
| `devops-app-stateful-1` | `0.00041` | `28008448 B` |
| `devops-app-stateful-2` | `0.00038` | `27480064 B` |

### 2) Namespace Analysis: CPU use in `default`

Pods ordered by CPU usage:

| Pod | CPU (cores) |
|---|---:|
| `cpu-hog-5f866f88cb-g5zc5` | `0.1999` |
| `traffic-gen-58fc575c96-nbvls` | `0.00417` |
| `web-5cbb799bb7-qflk6` | `0.00020` |

Most CPU: `cpu-hog-5f866f88cb-g5zc5`

Least CPU: `web-5cbb799bb7-qflk6`

### 3) Node Metrics

Single node in kind cluster:

| Node | Memory used | Memory used % | CPU cores |
|---|---:|---:|---:|
| `172.18.0.2:9100` | `7629.34 MB` | `48.63%` | `8` |

### 4) Kubelet: managed pods / containers

- Total pods in cluster: `22`
- Total containers in cluster: `22`

### 5) Network: traffic for pods in `default`

Current per-pod network rates:

| Pod | RX bytes/sec | TX bytes/sec |
|---|---:|---:|
| `cpu-hog-5f866f88cb-g5zc5` | `0` | `0` |
| `traffic-gen-58fc575c96-nbvls` | `2701.98` | `1383.33` |
| `web-5cbb799bb7-qflk6` | `564.23` | `1195.72` |

### 6) Alerts

Active alerts count: `12`

Examples currently firing / pending:

- `KubeControllerManagerInstanceUnreachable` — firing
- `KubeSchedulerInstanceUnreachable` — firing
- `KubeProxyInstanceUnreachable` — firing
- `TargetDown` — firing
- `Watchdog` — firing
- `etcdInsufficientMembers` — firing
- `CPUThrottlingHigh` — pending

---

## Task 3 — Init Containers

Implementation files:

- `k8s/init-containers/download-demo.yaml`
- `k8s/init-containers/wait-for-service-demo.yaml`

### 1) Basic init container: download file to shared volume

Pod: `init-download-demo`

- Init container `init-download` downloads `http://example.com` into `/work-dir/index.html`
- Shared volume: `emptyDir` (`workdir`)
- Main container mounts the same volume at `/data`

Verification commands:

```bash
kubectl logs init-download-demo -n default -c init-download
kubectl exec -n default init-download-demo -- sh -c 'ls -l /data && head -n 5 /data/index.html'
```

Evidence:

```text
Connecting to example.com (172.66.147.243:80)
saving to '/work-dir/index.html'
index.html           100% |********************************|   528  0:00:00 ETA
'/work-dir/index.html' saved
total 4
-rw-r--r--    1 root     root           528 May 14 10:59 index.html
```

Main container can read the downloaded file from shared volume:

```text
total 4
-rw-r--r--    1 root     root           528 May 14 10:59 index.html
<!doctype html><html lang="en"><head><title>Example Domain</title>...
```

### 2) Wait-for-service pattern

Resources in `k8s/init-containers/wait-for-service-demo.yaml`:

- `Deployment/wait-backend` + `Service/wait-backend`
- `Deployment/init-wait-demo` with init container `wait-for-service`

Init command:

```sh
until wget -q -O- http://wait-backend.default.svc.cluster.local >/dev/null; do
  echo "waiting for wait-backend..."
  sleep 2
done
echo "wait-backend is reachable"
```

Verification command:

```bash
kubectl logs -n default deploy/init-wait-demo -c wait-for-service --tail=50
```

Evidence:

```text
wait-backend is reachable
```

Pod readiness evidence (`init` finished, main container started):

```bash
kubectl get pods -n default
```

```text
init-download-demo                1/1   Running
init-wait-demo-74d69d75f8-9kjqs   1/1   Running
wait-backend-7fddd5ccb4-4d7r5     1/1   Running
```

---

## Task 4 — Documentation Completion

This report now includes all required Lab 16 sections:

1. **Stack Components** — covered in **Task 1 — Kube-Prometheus Stack Components**
2. **Installation Evidence** — `kubectl get po,svc -n monitoring` output included
3. **Dashboard Answers** — all 6 monitoring questions answered in **Task 2**
4. **Init Containers** — implementation + proof included in **Task 3**

### Final Installation Snapshot (current)

```bash
kubectl get po,svc -n monitoring
```

```text
monitoring pods: all Running (Prometheus, Grafana, Alertmanager, Operator, kube-state-metrics, node-exporter)
monitoring services: all present (grafana, prometheus, alertmanager, kube-state-metrics, node-exporter)
```

Recommended captures:

- Grafana dashboard panels used for Task 2 answers (CPU/memory, node, kubelet, network)
- Alertmanager page showing active alerts

