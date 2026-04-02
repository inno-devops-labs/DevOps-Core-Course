## Helm Package Manager (Lab 10)
### Chart structure

This Helm chart follows a standard and production-ready structure for deploying a Kubernetes application. Below is an explanation of each component and its purpose

### Root Directory

```
testiks/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
└── templates/
  ├── _helpers.tpl
  ├── deployment.yaml
  ├── service.yaml
  ├── hooks-preinstall-job.yaml
  └── hooks-postinstall-job.yaml
```

### Files and its purpose
charts/: Directory containing any dependencies


Chart.yaml:
- This file contains metadata about the Helm chart
Purpose:
- Defines chart name, version, and description
- Specifies chart type (application or library)
- Provides application version


values.yaml:
- The values.yaml file defines default configuration values used across templates.
Purpose:

- Centralized configuration management
- Allows easy customization without modifying templates
- Supports overrides via CLI or environment-specific files

_helpers.tpl:
- Contains reusable template definitions.
Purpose:
- Avoid duplication
- Standardize naming and labels
- Improve maintainability

deployment.yaml
- Defines the Kubernetes Deployment resource.
Purpose:
- Deploys the application pods
- Configures replicas, rolling updates, and container settings
- Uses values from values.yaml for dynamic configuration

hooks-postinstall-job.yaml:
- Defines a Helm post-install hook
Purpose:
- Executes after installation completes
- Used for smoke tests or notifications

## task 1

```
$ sudo apt install helm
$ helm version
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.26.1", KubeClientVersion:"v1.35"}
```

I started by creating a Helm chart in the k8s/ directory for my application. To do this, I ran the following command:
```
helm create k8s/testiks
```
This generated the basic Helm chart structure with all the necessary files and directories. I then updated the Chart.yaml to include the metadata for my chart:
```
apiVersion: v2
name: testiks
description: Helm chart for py web application
type: application
version: 0.1.0
appVersion: "1.0"
```
The name field is set to testiks, and I chose 0.1.0 as the chart version. The appVersion is set to "1.0" to represent the version of my Python app.

promethus repo:
```
$ helm show chart prometheus-community/prometheus
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
```

### Why Helm matters
Helm simplifies Kubernetes application management by providing a package manager for deploying, managing, and scaling applications. It allows you to define reusable and customizable Kubernetes manifests using charts, making deployments consistent across environments. Helm also offers versioning, rollback capabilities, dependency management, and automation, ensuring easier and more reliable application management on Kubernetes

## Task 2

Important Values:
- replicaCount: number of pod replicas
- image.repository / image.tag: container image source
- containerPort: container listening port
- service.type: NodePort for local access, LoadBalancer for production-style exposure
- service.nodePort: fixed local NodePort for dev install
- resources.requests / resources.limits: scheduler and runtime resource boundaries
- livenessProbe / readinessProbe: health-check timings and paths
- hooks.enabled: enables lifecycle Jobs

### Environment Customization

Two environment-specific configuration files are used:
- Development (values-dev.yaml)
    - 1 replica
    - Lower resource usage
    - NodePort service
    - Latest image tag

- Production (values-prod.yaml)
    - 5 replicas
    - Higher resource limits
    - LoadBalancer service
    - Fixed image version

### Install example
Development:
```
helm install testiks . -f values-dev.yaml
```
Production:
```
helm upgrade testiks . -f values-prod.yaml
```

## Task 3

Two Helm hooks are implemented:
1. Pre-install Hook
- Runs before chart installation
- Purpose: simulate pre-deployment validation

2. Post-install Hook
- Runs after deployment
- Purpose: simulate smoke testing

| | Pre-install | Post-install |
|---|-------------|--------------|
| Kind | Job | Job |
| `helm.sh/hook` | `pre-install` | `post-install` |
| `helm.sh/hook-weight` | `-5` | `5` |
| `helm.sh/hook-delete-policy` | `hook-succeeded` when `hooks.deleteAfterSuccess` is true | same |


### Operations
```
helm uninstall dev -n lab10-dev
helm uninstall prod -n lab10-prod
helm upgrade dev ./k8s/testiks -f k8s/testiks/values-dev.yaml -n lab10-dev
helm history dev -n lab10-dev
helm rollback dev <rev> -n lab10-dev
```

## Installation evidence

```text
$ helm lint ./k8s/testiks
==> Linting ./k8s/testiks
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed
```

```text
$ kubectl config current-context
minikube

$ kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:65035
CoreDNS is running at https://127.0.0.1:65035/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

$ kubectl get nodes
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   8d    v1.32.0
```

```bash
helm template dev ./k8s/testiks -f k8s/testiks/values-dev.yaml -n lab10-dev
helm template prod ./k8s/testiks -f k8s/testiks/values-prod.yaml -n lab10-prod
```

```text
$ helm template dev ./k8s/testiks -f k8s/testiks/values-dev.yaml -n lab10-dev 2>&1 | head -42
---
# Source: testiks/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dev-testiks
  labels:
    helm.sh/chart: testiks-0.1.0
    app.kubernetes.io/name: testiks
    app.kubernetes.io/instance: dev
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: testiks
      app.kubernetes.io/instance: dev
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app.kubernetes.io/name: testiks
        app.kubernetes.io/instance: dev
    spec:
      containers:
        - name: testiks
          image: "cacucoh/testiks:latest"
          imagePullPolicy: Always
          ports:
            - name: http
              containerPort: 5000
              protocol: TCP
```

```text
$ helm install dev ./k8s/testiks \
  -f k8s/testiks/values-dev.yaml \
  --namespace lab10-dev --create-namespace
NAME: dev
LAST DEPLOYED: Thu Apr  2 19:39:50 2026
NAMESPACE: lab10-dev
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
1. Get the application URL by running these commands:
  export NODE_PORT=$(kubectl get --namespace lab10-dev -o jsonpath="{.spec.ports[0].nodePort}" services dev-testiks)
  export NODE_IP=$(kubectl get nodes --namespace lab10-dev -o jsonpath="{.items[0].status.addresses[0].address}")
  echo http://$NODE_IP:$NODE_PORT/health

Release: dev
Namespace: lab10-dev
```

```text
$ helm list -n lab10-dev
NAME    NAMESPACE       REVISION        UPDATED                                 STATUS        CHART                            APP VERSION
dev     lab10-dev       1               2026-04-02 19:39:50.110994 +0300 MSK    deployed      testiks-0.1.0        1.0.0
```

```text
$ kubectl get all -n lab10-dev
NAME                                           READY   STATUS    RESTARTS   AGE
pod/dev-testiks-84579bd9bb-8mnkp   1/1     Running   0          62s

NAME                              TYPE       CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/dev-testiks   NodePort   10.103.117.200   <none>        80:30081/TCP   62s

NAME                                      READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/dev-testiks   1/1     1            1           62s

NAME                                                 DESIRED   CURRENT   READY   AGE
replicaset.apps/dev-testiks-84579bd9bb   1         1         1       62s
```

With default `deleteAfterSuccess: true`, hook Jobs are removed after success (`kubectl get jobs` is empty). With `values-hooks-keep.yaml`:

```bash
helm uninstall dev -n lab10-dev
helm install dev ./k8s/testiks \
  -f k8s/testiks/values-dev.yaml \
  -f k8s/testiks/values-hooks-keep.yaml \
  --namespace lab10-dev
kubectl get jobs -n lab10-dev
kubectl describe job dev-testiks-pre-install -n lab10-dev
kubectl describe job dev-testiks-post-install -n lab10-dev
kubectl logs -n lab10-dev job/dev-testiks-pre-install
kubectl logs -n lab10-dev job/dev-testiks-post-install
```

```text
$ helm install dev ./k8s/testiks \
  -f k8s/testiks/values-dev.yaml \
  -f k8s/testiks/values-hooks-keep.yaml \
  --namespace lab10-dev
NAME: dev
LAST DEPLOYED: Thu Apr  2 19:48:28 2026
NAMESPACE: lab10-dev
STATUS: deployed
REVISION: 1
```

```text
$ kubectl get jobs -n lab10-dev
NAME                                   STATUS     COMPLETIONS   DURATION   AGE
dev-testiks-post-install   Complete   1/1           4s         12s
dev-testiks-pre-install    Complete   1/1           3s         15s
```

```text
$ kubectl describe job dev-testiks-pre-install -n lab10-dev
Name:             dev-testiks-pre-install
Namespace:        lab10-dev
Selector:         batch.kubernetes.io/controller-uid=b3df58aa-361f-48fd-8b38-934fa4dbe167
Labels:           app.kubernetes.io/instance=dev
                  app.kubernetes.io/managed-by=Helm
                  app.kubernetes.io/name=testiks
                  app.kubernetes.io/version=1.0.0
                  helm.sh/chart=testiks-0.1.0
Annotations:      helm.sh/hook: pre-install
                  helm.sh/hook-weight: -5
Parallelism:      1
Completions:      1
Completion Mode:  NonIndexed
Suspend:          false
Backoff Limit:    2
Start Time:       Thu, 02 Apr 2026 19:48:28 +0300
Completed At:     Thu, 02 Apr 2026 19:48:31 +0300
Duration:         3s
Pods Statuses:    0 Active (0 Ready) / 1 Succeeded / 0 Failed
Pod Template:
  Labels:  app.kubernetes.io/managed-by=Helm
           batch.kubernetes.io/controller-uid=b3df58aa-361f-48fd-8b38-934fa4dbe167
           batch.kubernetes.io/job-name=dev-testiks-pre-install
           controller-uid=b3df58aa-361f-48fd-8b38-934fa4dbe167
           helm.sh/hook=pre-install
           job-name=dev-testiks-pre-install
  Containers:
   pre-install:
    Image:      busybox:1.36
    Command:
      sh
      -c
      set -e
      echo "pre-install: release=dev ns=lab10-dev"
      echo "pre-install OK"
    Environment:   <none>
    Mounts:        <none>
  Volumes:         <none>
  Node-Selectors:  <none>
  Tolerations:     <none>
Events:
  Type    Reason            Age   From            Message
  ----    ------            ----  ----            -------
  Normal  SuccessfulCreate  22s   job-controller  Created pod: dev-testiks-pre-install-q8xgb
  Normal  Completed         19s   job-controller  Job completed
```

```text
$ kubectl logs -n lab10-dev job/dev-testiks-pre-install
pre-install: release=dev ns=lab10-dev
pre-install OK
```

```text
$ kubectl logs -n lab10-dev job/dev-testiks-post-install
post-install: smoke GET http://dev-testiks.lab10-dev.svc.cluster.local:80/health
{"status":"healthy","timestamp":"2026-04-02T16:48:32.488027+00:00","uptime_seconds":507}
post-install OK
```

Production install (`values-prod.yaml`):

```text
$ helm list -n lab10-prod
NAME    NAMESPACE       REVISION        UPDATED                                 STATUS  CHART                          APP VERSION
prod    lab10-prod      1               2026-04-02 19:51:57.134345 +0300 MSK    failed  testiks-0.1.0      1.0.0
```

```text
$ kubectl get all -n lab10-prod
NAME                                              READY   STATUS      RESTARTS   AGE
pod/prod-testiks-05dff54df9-b77f4     0/1     Running     0          40s
pod/prod-testiks-05dff54df9-lf2j2     0/1     Running     0          40s
pod/prod-testiks-05dff54df9-q54dt     0/1     Running     0          40s
pod/prod-testiks-05dff54df9-sw95m     1/1     Running     0          40s
pod/prod-testiks-05dff54df9-z45wb     1/1     Running     0          40s
pod/prod-testiks-post-install-t4c9p   0/1     Completed   0          40s

NAME                               TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
service/prod-testiks   LoadBalancer   10.103.135.218   <pending>     80:31854/TCP   40s

NAME                                       READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/prod-testiks   2/5     5            2           40s

NAME                                                  DESIRED   CURRENT   READY   AGE
replicaset.apps/prod-testiks-05dff54df9   5         5         2       40s

NAME                                              STATUS     COMPLETIONS   DURATION   AGE
job.batch/prod-testiks-post-install   Complete   1/1           30s        40s
```

```text
$ kubectl get svc -n lab10-prod
NAME                       TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
prod-testiks   LoadBalancer   10.103.135.218   <pending>     80:31854/TCP   47s
```

```bash
kubectl port-forward -n lab10-prod svc/prod-testiks 8080:80
```

```text
$ kubectl rollout status deployment/prod-testiks -n lab10-prod
deployment "prod-testiks" successfully rolled out

$ helm upgrade prod ./k8s/testiks -f k8s/testiks/values-prod.yaml -n lab10-prod
Release "prod" has been upgraded. Happy Helming!
NAME: prod
LAST DEPLOYED: Thu Apr  2 19:54:16 2026
NAMESPACE: lab10-prod
STATUS: deployed
REVISION: 2
TEST SUITE: None
NOTES:
1. Get the application URL by running these commands:
  NOTE: It may take a few minutes for the LoadBalancer IP to be available.
        Watch status: kubectl get svc -w prod-testiks
  export SERVICE_IP=$(kubectl get svc --namespace lab10-prod prod-testiks -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
  echo http://$SERVICE_IP:80/health

Release: prod
Namespace: lab10-prod
```

The following `helm list -A` was captured before `helm upgrade prod`; the upgrade transcript above records `prod` at revision 2 `deployed`.

```text
$ helm list -A
NAME    NAMESPACE       REVISION        UPDATED                                 STATUS        CHART                            APP VERSION
dev     default         1               2026-04-02 19:38:26.499655 +0300 MSK    failed        testiks-0.1.0        1.0.0
dev     lab10-dev       1               2026-04-02 19:48:28.029525 +0300 MSK    deployed      testiks-0.1.0        1.0.0
prod    lab10-prod      1               2026-04-02 19:51:57.134345 +0300 MSK    failed        testiks-0.1.0        1.0.0
```

```bash
helm uninstall dev -n default
```

## Testing and validation

```bash
helm lint ./k8s/testiks
helm template dev ./k8s/testiks -f k8s/testiks/values-dev.yaml -n lab10-dev
helm install dev-dryrun ./k8s/testiks \
  -f k8s/testiks/values-dev.yaml \
  --namespace lab-dryrun --create-namespace \
  --dry-run=client
```

```text
$ helm install dev-dryrun ./k8s/testiks \
  -f k8s/testiks/values-dev.yaml \
  --namespace lab-dryrun --create-namespace \
  --dry-run=client 2>&1 | head -80
NAME: dev-dryrun
LAST DEPLOYED: Thu Apr  2 19:53:17 2026
NAMESPACE: lab-dryrun
STATUS: pending-install
REVISION: 1
TEST SUITE: None
HOOKS:
---
# Source: testiks/templates/hooks/post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: dev-dryrun-testiks-post-install
  annotations:
    helm.sh/hook: post-install
    helm.sh/hook-weight: "5"
    helm.sh/hook-delete-policy: hook-succeeded
  labels:
    helm.sh/chart: testiks-0.1.0
    app.kubernetes.io/name: testiks
    app.kubernetes.io/instance: dev-dryrun
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  backoffLimit: 3
  template:
    metadata:
      labels:
        app.kubernetes.io/managed-by: Helm
        helm.sh/hook: post-install
    spec:
      restartPolicy: Never
      containers:
        - name: post-install
          image: "curlimages/curl:8.5.0"
          command:
            - sh
            - -c
            - |
              set -e
              URL="http://dev-dryrun-testiks.lab-dryrun.svc.cluster.local:80/health"
              echo "post-install: smoke GET $URL"
              i=0
              while [ "$i" -lt 30 ]; do
                if curl -fsS --connect-timeout 3 --max-time 10 "$URL"; then
                  echo "post-install OK"
                  exit 0
                fi
                i=$((i + 1))
                echo "post-install: retry $i/30"
                sleep 2
              done
              echo "post-install: health check failed" >&2
              exit 1
```

```text
$ curl -sS -i localhost:8080/health

HTTP/1.1 200 OK
Server: Werkzeug/3.1.7 Python/3.13.12
Date: Thu, 02 Apr 2026 16:52:58 GMT
Content-Type: application/json
Content-Length: 88
Connection: close

{"status":"healthy","timestamp":"2026-04-02T16:52:58.654555+00:00","uptime_seconds":41}
```

```bash
curl "$(minikube service dev-testiks -n lab10-dev --url)/health"
```