# Monitoring — Lab 16

## Task 1 — Kube-Prometheus Stack Components

### Component Descriptions

**Prometheus Operator** — Kubernetes controller that manages Prometheus and Alertmanager instances as CRDs (`PrometheusRule`, `ServiceMonitor`, etc.). Automates deployment and configuration so you don't need to edit raw YAML every time scrape targets change.

**Prometheus** — Time-series database and scraping engine. Pulls metrics from targets on a schedule, stores them locally, and evaluates alerting rules. The central source of truth for cluster metrics.

**Alertmanager** — Receives firing alerts from Prometheus and handles routing, deduplication, silencing, and notification delivery (email, Slack, PagerDuty, etc.).

**Grafana** — Visualization frontend. Queries Prometheus (and other data sources) and renders dashboards with graphs, tables, and heatmaps. Provides the human-readable view of cluster health.

**kube-state-metrics** — Listens to the Kubernetes API and exposes metrics about object state: pod phases, deployment replica counts, node conditions, etc. Prometheus then scrapes this exporter.

**node-exporter** — DaemonSet that runs on every node and exposes hardware/OS-level metrics: CPU, memory, disk I/O, network. Gives visibility into the underlying machines, not just the workloads.

### Installation

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace

kubectl get pods -n monitoring
```

### Installation Evidence

`kubectl get po,svc -n monitoring` — все компоненты в `Running`:

![pods-and-services](./screenshots/lab16-monitoring-pods.png)

---

## Task 2 — Grafana Dashboard Exploration

**Доступ к Grafana:**
```bash
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
# Открыть: http://localhost:3000  (admin / prom-operator)
```

**Доступ к Alertmanager:**
```bash
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093
# Открыть: http://localhost:9093
```

### Q1 — CPU/Memory usage of StatefulSet

Dashboard: **Kubernetes / Compute Resources / Pod**, namespace `default`, pod `devops-info-service-0`.

![statefulset-resources](./screenshots/lab16-statefulset-resources.png)

### Q2 — Which pods use most/least CPU in default namespace?

Dashboard: **Kubernetes / Compute Resources / Namespace (Pods)**, namespace `default`. Данные по подам default namespace также видны на скриншоте StatefulSet выше ([lab16-statefulset-resources.png](./screenshots/lab16-statefulset-resources.png)).

**Ответ:** Больше всего CPU потребляет `init-download-pod` (~2m cores во время инициализации). Меньше всего — `monitoring-prometheus-node-exporter` (~0.1m cores в idle).

### Q3 — Node memory usage (% and MB) and CPU cores

Dashboard: **Node Exporter / Nodes**.

![node-metrics](./screenshots/lab16-node-metrics.png)

**Ответ:** Memory usage: ~62% (~3.7 GB из 6 GB). CPU: 4 cores, утилизация ~18%.

### Q4 — How many pods/containers managed by Kubelet?

Dashboard: **Kubernetes / Kubelet**.

![kubelet-metrics](./screenshots/lab16-kubelet.png)

**Ответ:** Running Pods: 18, Running Containers: 24.

### Q5 — Network traffic for pods in default namespace

Dashboard: **Kubernetes / Compute Resources / Namespace (Pods)**, namespace `default`, секция Network.

![network-traffic](./screenshots/lab16-network.png)

### Q6 — Active alerts in Alertmanager

```bash
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093
# Открыть: http://localhost:9093
```

![alertmanager](./screenshots/lab16-alertmanager.png)

**Ответ:** 8 active alerts (преимущественно Watchdog и InfoInhibitor — стандартные alerts kube-prometheus-stack).

---

## Task 3 — Init Containers

### 3.1 Basic Init Container (file preparation)

Манифест: [k8s/init-download.yaml](./init-download.yaml)

Init container создаёт файл в shared volume, main container читает его — паттерн демонстрирует передачу данных через `emptyDir` volume.

```yaml
spec:
  initContainers:
    - name: init-download
      image: busybox:1.36
      command: ['sh', '-c', 'echo "<html><body>Hello from init container</body></html>" > /work-dir/index.html && echo "File created"']
      volumeMounts:
        - name: workdir
          mountPath: /work-dir
  containers:
    - name: main-app
      image: busybox:1.36
      command: ['sh', '-c', 'echo "File contents:"; cat /data/index.html; sleep 3600']
      volumeMounts:
        - name: workdir
          mountPath: /data
  volumes:
    - name: workdir
      emptyDir: {}
```

**Apply и проверка:**
```bash
kubectl apply -f k8s/init-download.yaml
kubectl get pods -w                          # наблюдай переход Init:0/1 → Running
kubectl logs init-download-pod -c init-download
kubectl exec init-download-pod -- cat /data/index.html
```

![init-download](./screenshots/lab16-init-download.png)

### 3.2 Wait-for-Service Pattern

Манифест: [k8s/init-wait-for-service.yaml](./init-wait-for-service.yaml)

```yaml
initContainers:
  - name: wait-for-service
    image: busybox:1.36
    command: ['sh', '-c', 'until nslookup my-backend.default.svc.cluster.local; do echo "Waiting for my-backend..."; sleep 2; done; echo "Service is up!"']
```

Манифест создаёт:
- `Service/my-backend` — сервис, которого ждём
- `Pod/my-backend-pod` (nginx) — backend, который поднимается с небольшой задержкой
- `Pod/init-wait-pod` — под с init container, который ждёт DNS-резолюции сервиса

**Apply и проверка:**
```bash
kubectl apply -f k8s/init-wait-for-service.yaml
kubectl get pods -w                          # init-wait-pod сначала в Init:0/1
kubectl logs init-wait-pod -c wait-for-service
```

![init-wait](./screenshots/lab16-init-wait.png)
