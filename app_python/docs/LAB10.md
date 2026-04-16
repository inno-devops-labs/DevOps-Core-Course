# LAB10 — Helm Fundamentals (Task 1)

## Evidence
- Helm installation and version (`4.x`) — captured in terminal screenshots.
- Public chart exploration (`helm show chart prometheus-community/prometheus`) — captured in terminal screenshots.

## Helm Value Proposition (Brief)
Helm is a package manager for Kubernetes. It makes deployments reusable and consistent by packaging manifests into charts, moving configuration into values, and simplifying install/upgrade/rollback workflows across environments.

## Task 2 — Helm Chart Creation (Brief)
- Created chart: `k8s/devops-app`.
- Converted Lab 9 manifests into Helm templates:
	- `templates/deployment.yaml`
	- `templates/service.yaml`
- Added reusable labels/naming via helper templates (`templates/_helpers.tpl`).
- Extracted configuration to `values.yaml`:
	- image repository/tag, replica count, resources, service ports/type, probes.
- Kept and parameterized health checks (`livenessProbe` and `readinessProbe`).

## Task 2 Validation
- `helm lint k8s/devops-app` ✅
- `helm template test-release k8s/devops-app` ✅
- `helm install --dry-run --debug test-release k8s/devops-app` ✅
- `helm install myrelease k8s/devops-app` ✅ (installed successfully with an available NodePort override)

## Task 3 — Multi-Environment (Brief)
- Added environment files:
	- `k8s/devops-app/values-dev.yaml`
	- `k8s/devops-app/values-prod.yaml`
- Dev profile:
	- `replicaCount: 1`, relaxed resources, `service.type: NodePort`, `image.tag: latest`.
- Prod profile:
	- `replicaCount: 3`, stronger resources, `service.type: LoadBalancer`, fixed image tag.

## Task 3 Validation
- Installed with dev values:
	- `helm upgrade --install devops-env k8s/devops-app -f k8s/devops-app/values-dev.yaml`
	- Verified: replicas = `1`, service type = `NodePort`.
- Upgraded same release to prod values:
	- `helm upgrade devops-env k8s/devops-app -f k8s/devops-app/values-prod.yaml`
	- Verified: replicas = `3`, service type = `LoadBalancer`.

## Task 4 — Helm Hooks (Brief)
- Implemented hooks:
	- `templates/hooks/pre-install-job.yaml`
	- `templates/hooks/post-install-job.yaml`
- Hook annotations:
	- pre-install: `helm.sh/hook: pre-install`, weight `-5`
	- post-install: `helm.sh/hook: post-install`, weight `5`
	- delete policy: `helm.sh/hook-delete-policy: hook-succeeded`

## Task 4 Validation
- `helm lint k8s/devops-app` ✅
- `helm install --dry-run=client --debug hook-check k8s/devops-app -f k8s/devops-app/values-prod.yaml` ✅
- Fresh install test:
	- `helm install hook-run k8s/devops-app -f k8s/devops-app/values-prod.yaml` ✅
- Verified execution via events:
	- pre-install job completed first
	- post-install job completed after
- Verified deletion policy:
	- `kubectl get jobs | grep hook-run` → no hook jobs found after successful completion.
