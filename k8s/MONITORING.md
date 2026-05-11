# Lab — Monitoring, Grafana, Init Containers, and Custom Metrics

This document covers the kube-prometheus-stack, Grafana dashboard questions, init containers on the `devops-app` StatefulSet, and the Prometheus `ServiceMonitor` integration.

---

## 1. Stack components (roles in plain language)

| Component | Role |
|-----------|------|
| **Prometheus Operator** | Kubernetes controller that watches `Prometheus`, `Alertmanager`, `ServiceMonitor`, `PodMonitor`, and related CRDs. It generates Prometheus and Alertmanager configuration and manages their lifecycle so you configure monitoring declaratively instead of hand-editing `prometheus.yml`. |
| **Prometheus** | Time-series database and scraper. It pulls metrics from node exporters, kubelet, API objects (via kube-state-metrics), and any target you attach with a `ServiceMonitor`/`PodMonitor`. It stores samples and evaluates alerting rules. |
| **Alertmanager** | Receives firing alerts from Prometheus, deduplicates, groups, routes, and silences them, and sends notifications to receivers (email, Slack, PagerDuty, `null`, and so on). |
| **Grafana** | Visualization layer. It reads Prometheus (and other datasources), provides dashboards (for example *Kubernetes / Compute Resources / Namespace (Pods)*), and is where you answer most “what is the cluster doing?” questions interactively. |
| **kube-state-metrics** | Exposes Kubernetes object state as Prometheus metrics (Deployments, Pods, PVCs, and so on). Prometheus uses these series for cluster-level and workload-level dashboards and alerts. |
| **node-exporter** | DaemonSet (typically one Pod per node) that exposes hardware and OS metrics (CPU, memory, disk, network) from the node’s perspective. |

---

## 2. Installation (Helm)

Add the community chart repository and install the stack into the `monitoring` namespace (release name `monitoring` here matches the `ServiceMonitor` label used later):

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring
```

After install, confirm workloads:

```bash
kubectl get pods -n monitoring
kubectl get svc -n monitoring
```

### 2.1 Installation evidence (`kubectl get po,svc -n monitoring`)

Example output from this cluster (all Pods `Running`):

```text
NAME                                                     READY   STATUS    RESTARTS   AGE
pod/alertmanager-monitoring-kube-prometheus-alertmanager-0   2/2   Running   ...        ...
pod/monitoring-grafana-...                                 3/3   Running   ...        ...
pod/monitoring-kube-prometheus-operator-...                1/1   Running   ...        ...
pod/monitoring-kube-state-metrics-...                      1/1   Running   ...        ...
pod/monitoring-prometheus-node-exporter-...                1/1   Running   ...        ...
pod/prometheus-monitoring-kube-prometheus-prometheus-0      2/2   Running   ...        ...

NAME                                              TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)
service/alertmanager-operated                     ClusterIP   None            <none>        9093/TCP,9094/TCP,9094/UDP
service/monitoring-grafana                        ClusterIP   10.96.x.x       <none>        80/TCP
service/monitoring-kube-prometheus-alertmanager   ClusterIP   10.96.x.x       <none>        9093/TCP,8080/TCP
service/monitoring-kube-prometheus-operator       ClusterIP   10.96.x.x       <none>        443/TCP
service/monitoring-kube-prometheus-prometheus       ClusterIP   10.96.x.x       <none>        9090/TCP,8080/TCP
service/monitoring-kube-state-metrics               ClusterIP   10.96.x.x       <none>        8080/TCP
service/monitoring-prometheus-node-exporter         ClusterIP   10.96.x.x       <none>        9100/TCP
service/prometheus-operated                       ClusterIP   None            <none>        9090/TCP
```

---

## 3. Grafana and Alertmanager access

**Grafana** (default credentials are often `admin` / `prom-operator` unless you overrode them):

```bash
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
```

Open `http://localhost:3000`.

**Alertmanager UI**:

```bash
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093
```

Open `http://localhost:9093`.

Useful built-in dashboards (search in Grafana): *Kubernetes / Compute Resources / Namespace (Pods)*, *Kubernetes / Compute Resources / Pod*, *Node Exporter / Nodes*, *Kubernetes / Kubelet*.

---

## 4. Dashboard answers (six questions)

Numbers below were cross-checked with Prometheus on a single-node **kind**-style cluster at the time of writing. Your Grafana panels may differ slightly by time range and load, but ordering (which Pod is highest or lowest) should match when the workload is idle.

### 4.1 Pod resources — CPU and memory for the StatefulSet

**Question:** CPU and memory usage for the `devops-app` StatefulSet Pods.

**Answer (this cluster):**

- **CPU** (`sum by (pod)(rate(container_cpu_usage_seconds_total{namespace="default",container!=""}[5m]))`): highest **`devops-app-0`** (~0.00091 cores), lowest **`devops-app-1`** (~0.00084 cores); `devops-app-2` in between (~0.00090 cores).
- **Memory** (`container_memory_working_set_bytes` for app containers): highest **`devops-app-2`** (~26.5 MiB), lowest **`devops-app-1`** (~25.4 MiB).

**Grafana:** *Kubernetes / Compute Resources / Pod* — namespace `default`, Pod `devops-app-0` (repeat for `-1`, `-2`) or use Pod list filtered by workload.

**Screenshot:** ![StatefulSet pod compute](./screenshots/l16%202.1.png) (detail: ![Pod detail](./screenshots/l16%202.1.2.png))

---

### 4.2 Namespace analysis — which Pods use most / least CPU in `default`?

Only the three StatefulSet Pods were present in `default`.

**Answer:** **Most CPU:** `devops-app-0`. **Least CPU:** `devops-app-1`.

**Grafana:** *Kubernetes / Compute Resources / Namespace (Pods)* — namespace `default`, sort by CPU.

**Screenshot:** ![Namespace pods CPU](./screenshots/l16%202.2.png) (alternate view: ![Namespace pods](./screenshots/l16%202.2.2.png))

---

### 4.3 Node metrics — memory (% and MiB) and CPU cores

**Node:** single control-plane node (`desktop-control-plane` in metrics).

**Answer:**

- **Memory usage (approx.):** **~56.2%** used (from `(1 - MemAvailable / MemTotal) * 100` via node-exporter series).
- **Memory size:** **MemTotal ~8171651072 bytes** (~**7797 MiB**). At ~56% used, working set is on the order of **~4380 MiB** (derive: `MemTotal * used_ratio`; refresh in Grafana for exact MiB at your time).
- **CPU cores:** **12** logical cores (`count without(cpu, mode)(node_cpu_seconds_total{mode="idle"}))`.

**Grafana:** *Node Exporter / Nodes*.

**Screenshot:** ![Node metrics](./screenshots/l16%202.3.png)

---

### 4.4 Kubelet — how many Pods / containers managed?

From kubelet metrics on this node:

- **`kubelet_running_pods`:** **23**
- **`kubelet_running_containers`:** **27** in `container_state="running"` (other time series also report created/exited counts).

**Grafana:** *Kubernetes / Kubelet*.

**Screenshot:** ![Kubelet](./screenshots/l16%202.4.png)

---

### 4.5 Network — traffic for Pods in `default`

Using `sum by (pod)(rate(container_network_receive_bytes_total{namespace="default"}[5m]))` (receive rate as a simple traffic proxy):

**Answer:** **Highest receive rate:** `devops-app-0` (~310 B/s). **Lowest:** `devops-app-2` (~299 B/s). (`devops-app-1` ~308 B/s.)

**Grafana:** namespace-scoped networking panels or Prometheus explorer with the expression above.

**Screenshot:** ![Network default namespace](./screenshots/l16%202.5.png)

---

### 4.6 Alerts — how many active? Alertmanager UI

**Alertmanager API** (`GET /api/v2/alerts`) on this cluster returned **7** alerts in **`state: active`** at query time (mix of `TargetDown` on control-plane scrape targets in **kind**, `etcd*` rules, and the always-on **`Watchdog`** pipeline check).

**Answer:** **7 active alerts** (your count may change if targets recover or rules differ).

**Screenshot:** ![Alertmanager](./screenshots/l16%202.6.png)

---

## 5. Init containers (StatefulSet)

### 5.1 What was implemented

1. **Wait-for-service:** an init container loops with `wget` until `http://<service>.<namespace>.svc.cluster.local` returns data (dependency must be ready before the rest of the Pod starts).
2. **Download with `wget`:** a second init container writes a file into a shared **`emptyDir`** volume.
3. **Main app container:** mounts the same volume **read-only** at `/init-data` so the file is visible after startup.

Implementation (Helm template excerpt):

```38:87:k8s/devops-app/templates/statefulset.yaml
      {{- if .Values.initContainers.enabled }}
      initContainers:
        {{- if .Values.initContainers.wait.enabled }}
        - name: wait-for-dependency
          image: {{ .Values.initContainers.busyboxImage | quote }}
          command:
            - sh
            - -c
            - |
              url="http://{{ .Values.initContainers.wait.service }}.{{ .Values.initContainers.wait.namespace }}.svc.cluster.local:{{ .Values.initContainers.wait.port }}{{ .Values.initContainers.wait.path }}"
              echo "Waiting for $url"
              until wget -qO- "$url"; do
                echo "dependency not ready, sleeping..."
                sleep 2
              done
              echo "Dependency is reachable."
        {{- end }}
        {{- if .Values.initContainers.download.enabled }}
        - name: download-with-wget
          image: {{ .Values.initContainers.busyboxImage | quote }}
          command:
            - sh
            - -c
            - |
              set -e
              mkdir -p "{{ .Values.initContainers.download.mountPath }}"
              wget -qO "{{ .Values.initContainers.download.mountPath }}/{{ .Values.initContainers.download.filename }}" "{{ .Values.initContainers.download.url }}"
              ls -la "{{ .Values.initContainers.download.mountPath }}"
          volumeMounts:
            - name: init-data
              mountPath: {{ .Values.initContainers.download.mountPath }}
        {{- end }}
      {{- end }}
      containers:
        - name: {{ .Chart.Name }}
          ...
            {{- if .Values.initContainers.enabled }}
            - name: init-data
              mountPath: {{ .Values.initContainers.download.mountPath }}
              readOnly: true
            {{- end }}
```

Dependency Service and Deployment (apply **before** enabling init containers):

- Manifest: `k8s/monitoring/init-dependency.yaml` (nginx + `Service` `init-dependency`).

### 5.2 How to run the lab

```bash
kubectl apply -f k8s/monitoring/init-dependency.yaml
kubectl wait --for=condition=available deployment/init-dependency -n default --timeout=120s

helm upgrade --install devops-app ./k8s/devops-app -n default \
  --set service.nodePort=30081 \
  --set initContainers.enabled=true
```

If `busybox` or `nginx` images fail to pull (registry rate limits or air-gapped clusters), mirror them or override:

```bash
helm upgrade devops-app ./k8s/devops-app -n default \
  --set initContainers.busyboxImage=your-registry/library/busybox:1.36
```

### 5.3 Proof the main container sees the file

After Pods are `Ready`:

```bash
kubectl exec -n default sts/devops-app -c devops-app -- cat /init-data/init-downloaded.txt | head
```

You should see the beginning of the Prometheus `LICENSE` file downloaded in the init step.

Init container logs:

```bash
kubectl logs -n default devops-app-0 -c wait-for-dependency
kubectl logs -n default devops-app-0 -c download-with-wget
```

---

## 6. Bonus — application `/metrics` and `ServiceMonitor`

### 6.1 Application code

The Flask app already exposes Prometheus text exposition on **`/metrics`** using `prometheus_client`:

```191:193:app_python/app.py
@app.route("/metrics", methods=["GET"])
def metrics():
    return generate_latest(), 200, {'Content-Type': 'text/plain'}
```

**Important:** the chart default image `ray326sq/devops-info-python:lab03` may **not** include this route if it was built from an older commit. Build and push from `app_python` (see `app_python/Dockerfile`), bump `image.tag` in `values.yaml`, then redeploy. Until then, Prometheus may show targets as **down** for `/metrics` (for example HTTP **404**).

### 6.2 `ServiceMonitor` CRD

The chart renders a `ServiceMonitor` when `monitoring.serviceMonitor.enabled` is true. It selects the **primary** `Service` (`app.kubernetes.io/component: api`) and scrapes port name **`http`** on path **`/metrics`**.

The label **`release: monitoring`** must match your kube-prometheus-stack Helm **release name** (the value Prometheus uses in `serviceMonitorSelector`). If your release is named differently, set:

```yaml
monitoring:
  serviceMonitor:
    prometheusRelease: <your-prometheus-stack-release-name>
```

### 6.3 Verify in Prometheus UI

```bash
kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090
```

In the Prometheus UI: **Status → Targets** — look for `serviceMonitor/default/devops-app` (or search `devops-app`). After a good image build, run PromQL such as `http_requests_total{job="devops-app"}` or `devops_info_endpoint_calls`.

---

## 7. Checklist

| Item | Status |
|------|--------|
| Prometheus stack installed via Helm in `monitoring` | Done (see §2–2.1) |
| All six dashboard questions answered | Done (§4) |
| Screenshots included under `k8s/screenshots/` | Linked in §4 |
| Init container downloads a file with `wget` | Implemented in chart (§5) |
| Wait-for-service pattern | Implemented (§5) |
| `k8s/MONITORING.md` complete | This file |
| Bonus: `ServiceMonitor` + `/metrics` in source | `ServiceMonitor` in chart; `/metrics` in `app_python/app.py`; rebuild image to scrape successfully |

---

## 8. References in this repo

| Path | Purpose |
|------|---------|
| `k8s/devops-app/templates/servicemonitor.yaml` | `ServiceMonitor` for app scraping |
| `k8s/devops-app/templates/statefulset.yaml` | Init containers and shared `emptyDir` |
| `k8s/devops-app/values.yaml` | `monitoring.serviceMonitor.*`, `initContainers.*` |
| `k8s/monitoring/init-dependency.yaml` | Dependency Deployment + Service for wait loop |
| `app_python/app.py` | `/metrics` implementation |
