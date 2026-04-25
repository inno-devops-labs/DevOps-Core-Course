# Lab 16 — Kubernetes Monitoring & Init Containers

## Task 1 – Kube-Prometheus Stack

### 1.1 Component Roles

| Component | Description |
|-----------|-------------|
| **Prometheus Operator** | A Kubernetes operator that manages the lifecycle of Prometheus, Alertmanager, and related monitoring resources. It automates configuration (e.g., ServiceMonitors). |
| **Prometheus** | The main metrics system: scrapes metrics from configured targets, stores them as time‑series data, and evaluates alerting rules. |
| **Alertmanager** | Handles alerts sent by Prometheus: deduplicates, groups, routes, and sends notifications to external receivers (Slack, email, etc.). |
| **Grafana** | Provides rich visualisation dashboards. It queries Prometheus (or other data sources) and displays metrics as graphs, tables, etc. |
| **kube-state-metrics** | Exposes metrics about the state of Kubernetes objects (deployments, pods, nodes, etc.) by listening to the API server. |
| **node-exporter** | A Prometheus exporter that collects hardware and OS metrics from each node (CPU, memory, disk, network). |

### 1.2 Installation via Helm

Commands used for installation:

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

kubectl create namespace monitoring
helm install monitoring prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace

kubectl wait --for=condition=ready pod -l 'release=monitoring' -n monitoring --timeout=300s
```

Verification output:

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get po,svc -n monitoring
NAME                                                         READY   STATUS    RESTARTS   AGE
pod/alertmanager-monitoring-kube-prometheus-alertmanager-0   2/2     Running   0          2m51s
pod/monitoring-grafana-85f8f4b6c5-g7tt4                      3/3     Running   0          3m33s
pod/monitoring-kube-prometheus-operator-84c76446b8-kcvnl     1/1     Running   0          3m33s
pod/monitoring-kube-state-metrics-7d69554b96-d2r65           1/1     Running   0          3m34s
pod/monitoring-prometheus-node-exporter-7qm8w                1/1     Running   0          3m34s
pod/prometheus-monitoring-kube-prometheus-prometheus-0       2/2     Running   0          2m49s

NAME                                              TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)                      AGE
service/alertmanager-operated                     ClusterIP   None             <none>        9093/TCP,9094/TCP,9094/UDP   2m51s
service/monitoring-grafana                        ClusterIP   10.102.200.219   <none>        80/TCP                       3m35s
service/monitoring-kube-prometheus-alertmanager   ClusterIP   10.108.11.141    <none>        9093/TCP,8080/TCP            3m35s
service/monitoring-kube-prometheus-operator       ClusterIP   10.101.221.198   <none>        443/TCP                      3m35s
service/monitoring-kube-prometheus-prometheus     ClusterIP   10.98.91.110     <none>        9090/TCP,8080/TCP            3m35s
service/monitoring-kube-state-metrics             ClusterIP   10.103.222.48    <none>        8080/TCP                     3m35s
service/monitoring-prometheus-node-exporter       ClusterIP   10.103.199.84    <none>        9100/TCP                     3m35s
service/prometheus-operated                       ClusterIP   None             <none>        9090/TCP                     2m49s
PS C:\Users\zagur\DevOps\DevOps-Core-Course>
```

## Task 2 – Grafana Dashboard Explorarion

At first, we need to enter UI for Grafana:

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> helm install monitoring prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace
NAME: monitoring
LAST DEPLOYED: Sat Apr 25 16:26:10 2026
NAMESPACE: monitoring
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
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
Forwarding from 127.0.0.1:3000 -> 3000
Forwarding from [::1]:3000 -> 3000
```

### Answers to questions

1. **Pod Resources** – CPU / memory usage

    - **Dashboard:** Kubernetes / Compute Resources / Pod (I used pod from `dev` namespace for demonstration)
    - **Filter:** Namespace `stateful`, Pod `stateful-release-devops-info-service-0`

    | Metric | Value |
    |--------|-------|
    | CPU usage | 0.0500 CPUs |
    | Memory usage | 64 MiB |

    ![](/k8s/screenshots/resources.png)

2. **Namespace Analysis** – Which pods use most / least CPU in default namespace?

        - **Dashboard:** Kubernetes / Compute Resources / Namespace (Pods)
        - **Filter:** Namespace default

        ![](/k8s/screenshots/default.png)

        In my cluster in `default` namespace there no active pods. All pods are in `dev` or `prod` namespaces.

        ```bash
        PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl top pods -n dev
        NAME                                               CPU(cores)   MEMORY(bytes)   
        dev-release-devops-info-service-649799c4cc-97sbb   3m           39Mi            
        dev-release-devops-info-service-649799c4cc-h9llw   2m           39Mi            
        dev-release-devops-info-service-649799c4cc-kw2dq   2m           39Mi            
        dev-release-devops-info-service-649799c4cc-r99x9   2m           39Mi            
        dev-release-devops-info-service-649799c4cc-t2897   2m           39Mi
        ```

        ![](/k8s/screenshots/dev_prom.png)

3. Node Metrics – Memory usage and CPU cores

    - **Dashboard:** Node Exporter / Nodes
    - **Node:** minikube

    | Metric | Value |
    |--------|-------|
    | Memory usage (percentage) | 40.6% |
    | Memory usage (MB) | 3246 MB / 8192 MB |
    | CPU cores used | ~0.36 cores (4.5% out of 8 cores) |

    ![](/k8s/screenshots/node.png) 

4. Kubelet – How many pods/containers managed?

    - **Dashboard:** Kubernetes / Kubelet
    - **Look for:** `Number of Pods` and `Number of Containers` panels

    ![](/k8s/screenshots/kubelet.png)

5. Network – Traffic for pods in `default` namespace

    - **Dashboard:** Kubernetes / Compute Resources / Namespace (Pods)
    - **Metric:** Network Received Bytes, Network Transmitted Bytes
    - **Filter:** namespace `default`

    ![](/k8s/screenshots/network.png)
    
    All panels show `No data` because there are no user pods in the `default` namespace. All workloads are deployed in `dev` and `prod`.

6. Alerts – How many active alerts?

    Alertmanager shows 1 active alert – Watchdog (severity="none"). This is a heartbeat alert and does not indicate any problem. Therefore the number of actual active alerts is 0.

    ![](/k8s/screenshots/alert.png)

## Task 3 – Init Containers

### 3.1 Basic Init Container – Download a file

**YAML:** `init-download.yaml`

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: init-download-demo
spec:
  initContainers:
  - name: downloader
    image: busybox:1.36
    command: ['sh', '-c', 'wget -O /work-dir/index.html https://example.com']
    volumeMounts:
    - name: workdir
      mountPath: /work-dir
  containers:
  - name: main
    image: busybox:1.36
    command: ['sh', '-c', 'echo "Main container started"; sleep 300']
    volumeMounts:
    - name: workdir
      mountPath: /data
  volumes:
  - name: workdir
    emptyDir: {}
```

Output:

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course\k8s\init> kubectl apply -f init-download.yaml
pod/init-download-demo created
PS C:\Users\zagur\DevOps\DevOps-Core-Course\k8s\init> kubectl get pods -w                
NAME                 READY   STATUS     RESTARTS   AGE
init-download-demo   0/1     Init:0/1   0          5s
init-download-demo   0/1     Init:0/1   0          8s
init-download-demo   0/1     PodInitializing   0          9s
init-download-demo   1/1     Running           0          10s
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course\k8s\init> kubectl logs init-download-demo -c downloader
Connecting to example.com (104.20.23.154:443)
wget: note: TLS certificate validation not implemented
saving to '/work-dir/index.html'
index.html           100% |********************************|   528  0:00:00 ETA
'/work-dir/index.html' saved
PS C:\Users\zagur\DevOps\DevOps-Core-Course\k8s\init> 
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course\k8s\init> kubectl exec init-download-demo -- cat /data/index.html  
Defaulted container "main" out of: main, downloader (init)
<!doctype html><html lang="en"><head><title>Example Domain</title><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{background:#eee;width:60vw;margin:15vh auto;font-family:system-ui,sans-serif}h1{font-size:1.5em}div{opacity:0.8}a:link,a:visited{color:#348}</style></head><body><div><h1>Example Domain</h1><p>This domain is for use in documentation examples without needing permission. Avoid use in operations.</p><p><a href="https://iana.org/domains/example">Learn more</a></p></div></body></html>
PS C:\Users\zagur\DevOps\DevOps-Core-Course\k8s\init> 
```

### 3.2 Wait‑for‑Service Pattern

**YAML:** `init-wait.yaml`

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: init-wait-demo
spec:
  initContainers:
  - name: waiter
    image: busybox:1.36
    command: ['sh', '-c', 'until nslookup kubernetes.default.svc.cluster.local; do echo "Waiting for DNS..."; sleep 2; done']
  containers:
  - name: main
    image: busybox:1.36
    command: ['sh', '-c', 'echo "Service is ready – starting main container"; sleep 300']
```

Output:

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course\k8s\init> kubectl apply -f init-wait.yaml                                  
pod/init-wait-demo created
PS C:\Users\zagur\DevOps\DevOps-Core-Course\k8s\init> kubectl logs init-wait-demo -c waiter -f
Server:         10.96.0.10
Address:        10.96.0.10:53

Name:   kubernetes.default.svc.cluster.local
Address: 10.96.0.1
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course\k8s\init> kubectl describe pod init-wait-demo
Name:             init-wait-demo
Namespace:        default
Priority:         0
Service Account:  default
Node:             minikube/192.168.49.2
Start Time:       Sat, 25 Apr 2026 16:39:22 +0300
Labels:           <none>
Annotations:      <none>
Status:           Running
IP:               10.244.0.185
IPs:
  IP:  10.244.0.185
Init Containers:
  waiter:
    Container ID:  docker://96092ec15481e16df03d4ade29ae284e6f8005b64b59542d33b57cc8888f14e5
    Image:         busybox:1.36
    Image ID:      docker-pullable://busybox@sha256:73aaf090f3d85aa34ee199857f03fa3a95c8ede2ffd4cc2cdb5b94e566b11662
    Port:          <none>
    Host Port:     <none>
    Command:
      sh
      -c
      until nslookup kubernetes.default.svc.cluster.local; do echo waiting; sleep 2; done
    State:          Terminated
      Reason:       Completed
      Exit Code:    0
      Started:      Sat, 25 Apr 2026 16:39:23 +0300
      Finished:     Sat, 25 Apr 2026 16:39:24 +0300
    Ready:          True
    Restart Count:  0
    Environment:    <none>
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-8nmgp (ro)
Containers:
  main:
    Container ID:  docker://f5a5c6479fa454a49e45eabe1ddbbc10010fe6e8f0c97d28648eb0d8d539f734
    Image:         busybox:1.36
    Image ID:      docker-pullable://busybox@sha256:73aaf090f3d85aa34ee199857f03fa3a95c8ede2ffd4cc2cdb5b94e566b11662
    Port:          <none>
    Host Port:     <none>
    Command:
      sh
      -c
      echo "Service is ready"; sleep 300
    State:          Running
      Started:      Sat, 25 Apr 2026 16:39:24 +0300
    Ready:          True
    Restart Count:  0
    Environment:    <none>
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-8nmgp (ro)
Conditions:
  Type                        Status
  PodReadyToStartContainers   True 
  Initialized                 True 
  Ready                       True 
  ContainersReady             True 
  PodScheduled                True 
Volumes:
  kube-api-access-8nmgp:
    Type:                    Projected (a volume that contains injected data from multiple sources)
    TokenExpirationSeconds:  3607
    ConfigMapName:           kube-root-ca.crt
    Optional:                false
    DownwardAPI:             true
QoS Class:                   BestEffort
Node-Selectors:              <none>
Tolerations:                 node.kubernetes.io/not-ready:NoExecute op=Exists for 300s
                             node.kubernetes.io/unreachable:NoExecute op=Exists for 300s
Events:
  Type    Reason     Age   From               Message
  ----    ------     ----  ----               -------
  Normal  Scheduled  16s   default-scheduler  Successfully assigned default/init-wait-demo to minikube
  Normal  Pulled     15s   kubelet            Container image "busybox:1.36" already present on machine
  Normal  Created    15s   kubelet            Created container: waiter
  Normal  Started    14s   kubelet            Started container waiter
  Normal  Pulled     14s   kubelet            Container image "busybox:1.36" already present on machine
  Normal  Created    14s   kubelet            Created container: main
  Normal  Started    14s   kubelet            Started container main
PS C:\Users\zagur\DevOps\DevOps-Core-Course\k8s\init> 
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course\k8s\init> kubectl logs init-wait-demo -c waiter
Server:         10.96.0.10
Address:        10.96.0.10:53


Name:   kubernetes.default.svc.cluster.local
Address: 10.96.0.1

PS C:\Users\zagur\DevOps\DevOps-Core-Course\k8s\init> 
```
