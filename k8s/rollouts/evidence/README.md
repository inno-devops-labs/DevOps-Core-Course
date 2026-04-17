# Lab 14 — Evidence

Captures from the Argo Rollouts controller and dashboard that back
the claims in [`../../ROLLOUTS.md`](../../ROLLOUTS.md).

## Expected files

| File | Source |
|------|--------|
| `rollouts-install.txt` | `kubectl get pods -n argo-rollouts` + `kubectl api-resources --api-group=argoproj.io`. |
| `canary-initial.png` | Dashboard (`http://localhost:3100`) on first install. |
| `canary-paused.png` | Dashboard while rollout sits at step 1/9 (20 %) after `helm upgrade --set image.tag=...`. |
| `canary-progressing.txt` | `kubectl argo rollouts get rollout devops-app -w` across all 9 steps. |
| `canary-abort.png` | Dashboard mid-abort: canary RS scaling down, stable RS restoring replicas. |
| `bluegreen-preview.png` | Dashboard after upgrading in blue-green mode; preview has endpoints on new RS, active unchanged. |
| `bluegreen-promoted.png` | Dashboard immediately after `kubectl argo rollouts promote devops-app`. |
| `bluegreen-undo.png` | Dashboard after `kubectl argo rollouts undo devops-app`. |
| `analysis-failed.png` | Dashboard showing AnalysisRun `Failed` + Rollout `Degraded`. |
| `analysis-failed.txt` | `kubectl describe analysisrun ...` for the failed run. |

## How to reproduce

See [`../../ROLLOUTS.md`](../../ROLLOUTS.md) sections 3, 4 and 7 —
each section ends with exactly the commands used to generate the
corresponding files above.
