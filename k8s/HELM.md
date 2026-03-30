# Lab 10 — Helm Report (`k8s/HELM.md`)

This document covers **Task 5** (required sections **1–6**) and the **Bonus** write-up from the lab. **Task 1** (Helm install, repos, search) is summarized in the **Appendix** at the end.

## 1. Chart Overview

### Chart structure explanation

Charts live under **`k8s/`**:

- **`devops-info-service`** — main application (Lab 9 workload): Deployment, Service, hook Jobs.
- **`app2-nginx`** — bonus second app: nginx + ConfigMap.
- **`common-lib`** — **library** chart (`type: library`): packaged as `charts/common-lib-0.1.0.tgz`, not installed as its own release.

```text
devops-info-service/
├── Chart.yaml, Chart.lock
├── values.yaml, values-dev.yaml, values-prod.yaml
├── charts/common-lib-0.1.0.tgz
└── templates/
    ├── deployment.yaml, service.yaml, NOTES.txt
    └── hooks/pre-install-job.yaml, post-install-job.yaml
```

### Key template files and their purpose

| File | Purpose |
|------|---------|
| `templates/deployment.yaml` | Deployment; image, replicas, resources, **liveness/readiness** probes from values. |
| `templates/service.yaml` | Service; type and ports from values. |
| `templates/hooks/*.yaml` | Pre/post-install Jobs (see **section 3**). |
| `templates/NOTES.txt` | Post-install hints for the user. |
| `common-lib` (dependency) | Shared helpers: `include "common-lib.labels"`, `common-lib.selectorLabels`, `common-lib.fullname`. |

Health checks are **not** disabled; they come from `values`.

### Values organization strategy

- **Defaults** in `values.yaml` (aligned with former Lab 9 `deployment.yml` / `service.yml`).
- **Overrides** in `values-dev.yaml` and `values-prod.yaml` for environment-specific replica counts, resources, service `type`, and probe timings.
- Nested keys: `image`, `service`, `resources`, `livenessProbe`, `readinessProbe`, `hooks`, etc.

**Bonus — library chart and second app:** `app2-nginx` uses the same `common-lib` dependency and shared label patterns. See **section 6** for lint/template of both charts.

---

## 2. Configuration Guide

### Important values and their purpose

| Value | Purpose |
|-------|---------|
| `fullnameOverride` | Kubernetes resource names (e.g. `devops-info-service`). |
| `replicaCount` | Number of pods. |
| `image.*` | Repository, tag, `pullPolicy`. |
| `service.*` | `type`, `port`, `targetPort`, optional `nodePort`. |
| `resources` | Requests and limits. |
| `livenessProbe` / `readinessProbe` | HTTP probes. |
| `hooks.preInstall` / `hooks.postInstall` | Hook Job image and weight. |

### How to customize for different environments

| File | Use case |
|------|----------|
| `values-dev.yaml` | 1 replica, smaller resources, **NodePort**. |
| `values-prod.yaml` | 3 replicas, higher limits, **LoadBalancer**. |

**macOS:** If `helm dependency update` adds `._*` files into the `common-lib` tarball, `helm lint` can fail. Use `COPYFILE_DISABLE=1`, `xattr -cr common-lib`, or `k8s/scripts/repack-common-lib.sh`, then refresh `Chart.lock` digest if needed.

### Example installations with different configurations

```bash
cd k8s
helm install devops-dev ./devops-info-service -f ./devops-info-service/values-dev.yaml
helm upgrade devops-dev ./devops-info-service -f ./devops-info-service/values-prod.yaml
helm install app2 ./app2-nginx
```

---

## 3. Hook Implementation

### What hooks you implemented and why

| Hook | Purpose |
|------|---------|
| `pre-install` | Lightweight validation step before main resources (stub: echo + sleep). |
| `post-install` | Post-install smoke step after the workload is created (stub: echo + sleep). |

Templates: `templates/hooks/pre-install-job.yaml`, `templates/hooks/post-install-job.yaml`.

### Hook execution order and weights

| Hook | `helm.sh/hook` | `helm.sh/hook-weight` |
|------|----------------|------------------------|
| Pre-install | `pre-install` | `-5` |
| Post-install | `post-install` | `5` |

Lower weight runs first; main chart resources install between the two hook phases.

### Deletion policies explanation

Both Jobs use **`helm.sh/hook-delete-policy: hook-succeeded`**: after the Job completes successfully, Helm **deletes** the Job so it does not stay in the cluster. That is why **`kubectl get jobs`** may show **no resources** shortly after install — expected, not a failure.

For rendered hooks without applying to the cluster:

```bash
helm install test-dev ./devops-info-service -f ./devops-info-service/values-dev.yaml --dry-run=client --debug
```

```text
kubectl get jobs -n default
No resources found in default namespace.
```

---

## 4. Installation Evidence

### `helm list` output

Current releases after install → upgrade → **`helm rollback devops-dev 1`** (`devops-dev` is at **revision 3**):

```text
helm list
NAME            NAMESPACE       REVISION        UPDATED                                 STATUS          CHART                           APP VERSION
app2            default         1               2026-03-30 15:21:05.132132 +0300 MSK    deployed        app2-nginx-0.1.0                1.27
devops-dev      default         3               2026-03-30 15:24:15.661469 +0300 MSK    deployed        devops-info-service-0.1.0       1.0.0
```

**`helm history devops-dev`** (after rollback):

```text
helm history devops-dev
REVISION        UPDATED                         STATUS          CHART                           APP VERSION     DESCRIPTION
1               Mon Mar 30 15:16:07 2026        superseded      devops-info-service-0.1.0       1.0.0           Install complete
2               Mon Mar 30 15:20:28 2026        superseded      devops-info-service-0.1.0       1.0.0           Upgrade complete
3               Mon Mar 30 15:24:15 2026        deployed        devops-info-service-0.1.0       1.0.0           Rollback to 1
```

### `kubectl get all` showing deployed resources

```text
kubectl get all -n default
NAME                                       READY   STATUS    RESTARTS   AGE
pod/app2-nginx-9dd7cb79f-n2bs8             1/1     Running   0          3m2s
pod/devops-info-service-7944fdb697-p69hm   1/1     Running   0          3m28s
pod/devops-info-service-7944fdb697-tppr6   1/1     Running   0          3m16s
pod/devops-info-service-7944fdb697-tw6tv   1/1     Running   0          3m39s

NAME                          TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/app2-service          ClusterIP      10.104.38.155   <none>        80/TCP         3m2s
service/devops-info-service   LoadBalancer   10.104.229.39   <pending>     80:30222/TCP   7m51s
service/kubernetes            ClusterIP      10.96.0.1       <none>        443/TCP        5d3h

NAME                                  READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/app2-nginx            1/1     1            1           3m2s
deployment.apps/devops-info-service   3/3     3            3           7m51s

NAME                                             DESIRED   CURRENT   READY   AGE
replicaset.apps/app2-nginx-9dd7cb79f             1         1         1       3m2s
replicaset.apps/devops-info-service-5ccc77c98    0         0         0       7m51s
replicaset.apps/devops-info-service-7944fdb697   3         3         3       3m39s
```

### Hook execution output (`kubectl get jobs`, `kubectl describe job`)

```text
kubectl get jobs -n default
No resources found in default namespace.
```

Hooks ran during install; Jobs were removed per **`hook-succeeded`**, so there is nothing to `describe` later. To capture hook Pods in a future run, check immediately after `helm install` or watch: `kubectl get jobs -w`.

### Different environment deployments (dev vs prod)

| Stage | Values file | Observed behavior |
|-------|-------------|-------------------|
| **Dev** | `values-dev.yaml` | `helm install` → revision **1**, Service **NodePort**, **1** replica. |
| **Prod** | `values-prod.yaml` | `helm upgrade` → revision **2**, Service **LoadBalancer**, **3** replicas (see `kubectl get all` above). |
| **Rollback** | — | `helm rollback devops-dev 1` → revision **3**, state matching revision **1** (dev-oriented manifest). |

**Note:** If plain Lab 9 YAML existed without Helm labels, delete old `Deployment`/`Service` (and for app2: `ConfigMap`/`Deployment`/`Service`) before installing. Wrong working directory → `Error: path "./..." not found` — use **`cd k8s`**.

**Cluster context:**

```text
kubectl cluster-info
kubectl get nodes
# minikube Ready, control-plane
```

---

## 5. Operations

### Installation commands used

```bash
helm install devops-dev ./devops-info-service -f ./devops-info-service/values-dev.yaml
helm install app2 ./app2-nginx
```

### How to upgrade a release

```bash
helm upgrade devops-dev ./devops-info-service -f ./devops-info-service/values-prod.yaml
```

### How to rollback

```text
helm rollback devops-dev 1
Rollback was a success! Happy Helming!
```

Use `helm history devops-dev` to see revisions.

### How to uninstall

```bash
helm uninstall devops-dev
helm uninstall app2
```

---

## 6. Testing & Validation

### `helm lint` output

```text
helm lint ./devops-info-service ./app2-nginx
2 chart(s) linted, 0 chart(s) failed
```

(`[INFO] Chart.yaml: icon is recommended` — optional Artifact Hub hint.)

### `helm template` verification

```bash
helm template test-dev ./devops-info-service -f ./devops-info-service/values-dev.yaml
```

### Dry-run output

```bash
helm install test-dev ./devops-info-service -f ./devops-info-service/values-dev.yaml --dry-run=client --debug
```

On Helm 4 use **`--dry-run=client`**; bare `--dry-run` is deprecated.

### Application accessibility verification

```text
curl -s http://127.0.0.1:50392/health
{"status":"healthy","timestamp":"2026-03-30T12:18:36.275940+00:00","uptime_seconds":132}
```

(URL from `minikube service devops-info-service --url`.)

---

## Bonus — Library chart + second application

Documentation required by the assignment:

### Library chart structure

- **Path:** `k8s/common-lib/`
- **`Chart.yaml`:** `apiVersion: v2`, `name: common-lib`, **`type: library`**, `version: 0.1.0`. Library charts ship **no installable Kubernetes resources** — only reusable named templates.
- **`templates/_helpers.tpl`:** contains all `define` blocks (see below). There are no `deployment.yaml` / `service.yaml` files in the library.
- **Packaging:** the library is vendored as `charts/common-lib-0.1.0.tgz` under each app chart (or rebuilt via `helm dependency update` / `scripts/repack-common-lib.sh`).

### Shared templates implemented

| Template | Role |
|----------|------|
| `common-lib.name` | Short name from chart / `nameOverride`. |
| `common-lib.chart` | `helm.sh/chart` label value. |
| `common-lib.fullname` | Full resource name (`fullnameOverride` or release-based). |
| `common-lib.labels` | Standard labels: chart, selectors, `app.kubernetes.io/version`, `app.kubernetes.io/managed-by`. |
| `common-lib.selectorLabels` | `app.kubernetes.io/name` and `app.kubernetes.io/instance` for Service/Deployment selectors. |

### How both apps use the library

**Dependency** (same in both `Chart.yaml` files):

```yaml
dependencies:
  - name: common-lib
    version: 0.1.0
    repository: file://../common-lib
```

**In templates:** each application chart calls the library with the **parent** release context, e.g.:

- `{{ include "common-lib.fullname" . }}` — resource names
- `{{ include "common-lib.labels" . | nindent 4 }}` — metadata labels
- `{{ include "common-lib.selectorLabels" . | nindent N }}` — pod selectors and Service `spec.selector`

So **`devops-info-service`** and **`app2-nginx`** do not duplicate label/name logic; they only depend on `common-lib` and consistent `values` (`fullnameOverride`, etc.).

### Benefits of this approach

- **DRY:** One place to change label keys or naming rules for all charts that depend on `common-lib`.
- **Consistency:** Both apps expose the same `app.kubernetes.io/*` and Helm labels, which helps selectors, `kubectl` labels, and GitOps-style conventions.
- **Maintainability:** Updating a shared template or bumping the library version in `Chart.yaml` propagates to every consumer after `helm dependency update`.

### Terminal output showing successful deployment of both apps

```text
helm list
NAME            NAMESPACE       REVISION        UPDATED                                 STATUS          CHART                           APP VERSION
app2            default         1               2026-03-30 15:21:05.132132 +0300 MSK    deployed        app2-nginx-0.1.0                1.27
devops-dev      default         3               2026-03-30 15:24:15.661469 +0300 MSK    deployed        devops-info-service-0.1.0       1.0.0

kubectl get pods,svc -l app.kubernetes.io/instance=devops-dev
kubectl get pods,svc -l app.kubernetes.io/instance=app2
```

Example after install (app2):

```text
kubectl get pods,svc,cm -l app.kubernetes.io/instance=app2
NAME                             READY   STATUS    RESTARTS   AGE
pod/app2-nginx-9dd7cb79f-n2bs8   1/1     Running   0          3s

NAME                   TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
service/app2-service   ClusterIP   10.104.38.155   <none>        80/TCP    3s

NAME                  DATA   AGE
configmap/app2-html   1      3s
```

---

## Appendix — Task 1 (Helm fundamentals)


**Why Helm:** packages Kubernetes apps as versioned **charts**, installs **releases** into the cluster, supports **values** for environments and **hooks** for lifecycle steps—less copy-paste YAML than raw manifests.

**Explore repositories (`helm search repo`):** after `helm repo add prometheus-community …` and `helm repo update`, search lists available charts (excerpt):

```text
helm search repo
NAME                                                    CHART VERSION   APP VERSION     DESCRIPTION
prometheus-community/alertmanager                       1.34.0          v0.31.1         The Alertmanager handles alerts sent by client ...
prometheus-community/kube-prometheus-stack              82.15.1         v0.89.0         kube-prometheus-stack collects Kubernetes manif...
prometheus-community/kube-state-metrics                 7.2.2           2.18.0          Install kube-state-metrics to generate and expo...
prometheus-community/prometheus                         28.14.1         v3.10.0         Prometheus is a monitoring system and time seri...
prometheus-community/prometheus-node-exporter           4.52.2          1.10.2          A Helm chart for prometheus node-exporter
… (50+ more charts in this repository)
```

**`helm version` (full output):**

```text
marinalavrova@MacBook-Pro-Marina k8s % helm version
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.26.1", KubeClientVersion:"v1.35"}
```

**`helm show chart`:** the command needs a chart reference. Without it:

```text
marinalavrova@MacBook-Pro-Marina k8s % helm show chart
Error: "helm show chart" requires 1 argument

Usage:  helm show chart [CHART] [flags]
```

**`helm show chart prometheus-community/kube-prometheus-stack` (full `Chart.yaml` content):**

```yaml
annotations:
  artifacthub.io/license: Apache-2.0
  artifacthub.io/links: |
    - name: Chart Source
      url: https://github.com/prometheus-community/helm-charts
    - name: Upstream Project
      url: https://github.com/prometheus-operator/kube-prometheus
    - name: Upgrade Process
      url: https://github.com/prometheus-community/helm-charts/blob/main/charts/kube-prometheus-stack/README.md#upgrading-chart
  artifacthub.io/operator: "true"
apiVersion: v2
appVersion: v0.89.0
dependencies:
- condition: crds.enabled
  name: crds
  repository: ""
  version: 0.0.0
- condition: kubeStateMetrics.enabled
  name: kube-state-metrics
  repository: https://prometheus-community.github.io/helm-charts
  version: 7.2.2
- condition: nodeExporter.enabled
  name: prometheus-node-exporter
  repository: https://prometheus-community.github.io/helm-charts
  version: 4.52.2
- condition: grafana.enabled
  name: grafana
  repository: https://grafana-community.github.io/helm-charts
  version: 11.3.6
- condition: windowsMonitoring.enabled
  name: prometheus-windows-exporter
  repository: https://prometheus-community.github.io/helm-charts
  version: 0.12.*
description: kube-prometheus-stack collects Kubernetes manifests, Grafana dashboards,
  and Prometheus rules combined with documentation and scripts to provide easy to
  operate end-to-end Kubernetes cluster monitoring with Prometheus using the Prometheus
  Operator.
home: https://github.com/prometheus-operator/kube-prometheus
icon: https://raw.githubusercontent.com/prometheus/prometheus.github.io/master/assets/prometheus_logo-cb55bb5c346.png
keywords:
- operator
- prometheus
- kube-prometheus
kubeVersion: '>=1.25.0-0'
maintainers:
- email: andrew@quadcorps.co.uk
  name: andrewgkew
  url: https://github.com/andrewgkew
- email: gianrubio@gmail.com
  name: gianrubio
  url: https://github.com/gianrubio
- email: github.gkarthiks@gmail.com
  name: gkarthiks
  url: https://github.com/gkarthiks
- email: kube-prometheus-stack@sisti.pt
  name: GMartinez-Sisti
  url: https://github.com/GMartinez-Sisti
- email: github@jkroepke.de
  name: jkroepke
  url: https://github.com/jkroepke
- email: miroslav.hadzhiev@gmail.com
  name: Xtigyro
  url: https://github.com/Xtigyro
- email: quentin.bisson@gmail.com
  name: QuentinBisson
  url: https://github.com/QuentinBisson
name: kube-prometheus-stack
sources:
- https://github.com/prometheus-community/helm-charts
- https://github.com/prometheus-operator/kube-prometheus
type: application
version: 82.15.1
```

**Also completed for Task 1:** `brew install helm`, `helm repo add prometheus-community …` and `helm repo update` (see earlier terminal history).
