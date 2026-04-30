# Documentation

## Argo Rollouts Setup

### Installation verification

```bash
fountainer@Veronicas-MacBook-Air DevOps-Core-Course % kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
customresourcedefinition.apiextensions.k8s.io/analysisruns.argoproj.io created
customresourcedefinition.apiextensions.k8s.io/analysistemplates.argoproj.io created
customresourcedefinition.apiextensions.k8s.io/clusteranalysistemplates.argoproj.io created
customresourcedefinition.apiextensions.k8s.io/experiments.argoproj.io created
customresourcedefinition.apiextensions.k8s.io/rollouts.argoproj.io created
serviceaccount/argo-rollouts created
clusterrole.rbac.authorization.k8s.io/argo-rollouts created
clusterrole.rbac.authorization.k8s.io/argo-rollouts-aggregate-to-admin created
clusterrole.rbac.authorization.k8s.io/argo-rollouts-aggregate-to-edit created
clusterrole.rbac.authorization.k8s.io/argo-rollouts-aggregate-to-view created
clusterrolebinding.rbac.authorization.k8s.io/argo-rollouts created
configmap/argo-rollouts-config created
secret/argo-rollouts-notification-secret created
service/argo-rollouts-metrics created
deployment.apps/argo-rollouts created
fountainer@Veronicas-MacBook-Air DevOps-Core-Course % kubectl get pods -n argo-rollouts
NAME                            READY   STATUS    RESTARTS   AGE
argo-rollouts-5f64f8d68-zxx5z   1/1     Running   0          54s
```
```bash
==> Fetching downloads for: kubectl-argo-rollouts
✔︎ Formula kubectl-argo-rollouts (v1.8.3)                                                                                    Verified    130.1MB/130.1MB
==> Installing kubectl-argo-rollouts from argoproj/tap
```

```bash
fountainer@Veronicas-MacBook-Air DevOps-Core-Course % kubectl argo rollouts version
kubectl-argo-rollouts: v1.8.3+49fa151
  BuildDate: 2025-06-04T22:19:21Z
  GitCommit: 49fa1516cf71672b69e265267da4e1d16e1fe114
  GitTreeState: clean
  GoVersion: go1.23.9
  Compiler: gc
  Platform: darwin/amd64
```

### Dashboard access

```bash
fountainer@Veronicas-MacBook-Air DevOps-Core-Course % kubectl get pods -n argo-rollouts
NAME                                      READY   STATUS    RESTARTS   AGE
argo-rollouts-5f64f8d68-zxx5z             1/1     Running   0          12m
argo-rollouts-dashboard-755bbc64c-pnkl6   1/1     Running   0          28s
```

![](./../docs/screenshots/lab14-shots/argo-dashboard-access.png)

### Understand Rollout vs Deployment

Rollout CRD vs Deployment

- Rollout and Deployment are kinda similar and both have replicas, selector, template, strategy fields, they manage pod creation. But rollout has additional fields for strategy that allow to perform more controllable rollouts with specific configurations, like rolling an update for a group of users, not for all. 

Additional fields for progressive delivery

- canary: allows gradual traffic shifting to a new version using steps (e.g., setWeight, pause)
- blueGreen: supports switching between old and new versions using separate services
- steps: defines staged rollout progression
- analysis: integrates automated checks (metrics, tests) during rollout
- pause: enables manual or timed pauses between steps
- trafficRouting: controls how traffic is split between versions (with ingress/service mesh)


## Canary Deployment

### Strategy configuration explained

### Step-by-step rollout progression (screenshots from dashboard)

### Promotion and abort demonstration

## Blue-Green Deployment

### Strategy configuration explained

### Preview vs active service

### Promotion process

## Strategy Comparison

### When to use canary vs blue-green

### Pros and cons of each

### Your recommendation for different scenarios

## CLI Commands Reference

### Useful commands you used

### Monitoring and troubleshooting

