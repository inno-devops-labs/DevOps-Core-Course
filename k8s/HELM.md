# Lab 10 — Helm (Chart + Multi-env + Hooks)

This lab converts the Lab 9 Kubernetes manifests into a reusable Helm chart with environment values and lifecycle hooks.

Chart location: `k8s/devops-python/`

**Lab 11 (Secrets & Vault):** see `k8s/SECRETS.md` for Kubernetes Secrets, Helm `templates/secrets.yaml`, and optional HashiCorp Vault Agent injection.

---

## Task 1 — Helm Fundamentals (Evidence)

Run and capture output:

```bash
helm version
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm show chart prometheus-community/kube-prometheus-stack | head -50
```

Write a short explanation:
- **Chart** = package of templates + values
- **Release** = installed instance of a chart in a namespace
- **Values** = configuration inputs that customize the templates

---

## Task 2 — Create Your Helm Chart

### Chart structure

```
k8s/devops-python/
├── Chart.yaml
├── values.yaml
├── values-dev.yaml
├── values-prod.yaml
└── templates/
    ├── _helpers.tpl
    ├── rollout.yaml
    ├── statefulset.yaml
    ├── service.yaml
    ├── service-headless.yaml
    ├── NOTES.txt
    └── hooks/
        ├── pre-install-job.yaml
        └── post-install-job.yaml
```

### Key templated values

- **Init (Lab 16)**: `.Values.initContainers.*` — shared file under `/init` on the app container  
- **ServiceMonitor (bonus)**: `.Values.serviceMonitor.*` (Prometheus Operator)  
- **Workload**: `.Values.workload.kind` — `rollout` (Argo Rollouts, Lab 14) or `statefulSet` (Lab 15; `-f values-statefulset.yaml`)
- **Replicas**: `.Values.replicaCount`
- **Resources**: `.Values.resources`
- **Service**: `.Values.service.type`, `.Values.service.port`, `.Values.service.nodePort`
- **Health checks**: `.Values.probes.*` (enabled + timings)
- **Labels/names**: helper templates in `_helpers.tpl`

---

## Task 3 — Multi-Environment Support

- **Dev**: `values-dev.yaml` (1 replica, relaxed resources, NodePort)
- **Prod**: `values-prod.yaml` (5 replicas, bigger resources, LoadBalancer-ready)

Install dev:

```bash
helm install devops-dev k8s/devops-python -f k8s/devops-python/values-dev.yaml
```

Upgrade to prod:

```bash
helm upgrade devops-dev k8s/devops-python -f k8s/devops-python/values-prod.yaml
```

Evidence:

```bash
helm list
helm get values devops-dev
kubectl get rollout,sts,svc,pods
```

---

## Task 4 — Chart Hooks (Pre/Post Install Jobs)

Hooks are implemented as Kubernetes Jobs with annotations:
- `pre-install` job: runs before install
- `post-install` job: runs after install

Hook config lives in `values.yaml` under `hooks.*`.

Verify hook resources:

```bash
helm install --dry-run --debug hooktest k8s/devops-python | sed -n '1,220p'
kubectl get jobs
```

Evidence commands during real install:

```bash
helm install hookrun k8s/devops-python
kubectl get jobs -w
kubectl logs job/$(kubectl get jobs -o name | grep hookrun | head -1 | cut -d/ -f2)
kubectl get jobs
```

Deletion policy is set so successful hooks are deleted (`hook-succeeded`) and old hook jobs are removed before recreation (`before-hook-creation`).

---

## Task 5 — Testing & Validation + Operations

Validate chart:

```bash
helm lint k8s/devops-python
helm template devops k8s/devops-python | head -80
helm install --dry-run --debug devops k8s/devops-python
```

Install / upgrade / rollback / uninstall:

```bash
helm install devops k8s/devops-python
helm upgrade devops k8s/devops-python --set replicaCount=4
helm history devops
helm rollback devops 1
helm uninstall devops
```

App access:

```bash
kubectl get svc
kubectl port-forward service/devops-dev-devops-python 8080:80
curl http://localhost:8080/health
```

---

## Notes

- Health checks are **not** removed; they are configurable via values.
- Avoid putting secrets in values.yaml; use Kubernetes Secrets + Helm values references (Lab 11).

