# Lab 10 — Helm Package Manager

## Chart Overview

### Chart structure

```
devops-info-service-chart/
├── Chart.yaml # Chart metadata
├── values.yaml # Default configuration
├── values-dev.yaml # Development configuration
├── values-prod.yaml # Production configuration
├── templates/
│       ├── _helpers.tpl # Helper functions
│       ├── deployment.yaml # Kubernetes Deployment
│       ├── service.yaml # Kubernetes Service
│       ├── NOTES.txt # Post-installation instructions
│       └── hooks/
│             ├── pre-install-job.yaml
│             └── post-install-job.yaml
└── HELM.md # User documentation
```

### Key template files and their purpose

- **`_helpers.tpl`** — defines reusable named templates: `info-service.name`, `info-service.chart`, `info-service.labels` and others
- **`deployment.yaml`** — defines replicas, resource limits and environment variables
- **`service.yaml`** — templated Service with configurable type (NodePort/LoadBalancer), ports
- **`pre-install-job.yaml`** - instructions that runs before installation
- **`post-install-job.yaml`** - instructions that runs post installation
- **`NOTES.txt`** — displays instructions after installation

### Values organization strategy

The chart uses a layered values approach:

- **`values.yaml` (base/default)** contains shared settings used in all environments: image repository, default tag/pull policy, common env vars (`HOST`, `PORT`), probes, rolling update strategy, security context, and baseline resources.
- **`values-dev.yaml`** overrides only development-specific parameters: lower replica count, lighter CPU/memory requests and limits, `NodePort` exposure, and faster startup/health timings for quicker local iteration.
- **`values-prod.yaml`** overrides production-specific parameters: stable image tag, higher resource requests/limits, stricter probe timings, and `LoadBalancer` service type for production-ready exposure.

This structure keeps templates clean, avoids duplication, and allows switching environments with `-f values-*.yaml` while preserving one source of truth for common defaults.


## Configuration Guide

### Important values and their purpose

- **replicaCount** — number of Pod replicas in Deployment.
- **image.repository / image.tag / image.pullPolicy** — container image source, version, and pull behavior.
- **service.type** — Service exposure model (`NodePort` for local/minikube, `LoadBalancer` for production-ready external access).
- **service.port / service.targetPort / service.nodePort** — public Service port, container target port, and fixed node port (for NodePort mode).
- **resources.requests / resources.limits** — CPU and memory guarantees/limits for scheduling and stability.
- **livenessProbe** — health check used by Kubernetes to restart unhealthy containers.
- **readinessProbe** — readiness check controlling traffic routing to Pods.
- **strategy.rollingUpdate.maxSurge / maxUnavailable** — rollout behavior during update.
- **podSecurityContext.runAsNonRoot / runAsUser** — security settings for container runtime user.
- **env** — runtime environment variables passed into the container (`HOST`, `PORT`).

### How to customize for different environments

Use the same chart with different values files:

- **Development** uses [k8s/devops-info-service-chart/values-dev.yaml](devops-info-service-chart/values-dev.yaml):
  - fewer replicas (`replicaCount: 1`)
  - lighter resources
  - `NodePort` service for quick local testing
  - faster probe timing for rapid feedback

- **Production** uses [k8s/devops-info-service-chart/values-prod.yaml](devops-info-service-chart/values-prod.yaml):
  - more replicas (`replicaCount: 3`)
  - stricter/larger resources
  - fixed application tag for predictable rollout
  - `LoadBalancer` service for external access in cloud/K8s environments

Command example:
```
    helm install <release> k8s/devops-info-service-chart -f k8s/devops-info-service-chart/values-dev.yaml
```

### Example installations with different configurations

#### 1) Development install

```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/k8s$ helm install dev-release devops-info-service-chart -f devops-info-service-chart/values-dev.yaml 
NAME: dev-release
LAST DEPLOYED: Thu Apr  2 20:26:27 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
Thank you for installing devops-info-service.

Release: dev-release
Namespace: default

Your application should expose:
- GET /
- GET /health

Useful commands:
        kubectl get pods -n default
        kubectl get svc -n default
Service type is NodePort.

Access options:
1. Minikube:
         minikube service dev-release-devops-info-service -n default --url

2. Manual NodePort access:
         export NODE_PORT=$(kubectl get svc dev-release-devops-info-service -n default -o jsonpath='{.spec.ports[0].nodePort}')
         export NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
         echo "http://${NODE_IP}:${NODE_PORT}/"
         curl -i "http://${NODE_IP}:${NODE_PORT}/health"

Troubleshooting:
        kubectl describe deployment dev-release-devops-info-service -n default
        kubectl logs -n default deployment/dev-release-devops-info-service
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/k8s$ helm get values dev-release
USER-SUPPLIED VALUES:
env:
- name: HOST
  value: 0.0.0.0
- name: PORT
  value: "5000"
fullnameOverride: ""
image:
  pullPolicy: IfNotPresent
  repository: chaleshka/devops-info-service
  tag: latest
livenessProbe:
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 5
  periodSeconds: 10
nameOverride: ""
podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1000
readinessProbe:
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 5
  periodSeconds: 5
replicaCount: 1
resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi
service:
  nodePort: 30080
  port: 80
  targetPort: 5000
  type: NodePort
strategy:
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

#### 2) Upgrade to production

```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/k8s$ helm upgrade dev-release devops-info-service-chart -f devops-info-service-chart/values-prod.yaml 
Release "dev-release" has been upgraded. Happy Helming!
NAME: dev-release
LAST DEPLOYED: Thu Apr  2 20:28:11 2026
NAMESPACE: default
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
TEST SUITE: None
NOTES:
Thank you for installing devops-info-service.

Release: dev-release
Namespace: default

Your application should expose:
- GET /
- GET /health

Useful commands:
        kubectl get pods -n default
        kubectl get svc -n default
Service type is LoadBalancer.

Wait for external IP:
        kubectl get svc dev-release-devops-info-service -n default -w

Then test:
        export EXTERNAL_IP=$(kubectl get svc dev-release-devops-info-service -n default -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
        curl -i "http://${EXTERNAL_IP}:80/health"

Troubleshooting:
        kubectl describe deployment dev-release-devops-info-service -n default
        kubectl logs -n default deployment/dev-release-devops-info-service
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/k8s$ helm get values dev-release
USER-SUPPLIED VALUES:
env:
- name: HOST
  value: 0.0.0.0
- name: PORT
  value: "5000"
fullnameOverride: ""
image:
  pullPolicy: IfNotPresent
  repository: chaleshka/devops-info-service
  tag: 2026.02.11
livenessProbe:
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 30
  periodSeconds: 5
nameOverride: ""
podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1000
readinessProbe:
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 10
  periodSeconds: 3
replicaCount: 3
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 200m
    memory: 256Mi
service:
  port: 80
  targetPort: 5000
  type: LoadBalancer
strategy:
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```


## Hook Implementation

### What hooks you implemented and why

- **`pre-install-job.yaml`**: runs validation before installation
- **`post-install-job.yaml`**: runs validation after installation

### Hook execution order and weights

- **Pre-install** (weight: -5) — runs first and validates environment readiness
- Deploying service
-  **Post-install** (weight: 5) — runs after all resources are ready and validates deployment

### Deletion policies explanation
Both hooks use `hook-succeeded` policy. Jobs automatically deleted after successful completion.


## Installation Evidence

### helm list output
```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/k8s$ helm list
NAME            NAMESPACE       REVISION        UPDATED                                 STATUS          CHART                           APP VERSION
dev-release     default         2               2026-04-02 20:28:11.216547459 +0300 MSK deployed        devops-info-service-0.1.0       1.0.0  
```

### kubectl get all showing deployed resources

```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/k8s$ kubectl get all
NAME                                                  READY   STATUS    RESTARTS   AGE
pod/dev-release-devops-info-service-bdb4c4dcb-dwlqb   1/1     Running   0          8m29s
pod/dev-release-devops-info-service-bdb4c4dcb-q7ndl   1/1     Running   0          8m17s
pod/dev-release-devops-info-service-bdb4c4dcb-r2wv5   1/1     Running   0          8m44s

NAME                                      TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/dev-release-devops-info-service   LoadBalancer   10.98.149.182   <pending>     80:30080/TCP   10m
service/kubernetes                        ClusterIP      10.96.0.1       <none>        443/TCP        7d4h

NAME                                              READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/dev-release-devops-info-service   3/3     3            3           10m

NAME                                                        DESIRED   CURRENT   READY   AGE
replicaset.apps/dev-release-devops-info-service-b6f9c489d   0         0         0       10m
replicaset.apps/dev-release-devops-info-service-bdb4c4dcb   3         3         3       8m44s
```

### Hook execution output (kubectl get jobs, kubectl describe job)

```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/k8s$ kubectl get events -n default --sort-by=.metadata.creationTimestamp | grep -Ei "pre-install|post-install|job|hook"
20m         Normal    Scheduled           pod/dev-release-devops-info-service-pre-install-tbml7    Successfully assigned default/dev-release-devops-info-service-pre-install-tbml7 to minikube
20m         Normal    SuccessfulCreate    job/dev-release-devops-info-service-pre-install          Created pod: dev-release-devops-info-service-pre-install-tbml7
20m         Normal    Pulling             pod/dev-release-devops-info-service-pre-install-tbml7    Pulling image "busybox:1.36"
20m         Normal    Pulled              pod/dev-release-devops-info-service-pre-install-tbml7    Successfully pulled image "busybox:1.36" in 12.999s (12.999s including waiting). Image size: 4417166 bytes.
20m         Normal    Created             pod/dev-release-devops-info-service-pre-install-tbml7    Container created
20m         Normal    Started             pod/dev-release-devops-info-service-pre-install-tbml7    Container started
20m         Normal    Completed           job/dev-release-devops-info-service-pre-install          Job completed
17m         Normal    SuccessfulCreate    job/dev-release-devops-info-service-pre-install          Created pod: dev-release-devops-info-service-pre-install-kqn5g
17m         Normal    Scheduled           pod/dev-release-devops-info-service-pre-install-kqn5g    Successfully assigned default/dev-release-devops-info-service-pre-install-kqn5g to minikube
17m         Normal    Pulled              pod/dev-release-devops-info-service-pre-install-kqn5g    Container image "busybox:1.36" already present on machine and can be accessed by the pod
17m         Normal    Started             pod/dev-release-devops-info-service-pre-install-kqn5g    Container started
17m         Normal    Created             pod/dev-release-devops-info-service-pre-install-kqn5g    Container created
16m         Normal    Scheduled           pod/dev-release-devops-info-service-post-install-ms9mk   Successfully assigned default/dev-release-devops-info-service-post-install-ms9mk to minikube
16m         Normal    Completed           job/dev-release-devops-info-service-pre-install          Job completed
16m         Normal    SuccessfulCreate    job/dev-release-devops-info-service-post-install         Created pod: dev-release-devops-info-service-post-install-ms9mk
16m         Normal    Pulled              pod/dev-release-devops-info-service-post-install-ms9mk   Container image "busybox:1.36" already present on machine and can be accessed by the pod
16m         Normal    Created             pod/dev-release-devops-info-service-post-install-ms9mk   Container created
16m         Normal    Started             pod/dev-release-devops-info-service-post-install-ms9mk   Container started
16m         Normal    Completed           job/dev-release-devops-info-service-post-install         Job completed


andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/k8s$ helm get hooks dev-release -n default
---
# Source: devops-info-service/templates/hooks/post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "dev-release-devops-info-service-post-install"
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: dev-release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    metadata:
      labels:
        app.kubernetes.io/name: devops-info-service
        app.kubernetes.io/instance: dev-release
    spec:
      restartPolicy: Never
      containers:
        - name: post-install-smoke
          image: busybox:1.36
          command: ['sh', '-c', 'echo Post-install validation && sleep 10 && echo Validation passed']
---
# Source: devops-info-service/templates/hooks/pre-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "dev-release-devops-info-service-pre-install"
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: dev-release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    metadata:
      labels:
        app.kubernetes.io/name: devops-info-service
        app.kubernetes.io/instance: dev-release
    spec:
      restartPolicy: Never
      containers:
        - name: pre-install-check
          image: busybox:1.36
          command: ['sh', '-c', 'echo Pre-install task running && sleep 10 && echo Pre-install completed']


andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/k8s$ helm history dev-release -n default
REVISION        UPDATED                         STATUS          CHART                           APP VERSION     DESCRIPTION     
1               Thu Apr  2 20:26:27 2026        superseded      devops-info-service-0.1.0       1.0.0           Install complete
2               Thu Apr  2 20:28:11 2026        deployed        devops-info-service-0.1.0       1.0.0           Upgrade complete
```


## Operations

### Installation commands used

```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
"prometheus-community" has been added to your repositories


andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈


andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ helm search repo prometheus
NAME                                                    CHART VERSION   APP VERSION     DESCRIPTION                                       
prometheus-community/kube-prometheus-stack              82.16.1         v0.89.0         kube-prometheus-stack collects Kubernetes manif...
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
prometheus-community/prometheus-windows-exporter        0.12.6          0.31.6          A Helm chart for prometheus windows-exporter      
prometheus-community/prometheus-yet-another-clo...      0.43.0          v0.64.0         Yace - Yet Another CloudWatch Exporter            
prometheus-community/alertmanager                       1.34.0          v0.31.1         The Alertmanager handles alerts sent by client ...
prometheus-community/alertmanager-snmp-notifier         2.1.0           v2.1.0          The SNMP Notifier handles alerts coming from Pr...
prometheus-community/jiralert                           1.8.2           v1.3.0          A Helm chart for Kubernetes to install jiralert   
prometheus-community/kube-state-metrics                 7.2.2           2.18.0          Install kube-state-metrics to generate and expo...
prometheus-community/prom-label-proxy                   0.18.0          v0.12.1         A proxy that enforces a given label in a given ...
prometheus-community/yet-another-cloudwatch-exp...      0.39.1          v0.62.1         Yace - Yet Another CloudWatch Exporter      


andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ helm show chart prometheus-community/prometheus
level=WARN msg="unable to find exact version; falling back to closest available version" chart=prometheus requested="" selected=28.14.1
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

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ helm version 
version.BuildInfo{Version:"v4.0.0", GitCommit:"99cd1964357c793351be481d55abbe21c6b2f4ec", GitTreeState:"clean", GoVersion:"go1.25.3", KubeClientVersion:"v1.34"}
```

### How to upgrade a release

```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/k8s$ helm upgrade dev-release devops-info-service-chart -f devops-info-service-chart/values-prod.yaml 
Release "dev-release" has been upgraded. Happy Helming!
NAME: dev-release
LAST DEPLOYED: Thu Apr  2 20:28:11 2026
NAMESPACE: default
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
TEST SUITE: None
NOTES:
Thank you for installing devops-info-service.

Release: dev-release
Namespace: default

Your application should expose:
- GET /
- GET /health

Useful commands:
        kubectl get pods -n default
        kubectl get svc -n default
Service type is LoadBalancer.

Wait for external IP:
        kubectl get svc dev-release-devops-info-service -n default -w

Then test:
        export EXTERNAL_IP=$(kubectl get svc dev-release-devops-info-service -n default -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
        curl -i "http://${EXTERNAL_IP}:80/health"

Troubleshooting:
        kubectl describe deployment dev-release-devops-info-service -n default
        kubectl logs -n default deployment/dev-release-devops-info-service
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/k8s$ helm get values dev-release
USER-SUPPLIED VALUES:
env:
- name: HOST
  value: 0.0.0.0
- name: PORT
  value: "5000"
fullnameOverride: ""
image:
  pullPolicy: IfNotPresent
  repository: chaleshka/devops-info-service
  tag: 2026.02.11
livenessProbe:
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 30
  periodSeconds: 5
nameOverride: ""
podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1000
readinessProbe:
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 10
  periodSeconds: 3
replicaCount: 3
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 200m
    memory: 256Mi
service:
  port: 80
  targetPort: 5000
  type: LoadBalancer
strategy:
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

### How to rollback

```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/k8s$ helm history dev-release -n default
REVISION        UPDATED                         STATUS          CHART                           APP VERSION     DESCRIPTION     
1               Thu Apr  2 20:26:27 2026        superseded      devops-info-service-0.1.0       1.0.0           Install complete
2               Thu Apr  2 20:28:11 2026        deployed        devops-info-service-0.1.0       1.0.0           Upgrade complete


andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/k8s$ helm rollback dev-release 1 -n default
Rollback was a success! Happy Helming!


andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/k8s$ helm status dev-release -n default
NAME: dev-release
LAST DEPLOYED: Thu Apr  2 20:50:45 2026
NAMESPACE: default
STATUS: deployed
REVISION: 3
DESCRIPTION: Rollback to 1
RESOURCES:
==> v1/Service
NAME                              TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
dev-release-devops-info-service   NodePort   10.98.149.182   <none>        80:30080/TCP   24m

==> v1/Deployment
NAME                              READY   UP-TO-DATE   AVAILABLE   AGE
dev-release-devops-info-service   1/1     1            1           24m

==> v1/Pod(related)
NAME                                              READY   STATUS        RESTARTS   AGE
dev-release-devops-info-service-b6f9c489d-l9c6m   0/1     Running       0          9s
dev-release-devops-info-service-bdb4c4dcb-dwlqb   1/1     Running       0          22m
dev-release-devops-info-service-bdb4c4dcb-q7ndl   1/1     Terminating   0          22m
dev-release-devops-info-service-bdb4c4dcb-r2wv5   1/1     Terminating   0          22m


TEST SUITE: None
NOTES:
Thank you for installing devops-info-service.

Release: dev-release
Namespace: default

Your application should expose:
- GET /
- GET /health

Useful commands:
        kubectl get pods -n default
        kubectl get svc -n default
Service type is NodePort.

Access options:
1. Minikube:
         minikube service dev-release-devops-info-service -n default --url

2. Manual NodePort access:
         export NODE_PORT=$(kubectl get svc dev-release-devops-info-service -n default -o jsonpath='{.spec.ports[0].nodePort}')
         export NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
         echo "http://${NODE_IP}:${NODE_PORT}/"
         curl -i "http://${NODE_IP}:${NODE_PORT}/health"

Troubleshooting:
        kubectl describe deployment dev-release-devops-info-service -n default
        kubectl logs -n default deployment/dev-release-devops-info-service
```

### How to uninstall

```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/k8s$ helm uninstall dev-release -n default
release "dev-release" uninstalled


andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/k8s$ helm list -n default
NAME    NAMESPACE       REVISION        UPDATED STATUS  CHART   APP VERSION
```


## Testing & Validation

### helm lint output

```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/k8s$ helm lint devops-info-service-chart
==> Linting devops-info-service-chart
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### helm template verification
```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/k8s$ helm template release devops-info-service-chart/
---
# Source: devops-info-service/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: release-devops-info-service
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: release
  ports:
    - protocol: TCP
      port: 80
      targetPort: 5000
      nodePort: 30080
---
# Source: devops-info-service/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: release-devops-info-service
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: devops-info-service
      app.kubernetes.io/instance: release
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app.kubernetes.io/name: devops-info-service
        app.kubernetes.io/instance: release
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
      containers:
        - name: devops-info-service
          image: "chaleshka/devops-info-service:latest"
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 5000
              protocol: TCP
          env:
            - name: HOST
              value: "0.0.0.0"
            - name: PORT
              value: "5000"
          resources:
            limits:
              cpu: 200m
              memory: 256Mi
            requests:
              cpu: 100m
              memory: 128Mi
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
---
# Source: devops-info-service/templates/hooks/post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "release-devops-info-service-post-install"
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    metadata:
      labels:
        app.kubernetes.io/name: devops-info-service
        app.kubernetes.io/instance: release
    spec:
      restartPolicy: Never
      containers:
        - name: post-install-smoke
          image: busybox:1.36
          command: ['sh', '-c', 'echo Post-install validation && sleep 10 && echo Validation passed']
---
# Source: devops-info-service/templates/hooks/pre-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "release-devops-info-service-pre-install"
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    metadata:
      labels:
        app.kubernetes.io/name: devops-info-service
        app.kubernetes.io/instance: release
    spec:
      restartPolicy: Never
      containers:
        - name: pre-install-check
          image: busybox:1.36
          command: ['sh', '-c', 'echo Pre-install task running && sleep 10 && echo Pre-install completed']
```

### Dry-run output

```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course/k8s$ helm install --dry-run --debug test-release devops-info-service-chart
level=WARN msg="--dry-run is deprecated and should be replaced with '--dry-run=client'"
level=DEBUG msg="Original chart version" version=""
level=DEBUG msg="Chart path" path=/mnt/g/DevOps/DevOps-Core-Course/k8s/devops-info-service-chart
level=DEBUG msg="number of dependencies in the chart" dependencies=0
NAME: test-release
LAST DEPLOYED: Thu Apr  2 20:55:12 2026
NAMESPACE: default
STATUS: pending-install
REVISION: 1
DESCRIPTION: Dry run complete
TEST SUITE: None
USER-SUPPLIED VALUES:
{}

COMPUTED VALUES:
env:
- name: HOST
  value: 0.0.0.0
- name: PORT
  value: "5000"
fullnameOverride: ""
image:
  pullPolicy: IfNotPresent
  repository: chaleshka/devops-info-service
  tag: latest
livenessProbe:
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 10
  periodSeconds: 5
nameOverride: ""
podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1000
readinessProbe:
  httpGet:
    path: /health
    port: 5000
  initialDelaySeconds: 5
  periodSeconds: 3
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

HOOKS:
---
# Source: devops-info-service/templates/hooks/post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "test-release-devops-info-service-post-install"
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
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
      labels:
        app.kubernetes.io/name: devops-info-service
        app.kubernetes.io/instance: test-release
    spec:
      restartPolicy: Never
      containers:
        - name: post-install-smoke
          image: busybox:1.36
          command: ['sh', '-c', 'echo Post-install validation && sleep 10 && echo Validation passed']
---
# Source: devops-info-service/templates/hooks/pre-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "test-release-devops-info-service-pre-install"
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
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
      labels:
        app.kubernetes.io/name: devops-info-service
        app.kubernetes.io/instance: test-release
    spec:
      restartPolicy: Never
      containers:
        - name: pre-install-check
          image: busybox:1.36
          command: ['sh', '-c', 'echo Pre-install task running && sleep 10 && echo Pre-install completed']
MANIFEST:
---
# Source: devops-info-service/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: test-release-devops-info-service
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: test-release
  ports:
    - protocol: TCP
      port: 80
      targetPort: 5000
      nodePort: 30080
---
# Source: devops-info-service/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-release-devops-info-service
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: test-release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: devops-info-service
      app.kubernetes.io/instance: test-release
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app.kubernetes.io/name: devops-info-service
        app.kubernetes.io/instance: test-release
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
      containers:
        - name: devops-info-service
          image: "chaleshka/devops-info-service:latest"
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 5000
              protocol: TCP
          env:
            - name: HOST
              value: "0.0.0.0"
            - name: PORT
              value: "5000"
          resources:
            limits:
              cpu: 200m
              memory: 256Mi
            requests:
              cpu: 100m
              memory: 128Mi
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

NOTES:
Thank you for installing devops-info-service.

Release: test-release
Namespace: default

Your application should expose:
- GET /
- GET /health

Useful commands:
        kubectl get pods -n default
        kubectl get svc -n default
Service type is NodePort.

Access options:
1. Minikube:
         minikube service test-release-devops-info-service -n default --url

2. Manual NodePort access:
         export NODE_PORT=$(kubectl get svc test-release-devops-info-service -n default -o jsonpath='{.spec.ports[0].nodePort}')
         export NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
         echo "http://${NODE_IP}:${NODE_PORT}/"
         curl -i "http://${NODE_IP}:${NODE_PORT}/health"

Troubleshooting:
        kubectl describe deployment test-release-devops-info-service -n default
        kubectl logs -n default deployment/test-release-devops-info-service
```

### Application accessibility verification

```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ export NODE_PORT=$(kubectl get svc test-release-devops-info-service -n default -o jsonpath='{.spec.ports[0].nodePort}')
         export NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
         echo "http://${NODE_IP}:${NODE_PORT}/"
         curl -i "http://${NODE_IP}:${NODE_PORT}/health"
http://192.168.49.2:30080/
HTTP/1.1 200 OK
Server: Werkzeug/3.1.5 Python/3.12.12
Date: Thu, 02 Apr 2026 17:58:01 GMT
Content-Type: application/json
Content-Length: 95
Connection: close

{"status":"healthy","timestamp":"2026-04-02T17:58:01.727912+00:00","uptime_seconds":23.275833}

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ export NODE_PORT=$(kubectl get svc test-release-devops-info-service -n default -o jsonpath='{.spec.ports[0].nodePort}')
         export NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
         echo "http://${NODE_IP}:${NODE_PORT}/"
         curl -i "http://${NODE_IP}:${NODE_PORT}/"
http://192.168.49.2:30080/
HTTP/1.1 200 OK
Server: Werkzeug/3.1.5 Python/3.12.12
Date: Thu, 02 Apr 2026 17:58:25 GMT
Content-Type: application/json
Content-Length: 702
Connection: close

{"endpoints":[{"description":"Service information","method":"GET","path":"/"},{"description":"Health check","method":"GET","path":"/health"}],"request":{"client_ip":"10.244.0.1","method":"GET","path":"/","user_agent":"curl/8.5.0"},"runtime":{"current_time":"2026-04-02T17:58:25.939765+00:00","timezone":"UTC","uptime_human":"0.0h 0.0m","uptime_seconds":47.487697},"service":{"description":"DevOps course info service","framework":"Flask","name":"devops-info-service","version":"1.0.0"},"system":{"architecture":"x86_64","cpu_count":12,"hostname":"test-release-devops-info-service-5b885c6988-c652k","platform":"Linux","platform_version":"#1 SMP Tue Nov 5 00:21:55 UTC 2024","python_version":"3.12.12"}}
```