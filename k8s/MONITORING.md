# Kubernetes Monitoring & Init Containers

## 1. Stack Components

Here are the roles of the Kube-Prometheus stack components:

- **Prometheus Operator**: A Kubernetes controller that automates the deployment and configuration of Prometheus, Alertmanager, and related monitoring components. It uses Custom Resource Definitions (CRDs) like `ServiceMonitor` to easily manage scraping targets.
- **Prometheus**: The core time-series database and monitoring server. It pulls (scrapes) metrics from configured endpoints, stores them locally, and evaluates alerting rules against the collected data.
- **Alertmanager**: Receives alerts from Prometheus, deduplicates, groups, and routes them to the correct integration (e.g., Slack, Email, PagerDuty). It also handles alert silencing and inhibition.
- **Grafana**: A data visualization and observability platform. It connects to Prometheus as a data source to display metrics via customizable dashboards and charts.
- **kube-state-metrics**: A service that listens to the Kubernetes API server and generates metrics about the state of various cluster objects (e.g., Deployments, Pods, Nodes).
- **node-exporter**: A daemon that runs on every node in the cluster to export hardware and OS-level metrics (e.g., CPU, Memory, Disk I/O, Network statistics) so Prometheus can scrape them.

---

## 2. Installation Evidence

Output from `kubectl get po,svc -n monitoring`:

```text
NAME                                                      READY   STATUS              RESTARTS   AGE
pod/monitoring-grafana-7c666b6f9c-mtxjq                   1/3     Running             0          18s
pod/monitoring-kube-prometheus-operator-56dfc8596-76582   1/1     Running             0          18s
pod/monitoring-kube-state-metrics-5957bd45bc-5dg9d        1/1     Running             0          18s
pod/monitoring-prometheus-node-exporter-mzg9c             1/1     Running             0          18s

NAME                                              TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)             AGE
service/monitoring-grafana                        ClusterIP   10.97.147.7      <none>        80/TCP              18s
service/monitoring-kube-prometheus-alertmanager   ClusterIP   10.109.149.169   <none>        9093/TCP,8080/TCP   18s
service/monitoring-kube-prometheus-operator       ClusterIP   10.102.41.248    <none>        443/TCP             18s
service/monitoring-kube-prometheus-prometheus     ClusterIP   10.111.222.211   <none>        9090/TCP,8080/TCP   18s
service/monitoring-kube-state-metrics             ClusterIP   10.102.103.23    <none>        8080/TCP            18s
service/monitoring-prometheus-node-exporter       ClusterIP   10.102.243.231   <none>        9100/TCP            18s
```

---

## 3. Dashboard Answers

> *(Note: Replace the "[Insert Screenshot...]" placeholders with actual images after checking the Grafana port-forward instance)*

1. **Pod Resources**: My StatefulSet currently uses ~`X` MB of memory and `Y` CPU cores.
   - `![Pod Resources Screenshot](./screenshots/pod-resources.png)`
2. **Namespace Analysis**: In the default namespace, the `devops-info-service-...` pod uses the most CPU, while the `xyz...` pod uses the least.
   - `![Namespace Analysis Screenshot](./screenshots/namespace-analysis.png)`
3. **Node Metrics**: The Node is consuming `X`% (~`Y` MB) of its memory footprint out of its total `Z` CPU cores load.
   - `![Node Metrics Screenshot](./screenshots/node-metrics.png)`
4. **Kubelet**: The Kubelet currently manages `X` pods and `Y` containers.
   - `![Kubelet Screenshot](./screenshots/kubelet.png)`
5. **Network**: Incoming traffic for default namespace pods is ~`X` Kbps, and outgoing is ~`Y` Kbps.
   - `![Network Screenshot](./screenshots/network-traffic.png)`
6. **Alerts**: There are currently `X` active alerts (e.g., `Watchdog`, `InfoInhibitor`) sitting in the Alertmanager UI.
   - `![Alerts Screenshot](./screenshots/alerts.png)`

---

## 4. Init Containers

### Implementation: Download and Wait-for-Service Patterns

I implemented two init containers to run sequences before the main container starts.
1. `init-download`: Downloads a file using `wget` into the shared `/data` volume.
2. `wait-for-service`: Holds the main application by checking DNS resolution for an internal service (`kubernetes.default.svc.cluster.local`).

These were integrated via the Helm chart logic into the Deployment/StatefulSet/Rollout manifests.

**Configuration (`values.yaml`):**

```yaml
initContainers:
  enabled: true
  downloadFile:
    image: "busybox:1.36"
    command: ['sh', '-c', 'wget -O /data/index.html https://example.com']
  waitForService:
    image: "busybox:1.36"
    command: ['sh', '-c', 'until nslookup kubernetes.default.svc.cluster.local; do echo "waiting for service"; sleep 2; done; echo "Service found!"']
```

### Proof of Success

When deploying, the pod transitions through the `Init` stages, ensuring the setup scripts evaluate cleanly before allowing the main pod to bind:

```text
$ kubectl get pods -w
NAME                                                 READY   STATUS     RESTARTS      AGE
devops-info-service-f66c8bcbb-94zdl                  0/1     Init:1/2   0             30s
devops-info-service-f66c8bcbb-jw795                  0/1     Init:1/2   0             30s
```

Logs of the Download Init Container showing it successfully downloaded the HTML target:
```text
$ kubectl logs devops-info-service-f66c8bcbb-94zdl -c init-download
Connecting to example.com (172.66.147.243:443)
wget: note: TLS certificate validation not implemented
saving to '/data/index.html'
index.html           100% |********************************|   528  0:00:00 ETA
'/data/index.html' saved
```

Then we use `kubectl exec` against the running main container to read back the downloaded `/data/index.html` via the volume mount.
```text
$ kubectl exec devops-info-service-f66c8bcbb-94zdl -c devops-info-service -- cat /data/index.html
<!doctype html>
<html>
<head>
    <title>Example Domain</title>
```