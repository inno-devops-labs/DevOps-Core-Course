# lab 10: helm package manager

## 1. chart overview

### chart structure

```
k8s/devops-info-service/
├── Chart.yaml              # chart metadata
├── values.yaml             # default configuration values
├── values-dev.yaml         # development environment values
├── values-prod.yaml        # production environment values
├── charts/                 # chart dependencies (empty)
└── templates/
    ├── _helpers.tpl        # template helpers (labels, names)
    ├── deployment.yaml     # deployment template
    ├── service.yaml        # service template
    ├── serviceaccount.yaml # service account template
    ├── NOTES.txt           # post-install notes
    └── hooks/
        ├── pre-install-job.yaml   # pre-install hook
        └── post-install-job.yaml  # post-install hook
```

### key template files

| file | purpose |
|------|---------|
| [_helpers.tpl](../devops-info-service/templates/_helpers.tpl) | reusable template functions for labels, names, selectors |
| [deployment.yaml](../devops-info-service/templates/deployment.yaml) | parameterized deployment with probes and resources |
| [service.yaml](../devops-info-service/templates/service.yaml) | configurable service (nodeport/loadbalancer) |
| [hooks/pre-install-job.yaml](../devops-info-service/templates/hooks/pre-install-job.yaml) | validation before installation |
| [hooks/post-install-job.yaml](../devops-info-service/templates/hooks/post-install-job.yaml) | smoke tests after installation |

### values organization

```
values.yaml (base)
├── values-dev.yaml (overrides for development)
└── values-prod.yaml (overrides for production)
```

---

## 2. configuration guide

### important values

| value | default | description |
|-------|---------|-------------|
| `replicaCount` | 3 | number of pod replicas |
| `image.repository` | onemoreslacker/devops-info-service | docker image |
| `image.tag` | v0 | image tag |
| `image.pullPolicy` | IfNotPresent | image pull policy |
| `service.type` | NodePort | service type |
| `service.port` | 80 | service port |
| `service.targetPort` | 5000 | container port |
| `service.nodePort` | 30080 | node port (for NodePort type) |
| `resources.limits.cpu` | 200m | cpu limit |
| `resources.limits.memory` | 256Mi | memory limit |
| `resources.requests.cpu` | 100m | cpu request |
| `resources.requests.memory` | 128Mi | memory request |

### health check configuration

| probe | default path | initial delay | period |
|-------|--------------|---------------|--------|
| liveness | /health | 10s | 5s |
| readiness | /health | 5s | 3s |

### environment-specific values

**development (values-dev.yaml):**
| setting | value | why |
|---------|-------|-----|
| replicaCount | 1 | save resources in dev |
| image.tag | latest | always get latest changes |
| image.pullPolicy | Always | always pull latest |
| resources.limits.cpu | 100m | lower cpu for dev |
| resources.limits.memory | 128Mi | lower memory for dev |
| env.DEBUG | True | enable debug logging |
| livenessProbe.initialDelaySeconds | 5 | faster startup check |

**production (values-prod.yaml):**
| setting | value | why |
|---------|-------|-----|
| replicaCount | 5 | high availability |
| image.tag | v0 | specific version |
| service.type | LoadBalancer | cloud load balancer |
| resources.limits.cpu | 500m | headroom for traffic |
| resources.limits.memory | 512Mi | headroom for gc |
| env.DEBUG | False | no debug in prod |
| livenessProbe.initialDelaySeconds | 30 | slower startup for larger heap |
| affinity | pod anti-affinity | spread across nodes |

### example installations

```bash
# install with default values
helm install myapp k8s/devops-info-service

# install for development
helm install myapp-dev k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml

# install for production
helm install myapp-prod k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml

# override specific value
helm install myapp k8s/devops-info-service --set replicaCount=5 --set service.type=LoadBalancer

# override multiple values
helm install myapp k8s/devops-info-service \
  -f k8s/devops-info-service/values-prod.yaml \
  --set image.tag=v1.0.0
```

---

## 3. hook implementation

### pre-install hook

**purpose:** validate environment before installation

**configuration:**
| annotation | value | purpose |
|------------|-------|---------|
| helm.sh/hook | pre-install | runs before resources created |
| helm.sh/hook-weight | "-5" | execution order (lower first) |
| helm.sh/hook-delete-policy | hook-succeeded | delete after success |

**what it does:**
1. checks cluster connectivity
2. validates namespace
3. checks resource quotas

### post-install hook

**purpose:** smoke tests after installation

**configuration:**
| annotation | value | purpose |
|------------|-------|---------|
| helm.sh/hook | post-install | runs after resources ready |
| helm.sh/hook-weight | "5" | execution order (higher runs later) |
| helm.sh/hook-delete-policy | hook-succeeded | delete after success |

**what it does:**
1. waits for deployment to be ready
2. checks service endpoints
3. verifies health check endpoint
4. confirms pods are ready

### hook weights

```
pre-install (-5) → main resources (0) → post-install (5)
     ↓                    ↓                    ↓
 validation          deployment           smoke tests
```

### deletion policies

| policy | when to use |
|--------|-------------|
| hook-succeeded | clean up successful hooks |
| hook-failed | clean up failed hooks |
| before-hook-creation | delete previous before new |

---

## 4. installation evidence

### helm installation

[helm install output](screenshots/helm-install.png)

### helm list

[helm list output](screenshots/helm-list.png)

### deployed resources

[kubectl get all](screenshots/helm-kubectl-get-all.png)

### hook execution output

[hooks execution](screenshots/hooks-execution.png)


### different environment deployments

**development environment (values-dev.yaml):**

[helm install devops-app-dev](screenshots/helm-install-dev.png)

**production environment (values-prod.yaml):**

[helm install devops-app-prod](screenshots/helm-install-prod.png)

**comparison:**
| aspect | dev | prod |
|--------|-----|------|
| replicas | 1 | 5 |
| image tag | latest | v0 |
| service type | NodePort | LoadBalancer |
| cpu limit | 100m | 500m |
| memory limit | 128Mi | 512Mi |
| debug mode | True | False |
| pod anti-affinity | no | yes |

---

## 5. operations

### installation

```bash
# install from local chart
helm install <release-name> k8s/devops-info-service

# install with custom values
helm install <release-name> k8s/devops-info-service -f custom-values.yaml

# install with values override
helm install <release-name> k8s/devops-info-service --set replicaCount=5

# dry-run to see rendered manifests
helm install <release-name> k8s/devops-info-service --dry-run --debug
```

### upgrade

```bash
# upgrade with new values
helm upgrade <release-name> k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml

# upgrade with specific value change
helm upgrade <release-name> k8s/devops-info-service --set image.tag=v1.0.1

# upgrade with atomic (auto-rollback on failure)
helm upgrade <release-name> k8s/devops-info-service --atomic
```

### rollback

```bash
# view history
helm history <release-name>

# rollback to previous revision
helm rollback <release-name>

# rollback to specific revision
helm rollback <release-name> 2
```

### uninstall

```bash
# uninstall release
helm uninstall <release-name>

# uninstall and keep history
helm uninstall <release-name> --keep-history
```

### useful commands

```bash
# list releases
helm list

# list releases in all namespaces
helm list -A

# get release status
helm status <release-name>

# get rendered manifests
helm get manifest <release-name>

# get values (merged)
helm get values <release-name>

# get values (user-supplied only)
helm get values <release-name> --all

# download values
helm get values <release-name> -o yaml > current-values.yaml
```

---

## 6. testing & validation

### lint

[helm lint](screenshots/helm-lint.png)

### template rendering

[helm templates](screenshots/helm-templates.png)

### verification

[curl](screenshots/helm-curl.png)

---

## 7. key learnings

| concept | understanding |
|---------|---------------|
| helm charts | package of kubernetes resources with templating |
| values | configuration parameters for customization |
| templates | go templates for dynamic resource generation |
| hooks | lifecycle events for pre/post actions |
| releases | instances of charts in clusters |
| rollback | version history for recovery |

### best practices learned

1. **never hardcode values** - make everything configurable
2. **use helper templates** - keep templates dry and consistent
3. **test with dry-run** - validate before applying
4. **use meaningful labels** - standard kubernetes labels for discovery
5. **implement hooks** - validate and test at lifecycle events
6. **version your charts** - use semver for chart versions
7. **separate environments** - use different values files per environment

---

## 8. comparison: raw manifests vs helm

| aspect | raw manifests | helm charts |
|--------|---------------|-------------|
| reusability | copy/paste | parameterized templates |
| versioning | git only | chart versioning + releases |
| rollback | kubectl rollout | helm rollback |
| environments | separate files | values file override |
| dependencies | manual | chart dependencies |
| testing | manual | hooks + helm test |
| packaging | none | chart archives |

---

## 9. file references

| file | description |
|------|-------------|
| [Chart.yaml](../devops-info-service/Chart.yaml) | chart metadata |
| [values.yaml](../devops-info-service/values.yaml) | default configuration |
| [values-dev.yaml](../devops-info-service/values-dev.yaml) | development overrides |
| [values-prod.yaml](../devops-info-service/values-prod.yaml) | production overrides |
| [_helpers.tpl](../devops-info-service/templates/_helpers.tpl) | template helpers |
| [deployment.yaml](../devops-info-service/templates/deployment.yaml) | deployment template |
| [service.yaml](../devops-info-service/templates/service.yaml) | service template |
| [pre-install-job.yaml](../devops-info-service/templates/hooks/pre-install-job.yaml) | pre-install hook |
| [post-install-job.yaml](../devops-info-service/templates/hooks/post-install-job.yaml) | post-install hook |
