# Task 1 - Helm fundamentals

- `hel version` output
```bash
➜  DevOps-Core-Course git:(lab10) ✗ helm version
version.BuildInfo{Version:"v3.20.1", GitCommit:"a2369ca71c0ef633bf6e4fccd66d634eb379b371", GitTreeState:"clean", GoVersion:"go1.25.8"}
```

- Adding prometheus repo to helm
```bash
➜  DevOps-Core-Course git:(lab10) ✗ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
"prometheus-community" has been added to your repositories
```
```bash
➜  DevOps-Core-Course git:(lab10) ✗ helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈
```

- Search and explore charts 
```bash
➜  DevOps-Core-Course git:(lab10) ✗ helm search repo prometheus
NAME                                                    CHART VERSION   APP VERSION     DESCRIPTION                                       
prometheus-community/kube-prometheus-stack              82.15.1         v0.89.0         kube-prometheus-stack collects Kubernetes manif...
prometheus-community/prometheus                         28.14.1         v3.10.0         Prometheus is a monitoring system and time seri...
prometheus-community/prometheus-adapter                 5.3.0           v0.12.0         A Helm chart for k8s prometheus adapter           
prometheus-community/prometheus-blackbox-exporter       11.9.1          v0.28.0         Prometheus Blackbox Exporter                      
prometheus-community/prometheus-cloudwatch-expo...      0.28.1          0.16.0          A Helm chart for prometheus cloudwatch-exporter   
prometheus-community/prometheus-conntrack-stats...      0.5.35          v0.4.42         A Helm chart for conntrack-stats-exporter         
prometheus-community/prometheus-consul-exporter         1.1.1           v0.13.0         A Helm chart for the Prometheus Consul Exporter   
prometheus-community/prometheus-couchdb-exporter        1.0.1           1.0             A Helm chart to export the metrics from couchdb...
prometheus-community/prometheus-druid-exporter          1.2.0           v0.11.0         Druid exporter to monitor druid metrics with Pr...
prometheus-community/prometheus-elasticsearch-e...      7.2.1           v1.10.0         Elasticsearch stats exporter for Prometheus       
prometheus-community/prometheus-fastly-exporter         0.11.0          v10.2.0         A Helm chart for the Prometheus Fastly Exporter   
prometheus-community/prometheus-ipmi-exporter           0.8.0           v1.10.1         This is an IPMI exporter for Prometheus.          
prometheus-community/prometheus-json-exporter           0.19.2          v0.7.0          Install prometheus-json-exporter                  
prometheus-community/prometheus-kafka-exporter          3.0.1           v1.9.0          A Helm chart to export metrics from Kafka in Pr...
prometheus-community/prometheus-memcached-exporter      0.4.5           v0.15.5         Prometheus exporter for Memcached metrics         
prometheus-community/prometheus-modbus-exporter         0.1.4           0.4.1           A Helm chart for prometheus-modbus-exporter       
prometheus-community/prometheus-mongodb-exporter        3.18.0          0.49.0          A Prometheus exporter for MongoDB metrics         
prometheus-community/prometheus-mysql-exporter          2.13.0          v0.19.0         A Helm chart for prometheus mysql exporter with...
prometheus-community/prometheus-nats-exporter           2.22.1          0.19.2          A Helm chart for prometheus-nats-exporter         
prometheus-community/prometheus-nginx-exporter          1.20.8          1.5.1           A Helm chart for NGINX Prometheus Exporter        
prometheus-community/prometheus-node-exporter           4.52.2          1.10.2          A Helm chart for prometheus node-exporter         
prometheus-community/prometheus-opencost-exporter       0.1.2           1.108.0         Prometheus OpenCost Exporter                      
prometheus-community/prometheus-operator                9.3.2           0.38.1          DEPRECATED - This chart will be renamed. See ht...
prometheus-community/prometheus-operator-admiss...      0.38.0          0.90.1          Prometheus Operator Admission Webhook             
prometheus-community/prometheus-operator-crds           28.0.1          v0.90.1         A Helm chart that collects custom resource defi...
prometheus-community/prometheus-pgbouncer-exporter      0.10.0          v0.12.0         A Helm chart for prometheus pgbouncer-exporter    
prometheus-community/prometheus-pingdom-exporter        3.4.2           v0.5.6          A Helm chart for Prometheus Pingdom Exporter      
prometheus-community/prometheus-pingmesh-exporter       0.4.3           v1.2.2          Prometheus Pingmesh Exporter                      
prometheus-community/prometheus-postgres-exporter       7.5.2           v0.19.1         A Helm chart for prometheus postgres-exporter     
prometheus-community/prometheus-pushgateway             3.6.0           v1.11.2         A Helm chart for prometheus pushgateway           
prometheus-community/prometheus-rabbitmq-exporter       2.1.2           1.0.0           Rabbitmq metrics exporter for prometheus          
prometheus-community/prometheus-redis-exporter          6.22.0          v1.82.0         Prometheus exporter for Redis metrics             
prometheus-community/prometheus-smartctl-exporter       0.16.0          v0.14.0         A Helm chart for Kubernetes                       
prometheus-community/prometheus-snmp-exporter           9.13.1          v0.30.1         Prometheus SNMP Exporter                          
prometheus-community/prometheus-sql-exporter            0.5.0           v0.8            Prometheus SQL Exporter                           
prometheus-community/prometheus-stackdriver-exp...      4.12.2          v0.18.0         Stackdriver exporter for Prometheus               
prometheus-community/prometheus-statsd-exporter         1.0.0           v0.28.0         A Helm chart for prometheus stats-exporter        
prometheus-community/prometheus-systemd-exporter        0.5.2           0.7.0           A Helm chart for prometheus systemd-exporter      
prometheus-community/prometheus-to-sd                   0.5.1           v0.9.2          Scrape metrics stored in prometheus format and ...
prometheus-community/prometheus-windows-exporter        0.12.5          0.31.5          A Helm chart for prometheus windows-exporter      
prometheus-community/prometheus-yet-another-clo...      0.42.1          v0.63.0         Yace - Yet Another CloudWatch Exporter            
prometheus-community/alertmanager                       1.34.0          v0.31.1         The Alertmanager handles alerts sent by client ...
prometheus-community/alertmanager-snmp-notifier         2.1.0           v2.1.0          The SNMP Notifier handles alerts coming from Pr...
prometheus-community/jiralert                           1.8.2           v1.3.0          A Helm chart for Kubernetes to install jiralert   
prometheus-community/kube-state-metrics                 7.2.2           2.18.0          Install kube-state-metrics to generate and expo...
prometheus-community/prom-label-proxy                   0.18.0          v0.12.1         A proxy that enforces a given label in a given ...
prometheus-community/yet-another-cloudwatch-exp...      0.39.1          v0.62.1         Yace - Yet Another CloudWatch Exporter            
```

```bash
DevOps-Core-Course git:(lab10) ✗ helm show chart prometheus-community/prometheus
annotations:
  artifacthub.io/license: Apache-2.0
  artifacthub.io/links: |
    - name: Chart Source
      url: https://github.com/prometheus-community/helm-charts
    - name: Upstream Project
      url: https://github.com/prometheus/prometheus
apiVersion: v2
appVersion: v3.10.0
dependencies:
- condition: alertmanager.enabled
  name: alertmanager
  repository: https://prometheus-community.github.io/helm-charts
  version: 1.34.*
- condition: kube-state-metrics.enabled
  name: kube-state-metrics
  repository: https://prometheus-community.github.io/helm-charts
  version: 7.2.*
- condition: prometheus-node-exporter.enabled
  name: prometheus-node-exporter
  repository: https://prometheus-community.github.io/helm-charts
  version: 4.52.*
- condition: prometheus-pushgateway.enabled
  name: prometheus-pushgateway
  repository: https://prometheus-community.github.io/helm-charts
  version: 3.6.*
description: Prometheus is a monitoring system and time series database.
home: https://prometheus.io/
icon: https://raw.githubusercontent.com/prometheus/prometheus.github.io/master/assets/prometheus_logo-cb55bb5c346.png
keywords:
- monitoring
- prometheus
kubeVersion: '>=1.19.0-0'
maintainers:
- email: gianrubio@gmail.com
  name: gianrubio
  url: https://github.com/gianrubio
- email: zanhsieh@gmail.com
  name: zanhsieh
  url: https://github.com/zanhsieh
- email: miroslav.hadzhiev@gmail.com
  name: Xtigyro
  url: https://github.com/Xtigyro
- email: naseem@transit.app
  name: naseemkullah
  url: https://github.com/naseemkullah
- email: rootsandtrees@posteo.de
  name: zeritti
  url: https://github.com/zeritti
name: prometheus
sources:
- https://github.com/prometheus/alertmanager
- https://github.com/prometheus/prometheus
- https://github.com/prometheus/pushgateway
- https://github.com/prometheus/node_exporter
- https://github.com/kubernetes/kube-state-metrics
type: application
version: 28.14.1
```
- Inspect char structure

```bash
➜  k8s git:(lab10) ✗ helm pull prometheus-community/prometheus --untar
➜  k8s git:(lab10) ✗ cd prometheus 
➜  prometheus git:(lab10) ✗ ls
Chart.lock  Chart.yaml  README.md  charts  templates  values.schema.json  values.yaml
```

# Task 2 - Create your helm chart

- create app using helm

```bash
➜  k8s git:(lab10) ✗ helm create myapp
Creating myapp
```

After copy `deployment.yml` and `service.yml` into `myapp/templates`

- change `Chart.yml`
- change `values.yml`

- test chart
```bash 
➜  myapp git:(lab10) ✗ helm lint .
==> Linting .
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed 
```

```bash
➜  myapp git:(lab10) ✗ helm template myapp .
---
# Source: myapp/templates/service.yml
apiVersion: v1
kind: Service
metadata:
  name: my-app-service
spec:
  type: NodePort
  selector:
    app: my-app
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
      nodePort: 30080
---
# Source: myapp/templates/deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-python-app
  labels:
    app: my-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: my-app
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: my-app
          # image: zsalavat/devops-info-service-python:latest
          image: "zsalavat/devops-info-service-python:latest"
          ports:
            - containerPort: 5000

          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "200m"

          livenessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 10
            periodSeconds: 5

          readinessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 5
            periodSeconds: 3
```

```bash
➜  myapp git:(lab10) ✗ helm install myrelease .          
NAME: myrelease
LAST DEPLOYED: Sat Mar 28 21:02:17 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
TEST SUITE: None
```

- test using `kubectl`

```bash
➜  myapp git:(lab10) ✗ kubectl get all
NAME                                 READY   STATUS    RESTARTS   AGE
pod/my-python-app-598569f8d4-86ckz   1/1     Running   0          87s
pod/my-python-app-598569f8d4-8b5sl   1/1     Running   0          87s

NAME                     TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/kubernetes       ClusterIP   10.96.0.1       <none>        443/TCP        3m10s
service/my-app-service   NodePort    10.103.145.51   <none>        80:30080/TCP   87s

NAME                            READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/my-python-app   2/2     2            2           87s

NAME                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/my-python-app-598569f8d4   2         2         2       87s
➜  myapp git:(lab10) ✗ 
```

```bash
➜  myapp git:(lab10) ✗ kubectl get svc
NAME             TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
kubernetes       ClusterIP   10.96.0.1       <none>        443/TCP        3m41s
my-app-service   NodePort    10.103.145.51   <none>        80:30080/TCP   118s
➜  myapp git:(lab10) ✗ 
```

# Task 3 - Multi environment setup

To set up multienvironment setup we create to files `values-dev.yml` and `values-prod.yml`

```bash
➜  myapp git:(lab10) ✗ helm install myapp-dev . -f values-dev.yaml
NAME: myapp-dev
LAST DEPLOYED: Sat Mar 28 21:19:27 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
TEST SUITE: None
```

```bash
➜  myapp git:(lab10) ✗ helm upgrade myapp-dev . -f values-prod.yaml
Release "myapp-dev" has been upgraded. Happy Helming!
NAME: myapp-dev
LAST DEPLOYED: Sat Mar 28 21:20:57 2026
NAMESPACE: default
STATUS: deployed
REVISION: 2
TEST SUITE: None
```

# Task 4 - Chart Hooks

Created 2 hooks files `pre-install-job.yaml` and `post-install-job.yaml`

```bash
➜  myapp git:(lab10) ✗ helm install test-hooks .
kubectl get jobs
kubectl get pods
kubectl logs job/test-hooks-pre-install
NAME: test-hooks
LAST DEPLOYED: Sat Mar 28 21:23:49 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
TEST SUITE: None
No resources found in default namespace.
NAME                             READY   STATUS    RESTARTS   AGE
my-python-app-598569f8d4-8h75d   0/1     Running   0          15s
my-python-app-598569f8d4-s8j6x   0/1     Running   0          15s
error: error from server (NotFound): jobs.batch "test-hooks-pre-install" not found in namespace "default"

```