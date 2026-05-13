# Argo Rollouts Summary and Documentation

## 1. Argo Rollouts Setup
The Argo Rollouts Controller and its CRDs (Custom Resource Definitions) were installed successfully to the `argo-rollouts` namespace. The Dashboard was simultaneously deployed to help visualize rollout operations in the UI. 

To access the dashboard:
```bash
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

## 2. Canary Deployment

### Strategy Configuration
The Canary strategy handles incremental updates. We configured this in `values-canary.yaml` starting with a safe initial pause step requiring manual confirmation.
- 20% weight -> Pause (Indefinite: requires manual promote)
- 40% weight -> 30s pause
- 60% weight -> 30s pause
- 80% weight -> 30s pause
- 100% active traffic cutover.

### Process Followed & Tested
1. **Initial Deployment**: Rolled out the service successfully using the `canary` helm options.
2. **Update**: Changed the container tags (or updated configurations), causing Argo to shift 20% of traffic to the new replicaset.
3. **Validation & Promotion**: Used `kubectl argo rollouts promote` to resume the delayed deployment, observing the 30-second timers incrementing percentages automatically up to 100%.
4. **Rollback**: Triggered an artificial failure (like a missing image) and used `kubectl argo rollouts abort` to verify that traffic seamlessly and instantaneously transitioned back to the stable replica.

## 3. Blue-Green Deployment

### Strategy Configuration
This strategy sets up parallel identical environments. Configured through `values-bluegreen.yaml`:
- **Active Service**: Matches the live application.
- **Preview Service**: Handles validation/test traffic explicitly on the new environment.
- **Auto Promotion**: Disabled, enforcing manual validation of the new revision before updating the main active service label.

### Process Followed & Tested
1. We deployed the stack with `blueGreen` configurations. 
2. Changes to image tags resulted in new pods being completely spun up onto the `preview` service without any live traffic impact.
3. Upon validating the target state on the `preview` service, a manual `kubectl argo rollouts promote` was issued.
4. Argo cut over the live service to the new pods smoothly.
5. In disaster testing, `kubectl argo rollouts abort` returned routing to the older replicaset almost instantaneously.

## 4. Strategy Comparison

| Feature | Canary | Blue-Green |
|---|---|---|
| **Traffic Shifting** | Gradual routing (percentage-based) | Instant switch (service selector change) |
| **Rollback Capability** | Fast | Instantaneous |
| **Resource Overhead** | Partial (only a fraction of duplicated pods needed) | 2x scaling (exact replica stack sits idle while previewing) | 
| **Best Utility** | Good for catching production impact anomalies securely | Perfect for schema changes or testing fully isolated features before cutover |

**Recommendation:** 
- Use **Canary** for regular daily updates where you want to minimize blast radius and ensure operational stability without doubling hardware resources.
- Use **Blue-Green** for major version overhauls or changes where partial transitions would cause state friction.

## 5. CLI Commands Reference
- `kubectl argo rollouts version` — Validate plugin versions.
- `kubectl argo rollouts status <rollout-name>` — Check ongoing rollout health.
- `kubectl argo rollouts get rollout <rollout-name>` — Get tree topology and weights.
- `kubectl argo rollouts set image <rollout-name> <cnt>=<image>` — Perform an update manually via CLI.
- `kubectl argo rollouts promote <rollout-name>` — Continue a paused rollout state or approve a Blue-Green cutover.
- `kubectl argo rollouts abort <rollout-name>` — Instantly rollback routing to the fully stable subset.
- `kubectl argo rollouts undo <rollout-name>` — Rollback the configuration resource to its previous form.
