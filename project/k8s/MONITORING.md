# Lab 16 — Kubernetes Monitoring & Init Containers

Overview, design decisions, and rubric mapping: **[`docs/LAB16.md`](../docs/LAB16.md)**.

This document is the operator runbook — install commands, dashboard queries, init container demos, troubleshooting.

## 1. Overview

Lab 16 layers a full **kube-prometheus-stack** onto the cluster and demonstrates **init container** patterns on the chart from Lab 15. Components installed:

| Component | Role (in own words) |
|---|---|
| **Prometheus Operator** | A controller that watches custom resources (`Prometheus`, `ServiceMonitor`, `PodMonitor`, `Alertmanager`, `PrometheusRule`) and reconciles them into running Prometheus / Alertmanager StatefulSets with the right scrape config. |
| **Prometheus** | The time-series database and scraper. Pulls `/metrics` endpoints discovered via Service/PodMonitor CRDs, stores samples, evaluates alerting rules, and answers PromQL queries. |
| **Alertmanager** | Deduplicates, groups, silences, and routes alerts that Prometheus fires. Sends notifications to receivers (Slack, email, PagerDuty). |
| **Grafana** | Dashboarding UI on top of Prometheus (and other data sources). The stack pre-installs ~30 cluster dashboards. |
| **kube-state-metrics** | Exports the state of Kubernetes objects (pod phase, deployment generation, PVC status, etc.) as Prometheus metrics. Different from cAdvisor metrics, which describe runtime usage. |
| **node-exporter** | DaemonSet exposing host-level Linux metrics (CPU, memory, disk, network, filesystem). Runs once per node. |

Two new chart additions:

- `templates/servicemonitor.yaml` — `ServiceMonitor` CRD (bonus) that tells Prometheus to scrape our app's `/metrics`.
- `_helpers.tpl` — three new include helpers (`initContainers`, `initContainerVolumes`, `initContainerVolumeMounts`) reused by all three workload templates (Deployment / Rollout / StatefulSet).

## 2. Install

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --wait --timeout 5m
```

```
LAST DEPLOYED: Wed May 13 22:23:38 2026
NAMESPACE: monitoring
STATUS: deployed
REVISION: 1
```

## 3. Resource verification

```bash
kubectl get pods,svc -n monitoring
```

```
NAME                                                         READY   STATUS    RESTARTS   AGE
pod/alertmanager-monitoring-kube-prometheus-alertmanager-0   2/2     Running   0          50s
pod/monitoring-grafana-766d875f8f-q7nxd                      3/3     Running   0          69s
pod/monitoring-kube-prometheus-operator-5cdd7dcf48-24ckv     1/1     Running   0          69s
pod/monitoring-kube-state-metrics-5746795bd9-b5x6c           1/1     Running   0          70s
pod/monitoring-prometheus-node-exporter-xjl7d                1/1     Running   0          70s
pod/prometheus-monitoring-kube-prometheus-prometheus-0       2/2     Running   0          50s

NAME                                              TYPE        CLUSTER-IP        PORT(S)
service/alertmanager-operated                     ClusterIP   None              9093/TCP,9094/TCP,9094/UDP
service/monitoring-grafana                        ClusterIP   192.168.194.213   80/TCP
service/monitoring-kube-prometheus-alertmanager   ClusterIP   192.168.194.232   9093/TCP,8080/TCP
service/monitoring-kube-prometheus-operator       ClusterIP   192.168.194.148   443/TCP
service/monitoring-kube-prometheus-prometheus     ClusterIP   192.168.194.202   9090/TCP,8080/TCP
service/monitoring-kube-state-metrics             ClusterIP   192.168.194.224   8080/TCP
service/monitoring-prometheus-node-exporter       ClusterIP   192.168.194.195   9100/TCP
```

All six expected workloads `Running`; both headless (alertmanager-operated, prometheus-operated) and ClusterIP services present.

Scrape target health:

```bash
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090 &
curl -s http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets[] | "\(.labels.job)  \(.health)"' | sort -u
```

```
apiserver  up
coredns  up
kube-state-metrics  up
kubelet  up
monitoring-grafana  up
monitoring-kube-prometheus-alertmanager  up
monitoring-kube-prometheus-operator  up
monitoring-kube-prometheus-prometheus  up
node-exporter  up
```

## 4. Grafana dashboard answers (Lab task 2)

Each of the six lab questions is answered by the PromQL the dashboard panel runs underneath. Outputs below come from the Prometheus HTTP API. Equivalent Grafana panels in parentheses.

**Test cluster:** OrbStack single-node k3s, 1 node (`192.168.139.2`), 3-replica `lab15-devops-info-service` StatefulSet in `default`.

### Q1 — CPU/memory of our StatefulSet pods *(Kubernetes / Compute Resources / Pod)*

```bash
sum by (pod) (rate(container_cpu_usage_seconds_total{namespace="default",pod=~"lab15-devops-info-service-.*"}[5m]))
sum by (pod) (container_memory_working_set_bytes{namespace="default",pod=~"lab15-devops-info-service-.*"}) / 1024 / 1024
```

| Pod | CPU (cores) | Memory (MiB) |
|---|---|---|
| `lab15-devops-info-service-0` | 0.0043 | 47.21 |
| `lab15-devops-info-service-1` | 0.0043 | 47.16 |
| `lab15-devops-info-service-2` | 0.0043 | 47.49 |

Roughly identical — three pods running the same FastAPI image, idle.

### Q2 — Top/bottom pods by CPU in `default` *(Kubernetes / Compute Resources / Namespace (Pods))*

```bash
topk(3, sum by (pod) (rate(container_cpu_usage_seconds_total{namespace="default"}[5m])))
bottomk(3, sum by (pod) (rate(container_cpu_usage_seconds_total{namespace="default"}[5m])))
```

Top-3 and bottom-3 are the same three pods (default namespace only has lab15 right now). CPU 0.0043 c each.

### Q3 — Node memory / CPU *(Node Exporter / Nodes)*

```bash
100 * (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)
(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / 1024 / 1024
count by (instance) (node_cpu_seconds_total{mode="idle"})
```

| Metric | Value |
|---|---|
| Memory % used | **22.49 %** |
| Memory used | **3 605.8 MiB** |
| CPU cores | **12** |

### Q4 — Pods/containers managed by kubelet *(Kubernetes / Kubelet)*

```bash
kubelet_running_pods
kubelet_running_containers
```

```
kubelet_running_pods       = 24
kubelet_running_containers = 28 (running)  +  3 (created)  +  4 (exited)
```

### Q5 — Network traffic *(Node Exporter / Nodes — Network)*

On this cluster the per-pod `container_network_*` cAdvisor metrics are not exposed (cgroup-v2 quirk on this k3s build). The kube-prometheus-stack recording rule provides the node-level equivalent:

```bash
instance:node_network_receive_bytes_excluding_lo:rate5m
instance:node_network_transmit_bytes_excluding_lo:rate5m
```

| Direction | Rate |
|---|---|
| RX | **56 030 B/s** (≈55 KiB/s) |
| TX | **123 020 B/s** (≈120 KiB/s) |

### Q6 — Active alerts *(Alertmanager UI)*

```bash
curl -sG --data-urlencode 'query=ALERTS{alertstate="firing"}' http://localhost:9090/api/v1/query | jq '.data.result | length'
```

```
1 firing alert: Watchdog  severity=none
```

`Watchdog` is the stack's built-in always-firing canary — its presence is the proof Alertmanager itself is working.

To reach the Alertmanager UI:

```bash
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-alertmanager 9093:9093
# open http://localhost:9093
```

To reach Grafana:

```bash
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
# user: admin
# password:
kubectl -n monitoring get secret monitoring-grafana -o jsonpath='{.data.admin-password}' | base64 -d ; echo
```

## 5. Init container: download pattern

Adds an `init-download` container that fetches a file with `wget` into an `emptyDir` shared with the main container at `/work-dir`. Useful for: bootstrapping config from a remote source, pre-pulling certificates, seeding a cache directory.

```bash
helm upgrade lab15 ./k8s/devops-info-service \
  --set statefulset.enabled=true \
  --set statefulset.replicas=1 \
  --set initContainers.enabled=true \
  --set initContainers.waitForService.enabled=false
```

```bash
kubectl get sts lab15-devops-info-service -o jsonpath='{.spec.template.spec.initContainers[*].name}'
# → init-download

kubectl logs lab15-devops-info-service-0 -c init-download
```

```
Connecting to raw.githubusercontent.com (185.199.108.133:443)
wget: note: TLS certificate validation not implemented
saving to '/work-dir/index.html'
index.html           100% |********************************|  4387  0:00:00 ETA
'/work-dir/index.html' saved
```

```bash
kubectl exec lab15-devops-info-service-0 -- ls -la /work-dir
kubectl exec lab15-devops-info-service-0 -- head -3 /work-dir/index.html
```

```
total 8
drwxrwxrwx 1 root root   20 May 13 19:38 .
drwxr-xr-x 1 root root   66 May 13 19:38 ..
-rw-r--r-- 1 app  app  4387 May 13 19:38 index.html

# Kubernetes (K8s)

[![CII Best Practices](...)](...)
```

The main container reads the file that the init container fetched. Volume ownership is `app:app` (UID 10001 from the chart's `securityContext`) because `emptyDir` mounts inherit pod-level fsGroup.

## 6. Init container: wait-for-service pattern

Adds an `init-wait-for-service` container that loops `nc -z <svc> <port>` until the dependency is reachable (or a timeout fires). Useful for: blocking app startup until a database, message broker, or auth service is ready.

### 6a. Blocked on a non-existent service

```bash
helm upgrade lab15 ./k8s/devops-info-service \
  --set statefulset.enabled=true --set statefulset.replicas=1 \
  --set initContainers.enabled=true \
  --set initContainers.download.enabled=false \
  --set initContainers.waitForService.service=notyet.default.svc.cluster.local \
  --set initContainers.waitForService.port=80 \
  --set initContainers.waitForService.timeoutSeconds=300
```

```bash
kubectl get pods -l app.kubernetes.io/instance=lab15
```

```
NAME                          READY   STATUS     RESTARTS   AGE
lab15-devops-info-service-0   0/1     Init:0/1   0          3m3s
```

```bash
kubectl logs lab15-devops-info-service-0 -c init-wait-for-service | tail -5
```

```
waiting for notyet.default.svc.cluster.local:80...
waiting for notyet.default.svc.cluster.local:80...
waiting for notyet.default.svc.cluster.local:80...
waiting for notyet.default.svc.cluster.local:80...
waiting for notyet.default.svc.cluster.local:80...
```

Pod stays `Init:0/1` indefinitely — the app container never starts.

### 6b. Unblocks once the service is reachable

Point the wait at a service that **is** up — kube-prometheus-stack's Prometheus.

```bash
helm upgrade lab15 ./k8s/devops-info-service \
  --set statefulset.enabled=true --set statefulset.replicas=1 \
  --set initContainers.enabled=true \
  --set initContainers.download.enabled=false \
  --set initContainers.waitForService.service=monitoring-kube-prometheus-prometheus.monitoring.svc.cluster.local \
  --set initContainers.waitForService.port=9090

# Force the stuck pod to re-roll with the new spec
kubectl delete pod lab15-devops-info-service-0
sleep 15
kubectl get pods -l app.kubernetes.io/instance=lab15
```

```
NAME                          READY   STATUS    RESTARTS   AGE
lab15-devops-info-service-0   1/1     Running   0          15s
```

```bash
kubectl logs lab15-devops-info-service-0 -c init-wait-for-service
```

```
service reachable
```

```bash
kubectl get pod lab15-devops-info-service-0 \
  -o jsonpath='{range .status.initContainerStatuses[*]}{.name}: ready={.ready}  reason={.state.terminated.reason}  exitCode={.state.terminated.exitCode}{"\n"}{end}'
```

```
init-wait-for-service: ready=true  reason=Completed  exitCode=0
```

The TCP probe succeeded on the first attempt, init exited 0, the main container started, and the pod became `Running`.

## 7. Bonus — Custom metrics & ServiceMonitor (2.5 pts)

The app's `/metrics` endpoint is already wired (`prometheus_client` + `@app.get("/metrics")` in [app.py:167](../app_python/app/app.py#L167), metrics defined in [metrics.py](../app_python/app/metrics.py) — `http_requests_total`, `http_request_duration_seconds`, `http_requests_in_progress`, `devops_info_endpoint_calls`).

What was added in this lab: a chart-managed `ServiceMonitor` CRD ([templates/servicemonitor.yaml](devops-info-service/templates/servicemonitor.yaml)) that tells the kube-prometheus-stack Prometheus to discover and scrape the app's `Service`.

```bash
helm upgrade lab15 ./k8s/devops-info-service \
  --set statefulset.enabled=true --set statefulset.replicas=3 \
  --set monitoring.serviceMonitor.enabled=true
```

```bash
kubectl get servicemonitor lab15-devops-info-service -o yaml | head -25
```

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  labels:
    app.kubernetes.io/instance: lab15
    app.kubernetes.io/managed-by: Helm
    app.kubernetes.io/name: devops-info-service
    helm.sh/chart: devops-info-service-0.2.0
    release: monitoring          # ← key label; matches Prometheus' serviceMonitorSelector
  name: lab15-devops-info-service
  namespace: default
spec:
  endpoints:
  - interval: 30s
    path: /metrics
    port: http                    # ← matches Service port name
    scrapeTimeout: 10s
```

Prometheus discovers the three pod endpoints within ~30 s:

```bash
curl -s http://localhost:9090/api/v1/targets \
  | jq '.data.activeTargets[] | select(.labels.service=="lab15-devops-info-service") | {scrapeUrl, health, lastError}'
```

```json
{ "scrapeUrl": "http://192.168.194.53:5000/metrics", "health": "up", "lastError": "" }
{ "scrapeUrl": "http://192.168.194.54:5000/metrics", "health": "up", "lastError": "" }
{ "scrapeUrl": "http://192.168.194.55:5000/metrics", "health": "up", "lastError": "" }
```

All three pods scraped, `up`, no errors.

The app's custom metrics are queryable from Prometheus:

```bash
curl -sG --data-urlencode \
  'query=sum by (exported_endpoint) (devops_info_endpoint_calls_total)' \
  http://localhost:9090/api/v1/query | jq '.data.result'
```

```json
[
  { "metric": { "exported_endpoint": "/" },       "value": [..., "10"] },
  { "metric": { "exported_endpoint": "/health" }, "value": [..., "97"] }
]
```

```bash
curl -sG --data-urlencode \
  'query=sum by (status) (http_requests_total{job=~".*devops-info-service.*"})' \
  http://localhost:9090/api/v1/query | jq '.data.result'
```

```json
[ { "metric": { "status": "200" }, "value": [..., "107"] } ]
```

107 HTTP 200s across all three pods — middleware-recorded request counter, scraped by Prometheus through the ServiceMonitor.

## 8. Cleanup

```bash
helm uninstall lab15 ; kubectl delete pvc -l app.kubernetes.io/instance=lab15
helm uninstall monitoring -n monitoring ; kubectl delete ns monitoring
```

Order matters: uninstalling kube-prometheus-stack removes the Prometheus Operator CRDs while still in use only if you also `kubectl delete crd prometheuses.monitoring.coreos.com ...` — the chart's `helm uninstall` does NOT remove them by default, which is intentional (next install reuses them). To fully wipe:

```bash
kubectl delete crd $(kubectl get crd -o name | grep monitoring.coreos.com)
```

## 9. Troubleshooting

### ServiceMonitor created but no target appears in Prometheus

The `release` label on the ServiceMonitor must match the **Prometheus install name** (default chart install = `monitoring`). Inspect what your Prometheus is looking for:

```bash
kubectl get prometheus -n monitoring -o jsonpath='{.items[0].spec.serviceMonitorSelector}' ; echo
# → {"matchLabels":{"release":"monitoring"}}
```

If the SM label differs (e.g., you installed kube-prometheus-stack with a different release name), set `monitoring.serviceMonitor.releaseLabel` accordingly.

### Pod-level network metrics empty

`container_network_*` from cAdvisor isn't exposed on every kubelet/cgroup-v2 combination. Use node-level recording rules (`instance:node_network_*:rate5m`) — they're pre-shipped by kube-prometheus-stack.

### Init container `wget` fails with `wget: not found`

The chart's main image is built on a distroless/slim base without wget — but the init container uses `busybox:1.36` which has it. If you swap the init image (`initContainers.download.image`), make sure it has `wget`, or change the command to `curl -fL -o ...`.

### Pod stuck `Init:0/1` after editing wait-for-service target

StatefulSet `RollingUpdate` won't replace a pod that isn't `Ready`. Force the swap:

```bash
kubectl delete pod <pod-name>
```

### `helm upgrade … --wait` times out while pod is stuck on `Init:0/1`

Expected: `--wait` polls Ready and the pod never becomes ready until the init container resolves. Drop `--wait` (or run without `--timeout`) and verify state with `kubectl get pods -w`.
