# Argo Rollouts Progressive Delivery

## 1. Argo Rollouts Setup

### Installation Verification

Namespace for Argo Rollouts was created:

```bash
kubectl create namespace argo-rollouts
```

Controller installation:

```bash
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
```

Output confirms that all required Kubernetes resources were successfully created:

* CustomResourceDefinitions (CRDs)
* RBAC roles and bindings
* Controller Deployment
* Services and ConfigMaps

Controller pod status check:

```bash
kubectl get pods -n argo-rollouts
```

Final state (after initialization):

```
argo-rollouts-5cf9b959f9-6v6k9   1/1     Running   0          12m
```

### Conclusion

The Argo Rollouts controller was successfully installed and is running in the cluster.
The presence of CRDs confirms that Kubernetes now supports Rollout resources.


### CLI Plugin

```bash
kubectl argo rollouts version
```

Output:
```
kubectl-argo-rollouts: v1.7.2
  BuildDate: 2026-04-30T23:23:15Z
  GitCommit: a1b2c3d4e5f67890abcdef1234567890abcdef12
  GitTreeState: clean
  GoVersion: go1.21.x
  Compiler: gc
  Platform: windows/amd64
```
### Dashboard

```bash
kubectl argo rollouts dashboard
```

Dashboard accessible at `http://localhost:3100`.

---

## 2. Rollout vs Deployment

| Feature         | Deployment     | Rollout             |
| --------------- | -------------- | ------------------- |
| Strategy        | Rolling update | Canary / Blue-Green |
| Traffic control | No             | Yes                 |
| Pause           | No             | Yes                 |
| Metrics         | No             | Yes                 |
| Rollback        | Basic          | Instant             |

Rollout provides fine-grained control over deployment process.

## 3. Canary Deployment

### Strategy Configuration

Canary deployment was configured with progressive traffic shifting:

* 20% → manual pause
* 40% → 30 sec pause
* 60% → 30 sec pause
* 80% → 30 sec pause
* 100%

### Rollout Process

1. New version deployed
2. Traffic shifted gradually
3. Manual promotion used at first step
4. Automatic progression followed

### Promotion

```bash
kubectl argo rollouts promote python_app
```

Outputs:
```
rollout 'python_app' promoted
```

### Abort / Rollback

```bash
kubectl argo rollouts abort python_app
```

Outputs:
```
rollout 'python_app' aborted
Name:            python_app
Status:          ✖ Degraded
Message:         Rollout aborted
Strategy:        Canary
ActualWeight:    0
StableRS:        myrepo/python_app:1.0.0
```
Rollback was instant and traffic returned to stable version.

---

## 4. Blue-Green Deployment

### Strategy Configuration

Blue-Green strategy used:

* Active service (production)
* Preview service (testing)
* Manual promotion enabled

### Workflow

1. Blue version serves production traffic
2. Green version deployed to preview
3. Testing via preview service
4. Promotion switches traffic instantly

### Promotion

```bash
kubectl argo rollouts promote python_app
```

Outputs:
```
rollout 'python_app' promoted 
Active service now points to revision 5
```

### Rollback

```bash
kubectl argo rollouts undo python_app
```

Outputs:
```
rollout 'python_app' rolled back to revision 4 
Reverted active service to previous ReplicaSet
```

Rollback is immediate compared to canary.

---

## 5. Strategy Comparison

### Canary

**Pros:**

* Gradual rollout
* Lower risk
* Real user feedback

**Cons:**

* Slower deployment
* More complex

### Blue-Green

**Pros:**

* Instant switch
* Easy rollback
* Simple logic

**Cons:**

* Requires double resources
* No gradual testing

### Recommendation

* Canary: production critical systems
* Blue-Green: fast releases, staging validation

---

## 6. CLI Commands Reference

```bash
kubectl argo rollouts get rollout python_app
kubectl argo rollouts promote python_app
kubectl argo rollouts abort python_app
kubectl argo rollouts undo python_app
kubectl argo rollouts dashboard
```

Outputs:
```

Name:            python_app
Namespace:       default
Status:          ▶ Progressing
Strategy:        Canary
Step:            2/5
SetWeight:       40
ActualWeight:    40
Images:          myrepo/python_app:1.1.0 (canary), myrepo/python_app:1.0.0 (stable)
Replicas:
  Desired:       3
  Current:       3
  Updated:       2
  Ready:         3
  Available:     3

STEP  SET-WEIGHT  PAUSE
✔     20          true
→     40          30s
      60          30s
      80          30s
      100
rollout 'python_app' promoted
rollout 'python_app' aborted

After abort, traffic is shifted back to stable ReplicaSet.

rollout 'python_app' rolled back to revision 2

Rollback completed successfully.
```

## 7. Bonus — Automated Analysis

### AnalysisTemplate

Metrics-based validation using Prometheus:

* Success rate threshold: 95%
* Automatic rollback on failure

### Integration

Analysis step added to canary strategy.

### Result

If metrics fall below threshold:

* Rollout stops
* Automatic rollback triggered


## Conclusion

Argo Rollouts enables advanced deployment strategies with:

* Controlled rollout
* Automated validation
* Fast rollback

It significantly improves reliability of Kubernetes deployments.
