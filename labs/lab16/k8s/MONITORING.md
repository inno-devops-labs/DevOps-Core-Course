# Lab 16 — Kubernetes Monitoring & Init Containers

## 1. Monitoring Stack Overview

This lab implements Kubernetes monitoring using the `kube-prometheus-stack` Helm chart and demonstrates init container patterns.

The monitoring stack includes Prometheus, Grafana, Alertmanager, kube-state-metrics, node-exporter, and the Prometheus Operator.

| Component | Purpose |
|---|---|
| Prometheus Operator | Manages Prometheus, Alertmanager, ServiceMonitor, and related CRDs |
| Prometheus | Collects, stores, and queries metrics |
| Alertmanager | Receives alerts from Prometheus and manages alert routing/silencing |
| Grafana | Provides dashboards and visualization for cluster metrics |
| kube-state-metrics | Exposes metrics about Kubernetes objects such as pods, deployments, nodes, PVCs |
| node-exporter | Exposes node-level Linux metrics such as CPU, memory, disk, and network |

---

## 2. Kube-Prometheus Stack Installation

The Prometheus community Helm repository was added:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

The stack was installed into the `monitoring` namespace:

```bash
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

Verification:

```bash
kubectl get pods -n monitoring
kubectl get svc -n monitoring
```

Output:

```text
NAME                                                     READY   STATUS    RESTARTS   AGE
alertmanager-monitoring-kube-prometheus-alertmanager-0   2/2     Running   0          9m9s
monitoring-grafana-5987445f7d-pm7b2                      3/3     Running   0          9m26s
monitoring-kube-prometheus-operator-646fb7bdb-ckm45      1/1     Running   0          9m26s
monitoring-kube-state-metrics-5746795bd9-r2pst           1/1     Running   0          9m26s
monitoring-prometheus-node-exporter-bcmg9                1/1     Running   0          9m26s
prometheus-monitoring-kube-prometheus-prometheus-0       2/2     Running   0          9m9s
```

Services:

```text
NAME                                      TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)
alertmanager-operated                     ClusterIP   None            <none>        9093/TCP,9094/TCP,9094/UDP
monitoring-grafana                        ClusterIP   10.96.112.60    <none>        80/TCP
monitoring-kube-prometheus-alertmanager   ClusterIP   10.96.130.28    <none>        9093/TCP,8080/TCP
monitoring-kube-prometheus-operator       ClusterIP   10.96.52.198    <none>        443/TCP
monitoring-kube-prometheus-prometheus     ClusterIP   10.96.152.251   <none>        9090/TCP,8080/TCP
monitoring-kube-state-metrics             ClusterIP   10.96.91.33     <none>        8080/TCP
monitoring-prometheus-node-exporter       ClusterIP   10.96.67.167    <none>        9100/TCP
prometheus-operated                       ClusterIP   None            <none>        9090/TCP
```

---

## 3. Grafana Access

Grafana was accessed using port-forwarding:

```bash
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
```

URL:

```text
http://localhost:3000
```

The Grafana password was retrieved from the Kubernetes Secret:

```bash
kubectl get secret -n monitoring monitoring-grafana \
  -o jsonpath="{.data.admin-password}" | base64 -d && echo
```

Login:

```text
username: admin
password: from monitoring-grafana secret
```

---

## 4. Dashboard Exploration

### 4.1 Pod Resources

Dashboard used:

```text
Kubernetes / Compute Resources / Namespace (Pods)
```

Namespace selected:

```text
stateful
```

Observed StatefulSet pods:

```text
stateful-app-devops-info-service-0
stateful-app-devops-info-service-1
stateful-app-devops-info-service-2
```

Observed values from Grafana:

```text
CPU utilisation: approximately 3.57%
Memory utilisation: approximately 26.1%
```

The dashboard showed CPU and memory usage for the StatefulSet pods.

Screenshot:

```text
labs/lab16/screenshots/grafana-stateful-resources.png
```

---

### 4.2 Namespace Analysis

The same dashboard was used to compare pods inside the `stateful` namespace.

Observed CPU usage examples:

```text
stateful-app-devops-info-service-0   ~0.00363
stateful-app-devops-info-service-1   ~0.00348
stateful-app-devops-info-service-2   ~0.00327
```

The pods had similar CPU usage, with pod `stateful-app-devops-info-service-0` using slightly more CPU during the observed period.

---

### 4.3 Node Metrics

Dashboard used:

```text
Node Exporter / Nodes
```

Observed:
- CPU usage graphs
- Load average graphs
- Memory usage graph
- Memory usage percentage

Observed value:

```text
Memory usage: approximately 79.2%
```

Screenshot:

```text
labs/lab16/screenshots/grafana-node-exporter.png
```

---

### 4.4 Kubelet Metrics

Dashboard used:

```text
Kubernetes / Kubelet
```

Observed values:

```text
Running nodes: 1
Running pods: 28
Running containers: 32
Actual volume count: 88
Desired volume count: 88
```

Screenshot:

```text
labs/lab16/screenshots/grafana-kubelet.png
```

---

### 4.5 Network Metrics

Network traffic was checked through Kubernetes compute resource dashboards.

The dashboards provided pod-level and namespace-level resource visibility, including network-related panels for transmit and receive traffic.

This confirms that Prometheus and Grafana were collecting Kubernetes workload metrics.

---

### 4.6 Alerts

Alertmanager was accessed using:

```bash
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093
```

URL:

```text
http://localhost:9093
```

Observed alerts:

```text
1 alert in the default group
5 alerts in kube-system namespace
```

Screenshot:

```text
labs/lab16/screenshots/alertmanager-alerts.png
```

---

## 5. Prometheus UI

Prometheus was accessed using:

```bash
kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090
```

URL:

```text
http://localhost:9090
```

The `Status -> Targets` page was used to verify that Prometheus was scraping targets successfully.

Observed targets included:

```text
monitoring-grafana
monitoring-kube-prometheus-alertmanager
```

Target state:

```text
UP
```

Screenshot:

```text
labs/lab16/screenshots/prometheus-targets.png
```

---

## 6. Init Containers Overview

Init containers run before the main application container.

They are useful for:
- downloading files
- preparing configuration
- waiting for dependencies
- database migrations
- validating environment state before application startup

The main container starts only after all init containers complete successfully.

---

## 7. Init Container — Download Pattern

A pod was created with an init container that writes an HTML file into a shared `emptyDir` volume.

Manifest location:

```text
labs/lab16/k8s/init-containers/init-download.yaml
```

The init container:

```yaml
initContainers:
  - name: init-download
    image: busybox:1.36
    command:
      - sh
      - -c
      - |
        echo "Init container started"
        echo "<html><body><h1>Downloaded by init container</h1></body></html>" > /work-dir/index.html
        echo "Init container completed"
```

The main container mounted the same shared volume at `/data`.

Apply command:

```bash
kubectl apply -f labs/lab16/k8s/init-containers/init-download.yaml
```

Verification:

```bash
kubectl logs init-download-demo -c init-download
kubectl exec init-download-demo -- cat /data/index.html
```

Output:

```text
Init container started
Init container completed
```

The main container successfully accessed the file:

```html
<html><body><h1>Downloaded by init container</h1></body></html>
```

This proves that the init container completed first and shared generated data with the main container.

---

## 8. Init Container — Wait-for-Service Pattern

A second example implemented a wait-for-service pattern.

Manifest location:

```text
labs/lab16/k8s/init-containers/init-wait-service.yaml
```

The init container waited until `dependency-service.default.svc.cluster.local` resolved through Kubernetes DNS.

Apply command:

```bash
kubectl apply -f labs/lab16/k8s/init-containers/init-wait-service.yaml
```

Verification:

```bash
kubectl logs wait-for-service-demo -c wait-for-service
```

Output:

```text
Waiting for dependency-service DNS...
Server:         10.96.0.10
Address:        10.96.0.10:53

Name:   dependency-service.default.svc.cluster.local
Address: 10.96.27.77

Dependency service is available
```

This proves that the main container started only after the dependency service was available.

This pattern is useful when an application depends on:
- a database
- another API service
- message broker
- cache service
- internal dependency endpoint

---

## 9. Challenges and Solutions

### Grafana Default Password

The common default password `prom-operator` did not work.

Solution:

The actual admin password was retrieved from the Grafana Kubernetes Secret:

```bash
kubectl get secret -n monitoring monitoring-grafana \
  -o jsonpath="{.data.admin-password}" | base64 -d && echo
```

---

### Alertmanager Image Pull Delay

Alertmanager initially showed:

```text
ImagePullBackOff
```

The pod later recovered automatically after Kubernetes retried pulling the image.

Final state:

```text
alertmanager-monitoring-kube-prometheus-alertmanager-0   2/2   Running
```

---

### Dashboard Namespace Selection

Some Grafana panels initially showed `No data` because the selected namespace was `argo-rollouts`.

Solution:

The namespace filter was changed to:

```text
stateful
```

After selecting the correct namespace, CPU and memory metrics appeared.

---

## 10. Screenshots

Screenshots are stored in:

```text
labs/lab16/screenshots/
```

Included screenshots:

```text
grafana-stateful-resources.png
grafana-node-exporter.png
grafana-kubelet.png
alertmanager-alerts.png
prometheus-targets.png
```

---

## 11. Summary

This lab successfully implemented Kubernetes monitoring and init container patterns.

Completed:

- kube-prometheus-stack installation
- Prometheus deployment
- Grafana dashboard access
- Alertmanager access
- node-exporter metrics
- kube-state-metrics
- pod CPU and memory monitoring
- node CPU and memory monitoring
- kubelet metrics
- Prometheus target verification
- init container download pattern
- wait-for-service init container pattern

The Kubernetes cluster now has a production-style observability stack and working init container examples.
