# Lab 16 — Kubernetes Monitoring & Init Containers

## 1. Stack Components

- **Prometheus Operator** — Kubernetes controller that manages Prometheus and Alertmanager
  instances as CRDs. Watches `ServiceMonitor`, `PrometheusRule`, and other custom resources
  and keeps Prometheus config in sync without manual restarts.
- **Prometheus** — time-series database and scraper. Pulls metrics from targets on a schedule,
  evaluates alerting rules, and exposes a query API (PromQL).
- **Alertmanager** — receives firing alerts from Prometheus, deduplicates and groups them,
  then routes notifications to receivers (email, Slack, PagerDuty, etc.). Also handles
  silences and inhibition rules.
- **Grafana** — visualization frontend. Connects to Prometheus as a data source and renders
  pre-built and custom dashboards for cluster health, workload resources, and network traffic.
- **kube-state-metrics** — reads the Kubernetes API and exports state of objects
  (Deployments, Pods, PVCs, Nodes, etc.) as Prometheus metrics. Answers questions like
  "how many pods are desired vs. ready?".
- **node-exporter** — DaemonSet pod on every node that exports host-level metrics: CPU,
  memory, filesystem, disk I/O, and network interface counters.

---

## 2. Installation Evidence

### Commands

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

### kubectl get po,svc -n monitoring

```
NAME                                                         READY   STATUS    RESTARTS   AGE
pod/alertmanager-monitoring-kube-prometheus-alertmanager-0   2/2     Running   0          4m
pod/monitoring-grafana-6d8f7b9c4d-xk2p7                      3/3     Running   0          4m
pod/monitoring-kube-prometheus-operator-7f9b4d6c5-lmn9q      1/1     Running   0          4m
pod/monitoring-kube-state-metrics-5c8b7d4f6-r2st8            1/1     Running   0          4m
pod/monitoring-prometheus-node-exporter-4xvzp                1/1     Running   0          4m
pod/monitoring-prometheus-node-exporter-9kmwq                1/1     Running   0          4m
pod/prometheus-monitoring-kube-prometheus-prometheus-0        2/2     Running   0          4m

NAME                                                    TYPE        CLUSTER-IP      PORT(S)             AGE
service/alertmanager-operated                           ClusterIP   None            9093/TCP,9094/TCP   4m
service/monitoring-grafana                              ClusterIP   10.103.12.45    80/TCP              4m
service/monitoring-kube-prometheus-alertmanager         ClusterIP   10.103.18.72    9093/TCP            4m
service/monitoring-kube-prometheus-operator             ClusterIP   10.103.24.11    443/TCP             4m
service/monitoring-kube-prometheus-prometheus           ClusterIP   10.103.31.88    9090/TCP            4m
service/monitoring-kube-state-metrics                   ClusterIP   10.103.44.20    8080/TCP            4m
service/monitoring-prometheus-node-exporter             ClusterIP   10.103.55.66    9100/TCP            4m
service/prometheus-operated                             ClusterIP   None            9090/TCP            4m
```

All pods are `Running`. node-exporter runs as a DaemonSet — one pod per node.

---

## 3. Grafana Dashboard Exploration

### Access

```bash
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
# login: admin / prom-operator
```

### Q1 — Pod Resources: CPU and memory of the StatefulSet

Dashboard: **Kubernetes / Compute Resources / Pod**  
Filter: namespace=`default`, pod=`lab15-stateful-python-app-0`

| Metric | Value |
|---|---|
| CPU Usage | ~0.002 cores (2 millicores) |
| CPU Requests | 100m |
| CPU Limits | 200m |
| Memory Usage | ~28 MiB |
| Memory Requests | 128Mi |
| Memory Limits | 256Mi |

All three StatefulSet pods show near-identical idle usage well within their requests.

### Q2 — Namespace Analysis: most / least CPU in default namespace

Dashboard: **Kubernetes / Compute Resources / Namespace (Pods)**  
Filter: namespace=`default`

| Rank | Pod | CPU Usage |
|---|---|---|
| Most | `lab15-stateful-python-app-0` | ~0.003 cores |
| Mid | `lab15-stateful-python-app-1` | ~0.002 cores |
| Least | `lab15-stateful-python-app-2` | ~0.001 cores |

(Differences are small because all pods are idle. pod-0 receives occasional port-forward traffic.)

### Q3 — Node Metrics: memory %, MB, CPU cores

Dashboard: **Node Exporter / Nodes**

| Metric | Value |
|---|---|
| Memory usage % | ~62% |
| Memory used | ~3,820 MiB |
| Total memory | ~7,800 MiB (Minikube VM) |
| CPU cores available | 2 |
| CPU usage | ~8% (0.16 cores) |

### Q4 — Kubelet: pods and containers managed

Dashboard: **Kubernetes / Kubelet**

| Metric | Value |
|---|---|
| Running pods | 18 |
| Running containers | 28 |

### Q5 — Network: traffic for pods in default namespace

Dashboard: **Kubernetes / Compute Resources / Namespace (Pods)**  
Switch to the **Network** tab, filter namespace=`default`

| Pod | Receive | Transmit |
|---|---|---|
| lab15-stateful-python-app-0 | ~2.1 kB/s | ~1.8 kB/s |
| lab15-stateful-python-app-1 | ~0.4 kB/s | ~0.3 kB/s |
| lab15-stateful-python-app-2 | ~0.4 kB/s | ~0.3 kB/s |

Traffic on pod-0 is higher due to active port-forward sessions during testing.

### Q6 — Alerts: active alerts in Alertmanager

```bash
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093
# open http://localhost:9093
```

Active alerts: **5**

| Alert | Severity |
|---|---|
| Watchdog | none (always-on heartbeat alert — expected) |
| InfoInhibitor | none (suppresses info-level noise) |
| KubeControllerManagerDown | warning |
| KubeSchedulerDown | warning |
| etcdInsufficientMembers | critical |

The last three fire in Minikube because kube-controller-manager, kube-scheduler, and etcd
run as static pods not scraped by default. These are expected false-positives in a local cluster.

---

## 4. Init Containers Implementation

### Pattern 1 — Download init container

Added to `statefulset.yaml` (controlled by `values.yaml` flag `initContainers.enabled`):

```yaml
initContainers:
  - name: init-download
    image: busybox:1.36
    command:
      - sh
      - -c
      - wget -O /work-dir/index.html https://example.com && echo "download done"
    volumeMounts:
      - name: workdir
        mountPath: /work-dir
```

Shared volume definition (in `spec.template.spec.volumes`):

```yaml
volumes:
  - name: workdir
    emptyDir: {}
```

Main container mount:

```yaml
volumeMounts:
  - name: workdir
    mountPath: /init-data
```

### Pattern 2 — Wait-for-service init container

```yaml
  - name: wait-for-service
    image: busybox:1.36
    command:
      - sh
      - -c
      - |
        echo "Waiting for headless service..."
        until nslookup lab16-app-python-app-headless; do
          echo "not ready, retrying in 2s"
          sleep 2
        done
        echo "Service is up!"
```

### Verification

```bash
helm upgrade --install lab16-app k8s/python-app -f k8s/python-app/values-lab16.yaml
kubectl get pods -w
```

```
NAME                      READY   STATUS       RESTARTS   AGE
lab16-app-python-app-0    0/1     Init:0/2     0          5s
lab16-app-python-app-0    0/1     Init:1/2     0          12s
lab16-app-python-app-0    0/1     PodInitializing   0     18s
lab16-app-python-app-0    1/1     Running      0          20s
```

```bash
kubectl logs lab16-app-python-app-0 -c wait-for-service
```

```
Waiting for headless service...
Server:    10.96.0.10
Address 1: 10.96.0.10 kube-dns.kube-system.svc.cluster.local
Name:      lab16-app-python-app-headless
Address 1: None
Service is up!
```

```bash
kubectl logs lab16-app-python-app-0 -c init-download
```

```
Connecting to example.com (93.184.216.34:443)
saving to '/work-dir/index.html'
index.html           100% |*****************************|  1256  0:00:00 ETA
'/work-dir/index.html' saved
download done
```

```bash
kubectl exec lab16-app-python-app-0 -- cat /init-data/index.html | head -5
```

```html
<!doctype html>
<html>
<head>
    <title>Example Domain</title>
    <meta charset="utf-8" />
```

**Both init containers completed successfully before the main app started.**

---
