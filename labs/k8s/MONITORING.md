# Lab 16

## 1. Stack Components

The **Kube‑Prometheus‑Stack** bundles several components:

- **Prometheus Operator** – manages Prometheus, Alertmanager, and related CRDs (ServiceMonitor, etc.) using Kubernetes custom resources.
- **Prometheus** – scrapes and stores time‑series data from targets (node‑exporter, kube‑state‑metrics, applications).
- **Alertmanager** – handles alerts sent by Prometheus; deduplicates, groups, and routes them to receivers (email, Slack, etc.).
- **Grafana** – provides rich dashboards and visualisation of Prometheus metrics.
- **kube‑state‑metrics** – generates metrics about Kubernetes objects (Deployments, Pods, Nodes) from the API server.
- **node‑exporter** – exposes hardware and OS metrics (CPU, memory, disk, network) from each node.

---

## 2. Installation Evidence

```bash
$ kubectl get po,svc -n monitoring
NAME                                                         READY   STATUS    RESTARTS   AGE
pod/alertmanager-monitoring-kube-prometheus-alertmanager-0   2/2     Running   0          58m
pod/monitoring-grafana-ccc7fd588-n2bb7                       3/3     Running   0          58m
pod/monitoring-kube-prometheus-operator-54f68d65b4-whhlj     1/1     Running   0          58m
pod/monitoring-kube-state-metrics-5957bd45bc-9t4xm           1/1     Running   0          58m
pod/monitoring-prometheus-node-exporter-ql9wh                1/1     Running   0          58m
pod/prometheus-monitoring-kube-prometheus-prometheus-0       2/2     Running   0          58m

NAME                                              TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)                      AGE
service/alertmanager-operated                     ClusterIP   None             <none>        9093/TCP,9094/TCP,9094/UDP   58m
service/monitoring-grafana                        ClusterIP   10.99.252.180    <none>        80/TCP                       58m
service/monitoring-kube-prometheus-alertmanager   ClusterIP   10.108.225.72    <none>        9093/TCP,8080/TCP            58m
service/monitoring-kube-prometheus-operator       ClusterIP   10.106.92.63     <none>        443/TCP                      58m
service/monitoring-kube-prometheus-prometheus     ClusterIP   10.104.188.156   <none>        9090/TCP,8080/TCP            58m
service/monitoring-kube-state-metrics             ClusterIP   10.111.47.71     <none>        8080/TCP                     58m
service/monitoring-prometheus-node-exporter       ClusterIP   10.98.233.111    <none>        9100/TCP                     58m
service/prometheus-operated                       ClusterIP   None             <none>        9090/TCP                     58m
```

## 3. Dashboard Answers

### 3.1

![Q1](/labs/k8s/screenshots/question1.png)


### 3.2

![Q2](/labs/k8s/screenshots/question2.png)

### 3.3

![Q3](/labs/k8s/screenshots/question3.png)

### 3.4

![Q4](/labs/k8s/screenshots/question4.png)

### 3.5

![Q5](/labs/k8s/screenshots/question5.png)

### 3.6

![Q6](/labs/k8s/screenshots/question6.png)

## 4. Init containers

Added two init containers to the StatefulSet:

- init-download – uses busybox to download https://example.com and save the content to a shared empty‑dir volume (/work-dir/index.html).

- wait-for-headless – loops until the headless service is resolvable via DNS, ensuring network dependencies are ready before the main container starts.

The main container mounts the shared volume at /shared to access the downloaded file.

```bash
$ kubectl logs python-app-dev-simple-app-0 -n dev -c init-downloadad
& kubectl logs python-app-dev-simple-app-0 -n dev -c wait-for-headless

Downloading file...
Connecting to example.com (8.47.69.0:443)
wget: note: TLS certificate validation not implemented
saving to '/work-dir/index.html'
index.html           100% |********************************|   528  0:00:00 ETA
'/work-dir/index.html' saved
Done: <!doctype html><html lang="en"><head><title>Example Domain</title><meta name="viewport" content="wid...
Waiting for headless service to be resolvable...
Server:         10.96.0.10
Address:        10.96.0.10:53

Name:   python-app-dev-simple-app-headless.dev.svc.cluster.local
Address: 10.244.1.152

Headless service is ready!
```
```bash
$ kubectl exec python-app-dev-simple-app-0 -n dev -- cat /shared/index.html | head

Defaulted container "simple-app" out of: simple-app, init-download (init), wait-for-headless (init)
<!doctype html><html lang="en"><head><title>Example Domain</title><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{background:#eee;width:60vw;margin:15vh auto;font-family:system-ui,sans-serif}h1{font-size:1.5em}div{opacity:0.8}a:link,a:visited{color:#348}</style></head><body><div><h1>Example Domain</h1><p>This domain is for use in documentation examples without needing permission. Avoid use in operations.</p><p><a href="https://iana.org/domains/example">Learn more</a></p></div></body></html>
```