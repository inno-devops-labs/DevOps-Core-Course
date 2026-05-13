# Lab 16 Report — Kubernetes Monitoring & Init Containers

## 1. Overview

Lab 16 adds cluster observability with `kube-prometheus-stack` and extends the existing `k8s/devops-info` Helm chart with init containers and a `ServiceMonitor`.

Implemented files:

```text
k8s/devops-info/
├── templates/
│   ├── servicemonitor.yaml
│   └── statefulset.yaml
└── values-monitoring.yaml

k8s/MONITORING.md
```

The default chart behavior is unchanged. Lab 16 features are enabled only through:

```yaml
initContainers:
  enabled: true

serviceMonitor:
  enabled: true
```

## 2. Monitoring Stack Components

`Prometheus Operator` manages Prometheus, Alertmanager, ServiceMonitor, and related custom resources. It converts Kubernetes-native CRDs into running monitoring configuration.

`Prometheus` stores time-series metrics and evaluates PromQL queries and alerting rules.

`Alertmanager` receives alerts from Prometheus, groups them, applies silences/inhibition, and routes notifications.

`Grafana` visualizes Prometheus data through dashboards such as Kubernetes pod, namespace, node, and kubelet views.

`kube-state-metrics` exposes Kubernetes object state as metrics, for example pod readiness, Deployment replicas, StatefulSet status, and PVC state.

`node-exporter` exposes node-level OS metrics such as CPU, memory, filesystem, and network usage.

## 3. Installation

Commands used:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --version 65.8.1
```

Monitoring release:

```text
NAME: monitoring
NAMESPACE: monitoring
STATUS: deployed
REVISION: 1
```

Cluster monitoring resources:

```text
$ kubectl get po,svc -n monitoring -o wide

pod/alertmanager-monitoring-kube-prometheus-alertmanager-0   2/2   Running
pod/monitoring-grafana-69db76f9b4-jbmc6                      3/3   Running
pod/monitoring-kube-prometheus-operator-d5dbb45f9-tl58d      1/1   Running
pod/monitoring-kube-state-metrics-75c9d8f7c7-xzg9l           1/1   Running
pod/monitoring-prometheus-node-exporter-88vbg                1/1   Running
pod/prometheus-monitoring-kube-prometheus-prometheus-0       2/2   Running

service/monitoring-grafana                        ClusterIP   10.96.166.30    80/TCP
service/monitoring-kube-prometheus-alertmanager   ClusterIP   10.96.21.198    9093/TCP,8080/TCP
service/monitoring-kube-prometheus-prometheus     ClusterIP   10.96.135.218   9090/TCP,8080/TCP
service/monitoring-kube-state-metrics             ClusterIP   10.96.245.8     8080/TCP
service/monitoring-prometheus-node-exporter       ClusterIP   10.96.186.107   9100/TCP
```

Grafana access:

```bash
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
```

Open `http://127.0.0.1:3000`, login `admin / prom-operator`.

## 4. Application Deployment

The lab application was deployed as a StatefulSet in namespace `lab16`:

```bash
kind load docker-image app_python-devops-info:latest --name devops-lab
kubectl create namespace lab16

helm upgrade --install lab16 k8s/devops-info \
  -n lab16 \
  -f k8s/devops-info/values-monitoring.yaml
```

Verification:

```text
$ kubectl get po,sts,svc,pvc,servicemonitor -n lab16 -o wide

pod/lab16-devops-info-0   1/1   Running   0
pod/lab16-devops-info-1   1/1   Running   0
pod/lab16-devops-info-2   1/1   Running   0

statefulset.apps/lab16-devops-info   3/3   app_python-devops-info:latest

service/lab16-devops-info            NodePort    10.96.72.73   80:30090/TCP
service/lab16-devops-info-headless   ClusterIP   None          80/TCP

persistentvolumeclaim/data-volume-lab16-devops-info-0   Bound   100Mi   RWO   standard
persistentvolumeclaim/data-volume-lab16-devops-info-1   Bound   100Mi   RWO   standard
persistentvolumeclaim/data-volume-lab16-devops-info-2   Bound   100Mi   RWO   standard

servicemonitor.monitoring.coreos.com/lab16-devops-info
```

## 5. Grafana Dashboard Answers

The same values can be checked in Grafana dashboards:

- `Kubernetes / Compute Resources / Namespace (Pods)`
- `Kubernetes / Compute Resources / Pod`
- `Node Exporter / Nodes`
- `Kubernetes / Kubelet`

### 5.1 Pod Resources

StatefulSet pods in `lab16`:

| Pod | CPU cores | Memory |
|---|---:|---:|
| `lab16-devops-info-0` | `0.00152` | `27.81 MiB` |
| `lab16-devops-info-1` | `0.00150` | `27.75 MiB` |
| `lab16-devops-info-2` | `0.00166` | `27.75 MiB` |

PromQL:

```promql
rate(container_cpu_usage_seconds_total{namespace="lab16",pod=~"lab16-devops-info-.*",container="devops-info"}[2m])
container_memory_working_set_bytes{namespace="lab16",pod=~"lab16-devops-info-.*",container="devops-info"}
```

Screenshots:

![Lab 16 pod CPU usage](<lab16report/Screenshot 2026-05-13 at 12.36.26.png>)

![Lab 16 pod memory usage](<lab16report/Screenshot 2026-05-13 at 12.36.40.png>)

### 5.2 Namespace Analysis

The assignment asks for `default` namespace. In this cluster, `default` has no application pods, so the CPU query returned an empty vector:

```promql
kube_pod_info{namespace="default"}
sum by (pod) (rate(container_cpu_usage_seconds_total{namespace="default"}[2m]))
```

For the lab workload in `lab16`, the highest CPU pod was `lab16-devops-info-2` and the lowest was `lab16-devops-info-1`.

Screenshot:

![Default namespace CPU and memory have no data](<lab16report/Screenshot 2026-05-13 at 12.43.13.png>)

### 5.3 Node Metrics

Single kind node: `devops-lab-control-plane`.

| Metric | Value |
|---|---:|
| Memory used | `52.31%` |
| Memory used | `4099.84 MiB` |
| CPU cores | `10` |

PromQL:

```promql
(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100
(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / 1024 / 1024
machine_cpu_cores
```

Screenshot:

![Node Exporter node CPU and memory dashboard](<lab16report/Screenshot 2026-05-13 at 12.43.47.png>)

### 5.4 Kubelet

Kubelet metrics:

| Metric | Value |
|---|---:|
| Running pods | `42` |
| Running containers | `46` |
| Created containers | `18` |
| Exited containers | `42` |

PromQL:

```promql
kubelet_running_pods
kubelet_running_containers
```

Screenshots:

![Kubelet running pods and containers](<lab16report/Screenshot 2026-05-13 at 12.44.35.png>)

![Kubelet operation and storage panels](<lab16report/Screenshot 2026-05-13 at 12.44.43.png>)

### 5.5 Network

The `default` namespace had no pods, so receive/transmit traffic queries returned empty vectors:

```promql
sum by (pod) (rate(container_network_receive_bytes_total{namespace="default"}[2m]))
sum by (pod) (rate(container_network_transmit_bytes_total{namespace="default"}[2m]))
```

The lab app traffic is visible in `lab16`; Prometheus scrapes every pod on `/metrics`.

Screenshots:

![Lab 16 pod network usage](<lab16report/Screenshot 2026-05-13 at 12.36.48.png>)

![Lab 16 pod network and storage usage](<lab16report/Screenshot 2026-05-13 at 12.36.54.png>)

![Default namespace network has no data](<lab16report/Screenshot 2026-05-13 at 12.54.19.png>)

### 5.6 Alerts

Alertmanager access:

```bash
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093
```

Active alerts are visible in Alertmanager at `http://127.0.0.1:9093`.

At the time of the screenshots, Alertmanager showed active alerts grouped by namespace and receiver. The visible groups included kube-system and monitoring alerts such as `TargetDown`, `etcdMembersDown`, and `etcdInsufficientMembers`.

Screenshots:

![Alertmanager active alert groups](<lab16report/Screenshot 2026-05-13 at 12.58.33.png>)

![Alertmanager expanded kube-system alerts](<lab16report/Screenshot 2026-05-13 at 13.13.36.png>)

## 6. Init Containers

Lab 16 uses two init containers in the StatefulSet.

### 6.1 Wait-for-Service

The first init container waits until the main Service has a DNS record:

```yaml
initContainers:
  - name: wait-for-service
    image: busybox:1.36
    command:
      - sh
      - -c
      - |
        until nslookup "${SERVICE_NAME}"; do
          echo "waiting for ${SERVICE_NAME}"
          sleep 2
        done
```

Proof:

```text
$ kubectl logs lab16-devops-info-0 -n lab16 -c wait-for-service

Server:         10.96.0.10
Address:        10.96.0.10:53

Name:   lab16-devops-info.lab16.svc.cluster.local
Address: 10.96.72.73
```

### 6.2 Download Init Container

The second init container downloads `http://example.com` to an `emptyDir` volume shared with the main container:

```yaml
initContainers:
  - name: init-download
    image: busybox:1.36
    command:
      - sh
      - -c
      - |
        wget -O "${WORKDIR}/${FILE_NAME}" "${DOWNLOAD_URL}"
        ls -l "${WORKDIR}/${FILE_NAME}"
```

Proof:

```text
$ kubectl logs lab16-devops-info-0 -n lab16 -c init-download

Connecting to example.com (104.20.23.154:80)
saving to '/init-data/index.html'
index.html           100% |********************************|   528  0:00:00 ETA
'/init-data/index.html' saved
-rw-r--r--    1 1000     1000           528 May 13 08:57 /init-data/index.html
```

Main container can read the file:

```text
$ kubectl exec lab16-devops-info-0 -n lab16 -- head -n 5 /init-data/index.html

<!doctype html><html lang="en"><head><title>Example Domain</title>...
```

Pod description confirms both init containers completed:

```text
Init Containers:
  wait-for-service:
    State:      Terminated
    Reason:     Completed
    Exit Code:  0
  init-download:
    State:      Terminated
    Reason:     Completed
    Exit Code:  0
```

## 7. Bonus: Custom Metrics and ServiceMonitor

The Python app exposes `/metrics` using `prometheus-client`.

Implemented application metrics include:

- `http_requests_total`
- `http_request_duration_seconds`
- `http_requests_in_progress`
- `devops_info_endpoint_calls`
- `devops_info_system_collection_seconds`

The chart now renders a `ServiceMonitor`:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: lab16-devops-info
  labels:
    release: monitoring
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: devops-info
      app.kubernetes.io/instance: lab16
      app.kubernetes.io/monitoring: "true"
  endpoints:
    - port: http
      path: /metrics
      interval: 15s
```

Prometheus target verification:

```promql
up{namespace="lab16",service="lab16-devops-info"}
```

Result:

```text
pod="lab16-devops-info-0"   value=1
pod="lab16-devops-info-1"   value=1
pod="lab16-devops-info-2"   value=1
```

Custom metric verification:

```promql
http_requests_total{namespace="lab16"}
```

Result included `/health` and `/metrics` samples for all three pods, confirming that Prometheus scrapes the application through the `ServiceMonitor`.

