# Lab 16 — Monitoring & Init Containers

## 1. Stack Components

- **Prometheus Operator** manages Prometheus-related custom resources and reconciles Prometheus and Alertmanager deployments.
- **Prometheus** scrapes metrics from the cluster and stores them as time-series data.
- **Alertmanager** receives alerts from Prometheus and shows active alert groups.
- **Grafana** provides dashboards for cluster, node, pod, and alert visualization.
- **kube-state-metrics** exports metrics describing Kubernetes resources such as pods, services, PVCs, and StatefulSets.
- **node-exporter** exports low-level node metrics such as CPU, memory, disk, and networking.

## 2. Installation Evidence

The monitoring stack was installed in the `monitoring` namespace with:

```bash
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring
```

Verification was performed with:

```bash
kubectl get po,svc -n monitoring
kubectl get po,sts,svc,pvc,cm -n monitoring
```

The screenshots show the main components in `Running` state, including Grafana, Prometheus, Alertmanager, the Operator, `kube-state-metrics`, and `node-exporter`.

### Screenshot — monitoring stack installation

![Task 1 Helm install](docs/screenshots/task_1_helm_upgrade_install.png)

### Screenshot — monitoring resources

![Task 1 resources](docs/screenshots/task_1_kubectl_get_pods.png)

## 3. Dashboard Answers

### 3.1 Pod Resources

The pod dashboard for `app-python-0` shows approximately:

- CPU usage: `0.000600`
- CPU requests: `0.100`
- CPU limits: `0.200`
- memory usage: `27.8 MiB`
- memory request: `128 MiB`
- memory limit: `256 MiB`

![Q1 pod resources](docs/screenshots/task_2_q1_1.png)

![Q1 pod networking](docs/screenshots/task_2_q1_2.png)

### 3.2 Namespace Analysis

In the `default` namespace:

- highest CPU among application pods: `app-python-2` (`0.000662`)
- lowest CPU among application pods: `app-python-1` (`0.000613`)
- lowest overall CPU: `demo-0` (`0`)

![Q2 namespace CPU](docs/screenshots/task_2_q2_1.png)

![Q2 namespace memory](docs/screenshots/task_2_q2_2.png)

### 3.3 Node Metrics

The node dashboard shows:

- memory usage: `48.8%`
- logical CPU cores: `8`
- approximately half of node RAM in use (`~4.9–5.0 GiB`)

![Q3 node metrics](docs/screenshots/task_2_q3.png)

### 3.4 Kubelet

The kubelet dashboard shows:

- Running Pods: `29`
- Running Containers: `64`
- Actual Volume Count: `120`
- Desired Volume Count: `120`

![Q4 kubelet](docs/screenshots/task_2_q4.png)

### 3.5 Network

For `app-python-0`:

- receive bandwidth: `1.45 kb/s`
- transmit bandwidth: `1.44 kb/s`
- no packet drops were observed

![Q5 networking](docs/screenshots/task_2_q5.png)

### 3.6 Alerts

Alertmanager showed **5 active alerts**:

- `1` Watchdog alert
- `4` alerts in `kube-system`

![Q6 active alerts](docs/screenshots/task_2_q6_1.png)

## 4. Init Containers

### 4.1 Download Pattern

A pod with an init container downloaded `http://example.com` into a shared `emptyDir` volume. The main container later accessed the downloaded file.

![Init download apply](docs/screenshots/task_3_kubectl_apply.png)

![Init download logs](docs/screenshots/task_3_kubectl_logs.png)

### 4.2 Wait-for-Service Pattern

A separate init container waited until `wait-backend.default.svc.cluster.local` became resolvable. Only after that did the main container start.

![Wait backend](docs/screenshots/task_3_kubectl_apply_get_pod.png)

![Init wait demo](docs/screenshots/task_3_kubectl_apply_init_wait_demo.png)

## 5. Bonus Status

The application already exposes `/metrics`, but the provided evidence set does not include a `ServiceMonitor` or Prometheus target validation. Therefore, the bonus task is not claimed here.