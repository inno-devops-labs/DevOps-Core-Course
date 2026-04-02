# Helm charts (LAB10)

## 1. Chart overview

**Layout**

```text
k8s/
  common-lib/              # type: library
    templates/_helpers.tpl
  devops-info-python/
    Chart.yaml             # depends on file://../common-lib
    values.yaml, values-dev.yaml, values-prod.yaml
    templates/deployment.yaml, service.yaml, ingress.yaml, hooks/, NOTES.txt
  devops-info-go/
    Chart.yaml, values*.yaml, templates/deployment.yaml, service.yaml, NOTES.txt
```

**Ideas**

- Defaults live in `values.yaml`; dev/prod overrides in `values-*.yaml`.
- `fullnameOverride` matches LAB09 names (`devops-info-python`, `devops-info-go`) so Services and optional Ingress line up with `k8s/ingress.yml`.

---

## 2. Configuration guide

| Area | Values | Role |
|------|--------|------|
| Image | `image.repository`, `image.tag` | Container image |
| Scale | `replicaCount` | Pod count |
| Service | `service.type`, `service.port`, `service.nodePort` | NodePort `30080` in dev; prod uses `LoadBalancer` (pending on Minikube without `minikube tunnel`) |
| Probes | `livenessProbe`, `readinessProbe` | `/health`, still configurable |
| Hooks | `hooks.preInstall.image`, `hooks.postInstall.image` | Busybox (or similar) for hook Jobs |
| Ingress | `ingress.enabled`, … | Optional; needs TLS secret like LAB09 |

**Typical flow (repo root)**

```bash
helm dependency update k8s/devops-info-python
helm install python-lab10 k8s/devops-info-python -f k8s/devops-info-python/values-dev.yaml
helm upgrade python-lab10 k8s/devops-info-python -f k8s/devops-info-python/values-prod.yaml
```

Enable Ingress only if the controller and TLS secret exist:

```bash
helm upgrade python-lab10 k8s/devops-info-python -f k8s/devops-info-python/values-dev.yaml --set ingress.enabled=true
```

---

## 3. Hook implementation

| Hook | Weight | Delete policy | Note |
|------|--------|---------------|------|
| `pre-install` | `-5` | `hook-succeeded` | Runs before main resources |
| `post-install` | `5` | `hook-succeeded` | Runs after install; Jobs removed after success |

Lower weight runs first. Jobs often disappear quickly—use `kubectl get jobs -w` during `helm install` to capture evidence.

---

## 4. Installation evidence

Screenshots and exact commands are in **`k8s/docs/LAB10.md`**.

---

## 5. Operations

```bash
helm uninstall python-lab10
helm uninstall go-dev
```

```bash
helm history python-lab10
helm rollback python-lab10 <revision>
```

---

## 6. Testing

```bash
helm lint k8s/devops-info-python
helm lint k8s/devops-info-go
helm template lab10-check k8s/devops-info-python -f k8s/devops-info-python/values-dev.yaml
```

**App check**

```bash
kubectl port-forward svc/devops-info-python-service 8080:80
curl -s http://127.0.0.1:8080/health
```

---

## 7. Bonus — library chart

`k8s/common-lib` exposes `common.fullname`, `common.labels`, `common.serviceName`, etc. Both app charts depend on it and run `helm dependency update` before install.

**Why:** one place for label/name rules (DRY), fewer mistakes when both charts evolve together.