# Lab 16 — Kubernetes Monitoring & Init Containers

Environment:

- Kubernetes context: `kind-lab9`
- Cluster node: `lab9-control-plane`
- Monitoring release: `monitoring`
- Chart: `kube-prometheus-stack` `65.8.1`
- Application namespace: `lab16`
- Application workload: `StatefulSet/devops-info-service`, 2 replicas

Screenshots:

- [Prometheus targets](lab16/screenshots/prometheus-targets.png)
- [Prometheus query](lab16/screenshots/prometheus-query.png)
- [Grafana namespace pods dashboard](lab16/screenshots/grafana-namespace-pods.png)
- [Alertmanager alerts](lab16/screenshots/alertmanager-alerts.png)

## Stack Components

| Component | Role |
| --- | --- |
| Prometheus Operator | Reconciles monitoring CRDs such as `Prometheus`, `Alertmanager`, `ServiceMonitor`, and generated scrape configuration. |
| Prometheus | Stores time series, evaluates PromQL, scrapes Kubernetes and app targets. |
| Alertmanager | Receives firing alerts from Prometheus, groups them, deduplicates them, and handles notification routing. |
| Grafana | Provides dashboards for Kubernetes workloads, nodes, kubelet, and custom app metrics. |
| kube-state-metrics | Exposes Kubernetes object state as metrics: deployments, pods, StatefulSets, services, labels, conditions. |
| node-exporter | Exposes Linux node CPU, memory, filesystem, and network metrics. |

## Installation Evidence

Install command:

```bash
helm upgrade --install monitoring /tmp/lab16-helm/kube-prometheus-stack-65.8.1.tgz \
  --namespace monitoring \
  --create-namespace \
  --wait \
  --timeout 10m
```

`kubectl get po,svc -n monitoring`:

```text
NAME                                                         READY   STATUS    RESTARTS   AGE
pod/alertmanager-monitoring-kube-prometheus-alertmanager-0   2/2     Running   0          4m1s
pod/monitoring-grafana-69db76f9b4-zqbcz                      3/3     Running   0          5m22s
pod/monitoring-kube-prometheus-operator-d5dbb45f9-rj827      1/1     Running   0          5m22s
pod/monitoring-kube-state-metrics-75c9d8f7c7-5nckw           1/1     Running   0          5m22s
pod/monitoring-prometheus-node-exporter-qknxg                1/1     Running   0          80s
pod/prometheus-monitoring-kube-prometheus-prometheus-0       2/2     Running   0          4m1s

NAME                                              TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)
service/alertmanager-operated                     ClusterIP   None            <none>        9093/TCP,9094/TCP,9094/UDP
service/monitoring-grafana                        ClusterIP   10.96.211.118   <none>        80/TCP
service/monitoring-kube-prometheus-alertmanager   ClusterIP   10.96.85.78     <none>        9093/TCP,8080/TCP
service/monitoring-kube-prometheus-operator       ClusterIP   10.96.145.86    <none>        443/TCP
service/monitoring-kube-prometheus-prometheus     ClusterIP   10.96.231.176   <none>        9090/TCP,8080/TCP
service/monitoring-kube-state-metrics             ClusterIP   10.96.52.90     <none>        8080/TCP
service/monitoring-prometheus-node-exporter       ClusterIP   10.96.194.144   <none>        9100/TCP
service/prometheus-operated                       ClusterIP   None            <none>        9090/TCP
```

## Dashboard Answers

### 1. Pod Resources: StatefulSet CPU and Memory

PromQL:

```promql
sum by (pod) (rate(container_cpu_usage_seconds_total{namespace="lab16",pod=~"devops-info-service-.*",container!="",container!="POD"}[2m]))
sum by (pod) (container_memory_working_set_bytes{namespace="lab16",pod=~"devops-info-service-.*",container!="",container!="POD"})
```

Observed values:

| Pod | CPU cores | CPU millicores | Memory bytes | Memory MiB |
| --- | ---: | ---: | ---: | ---: |
| `devops-info-service-0` | `0.001366` | `1.37m` | `9,965,568` | `9.50` |
| `devops-info-service-1` | `0.000675` | `0.68m` | `15,953,920` | `15.22` |

### 2. Namespace Analysis: Default Namespace CPU

`kubectl get pods -n default` returned:

```text
No resources found in default namespace.
```

So there are no default namespace pods to rank by most/least CPU. The app workload for this lab runs in `lab16`.

### 3. Node Metrics

PromQL:

```promql
100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))
node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes
count(count by (cpu) (node_cpu_seconds_total{mode="idle"}))
```

Observed values for `192.168.117.2:9100`:

| Metric | Value |
| --- | ---: |
| Memory used | `52.33%` |
| Memory used | `4,386,590,720` bytes, about `4,183 MiB` |
| CPU cores | `10` |

### 4. Kubelet: Pods and Containers

PromQL:

```promql
kubelet_running_pods
kubelet_running_containers
```

Observed values for kubelet `192.168.117.2:10250`:

| Metric | Value |
| --- | ---: |
| Running pods | `53` |
| Containers: running | `57` |
| Containers: exited | `54` |
| Containers: created | `1` |

### 5. Network: Pod Traffic

Default namespace has no pods, so no default pod traffic exists. For the lab StatefulSet in `lab16`:

PromQL:

```promql
sum by (pod) (rate(container_network_receive_bytes_total{namespace="lab16",pod=~"devops-info-service-.*"}[2m]))
sum by (pod) (rate(container_network_transmit_bytes_total{namespace="lab16",pod=~"devops-info-service-.*"}[2m]))
```

Observed values:

| Pod | Receive bytes/s | Transmit bytes/s |
| --- | ---: | ---: |
| `devops-info-service-0` | `123.93` | `193.99` |
| `devops-info-service-1` | `126.07` | `191.75` |

### 6. Alerts

Prometheus firing alerts:

```text
Watchdog        severity=none
InfoInhibitor   severity=none   namespace=kube-system
InfoInhibitor   severity=none   namespace=dev
```

Alertmanager UI/API had `8` active entries at capture time. Some were transient `TargetDown` entries caused by restarting Prometheus to reload the updated `ServiceMonitor` selector.

## Init Containers

Implemented in [k8s/lab16/app.yaml](lab16/app.yaml):

- `wait-for-service`: waits until `lab16-dependency.lab16.svc.cluster.local` resolves.
- `init-download`: uses `wget` to download `http://example.com` to `/work-dir/index.html`.
- Main app mounts the same `emptyDir` at `/data` and exposes `/init-file`, proving it can read `/data/index.html`.

Resource verification:

```text
NAME                        READY   STATUS    RESTARTS   AGE
pod/devops-info-service-0   1/1     Running   0          6m49s
pod/devops-info-service-1   1/1     Running   0          6m13s

NAME                                   READY   AGE
statefulset.apps/devops-info-service   2/2     67s

NAME                                   TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)
service/devops-info-service            ClusterIP   10.96.159.226   <none>        80/TCP
service/devops-info-service-headless   ClusterIP   None            <none>        80/TCP
service/lab16-dependency               ClusterIP   10.96.25.31     <none>        80/TCP
```

Init logs:

```text
Name: lab16-dependency.lab16.svc.cluster.local
Address: 10.96.25.31
dependency DNS is ready

Connecting to example.com (198.20.0.43:80)
saving to '/work-dir/index.html'
'/work-dir/index.html' saved
downloaded 528 bytes
```

Main container proof:

```bash
curl http://127.0.0.1:18080/init-file
```

Output starts with:

```html
<!doctype html><html lang="en"><head><title>Example Domain</title>
```

## Bonus: Custom Metrics and ServiceMonitor

Application changes:

- Added `/metrics` endpoint in [app_go/main.go](../app_go/main.go).
- Added Prometheus client dependency in [app_go/go.mod](../app_go/go.mod).
- Added tests for `/metrics` and `/init-file` in [app_go/main_test.go](../app_go/main_test.go).

Kubernetes changes:

- App Service labels include `monitoring: enabled`.
- [k8s/lab16/servicemonitor.yaml](lab16/servicemonitor.yaml) selects only the app Service and scrapes `/metrics` on port `http`.

Direct metrics proof:

```text
go_gc_duration_seconds_count 1
go_goroutines 15
process_cpu_seconds_total 0.07
```

Prometheus target proof:

```text
up  devops-info-service  devops-info-service-0  http://10.244.0.48:8080/metrics
up  devops-info-service  devops-info-service-1  http://10.244.0.49:8080/metrics
```

Verification:

```bash
go test ./...
docker build -t devops-info-service-go:lab16 ./app_go
kind load docker-image devops-info-service-go:lab16 --name lab9
kubectl apply -k k8s/lab16
kubectl apply -f k8s/lab16/servicemonitor.yaml
kubectl rollout status statefulset/devops-info-service -n lab16
```
