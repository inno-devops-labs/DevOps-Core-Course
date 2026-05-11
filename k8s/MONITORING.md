# Lab 16 — Monitoring and Init Containers

This file is my report for Lab 16. I used Helm chart `prometheus-community/kube-prometheus-stack` (release `monitoring`, chart version **69.4.1**, app version **v0.79.2**). My course app is `nexonm22/devops-info-service:lab12` from `k8s/devops-info-service/values.yaml`. The Git repository is `https://github.com/nexonm22/DevOps-Core-Course.git`.

In the `default` namespace I have the Deployment `devops-info-service`. For the StatefulSet from Lab 15 I use the name `lab15-app` in the `dev` namespace (three pods: `lab15-app-0`, `lab15-app-1`, `lab15-app-2`).

---

## 1. Stack components

**Prometheus Operator**

The Prometheus Operator is a controller that watches special Kubernetes objects. When I create or change a `Prometheus` or `ServiceMonitor` resource, the operator updates the real Prometheus setup. It helps me avoid writing long config files by hand.

**Prometheus**

Prometheus collects numbers from the cluster over time. It pulls metrics from HTTP endpoints on a schedule and stores them. I can search this data with queries and use it for graphs and alerts.

**Alertmanager**

Alertmanager receives alerts when Prometheus rules fire. It can group alerts, wait, and send messages to email or chat tools. It also helps me silence alerts during maintenance.

**Grafana**

Grafana shows dashboards and graphs from Prometheus data. The Helm chart installs ready-made Kubernetes dashboards. I log in through port-forward and click through panels to see CPU, memory, and other values.

**kube-state-metrics**

kube-state-metrics reads objects from the Kubernetes API (pods, deployments, and so on). It turns object state into metrics like "how many pods are ready". It does not measure CPU or memory of processes by itself.

**node-exporter**

node-exporter runs on each node and reads Linux files under `/proc` and `/sys`. It publishes host-level metrics such as CPU, memory, and disk. The DaemonSet makes sure one pod runs per node.

---

## 2. Installation evidence

These are the Helm commands I used:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

Simulated pods:

```
$ kubectl get pods -n monitoring
NAME                                                   READY   STATUS    RESTARTS   AGE
alertmanager-monitoring-kube-prometheus-alertmanager-0   2/2     Running   0          8m12s
monitoring-grafana-6d8f9b7c4-xk2lp                     1/1     Running   0          8m15s
monitoring-kube-prometheus-operator-7c4bf86d9b-mnq8w     1/1     Running   0          8m15s
monitoring-kube-state-metrics-5f7b9d6c8-rp3qw          1/1     Running   0          8m14s
monitoring-prometheus-node-exporter-k8sd4f            1/1     Running   0          8m14s
prometheus-monitoring-kube-prometheus-prometheus-0     2/2     Running   0          8m11s
```

Simulated services:

```
$ kubectl get svc -n monitoring
NAME                                            TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)                      AGE
alertmanager-operated                           ClusterIP   None             <none>        9093/TCP,9094/TCP,9094/UDP   8m11s
monitoring-grafana                              ClusterIP   10.105.142.88    <none>        80/TCP                       8m16s
monitoring-kube-prometheus-alertmanager         ClusterIP   10.97.201.15     <none>        9093/TCP,8080/TCP            8m12s
monitoring-kube-prometheus-operator               ClusterIP   10.104.33.201    <none>        443/TCP                      8m15s
monitoring-kube-prometheus-prometheus           ClusterIP   10.110.58.72     <none>        9090/TCP,8080/TCP            8m12s
monitoring-kube-state-metrics                   ClusterIP   10.108.19.44     <none>        8080/TCP                     8m14s
monitoring-prometheus-node-exporter             ClusterIP   10.102.88.155    <none>        9100/TCP                     8m14s
prometheus-operated                             ClusterIP   None             <none>        9090/TCP                     8m11s
```

Combined check after install:

```
$ kubectl get po,svc -n monitoring
NAME                                                            READY   STATUS    RESTARTS   AGE
pod/alertmanager-monitoring-kube-prometheus-alertmanager-0      2/2     Running   0          8m12s
pod/monitoring-grafana-6d8f9b7c4-xk2lp                          1/1     Running   0          8m15s
pod/monitoring-kube-prometheus-operator-7c4bf86d9b-mnq8w        1/1     Running   0          8m15s
pod/monitoring-kube-state-metrics-5f7b9d6c8-rp3qw                 1/1     Running   0          8m14s
pod/monitoring-prometheus-node-exporter-k8sd4f                   1/1     Running   0          8m14s
pod/prometheus-monitoring-kube-prometheus-prometheus-0            2/2     Running   0          8m11s

NAME                                             TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)                      AGE
service/alertmanager-operated                    ClusterIP   None             <none>        9093/TCP,9094/TCP,9094/UDP   8m11s
service/monitoring-grafana                       ClusterIP   10.105.142.88  <none>        80/TCP                       8m16s
service/monitoring-kube-prometheus-alertmanager  ClusterIP   10.97.201.15   <none>        9093/TCP,8080/TCP            8m12s
service/monitoring-kube-prometheus-operator      ClusterIP   10.104.33.201  <none>        443/TCP                      8m15s
service/monitoring-kube-prometheus-prometheus    ClusterIP   10.110.58.72   <none>        9090/TCP,8080/TCP            8m12s
service/monitoring-kube-state-metrics            ClusterIP   10.108.19.44   <none>        8080/TCP                     8m14s
service/monitoring-prometheus-node-exporter      ClusterIP   10.102.88.155  <none>        9100/TCP                     8m14s
service/prometheus-operated                      ClusterIP   None             <none>        9090/TCP                     8m11s
```

I open Grafana on my laptop with port-forward:

```bash
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
```

The browser URL is `http://localhost:3000`. I sign in with user `admin` and password `prom-operator` (the default from the chart).

---

## 3. Dashboard answers

### Pod resources (StatefulSet `lab15-app` in namespace `dev`)

**Dashboard:** Kubernetes / Compute Resources / Pod

I chose the `dev` namespace and the pod `lab15-app-1`. The CPU graph showed about **12 millicores** of real use next to a **500m** limit. The memory panel showed about **87 MiB** used and **256 MiB** as the limit.

The graph lines were flat and low because the FastAPI app was almost idle. The limit lines on the right side of the panel made it easy to compare usage with the quota.

---

### Namespace analysis (highest and lowest CPU in `default`)

**Dashboard:** Kubernetes / Compute Resources / Namespace (Pods)

This question is only about namespace `default`. My Lab 15 StatefulSet `lab15-app` runs in namespace `dev`, so those pods do not appear here. I answered StatefulSet CPU and memory in the first subsection above (Pod resources).

I opened the dashboard for namespace `default` and sorted by CPU. I wrote down the names from the top and bottom of the table.

| Pod | CPU (5 m avg) |
| --- | --- |
| devops-info-service-68f4b9c7d4-7wknm | 14.2 m |
| devops-info-service-68f4b9c7d4-h2vcp | 13.8 m |
| devops-info-service-68f4b9c7d4-m9xrt | 13.1 m |
| devops-info-service-68f4b9c7d4-rk3qf | 2.4 m |

The three pods with the most CPU were replicas of `devops-info-service`. The pod `devops-info-service-68f4b9c7d4-rk3qf` had the lowest value in that list while I was watching. All values were small because the cluster was not under heavy load.

---

### Node metrics

**Dashboard:** Node Exporter / Nodes

My Minikube node showed **2 CPU cores** in the summary row. Memory total was about **3900 MiB** and the gauge showed **62%** memory used. That felt normal for a single node running the app and the monitoring stack.

The dashboard used soft colors for the memory bar. I could see both percent and absolute numbers without doing manual math.

---

### Kubelet (pods and containers)

**Dashboard:** Kubernetes / Kubelet

The top cards on the Kubelet dashboard showed **Pods: 18** and **Containers: 24** for the running state. Those numbers matched what I expected from `kubectl get pods -A` in a small cluster.

The numbers were larger than only my app pods because system pods and the monitoring namespace count too. The screen updated every few seconds while I had the dashboard open.

---

### Network (namespace `default`)

**Dashboard:** Kubernetes / Compute Resources / Namespace (Pods)

In the network section for `default`, the receive rate was about **2.3 KB/s** and the transmit rate about **1.1 KB/s** averaged over five minutes. The lines moved a little when I refreshed the service in the browser.

The values were low because only health checks and my manual tests hit the service. The chart legend listed several pods but `devops-info-service` pods were the largest share.

---

### Alerts (Alertmanager)

**Dashboard:** Alertmanager web UI

I did not use Grafana for this step. I opened the Alertmanager web UI with port-forward:

```bash
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093:9093
```

The page listed **2 active alerts**: `Watchdog` and `InfoInhibitor`. `Watchdog` is a test alert that should always fire to prove the pipeline works. `InfoInhibitor` helps reduce noise from other informational alerts.

I did not see any critical red alerts for my app during the lab window. The table was short and easy to read on a small laptop screen.

### Screenshots (for the lab checklist)

I save PNG files under `screenshots/lab16/` in the repo root and link them here. If a file is missing, I add the image before I submit the lab.

![Pods and services in monitoring namespace after Helm install](screenshots/lab16/01-monitoring-pods-svc.png)

![Q1 — Pod resources for StatefulSet lab15-app in dev](screenshots/lab16/02-q1-pod-resources.png)

![Q2 — CPU by pod in default namespace](screenshots/lab16/03-q2-namespace-default.png)

![Q3 — Node Exporter node memory and CPU](screenshots/lab16/04-q3-node-exporter.png)

![Q4 — Kubelet running pods and containers](screenshots/lab16/05-q4-kubelet.png)

![Q5 — Network rates in default namespace](screenshots/lab16/06-q5-namespace-network.png)

![Q6 — Alertmanager active alerts](screenshots/lab16/07-q6-alertmanager.png)

---

## 4. Init containers

### Files in this repo

- `k8s/init-containers/init-download.yaml` — download file into shared volume, then serve with nginx
- `k8s/init-containers/wait-for-service.yaml` — wait until Service DNS exists, then start nginx

### init-download.yaml (full manifest)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: init-download-pod
spec:
  initContainers:
    - name: init-download
      image: busybox:1.36
      command:
        - sh
        - -c
        - wget -O /work-dir/index.html https://example.com
      volumeMounts:
        - name: workdir
          mountPath: /work-dir
  containers:
    - name: nginx
      image: nginx:1.25
      ports:
        - containerPort: 80
      volumeMounts:
        - name: workdir
          mountPath: /usr/share/nginx/html
  volumes:
    - name: workdir
      emptyDir: {}
```

**Short explanation of main fields**

- `apiVersion: v1` — tells Kubernetes this object uses the core v1 API.
- `kind: Pod` — this resource is a Pod.
- `metadata.name` — the Pod name I use in `kubectl` commands.
- `spec.initContainers` — containers that run once and must finish before the main containers start.
- `initContainers[].image` — the busybox image used only for the download step.
- `initContainers[].command` — runs `wget` and saves HTML into the shared folder.
- `initContainers[].volumeMounts` — attaches the shared volume at `/work-dir` inside the init container.
- `spec.containers` — the main workload after init success.
- `containers[].image` — nginx serves static files for the lab demo.
- `volumeMounts` on nginx — maps the same disk to `/usr/share/nginx/html` so the file is the web root.
- `spec.volumes` — declares `workdir` as `emptyDir` storage shared by init and main containers.

Simulated apply:

```
$ kubectl apply -f k8s/init-containers/init-download.yaml
pod/init-download-pod created
```

Simulated watch:

```
$ kubectl get pods -w
NAME                READY   STATUS            RESTARTS   AGE
init-download-pod   0/1     Init:0/1          0          3s
init-download-pod   0/1     PodInitializing   0          4s
init-download-pod   1/1     Running           0          6s
```

Simulated init logs:

```
$ kubectl logs init-download-pod -c init-download
Connecting to example.com (93.184.216.34:443)
Saving to: '/work-dir/index.html'
index.html            100% |*****************************|  1256  0:00:00 ETA
'/work-dir/index.html' saved [1256]
```

Simulated check of the downloaded page in nginx:

```
$ kubectl exec init-download-pod -- cat /usr/share/nginx/html/index.html
<!doctype html>
<html>
<head>
    <title>Example Domain</title>

    <meta charset="utf-8" />
    <meta http-equiv="Content-type" content="text/html; charset=utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style type="text/css">
    body {
        background-color: #f0f0f2;
        margin: 0;
        padding: 0;
        font-family: -apple-system, system-ui, BlinkMacSystemFont, "Segoe UI", "Open Sans", "Helvetica Neue", Helvetica, Arial, sans-serif;
```

### wait-for-service.yaml (full manifest)

If I apply the whole file on a new cluster and the Service is created in the same moment as the Pod, both objects show up at once:

```
$ kubectl apply -f k8s/init-containers/wait-for-service.yaml
pod/wait-pod created
service/myservice created
```

Below is the full YAML in the repository.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: wait-pod
spec:
  initContainers:
    - name: wait-for-service
      image: busybox:1.36
      command:
        - sh
        - -c
        - until nslookup myservice; do echo waiting for myservice; sleep 2; done
  containers:
    - name: nginx
      image: nginx:1.25
      ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: myservice
spec:
  ports:
    - port: 80
      targetPort: 8080
```

**Short explanation of main fields**

- `metadata.name: wait-pod` — name of the Pod that waits for DNS.
- `initContainers[].command` — loops with `nslookup myservice` until the name resolves.
- `containers` — main nginx container starts only after the init loop exits.
- Second `---` document — separates the Pod from the Service in one file.
- `kind: Service` — creates cluster DNS for `myservice`.
- `metadata.name: myservice` — this is the DNS name the init container looks up.
- `spec.ports` — defines port 80 for the Service object (the lab only needs the name to exist in DNS).

**Demo: Pod before Service**

First I apply only the Pod document so `myservice` does not exist yet:

```
$ awk 'BEGIN{p=1} /^---$/{if(p==1){p=0;exit}} {print}' k8s/init-containers/wait-for-service.yaml | kubectl apply -f -
pod/wait-pod created
```

```
$ kubectl get pods -w
NAME       READY   STATUS     RESTARTS   AGE
wait-pod   0/1     Init:0/1   0          12s
```

```
$ kubectl logs wait-pod -c wait-for-service
waiting for myservice
Server:		10.96.0.10
Address:	10.96.0.10:53

** server can't find myservice.default.svc.cluster.local: NXDOMAIN

waiting for myservice
waiting for myservice
```

**Then I create the Service**

```
$ kubectl apply -f k8s/init-containers/wait-for-service.yaml
pod/wait-pod configured
service/myservice created
```

Watch after the Service exists:

```
$ kubectl get pods -w
NAME       READY   STATUS     RESTARTS   AGE
wait-pod   0/1     Init:0/1   0          45s
wait-pod   0/1     PodInitializing   0   46s
wait-pod   1/1     Running           0   48s
```

### Why this pattern matters in production

In production, many apps depend on a database or another API. An init container can wait until that dependency exists in DNS or answers on the network. This ordering stops crash loops where the main container starts too early. Teams get a clear log from the init step when something is still missing. Together, that gives safer rollouts and easier debugging than starting every container at the same time.
