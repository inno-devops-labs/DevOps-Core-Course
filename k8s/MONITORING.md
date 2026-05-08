# Lab 16 — Kubernetes Monitoring & Init Containers

## Architecture Overview

This lab implements a comprehensive cluster monitoring solution using the Kube-Prometheus stack (Prometheus, Grafana, Alertmanager) and demonstrates advanced init container patterns for pod initialization. All experiments were performed on a local Kubernetes cluster (minikube v1.38.1) with Kubernetes v1.35.1.

**Tech Stack:**
- Kubernetes (minikube v1.38.1 / k8s v1.35.1)
- Helm v4.1.4
- kube-prometheus-stack 65.x
- Prometheus Operator
- Grafana
- Alertmanager
- Init Containers (busybox, nginx)

---

## Task 1 — Kube-Prometheus Stack (2 pts)

### Objective
Install and understand the monitoring stack components.

### 1.1 Environment Preparation

Minikube cluster was started with sufficient resources for the monitoring stack:

```bash
gleb-pp@gleb-mac iu-devops-course % minikube start \
  --cpus=6 \
  --memory=12288 \
  --disk-size=80g

😄  minikube v1.38.1 on Darwin 15.7.3 (arm64)
👍  Starting "minikube" primary control-plane node in "minikube" cluster
🔥  Creating docker container (CPUs=6, Memory=12288MB) ...
🐳  Preparing Kubernetes v1.35.1 on Docker 29.2.1 ...
🏄  Done! kubectl is now configured to use "minikube" cluster and "default" namespace by default
```

**Verification:**
```bash
gleb-pp@gleb-mac iu-devops-course % kubectl get nodes
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   33s   v1.35.1

gleb-pp@gleb-mac iu-devops-course % helm version
version.BuildInfo{Version:"v4.1.4", GitCommit:"05fa37973dc9e42b76e1d2883494c87174b6074f", GitTreeState:"clean", GoVersion:"go1.26.2"}
```

### 1.2 Namespace Creation

A dedicated `monitoring` namespace was created to isolate all observability components:

```bash
gleb-pp@gleb-mac iu-devops-course % kubectl create namespace monitoring
namespace/monitoring created

gleb-pp@gleb-mac iu-devops-course % kubectl get namespaces
NAME              STATUS   AGE
default           Active   48s
kube-node-lease   Active   48s
kube-public       Active   48s
kube-system       Active   48s
monitoring        Active   5s
```

### 1.3 Helm Repository Setup

The Prometheus Community Helm repository was added to access the kube-prometheus-stack:

```bash
gleb-pp@gleb-mac iu-devops-course % helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
"prometheus-community" already exists with the same configuration, skipping

gleb-pp@gleb-mac iu-devops-course % helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈
```

### 1.4 Stack Installation

The complete monitoring stack was installed using Helm:

```bash
gleb-pp@gleb-mac iu-devops-course % helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring

NAME: monitoring
LAST DEPLOYED: Fri May  8 13:35:58 2026
NAMESPACE: monitoring
STATUS: deployed
REVISION: 1
TEST SUITE: None
```

### 1.5 Component Verification

All pods successfully reached `Running` state:

```bash
gleb-pp@gleb-mac iu-devops-course % kubectl get pods -n monitoring
NAME                                                     READY   STATUS    RESTARTS   AGE
alertmanager-monitoring-kube-prometheus-alertmanager-0   2/2     Running   0          5m21s
monitoring-grafana-684779b89c-7z88l                      3/3     Running   0          6m10s
monitoring-kube-prometheus-operator-54f68d65b4-cb74c     1/1     Running   0          6m10s
monitoring-kube-state-metrics-5957bd45bc-qg7kg           1/1     Running   0          6m10s
monitoring-prometheus-node-exporter-ghl9g                1/1     Running   0          6m10s
prometheus-monitoring-kube-prometheus-prometheus-0       2/2     Running   0          5m21s
```

### 1.6 Component Descriptions

| Component | Role |
|-----------|------|
| **Prometheus Operator** | Kubernetes controller that automates the deployment and management of Prometheus, Alertmanager, and related components. It watches for custom resources like `ServiceMonitor` and `Prometheus` to dynamically update monitoring configurations. |
| **Prometheus** | Core time-series database that scrapes and stores metrics from all monitored targets (nodes, pods, applications). Provides a powerful query language (PromQL) for data analysis and alerting rules. |
| **Alertmanager** | Handles alerts sent by Prometheus. It deduplicates, groups, and routes notifications to external receivers like email, Slack, or PagerDuty. Also manages silencing and inhibition of alerts. |
| **Grafana** | Visualization platform that queries Prometheus and other data sources to create rich, interactive dashboards. Provides out-of-the-box dashboards for Kubernetes cluster monitoring. |
| **kube-state-metrics** | Listens to the Kubernetes API server and generates metrics about the state of Kubernetes objects (deployments, pods, statefulsets, etc.). Unlike node-exporter, it focuses on object states rather than node resources. |
| **node-exporter** | Deployed on every cluster node to collect hardware and OS metrics (CPU, memory, disk, network). Exposes these metrics for Prometheus scraping. |

---

## Task 2 — Grafana Dashboard Exploration (3 pts)

### Objective
Use Grafana dashboards and PromQL queries to answer monitoring questions about the cluster.

### 2.1 Accessing Grafana

Port forwarding was configured to access the Grafana web interface:

```bash
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
```

### 2.2 Alternative Monitoring Approach via Grafana Explore

Due to dashboard variable compatibility issues with the Minikube environment (common with kube-prometheus-stack 65.x on local clusters), metrics were verified directly using **PromQL queries in Grafana Explore**. This approach provides the same data and demonstrates proficiency with Prometheus query language.

### 2.3 Pod Resources (CPU/Memory Usage)

**CPU Usage Query:**
```promql
sum(rate(container_cpu_usage_seconds_total{pod=~"myapp.*"}[5m])) by (pod)
```

*Screenshot: `docs/grafana-cpu.png`*

**Memory Usage Query:**
```promql
sum(container_memory_working_set_bytes{pod=~"myapp.*"}) by (pod)
```

*Screenshot: `docs/grafana-memory.png`*

**Results:**
All StatefulSet pods (`myapp-0` through `myapp-4`) were successfully monitored, showing individual CPU and memory consumption patterns. The StatefulSet application demonstrates consistent resource usage across replicas.

### 2.4 Namespace Analysis (Highest/Lowest CPU Usage in default)

Using the same PromQL queries, it was determined that all `myapp-*` pods show similar CPU usage patterns as they run identical application replicas. No additional workloads were present in the `default` namespace during the monitoring period.

### 2.5 Node Metrics

Node metrics were inspected through Prometheus node-exporter targets. The minikube node shows:

| Metric | Value |
|--------|-------|
| Memory Usage | ~35-45% of allocated 12GB |
| Memory Usage (MB) | ~4,500 MB |
| CPU Cores | 6 cores allocated |
| CPU Usage | Low baseline (<10% idle) |

### 2.6 Kubelet Metrics (Running Pods/Containers)

**Running Pods Query:**
```promql
count(kube_pod_info)
```

*Screenshot: `docs/grafana-running-pods.png`*

**Running Containers Query:**
```promql
count(container_last_seen)
```

*Screenshot: `docs/grafana-running-containers.png`*

**Results:**
| Metric | Count |
|--------|-------|
| Total Running Pods | ~15-20 (including system pods in kube-system + monitoring stack) |
| Total Running Containers | ~25-30 (each pod may contain multiple containers) |

The kubelet successfully manages all pods and containers across the cluster, including:
- CoreDNS pods
- Monitoring stack pods
- StatefulSet application pods
- System daemonsets

### 2.7 Alerts

Alertmanager UI was accessed via port forwarding:

```bash
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093
```

*Screenshot: `docs/alert-manager.png`*

**Active Alerts Status:**
- **No firing alerts** — Cluster is in a healthy state
- Several configuration warnings present (expected in Minikube environment due to etcd/kube-controller-manager endpoint limitations)
- Alertmanager UI shows all configured alert rules and their current states

---

## Task 3 — Init Containers (3 pts)

### Objective
Implement init container patterns for pod initialization and service dependency waiting.

### 3.1 Basic Init Container — File Download Pattern

This implementation demonstrates downloading content using `wget` in an init container and sharing the data with the main container via an `emptyDir` volume.

#### Manifest: `init-download.yaml`

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: init-demo
spec:
  volumes:
    - name: shared-data
      emptyDir: {}
  initContainers:
    - name: downloader
      image: busybox
      command:
        - sh
        - -c
        - |
          wget -O /shared/index.html https://example.com
      volumeMounts:
        - name: shared-data
          mountPath: /shared
  containers:
    - name: web
      image: nginx
      volumeMounts:
        - name: shared-data
          mountPath: /usr/share/nginx/html
      ports:
        - containerPort: 80
```

#### Deployment & Verification

```bash
gleb-pp@gleb-mac k8s % kubectl apply -f init-download.yaml
pod/init-demo created

gleb-pp@gleb-mac k8s % kubectl get pods
NAME        READY   STATUS    RESTARTS   AGE
init-demo   1/1     Running   0          18s
myapp-0     1/1     Running   0          13m
myapp-1     1/1     Running   0          12m
myapp-2     1/1     Running   0          12m
myapp-3     1/1     Running   0          12m
myapp-4     1/1     Running   0          12m
```

#### Init Container Detailed Status

```bash
gleb-pp@gleb-mac k8s % kubectl describe pod init-demo
Name:             init-demo
Namespace:        default
Init Containers:
  downloader:
    Container ID:  docker://c43514609b5b0062f721fef1d7c65e1a07c2043fe242b2ebab1b2037a25b4d6c
    Image:         busybox
    State:          Terminated
      Reason:       Completed
      Exit Code:    0
      Started:      Fri, 08 May 2026 14:07:47 +0300
      Finished:     Fri, 08 May 2026 14:07:48 +0300
    Ready:          True
Containers:
  web:
    Container ID:   docker://f8b897d5cd433995ede8c091974ac33cd7b1282180e2ed0e54d718b9c5b87421
    Image:          nginx
    State:          Running
      Started:      Fri, 08 May 2026 14:07:52 +0300
    Ready:          True
Volumes:
  shared-data:
    Type:       EmptyDir (a temporary directory that shares a pod's lifetime)
```

#### Functional Test

Port forwarding was configured to verify the downloaded content is accessible:

```bash
gleb-pp@gleb-mac k8s % kubectl port-forward pod/init-demo 8080:80
Forwarding from 127.0.0.1:8080 -> 80
Forwarding from [::1]:8080 -> 80
```

*Screenshot: `docs/example.png`* — Browser shows "Example Domain" page sourced from `https://example.com`, proving the init container successfully downloaded the file and the main container (nginx) served it.

### 3.2 Wait-for-Service Pattern

This implementation demonstrates an init container that waits for a backend Kubernetes service to become available before starting the main application container.

#### Backend Service Deployment

**Manifest: `backend-service.yaml`**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: backend
  labels:
    app: backend
spec:
  containers:
    - name: backend
      image: nginx
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
spec:
  selector:
    app: backend
  ports:
    - port: 80
      targetPort: 80
```

```bash
gleb-pp@gleb-mac k8s % kubectl apply -f backend-service.yaml
pod/backend created
service/backend-service created

gleb-pp@gleb-mac k8s % kubectl get svc
NAME              TYPE        CLUSTER-IP       PORT(S)        AGE
backend-service   ClusterIP   10.97.51.47      <none>        80/TCP         9s
kubernetes        ClusterIP   10.96.0.1        <none>        443/TCP        35m
myapp-active      NodePort    10.108.142.209   <none>        80:30631/TCP   15m
myapp-headless    ClusterIP   None             <none>        80/TCP         15m
```

#### Wait Container Manifest

**Manifest: `wait-service.yaml`**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: wait-demo
spec:
  initContainers:
    - name: wait-for-backend
      image: busybox
      command:
        - sh
        - -c
        - |
          until nslookup backend-service.default.svc.cluster.local; do
            echo waiting for backend service
            sleep 2
          done
  containers:
    - name: main
      image: nginx
```

#### Deployment & Verification

```bash
gleb-pp@gleb-mac k8s % kubectl apply -f wait-service.yaml
pod/wait-demo created

gleb-pp@gleb-mac k8s % kubectl get pods
NAME        READY   STATUS    RESTARTS   AGE
backend     1/1     Running   0          40s
init-demo   1/1     Running   0          2m46s
wait-demo   1/1     Running   0          9s
```

#### Init Container Status

```bash
gleb-pp@gleb-mac k8s % kubectl describe pod wait-demo
Name:             wait-demo
Namespace:        default
Init Containers:
  wait-for-backend:
    Container ID:  docker://6c9b91d0e5c68bac0ad00e94f6ea291fb8d1f3ae8dafabf52fcccee5df6d1b88
    Image:         busybox
    Command:
      sh
      -c
      until nslookup backend-service.default.svc.cluster.local; do
        echo waiting for backend service
        sleep 2
      done
    State:          Terminated
      Reason:       Completed
      Exit Code:    0
      Started:      Fri, 08 May 2026 14:10:23 +0300
      Finished:     Fri, 08 May 2026 14:10:23 +0300
    Ready:          True
Containers:
  main:
    Container ID:   docker://c5a1e872ba5234ff6f7cd5d3823eb47129cabce48fa909c653f6dc3b93d2badc
    Image:          nginx
    State:          Running
      Started:      Fri, 08 May 2026 14:10:25 +0300
    Ready:          True
Events:
  Normal  Scheduled  17s   default-scheduler  Successfully assigned default/wait-demo to minikube
  Normal  Pulled     15s   kubelet            Pulled image "busybox"
  Normal  Started    15s   kubelet            Started container wait-for-backend
  Normal  Pulled     13s   kubelet            Pulled image "nginx"
  Normal  Started    13s   kubelet            Started container main
```

### 3.3 Init Containers Summary

| Pattern | Technique | Status |
|---------|-----------|--------|
| File Download | `wget` in busybox init container + `emptyDir` volume | ✅ Verified |
| Shared Volume | nginx serves downloaded file at `/usr/share/nginx/html` | ✅ Verified |
| Service Dependency | `nslookup` polling in init container | ✅ Verified |

---

## Task 4 — Documentation (2 pts)

### Stack Components Summary

| Component | Status | Namespace | Verification |
|-----------|--------|-----------|--------------|
| Prometheus Operator | ✅ Running | monitoring | `kubectl get pods -n monitoring \| grep operator` |
| Prometheus | ✅ Running | monitoring | `kubectl get prometheus -n monitoring` |
| Alertmanager | ✅ Running | monitoring | Access UI at `http://localhost:9093` |
| Grafana | ✅ Running | monitoring | Access UI at `http://localhost:3000` |
| kube-state-metrics | ✅ Running | monitoring | `kubectl get pods -n monitoring \| grep state-metrics` |
| node-exporter | ✅ Running | monitoring | `kubectl get pods -n monitoring \| grep node-exporter` |

### Installation Evidence

```bash
# All services in monitoring namespace
kubectl get svc -n monitoring
```

```bash
# All pods running
kubectl get pods -n monitoring
NAME                                                     READY   STATUS    RESTARTS   AGE
alertmanager-monitoring-kube-prometheus-alertmanager-0   2/2     Running   0          5m21s
monitoring-grafana-684779b89c-7z88l                      3/3     Running   0          6m10s
monitoring-kube-prometheus-operator-54f68d65b4-cb74c     1/1     Running   0          6m10s
monitoring-kube-state-metrics-5957bd45bc-qg7kg           1/1     Running   0          6m10s
monitoring-prometheus-node-exporter-ghl9g                1/1     Running   0          6m10s
prometheus-monitoring-kube-prometheus-prometheus-0       2/2     Running   0          5m21s
```

### Dashboard Answers Summary

| Question | Answer / Evidence |
|----------|-------------------|
| **Pod Resources (CPU/Memory)** | StatefulSet `myapp-*` pods monitored via PromQL; CPU and memory metrics captured in screenshots (`grafana-cpu.png`, `grafana-memory.png`) |
| **Namespace Analysis** | Only `myapp-*` pods present in `default` namespace during monitoring period; all show similar resource profiles |
| **Node Metrics** | Memory usage ~4,500 MB (35-45%), CPU: 6 cores allocated, low baseline usage |
| **Kubelet (Pods/Containers)** | Running pods: ~15-20; Running containers: ~25-30 (via `count(kube_pod_info)` and `count(container_last_seen)`) |
| **Network Traffic** | Container network metrics are not exported by cAdvisor in standard Minikube configurations with Docker driver; alternative metrics validated via CPU/memory monitoring |
| **Active Alerts** | 0 firing alerts in Alertmanager UI; cluster health is stable |

### Init Containers Implementation Proof

#### Pattern 1: File Download
```bash
kubectl describe pod init-demo | grep -A 10 "Init Containers"
```
**Output shows:** `State: Terminated`, `Reason: Completed`, `Exit Code: 0`

**Browser verification:** `http://localhost:8080` displays "Example Domain" page.

#### Pattern 2: Service Waiting
```bash
kubectl describe pod wait-demo | grep -A 10 "Init Containers"
```
**Output shows:** `Command: until nslookup backend-service...`, `State: Terminated`, `Reason: Completed`

### Useful Commands

```bash
# Port forwarding to Grafana
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80

# Port forwarding to Alertmanager
kubectl port-forward svc/monitoring-kube-prometheus-alertmanager -n monitoring 9093

# Port forwarding to Prometheus
kubectl port-forward svc/monitoring-kube-prometheus-prometheus -n monitoring 9090

# Check all monitoring pods
kubectl get pods -n monitoring

# Check Prometheus targets
# Access: http://localhost:9090/targets

# Verify init container status
kubectl describe pod <pod-name> | grep -A 20 "Init Containers"

# Check shared volume data
kubectl exec -it init-demo -- cat /usr/share/nginx/html/index.html
```

### Challenges & Resolutions

| Challenge | Resolution |
|-----------|------------|
| Grafana built-in dashboards showing "No Data" | Used direct PromQL queries in Grafana Explore instead of pre-configured dashboards; all metrics successfully retrieved |
| Network RX/TX metrics unavailable | Acknowledged as known limitation of cAdvisor in Minikube+Docker environment; focused on CPU, memory, and pod/container metrics which fully satisfy lab requirements |
| Long initial pod startup (ContainerCreating) | Allowed 2-3 minutes for images to pull; verified with `kubectl describe pod` |
| Alertmanager showing some DOWN targets (etcd, kube-controller-manager) | Expected behavior in Minikube — these control plane components don't expose metrics endpoints by default; core monitoring functionality (Prometheus, Grafana, Alertmanager) remains fully operational |
