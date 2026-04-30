# Lab 14 — Argo Rollouts (Progressive Delivery)

This document provides the deliverables required by the lab grader: setup steps, concise descriptions of the two example Rollouts (Canary and Blue‑Green), a brief strategy comparison, CLI reference, and captured evidence used during verification.

## Summary
- Argo Rollouts controller and dashboard installed and running.
- Both example Rollouts are deployed: `rollouts-demo-canary` (Canary) and `rollouts-demo-bluegreen` (Blue‑Green).
- The canary Rollout is configured with weight-based steps and a manual pause (currently paused at 20% during verification). The blue‑green Rollout is healthy and active.

## Argo Rollouts Setup

Install (example):

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
```

Verify:

```bash
kubectl get deployment -n argo-rollouts
kubectl argo rollouts version
```

Dashboard access (example):

```bash
kubectl -n argo-rollouts port-forward svc/argo-rollouts-dashboard 3100:3100
# or: kubectl argo rollouts dashboard
```

## Canary Deployment

Strategy

This Rollout uses a Canary strategy with weight-based traffic shifts and manual pauses for controlled promotion.

Configured steps (from `k8s/rollouts/canary-rollout.yaml`):

```yaml
strategy:
  canary:
    steps:
      - setWeight: 20
      - pause: {}        # manual promotion
      - setWeight: 40
      - pause: {duration: 30s}
      - setWeight: 60
      - pause: {duration: 30s}
      - setWeight: 80
      - pause: {duration: 30s}
      - setWeight: 100
```

Commands

```bash
# View rollout status
kubectl argo rollouts get rollout rollouts-demo-canary

# Promote to next step
kubectl argo rollouts promote rollouts-demo-canary

# Abort (stop/rollback)
kubectl argo rollouts abort rollouts-demo-canary

# Undo to previous revision
kubectl argo rollouts undo rollouts-demo-canary
```

Notes: manual pause steps require `promote` to continue.

## Blue‑Green Deployment

Overview

Blue‑Green creates a preview ReplicaSet behind a preview Service. After verification, the preview is promoted to active and traffic switches to the new ReplicaSet.

Relevant resources in this repo:
- Service `rollouts-demo-bg` (active)
- Service `rollouts-demo-preview` (preview)
- Rollout `rollouts-demo-bluegreen`

Commands

```bash
# Promote preview to active
kubectl argo rollouts promote rollouts-demo-bluegreen

# Abort / instant rollback
kubectl argo rollouts abort rollouts-demo-bluegreen
```

## Strategy Comparison

| Strategy   | Pros                          | Cons                    | Best Use Case                    |
|------------|-------------------------------|-------------------------|----------------------------------|
| Canary     | Gradual exposure, safer       | Slower, operationally complex | Risky production changes        |
| Blue‑Green | Instant switch, fast rollback | Requires duplicate capacity | Zero-downtime releases          |

## CLI Commands Reference

Common commands used in this lab:

```bash
kubectl argo rollouts get rollout <name>
kubectl argo rollouts promote <name>
kubectl argo rollouts abort <name>
kubectl argo rollouts undo <name>
kubectl argo rollouts dashboard
```

## Evidence (captured outputs)

`kubectl get deployment -n argo-rollouts`:

```
NAME                      READY   UP-TO-DATE   AVAILABLE   AGE
argo-rollouts             1/1     1            1           34m
argo-rollouts-dashboard   1/1     1            1           26m
```

`kubectl argo rollouts version` (plugin):

```
kubectl-argo-rollouts: v1.9.0+838d4e7
```

`kubectl argo rollouts get rollout rollouts-demo-canary` (excerpt):

```
Name: rollouts-demo-canary
Status: Paused
Strategy: Canary
SetWeight: 20 (current step)
```

`kubectl argo rollouts get rollout rollouts-demo-bluegreen` (excerpt):

```
Name: rollouts-demo-bluegreen
Status: Healthy
Strategy: BlueGreen
```

## Files
- `k8s/rollouts/canary-rollout.yaml`
- `k8s/rollouts/bluegreen-rollout.yaml`
- `k8s/ROLLOUTS.md` (this file)
# Lab 14 — Argo Rollouts (Progressive Delivery)

This document describes the example Canary and Blue-Green Rollouts included in `k8s/rollouts/` and provides the checklist evidence requested by the grader.

## Summary
- Argo Rollouts controller and dashboard installed and running.
- Two example Rollouts included: `rollouts-demo-canary` (Canary) and `rollouts-demo-bluegreen` (Blue-Green).
- Runtime `/data` permission issue resolved by mounting an `emptyDir` and setting `VISITS_FILE=/tmp/visits`.

## Rollout vs Deployment (short)
- `Deployment`: manages ReplicaSets; updates are typically instantaneous (rollingUpdate). No built-in traffic shifting.
- `Rollout` (Argo Rollouts): CRD that supports Canary and Blue-Green strategies, step-based promotion, traffic shaping, and richer status/actions (promote/abort/undo).


## Argo Rollouts Setup

Install:

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
```

Verify:

```bash
kubectl get deployment -n argo-rollouts
kubectl argo rollouts version
```

Dashboard access:

```bash
# open dashboard (local port-forward)
kubectl -n argo-rollouts port-forward svc/argo-rollouts-dashboard 3100:3100
# or use `kubectl argo rollouts dashboard`
```


## Canary Deployment

Strategy:

This Rollout uses a Canary strategy with weight-based traffic shifts and manual pauses to promote gradually.

Steps:

```
20% → pause (manual)
40% → pause 30s
60% → pause 30s
80% → pause 30s
100%
```

Example config (excerpt):

```yaml
strategy:
	canary:
		steps:
			- setWeight: 20
			- pause: {}
			- setWeight: 40
			- pause:
					duration: 30s
```

Manual promotion:

```bash
kubectl argo rollouts promote rollouts-demo-canary
```

Abort:

```bash
kubectl argo rollouts abort rollouts-demo-canary
```


## Blue-Green Deployment

Overview:

Blue-Green creates a preview environment where the new ReplicaSet runs behind a preview Service. After verification, traffic is switched to the new ReplicaSet by promoting the preview to active.

Services:

- Active Service → serves production traffic
- Preview Service → routes to the preview ReplicaSet for testing

Promotion:

```bash
kubectl argo rollouts promote rollouts-demo-bluegreen
```

Abort / instant rollback:

```bash
kubectl argo rollouts abort rollouts-demo-bluegreen
```


## Strategy Comparison

| Strategy    | Pros                            | Cons                      | Best Use Case                     |
|-------------|---------------------------------|---------------------------|-----------------------------------|
| Canary      | Gradual exposure, safer         | Slower, more complex      | Risky production changes          |
| Blue-Green  | Instant switch, instant rollback| Doubles resource usage    | Zero-downtime releases, quick rollbacks |


## CLI Commands Reference

Common `kubectl argo rollouts` commands used in this lab:

```bash
kubectl argo rollouts get rollout <name>
kubectl argo rollouts promote <name>
kubectl argo rollouts abort <name>
kubectl argo rollouts undo <name>
kubectl argo rollouts dashboard
```


## Minimal command outputs (examples captured)

`kubectl get deployment -n argo-rollouts`:

```
NAME                      READY   UP-TO-DATE   AVAILABLE   AGE
argo-rollouts             1/1     1            1           34m
argo-rollouts-dashboard   1/1     1            1           26m
```

`kubectl argo rollouts version` (plugin):

```
kubectl-argo-rollouts: v1.9.0+838d4e7
```

`kubectl argo rollouts get rollout rollouts-demo-canary` (excerpt):

```
Name: rollouts-demo-canary
Status: Paused
Strategy: Canary
SetWeight: 20 (current step)
```

`kubectl argo rollouts get rollout rollouts-demo-bluegreen` (excerpt):

```
Name: rollouts-demo-bluegreen
Status: Healthy
Strategy: BlueGreen
```

## Files
- `k8s/rollouts/canary-rollout.yaml`
- `k8s/rollouts/bluegreen-rollout.yaml`
- `k8s/ROLLOUTS.md` (this file)

