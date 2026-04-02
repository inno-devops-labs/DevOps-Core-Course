# Lab 10 — Helm Package Manager

## Overview

In this lab, I converted my Lab 9 Kubernetes manifests into reusable Helm charts and validated the result in my local `kind` cluster. I completed both the main assignment and the bonus task. My final solution consists of:

- one application chart for the Python service
- one application chart for the bonus Go service
- one shared library chart for common helpers
- environment-specific values for the main chart
- Helm hooks for lifecycle validation and smoke testing

I kept the health checks enabled and made their configuration customizable through values, as required by the task.

## Step 1 — Helm Fundamentals

I started by installing Helm and verifying the installed version.

```bash
$ helm version --short
v4.1.3+gc94d381
```

After that, I explored a public chart repository to review chart structure and metadata in a real example.

```bash
$ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
"prometheus-community" has been added to your repositories

$ helm repo update
...Successfully got an update from the "prometheus-community" chart repository

$ helm show chart prometheus-community/prometheus
apiVersion: v2
name: prometheus
description: Prometheus is a monitoring system and time series database.
type: application
version: 28.14.1
appVersion: v3.10.0
```

This confirmed the standard Helm chart structure and reminded me why Helm is useful in this course project:

- I can package Kubernetes resources into versioned charts.
- I can reuse the same templates with different values.
- I can manage installs and upgrades as releases instead of manually applying YAML files.
- I can add lifecycle automation with hooks.

## Step 2 — Converting My Lab 9 Manifests into a Helm Chart

I used my Lab 9 manifests as the starting point. The base Kubernetes resources already existed as raw YAML files in the `k8s/` directory, so my next step was to move that logic into a Helm chart.

I created the main chart here:

```text
k8s/devops-info-service/
```

The main files are:

- `Chart.yaml`
- `values.yaml`
- `values-dev.yaml`
- `values-prod.yaml`
- `templates/deployment.yaml`
- `templates/service.yaml`
- `templates/hooks/pre-install-job.yaml`
- `templates/hooks/post-install-job.yaml`
- `templates/NOTES.txt`

In `Chart.yaml`, I declared the chart as an `application` chart and set the chart metadata:

```yaml
apiVersion: v2
name: devops-info-service
description: Helm chart for the Python DevOps Info Service
type: application
version: 0.1.0
appVersion: "1.0.0"
```

Then I converted the old static manifests into templates.

### Deployment Template

In the deployment template, I made the following values configurable:

- image repository
- image tag
- image pull policy
- replica count
- revision history limit
- rolling update settings
- resource requests and limits
- environment variables
- liveness probe
- readiness probe

The deployment template uses values such as:

```yaml
replicas: {{ .Values.replicaCount }}
image: "{{ .Values.image.repository }}:{{ default .Chart.AppVersion .Values.image.tag }}"
```

I also added a checksum annotation for the environment variable list so that configuration changes can trigger a rollout:

```yaml
checksum/config: {{ toJson .Values.env | sha256sum }}
```

### Service Template

In the service template, I made the following items configurable:

- service type
- service port
- target port
- optional NodePort

That allowed the same chart to be used for both development and production without copying manifests.

### Health Checks

The lab explicitly says never to comment out probes, so I preserved them and moved all probe settings into values:

- `path`
- `port`
- `initialDelaySeconds`
- `periodSeconds`
- `timeoutSeconds`
- `failureThreshold`

This kept the probes active while still making them tunable per environment.

## Step 3 — Designing the Values Files

I organized the chart values so that the default file contains the common configuration, while environment-specific files override only what changes between environments.

### Default Values

The default `values.yaml` contains:

- `replicaCount: 3`
- Python image settings
- default environment variables
- `NodePort` service defaults
- resource requests and limits
- liveness and readiness probe settings
- hook configuration

### Development Values

I created `values-dev.yaml` for development. In this file, I configured:

- `replicaCount: 1`
- smaller CPU and memory requests/limits
- `NodePort` service
- a dedicated NodePort value
- development-specific environment variables such as `SERVICE_NAME`, `SERVICE_VERSION`, and `RELEASE_TRACK`

The key idea was to keep development lightweight and fast to test.

### Production Values

I created `values-prod.yaml` for production. In this file, I configured:

- `replicaCount: 4`
- stronger resource requests and limits
- `LoadBalancer` service type
- production-specific environment variables
- more conservative probe timings

This allowed me to install the chart in development mode first and then upgrade the same release to production values later.

## Step 4 — Creating Helm Hooks

The next part of the lab was to implement lifecycle hooks. I added two jobs:

- a `pre-install` validation job
- a `post-install` smoke-test job

Both are defined in:

- `k8s/devops-info-service/templates/hooks/pre-install-job.yaml`
- `k8s/devops-info-service/templates/hooks/post-install-job.yaml`

### Pre-Install Hook

The pre-install hook validates the release configuration before the application resources are created. I used a lightweight `busybox` image and printed key deployment parameters such as:

- release name
- namespace
- image name
- replica count
- service type

I configured it with:

- `helm.sh/hook: pre-install`
- `helm.sh/hook-weight: "-5"`
- `helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded`

### Post-Install Hook

The post-install hook performs an HTTP smoke test against the deployed service by requesting `/health` from inside the cluster.

I configured it with:

- `helm.sh/hook: post-install`
- `helm.sh/hook-weight: "5"`
- `helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded`

### Why I Used Hook Weights and Deletion Policies

I used a lower weight for the pre-install job and a higher weight for the post-install job to make the execution order explicit.

I also used `before-hook-creation,hook-succeeded` so that:

- old hook jobs do not block new installs or upgrades
- successful jobs are automatically deleted
- the namespace stays clean after validation is complete

In addition, I set `ttlSecondsAfterFinished` and `backoffLimit` to keep the jobs predictable and easy to debug.

## Step 5 — Implementing the Bonus Task with a Library Chart

For the bonus task, I created a second application chart for the Go service and extracted the shared Helm helper logic into a library chart.

### Bonus Application Chart

I created the second chart here:

```text
k8s/devops-info-service-alt/
```

This chart deploys the Go version of the application. It has its own:

- `Chart.yaml`
- `values.yaml`
- `templates/deployment.yaml`
- `templates/service.yaml`
- `templates/hooks/pre-install-job.yaml`
- `templates/hooks/post-install-job.yaml`
- `templates/NOTES.txt`

### Library Chart

I created the shared library chart here:

```text
k8s/common-lib/
```

Its `Chart.yaml` declares:

```yaml
type: library
```

Inside `templates/_helpers.tpl`, I extracted the common logic for:

- chart name generation
- full resource name generation
- chart labels
- selector labels

The shared helpers include:

- `common-lib.name`
- `common-lib.fullname`
- `common-lib.chart`
- `common-lib.selectorLabels`
- `common-lib.labels`

### Using the Library in Both Application Charts

In both application charts, I added this dependency:

```yaml
dependencies:
  - name: common-lib
    version: 0.1.0
    repository: "file://../common-lib"
```

Then I used the helpers from the library chart inside the deployment and service templates:

```yaml
name: {{ include "common-lib.fullname" . }}
labels:
  {{- include "common-lib.labels" . | nindent 4 }}
selector:
  matchLabels:
    {{- include "common-lib.selectorLabels" . | nindent 6 }}
```

This removed duplicated helper code from the two application charts and made the naming and labels consistent.

## Step 6 — Preparing the Images for Local Validation

To validate the charts in my local `kind` cluster, I built both container images locally:

```bash
docker build -t devops-info-service:lab10-python app_python
docker build -t devops-info-service-go:lab10-go app_go
```

While doing that, I found a real issue in the Go Dockerfile: it was hardcoded to build an `amd64` binary. On my local environment, that would break the bonus deployment when running in the current cluster setup. I fixed the Dockerfile so that it builds for the target architecture using build arguments:

```dockerfile
ARG TARGETOS=linux
ARG TARGETARCH
RUN CGO_ENABLED=0 GOOS=${TARGETOS} GOARCH=${TARGETARCH} go build ...
```

After that, I loaded both images into the existing `kind` cluster:

```bash
kind load docker-image devops-info-service:lab10-python --name lab9
kind load docker-image devops-info-service-go:lab10-go --name lab9
```

## Step 7 — Building Dependencies and Validating the Charts

Before installing the charts, I built the local file-based dependencies and ran Helm validation commands.

```bash
helm dependency build k8s/devops-info-service
helm dependency build k8s/devops-info-service-alt

helm lint k8s/devops-info-service
helm lint k8s/devops-info-service-alt
```

The lint results were successful:

```bash
$ helm lint k8s/devops-info-service
==> Linting k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed

$ helm lint k8s/devops-info-service-alt
==> Linting k8s/devops-info-service-alt
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted, 0 chart(s) failed
```

I also rendered the manifests locally with `helm template` to verify that:

- values were substituted correctly
- the hooks were rendered
- the selectors and labels matched
- the dev environment produced a `NodePort` service

## Step 8 — Installing the Main Chart in Development Mode

I installed the Python application chart first with development values:

```bash
helm install devops-info-service k8s/devops-info-service \
  -n devops-lab10 \
  --create-namespace \
  -f k8s/devops-info-service/values-dev.yaml \
  --wait --debug
```

During this installation:

- the `pre-install` hook executed first
- the deployment and service were created
- the `post-install` hook ran after the application became ready

While the hook jobs were still present, I inspected them with `kubectl describe job` and confirmed:

- the correct hook annotations were present
- the configured weights were applied
- the deletion policy matched the chart configuration

For example, the pre-install job looked like this:

```text
Annotations:                 helm.sh/hook: pre-install
                             helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded
                             helm.sh/hook-weight: -5
```

At this stage, the development profile created:

- 1 application replica
- `NodePort` service
- reduced resource requests and limits

## Step 9 — Upgrading the Main Chart to Production Values

After confirming the development deployment worked, I upgraded the same release to production values:

```bash
helm upgrade devops-info-service k8s/devops-info-service \
  -n devops-lab10 \
  -f k8s/devops-info-service/values-prod.yaml \
  --wait --debug
```

This changed the live release to:

- `replicaCount: 4`
- `service.type: LoadBalancer`
- higher resource requests and limits
- production-specific environment values

The rollout completed successfully:

```bash
$ kubectl rollout status deployment/devops-info-service -n devops-lab10 --timeout=120s
deployment "devops-info-service" successfully rolled out
```

In the `kind` environment, the `LoadBalancer` external IP remained `<pending>`, which is expected because there is no real cloud load balancer integration in this local cluster. However, the service type itself was applied correctly.

## Step 10 — Installing the Bonus Chart

I then installed the bonus Go application chart:

```bash
helm install devops-info-service-alt k8s/devops-info-service-alt \
  -n devops-lab10 \
  --wait --debug
```

This installation also executed:

- a `pre-install` validation hook
- a `post-install` smoke-test hook

The bonus chart successfully reused the library chart helpers and deployed:

- 2 Go application replicas
- a `ClusterIP` service
- working readiness and liveness probes

## Step 11 — Verifying the Final Cluster State

After installing both charts, I checked the final release list:

```bash
$ helm list -n devops-lab10
NAME                    NAMESPACE    REVISION  UPDATED                              STATUS    CHART                         APP VERSION
devops-info-service     devops-lab10 2         2026-04-02 16:07:43.420407 +0300 MSK deployed devops-info-service-0.1.0     1.0.0
devops-info-service-alt devops-lab10 1         2026-04-02 16:08:49.576833 +0300 MSK deployed devops-info-service-alt-0.1.0 1.0.0
```

Then I checked the resources in the namespace:

```bash
$ kubectl get all -n devops-lab10
NAME                                           READY   STATUS    RESTARTS   AGE
pod/devops-info-service-5694b5995-5vzlg        1/1     Running   0          103s
pod/devops-info-service-5694b5995-82ph8        1/1     Running   0          116s
pod/devops-info-service-5694b5995-rmm76        1/1     Running   0          79s
pod/devops-info-service-5694b5995-tbfr5        1/1     Running   0          91s
pod/devops-info-service-alt-5d7dddbc9c-8s4g4   1/1     Running   0          41s
pod/devops-info-service-alt-5d7dddbc9c-snc89   1/1     Running   0          41s

NAME                              TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service       LoadBalancer   10.96.252.171   <pending>     80:30081/TCP   3m
service/devops-info-service-alt   ClusterIP      10.96.12.235    <none>        80/TCP         41s

NAME                                      READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-service       4/4     4            4           3m
deployment.apps/devops-info-service-alt   2/2     2            2           41s
```

Finally, I confirmed that the hook jobs were deleted after success, exactly as the chart configuration intended:

```bash
$ kubectl get jobs -n devops-lab10
No resources found in devops-lab10 namespace.
```

## Step 12 — Testing Application Accessibility

To confirm that both deployed applications were actually reachable and healthy, I used `kubectl port-forward` and `curl`.

### Python Service

```bash
$ curl -s http://127.0.0.1:18080/health
{"status":"healthy","timestamp":"2026-04-02T13:10:31.298219+00:00","uptime_seconds":166}
```

```bash
$ curl -s http://127.0.0.1:18080/ | jq '{service: .service, runtime: .runtime}'
{
  "service": {
    "description": "Production deployment of the Python DevOps Info Service",
    "framework": "Flask",
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "runtime": {
    "current_time": "2026-04-02T13:10:31.330420+00:00",
    "timezone": "UTC",
    "uptime_human": "0 hours, 2 minutes",
    "uptime_seconds": 166
  }
}
```

### Bonus Go Service

```bash
$ curl -s http://127.0.0.1:18081/health
{"status":"healthy","timestamp":"2026-04-02T13:10:31Z","uptime_seconds":92}
```

```bash
$ curl -s http://127.0.0.1:18081/ | jq '{service: .service, runtime: .runtime}'
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "net/http"
  },
  "runtime": {
    "uptime_seconds": 92,
    "uptime_human": "0 hours, 1 minute",
    "current_time": "2026-04-02T13:10:31Z",
    "timezone": "UTC"
  }
}
```

These checks confirmed that both charts deployed working applications and that the health endpoints used by the probes and hooks were valid.

## Operations

These are the Helm operations I used during the lab and can use again later.

### Install the Main Chart in Development Mode

```bash
helm install devops-info-service k8s/devops-info-service \
  -n devops-lab10 \
  --create-namespace \
  -f k8s/devops-info-service/values-dev.yaml \
  --wait
```

### Upgrade the Main Chart to Production Mode

```bash
helm upgrade devops-info-service k8s/devops-info-service \
  -n devops-lab10 \
  -f k8s/devops-info-service/values-prod.yaml \
  --wait
```

### Install the Bonus Chart

```bash
helm install devops-info-service-alt k8s/devops-info-service-alt \
  -n devops-lab10 \
  --wait
```

### Roll Back the Main Chart

```bash
helm rollback devops-info-service 1 -n devops-lab10 --wait
```

### Uninstall the Charts

```bash
helm uninstall devops-info-service -n devops-lab10
helm uninstall devops-info-service-alt -n devops-lab10
kubectl delete namespace devops-lab10
```

## Conclusion

In this lab, I completed all required tasks and the bonus task:

- I installed and verified Helm.
- I explored a public chart and reviewed Helm concepts.
- I converted my Lab 9 Kubernetes manifests into a reusable Helm chart.
- I created environment-specific values for development and production.
- I implemented working pre-install and post-install hooks.
- I validated the chart with `helm lint`, `helm template`, `helm install`, and `helm upgrade`.
- I created a second application chart for the bonus task.
- I extracted shared helper templates into a reusable library chart.
- I deployed and verified both applications in the cluster.

As a result, I now have a reusable Helm-based deployment structure for both applications, with shared logic, configurable environments, and working lifecycle validation.
