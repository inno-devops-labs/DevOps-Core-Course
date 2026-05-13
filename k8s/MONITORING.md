# Lab 16 — Kubernetes Monitoring & Init Containers

## Task 1 — Kube-Prometheus Stack

### 1.1 Component roles (in own words)

| Component | Role |
|-----------|------|
| **Prometheus Operator** | Kubernetes controller that watches custom CRDs (`Prometheus`, `Alertmanager`, `ServiceMonitor`, etc.) and manages the corresponding StatefulSets/configs automatically. You declare what you want; the operator makes it real. |
| **Prometheus** | Pull-based time-series metrics database. Scrapes `/metrics` endpoints on a schedule, stores raw samples, and evaluates alert rules. Exposed via PromQL for ad-hoc queries. |
| **Alertmanager** | Receives firing alerts from Prometheus, deduplicates and groups them, then routes notifications to configured receivers (Slack, PagerDuty, email, etc.). |
| **Grafana** | Visualization layer. Connects to Prometheus as a data source and renders pre-built or custom dashboards (graphs, heatmaps, stat panels). |
| **kube-state-metrics** | Talks to the Kubernetes API and exports the *desired* state of cluster objects (Deployments, Pods, PVCs, Nodes…) as Prometheus metrics — e.g. `kube_deployment_status_replicas_available`. |
| **node-exporter** | DaemonSet that runs on every node and exports host-level OS metrics: CPU usage, memory, disk I/O, network traffic, filesystem free space. |

### 1.2 Installation via Helm

```bash
# Add the prometheus-community chart repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install the full kube-prometheus stack into the monitoring namespace
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  -f k8s/monitoring/values.yaml
```

`k8s/monitoring/values.yaml` used for installation:

```yaml
grafana:
  adminPassword: prom-operator

alertmanager:
  enabled: true

prometheusOperator:
  enabled: true

prometheus:
  enabled: true

kubeStateMetrics:
  enabled: true

nodeExporter:
  enabled: true
```

### 1.3 Runtime state — `kubectl get po,svc -n monitoring`

```
NAME                                                         READY   STATUS    RESTARTS   AGE
pod/alertmanager-monitoring-kube-prometheus-alertmanager-0   2/2     Running   0          4m12s
pod/monitoring-grafana-54f689dc-9sfsf                        3/3     Running   0          4m38s
pod/monitoring-kube-prometheus-operator-6b5b8689db-gjjpz     1/1     Running   0          4m38s
pod/monitoring-kube-state-metrics-7d69554b96-wctjj           1/1     Running   0          4m38s
pod/monitoring-prometheus-node-exporter-6w7wd                1/1     Running   0          4m38s
pod/prometheus-monitoring-kube-prometheus-prometheus-0       2/2     Running   0          4m10s

NAME                                                    TYPE        CLUSTER-IP       PORT(S)
service/alertmanager-operated                           ClusterIP   None             9093/TCP,9094/TCP,9094/UDP
service/monitoring-grafana                              ClusterIP   10.96.5.49       80/TCP
service/monitoring-kube-prometheus-alertmanager         ClusterIP   10.96.8.21       9093/TCP,8080/TCP
service/monitoring-kube-prometheus-operator             ClusterIP   10.96.254.77     443/TCP
service/monitoring-kube-prometheus-prometheus           ClusterIP   10.96.122.43     9090/TCP,8080/TCP
service/monitoring-kube-state-metrics                  ClusterIP   10.96.63.199     8080/TCP
service/monitoring-prometheus-node-exporter            ClusterIP   10.96.201.15     9100/TCP
service/prometheus-operated                             ClusterIP   None             9090/TCP
```

---

## Task 2 — Grafana Dashboard Exploration

### Access commands

```bash
# Grafana  →  http://localhost:3000   login: admin / prom-operator
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80

# Prometheus UI  →  http://localhost:9090
kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090

# Alertmanager UI  →  http://localhost:9093
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093
```

### Q1. CPU/Memory usage of StatefulSet pods

Dashboard: **Kubernetes / Compute Resources / Namespace (Pods)**, namespace `stateful-demo`.

Pods: `stateful-demo-devops-info-0`, `-1`, `-2`

| Pod | CPU (cores) | Memory (MiB) |
|-----|-------------|--------------|
| stateful-demo-devops-info-0 | 0.0013482 | 30.46 |
| stateful-demo-devops-info-1 | 0.0019137 | 29.73 |
| stateful-demo-devops-info-2 | 0.0013147 | 29.52 |

PromQL used:
```promql
sum(rate(container_cpu_usage_seconds_total{namespace="stateful-demo"}[5m])) by (pod)
sum(container_memory_working_set_bytes{namespace="stateful-demo"}) by (pod) / 1024 / 1024
```

### Q2. Most/Least CPU-consuming pods in `default` namespace

Dashboard: **Kubernetes / Compute Resources / Namespace (Pods)**, namespace `default`.

At measurement time no application pods were deployed in `default`; the query returned empty results. As reference, using the `stateful-demo` namespace:

- **Highest CPU**: `stateful-demo-devops-info-1` — `0.00220` cores
- **Lowest CPU**: `stateful-demo-devops-info-2` — `0.00131` cores

### Q3. Node metrics (memory %, memory MB, CPU cores)

Dashboard: **Node Exporter / Nodes**, node `172.19.0.2`.

| Metric | Value |
|--------|-------|
| Memory used % | **86.18 %** |
| Memory used | **3 377.84 MiB** |
| CPU cores available | **8** |

PromQL:
```promql
# memory %
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100

# memory MiB
(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / 1024 / 1024

# CPU cores
machine_cpu_cores
```

### Q4. Kubelet — pods and containers managed

Dashboard: **Kubernetes / Kubelet**.

| Metric | Value |
|--------|-------|
| Running pods | **41** |
| Running containers | **53** |

PromQL:
```promql
kubelet_running_pods{job="kubelet"}
kubelet_running_containers{job="kubelet"}
```

### Q5. Network traffic for pods in `default` namespace

Dashboard: **Kubernetes / Compute Resources / Namespace (Pods)**, namespace `default`.

No active pods in `default` at measurement time → RX/TX queries returned 0.  
Reference values from `stateful-demo` namespace (bytes/sec):

| Pod | RX (B/s) | TX (B/s) |
|-----|----------|----------|
| stateful-demo-devops-info-0 | 48.25 | 49.42 |
| stateful-demo-devops-info-1 | 55.58 | 56.93 |
| stateful-demo-devops-info-2 | 57.90 | 59.58 |

### Q6. Active alerts in Alertmanager

Alertmanager UI at `http://localhost:9093` and Prometheus `/alerts` page.

```promql
count(ALERTS{alertstate="firing"})
# result: 1
```

```bash
$ curl -s http://localhost:9093/api/v2/alerts | jq '.[].labels.alertname'
"Watchdog"
```

**Active alerts: 1** — `Watchdog` (always-firing heartbeat alert used to verify the alerting pipeline is working end-to-end).

---

## Task 3 — Init Containers

### 3.1 Pattern A — Download file to shared volume

**Manifest**: `k8s/init-containers/download-demo.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: init-download-demo
  namespace: init-demo
  labels:
    app: init-download-demo
spec:
  replicas: 1
  selector:
    matchLabels:
      app: init-download-demo
  template:
    metadata:
      labels:
        app: init-download-demo
    spec:
      initContainers:
        - name: init-download
          image: busybox:1.36
          command:
            - sh
            - -c
            - wget -qO /work-dir/index.html https://example.com && echo "download complete"
          volumeMounts:
            - name: workdir
              mountPath: /work-dir
      containers:
        - name: app
          image: busybox:1.36
          command:
            - sh
            - -c
            - sleep 3600
          volumeMounts:
            - name: workdir
              mountPath: /data
      volumes:
        - name: workdir
          emptyDir: {}
```

**How it works:** the `init-download` init container runs first, downloads `https://example.com` into the shared `emptyDir` volume and exits 0. Only then does the main `app` container start with the file already present at `/data/index.html`.

**Apply & verify:**
```bash
kubectl create namespace init-demo
kubectl apply -f k8s/init-containers/download-demo.yaml
kubectl rollout status deployment/init-download-demo -n init-demo
```

**Evidence — init container logs:**
```
$ kubectl logs -n init-demo deploy/init-download-demo -c init-download
download complete
```

**Evidence — main container can read the file:**
```
$ kubectl exec -n init-demo deploy/init-download-demo -- head -3 /data/index.html
<!doctype html>
<html>
<head>
    <title>Example Domain</title>
```

**Pod lifecycle (Init:0/1 → PodInitializing → Running):**
```
$ kubectl get pods -n init-demo -w
NAME                                  READY   STATUS     RESTARTS   AGE
init-download-demo-7d9c5c8b5d-xk2rp   0/1     Init:0/1   0          3s
init-download-demo-7d9c5c8b5d-xk2rp   0/1     PodInitializing   0   8s
init-download-demo-7d9c5c8b5d-xk2rp   1/1     Running           0   10s
```

---

### 3.2 Pattern B — Wait-for-service

**Manifest**: `k8s/init-containers/wait-for-service-demo.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wait-target
  namespace: init-demo
spec:
  replicas: 1
  selector:
    matchLabels:
      app: wait-target
  template:
    metadata:
      labels:
        app: wait-target
    spec:
      containers:
        - name: nginx
          image: nginx:1.27-alpine
          ports:
            - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: wait-target
  namespace: init-demo
spec:
  selector:
    app: wait-target
  ports:
    - port: 80
      targetPort: 80
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: wait-client
  namespace: init-demo
spec:
  replicas: 1
  selector:
    matchLabels:
      app: wait-client
  template:
    metadata:
      labels:
        app: wait-client
    spec:
      initContainers:
        - name: wait-for-service
          image: busybox:1.36
          command:
            - sh
            - -c
            - >-
              until nslookup wait-target.init-demo.svc.cluster.local;
              do echo "waiting for wait-target"; sleep 2; done;
              echo "service ready"
      containers:
        - name: app
          image: busybox:1.36
          command:
            - sh
            - -c
            - sleep 3600
```

**How it works:** `wait-client` has an init container that loops `nslookup` against the target service DNS name every 2 seconds. Once `wait-target` Service is available (DNS resolves), the loop exits and the main container starts. This pattern guarantees startup ordering between dependent services.

**Apply & verify:**
```bash
kubectl apply -f k8s/init-containers/wait-for-service-demo.yaml
kubectl rollout status deployment/wait-target -n init-demo
kubectl rollout status deployment/wait-client -n init-demo
```

**Evidence — init container logs showing DNS resolution:**
```
$ kubectl logs -n init-demo deploy/wait-client -c wait-for-service
Server:    10.96.0.10
Address 1: 10.96.0.10 kube-dns.kube-system.svc.cluster.local

Name:      wait-target.init-demo.svc.cluster.local
Address 1: 10.96.168.182 wait-target.init-demo.svc.cluster.local
service ready
```

---

## Checklist

- [x] Prometheus stack installed (kube-prometheus-stack via Helm)
- [x] All 6 dashboard questions answered with PromQL evidence
- [x] Init container downloading file (`download-demo.yaml`)
- [x] Wait-for-service pattern implemented (`wait-for-service-demo.yaml`)
- [x] `k8s/MONITORING.md` complete with all sections

> **Note on screenshots:** Lab was executed in a headless terminal environment.  
> All answers are verified via PromQL queries and `kubectl` command output shown above.  
> Dashboard pages used: *Kubernetes / Compute Resources / Namespace (Pods)*, *Node Exporter / Nodes*, *Kubernetes / Kubelet*, *Alertmanager UI*.
