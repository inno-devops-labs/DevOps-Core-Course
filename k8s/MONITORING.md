# lab 16: kubernetes monitoring & init containers

## 1. kube-prometheus stack components

| component | purpose |
|-----------|---------|
| prometheus operator | manages prometheus/alertmanager/grafana lifecycle via crds (servicemonitors, prometheusrules). eliminates manual config reloads |
| prometheus | time-series database that scrapes metrics from targets, evaluates alerting rules, and serves queries |
| alertmanager | handles alerts from prometheus — deduplication, grouping, routing (email, slack, pagerduty), silencing, inhibition |
| grafana | visualization and dashboarding platform. queries prometheus/loki datasources and renders dashboards |
| kube-state-metrics | listens to kubernetes api server and exposes cluster state metrics (deployments, pods, pvc status, resource requests/limits) as prometheus metrics |
| node-exporter | daemonset that exposes hardware/os-level metrics from each node (cpu, memory, disk, network) |

---

## 2. installation evidence

### helm install

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

### pod and service verification

```bash
kubectl get po,svc -n monitoring
```

expected output:

```
NAME                                                         READY   STATUS    RESTARTS   AGE
pod/monitoring-grafana-xxxxxxxxxx-xxxxx                      3/3     Running   0          5m
pod/monitoring-kube-prometheus-operator-xxxxxxxxxx-xxxxx      1/1     Running   0          5m
pod/monitoring-kube-state-metrics-xxxxxxxxxx-xxxxx            1/1     Running   0          5m
pod/monitoring-prometheus-node-exporter-xxxxx                 1/1     Running   0          5m
pod/prometheus-monitoring-kube-prometheus-prometheus-0        2/2     Running   0          5m
pod/alertmanager-monitoring-kube-prometheus-alertmanager-0    2/2     Running   0          5m

NAME                                              TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)                      AGE
service/monitoring-grafana                        ClusterIP   10.x.x.x         <none>        80/TCP                       5m
service/monitoring-kube-prometheus-alertmanager   ClusterIP   10.x.x.x         <none>        9093/TCP                     5m
service/monitoring-kube-prometheus-operator       ClusterIP   10.x.x.x         <none>        443/TCP                      5m
service/monitoring-kube-prometheus-prometheus     ClusterIP   10.x.x.x         <none>        9090/TCP                     5m
service/monitoring-kube-state-metrics             ClusterIP   10.x.x.x         <none>        8080/TCP                     5m
service/monitoring-prometheus-node-exporter       ClusterIP   10.x.x.x         <none>        9100/TCP                     5m
```

---

## 3. grafana dashboard answers

### 3.1 pod resources: cpu/memory usage of statefulset

[cpu/memory usage](docs/screenshots/3.1.png)

### 3.2 namespace analysis: most/least cpu in default namespace

[memory and cpu cores](docs/screenshots/3.2.png)

### 3.3 node metrics: memory and cpu cores

[memory and cpu cores](docs/screenshots/3.3.png)

### 3.4 kubelet: pods and containers managed

[pods and containers managed](docs/screenshots/3.4.png)

### 3.5 network: traffic for pods in default namespace

[traffic for pods in default namespaces](docs/screenshots/3.5.png)

### 3.6 alerts: active alertmanager alerts

[alerts](docs/screenshots/3.6.png)

---

## 4. init containers

### 4.1 download init container

the init container downloads a file before the main app starts, making it available via a shared `emptydir` volume:

**template:** [statefulset.yaml](devops-info-service/templates/statefulset.yaml)

```yaml
initContainers:
  - name: init-download
    image: busybox:1.36
    command: ['sh', '-c', 'wget -O /work-dir/index.html "https://example.com"']
    volumeMounts:
      - name: workdir
        mountPath: /work-dir
```

the main container mounts the same `workdir` volume at `/data/init`:

```yaml
volumeMounts:
  - name: workdir
    mountPath: /data/init
    readOnly: true
```

**values configuration:**

```yaml
initContainers:
  download:
    enabled: true
    url: "https://example.com"
```

**verification:**

```bash
# watch init containers running
kubectl get pods -w
# devops-info-service-0   0/1     Init:0/2   0          1s
# devops-info-service-0   0/1     Init:1/2   0          3s
# devops-info-service-0   0/1     Init:2/2   0          5s
# devops-info-service-0   1/1     Running    0          7s

# check init container logs
kubectl logs devops-info-service-0 -c init-download

# verify the downloaded file is accessible in the main container
kubectl exec devops-info-service-0 -- cat /data/init/index.html
```

### 4.2 wait-for-service pattern

a second init container blocks startup until the headless service is dns-resolvable:

```yaml
initContainers:
  - name: wait-for-service
    image: busybox:1.36
    command: ['sh', '-c', 'until nslookup devops-info-service-headless; do echo waiting for devops-info-service-headless; sleep 2; done']
```

**values configuration:**

```yaml
initContainers:
  waitForService:
    enabled: true
    service: "devops-info-service-headless"
```

**verification:**

```bash
# the wait-for-service init container completes quickly since the headless service
# already exists when pods are being created
kubectl logs devops-info-service-0 -c wait-for-service
```

### 4.3 init container lifecycle

init containers run sequentially before any app container starts. if any init container fails, the pod restarts (on `restartpolicy: always`, which is the default). once all init containers complete successfully, they are never re-run.

```
pod startup sequence:
1. init-download      → downloads file to shared volume
2. wait-for-service   → blocks until dns resolves
3. main app container → starts with downloaded file available at /data/init
```

---

## 5. service monitor (bonus)

### 5.1 application metrics

the python app exposes a `/metrics` endpoint using `prometheus_client` ([metrics.py](../../app_python/metrics.py)):

| metric | type | labels | description |
|--------|------|--------|-------------|
| `http_requests_total` | counter | method, endpoint, status_code | total http requests |
| `http_request_duration_seconds` | histogram | method, endpoint | request latency distribution |
| `http_requests_active` | gauge | method, endpoint | currently in-flight requests |
| `app_info` | gauge | version, python_version | application version metadata |

### 5.2 servicemonitor crd

the `servicemonitor` tells the prometheus operator how to discover and scrape our app:

**template:** [service-monitor.yaml](devops-info-service/templates/service-monitor.yaml)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: devops-info-service
  labels:
    release: monitoring   # must match the prometheus release label
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: devops-info-service
  endpoints:
    - port: http
      path: /metrics
      interval: 15s
```

**key field:** `release: monitoring` — the prometheus operator is configured to select servicemonitors with this label. without it, the servicemonitor is ignored.

**values configuration:**

```yaml
serviceMonitor:
  enabled: true
  path: /metrics
  interval: 15s
```

### 5.3 verifying metrics in prometheus

```bash
# port-forward prometheus
kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090

# open http://localhost:9090 and query:
#   http_requests_total
#   http_request_duration_seconds_bucket
#   http_requests_active
```

alternatively via api:

```bash
curl -s 'http://localhost:9090/api/v1/query?query=http_requests_total' | python3 -m json.tool
```

---

## 6. chart structure (updated)

```
k8s/
├── devops-info-service/
│   ├── Chart.yaml
│   ├── values.yaml                          # init containers + service monitor config
│   ├── values-dev.yaml
│   ├── values-prod.yaml
│   └── templates/
│       ├── statefulset.yaml                 # now includes init containers
│       ├── service-monitor.yaml             # servicemonitor crd (new)
│       ├── headless-service.yaml
│       ├── deployment.yaml
│       ├── rollout.yaml
│       ├── preview-service.yaml
│       ├── analysis-template.yaml
│       ├── service.yaml
│       ├── pvc.yaml
│       ├── configmap.yaml
│       ├── secrets.yaml
│       ├── serviceaccount.yaml
│       ├── hooks/
│       └── _helpers.tpl
├── argocd/
│   └── ...
├── MONITORING.md                            # this documentation
├── STATEFULSET.md
├── ROLLOUTS.md
└── CONFIGMAPS.md
```

---

## 7. helm deployment

```bash
# deploy with monitoring enabled (default)
helm install devops-info-service ./k8s/devops-info-service

# deploy with init containers disabled
helm install devops-info-service ./k8s/devops-info-service \
  --set initContainers.download.enabled=false \
  --set initContainers.waitForService.enabled=false

# deploy with service monitor disabled
helm install devops-info-service ./k8s/devops-info-service \
  --set serviceMonitor.enabled=false

# install kube-prometheus-stack first
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

---

## 8. file references

| file | description |
|------|-------------|
| [statefulset.yaml](devops-info-service/templates/statefulset.yaml) | statefulset with init containers and volumeclaimtemplates |
| [service-monitor.yaml](devops-info-service/templates/service-monitor.yaml) | servicemonitor crd for prometheus scraping |
| [service.yaml](devops-info-service/templates/service.yaml) | service (nodeport) with http port for metrics |
| [values.yaml](devops-info-service/values.yaml) | helm values with init container and service monitor config |
| [metrics.py](../../app_python/metrics.py) | prometheus metrics definitions (red method) |
