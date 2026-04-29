# Lab 16 — Kubernetes Monitoring & Init Containers

## 1. Kube-Prometheus Stack

### Components

| Component | Role |
|-----------|------|
| **Prometheus Operator** | Manages Prometheus and Alertmanager instances via CRDs (`PrometheusRule`, `ServiceMonitor`, `AlertmanagerConfig`). Eliminates manual config file management. |
| **Prometheus** | Time-series metrics database. Scrapes targets defined by ServiceMonitors and PodMonitors. Evaluates alerting rules. |
| **Alertmanager** | Receives firing alerts from Prometheus. Routes, deduplicates, and silences them. Sends notifications to Slack, PagerDuty, email, etc. |
| **Grafana** | Visualization layer. Provides pre-built dashboards for Kubernetes, nodes, pods, and custom application metrics. |
| **kube-state-metrics** | Exposes Kubernetes object state as metrics (`kube_pod_status_phase`, `kube_deployment_replicas`, etc.). Does NOT collect resource usage — only object state. |
| **node-exporter** | Runs as a DaemonSet on every node. Exposes hardware and OS metrics: CPU, memory, disk, network. |

### Installation

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.adminPassword=admin

kubectl get pods -n monitoring
```

![All monitoring pods running](img/lab16/monitoring-pods.png)

---

## 2. Grafana Dashboard Exploration

### Access Grafana

```bash
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
# Open http://localhost:3000  —  admin / admin
```

### Q1 — CPU/Memory usage of the StatefulSet pod

Dashboard: **Kubernetes / Compute Resources / Pod** → select `python-app-sts-0`

![StatefulSet pod CPU and memory usage](img/lab16/grafana-pod-resources.png)

### Q2 — Which pods use most/least CPU in `default` namespace?

Dashboard: **Kubernetes / Compute Resources / Namespace (Pods)** → namespace: `default`

![CPU usage per pod in default namespace](img/lab16/grafana-namespace-cpu.png)

### Q3 — Node memory usage (% and MB) and CPU cores

Dashboard: **Node Exporter / Nodes**

![Node memory and CPU metrics](img/lab16/grafana-node-metrics.png)

### Q4 — How many pods/containers does Kubelet manage?

Dashboard: **Kubernetes / Kubelet**

![Kubelet pod and container count](img/lab16/grafana-kubelet.png)

### Q5 — Network traffic for pods in `default` namespace

Dashboard: **Kubernetes / Compute Resources / Namespace (Pods)** → Network tab → namespace: `default`

![Network receive/transmit per pod](img/lab16/grafana-network.png)

### Q6 — How many active alerts? Alertmanager UI

```bash
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093
# Open http://localhost:9093
```

![Alertmanager — active alerts](img/lab16/alertmanager-alerts.png)

---

## 3. Init Containers

### Template

The Pod manifest lives at `k8s/devops-python-chart/templates/init-pod.yaml`.

Enable it:

```bash
helm upgrade --install python-app ./k8s/devops-python-chart \
  --set initContainers.enabled=true
```

### Init Container 1 — File Download

Downloads a file from the internet and saves it to a shared `emptyDir` volume:

```yaml
initContainers:
  - name: init-download
    image: busybox:1.36
    command: ['sh', '-c', 'wget -O /work-dir/index.html https://example.com && echo "Download complete"']
    volumeMounts:
      - name: workdir
        mountPath: /work-dir
```

Watch the pod go through init stages:

```bash
kubectl get pods python-app-init-demo -w
```

![Pod transitioning through Init:0/2 → Init:1/2 → Running](img/lab16/init-pod-status.png)

Verify the file was downloaded and is accessible in the main container:

```bash
kubectl logs python-app-init-demo -c init-download
kubectl exec python-app-init-demo -- head -5 /data/index.html
```

![init-download logs and file content in main container](img/lab16/init-download-verify.png)

### Init Container 2 — Wait-for-Service Pattern

Blocks the main container from starting until the app's Service is resolvable via DNS:

```yaml
  - name: wait-for-service
    image: busybox:1.36
    command:
      - sh
      - -c
      - |
        until nslookup python-app.default.svc.cluster.local; do
          echo "Waiting for service..."
          sleep 2
        done
        echo "Service is ready"
```

Verify the wait-for-service init container logs:

```bash
kubectl logs python-app-init-demo -c wait-for-service
```

![wait-for-service logs showing retry then success](img/lab16/init-wait-verify.png)

**Use case:** Prevents the main application from starting before its dependency is available, eliminating startup race conditions.

---

## 4. Bonus — Custom Metrics & ServiceMonitor

### ServiceMonitor

The manifest `k8s/monitoring/servicemonitor.yaml` configures Prometheus to scrape the `/metrics` endpoint of the Python app.

```bash
kubectl apply -f k8s/monitoring/servicemonitor.yaml
```

### Verify in Prometheus UI

```bash
kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090
# Open http://localhost:9090
# Query: http_requests_total
```

![Custom app metrics visible in Prometheus](img/lab16/prometheus-metrics.png)

---

## 5. Summary

The Kube-Prometheus stack provides complete observability for Kubernetes clusters with minimal setup. Key takeaways:

1. **Prometheus** collects and stores metrics; **Grafana** visualizes them — together they answer questions about resource usage, saturation, and traffic.
2. **Alertmanager** closes the loop: alerts fire when metrics cross thresholds, routing notifications to the right team.
3. **node-exporter** and **kube-state-metrics** cover infrastructure and Kubernetes object state without any application changes.
4. **Init containers** solve dependency ordering — they run to completion before the main container starts, enabling safe file pre-population and service readiness checks.
5. **ServiceMonitor** integrates custom application metrics into the same Prometheus instance, giving full observability from infrastructure to business logic in a single tool.
