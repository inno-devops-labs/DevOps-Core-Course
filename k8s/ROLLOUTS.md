# Lab 14 - Progressive Delivery with Argo Rollouts

This lab replaces the standard Kubernetes Deployment with an Argo Rollout so the app can be released with canary and blue-green strategies.

## 1. Argo Rollouts Fundamentals

### Install the controller

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl get pods -n argo-rollouts
```

### Install the kubectl plugin

Download the `kubectl-argo-rollouts` binary for your platform from the official releases page and place it on `PATH`.

Verify:

```bash
kubectl argo rollouts version
```

### Install the dashboard

```bash
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

Open:

```text
http://localhost:3100
```

### Rollout vs Deployment

- `Deployment` handles rolling updates only
- `Rollout` adds progressive delivery strategy fields
- `Rollout` supports canary steps, blue-green promotion, dashboard visualization, and manual abort/promote actions

## 2. Canary Deployment

### Strategy used

The chart uses a `Rollout` with canary steps:

1. `20%`
2. pause for manual promotion
3. `40%`
4. pause for `30s`
5. `60%`
6. pause for `30s`
7. `80%`
8. pause for `30s`
9. `100%`

The canary configuration is defined in [`k8s/python-app/values.yaml`](./python-app/values.yaml) and can be overridden with [`k8s/python-app/values-canary.yaml`](./python-app/values-canary.yaml).

### Deploy

```bash
helm upgrade --install canary ./k8s/python-app -f k8s/python-app/values-canary.yaml
kubectl argo rollouts get rollout canary-python-app -w
```

### Promote

```bash
kubectl argo rollouts promote canary-python-app
```

### Abort

```bash
kubectl argo rollouts abort canary-python-app
```

### What to capture

- Rollout dashboard showing the canary steps
- `kubectl argo rollouts get rollout ... -w`
- Manual promote and abort output

## 3. Blue-Green Deployment

### Strategy used

Blue-green is enabled with:

- active service: `python-app-bg-python-app-service`
- preview service: `python-app-bg-python-app-preview`
- `autoPromotionEnabled: false`

The blue-green overrides are in [`k8s/python-app/values-bluegreen.yaml`](./python-app/values-bluegreen.yaml).

### Deploy

```bash
helm upgrade --install bluegreen ./k8s/python-app -f k8s/python-app/values-bluegreen.yaml
kubectl argo rollouts get rollout bluegreen-python-app -w
```

### Preview service

```bash
kubectl port-forward svc/bluegreen-python-app-preview 8081:80
```

### Active service

```bash
kubectl port-forward svc/bluegreen-python-app-service 8080:80
```

### Promote

```bash
kubectl argo rollouts promote bluegreen-python-app
```

### Roll back

```bash
kubectl argo rollouts undo bluegreen-python-app
```

## 4. Strategy Comparison

### Canary

- Safer gradual rollout
- Good for validating a new version on a subset of traffic
- Slower than blue-green
- Easier to observe behavior before full rollout

### Blue-Green

- Instant switch between versions
- Great for quick cutover and rollback
- Uses extra resources during the transition
- Best when you want a clean test environment before promotion

### Recommendation

- Use **canary** for risky changes and user-facing services
- Use **blue-green** when you want a fast switch and a very simple rollback path

## 5. Useful CLI Commands

```bash
kubectl argo rollouts list rollout
kubectl argo rollouts get rollout <name> -w
kubectl argo rollouts promote <name>
kubectl argo rollouts abort <name>
kubectl argo rollouts undo <name>
kubectl argo rollouts dashboard
```

## 6. Verification Notes

For the lab submission, capture:

- controller pod status in `argo-rollouts`
- dashboard access
- canary promotion and abort
- blue-green preview and active service access
- screenshots from the dashboard and rollout detail view
