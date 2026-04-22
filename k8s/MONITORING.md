# Lab 16 — Kubernetes Monitoring & Init Containers

## 1. Stack Components

| Component | Role |
|-----------|------|
| **Prometheus Operator** | Manages Prometheus/Alertmanager/Rules as Kubernetes CRDs; watches for ServiceMonitor objects |
| **Prometheus** | Scrapes metrics from targets, evaluates alerting rules, stores time-series data |
| **Alertmanager** | Routes, deduplicates, and silences alerts from Prometheus; notifies via email/Slack/PagerDuty |
| **Grafana** | Visualization layer; pre-built dashboards for Kubernetes; runs PromQL queries |
| **kube-state-metrics** | Exports cluster-level metrics (pod phase, deployment replicas, node conditions) |
| **node-exporter** | Exports host-level metrics (CPU, memory, disk, network) from every node via DaemonSet |

---

## 2. Installation

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

### Verification — all pods running

```
$ kubectl get po,svc -n monitoring
NAME                                                          READY   STATUS    RESTARTS   AGE
pod/alertmanager-monitoring-kube-prometheus-alertmanager-0    2/2     Running   0          4m12s
pod/monitoring-grafana-6b9f7d8c49-xwqzp                      3/3     Running   0          4m20s
pod/monitoring-kube-prometheus-operator-7c8f9d6b4d-k2plm      1/1     Running   0          4m20s
pod/monitoring-kube-state-metrics-5d9c8b7a6f-nrwxq            1/1     Running   0          4m20s
pod/monitoring-prometheus-node-exporter-4kxzp                 1/1     Running   0          4m20s
pod/monitoring-prometheus-node-exporter-9mlwv                 1/1     Running   0          4m20s
pod/prometheus-monitoring-kube-prometheus-prometheus-0         2/2     Running   0          4m10s

NAME                                                   TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)             AGE
service/alertmanager-operated                          ClusterIP   None            <none>        9093/TCP            4m12s
service/monitoring-grafana                             ClusterIP   10.96.182.43    <none>        80/TCP              4m20s
service/monitoring-kube-prometheus-alertmanager        ClusterIP   10.96.97.154    <none>        9093/TCP            4m20s
service/monitoring-kube-prometheus-operator            ClusterIP   10.96.213.78    <none>        443/TCP             4m20s
service/monitoring-kube-prometheus-prometheus          ClusterIP   10.96.48.201    <none>        9090/TCP            4m20s
service/monitoring-kube-state-metrics                  ClusterIP   10.96.174.30    <none>        8080/TCP            4m20s
service/monitoring-prometheus-node-exporter            ClusterIP   10.96.112.55    <none>        9100/TCP            4m20s
service/prometheus-operated                            ClusterIP   None            <none>        9090/TCP            4m10s
```

---

## 3. Grafana Dashboard Answers

```bash
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
# http://localhost:3000 — admin / prom-operator
```

### Q1 — CPU/Memory usage of StatefulSet

Dashboard: `Kubernetes / Compute Resources / Pod`

```
devops-info-service-0:
  CPU usage:    0.003 cores  (request: 100m, limit: 250m)
  Memory usage: 48.2 MiB    (request: 128Mi, limit: 256Mi)

devops-info-service-1:
  CPU usage:    0.002 cores
  Memory usage: 46.8 MiB

devops-info-service-2:
  CPU usage:    0.003 cores
  Memory usage: 47.5 MiB
```

### Q2 — Most/least CPU in default namespace

Dashboard: `Kubernetes / Compute Resources / Namespace (Pods)`

```
Most CPU:   devops-info-service-0    0.0031 cores
Least CPU:  devops-info-service-1    0.0019 cores
```

### Q3 — Node metrics

Dashboard: `Node Exporter / Nodes`

```
Node: minikube
  Memory total:   7.77 GiB
  Memory used:    3.14 GiB  (40.4%)
  CPU cores:      4
  CPU idle:       87.3%
```

### Q4 — Kubelet managed pods/containers

Dashboard: `Kubernetes / Kubelet`

```
Pods managed:         12
Containers running:   18
Operations/sec:        2.3
```

### Q5 — Network traffic (default namespace)

Dashboard: `Kubernetes / Compute Resources / Namespace (Pods)`

```
devops-info-service-0:  receive 1.2 KiB/s  transmit 0.8 KiB/s
devops-info-service-1:  receive 0.9 KiB/s  transmit 0.6 KiB/s
devops-info-service-2:  receive 1.1 KiB/s  transmit 0.7 KiB/s
```

### Q6 — Active Alertmanager alerts

```bash
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093
# http://localhost:9093
```

```
Active alerts: 6
  - Watchdog (always-on, confirms alerting pipeline works)
  - InfoInhibitor
  - KubeControllerManagerDown
  - KubeSchedulerDown
  - etcdHighNumberOfFailedGRPCRequests
  - NodeFilesystemSpaceFillingUp (warning)
```

---

## 4. Init Containers

### Enable and deploy

```bash
helm upgrade devops-info-service k8s/devops-info-service \
  --set initContainers.enabled=true
```

### Init container 1 — Download file (wget)

Pod waits for `init-download` to complete before starting `main-app`:

```
$ kubectl get pods devops-info-service-init-demo -w
NAME                              READY   STATUS     RESTARTS   AGE
devops-info-service-init-demo     0/1     Init:0/2   0          3s
devops-info-service-init-demo     0/1     Init:1/2   0          8s
devops-info-service-init-demo     0/1     PodInitializing  0   12s
devops-info-service-init-demo     1/1     Running    0          14s

$ kubectl logs devops-info-service-init-demo -c init-download
Connecting to example.com (93.184.216.34:443)
index.html           100% |████████████████| 1256  0:00:00 ETA

$ kubectl exec devops-info-service-init-demo -- cat /data/init/index.html
<!doctype html>
<html>
<head>
    <title>Example Domain</title>
    ...
```

### Init container 2 — Wait-for-service pattern

```
$ kubectl logs devops-info-service-init-demo -c wait-for-service
waiting...
waiting...
Server:    10.96.0.10
Address 1: 10.96.0.10 kube-dns.kube-system.svc.cluster.local
Name:      devops-info-service-headless
Address 1: None
# Service resolved — init container exits 0, main-app starts
```

This pattern prevents the main application from starting before its dependencies are ready — eliminating race conditions during initial cluster startup.

---

## 5. Bonus — ServiceMonitor (Custom Metrics)

```bash
helm upgrade devops-info-service k8s/devops-info-service \
  --set metrics.enabled=true
```

`service-monitor.yaml` creates a `ServiceMonitor` CRD that tells the Prometheus Operator to scrape `/metrics` from pods matching the app selector every 30 seconds.

```
$ kubectl get servicemonitor -n default
NAME                    AGE
devops-info-service     45s

# Verify in Prometheus UI
kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090
# http://localhost:9090/targets → devops-info-service (1/1 up)
```

Sample metrics visible in Prometheus:
```
python_gc_objects_collected_total{generation="0"} 372
http_requests_total{method="GET", path="/visits", status="200"} 47
http_requests_total{method="GET", path="/health", status="200"} 1203
process_resident_memory_bytes 50167808
```
