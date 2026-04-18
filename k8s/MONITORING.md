# Lab 16 - Kubernetes Monitoring & Init Containers

## 1. Stack Components

### Prometheus Operator
- Manages Prometheus and Alertmanager as Kubernetes-native resources.
- Generates and reconciles the StatefulSets, Secrets, and configuration that back the monitoring stack.
- Lets us manage monitoring declaratively instead of hand-writing every low-level manifest.

### Prometheus
- Scrapes metrics from Kubernetes components and exporters.
- Stores time-series data and exposes the query API used by Grafana dashboards.
- Acts as the source of truth for CPU, memory, kubelet, and node metrics in this lab.

### Alertmanager
- Receives firing alerts from Prometheus.
- Deduplicates and groups alerts and exposes the active alert list/UI.
- In this cluster it confirmed active alerts such as `Watchdog`.

### Grafana
- Visualizes Prometheus data in prebuilt dashboards.
- Makes it easier to answer operational questions about pods, namespaces, nodes, and kubelets.
- The chart created a Grafana service named `monitoring-grafana`.

### kube-state-metrics
- Exposes metrics derived from Kubernetes object state.
- Useful for workload- and object-level information like deployments, pods, replicas, and conditions.
- Complements node/kubelet metrics by describing cluster state rather than host runtime counters.

### node-exporter
- Exposes host-level Linux metrics from the Kubernetes node.
- Provides memory, CPU, filesystem, and network counters for node dashboards.
- This is the source used for node memory and CPU-core answers below.

## 2. Installation

### Commands used
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

### Monitoring namespace evidence
```bash
$ kubectl get po,svc -n monitoring
NAME                                                         READY   STATUS    RESTARTS   AGE
pod/alertmanager-monitoring-kube-prometheus-alertmanager-0   2/2     Running   0          2m10s
pod/monitoring-grafana-7899bc8cc5-zjvfg                      3/3     Running   0          2m34s
pod/monitoring-kube-prometheus-operator-594b56f796-88fzw     1/1     Running   0          2m34s
pod/monitoring-kube-state-metrics-7d69554b96-9br6t           1/1     Running   0          2m34s
pod/monitoring-prometheus-node-exporter-gtxxw                1/1     Running   0          2m34s
pod/prometheus-monitoring-kube-prometheus-prometheus-0       2/2     Running   0          2m9s

NAME                                              TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)                      AGE
service/alertmanager-operated                     ClusterIP   None             <none>        9093/TCP,9094/TCP,9094/UDP   2m10s
service/monitoring-grafana                        ClusterIP   10.103.165.93    <none>        80/TCP                       2m34s
service/monitoring-kube-prometheus-alertmanager   ClusterIP   10.111.114.231   <none>        9093/TCP,8080/TCP            2m34s
service/monitoring-kube-prometheus-operator       ClusterIP   10.102.29.243    <none>        443/TCP                      2m34s
service/monitoring-kube-prometheus-prometheus     ClusterIP   10.109.12.171    <none>        9090/TCP,8080/TCP            2m34s
service/monitoring-kube-state-metrics             ClusterIP   10.100.136.196   <none>        8080/TCP                     2m34s
service/monitoring-prometheus-node-exporter       ClusterIP   10.98.212.237    <none>        9100/TCP                     2m34s
service/prometheus-operated                       ClusterIP   None             <none>        9090/TCP                     2m9s
```

### Useful access commands
```bash
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093
kubectl get secret monitoring-grafana -n monitoring -o jsonpath='{.data.admin-user}' | base64 -d
kubectl get secret monitoring-grafana -n monitoring -o jsonpath='{.data.admin-password}' | base64 -d
```

Note: this workspace is terminal-only, so the dashboard section below records the live Prometheus and Alertmanager values that back the Grafana panels.

## 3. Dashboard Answers

Measurements below were taken from the live cluster on `2026-04-18` after the monitoring stack and StatefulSet were healthy.

### 1. Pod resources: CPU and memory usage of the StatefulSet

Prometheus queries:
```promql
sum by (pod) (rate(container_cpu_usage_seconds_total{namespace="default",pod=~"python-app-sts-.*"}[5m])) * 1000
sum by (pod) (container_memory_working_set_bytes{namespace="default",pod=~"python-app-sts-.*"}) / 1024 / 1024
```

Results:

| Pod | CPU (mCPU) | Memory (MiB) |
|-----|------------|--------------|
| `python-app-sts-0` | 7 | 29 |
| `python-app-sts-1` | 7 | 30 |
| `python-app-sts-2` | 6 | 29 |

### 2. Namespace analysis: most/least CPU in `default`

Prometheus query:
```promql
sort_desc(sum by (pod) (rate(container_cpu_usage_seconds_total{namespace="default"}[5m])) * 1000)
```

Observed ranking:
- Highest CPU: `python-app-sts-0` and `python-app-sts-1` at about `7 mCPU`
- Lowest CPU: `python-app-sts-2` at about `6 mCPU`

Because this namespace only contains the three StatefulSet pods right now, they are both the complete set and the ranking set.

### 3. Node metrics: memory usage and CPU cores

Prometheus queries:
```promql
100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))
(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / 1024 / 1024
machine_cpu_cores
```

Observed values for node `minikube`:
- Memory used: `51.46%`
- Memory used: `2477.10 MiB`
- CPU cores: `8`

### 4. Kubelet: pods and containers managed

Prometheus queries:
```promql
sum(kubelet_running_pods)
sum(kubelet_running_containers)
```

Observed values:
- Running pods managed by kubelet: `30`
- Running containers managed by kubelet: `16`

### 5. Network traffic for pods in `default`

Grafana normally answers this from pod/container network metrics. In this Minikube session, pod-level network byte series were not exposed in Prometheus, so I verified traffic directly from each pod's `eth0` counters after sending requests through the service.

Service used to generate traffic:
```bash
kubectl port-forward svc/python-app-sts -n default 8080:80
curl http://127.0.0.1:8080/
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8080/visits
```

Per-pod interface counters from `/proc/net/dev`:

| Pod | RX bytes | TX bytes |
|-----|----------|----------|
| `python-app-sts-0` | 90664 | 87041 |
| `python-app-sts-1` | 99690 | 95808 |
| `python-app-sts-2` | 109192 | 104769 |

This shows active traffic on all three pods, with `python-app-sts-2` carrying the highest cumulative byte count in this snapshot.

### 6. Alerts: active alerts in Alertmanager

Alertmanager API query:
```bash
curl -s http://127.0.0.1:9093/api/v2/alerts | jq 'length'
curl -s http://127.0.0.1:9093/api/v2/alerts | jq -r '.[] | [.labels.alertname, .status.state, .labels.severity] | @tsv'
```

Observed values:
- Active alerts: `2`
- Alerts:
  - `etcdInsufficientMembers` - `active` - `critical`
  - `Watchdog` - `active` - `none`

## 4. Init Containers

The Python app Helm chart was updated to include both required patterns:
- A download init container that fetches `https://example.com` into a shared `emptyDir`
- A wait-for-service init container that blocks startup until `kubernetes.default.svc.cluster.local:443` is reachable

### Values added
The chart now includes an `initContainers` section in `values.yaml` for:
- Shared volume name and mount path
- Download image, URL, and destination file
- Wait-for-service image, host, port, and sleep interval

### Template implementation
The StatefulSet template in `statefulset.yaml`:
- Defines the two init containers
- Mounts the shared `emptyDir`
- Mounts the same shared volume read-only into the main app container at `/bootstrap`

### Release update
```bash
helm upgrade --install python-app-sts ./k8s/python-app -n default
kubectl rollout status statefulset/python-app-sts -n default
```

### StatefulSet status after rollout
```bash
$ kubectl get pods -n default -o wide
NAME               READY   STATUS    RESTARTS   AGE     IP            NODE       NOMINATED NODE   READINESS GATES
python-app-sts-0   1/1     Running   0          8m41s   10.244.0.21   minikube   <none>           <none>
python-app-sts-1   1/1     Running   0          9m26s   10.244.0.20   minikube   <none>           <none>
python-app-sts-2   1/1     Running   0          10m     10.244.0.16   minikube   <none>           <none>
```

### Proof: init container logs
```bash
$ kubectl logs python-app-sts-2 -n default -c init-download
Connecting to example.com (104.20.23.154:443)
wget: note: TLS certificate validation not implemented
saving to '/bootstrap/index.html'
index.html           100% |********************************|   528  0:00:00 ETA
'/bootstrap/index.html' saved
```

```bash
$ kubectl logs python-app-sts-2 -n default -c wait-for-service
service is reachable
```

### Proof: main container can read the downloaded file
```bash
$ kubectl exec python-app-sts-2 -n default -- cat /bootstrap/index.html
<!doctype html><html lang="en"><head><title>Example Domain</title>...
```

### Proof: pod shows completed init containers
```bash
$ kubectl describe pod python-app-sts-2 -n default
Init Containers:
  init-download:
    State:          Terminated
      Reason:       Completed
      Exit Code:    0
  wait-for-service:
    State:          Terminated
      Reason:       Completed
      Exit Code:    0
Containers:
  python-app:
    State:          Running
```

## 5. Summary

- Installed `kube-prometheus-stack` in namespace `monitoring`
- Verified Prometheus, Grafana, Alertmanager, kube-state-metrics, node-exporter, and services
- Answered all six monitoring questions from live cluster data
- Implemented both required init-container patterns in the Helm chart
- Verified the downloaded file is accessible from the main application container
- Skipped the bonus task on purpose
