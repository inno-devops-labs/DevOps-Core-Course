# Lab 16 — Kubernetes Monitoring & Init Containers

## 1. Stack components (in own words)

- **Prometheus Operator**: watches CRDs and manages Prometheus/Alertmanager/Grafana-related resources declaratively.
- **Prometheus**: time-series database + PromQL engine for metrics collection and querying.
- **Alertmanager**: receives alerts from Prometheus rules, groups/deduplicates/routes notifications.
- **Grafana**: visualization UI over Prometheus metrics (dashboards, panels, queries).
- **kube-state-metrics**: exports Kubernetes object state (deployments, pods, PVCs, etc.) as metrics.
- **node-exporter**: exports host/node OS metrics (CPU, memory, filesystem, network).

## 2. Installation evidence

### Install
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace -f k8s/monitoring/values.yaml
```

### Access
```bash
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
# login: admin / prom-operator

kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090:9090
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093
```

### Runtime state
```bash
$ kubectl get po,svc -n monitoring
NAME                                                         READY   STATUS
pod/alertmanager-monitoring-kube-prometheus-alertmanager-0   2/2     Running
pod/monitoring-grafana-54f689dc-9sfsf                        3/3     Running
pod/monitoring-kube-prometheus-operator-6b5b8689db-gjjpz     1/1     Running
pod/monitoring-kube-state-metrics-7d69554b96-wctjj           1/1     Running
pod/monitoring-prometheus-node-exporter-6w7wd                1/1     Running
pod/prometheus-monitoring-kube-prometheus-prometheus-0       2/2     Running

NAME                                              TYPE
service/monitoring-grafana                        ClusterIP
service/monitoring-kube-prometheus-alertmanager   ClusterIP
service/monitoring-kube-prometheus-prometheus     ClusterIP
service/monitoring-kube-state-metrics             ClusterIP
service/monitoring-prometheus-node-exporter       ClusterIP
```

## 3. Dashboard questions (answered via Prometheus data)

### Q1. CPU/memory usage of StatefulSet pods
Namespace: `stateful-demo`, pods `stateful-demo-devops-info-{0,1,2}`.

CPU (cores/sec):
- `stateful-demo-devops-info-1`: `0.0019137`
- `stateful-demo-devops-info-0`: `0.0013482`
- `stateful-demo-devops-info-2`: `0.0013147`

Memory (MiB):
- `stateful-demo-devops-info-1`: `29.73`
- `stateful-demo-devops-info-0`: `30.46`
- `stateful-demo-devops-info-2`: `29.52`

### Q2. Most/least CPU pods in `default` namespace
PromQL for `default` returned empty results because no application pods were running in `default` at measurement time.

Supplementary sample (stateful namespace):
- highest CPU: `stateful-demo-devops-info-1` (`0.0021957`)
- lowest CPU: `stateful-demo-devops-info-2` (`0.0013580`)

### Q3. Node metrics (memory %, memory MB, CPU cores)
- node `172.19.0.2:9100` memory used: `86.18%`
- node `172.19.0.2:9100` memory used: `3377.84 MiB`
- node `172.19.0.2:10250` CPU cores: `8`

### Q4. Kubelet managed pods/containers
- running pods: `41`
- running containers: `53`

### Q5. Network traffic in `default` namespace
`default` namespace had no active workload pods at measurement time, so RX/TX query results were empty.

Supplementary sample for `stateful-demo` (bytes/sec):
- RX: pod0 `48.25`, pod1 `55.58`, pod2 `57.90`
- TX: pod0 `49.42`, pod1 `56.93`, pod2 `59.58`

### Q6. Active alerts (Alertmanager)
- Prometheus `count(ALERTS{alertstate="firing"})`: `1`
- Alertmanager `/api/v2/alerts`: `1`
- firing alert name: `Watchdog`

## 4. Init containers

Implemented manifests:
- `k8s/init-containers/download-demo.yaml`
- `k8s/init-containers/wait-for-service-demo.yaml`

Applied in namespace `init-demo`:
```bash
kubectl create namespace init-demo
kubectl apply -f k8s/init-containers
kubectl rollout status deployment/init-download-demo -n init-demo
kubectl rollout status deployment/wait-client -n init-demo
```

### Pattern A: download file to shared volume
`init-download` container downloads `https://example.com` into `emptyDir`, then main container reads it.

Evidence:
```bash
$ kubectl logs -n init-demo deploy/init-download-demo -c init-download
download complete

$ kubectl exec -n init-demo deploy/init-download-demo -- head -n 3 /data/index.html
<!doctype html><html lang="en"><head><title>Example Domain</title>...
```

### Pattern B: wait for service
`wait-for-service` init container loops until DNS resolves `wait-target.init-demo.svc.cluster.local`.

Evidence:
```bash
$ kubectl logs -n init-demo deploy/wait-client -c wait-for-service
Name: wait-target.init-demo.svc.cluster.local
Address: 10.96.168.182
service ready
```

## 5. Screenshots requirement

Execution was done in a headless environment, so verification is provided via command output above.
If screenshots are required for submission, capture these UI pages:
1. Grafana dashboards (`Kubernetes / Compute Resources / Namespace (Pods)`, `Node Exporter / Nodes`, `Kubernetes / Kubelet`)
2. Alertmanager active alerts page
3. Init container pod details (`Init:` phase + container logs)
