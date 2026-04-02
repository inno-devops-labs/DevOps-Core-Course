# Lab 10 — Helm Package Manager

## Task 1 — Helm Fundamentals

### Helm installation & version verification

The Helm CLI is installed and runs version 4.x.

Command:

```bash
helm version
```

Output:

```text
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.26.1", KubeClientVersion:"v1.35"}
```

### Chart repositories added / explored

Command:

```bash
helm repo list
```

Output:

```text
NAME                	URL                                               
prometheus-community	https://prometheus-community.github.io/helm-charts
```

Command:

```bash
helm search repo prometheus-community | head -n 20
```

Output (snippet):

```text
NAME                                              	CHART VERSION	APP VERSION	DESCRIPTION                                       
prometheus-community/alertmanager                 	1.34.0       	v0.31.1    	The Alertmanager handles alerts sent by client ...
prometheus-community/kube-prometheus-stack        	82.16.1      	v0.89.0    	kube-prometheus-stack collects Kubernetes manif...
prometheus-community/prometheus                   	28.14.1      	v3.10.0    	Prometheus is a monitoring system and time seri...
```

### Exploring a public chart

Example inspection of a public chart (Prometheus):

Command:

```bash
helm show chart prometheus-community/prometheus | head -n 60
```

Output (snippet):

```text
apiVersion: v2
appVersion: v3.10.0
description: Prometheus is a monitoring system and time series database.
name: prometheus
type: application
version: 28.14.1
```

### Value proposition

Helm packages Kubernetes manifests into reusable **charts** and renders them using **Go templates** with **values**. It provides repeatable **installs/upgrades**, a release history, and rollback support. Helm also supports **lifecycle hooks** (pre/post install/upgrade/delete) to run jobs around release events.

---

## Chart Overview

- Parameterized templates (image, replicas, resources, service configuration, labels).
- Configurable health checks (readiness/liveness probes).
- Helm lifecycle hooks (pre-install and post-install jobs).
- Multi-environment support via `values-dev.yaml` and `values-prod.yaml`.
- Bonus: a library chart (`common-lib`) reused by two app charts.

### Chart structure

Main charts:

- `k8s/devops-info-service/`
- `k8s/devops-app-java/`
- `k8s/common-lib/` (bonus library chart)

Key template files (app charts):

- `templates/deployment.yaml`: Deployment template with security contexts, env vars, resources, and probes.
- `templates/service.yaml`: Service template with configurable `type`, ports, and conditional `nodePort`.
- `templates/hooks/pre-install-job.yaml`: pre-install Job hook.
- `templates/hooks/post-install-job.yaml`: post-install Job hook.
- `templates/_helpers.tpl`: chart-specific helper wrappers (naming/labels via `common-lib`).

Values organization:

- `values.yaml`: defaults (production-like baseline).
- `values-dev.yaml`: dev overrides (1 replica, smaller resources, NodePort service).
- `values-prod.yaml`: prod overrides (3 replicas+, proper resources, LoadBalancer service).

---

## Configuration Guide

### Important values

- `replicaCount`: number of Deployment replicas.
- `image.repository` / `image.tag` / `image.pullPolicy`: container image configuration.
- `resources.requests.`* and `resources.limits.*`: CPU/memory requests and limits.
- `service.type`: `NodePort` (dev) or `LoadBalancer` (prod).
- `service.port`, `service.portName`, `service.targetPort`, `service.nodePort`: service port settings.
- `probes.readiness` and `probes.liveness`: HTTP probe configuration.
- `env.*`: environment variables passed to the container (`HOST`, `PORT`, `SERVICE_NAME`, `SERVICE_VERSION`, etc.).
- `hooks.preInstall.sleepSeconds` / `hooks.postInstall.sleepSeconds`: hook runtime duration.

### Example installs (dev and prod)

Dev:

```bash
helm install devops-info k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml --wait --timeout 300s
```

Upgrade to prod:

```bash
helm upgrade devops-info k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml --wait --timeout 300s
```

---

## Hook Implementation

### Hooks added

- **Pre-install hook** (`templates/hooks/pre-install-job.yaml`)
  - Annotation: `helm.sh/hook: pre-install`
  - Weight: `helm.sh/hook-weight: "-5"` (runs earlier)
  - Deletion policy: `helm.sh/hook-delete-policy: hook-succeeded`
- **Post-install hook** (`templates/hooks/post-install-job.yaml`)
  - Annotation: `helm.sh/hook: post-install`
  - Weight: `helm.sh/hook-weight: "5"` (runs after install resources are created)
  - Deletion policy: `helm.sh/hook-delete-policy: hook-succeeded`

### Execution order (weights)

Lower weight runs first. In this chart:

- `pre-install` hook weight is `-5`
- `post-install` hook weight is `+5`

### Deletion policy behavior

Because the delete policy is `hook-succeeded`, hook Jobs are removed after successful completion.

---

## Installation Evidence

### Kubernetes cluster evidence

Command:

```bash
kubectl cluster-info
```

Output:

```text
Kubernetes control plane is running at https://127.0.0.1:64730
CoreDNS is running at https://127.0.0.1:64730/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy
```

Command:

```bash
kubectl get nodes -o wide
```

Output:

```text
NAME       STATUS   ROLES           AGE    VERSION   INTERNAL-IP    EXTERNAL-IP   OS-IMAGE                         KERNEL-VERSION     CONTAINER-RUNTIME
minikube   Ready    control-plane   5d2h   v1.35.1   192.168.49.2   <none>        Debian GNU/Linux 12 (bookworm)   6.10.14-linuxkit   docker://29.2.1
```

### Helm releases list

Command:

```bash
helm list -A
```

Output:

```text
NAME             	NAMESPACE	REVISION	UPDATED                             	STATUS  	CHART                    	APP VERSION
devops-app2      	default  	1       	2026-04-02 13:08:41.244777 +0300 MSK	deployed	devops-app-java-0.1.0    	latest     
devops-info      	default  	2       	2026-04-02 12:59:10.22802 +0300 MSK 	deployed	devops-info-service-0.1.0	latest     
devops-info-hooks	default  	1       	2026-04-02 12:57:21.562297 +0300 MSK	deployed	devops-info-service-0.1.0	latest     
```

### Deployed resources (`kubectl get all`)

Command:

```bash
kubectl get all -n default -l app.kubernetes.io/instance=devops-info
```

Output:

```text
NAME                                                   READY   STATUS    RESTARTS   AGE
pod/devops-info-devops-info-service-5b9b94cf4f-6mq2h   1/1     Running   0          30m
pod/devops-info-devops-info-service-5b9b94cf4f-f29zm   1/1     Running   0          30m
pod/devops-info-devops-info-service-5b9b94cf4f-w7kjg   1/1     Running   0          30m

NAME                                      TYPE           CLUSTER-IP    EXTERNAL-IP   PORT(S)        AGE
service/devops-info-devops-info-service   LoadBalancer   10.96.128.3   127.0.0.1     80:30082/TCP   33m

NAME                                              READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-devops-info-service   3/3     3            3           33m
```

### Service spec evidence (`LoadBalancer`)

Command:

```bash
kubectl get svc devops-info-devops-info-service -o yaml | sed -n '1,120p'
```

Output (snippet):

```text
spec:
  ports:
  - name: http
    nodePort: 30082
    port: 80
    protocol: TCP
    targetPort: http
  type: LoadBalancer
status:
  loadBalancer:
    ingress:
    - ip: 127.0.0.1
      ipMode: VIP
```

### Deployment spec evidence (replicas/resources/probes)

Command:

```bash
kubectl describe deployment devops-info-devops-info-service | sed -n '1,200p'
```

Output (snippet):

```text
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Containers:
 devops-info-service:
  Image:      gghost1/devops-lab-app-python:1.0.0
  Limits:
    cpu:     300m
    memory:  384Mi
  Requests:
    cpu:      100m
    memory:   128Mi
  Liveness:   http-get http://:http/health delay=30s timeout=2s period=5s #success=1 #failure=3
  Readiness:  http-get http://:http/health delay=10s timeout=2s period=3s #success=1 #failure=3
  Environment:
    SERVICE_VERSION:          1.0.0
    SERVICE_DESCRIPTION:      Production environment (LoadBalancer)
```

### Dev vs Prod verification

Dev values (Helm revision 1):
Command:

```bash
helm get values devops-info --revision 1
```

Output:

```text
USER-SUPPLIED VALUES:
replicaCount: 1
service:
  nodePort: 30082
  type: NodePort
```

Prod values (Helm revision 2):
Command:

```bash
helm get values devops-info --revision 2
```

Output:

```text
USER-SUPPLIED VALUES:
replicaCount: 3
service:
  nodePort: ""
  type: LoadBalancer
```

Additionally, the Service shows `LoadBalancer` and external IP `127.0.0.1`:

```text
devops-info-devops-info-service   LoadBalancer   10.96.128.3   127.0.0.1
```

### Hook execution output

Evidence below shows hooks are created, executed, and then deleted due to `hook-succeeded`.

Command (hook-only install for evidence):

```bash
helm install devops-info-hooks2 k8s/devops-info-service \
  -f k8s/devops-info-service/values-dev.yaml \
  --set service.nodePort=30085 \
  --set hooks.preInstall.sleepSeconds=15 \
  --set hooks.postInstall.sleepSeconds=15 \
  --wait=hookOnly --timeout 5m --debug
```

#### Pre-install hook (job created + logs)

Command:

```bash
kubectl get jobs -n default | awk 'NR==1 || $1 ~ /devops-info-hooks2/ {print}'
kubectl describe job devops-info-hooks2-devops-info-service-pre-install -n default | sed -n '1,120p'
kubectl logs job/devops-info-hooks2-devops-info-service-pre-install -n default --tail=20
```

Output (snippet):

```text
NAME                                                 STATUS    COMPLETIONS   DURATION   AGE
devops-info-hooks2-devops-info-service-pre-install   Running   0/1           6s         6s

Annotations:      helm.sh/hook: pre-install
                  helm.sh/hook-delete-policy: hook-succeeded
                  helm.sh/hook-weight: -5
Args:
  echo "Pre-install hook is running for devops-info-hooks2";
  sleep 15;
  echo "Pre-install hook completed";

Pre-install hook is running for devops-info-hooks2
```

#### Post-install hook (job created + logs)

Command:

```bash
kubectl get jobs -n default | awk 'NR==1 || $1 ~ /devops-info-hooks2/ {print}'
kubectl describe job devops-info-hooks2-devops-info-service-post-install -n default | sed -n '1,120p'
kubectl logs job/devops-info-hooks2-devops-info-service-post-install -n default --tail=20
```

Output (snippet):

```text
NAME                                                  STATUS    COMPLETIONS   DURATION   AGE
devops-info-hooks2-devops-info-service-post-install   Running   0/1           9s         9s

Annotations:      helm.sh/hook: post-install
                  helm.sh/hook-delete-policy: hook-succeeded
                  helm.sh/hook-weight: 5
Args:
  echo "Post-install hook is running for devops-info-hooks2";
  sleep 15;
  echo "Post-install hook completed";

Post-install hook is running for devops-info-hooks2
Post-install hook completed
```

After completion, hook Jobs were deleted (deletion policy `hook-succeeded`):
Command:

```bash
kubectl get jobs -n default | awk 'NR==1 || $1 ~ /devops-info-hooks2/ {print}'
```

Output:

```text
No resources found in default namespace.
```

---

## Operations

### Commands used

- Install (dev):
  ```bash
  helm install devops-info k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml --wait --timeout 300s
  ```
- Upgrade to prod:
  ```bash
  helm upgrade devops-info k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml --wait --timeout 300s
  ```
- Rollback (documented command example):
  ```bash
  helm rollback devops-info 1
  ```
- Uninstall:
  ```bash
  helm uninstall devops-info
  ```

---

## Testing & Validation

### `helm lint` output

Command:

```bash
helm lint k8s/devops-info-service
helm lint k8s/devops-app-java
```

Output:

```text
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
==> Linting k8s/devops-app-java
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### `helm template` verification (rendered manifests)

Command:

```bash
helm template devops-info k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml > /tmp/devops-info-dev.rendered.yaml
wc -l /tmp/devops-info-dev.rendered.yaml
head -n 40 /tmp/devops-info-dev.rendered.yaml
```

Output (snippet):

```text
     180 /tmp/devops-info-dev.rendered.yaml
---
# Source: devops-info-service/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: devops-info-devops-info-service
spec:
  type: NodePort
  ports:
    - name: http
      port: 80
      targetPort: http
      nodePort: 30082
```

### Dry-run output (hooks)

Command:

```bash
helm install devops-info-dry k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml --dry-run --debug 2>&1 | awk '/HOOKS:|helm\\.sh\\/hook|hook-delete-policy|hook-weight/ {print}'
```

Output:

```text
HOOKS:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": hook-succeeded
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": hook-succeeded
```

### Application accessibility verification

To verify the application endpoint, I used `kubectl port-forward` to the Service and tested `/health`.

Command:

```bash
kubectl port-forward service/devops-info-devops-info-service 8080:80 -n default
curl -sS http://127.0.0.1:8080/health
```

```text
Forwarding from 127.0.0.1:8080 -> 5000
Forwarding from [::1]:8080 -> 5000
```

And then:

```text
{"status":"healthy","timestamp":"2026-04-02T10:01:00.416Z","uptime_seconds":109}
```

### Application logs (evidence of successful probe traffic)

Command:

```bash
kubectl logs -l app.kubernetes.io/instance=devops-info --tail=10
```

Output (snippet):

```text
2026-04-02 10:29:52,966 - devops-info-service - INFO - GET /health from 10.244.0.1
2026-04-02 10:29:52,966 - werkzeug - INFO - 10.244.0.1 - - [02/Apr/2026 10:29:52] "GET /health HTTP/1.1" 200 -
```

---

## Bonus — Library Charts

### Library chart created

Library chart:

- `k8s/common-lib/Chart.yaml` is set to `type: library`

It contains shared helper templates:

- `common.name`
- `common.fullname`
- `common.labels`
- `common.selectorLabels`

### Both app charts use the library

Both application charts declare a local dependency:

```yaml
dependencies:
  - name: common-lib
    version: 0.1.0
    repository: "file://../common-lib"
```

They then use helper wrappers (`templates/_helpers.tpl`) which delegate to `common-lib` helpers for consistent naming and labels, eliminating duplication.

### Benefits

Using a library chart improves:

- DRYness (shared naming/label logic in one place).
- Consistency (same label schema across apps).
- Maintainability (updates to naming/labels are done once in `common-lib`).

### Bonus Deployment Evidence (both apps)

Both application charts were installed successfully and render templates using the shared `common-lib` dependency:

```text
NAME             	NAMESPACE	REVISION	UPDATED                             	STATUS  	CHART                    	APP VERSION
devops-app2      	default  	1       	2026-04-02 13:08:41.244777 +0300 MSK	deployed	devops-app-java-0.1.0    	latest     
devops-info      	default  	2       	2026-04-02 12:59:10.22802 +0300 MSK 	deployed	devops-info-service-0.1.0	latest     
devops-info-hooks	default  	1       	2026-04-02 12:57:21.562297 +0300 MSK	deployed	devops-info-service-0.1.0	latest     
```

Second app Service (dev):

```text
devops-app2-devops-app-java   NodePort   10.97.156.52   <none>        80:30083/TCP
```

