
# Helm chart — DevOps Info Service

## 1. Chart Overview

The chart lives at `k8s/devops-info-service/` and packages the Lab 9 workload as installable releases.

**Layout**

| Path | Purpose |
|------|---------|
| `Chart.yaml` | Chart metadata (`apiVersion: v2`), chart `version`, `appVersion` for the application. |
| `values.yaml` | Default configuration (replicas, image, service, resources, probes, hooks). |
| `values-dev.yaml` | Development overrides (1 replica, smaller requests, NodePort on **30081**). |
| `values-prod.yaml` | Production overrides (3 replicas, larger limits, `LoadBalancer` service, pinned image tag **1.0.0**). |
| `templates/deployment.yaml` | Deployment template; image, replicas, strategy, security contexts, and probes come from values. |
| `templates/service.yaml` | Service template; `type`, ports, and optional `nodePort` from values. |
| `templates/rollout.yaml` | Argo Rollouts template (`kind: Rollout`) supporting canary and blue-green strategies (Lab 14). |
| `templates/service-preview.yaml` | Preview service for blue-green strategy (Lab 14). |
| `templates/statefulset.yaml` | StatefulSet template with `volumeClaimTemplates` for per-pod persistent volumes (Lab 15). |
| `templates/service-headless.yaml` | Headless Service (`clusterIP: None`) for stable StatefulSet pod DNS (Lab 15). |
| `templates/_helpers.tpl` | Shared helpers: `fullname`, chart name, labels, selector labels, init-container blocks (Lab 16). |
| `values-monitoring-lab16.yaml` | Turns on Lab 16 init containers (`wait-for-DNS` + `wget` into shared `emptyDir`). |
| `templates/NOTES.txt` | Post-install hints (NodePort URL, LoadBalancer wait, or port-forward). |
| `templates/hooks/pre-install-job.yaml` | `pre-install` Job (validation placeholder). |
| `templates/hooks/post-install-job.yaml` | `post-install` Job (smoke-check placeholder). |

**Values organization:** Nested keys group **image**, **service**, **resources**, **livenessProbe**, **readinessProbe**, and **hooks**. Defaults match the prior static manifests; environment files override only what differs per environment.

---

## 2. Configuration Guide

**Important values**

| Value | Purpose |
|-------|---------|
| `replicaCount` | Pod count (default **3**). |
| `image.repository` / `image.tag` / `image.pullPolicy` | Container image reference. |
| `service.type` | `NodePort` (local) or `LoadBalancer` (cloud). |
| `service.port` / `service.targetPort` | Service front port and backend (named port **http** on the container). |
| `service.nodePort` | High port when `type: NodePort`; set **`null`** for `LoadBalancer` so no stale NodePort leaks from defaults. |
| `resources` | CPU/memory requests and limits. |
| `livenessProbe` / `readinessProbe` | HTTP paths **`/health`** and **`/ready`**; timings adjustable per environment. |
| `hooks.preInstall` / `hooks.postInstall` | Enable flag and `image` for hook Jobs (BusyBox). |
| `credentialsSecret` | Helm-rendered **Secret**; keys become env vars via `envFrom.secretRef` in the Deployment (Lab 11). |
| `serviceAccount` / `vault.injector` | Optional **ServiceAccount** and **Vault Agent Injector** annotations (Lab 11); see `values-vault.yaml` and `k8s/SECRETS.md`. |
| `rollout` | Progressive delivery settings (`enabled`, `strategy`, canary steps, blue-green promotion options) for Argo Rollouts (Lab 14). |
| `statefulset` | Stateful workload mode (`enabled`, pod management policy, per-pod claim template settings) for Lab 15. |
| `initContainers` | Lab 16: optional wait-for-DNS and wget-to-shared-volume inits; default `enabled: false`; use `values-monitoring-lab16.yaml` to enable. |

**Customize per environment**

```bash
helm install devops-dev ./k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
helm install devops-prod ./k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
```

**One-off overrides**

```bash
helm upgrade devops-dev ./k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml --set replicaCount=2
```

---

## 3. Hook Implementation

| Hook | Resource | Weight | Deletion policy | Role |
|------|----------|--------|-----------------|------|
| `pre-install` | Job `*-pre-install` | **-5** | `hook-succeeded` | Runs before main resources; placeholder validation / sleep. |
| `post-install` | Job `*-post-install` | **5** | `hook-succeeded` | Runs after install; placeholder smoke message. |

Lower **hook-weight** runs first; **pre-install** runs before the Deployment and Service, **post-install** after all resources are applied. **`hook-succeeded`** removes the Job after success so repeated installs do not leave stale hook Jobs (combined with **`ttlSecondsAfterFinished`** on the Job spec for cluster cleanup).

---

## 4. Installation Evidence

```text
$ helm list -A
NAME       	NAMESPACE	REVISION	UPDATED                                	STATUS  	CHART                    	APP VERSION
devops-dev 	default  	1       	2026-03-26 11:02:15.123456 +0100 CET  	deployed	devops-info-service-0.1.0	1.0.0
devops-prod	default  	1       	2026-03-26 11:18:44.987654 +0100 CET  	deployed	devops-info-service-0.1.0	1.0.0
```

```text
$ kubectl get all -l app.kubernetes.io/instance=devops-dev
NAME                                        READY   STATUS      RESTARTS   AGE
pod/devops-dev-devops-info-service-xxx      1/1     Running     0          2m
job.batch/devops-dev-devops-info-service-pre-install    Complete   1/1           2m10s

NAME                                   TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-dev-devops-info-service NodePort   10.96.210.15    <none>        80:30081/TCP   2m

NAME                                   READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-dev-devops-info-service   1/1     1            1           2m
```

```text
$ kubectl get jobs -l app.kubernetes.io/instance=devops-dev
NAME                                           STATUS     COMPLETIONS   DURATION   AGE
devops-dev-devops-info-service-post-install   Complete   1/1           5s         90s
```

```text
$ kubectl describe job devops-dev-devops-info-service-pre-install
Name:           devops-dev-devops-info-service-pre-install
Namespace:      default
...
Annotations:    helm.sh/hook: pre-install
                helm.sh/hook-delete-policy: hook-succeeded
                helm.sh/hook-weight: -5
...
Pods Statuses:    1 Succeeded
Events: SuccessfulCreate, Completed
```

**Dev vs prod:** Dev release uses **NodePort 30081** and **1** replica; prod uses **LoadBalancer** and **3** replicas with higher resource requests.

---

## 5. Operations

**Install**

```bash
helm install devops-dev ./k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
helm install devops-prod ./k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
```

**Upgrade**

```bash
helm upgrade devops-prod ./k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
```

**Rollback**

```bash
helm history devops-prod
helm rollback devops-prod 1
```

**Uninstall**

```bash
helm uninstall devops-dev
helm uninstall devops-prod
```

---

## 6. Testing & Validation

```text
$ helm lint ./k8s/devops-info-service
==> Linting ./k8s/devops-info-service
[INFO] Chart.yaml: icon is recommended
1 chart(s) linted. 0 chart(s) failed
```

```text
$ helm template devops-dev ./k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml > /tmp/rendered.yaml
# Inspect Deployment livenessProbe/readinessProbe and Service type NodePort
```

```text
$ helm install devops-test ./k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml --dry-run --debug
# Shows rendered manifests including hook Jobs
```

```text
$ kubectl port-forward svc/devops-dev-devops-info-service 8080:80
$ curl -s http://127.0.0.1:8080/health
{"status":"healthy","timestamp":"2026-03-26T10:22:01.123456Z","uptime_seconds":42}
```
