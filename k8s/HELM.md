# LAB10 - Helm Package Manager

## 1. Chart Overview

### Helm value proposition (why Helm)

Helm gives us a reusable package layer over Kubernetes manifests:

- A **Chart** is a versioned package of Kubernetes resources.
- A **Release** is one installed instance of that chart in a cluster.
- **Values** let us change behavior per environment without duplicating YAML.
- **Hooks** let us run lifecycle tasks (pre/post install, etc.) in a controlled way.

Compared to raw manifests from Lab 9, Helm reduced duplication and made environment changes a one-command upgrade.

### Helm setup and fundamentals evidence

System Helm in this environment is `v3.18.4`, so for lab requirement (4.x) I used a local Helm 4 binary:

```bash
$ /tmp/linux-amd64/helm version
version.BuildInfo{Version:"v4.0.0", GitCommit:"99cd1964357c793351be481d55abbe21c6b2f4ec", GitTreeState:"clean", GoVersion:"go1.25.3", KubeClientVersion:"v1.34"}
```

Repository exploration:

```bash
$ /tmp/linux-amd64/helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
"prometheus-community" has been added to your repositories

$ /tmp/linux-amd64/helm repo update
...Successfully got an update from the "prometheus-community" chart repository
```

```bash
$ /tmp/linux-amd64/helm search repo prometheus-community/prometheus
NAME                                    CHART VERSION   APP VERSION   DESCRIPTION
prometheus-community/prometheus         28.15.0         v3.11.0       Prometheus is a monitoring system...
...
```

```bash
$ /tmp/linux-amd64/helm show chart prometheus-community/prometheus
apiVersion: v2
name: prometheus
version: 28.15.0
appVersion: v3.11.0
dependencies:
  - name: alertmanager
  - name: kube-state-metrics
  - name: prometheus-node-exporter
  - name: prometheus-pushgateway
```

### Chart structure

Chart path: `k8s/devops-info`

```text
k8s/devops-info/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
└── templates/
    ├── _helpers.tpl
    ├── deployment.yaml
    ├── service.yaml
    ├── NOTES.txt
    └── hooks/
        ├── pre-install-job.yaml
        └── post-install-job.yaml
```

### Key templates and purpose

- `templates/deployment.yaml`: app Deployment with probes/resources/rolling update.
- `templates/service.yaml`: Service (NodePort or LoadBalancer from values).
- `templates/_helpers.tpl`: shared naming and label helpers for consistency.
- `templates/hooks/pre-install-job.yaml`: validation task before install.
- `templates/hooks/post-install-job.yaml`: smoke task after install.

## 2. Configuration Guide

### Values organization strategy

- `values.yaml`: default baseline (similar to Lab 9 prod-safe defaults).
- `values-dev.yaml`: developer-friendly footprint.
- `values-prod.yaml`: production-oriented footprint.

Important value groups:

- `replicaCount`: desired pod replicas.
- `image.{repository,tag,pullPolicy}`: container image settings.
- `service.{type,port,targetPort,nodePort}`: exposure model.
- `resources.{requests,limits}`: scheduling and runtime limits.
- `probes.{readiness,liveness}`: health checks (kept mandatory).
- `hooks.*`: lifecycle jobs and behavior.

### Environment differences

#### Development (`values-dev.yaml`)

- `replicaCount: 1`
- `service.type: NodePort` (`nodePort: 30081`)
- lower resources (`50m/64Mi` requests)
- `env.RELEASE_VERSION: dev`
- faster probe startup

#### Production (`values-prod.yaml`)

- `replicaCount: 3`
- `service.type: LoadBalancer`
- higher resources (`200m/256Mi` requests, `500m/512Mi` limits)
- `image.tag: 1.0.0`
- `env.RELEASE_VERSION: prod`
- stricter probe timing

### Installation/override examples

```bash
# Dev install
/tmp/linux-amd64/helm install lab10-dev k8s/devops-info -f k8s/devops-info/values-dev.yaml

# Upgrade same release to prod
/tmp/linux-amd64/helm upgrade lab10-dev k8s/devops-info -f k8s/devops-info/values-prod.yaml

# One-off override example
/tmp/linux-amd64/helm upgrade --install lab10-dev k8s/devops-info --set replicaCount=5
```

## 3. Hook Implementation

### Implemented hooks

1. **Pre-install hook**
- File: `templates/hooks/pre-install-job.yaml`
- Type: `pre-install`
- Purpose: run validation task before release resources are installed.

2. **Post-install hook**
- File: `templates/hooks/post-install-job.yaml`
- Type: `post-install`
- Purpose: run smoke-style task after install.

### Hook annotations

Both jobs include:

- `"helm.sh/hook"`: lifecycle phase (`pre-install`, `post-install`)
- `"helm.sh/hook-weight"`: execution ordering
- `"helm.sh/hook-delete-policy"`: `before-hook-creation,hook-succeeded`

### Execution order and weights

- Pre-install weight: `-5`
- Post-install weight: `5`

Lower values run earlier, so pre-install always runs before post-install.

### Deletion policy behavior

Policy `hook-succeeded` deletes hook jobs after successful completion.

Evidence:

```bash
$ kubectl get jobs -n default
No resources found in default namespace.
```

## 4. Installation Evidence

### Helm releases

```bash
$ /tmp/linux-amd64/helm list -A
NAME      NAMESPACE  REVISION  STATUS    CHART             APP VERSION
lab10-dev default    4         deployed  devops-info-0.1.0 1.0.0
```

### `kubectl get all` evidence

```bash
$ kubectl get all -n default
NAME                                         READY   STATUS    RESTARTS   AGE
pod/lab10-dev-devops-info-746f8b66c9-lgqvj   1/1     Running   0          ...
pod/lab10-dev-devops-info-746f8b66c9-lkztj   1/1     Running   0          ...
pod/lab10-dev-devops-info-746f8b66c9-wh2nc   1/1     Running   0          ...

NAME                            TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/lab10-dev-devops-info   LoadBalancer   10.98.125.142   <pending>     80:30081/TCP   ...

NAME                                    READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/lab10-dev-devops-info   3/3     3            3           ...
```

### Hook execution evidence

Watched jobs during install:

```bash
$ kubectl get jobs -w -n default
lab10-dev-devops-info-pre-install   Running
lab10-dev-devops-info-pre-install   Complete
```

Hook lifecycle events show both hooks executed and completed:

```bash
$ kubectl get events -n default --sort-by=.lastTimestamp | grep 'lab10-dev-devops-info-.*install'
... SuccessfulCreate job/lab10-dev-devops-info-pre-install
... Completed       job/lab10-dev-devops-info-pre-install
... SuccessfulCreate job/lab10-dev-devops-info-post-install
... Completed       job/lab10-dev-devops-info-post-install
```

`kubectl describe job` output was captured during execution (before auto-deletion):

- Pre-install job details included:
  - `helm.sh/hook: pre-install`
  - `helm.sh/hook-weight: -5`
  - `helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded`

- Post-install job details included:
  - `helm.sh/hook: post-install`
  - `helm.sh/hook-weight: 5`
  - `helm.sh/hook-delete-policy: before-hook-creation,hook-succeeded`

### Multi-environment deployment evidence (dev -> prod)

Dev install state:

```bash
$ kubectl get deploy,svc,pods -l app.kubernetes.io/instance=lab10-dev -o wide
deployment ... READY 1/1, image j0cos/devops-info-service:lab02
service ... TYPE NodePort, PORT 80:30081
```

Dev accessibility:

```bash
$ minikube service lab10-dev-devops-info --url
http://192.168.49.2:30081

$ curl -sS http://192.168.49.2:30081/health
{"status":"healthy",...}
```

After prod upgrade:

```bash
$ kubectl get deployment lab10-dev-devops-info -o jsonpath='replicas={.spec.replicas} image={.spec.template.spec.containers[0].image}'
replicas=3 image=j0cos/devops-info-service:1.0.0

$ kubectl get svc lab10-dev-devops-info -o jsonpath='{.spec.type}'
LoadBalancer
```

Prod accessibility verification (via port-forward because minikube LoadBalancer external IP is pending):

```bash
$ kubectl port-forward svc/lab10-dev-devops-info 18080:80
$ curl -sS http://127.0.0.1:18080/health
{"status":"healthy",...}
```

## 5. Operations

### Commands used

Install:

```bash
/tmp/linux-amd64/helm install lab10-dev k8s/devops-info -f k8s/devops-info/values-dev.yaml --wait --timeout 5m
```

Upgrade to prod:

```bash
/tmp/linux-amd64/helm upgrade lab10-dev k8s/devops-info -f k8s/devops-info/values-prod.yaml --wait --timeout 5m
```

History:

```bash
$ /tmp/linux-amd64/helm history lab10-dev
REVISION ... DESCRIPTION
1 ... Install complete
2 ... Upgrade complete
3 ... Rollback to 1
4 ... Upgrade complete
```

Rollback demonstration performed:

```bash
/tmp/linux-amd64/helm rollback lab10-dev 1 --wait --timeout 5m
```

Rollback verification (captured):

```bash
after_rollback replicas=1 image=j0cos/devops-info-service:lab02
service_type=NodePort
```

Uninstall command:

```bash
/tmp/linux-amd64/helm uninstall lab10-dev
```

Note: I executed uninstall only for a temporary hook-demo release (`lab10-hooks`) after collecting hook evidence.

## 6. Testing & Validation

### Helm lint

```bash
$ /tmp/linux-amd64/helm lint k8s/devops-info
1 chart(s) linted, 0 chart(s) failed
```

### Template rendering

```bash
$ /tmp/linux-amd64/helm template test-render k8s/devops-info
# Rendered Deployment, Service, pre-install Job, post-install Job
# Includes probes, resources, and values-driven image/replicas/service
```

### Dry-run with debug

```bash
$ /tmp/linux-amd64/helm install --dry-run --debug test-release k8s/devops-info
STATUS: pending-install
HOOKS:
  - pre-install Job (weight -5)
  - post-install Job (weight 5)
MANIFEST:
  - Service
  - Deployment
```

### Runtime validation summary

- Chart installed successfully in dev and prod configurations.
- Dev -> prod upgrade applied expected changes (replicas/image/service type/resources).
- Hook jobs executed in lifecycle order and were deleted on success.
- Application endpoint reachable in both scenarios (NodePort and port-forward).

