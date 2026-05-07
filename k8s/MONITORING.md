# Lab 16

## Task 1 — Kube-Prometheus Stack Components

| Component | Role |
|-----------|------|
| **Prometheus Operator** | Manages Prometheus, Alertmanager, and ServiceMonitor resources using custom resource definitions (CRDs). It automates the creation, scaling, and configuration of monitoring components. |
| **Prometheus** | A time‑series database that scrapes metrics from various endpoints (pods, nodes, services). It stores those metrics and makes them queryable via PromQL. |
| **Alertmanager** | Handles alerts sent by Prometheus. It can group, inhibit, silence, and route alerts to external receivers like email, Slack, or PagerDuty. |
| **Grafana** | A dashboarding and visualisation tool that connects to Prometheus (and other data sources) to create rich, interactive graphs and alerts. |
| **kube-state-metrics** | Exposes cluster‑level state metrics (e.g., number of deployments, pods, replica sets, their status, labels, etc.) to Prometheus. |
| **node-exporter** | A DaemonSet that collects hardware and operating system metrics from each node (CPU, memory, disk I/O, network, etc.). |

---

## Task 2 — Installation Evidence

```bash
$ helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace

STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
kube-prometheus-stack has been installed. Check its status by running:
  kubectl --namespace monitoring get pods -l "release=monitoring"

Get Grafana 'admin' user password by running:

  kubectl --namespace monitoring get secrets monitoring-grafana -o jsonpath="{.data.admin-password}" | base64 -d ; echo

Access Grafana local instance:

  export POD_NAME=$(kubectl --namespace monitoring get pod -l "app.kubernetes.io/name=grafana,app.kubernetes.io/instance=monitoring" -oname)
  kubectl --namespace monitoring port-forward $POD_NAME 3000

Get your grafana admin user password by running:

  kubectl get secret --namespace monitoring -l app.kubernetes.io/component=admin-secret -o jsonpath="{.items[0].data.admin-password}" | base64 --decode ; echo


Visit https://github.com/prometheus-operator/kube-prometheus for instructions on how to create & configure Alertmanager and Prometheus instances using the Operator.

$ kubectl get po,svc -n monitoring
NAME                                                         READY   STATUS    RESTARTS   AGE
pod/alertmanager-monitoring-kube-prometheus-alertmanager-0   2/2     Running   0          12m
pod/monitoring-grafana-8486576b5-ptrrv                       3/3     Running   0          13m
pod/monitoring-kube-prometheus-operator-54f68d65b4-ff7g7     1/1     Running   0          13m
pod/monitoring-kube-state-metrics-5957bd45bc-txxv8           1/1     Running   0          13m
pod/monitoring-prometheus-node-exporter-5m8qf                1/1     Running   0          13m
pod/prometheus-monitoring-kube-prometheus-prometheus-0       2/2     Running   0          12m

NAME                                              TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)                      AGE
service/alertmanager-operated                     ClusterIP   None             <none>        9093/TCP,9094/TCP,9094/UDP   12m
service/monitoring-grafana                        ClusterIP   10.107.7.151     <none>        80/TCP                       13m
service/monitoring-kube-prometheus-alertmanager   ClusterIP   10.97.142.49     <none>        9093/TCP,8080/TCP            13m
service/monitoring-kube-prometheus-operator       ClusterIP   10.110.45.248    <none>        443/TCP                      13m
service/monitoring-kube-prometheus-prometheus     ClusterIP   10.110.189.143   <none>        9090/TCP,8080/TCP            13m
service/monitoring-kube-state-metrics             ClusterIP   10.106.3.116     <none>        8080/TCP                     13m
service/monitoring-prometheus-node-exporter       ClusterIP   10.101.66.138    <none>        9100/TCP                     13m
service/prometheus-operated                       ClusterIP   None             <none>        9090/TCP                     12m
```

---

## Task 3 — Grafana Dashboard Answers

All screenshots are in `screenshots/` folder. 

### 1. Pod Resources – CPU/memory usage of your Python app pod

| Metric | Value |
|--------|----------------|
| CPU Usage (cores) | 0.01 cores |
| Memory Usage (MB) | 128 MB |

### 2. Namespace Analysis – pods using most/least CPU in `default` namespace

All the same: 0.01 CPU usage

### 3. Node Metrics – memory usage (%, MB) and CPU cores

| Metric | Value |
|--------|----------------|
| Memory usage % | 81% |
| Memory usage MB | 2.9 GiB |
| CPU cores total | 1 cores |
| CPU cores used | 0.91 cores |

### 4. Kubelet – number of pods/containers managed


| Metric | Value |
|--------|----------------|
| Pods on node | 32 pods |
| Running containers | 73 containers |

### 5. Network traffic for pods in `default` namespace

No data were in grafana

### 6. Alerts – how many active alerts in Alertmanager?

---

## Task 4 — Init Containers Implementation

I added two init containers to our `templates/deployment.yaml`:

1. **init-download** – downloads `https://example.com` into a shared volume.
2. **wait-for-service** – waits for `kubernetes.default.svc.cluster.local` to be resolvable (ensures network is up).

### Verification commands

```bash
$ kubectl get pods -l app.kubernetes.io/instance=my-python-app
NAME                             READY   STATUS     RESTARTS       AGE
my-python-app-0                  1/1     Running    0              36m
my-python-app-1                  1/1     Running    0              36m
my-python-app-2                  1/1     Running    0              35m
my-python-app-6cc67c4999-2lftt   1/1     Running    0              36m
my-python-app-6cc67c4999-b9xpg   0/1     Init:0/2   2 (6m8s ago)   36m
my-python-app-6cc67c4999-x448b   1/1     Running    0              36m
my-python-app-8757f4998-bgl5m    1/1     Running    0              36m
my-python-app-8757f4998-jbwkl    1/1     Running    0              36m
my-python-app-8757f4998-p8r2p    1/1     Running    0              36m
```

**Check init container logs:**

```bash
$ kubectl logs my-python-app-6cc67c4999-2lftt -c init-download
Connecting to example.com (8.47.69.1:443)
wget: note: TLS certificate validation not implemented
saving to '/work-dir/index.html'
index.html           100% |********************************|   528  0:00:00 ETA
'/work-dir/index.html' saved

$ kubectl logs my-python-app-6cc67c4999-2lftt -c wait-for-service
Server:         10.96.0.10
Address:        10.96.0.10:53

Name:   kubernetes.default.svc.cluster.local
Address: 10.96.0.1
```

**Verify downloaded file in main container:**

```bash
$ kubectl exec my-python-app-6cc67c4999-2lftt -c python-app -- cat /data/index.html
<!doctype html><html lang="en"><head><title>Example Domain</title><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{background:#eee;width:60vw;margin:15vh auto;font-family:system-ui,sans-serif}h1{font-size:1.5em}div{opacity:0.8}a:link,a:visited{color:#348}</style></head><body><div><h1>Example Domain</h1><p>This domain is for use in documentation examples without needing permission. Avoid use in operations.</p><p><a href="https://iana.org/domains/example">Learn more</a></p></div></body></html>
```

The file is accessible inside the application container, proving the init container succeeded.

---

## Bonus Task — Custom Metrics & ServiceMonitor

### ServiceMonitor creation

I added a `templates/servicemonitor.yaml` and enabled it via `values.yaml`.

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: my-python-app
  labels:
    release: monitoring
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: python-app
      monitoring: enabled
  endpoints:
    - port: http
      path: /metrics
      interval: 30s
```

### Verification in Prometheus UI

In screenshots
---

## Conclusion

All monitoring components are successfully installed and configured. The Python application metrics are scraped by Prometheus, visualised in Grafana, and we demonstrated init containers for pod initialisation and dependency handling.
