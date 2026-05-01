# Lab 16 — Kubernetes monitoring and init containers

This document describes the kube-prometheus stack, how to reach Grafana and Alertmanager, reproducible Prometheus queries that answer the Grafana exploration questions, init containers added to the `devops-info` chart, and ServiceMonitor-based scraping of `/metrics`.

**Evidence note:** Prometheus queries and `kubectl` output below were captured **2026-05-01** on minikube **`lab09`**, with **`monitoring`** installed in namespace **`monitoring`** and **`lab15`** (`devops-info` StatefulSet + ServiceMonitor) in namespace **`lab15`**.

---

## 1. Stack components

| Component | Role (short) |
|-----------|----------------|
| **Prometheus Operator** | Watches `Prometheus`, `Alertmanager`, `ServiceMonitor`, `PodMonitor`, etc., and reconciles their desired state (StatefulSets, configs, RBAC). |
| **Prometheus** | Time-series database and scraper: pulls metrics from targets (kubelet/cAdvisor, node-exporter, ServiceMonitors), evaluates recording/alert rules. |
| **Alertmanager** | Receives alerts from Prometheus, deduplicates, groups, routes to receivers (email, Slack, etc.). |
| **Grafana** | Dashboards on top of Prometheus (and other) datasources; kube-prometheus-stack ships many Kubernetes dashboards. |
| **kube-state-metrics** | Exposes Kubernetes object state as metrics (Pods, Deployments, PVCs, …) from the API; complements cAdvisor “how much CPU” with “what exists”. |
| **node-exporter** | Host-level metrics on each node (CPU, memory, disk, filesystem, basic hardware). |

---

## 2. Installation 

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --wait --timeout 15m
```

### 2.1 Verification — `kubectl get po,svc -n monitoring`

```text
NAME                                                         READY   STATUS    RESTARTS   AGE
pod/alertmanager-monitoring-kube-prometheus-alertmanager-0   2/2     Running   0          ...
pod/monitoring-grafana-688cfcb44-q5wdg                       3/3     Running   0          ...
pod/monitoring-kube-prometheus-operator-7456864f78-6tgsk    1/1     Running   0          ...
pod/monitoring-kube-state-metrics-5957bd45bc-z7ngr           1/1     Running   0          ...
pod/monitoring-prometheus-node-exporter-l9nkv                1/1     Running   0          ...
pod/prometheus-monitoring-kube-prometheus-prometheus-0       2/2     Running   0          ...

NAME                                              TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)
service/monitoring-grafana                        ClusterIP   10.101.250.138   <none>        80/TCP
service/monitoring-kube-prometheus-alertmanager   ClusterIP   10.98.250.192    <none>        9093/TCP,8080/TCP
service/monitoring-kube-prometheus-prometheus     ClusterIP   10.99.190.57     <none>        9090/TCP,8080/TCP
service/monitoring-kube-state-metrics             ClusterIP   10.106.199.172   <none>        8080/TCP
service/monitoring-prometheus-node-exporter       ClusterIP   10.107.198.65    <none>        9100/TCP
...
```

**Grafana:** `kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80` — default user **`admin`**, password from:

```bash
kubectl get secret --namespace monitoring -l app.kubernetes.io/component=admin-secret \
  -o jsonpath="{.items[0].data.admin-password}" | base64 --decode ; echo
```

(Legacy charts sometimes document **`prom-operator`**; this cluster used the generated secret above.)

**Prometheus UI:** `kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090`

**Alertmanager UI:** `kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093`

---

## 3. Grafana exploration — answers 

The rubric asks for **screenshots** from Grafana. For each item: open the suggested dashboard, reproduce the view, and export a PNG (share icon → Export → Save as PNG). Below, **Prometheus instant/range queries** give the same underlying numbers so answers stay reproducible without the UI.

### 3.1 StatefulSet pod resources (`lab15`, `lab15-devops-info-*`)

**Suggested Grafana dashboard:** *Kubernetes / Compute Resources / Pod* or *Namespace (Pods)*, namespace `lab15`.

**Prometheus (5m CPU rate, cores used):**

```promql
sum(rate(container_cpu_usage_seconds_total{namespace="lab15",pod=~"lab15-devops-info-.*"}[5m])) by (pod)
```

Observed (approximate cores per pod): `lab15-devops-info-0` ≈ **0.00183**, `-1` ≈ **0.00155**, `-2` ≈ **0.00180**.

**Working set memory (bytes → divide by 1024² for MiB):**

```promql
sum(container_memory_working_set_bytes{namespace="lab15",pod=~"lab15-devops-info-.*"}) by (pod)
```

Observed: `-0` ≈ **24 MiB**, `-1` ≈ **26 MiB**, `-2` ≈ **37 MiB** working set (rounded).

### 3.2 Default namespace — which pods use most / least CPU?

**Suggested Grafana dashboard:** *Kubernetes / Compute Resources / Namespace (Pods)*, namespace `default`.

```promql
topk(5, sum(rate(container_cpu_usage_seconds_total{namespace="default"}[5m])) by (pod))
```

Observed: three `devops-info-c45cbbfb8-*` pods; **highest** approximate rate: pod **`devops-info-c45cbbfb8-q5smb`** (~**0.00168** “cores” from the counter derivative), **lowest**: **`devops-info-c45cbbfb8-42lmn`** (~**0.00158**). Differences are small; range queries over time show spikes better than one instant vector.

### 3.3 Node metrics — memory (% and MB), CPU cores

**Suggested Grafana dashboard:** *Node Exporter / Nodes*.

**Memory fraction used (from node-exporter):**

```promql
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100
```

Observed: ~**86%** used on the sample node.

**Approximate “used” RAM (bytes):**

```promql
node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes
```

Observed: ~**7.15×10⁹** bytes ≈ **6818 MiB** used.

**Total RAM:**

```promql
node_memory_MemTotal_bytes
```

Observed: ~**8.32×10⁹** bytes ≈ **7936 MiB** total.

**Logical CPUs (node-exporter sample):**

```promql
count without(cpu, mode) (node_cpu_seconds_total{job="node-exporter",mode="idle"})
```

Observed: **10** “cpus” (hardware threads) on this VM.

### 3.4 Kubelet — pods / containers managed

**Suggested Grafana dashboard:** *Kubernetes / Kubelet*.

```promql
kubelet_running_pods{job="kubelet"}
```

Observed: **31** pods reported by kubelet on node `lab09`.

(Optional companion: `kubelet_running_containers{job="kubelet"}` when exposed.)

### 3.5 Network — traffic for pods in `default`

**Suggested Grafana dashboard:** *Kubernetes / Networking / Namespace* or pod networking panels.

**Prometheus note:** On this cluster, `container_network_receive_bytes_total` series filtered by `namespace="default"` returned **no samples** at capture time (cadvisor/kubelet networking metrics can be sparse depending on CNI, scrape config, or workload). Use Grafana’s pre-built panels (they often join kube-state-metrics labels) or validate after generating pod traffic.

Example query to try when series exist:

```promql
sum(rate(container_network_receive_bytes_total{namespace="default"}[5m])) by (pod)
```

### 3.6 Alerts — how many firing? Alertmanager UI

**Prometheus:**

```promql
count(ALERTS{alertstate="firing"})
```

Observed: **1** firing alert.

```promql
ALERTS{alertstate="firing"}
```

Observed: **`Watchdog`** (`severity="none"`) — a **deliberate “always firing”** probe from kube-prometheus to prove the alerting pipeline works; not an outage.

**Alertmanager:** after `port-forward` to `:9093`, the **Alerts** page lists the same active alerts.

---

## 4. Init containers 

Implemented in the Helm chart when `initContainers.enabled` is true (see **`k8s/devops-info/values-lab16.yaml`** and **`templates/_helpers.tpl`** definitions `devops-info.initContainers` / `devops-info.waitForServiceHost`). Both **Rollout** and **StatefulSet** pod templates mount an `emptyDir` **`init-workdir`** at **`/init-files`** (read-only) on the app container.

1. **`init-download`** — `busybox` + `wget` downloads **`values.initContainers.download.url`** into `/work-dir/` on the shared volume; the main container reads **`/init-files/index.html`**.
2. **`init-wait-service`** — loops until **`nslookup`** succeeds for the chart’s ClusterIP Service FQDN (`<fullname>.<namespace>.svc.cluster.local` by default), demonstrating wait-for-dependency DNS readiness before the app starts.

### 4.1 Proof (logs + file)

```bash
kubectl logs -n lab15 lab15-devops-info-0 -c init-download
kubectl logs -n lab15 lab15-devops-info-0 -c init-wait-service
kubectl exec -n lab15 lab15-devops-info-0 -- head -5 /init-files/index.html
```

Captured log lines:

```text
wget: note: TLS certificate validation not implemented
downloaded to /work-dir/index.html
waiting for DNS: lab15-devops-info.lab15.svc.cluster.local
DNS ready for lab15-devops-info.lab15.svc.cluster.local
```

First lines of **`/init-files/index.html`** match Example Domain HTML from `https://example.com`.

---

## 5. Bonus — custom metrics and ServiceMonitor

The Python service already exposes **`GET /metrics`** via `prometheus_client` (`app_python/app.py`).

**Helm:** `templates/servicemonitor.yaml` creates a `ServiceMonitor` when `serviceMonitor.enabled` is true. It must carry label **`release: monitoring`** (same string as the kube-prometheus-stack Helm release name) so the default Prometheus `serviceMonitorSelector` picks it up.

**Deploy app with Lab 16 values:**

```bash
helm upgrade --install lab15 ./k8s/devops-info \
  -n lab15 --create-namespace \
  -f k8s/devops-info/values-lab16.yaml
```

**Verify in Prometheus UI:** Status → Targets — jobs named like **`lab15-devops-info`** / **`lab15-devops-info-headless`** should be **UP**. Example query:

```promql
http_requests_total{namespace="lab15"}
```

Sample series included **`exported_endpoint="/metrics"`** and **`/health`**, confirming scraping hits the app.

---

## 6. Screenshots checklist 

![alt](/k8s/assets/Screenshot%202026-05-01%20at%2011.36.48.png)
![alt](/k8s/assets/Screenshot%202026-05-01%20at%2011.37.17.png)
![alt](/k8s/assets/Screenshot%202026-05-01%20at%2011.37.32.png)
![alt](/k8s/assets/Screenshot%202026-05-01%20at%2011.38.04.png)
![alt](/k8s/assets/Screenshot%202026-05-01%20at%2011.38.44.png)

---

## References

- [kube-prometheus-stack chart](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)
- [Init containers](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/)
- [ServiceMonitor](https://prometheus-operator.dev/docs/user-guides/getting-started/)
