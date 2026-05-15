# Lab 16 — Kubernetes monitoring & init containers

This document supports **kube-prometheus-stack** (Prometheus Operator, Prometheus, Grafana, Alertmanager, **kube-state-metrics**, **node-exporter**) and the **init containers** / **ServiceMonitor** additions in the `devops-python` Helm chart.

## 1. Stack components (Task 1)

| Component | Role |
|-----------|------|
| **Prometheus Operator** | CRDs + controllers: `Prometheus`, `Alertmanager`, `ServiceMonitor`, `PodMonitor`, … |
| **Prometheus** | TSDB + scrapers; discovers targets via `ServiceMonitor` selectors |
| **Alertmanager** | Alert routing, silencing, receivers (Slack, email, …) |
| **Grafana** | Dashboards; often bundled with Prometheus datasource |
| **kube-state-metrics** | Exposes K8s object state as metrics (Deployments, Pods, …) |
| **node-exporter** | Node CPU, memory, disk, network (host metrics) |

## 2. Installation (Helm)

```bash
chmod +x k8s/monitoring/install-kube-prometheus-stack.sh
./k8s/monitoring/install-kube-prometheus-stack.sh
```

Or manually (match your course’s release name — default **`monitoring`**):

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace
```

**Evidence (capture for your report):**

```bash
kubectl get pods,svc -n monitoring
```

Expected: Prometheus, Grafana, Alertmanager, Operator, kube-state-metrics, node-exporter pods eventually **Running**.

## 3. Grafana & dashboards (Task 2)

**Port-forward** (release name `monitoring`):

```bash
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
```

Open **http://localhost:3000**. If you installed with **`install-kube-prometheus-stack.sh`**, Grafana is set to **admin** / **admin** via `grafana.adminPassword`. For a cluster-default install without that flag, the password is often **prom-operator** or stored in a Secret:

```bash
kubectl get secret monitoring-grafana -n monitoring -o jsonpath='{.data.admin-password}' | base64 -d
echo
```

**Alertmanager UI:**

```bash
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093
```

### Dashboard questions (answer in Grafana — add screenshots to your submission)

Use built-in charts such as **Kubernetes / Compute Resources / Namespace (Pods)**, **Kubernetes / Compute Resources / Pod**, **Node Exporter / Nodes**, **Kubernetes / Kubelet**.

1. **Pod resources** — CPU/memory for your **StatefulSet** (or Rollout) pods in the target namespace.  
2. **Namespace** — Which **Pods** in `default` (or your app namespace) use the **most / least** CPU?  
3. **Nodes** — Memory (% and absolute), CPU cores (node exporter / cluster views).  
4. **Kubelet** — Pods/containers managed (Kubelet dashboards / summary panels).  
5. **Network** — Traffic for Pods in your namespace (where available in your stack version).  
6. **Alerts** — Count **firing** alerts in Grafana; cross-check in Alertmanager **/#/alerts**.

## 4. Init containers (Task 3)

The chart runs **two optional init containers** when `initContainers.enabled: true` (default):

1. **`wait-for-dns`** — loops until `nslookup` succeeds for **`kubernetes.default.svc.cluster.local`** (cluster DNS up).  
2. **`init-download`** — **`wget`** saves **`http://example.com`** to **`index.html`** on a shared **`emptyDir`** (`init-workdir`).

The main app container mounts that volume **read-only** at **`/init`** (file path **`/init/index.html`**).

**Verify:**

```bash
kubectl get pods -w
kubectl logs <pod> -c wait-for-dns
kubectl logs <pod> -c init-download
kubectl exec -it <pod> -c devops-python -- head -5 /init/index.html
```

Disable or tweak in **`values.yaml`** under **`initContainers.*`**.

## 5. Custom metrics & ServiceMonitor (bonus)

The Python app already exposes **`GET /metrics`** (`prometheus_client` from earlier labs).

Enable the chart’s **ServiceMonitor** (requires **Prometheus Operator** CRDs from kube-prometheus-stack):

```bash
helm upgrade --install myapp ./k8s/devops-python -n <app-namespace> \
  --set serviceMonitor.enabled=true \
  --set serviceMonitor.releaseLabel=monitoring
```

Or **`-f k8s/devops-python/values-servicemonitor.yaml`** (and ensure **`releaseLabel`** matches your kube-prometheus-stack Helm **release name**).

The `ServiceMonitor` selects the app **Service** by **`app.kubernetes.io/name`** / **`instance`** and scrapes **`port: http`**, **`path: /metrics`**.

**Prometheus UI:**

```bash
kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090
```

Check **Status → Targets** for your job; run **Explore** / **Graph** with e.g. `http_requests_total`.

## 6. References

- [kube-prometheus-stack](https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack)  
- [Init containers](https://kubernetes.io/docs/concepts/workloads/pods/init-containers/)  
- [ServiceMonitor](https://prometheus-operator.dev/docs/developer-guide/api/)  
