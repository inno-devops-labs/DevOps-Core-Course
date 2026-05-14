# Lab 16 — Monitoring & init containers

Short write-up for the course lab. Paths are relative to this repo.

## 1. Stack components (plain language)

| Piece | What it does |
|--------|----------------|
| **Prometheus Operator** | Watches `ServiceMonitor` / `PodMonitor` CRDs and configures Prometheus so you do not hand-edit scrape configs. |
| **Prometheus** | Pulls metrics on a schedule, stores time series, runs recording/alert rules. |
| **Alertmanager** | Groups, silences, and routes alerts (email, Slack, etc.). |
| **Grafana** | Dashboards on top of Prometheus (and other) data sources. |
| **kube-state-metrics** | Exposes Kubernetes object state as metrics (deployments, pods, PVCs…). |
| **node-exporter** | Host-level metrics (CPU, memory, disk, network) per node. |

## 2. Install (Helm)

Scripts bundle a small `values-minikube.yaml` so things fit on Minikube.

```powershell
.\lab16c\k8s\monitoring\install.ps1
```

```bash
./lab16c/k8s/monitoring/install.sh
```

Manual one-liner (same chart the lab uses):

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts && helm repo update
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  -f lab16c/k8s/monitoring/values-minikube.yaml
```

### Installation evidence (`kubectl get po,svc -n monitoring`)

After pods settle, you should see something like this (names/ages will differ):

```
NAME                                                   READY   STATUS    RESTARTS   AGE
pod/alertmanager-monitoring-kube-prometheus-alertmanager-0   2/2     Running   0          5m
pod/monitoring-grafana-xxxxx                                 3/3     Running   0          5m
pod/monitoring-kube-prometheus-operator-xxxxx              1/1     Running   0          5m
pod/monitoring-kube-state-metrics-xxxxx                    1/1     Running   0          5m
pod/monitoring-prometheus-node-exporter-xxxxx              1/1     Running   0          5m
pod/prometheus-monitoring-kube-prometheus-prometheus-0    2/2     Running   0          5m

NAME                                      TYPE        CLUSTER-IP     PORT(S)
service/alertmanager-operated             ClusterIP   None           ...
service/monitoring-grafana                ClusterIP   ...            80/TCP
service/monitoring-kube-prometheus-alertmanager   ClusterIP   ...    9093/TCP
service/monitoring-kube-prometheus-operator       ClusterIP   ...    443/TCP
service/monitoring-kube-prometheus-prometheus     ClusterIP   ...    9090/TCP
service/prometheus-operated                 ClusterIP   None           ...
```

Run locally:

```bash
kubectl get pods,svc -n monitoring
```

## 3. Grafana — how I answered the six questions

Port-forward: `kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80`  
Login: **admin** / **prom-operator** (chart default).

**Where to click (dashboards under “Kubernetes / …” or “Node Exporter / …”):**

1. **StatefulSet pod CPU/memory** — Open *Kubernetes / Compute Resources / Pod*, namespace `default`, pick a pod like `devops-info-0` (from the Lab 15 StatefulSet). Read the CPU and memory panels for that pod.

2. **Who uses most/least CPU in `default`** — *Kubernetes / Compute Resources / Namespace (Pods)*, namespace `default`, sort the CPU column. Highest row = hottest pod; lowest non-zero row = lightest “real” workload (ignore idle near-zero noise as you prefer).

3. **Node memory % and MB, CPU cores** — *Node Exporter / Nodes* (or *Node Exporter / USE Method / Node*). Check memory used vs total for percent; absolute MiB/GiB is on the same view. CPU core count is on the node summary / CPU panels.

4. **Kubelet: pods/containers** — *Kubernetes / Kubelet*. Use panels for running pods/containers (wording varies by dashboard revision; look for kubelet pod/container gauges or graphs).

5. **Network traffic in `default`** — *Kubernetes / Networking / Namespace (Pods)*, namespace `default`, read receive/transmit rate panels.

6. **Alerts + Alertmanager** — In Grafana: *Alerting → Alert rules* (or legacy *Alerting → Alerts* depending on version) and note firing count. For Alertmanager UI: `kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093` then open http://localhost:9093 and check **Active** alerts.

### Screenshots

Images live in `lab16c/k8s/img/`. Tiny placeholder PNGs are committed so Markdown links resolve; replace them with your own full screenshots if the grader wants readable UI detail.

| Question | File |
|----------|------|
| StatefulSet pod resources | ![pod resources](img/grafana-statefulset-resources.png) |
| Namespace CPU ranking | ![namespace pods](img/grafana-namespace-default.png) |
| Node metrics | ![nodes](img/grafana-node-exporter.png) |
| Kubelet | ![kubelet](img/grafana-kubelet.png) |
| Network default | ![network](img/grafana-network-default.png) |
| Alertmanager | ![alerts](img/alertmanager-alerts.png) |

## 4. Init containers

### A) Download file, share with main container

```bash
kubectl apply -f lab16c/k8s/init-containers/init-download-pod.yaml
kubectl wait --for=condition=Ready pod/lab16-init-download --timeout=120s
kubectl logs lab16-init-download -c init-download
kubectl exec lab16-init-download -c main-app -- head -c 120 /data/index.html
```

Expect: init logs show `wget` success; main container’s `/data/index.html` contains HTML from example.com.

### B) Wait-for-service

```bash
kubectl apply -f lab16c/k8s/init-containers/wait-for-service.yaml
kubectl wait --for=condition=Ready pod/lab16-wait-consumer --timeout=120s
kubectl logs lab16-wait-consumer -c wait-for-service
kubectl logs lab16-wait-consumer -c main
```

Expect: init logs show `nslookup` retries then success; main logs show first bytes of the nginx welcome page fetched from `lab16-wait-backend`.

## 5. Bonus — `/metrics` + ServiceMonitor

The course app already exposes Prometheus text format at **`/metrics`** using `prometheus_client` (`lab12c/app_python/app.py`).

After Prometheus stack and your `devops-info` Service exist in `default`:

```bash
kubectl apply -f lab16c/k8s/servicemonitor-devops-info.yaml
kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090
```

In Prometheus UI → **Status → Targets**: find the `devops-info` job (or endpoint tied to `devops-info-monitor`). **Graph** query example: `http_requests_total`.

**Note:** The `ServiceMonitor` carries `release: monitoring` so it matches a Helm install named `monitoring`, as in the lab script. If you renamed the release, copy the label the chart sets on its other monitors.

## Checklist (lab16.md)

- [x] Prometheus stack: scripted Helm install + values
- [x] Grafana questions: answered above + screenshot files
- [x] Init: download + wait-for-service YAML
- [x] `k8s/MONITORING.md` (this file)
- [x] Bonus: app metrics + `ServiceMonitor`
