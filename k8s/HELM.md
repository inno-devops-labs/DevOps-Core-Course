# Helm Package Manager (Lab 10)

## Chart structure


This Helm chart follows a standard and production-ready structure for deploying a Kubernetes application. Below is an explanation of each component and its purpose.

### Root Directory

```
k8s/devops-service/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
├── templates/
│ ├── _helpers.tpl
│ ├── deployment.yaml
│ ├── service.yaml
│ ├── hooks-preinstall-job.yaml
│ └── hooks-postinstall-job.yaml
```


---

### Chart.yaml

The `Chart.yaml` file contains metadata about the Helm chart.

#### Purpose:
- Defines chart name, version, and description
- Specifies chart type (application or library)
- Provides application version

### values.yaml

The ```values.yaml``` file defines default configuration values used across templates.

Purpose:
* Centralized configuration management
* Allows easy customization without modifying templates
* Supports overrides via CLI or environment-specific files

Contains:
* Replica count
* Container image configuration
* Service settings
* Resource limits
* Health check configuration

### values-dev.yaml / values-prod.yaml

Environment-specific configuration files.

Purpose:

Provide different settings for development and production
Override default values from ```values.yaml```

Differences:
* Development: fewer replicas, lower resource usage, NodePort service
* Production: higher replicas, stricter resources, LoadBalancer service

### _helpers.tpl

Contains reusable template definitions.

Purpose:
* Avoid duplication
* Standardize naming and labels
* Improve maintainability


### deployment.yaml
Defines the Kubernetes Deployment resource.

Purpose:
* Deploys the application pods
* Configures replicas, rolling updates, and container settings
* Uses values from ```values.yaml``` for dynamic configuration

Key Features:
* Templated image and tag
* Configurable replica count
* Resource limits and requests
* Liveness and readiness probes (never hardcoded or removed)


### service.yaml
Defines the Kubernetes Service resource.

Purpose:
* Exposes the application within or outside the cluster
* Maps external traffic to pods

Key Features:
* Configurable service type (NodePort / LoadBalancer)
* Dynamic ports from values

### hooks-preinstall-job.yaml
Defines a Helm pre-install hook.

Purpose:
* Executes before the chart is installed
* Used for setup tasks (e.g., validation, migrations)

Features:
* Hook annotation: pre-install
* Execution order via weight
* Auto-deletion after success

### hooks-postinstall-job.yaml
Defines a Helm post-install hook.

Purpose:
* Executes after installation completes
* Used for smoke tests or notifications

Features:
* Hook annotation: post-install
* Cleanup via deletion policy

## Configuration guide

This Helm chart is configured using `values.yaml` and can be customized for different environments.

### Key Configuration Areas

- **Replicas** – controls how many pods are running  
- **Image** – defines the container image and version  
- **Service** – specifies how the app is exposed (NodePort or LoadBalancer)  
- **Resources** – sets CPU and memory limits  
- **Health Checks** – ensures the app is running and ready  

### Environments

- **Development**: fewer resources, single replica, NodePort  
- **Production**: multiple replicas, higher resources, LoadBalancer  

### Customization

Values can be overridden during installation, making the chart flexible and reusable across environments.

## Hook implementation

This chart uses Helm hooks to manage actions during the release lifecycle.

### Implemented Hooks

- **Pre-install hook**  
  Runs before deployment. Used for preparation tasks such as validation or setup.

- **Post-install hook**  
  Runs after deployment. Used for smoke testing or verification.

### Execution Order

Hooks use weights to control execution order:
- Pre-install runs first (lower weight)
- Post-install runs after resources are created

### Deletion Policy

Both hooks use automatic cleanup:
- Removed after successful execution (`hook-succeeded`)

### Purpose

Hooks improve reliability by ensuring required steps run before and after deployment.


## Installation evidence
## Task 1
### helm installation 

```bash
abraham_barrett@Abrahams-Air DevOps-Core-Course % brew install helm
```

```bash
abraham_barrett@Abrahams-Air DevOps-Core-Course % helm version
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.26.1", KubeClientVersion:"v1.35"}
```

### prometheus repo adding

```bash
abraham_barrett@Abrahams-Air DevOps-Core-Course % helm version
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.26.1", KubeClientVersion:"v1.35"}
abraham_barrett@Abrahams-Air DevOps-Core-Course % helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
"prometheus-community" has been added to your repositories
abraham_barrett@Abrahams-Air DevOps-Core-Course % helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈
abraham_barrett@Abrahams-Air DevOps-Core-Course % helm show chart prometheus-community/prometheus
annotations:
  artifacthub.io/license: Apache-2.0
  artifacthub.io/links: |
    - name: Chart Source
      url: https://github.com/prometheus-community/helm-charts
    - name: Upstream Project
      url: https://github.com/prometheus/prometheus
apiVersion: v2
appVersion: v3.11.0
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
version: 28.15.0

abraham_barrett@Abrahams-Air DevOps-Core-Course % 

```


## Task 2

### validation of the chart

```bash
abraham_barrett@Abrahams-Air DevOps-Core-Course % helm lint k8s/devops-info-service 
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
abraham_barrett@Abrahams-Air DevOps-Core-Course % helm lint k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml 
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
abraham_barrett@Abrahams-Air DevOps-Core-Course % helm lint k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml 
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
abraham_barrett@Abrahams-Air DevOps-Core-Course % helm install --dry-run --debug test-release k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml 
level=WARN msg="--dry-run is deprecated and should be replaced with '--dry-run=client'"
level=DEBUG msg="Original chart version" version=""
level=DEBUG msg="Chart path" path=/Users/abraham_barrett/Documents/DevOps-Core-Course/k8s/devops-info-service
level=DEBUG msg="number of dependencies in the chart" chart=devops-service dependencies=0
NAME: test-release
LAST DEPLOYED: Thu Apr  2 21:59:11 2026
NAMESPACE: default
STATUS: pending-install
REVISION: 1
DESCRIPTION: Dry run complete
TEST SUITE: None
USER-SUPPLIED VALUES:
replicaCount: 1
resources:
  requests:
    cpu: 50m
    memory: 64Mi
service:
  type: NodePort

COMPUTED VALUES:
image:
  pullPolicy: IfNotPresent
  repository: abrahambarrett228/lab02
  tag: latest
probes:
  liveness:
    initialDelaySeconds: 10
    path: /health
    periodSeconds: 10
  readiness:
    initialDelaySeconds: 5
    path: /health
    periodSeconds: 5
replicaCount: 1
resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 50m
    memory: 64Mi
service:
  nodePort: 30560
  port: 80
  targetPort: 5000
  type: NodePort

HOOKS:
---
# Source: devops-service/templates/hooks-postinstall-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: postinstall-job
  annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    spec:
      containers:
        - name: postinstall
          image: busybox
          command: ["sh", "-c", "echo Post-install hook running"]
      restartPolicy: Never
---
# Source: devops-service/templates/hooks-preinstall-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: preinstall-job
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    spec:
      containers:
        - name: preinstall
          image: busybox
          command: ["sh", "-c", "echo Pre-install hook running"]
      restartPolicy: Never
MANIFEST:
---
# Source: devops-service/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: devops-service
  labels:
    app: devops-service
spec:
  type: NodePort
  selector:
    app: devops-service
  ports:
    - port: 80
      targetPort: 5000
      nodePort: 30560
---
# Source: devops-service/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: devops-service
  labels:
    app: devops-service
spec:
  replicas: 1
  revisionHistoryLimit: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: devops-service
  template:
    metadata:
      labels:
        app: devops-service
    spec:
      containers:
        - name: app
          image: "abrahambarrett228/lab02:latest"
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 5000
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
              cpu: 50m
              memory: 64Mi

          livenessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 10
            periodSeconds: 10

          readinessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 5
            periodSeconds: 5

abraham_barrett@Abrahams-Air DevOps-Core-Course % 
```

### installation (dev)

```bash
abraham_barrett@Abrahams-Air DevOps-Core-Course % helm install dev k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml 
NAME: dev
LAST DEPLOYED: Thu Apr  2 22:04:06 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
abraham_barrett@Abrahams-Air DevOps-Core-Course % helm list
NAME	NAMESPACE	REVISION	UPDATED                             	STATUS  	CHART               	APP VERSION
dev 	default  	1       	2026-04-02 22:04:06.233017 +0300 MSK	deployed	devops-service-0.1.0	1.0        
abraham_barrett@Abrahams-Air DevOps-Core-Course % kubectl get all
NAME                                  READY   STATUS    RESTARTS   AGE
pod/devops-service-748545fdf8-dfsvz   1/1     Running   0          24s

NAME                     TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/devops-service   NodePort    10.109.161.205   <none>        80:30560/TCP   24s
service/kubernetes       ClusterIP   10.96.0.1        <none>        443/TCP        7d3h

NAME                             READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-service   1/1     1            1           24s

NAME                                        DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-service-748545fdf8   1         1         1       24s
abraham_barrett@Abrahams-Air DevOps-Core-Course % 
```

## Task 3

```bash
abraham_barrett@Abrahams-Air DevOps-Core-Course % helm upgrade dev k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml 
Release "dev" has been upgraded. Happy Helming!
NAME: dev
LAST DEPLOYED: Thu Apr  2 22:05:47 2026
NAMESPACE: default
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
TEST SUITE: None
abraham_barrett@Abrahams-Air DevOps-Core-Course % kubectl get pods 
NAME                              READY   STATUS              RESTARTS   AGE
devops-service-748545fdf8-5kpbt   1/1     Terminating         0          14s
devops-service-748545fdf8-dfsvz   1/1     Running             0          110s
devops-service-89fbff7bc-5dk4n    1/1     Running             0          7s
devops-service-89fbff7bc-mzv2m    1/1     Running             0          14s
devops-service-89fbff7bc-wgjqf    0/1     ContainerCreating   0          0s
abraham_barrett@Abrahams-Air DevOps-Core-Course % kubectl get pods 
NAME                             READY   STATUS    RESTARTS   AGE
devops-service-89fbff7bc-5dk4n   1/1     Running   0          17s
devops-service-89fbff7bc-mzv2m   1/1     Running   0          24s
devops-service-89fbff7bc-wgjqf   1/1     Running   0          10s
abraham_barrett@Abrahams-Air DevOps-Core-Course % helm history dev       
REVISION	UPDATED                 	STATUS    	CHART               	APP VERSION	DESCRIPTION     
1       	Thu Apr  2 22:04:06 2026	superseded	devops-service-0.1.0	1.0        	Install complete
2       	Thu Apr  2 22:05:47 2026	deployed  	devops-service-0.1.0	1.0        	Upgrade complete
abraham_barrett@Abrahams-Air DevOps-Core-Course % 
```

## Task 4
```kubectl get jobs``` shows nothing because of  ```hook-succeeded``` deletion policy.
However, I can find all the hooks by ```helm get hooks dev ```
```bash
abraham_barrett@Abrahams-Air DevOps-Core-Course % kubectl get jobs
No resources found in default namespace.
abraham_barrett@Abrahams-Air DevOps-Core-Course % helm get hooks dev          
---
# Source: devops-service/templates/hooks-postinstall-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: postinstall-job
  annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    spec:
      containers:
        - name: postinstall
          image: busybox
          command: ["sh", "-c", "echo Post-install hook running"]
      restartPolicy: Never
---
# Source: devops-service/templates/hooks-preinstall-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: preinstall-job
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    spec:
      containers:
        - name: preinstall
          image: busybox
          command: ["sh", "-c", "echo Pre-install hook running"]
      restartPolicy: Never
abraham_barrett@Abrahams-Air DevOps-Core-Course % 
```

## Operations

### install
```bash
helm install <release_name> k8s/devops-info-service
```

### upgrade
```bash
helm upgrade <release_name> k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
```

or 

```bash
helm upgrade <release_name> k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
```

### rollback
```bash
helm rollback <release_name> 1
```

### uninstall
```bash
helm uninstall <release_name>
```



## Testing & Validation

```bash
abraham_barrett@Abrahams-Air DevOps-Core-Course % echo "linter"
linter
abraham_barrett@Abrahams-Air DevOps-Core-Course % helm lint k8s/devops-info-service 
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
abraham_barrett@Abrahams-Air DevOps-Core-Course % echo "templating"
templating
abraham_barrett@Abrahams-Air DevOps-Core-Course % helm template test-release k8s/devops-info-service
---
# Source: devops-service/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: devops-service
  labels:
    app: devops-service
...


abraham_barrett@Abrahams-Air DevOps-Core-Course % helm template test-release k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
---
# Source: devops-service/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: devops-service
  labels:
    app: devops-service
spec:
  type: NodePort
  selector:
    app: devops-service
  ports:
...

abraham_barrett@Abrahams-Air DevOps-Core-Course % helm template test-release k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
---
# Source: devops-service/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: devops-service
  labels:
    app: devops-service
spec:
  type: LoadBalancer
  selector:
    app: devops-service
  ports:
    - port: 80
      targetPort: 5000
      nodePort: 30560
      ...


abraham_barrett@Abrahams-Air DevOps-Core-Course % echo "dry run"                                                                                
dry run
abraham_barrett@Abrahams-Air DevOps-Core-Course % helm install --dry-run --debug demo-release k8s/devops-info-service
level=WARN msg="--dry-run is deprecated and should be replaced with '--dry-run=client'"
level=DEBUG msg="Original chart version" version=""
level=DEBUG msg="Chart path" path=/Users/abraham_barrett/Documents/DevOps-Core-Course/k8s/devops-info-service
level=DEBUG msg="number of dependencies in the chart" chart=devops-service dependencies=0
NAME: demo-release
LAST DEPLOYED: Thu Apr  2 22:24:41 2026
NAMESPACE: default
STATUS: pending-install
REVISION: 1
DESCRIPTION: Dry run complete
TEST SUITE: None
USER-SUPPLIED VALUES:
{}

COMPUTED VALUES:
image:
  pullPolicy: IfNotPresent
  repository: abrahambarrett228/lab02
  tag: latest
probes:
...

abraham_barrett@Abrahams-Air DevOps-Core-Course % echo "availability"                                                
availability

abraham_barrett@Abrahams-Air DevOps-Core-Course % kubectl get svc
NAME             TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
devops-service   LoadBalancer   10.109.161.205   <pending>     80:30560/TCP   21m
kubernetes       ClusterIP      10.96.0.1        <none>        443/TCP        7d4h
```