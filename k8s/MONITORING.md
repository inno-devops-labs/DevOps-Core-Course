# Lab 16 — Kubernetes Monitoring & Init Containers

Date: 2026-05-02

## 1. Stack Components

- Prometheus Operator: управляет CRD-ресурсами (`Prometheus`, `Alertmanager`, `ServiceMonitor`) и reconciliation мониторинг-стека.
- Prometheus: собирает и хранит метрики, выполняет PromQL-запросы.
- Alertmanager: принимает alert'ы от Prometheus и управляет их состоянием/маршрутизацией.
- Grafana: визуализирует метрики из Prometheus дашбордами.
- kube-state-metrics: публикует метрики состояния объектов Kubernetes API.
- node-exporter: публикует node-level метрики (CPU, memory, filesystem, network).

## 2. Installation Evidence

### 2.1 Install commands

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace
```

### 2.2 Runtime check (`kubectl get po,svc -n monitoring`)

```text
NAME                                                         READY   STATUS    RESTARTS   AGE
pod/alertmanager-monitoring-kube-prometheus-alertmanager-0   2/2     Running   0          2m56s
pod/monitoring-grafana-7dfb6dd6d-zmlw7                       3/3     Running   0          3m8s
pod/monitoring-kube-prometheus-operator-7fdc7f994c-bzwn5     1/1     Running   0          3m8s
pod/monitoring-kube-state-metrics-676c88cc4-t6ssj            1/1     Running   0          3m8s
pod/monitoring-prometheus-node-exporter-ssn7t                1/1     Running   0          3m8s
pod/monitoring-prometheus-node-exporter-wfgzx                1/1     Running   0          3m8s
pod/prometheus-monitoring-kube-prometheus-prometheus-0       2/2     Running   0          2m56s

NAME                                              TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)                      AGE
service/alertmanager-operated                     ClusterIP   None            <none>        9093/TCP,9094/TCP,9094/UDP   2m56s
service/monitoring-grafana                        ClusterIP   10.96.216.158   <none>        80/TCP                       3m8s
service/monitoring-kube-prometheus-alertmanager   ClusterIP   10.96.156.172   <none>        9093/TCP,8080/TCP            3m8s
service/monitoring-kube-prometheus-operator       ClusterIP   10.96.228.174   <none>        443/TCP                      3m8s
service/monitoring-kube-prometheus-prometheus     ClusterIP   10.96.240.216   <none>        9090/TCP,8080/TCP            3m8s
service/monitoring-kube-state-metrics             ClusterIP   10.96.244.10    <none>        8080/TCP                     3m8s
service/monitoring-prometheus-node-exporter       ClusterIP   10.96.168.51    <none>        9100/TCP                     3m8s
service/prometheus-operated                       ClusterIP   None            <none>        9090/TCP                     2m56s
```

## 3. Task 2 Dashboard Answers + Evidence

UI screenshots:
- 1) CPU/Memory StatefulSet `lab16`: `k8s/docs/screenshots/lab16-task2-statefulset-cpu-memory.png`
- 2) Most/least CPU in `default`: `k8s/docs/screenshots/lab16-task2-default-cpu-most-least.png`
- 3) Node metrics: `k8s/docs/screenshots/lab16-task2-node-metrics.png`
- 4) Kubelet pods/containers: `k8s/docs/screenshots/lab16-task2-kubelet-pods-containers.png`
- 5) Network traffic in `default`: `k8s/docs/screenshots/lab16-task2-default-network-traffic.png`
- 6) Alerts (Alertmanager): `k8s/docs/screenshots/lab16-task2-alerts.png`

All answers below were captured on 2026-05-02 from Prometheus (same datasource as Grafana dashboards).

1. Pod resources (StatefulSet `lab16`)
- PromQL CPU:
  - `sum(rate(container_cpu_usage_seconds_total{namespace="lab16",container!="",image!=""}[5m])) by (pod)`
- PromQL Memory MB:
  - `sum(container_memory_working_set_bytes{namespace="lab16",container!="",image!=""}) by (pod) / 1024 / 1024`
- Result:
  - CPU: `lab16-devops-info-python-0=0.001821`, `lab16-devops-info-python-1=0.001473`, `lab16-devops-info-python-2=0.001439`
  - Memory: `lab16-devops-info-python-2=27.95 MB`, `lab16-devops-info-python-0=27.45 MB`, `lab16-devops-info-python-1=27.37 MB`

2. Default namespace (most/least CPU)
- PromQL:
  - `sort_desc(sum(rate(container_cpu_usage_seconds_total{namespace="default",container!="",image!=""}[5m])) by (pod))`
- Result:
  - Most CPU: `devops-info-python-7c4f5b8b58-nc6sq=0.000150`
  - Least CPU: `devops-info-go-84f4f6c68b-wbx4c=0.000036`

3. Node metrics
- PromQL Memory %:
  - `100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))`
- PromQL Memory used MB:
  - `(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / 1024 / 1024`
- PromQL CPU cores:
  - `machine_cpu_cores`
- Result:
  - `172.19.0.2`: memory `85.82%`, used `5084.67 MB`, CPU cores `4`
  - `172.19.0.3`: memory `86.88%`, used `5147.49 MB`, CPU cores `4`

4. Kubelet managed pods/containers
- PromQL Pods:
  - `kubelet_running_pods`
- PromQL Containers:
  - `sum(kubelet_running_containers) by (instance)`
- Result:
  - `172.19.0.2`: pods `11`, containers `19`
  - `172.19.0.3`: pods `65`, containers `148`

5. Network traffic for default namespace pods (RX+TX bytes/s)
- PromQL:
  - `sort_desc(sum(rate(container_network_receive_bytes_total{namespace="default",pod!=""}[5m]) + rate(container_network_transmit_bytes_total{namespace="default",pod!=""}[5m])) by (pod))`
- Result:
  - `devops-info-python-7c4f5b8b58-nc6sq=104.51`
  - `devops-info-python-7c4f5b8b58-n6bmn=95.63`
  - `devops-info-go-84f4f6c68b-wbx4c=93.51`

6. Alerts (Alertmanager)
- UI screenshot: `k8s/docs/screenshots/lab16-task2-alerts.png`
- Result:
  - Active alerts: `1`
  - `InfoInhibitor`, state `active`, severity `none`

## 4. Init Containers

## 4.1 Implementation

Helm values for lab16: [values-lab16.yaml](devops-info-python/values-lab16.yaml)

Enabled patterns:
- `init-download`: скачивает `https://example.com` в shared `emptyDir` (`/init-data/index.html`)
- `wait-for-service`: ждёт DNS `kubernetes.default.svc.cluster.local`

Commands:

```bash
helm upgrade --install lab16 k8s/devops-info-python -n lab16 --create-namespace \
  -f k8s/devops-info-python/values-lab16.yaml
kubectl rollout status statefulset/lab16-devops-info-python -n lab16
```

## 4.2 Proof

Init download log:

```text
Connecting to example.com (104.20.23.154:443)
saving to '/init-data/index.html'
'/init-data/index.html' saved
```

Wait-for-service log:

```text
Name: kubernetes.default.svc.cluster.local
Address: 10.96.0.1
```

Main container reads downloaded file:

```bash
kubectl exec -n lab16 lab16-devops-info-python-0 -- head -n 1 /init-data/index.html
# <!doctype html><html lang="en"><head><title>Example Domain</title>...
```

## 5. Bonus — ServiceMonitor

Реализовано в Helm chart: [servicemonitor.yaml](devops-info-python/templates/servicemonitor.yaml)

Проверки:

```bash
kubectl get servicemonitor -n lab16
kubectl get servicemonitor -n lab16 -o yaml
```

Ключевые факты:
- `kind: ServiceMonitor` создан в namespace `lab16`
- label `release: monitoring` добавлен
- endpoint: `port: http`, `path: /metrics`

Prometheus scrape verification (`up{namespace="lab16"}`):
- endpoints for pods `lab16-devops-info-python-0/1/2` имеют `value=1` (UP)

Actual output:

```text
{"status":"success","data":{"resultType":"vector","result":[{"metric":{"__name__":"up","container":"devops-info-python","endpoint":"http","instance":"10.244.1.74:3000","job":"lab16-devops-info-python","namespace":"lab16","pod":"lab16-devops-info-python-0","service":"lab16-devops-info-python"},"value":[1777711900.731,"1"]},{"metric":{"__name__":"up","container":"devops-info-python","endpoint":"http","instance":"10.244.1.74:3000","job":"lab16-devops-info-python-headless","namespace":"lab16","pod":"lab16-devops-info-python-0","service":"lab16-devops-info-python-headless"},"value":[1777711900.731,"1"]},{"metric":{"__name__":"up","container":"devops-info-python","endpoint":"http","instance":"10.244.1.76:3000","job":"lab16-devops-info-python-headless","namespace":"lab16","pod":"lab16-devops-info-python-1","service":"lab16-devops-info-python-headless"},"value":[1777711900.731,"1"]},{"metric":{"__name__":"up","container":"devops-info-python","endpoint":"http","instance":"10.244.1.76:3000","job":"lab16-devops-info-python","namespace":"lab16","pod":"lab16-devops-info-python-1","service":"lab16-devops-info-python"},"value":[1777711900.731,"1"]},{"metric":{"__name__":"up","container":"devops-info-python","endpoint":"http","instance":"10.244.1.78:3000","job":"lab16-devops-info-python","namespace":"lab16","pod":"lab16-devops-info-python-2","service":"lab16-devops-info-python"},"value":[1777711900.731,"1"]},{"metric":{"__name__":"up","container":"devops-info-python","endpoint":"http","instance":"10.244.1.78:3000","job":"lab16-devops-info-python-headless","namespace":"lab16","pod":"lab16-devops-info-python-2","service":"lab16-devops-info-python-headless"},"value":[1777711900.731,"1"]}]}}
```

ServiceMonitor YAML fragment:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: lab16-devops-info-python
  namespace: lab16
  labels:
    release: monitoring
spec:
  endpoints:
  - interval: 30s
    path: /metrics
    port: http
    scrapeTimeout: 10s
  namespaceSelector:
    matchNames:
    - lab16
  selector:
    matchLabels:
      app.kubernetes.io/instance: lab16
      app.kubernetes.io/name: devops-info-python
```

## 6. Repro Commands

```bash
# Monitoring stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace

# Lab16 app + init containers + ServiceMonitor
helm upgrade --install lab16 k8s/devops-info-python -n lab16 --create-namespace \
  -f k8s/devops-info-python/values-lab16.yaml

# Quick checks
kubectl get po,svc -n monitoring
kubectl get po,svc,servicemonitor -n lab16
kubectl logs -n lab16 lab16-devops-info-python-0 -c init-download
kubectl exec -n lab16 lab16-devops-info-python-0 -- head -n 1 /init-data/index.html
```
