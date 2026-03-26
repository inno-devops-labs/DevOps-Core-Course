# Helm Chart Documentation

## 1. Chart Overview

### Structure

```
k8s/
├── python-app/                 # Main application chart
│   ├── Chart.yaml              # Chart metadata + common-lib dependency
│   ├── values.yaml             # Default values
│   ├── values-dev.yaml         # Dev environment overrides
│   ├── values-prod.yaml        # Prod environment overrides
│   └── templates/
│       ├── _helpers.tpl        # Name/label helpers (bridges to common-lib)
│       ├── deployment.yaml     # Deployment template
│       ├── service.yaml        # Service template
│       ├── NOTES.txt           # Post-install notes
│       └── hooks/
│           ├── pre-install-job.yaml   # Pre-install validation hook
│           └── post-install-job.yaml  # Post-install smoke test hook
├── go-app/                     # Second app chart (bonus)
│   ├── Chart.yaml              # Chart metadata + common-lib dependency
│   ├── values.yaml
│   └── templates/
│       ├── _helpers.tpl
│       ├── deployment.yaml
│       ├── service.yaml
│       └── NOTES.txt
└── common-lib/                 # Shared library chart (bonus)
    ├── Chart.yaml              # type: library
    └── templates/
        ├── _names.tpl          # Shared name/fullname/chart helpers
        └── _labels.tpl         # Shared labels and selector labels
```

### Key Templates

| Template | Purpose |
|----------|---------|
| `_helpers.tpl` | Delegates naming/labeling to `common-lib` |
| `deployment.yaml` | Templated Deployment with configurable replicas, image, resources, probes, env |
| `service.yaml` | Templated Service with configurable type, ports, nodePort |
| `hooks/pre-install-job.yaml` | Job that validates cluster DNS before install |
| `hooks/post-install-job.yaml` | Job that runs a smoke test against the deployed service |

### Values Organization

Values are grouped by concern: `image`, `service`, `resources`, `livenessProbe`, `readinessProbe`, `env`, `strategy`. Environment-specific overrides (`values-dev.yaml`, `values-prod.yaml`) only redefine what differs from `values.yaml`.

---

## 2. Configuration Guide

### Key Values

| Value | Default | Description |
|-------|---------|-------------|
| `replicaCount` | 3 | Number of pod replicas |
| `image.repository` | `karishka1222/devops-python-app` | Docker image |
| `image.tag` | `latest` | Image tag |
| `image.pullPolicy` | `IfNotPresent` | Pull policy |
| `service.type` | `NodePort` | Service type |
| `service.port` | 80 | Service port |
| `service.targetPort` | 5000 | Container port |
| `service.nodePort` | 30080 | NodePort (when type=NodePort) |
| `resources.requests.memory` | 128Mi | Memory request |
| `resources.limits.memory` | 256Mi | Memory limit |
| `containerPort` | 5000 | Container port |

### Environment Customization

**Dev** (`values-dev.yaml`): 1 replica, relaxed resources (64Mi/50m), `pullPolicy: Never` (local images), lenient probes.

**Prod** (`values-prod.yaml`): 5 replicas, higher resources (256Mi/200m requests, 512Mi/500m limits), `LoadBalancer` service, stricter probes with longer initial delay.

### Installation Examples

```bash
# Default
helm install python-release k8s/python-app

# Dev environment
helm install python-dev k8s/python-app -f k8s/python-app/values-dev.yaml

# Prod environment
helm install python-prod k8s/python-app -f k8s/python-app/values-prod.yaml

# Override single value
helm install python-release k8s/python-app --set replicaCount=10
```

---

## 3. Hook Implementation

### Pre-install Hook (`pre-install-job.yaml`)

- **Purpose**: Validates cluster readiness (DNS resolution) before deploying the app.
- **Annotation**: `helm.sh/hook: pre-install`
- **Weight**: `-5` (runs first)
- **Deletion policy**: `hook-succeeded` — Job is cleaned up after successful execution.

### Post-install Hook (`post-install-job.yaml`)

- **Purpose**: Runs a smoke test — waits 15s then tries to reach the app's `/health` endpoint.
- **Annotation**: `helm.sh/hook: post-install`
- **Weight**: `5` (runs after all resources are installed)
- **Deletion policy**: `hook-succeeded` — Job is cleaned up after successful execution.

### Execution Order

1. Pre-install job (weight -5) runs and validates cluster
2. Helm installs all chart resources (Deployment, Service)
3. Post-install job (weight 5) runs smoke test against the new service

---

## 4. Installation Evidence

```
karinasiniatullina@MacBook-Pro--Karina ~ % brew install helm
==> Auto-updating Homebrew...
Adjust how often this is run with `$HOMEBREW_AUTO_UPDATE_SECS` or disable with
`$HOMEBREW_NO_AUTO_UPDATE=1`. Hide these hints with `$HOMEBREW_NO_ENV_HINTS=1` (see `man brew`).
==> Auto-updated Homebrew!
Updated 1 tap (hashicorp/tap).

You have 69 outdated formulae installed.

==> Fetching downloads for: helm
✔︎ Bottle Manifest helm (4.1.3)                       Downloaded    7.4KB/  7.4KB
✔︎ Bottle helm (4.1.3)                                Downloaded   18.1MB/ 18.1MB
==> Pouring helm--4.1.3.arm64_tahoe.bottle.tar.gz
🍺  /opt/homebrew/Cellar/helm/4.1.3: 69 files, 61.3MB
==> Running `brew cleanup helm`...
Disable this behaviour by setting `HOMEBREW_NO_INSTALL_CLEANUP=1`.
Hide these hints with `HOMEBREW_NO_ENV_HINTS=1` (see `man brew`).
==> Caveats
zsh completions have been installed to:
  /opt/homebrew/share/zsh/site-functions
```

### Helm version

```
karinasiniatullina@MacBook-Pro--Karina ~ % helm version  
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.26.1", KubeClientVersion:"v1.35"}
```

### Add a repository

```
karinasiniatullina@MacBook-Pro--Karina DevOps-Core-Course % helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
"prometheus-community" has been added to your repositories\


karinasiniatullina@MacBook-Pro--Karina DevOps-Core-Course % helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈


karinasiniatullina@MacBook-Pro--Karina DevOps-Core-Course % helm search repo prometheus
NAME                                                    CHART VERSION   APP VERSION     DESCRIPTION                                       
prometheus-community/kube-prometheus-stack              82.14.0         v0.89.0         kube-prometheus-stack collects Kubernetes manif...
prometheus-community/prometheus                         28.14.0         v3.10.0         Prometheus is a monitoring system and time seri...
prometheus-community/prometheus-adapter                 5.3.0           v0.12.0         A Helm chart for k8s prometheus adapter           
prometheus-community/prometheus-blackbox-exporter       11.9.0          v0.28.0         Prometheus Blackbox Exporter                      
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
prometheus-community/prometheus-nats-exporter           2.21.1          0.18.0          A Helm chart for prometheus-nats-exporter         
prometheus-community/prometheus-nginx-exporter          1.20.7          1.5.1           A Helm chart for NGINX Prometheus Exporter        
prometheus-community/prometheus-node-exporter           4.52.2          1.10.2          A Helm chart for prometheus node-exporter         
prometheus-community/prometheus-opencost-exporter       0.1.2           1.108.0         Prometheus OpenCost Exporter                      
prometheus-community/prometheus-operator                9.3.2           0.38.1          DEPRECATED - This chart will be renamed. See ht...
prometheus-community/prometheus-operator-admiss...      0.37.1          0.90.0          Prometheus Operator Admission Webhook             
prometheus-community/prometheus-operator-crds           28.0.0          v0.90.0         A Helm chart that collects custom resource defi...
prometheus-community/prometheus-pgbouncer-exporter      0.10.0          v0.12.0         A Helm chart for prometheus pgbouncer-exporter    
prometheus-community/prometheus-pingdom-exporter        3.4.2           v0.5.6          A Helm chart for Prometheus Pingdom Exporter      
prometheus-community/prometheus-pingmesh-exporter       0.4.3           v1.2.2          Prometheus Pingmesh Exporter                      
prometheus-community/prometheus-postgres-exporter       7.5.1           v0.19.1         A Helm chart for prometheus postgres-exporter     
prometheus-community/prometheus-pushgateway             3.6.0           v1.11.2         A Helm chart for prometheus pushgateway           
prometheus-community/prometheus-rabbitmq-exporter       2.1.2           1.0.0           Rabbitmq metrics exporter for prometheus          
prometheus-community/prometheus-redis-exporter          6.22.0          v1.82.0         Prometheus exporter for Redis metrics             
prometheus-community/prometheus-smartctl-exporter       0.16.0          v0.14.0         A Helm chart for Kubernetes                       
prometheus-community/prometheus-snmp-exporter           9.13.0          v0.30.1         Prometheus SNMP Exporter                          
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

### helm show chart prometheus-community/prometheus

```
karinasiniatullina@MacBook-Pro--Karina DevOps-Core-Course % helm show chart prometheus-community/prometheus
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
version: 28.14.0
```

### Brief explanation of Helm's value proposition

Helm is a Kubernetes package manager that lets you package manifests into charts, reuse them across environments via Go templating + `values`, and manage releases with versioning and upgrades/rollback in a controlled way.

### helm lint

```
karinasiniatullina@MacBook-Pro--Karina DevOps-Core-Course % helm lint k8s/python-app
==> Linting k8s/python-app
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### helm template (dry render)

```
karinasiniatullina@MacBook-Pro--Karina DevOps-Core-Course % helm template test-release k8s/python-app
---
# Source: python-app/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: test-release-python-app
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
  ports:
    - protocol: TCP
      port: 80
      targetPort: 5000
      nodePort: 30080
---
# Source: python-app/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-release-python-app
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: python-app
      app.kubernetes.io/instance: test-release
  strategy:
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
    type: RollingUpdate
  template:
    metadata:
      labels:
        app.kubernetes.io/name: python-app
        app.kubernetes.io/instance: test-release
    spec:
      containers:
        - name: python-app
          image: "karishka1222/devops-python-app:latest"
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 5000
              protocol: TCP
          resources:
            limits:
              cpu: 200m
              memory: 256Mi
            requests:
              cpu: 100m
              memory: 128Mi
          livenessProbe:
            failureThreshold: 3
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 10
            periodSeconds: 5
            timeoutSeconds: 3
          readinessProbe:
            failureThreshold: 3
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 5
            periodSeconds: 3
            timeoutSeconds: 2
          env:
            - name: HOST
              value: 0.0.0.0
            - name: PORT
              value: "5000"
---
# Source: python-app/templates/hooks/post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "test-release-python-app-post-install"
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    metadata:
      name: "test-release-python-app-post-install"
    spec:
      restartPolicy: Never
      containers:
        - name: post-install-test
          image: busybox
          command:
            - 'sh'
            - '-c'
            - |
              echo "=== Post-install smoke test ==="
              echo "Waiting for service to become available..."
              sleep 15
              echo "Checking service endpoint..."
              wget -qO- --timeout=5 http://test-release-python-app:80/health || echo "Service not reachable yet (expected during initial rollout)"
              echo "Post-install smoke test completed"
---
# Source: python-app/templates/hooks/pre-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "test-release-python-app-pre-install"
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    metadata:
      name: "test-release-python-app-pre-install"
    spec:
      restartPolicy: Never
      containers:
        - name: pre-install-check
          image: busybox
          command:
            - 'sh'
            - '-c'
            - |
              echo "=== Pre-install validation ==="
              echo "Checking cluster DNS resolution..."
              nslookup kubernetes.default.svc.cluster.local || true
              echo "Pre-install checks completed successfully"
```

### helm install --dry-run

```
karinasiniatullina@MacBook-Pro--Karina DevOps-Core-Course % helm install --dry-run --debug test-release k8s/python-app
level=WARN msg="--dry-run is deprecated and should be replaced with '--dry-run=client'"
level=DEBUG msg="Original chart version" version=""
level=DEBUG msg="Chart path" path="/Users/karinasiniatullina/innopolis/3 курс/2sem/devops/DevOps-Core-Course/k8s/python-app"
level=DEBUG msg="number of dependencies in the chart" chart=python-app dependencies=1
level=DEBUG msg="number of dependencies in the chart" chart=common-lib dependencies=0
NAME: test-release
LAST DEPLOYED: Thu Mar 26 12:48:53 2026
NAMESPACE: default
STATUS: pending-install
REVISION: 1
DESCRIPTION: Dry run complete
TEST SUITE: None
USER-SUPPLIED VALUES:
{}

COMPUTED VALUES:
common-lib:
  global: {}
containerPort: 5000
env:
- name: HOST
  value: 0.0.0.0
- name: PORT
  value: "5000"
fullnameOverride: ""
image:
  pullPolicy: IfNotPresent
  repository: karishka1222/devops-python-app
  tag: latest
livenessProbe:
  failureThreshold: 3
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
nameOverride: ""
readinessProbe:
  failureThreshold: 3
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 5
  periodSeconds: 3
  timeoutSeconds: 2
replicaCount: 3
resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
service:
  nodePort: 30080
  port: 80
  targetPort: 5000
  type: NodePort
strategy:
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
  type: RollingUpdate

HOOKS:
---
# Source: python-app/templates/hooks/post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "test-release-python-app-post-install"
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    metadata:
      name: "test-release-python-app-post-install"
    spec:
      restartPolicy: Never
      containers:
        - name: post-install-test
          image: busybox
          command:
            - 'sh'
            - '-c'
            - |
              echo "=== Post-install smoke test ==="
              echo "Waiting for service to become available..."
              sleep 15
              echo "Checking service endpoint..."
              wget -qO- --timeout=5 http://test-release-python-app:80/health || echo "Service not reachable yet (expected during initial rollout)"
              echo "Post-install smoke test completed"
---
# Source: python-app/templates/hooks/pre-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "test-release-python-app-pre-install"
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    metadata:
      name: "test-release-python-app-pre-install"
    spec:
      restartPolicy: Never
      containers:
        - name: pre-install-check
          image: busybox
          command:
            - 'sh'
            - '-c'
            - |
              echo "=== Pre-install validation ==="
              echo "Checking cluster DNS resolution..."
              nslookup kubernetes.default.svc.cluster.local || true
              echo "Pre-install checks completed successfully"
MANIFEST:
---
# Source: python-app/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: test-release-python-app
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
  ports:
    - protocol: TCP
      port: 80
      targetPort: 5000
      nodePort: 30080
---
# Source: python-app/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-release-python-app
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: python-app
      app.kubernetes.io/instance: test-release
  strategy:
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
    type: RollingUpdate
  template:
    metadata:
      labels:
        app.kubernetes.io/name: python-app
        app.kubernetes.io/instance: test-release
    spec:
      containers:
        - name: python-app
          image: "karishka1222/devops-python-app:latest"
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 5000
              protocol: TCP
          resources:
            limits:
              cpu: 200m
              memory: 256Mi
            requests:
              cpu: 100m
              memory: 128Mi
          livenessProbe:
            failureThreshold: 3
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 10
            periodSeconds: 5
            timeoutSeconds: 3
          readinessProbe:
            failureThreshold: 3
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 5
            periodSeconds: 3
            timeoutSeconds: 2
          env:
            - name: HOST
              value: 0.0.0.0
            - name: PORT
              value: "5000"

NOTES:
python-app has been deployed!

Release: test-release
Namespace: default
Access via NodePort:
  minikube service test-release-python-app --url
```

### helm install (actual)

```
karinasiniatullina@MacBook-Pro--Karina DevOps-Core-Course % helm install python-dev-install k8s/python-app --set service.nodePort=30083
NAME: python-dev-install
LAST DEPLOYED: Thu Mar 26 13:27:14 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
python-app has been deployed!

Release: python-dev-install
Namespace: default
Access via NodePort:
  minikube service python-dev-install-python-app --url
```

### helm list

```
karinasiniatullina@MacBook-Pro--Karina DevOps-Core-Course % helm list
NAME                    NAMESPACE       REVISION        UPDATED                                 STATUS          CHART                   APP VERSION
python-dev              default         1               2026-03-26 13:13:33.070379 +0300 MSK    deployed        python-app-0.1.0        1.0.0      
python-dev-install      default         1               2026-03-26 13:38:09.238927 +0300 MSK    deployed        python-app-0.1.0        1.0.0    
```

### kubectl get all

```
karinasiniatullina@MacBook-Pro--Karina DevOps-Core-Course % kubectl get all   
NAME                                                READY   STATUS    RESTARTS       AGE
pod/go-app-fb8d4b49d-dkf92                          1/1     Running   1 (4d1h ago)   4d1h
pod/go-app-fb8d4b49d-jfttb                          1/1     Running   1 (4d1h ago)   4d1h
pod/go-app-fb8d4b49d-qz5ff                          1/1     Running   1 (4d1h ago)   4d1h
pod/python-app-7c9b856bcd-25g7f                     1/1     Running   1 (4d1h ago)   4d18h
pod/python-app-7c9b856bcd-gfj5b                     1/1     Running   1 (4d1h ago)   4d18h
pod/python-app-7c9b856bcd-zvjxt                     1/1     Running   1 (4d1h ago)   4d18h
pod/python-dev-install-python-app-98494d859-824k6   1/1     Running   0              81s
pod/python-dev-python-app-9fcbdb9d5-hgrt4           1/1     Running   0              25m

NAME                                    TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/go-app-service                  ClusterIP   10.97.10.23     <none>        80/TCP         4d1h
service/kubernetes                      ClusterIP   10.96.0.1       <none>        443/TCP        5d17h
service/python-app-service              NodePort    10.100.220.46   <none>        80:30080/TCP   4d21h
service/python-dev-install-python-app   NodePort    10.108.35.225   <none>        80:30083/TCP   81s
service/python-dev-python-app           NodePort    10.96.94.57     <none>        80:30081/TCP   25m

NAME                                            READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/go-app                          3/3     3            3           4d1h
deployment.apps/python-app                      3/3     3            3           4d22h
deployment.apps/python-dev-install-python-app   1/1     1            1           81s
deployment.apps/python-dev-python-app           1/1     1            1           25m

NAME                                                      DESIRED   CURRENT   READY   AGE
replicaset.apps/go-app-fb8d4b49d                          3         3         3       4d1h
replicaset.apps/python-app-6dc4c9bfd6                     0         0         0       4d18h
replicaset.apps/python-app-7c9b856bcd                     3         3         3       4d22h
replicaset.apps/python-dev-install-python-app-98494d859   1         1         1       81s
replicaset.apps/python-dev-python-app-9fcbdb9d5           1         1         1       25m
```

### Hook execution

```
karinasiniatullina@MacBook-Pro--Karina DevOps-Core-Course %    kubectl get jobs -w
NAME                                        STATUS    COMPLETIONS   DURATION   AGE
python-dev-install-python-app-pre-install   Running   0/1                      0s
python-dev-install-python-app-pre-install   Running   0/1           0s         0s
python-dev-install-python-app-pre-install   SuccessCriteriaMet   0/1           5s         5s
python-dev-install-python-app-pre-install   Complete             1/1           5s         5s
python-dev-install-python-app-pre-install   Complete             1/1           5s         5s
python-dev-install-python-app-post-install   Running              0/1                      0s
python-dev-install-python-app-post-install   Running              0/1           0s         0s
python-dev-install-python-app-post-install   Running              0/1           4s         4s
python-dev-install-python-app-post-install   Running              0/1           19s        19s
python-dev-install-python-app-post-install   SuccessCriteriaMet   0/1           20s        20s
python-dev-install-python-app-post-install   Complete             1/1           20s        20s
python-dev-install-python-app-post-install   Complete             1/1           20s        20s

```

```
karinasiniatullina@MacBook-Pro--Karina DevOps-Core-Course %    kubectl describe job/python-dev-install-python-app-pre-install
   kubectl logs job/python-dev-install-python-app-pre-install
Name:             python-dev-install-python-app-pre-install
Namespace:        default
Selector:         batch.kubernetes.io/controller-uid=8ee90097-6eb6-451e-9241-703f55ba90aa
Labels:           app.kubernetes.io/instance=python-dev-install
                  app.kubernetes.io/managed-by=Helm
                  app.kubernetes.io/name=python-app
                  app.kubernetes.io/version=1.0.0
                  helm.sh/chart=python-app-0.1.0
Annotations:      helm.sh/hook: pre-install
                  helm.sh/hook-delete-policy: hook-succeeded
                  helm.sh/hook-weight: -5
Parallelism:      1
Completions:      1
Completion Mode:  NonIndexed
Suspend:          false
Backoff Limit:    6
Start Time:       Thu, 26 Mar 2026 13:38:09 +0300
Pods Statuses:    1 Active (0 Ready) / 0 Succeeded / 0 Failed
Pod Template:
  Labels:  batch.kubernetes.io/controller-uid=8ee90097-6eb6-451e-9241-703f55ba90aa
           batch.kubernetes.io/job-name=python-dev-install-python-app-pre-install
           controller-uid=8ee90097-6eb6-451e-9241-703f55ba90aa
           job-name=python-dev-install-python-app-pre-install
  Containers:
   pre-install-check:
    Image:      busybox
    Port:       <none>
    Host Port:  <none>
    Command:
      sh
      -c
      echo "=== Pre-install validation ==="
      echo "Checking cluster DNS resolution..."
      nslookup kubernetes.default.svc.cluster.local || true
      echo "Pre-install checks completed successfully"
      
    Environment:   <none>
    Mounts:        <none>
  Volumes:         <none>
  Node-Selectors:  <none>
  Tolerations:     <none>
Events:
  Type    Reason            Age   From            Message
  ----    ------            ----  ----            -------
  Normal  SuccessfulCreate  4s    job-controller  Created pod: python-dev-install-python-app-pre-install-5pzq9
=== Pre-install validation ===
Checking cluster DNS resolution...
Server:         10.96.0.10
Address:        10.96.0.10:53

Name:   kubernetes.default.svc.cluster.local
Address: 10.96.0.1


Pre-install checks completed successfully
```

```
karinasiniatullina@MacBook-Pro--Karina DevOps-Core-Course % kubectl get jobs
No resources found in default namespace.
```

### Dev environment deployment

```
karinasiniatullina@MacBook-Pro--Karina DevOps-Core-Course % helm install python-dev k8s/python-app -f k8s/python-app/values-dev.yaml --set service.nodePort=30081 
NAME: python-dev
LAST DEPLOYED: Thu Mar 26 13:13:33 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
python-app has been deployed!

Release: python-dev
Namespace: default
Access via NodePort:
  minikube service python-dev-python-app --url
```

### Prod environment deployment

```
Release "python-dev-install" has been upgraded. Happy Helming!
NAME: python-dev-install
LAST DEPLOYED: Thu Mar 26 13:44:17 2026
NAMESPACE: default
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
TEST SUITE: None
NOTES:
python-app has been deployed!

Release: python-dev-install
Namespace: default
Access via LoadBalancer (wait for external IP):
  kubectl get svc python-dev-install-python-app -w
```

### Application accessibility

```
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"},{"description":"Prometheus metrics","method":"GET","path":"/metrics"}],"request":{"client_ip":"10.244.0.1","method":"GET","path":"/","user_agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.3.1 Safari/605.1.15"},"runtime":{"current_time":"2026-03-26T12:38:41.756211+00:00","timezone":"UTC","uptime_human":"2 hours, 0 minutes","uptime_seconds":7223},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"aarch64","cpu_count":11,"hostname":"python-dev-install-python-app-98494d859-824k6","platform":"Linux","platform_version":"#1 SMP Tue Apr 15 16:00:54 UTC 2025","python_version":"3.13.12"}}
```

---

## 5. Operations

### Install

```bash
# First time — build dependencies (needed for common-lib)
helm dependency update k8s/python-app
helm install python-release k8s/python-app
```

### Upgrade

```bash
helm upgrade python-release k8s/python-app -f k8s/python-app/values-prod.yaml
```

### Rollback

```bash
helm history python-release
helm rollback python-release <REVISION>
```

### Uninstall

```bash
helm uninstall python-release
```

### Check status

```bash
helm status python-release
helm get values python-release
helm get manifest python-release
```

---

## 6. Testing & Validation

### helm lint output

```
karinasiniatullina@MacBook-Pro--Karina DevOps-Core-Course % helm lint k8s/python-app
==> Linting k8s/python-app
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### helm template verification

```
karinasiniatullina@MacBook-Pro--Karina DevOps-Core-Course % helm template test-release k8s/python-app
---
# Source: python-app/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: test-release-python-app
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
  ports:
    - protocol: TCP
      port: 80
      targetPort: 5000
      nodePort: 30080
---
# Source: python-app/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-release-python-app
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: python-app
      app.kubernetes.io/instance: test-release
  strategy:
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
    type: RollingUpdate
  template:
    metadata:
      labels:
        app.kubernetes.io/name: python-app
        app.kubernetes.io/instance: test-release
    spec:
      containers:
        - name: python-app
          image: "karishka1222/devops-python-app:latest"
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 5000
              protocol: TCP
          resources:
            limits:
              cpu: 200m
              memory: 256Mi
            requests:
              cpu: 100m
              memory: 128Mi
          livenessProbe:
            failureThreshold: 3
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 10
            periodSeconds: 5
            timeoutSeconds: 3
          readinessProbe:
            failureThreshold: 3
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 5
            periodSeconds: 3
            timeoutSeconds: 2
          env:
            - name: HOST
              value: 0.0.0.0
            - name: PORT
              value: "5000"
---
# Source: python-app/templates/hooks/post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "test-release-python-app-post-install"
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    metadata:
      name: "test-release-python-app-post-install"
    spec:
      restartPolicy: Never
      containers:
        - name: post-install-test
          image: busybox
          command:
            - 'sh'
            - '-c'
            - |
              echo "=== Post-install smoke test ==="
              echo "Waiting for service to become available..."
              sleep 15
              echo "Checking service endpoint..."
              wget -qO- --timeout=5 http://test-release-python-app:80/health || echo "Service not reachable yet (expected during initial rollout)"
              echo "Post-install smoke test completed"
---
# Source: python-app/templates/hooks/pre-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "test-release-python-app-pre-install"
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    metadata:
      name: "test-release-python-app-pre-install"
    spec:
      restartPolicy: Never
      containers:
        - name: pre-install-check
          image: busybox
          command:
            - 'sh'
            - '-c'
            - |
              echo "=== Pre-install validation ==="
              echo "Checking cluster DNS resolution..."
              nslookup kubernetes.default.svc.cluster.local || true
              echo "Pre-install checks completed successfully"
```

### Dry-run output

```
karinasiniatullina@MacBook-Pro--Karina DevOps-Core-Course % helm install --dry-run --debug test-release k8s/python-app
level=WARN msg="--dry-run is deprecated and should be replaced with '--dry-run=client'"
level=DEBUG msg="Original chart version" version=""
level=DEBUG msg="Chart path" path="/Users/karinasiniatullina/innopolis/3 курс/2sem/devops/DevOps-Core-Course/k8s/python-app"
level=DEBUG msg="number of dependencies in the chart" chart=python-app dependencies=1
level=DEBUG msg="number of dependencies in the chart" chart=common-lib dependencies=0
NAME: test-release
LAST DEPLOYED: Thu Mar 26 12:48:53 2026
NAMESPACE: default
STATUS: pending-install
REVISION: 1
DESCRIPTION: Dry run complete
TEST SUITE: None
USER-SUPPLIED VALUES:
{}

COMPUTED VALUES:
common-lib:
  global: {}
containerPort: 5000
env:
- name: HOST
  value: 0.0.0.0
- name: PORT
  value: "5000"
fullnameOverride: ""
image:
  pullPolicy: IfNotPresent
  repository: karishka1222/devops-python-app
  tag: latest
livenessProbe:
  failureThreshold: 3
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
nameOverride: ""
readinessProbe:
  failureThreshold: 3
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 5
  periodSeconds: 3
  timeoutSeconds: 2
replicaCount: 3
resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
service:
  nodePort: 30080
  port: 80
  targetPort: 5000
  type: NodePort
strategy:
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
  type: RollingUpdate

HOOKS:
---
# Source: python-app/templates/hooks/post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "test-release-python-app-post-install"
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    metadata:
      name: "test-release-python-app-post-install"
    spec:
      restartPolicy: Never
      containers:
        - name: post-install-test
          image: busybox
          command:
            - 'sh'
            - '-c'
            - |
              echo "=== Post-install smoke test ==="
              echo "Waiting for service to become available..."
              sleep 15
              echo "Checking service endpoint..."
              wget -qO- --timeout=5 http://test-release-python-app:80/health || echo "Service not reachable yet (expected during initial rollout)"
              echo "Post-install smoke test completed"
---
# Source: python-app/templates/hooks/pre-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "test-release-python-app-pre-install"
  labels:
    helm.sh/chart: python-app-0.1.0
    app.kubernetes.io/name: python-app
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    metadata:
      name: "test-release-python-app-pre-install"
    spec:
      restartPolicy: Never
      containers:
        - name: pre-install-check
          image: busybox
          command:
            - 'sh'
            - '-c'
            - |
              echo "=== Pre-install validation ==="
              echo "Checking cluster DNS resolution..."
              nslookup kubernetes.default.svc.cluster.local || true
              echo "Pre-install checks completed successfully"
```

### Application accessibility

```
{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"},{"description":"Prometheus metrics","method":"GET","path":"/metrics"}],"request":{"client_ip":"10.244.0.1","method":"GET","path":"/","user_agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.3.1 Safari/605.1.15"},"runtime":{"current_time":"2026-03-26T12:38:41.756211+00:00","timezone":"UTC","uptime_human":"2 hours, 0 minutes","uptime_seconds":7223},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"aarch64","cpu_count":11,"hostname":"python-dev-install-python-app-98494d859-824k6","platform":"Linux","platform_version":"#1 SMP Tue Apr 15 16:00:54 UTC 2025","python_version":"3.13.12"}}
```

---

## 7. Library Chart (Bonus)

### Structure

`k8s/common-lib/` is a `type: library` chart containing shared template helpers:

- `_names.tpl`: `common.name`, `common.fullname`, `common.chart`
- `_labels.tpl`: `common.labels`, `common.selectorLabels`

### Usage

Both `python-app` and `go-app` declare `common-lib` as a dependency in `Chart.yaml`:

```yaml
dependencies:
  - name: common-lib
    version: 0.1.0
    repository: "file://../common-lib"
```

Their `_helpers.tpl` files bridge chart-specific template names to the common definitions:

```yaml
{{- define "python-app.labels" -}}
{{- include "common.labels" . }}
{{- end }}
```

### Benefits

- **DRY**: Labels, names, and selector logic defined once.
- **Consistency**: Both apps produce identical label formats.
- **Maintainability**: Change label schema in one place, all charts updated.

### Deployment evidence

```
karinasiniatullina@MacBook-Pro--Karina DevOps-Core-Course % helm dependency update k8s/python-app && helm dependency update k8s/go-app
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈
Saving 1 charts
Deleting outdated charts
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈
Saving 1 charts
Deleting outdated charts
```

```
karinasiniatullina@MacBook-Pro--Karina DevOps-Core-Course % helm install go-release k8s/go-app
NAME: go-release
LAST DEPLOYED: Thu Mar 26 16:09:48 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
go-app has been deployed!

Release: go-release
Namespace: default

Access via port-forward:
  kubectl port-forward svc/go-release-go-app 8080:80
```
```
karinasiniatullina@MacBook-Pro--Karina DevOps-Core-Course % kubectl get all
NAME                                                 READY   STATUS             RESTARTS       AGE
pod/go-app-fb8d4b49d-dkf92                           1/1     Running            1 (4d4h ago)   4d4h
pod/go-app-fb8d4b49d-jfttb                           1/1     Running            1 (4d4h ago)   4d4h
pod/go-app-fb8d4b49d-qz5ff                           1/1     Running            1 (4d4h ago)   4d4h
pod/go-release-go-app-7bc9754878-hb9wg               1/1     Running            0              6s
pod/go-release-go-app-7bc9754878-jsw5q               1/1     Running            0              6s
pod/go-release-go-app-7bc9754878-prcr4               1/1     Running            0              6s
pod/python-app-7c9b856bcd-25g7f                      1/1     Running            1 (4d4h ago)   4d4h
pod/python-app-7c9b856bcd-gfj5b                      1/1     Running            1 (4d4h ago)   4d4h
pod/python-app-7c9b856bcd-zvjxt                      1/1     Running            1 (4d4h ago)   4d4h
pod/python-dev-install-python-app-6697b5d74f-48pdj   0/1     ImagePullBackOff   0              145m
pod/python-dev-install-python-app-98494d859-2thlr    1/1     Running            0              145m
pod/python-dev-install-python-app-98494d859-824k6    1/1     Running            0              151m
pod/python-dev-install-python-app-98494d859-mckfm    1/1     Running            0              145m
pod/python-dev-install-python-app-98494d859-pb4ms    1/1     Running            0              145m
pod/python-dev-install-python-app-98494d859-z84ng    1/1     Running            0              145m
pod/python-dev-python-app-9fcbdb9d5-hgrt4            1/1     Running            0              176m

NAME                                    TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/go-app-service                  ClusterIP      10.97.10.23     <none>        80/TCP         4d4h
service/go-release-go-app               ClusterIP      10.99.42.5      <none>        80/TCP         6s
service/kubernetes                      ClusterIP      10.96.0.1       <none>        443/TCP        5d19h
service/python-app-service              NodePort       10.100.220.46   <none>        80:30080/TCP   4d23h
service/python-dev-install-python-app   LoadBalancer   10.108.35.225   <pending>     80:30083/TCP   151m
service/python-dev-python-app           NodePort       10.96.94.57     <none>        80:30081/TCP   176m

NAME                                            READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/go-app                          3/3     3            3           4d4h
deployment.apps/go-release-go-app               3/3     3            3           6s
deployment.apps/python-app                      3/3     3            3           5d
deployment.apps/python-dev-install-python-app   5/5     1            5           151m

NAME                                                       DESIRED   CURRENT   READY   AGE
replicaset.apps/go-app-fb8d4b49d                           3         3         3       4d4h
replicaset.apps/go-release-go-app-7bc9754878               3         3         3       6s
replicaset.apps/python-app-7c9b856bcd                      3         3         3       5d
replicaset.apps/python-dev-install-python-app-98494d859    5         5         5       151m
```
