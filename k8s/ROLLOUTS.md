# Lab 14 — Progressive Delivery with Argo Rollouts

## 1. Argo Rollouts Setup

### 1.1 Controller Installation

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl get pods -n argo-rollouts
```

Installation output:

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get pods -n argo-rollouts
NAME                             READY   STATUS    RESTARTS   AGE
argo-rollouts-79b89d8856-tvttj   1/1     Running   0          147m
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get pods -n argo-rollouts                      
NAME                             READY   STATUS    RESTARTS   AGE
argo-rollouts-79b89d8856-tvttj   1/1     Running   0          3h15m
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get svc -n argo-rollouts 
NAME                    TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)    AGE
argo-rollouts-metrics   ClusterIP   10.109.177.179   <none>        8090/TCP   3h15m
PS C:\Users\zagur\DevOps\DevOps-Core-Course> curl http://localhost:3100/rollouts
<!doctype html><html lang="en"><head><base href="/rollouts/" /><title>Argo Rollouts</title><link href="main.css" rel="stylesheet"></head><body><noscript>You need to enable JavaScript to run this app.</noscript><div id="root"></div><script src="main.e4dfa16c55cf932e70bd.js"></script></body></html>
PS C:\Users\zagur\DevOps\DevOps-Core-Course> 
```

The output shows that the controller pod was running successfully in the `argo-rollouts` namespace. This confirms that the Rollout CRD controller was installed and ready to reconcile `Rollout` resources instead of standard `Deployment` resources.

### 1.2 Kubectl Plugin

```powershell
$version = (Invoke-RestMethod https://api.github.com/repos/argoproj/argo-rollouts/releases/latest).tag_name
$url = "https://github.com/argoproj/argo-rollouts/releases/download/" + $version + "/kubectl-argo-rollouts-windows-amd64"
Invoke-WebRequest -Uri $url -OutFile kubectl-argo-rollouts.exe
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl argo rollouts version
kubectl-argo-rollouts: v1.9.0+838d4e7
  BuildDate: 2026-03-20T21:15:27Z
  GitCommit: 838d4e792be666ec11bd0c80331e0c5511b5010e
  GitTreeState: clean
  GoVersion: go1.24.13
  Compiler: gc
  Platform: windows/amd64
```

The plugin was required for observing rollout steps, manually promoting a paused rollout, aborting an update, and checking the revision tree in a readable form.

### 1.3 Dashboard Access

```bash
kubectl argo rollouts dashboard -n dev
```

Open:

```text
http://localhost:3100/rollouts
```

The dashboard was useful for visualizing revision history, paused canary steps, stable vs preview states, and the effect of `promote` / `abort` actions.

### 1.4 Rollout vs Deployment

A `Rollout` replaces a standard `Deployment` when progressive delivery is needed. The pod template, selectors, probes, resources, ConfigMap mounts, Secret usage, and service account remain almost identical. The main change is the resource kind and strategy logic.

Key differences:
- `Deployment` performs a standard rolling update managed only by Kubernetes.
- `Rollout` supports explicit progressive-delivery strategies such as `canary` and `blueGreen`.
- `Rollout` supports manual pauses, promotions, aborts, preview environments, and richer status visualization.
- `Rollout` can work together with existing Services to separate stable, canary, active, and preview traffic.

In this lab, the previous Helm-based `Deployment` was converted into a `Rollout`, while the rest of the application definition stayed mostly unchanged.

---

## 2. Canary Deployment

### 2.1 Helm Changes

Files changed:
- `templates/deployment.yaml` wrapped with `if not .Values.rollout.enabled`
- `templates/rollout.yaml` added
- `templates/service-canary.yaml` added
- `values.yaml` / `values-dev.yaml` updated

This allowed the same Helm chart to support two modes:
- classic `Deployment` when rollouts are disabled;
- `Rollout` when progressive delivery is enabled.

### 2.2 Canary Strategy

The dev environment uses canary rollout:

```yaml
strategy:
  canary:
    maxSurge: 1
    maxUnavailable: 0
    stableService: devops-info-service-dev-devops-info-service
    canaryService: devops-info-service-dev-devops-info-service-canary
    steps:
      - setWeight: 20
      - pause: {}
      - setWeight: 40
      - pause:
          duration: 30s
      - setWeight: 60
      - pause:
          duration: 30s
      - setWeight: 80
      - pause:
          duration: 30s
      - setWeight: 100
```

Explanation of the steps:
- `setWeight: 20` sends the first portion of traffic to the new version.
- `pause: {}` creates an **indefinite pause**. This means the rollout stops and waits for manual approval.
- The next steps move traffic to 40%, 60%, 80%, and finally 100%.
- The later pauses are timed pauses, so the rollout continues automatically after 30 seconds.

This strategy was chosen to demonstrate both manual approval and automatic progression in a single rollout.

### 2.3 Deploy Canary Version

```bash
helm lint k8s/devops-info-service
helm template devops-info-service-dev k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
```

The Helm chart was validated locally before syncing through ArgoCD.

Pushed Helm changes to Git, then synced the ArgoCD dev app:

```bash
argocd app sync devops-info-service-dev --prune
kubectl get rollout -n dev
kubectl argo rollouts get rollout devops-info-service-dev-devops-info-service -n dev -w
```

Output:

```bash
NAME                                                                     KIND        STATUS        AGE    INFO
⟳ devops-info-service-dev-devops-info-service                            Rollout     ✔ Healthy     137m   
├──# revision:2                                                                                           
│  └──⧉ devops-info-service-dev-devops-info-service-76c8fcb6d8           ReplicaSet  ✔ Healthy     90m    stable
│     └──□ devops-info-service-dev-devops-info-service-76c8fcb6d8-q8m2f  Pod         ✔ Running     4m17s  ready:2/2
└──# revision:1                                                                                           
   └──⧉ devops-info-service-dev-devops-info-service-7c5f5d96df           ReplicaSet  • ScaledDown  137m   
Name:            devops-info-service-dev-devops-info-service
Namespace:       dev
Status:          ✔ Healthy
Strategy:        Canary
  Step:          9/9
  SetWeight:     100
  ActualWeight:  100
Images:          devops-info-service:dev_canary (stable)
Replicas:
  Desired:       1
  Current:       1
  Updated:       1
  Ready:         1
  Available:     1

NAME                                                                     KIND        STATUS        AGE    INFO
⟳ devops-info-service-dev-devops-info-service                            Rollout     ✔ Healthy     137m   
├──# revision:2                                                                                           
│  └──⧉ devops-info-service-dev-devops-info-service-76c8fcb6d8           ReplicaSet  ✔ Healthy     90m    stable
│     └──□ devops-info-service-dev-devops-info-service-76c8fcb6d8-q8m2f  Pod         ✔ Running     4m18s  ready:2/2
└──# revision:1                                                                                           
   └──⧉ devops-info-service-dev-devops-info-service-7c5f5d96df           ReplicaSet  • ScaledDown  137m   
PS C:\Users\zagur\DevOps\DevOps-Core-Course> 
```

This output shows a completed rollout where revision 2 became stable and revision 1 was scaled down.

### 2.4 Trigger a Canary Update

A new rollout was triggered by changing the pod template, for example by updating `image.tag` in `values-dev.yaml`.

```bash
git add .
git commit -m "lab14: trigger canary rollout"
git push
argocd app sync devops-info-service-dev --prune
kubectl argo rollouts get rollout devops-info-service-dev-devops-info-service -n dev -w
```

Important observation: a rollout only starts when the pod template changes. Simply re-syncing an unchanged manifest does not create a new revision.

During testing, changing the image tag to a non-existing image produced `ImagePullBackOff`. That was not a Rollouts problem; it was an image availability problem. The issue was fixed by building the new tag locally and loading it into Minikube before re-syncing.

```bash
NAME                                                                     KIND        STATUS        AGE    INFO
⟳ devops-info-service-dev-devops-info-service                            Rollout     ✔ Healthy     137m   
├──# revision:2                                                                                           
│  └──⧉ devops-info-service-dev-devops-info-service-76c8fcb6d8           ReplicaSet  ✔ Healthy     90m    stable
│     └──□ devops-info-service-dev-devops-info-service-76c8fcb6d8-q8m2f  Pod         ✔ Running     4m17s  ready:2/2
└──# revision:1                                                                                           
   └──⧉ devops-info-service-dev-devops-info-service-7c5f5d96df           ReplicaSet  • ScaledDown  137m   
Name:            devops-info-service-dev-devops-info-service
Namespace:       dev
Status:          ✔ Healthy
Strategy:        Canary
  Step:          9/9
  SetWeight:     100
  ActualWeight:  100
Images:          devops-info-service:dev_canary (stable)
Replicas:
  Desired:       1
  Current:       1
  Updated:       1
  Ready:         1
  Available:     1

NAME                                                                     KIND        STATUS        AGE    INFO
⟳ devops-info-service-dev-devops-info-service                            Rollout     ✔ Healthy     137m   
├──# revision:2                                                                                           
│  └──⧉ devops-info-service-dev-devops-info-service-76c8fcb6d8           ReplicaSet  ✔ Healthy     90m    stable
│     └──□ devops-info-service-dev-devops-info-service-76c8fcb6d8-q8m2f  Pod         ✔ Running     4m18s  ready:2/2
└──# revision:1                                                                                           
   └──⧉ devops-info-service-dev-devops-info-service-7c5f5d96df           ReplicaSet  • ScaledDown  137m   
PS C:\Users\zagur\DevOps\DevOps-Core-Course> 
```

### 2.5 Manual Promotion and Automatic Progression

```bash
kubectl argo rollouts promote devops-info-service-dev-devops-info-service -n dev
kubectl argo rollouts get rollout devops-info-service-dev-devops-info-service -n dev -w
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl argo rollouts promote devops-info-service-dev-devops-info-service -n dev
rollout 'devops-info-service-dev-devops-info-service' promoted
```

![](/k8s/screenshots/revision2.png)

![](/k8s/screenshots/canary_v2.png)
![](/k8s/screenshots/promote.png)

Expected behavior:
- the first pause at 20% requires manual promotion;
- the next pauses at 40%, 60%, and 80% continue automatically after 30 seconds each;
- the rollout ends at 100%.

Additional explanation:
- When the dashboard showed **Suspended** with **CanaryPauseStep**, this was expected. The rollout was not broken; it was simply waiting at the manual pause step.
- `pause: {}` means “wait indefinitely until someone approves the rollout.”
- After `promote`, the rollout continued and automatically passed the timed pauses.

A practical detail discovered during testing: with very few replicas, the **actual traffic weight** may not match the configured percentage exactly. Without a traffic manager, Rollouts approximates traffic shifting by scaling pod counts, so small replica counts make 20% / 40% steps less visually precise.

### 2.6 Abort / Rollback Test

During one rollout attempt, the update was aborted:

```bash
kubectl argo rollouts abort devops-info-service-dev-devops-info-service -n dev
kubectl argo rollouts get rollout devops-info-service-dev-devops-info-service -n dev -w
```

Optional retry:

```bash
kubectl argo rollouts retry rollout devops-info-service-dev-devops-info-service -n dev
```

![](/k8s/screenshots/after_abort.png)

Explanation:
- `abort` stops the current rollout and keeps the stable revision serving traffic.
- The failed or unfinished revision stays in history, but it is no longer promoted further.
- This is useful when the new version has an issue, for example an invalid image tag or a functional problem detected during validation.

The abort test demonstrated that canary is well suited for gradual releases because a problematic version can be stopped before it fully replaces the stable one.

---

## 3. Blue-Green Deployment

### 3.1 Helm Changes

The prod environment uses blue-green rollout:
- the active service is the existing main service;
- a preview service is added in `templates/service-preview.yaml`;
- the strategy is defined in `values-prod.yaml`.

This design allows the new version to be deployed separately and tested before switching production traffic.

### 3.2 Blue-Green Strategy

```yaml
strategy:
  blueGreen:
    activeService: devops-info-service-prod-devops-info-service
    previewService: devops-info-service-prod-devops-info-service-preview
    autoPromotionEnabled: false
    previewReplicaCount: 1
    scaleDownDelaySeconds: 30
```

Explanation:
- `activeService` serves current production traffic.
- `previewService` exposes the new version before promotion.
- `autoPromotionEnabled: false` means promotion must be done manually.
- `previewReplicaCount: 1` keeps the preview environment lightweight.
- `scaleDownDelaySeconds: 30` delays removal of the previous version after switching.

### 3.3 Deploy Blue-Green Version

```bash
helm template devops-info-service-prod k8s/devops-info-service -f k8s/devops-info-service/values-prod.yaml
argocd app sync devops-info-service-prod --prune
kubectl get rollout,svc -n prod
kubectl argo rollouts get rollout devops-info-service-prod-devops-info-service -n prod -w
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get rollout,svc -n prod
NAME                                                               DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
rollout.argoproj.io/devops-info-service-prod-devops-info-service   2         2         2            2           127m

NAME                                                           TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service-prod-devops-info-service           LoadBalancer   10.97.149.16    127.0.0.1     80:31960/TCP   3d23h
service/devops-info-service-prod-devops-info-service-preview   ClusterIP      10.108.98.218   <none>        80/TCP         127m
PS C:\Users\zagur\DevOps\DevOps-Core-Course> 
```

```bash
NAME                                                                      KIND        STATUS     AGE    INFO
⟳ devops-info-service-prod-devops-info-service                            Rollout     ✔ Healthy  126m   
└──# revision:1                                                                                         
   └──⧉ devops-info-service-prod-devops-info-service-77c99499c4           ReplicaSet  ✔ Healthy  126m   stable,active
      ├──□ devops-info-service-prod-devops-info-service-77c99499c4-mdxrv  Pod         ✔ Running  114m   ready:2/2
      └──□ devops-info-service-prod-devops-info-service-77c99499c4-52kl8  Pod         ✔ Running  2m32s  ready:2/2
Name:            devops-info-service-prod-devops-info-service
Namespace:       prod
Status:          ✔ Healthy
Strategy:        BlueGreen
Images:          devops-info-service:1.0.0 (stable, active)
Replicas:
  Desired:       2
  Current:       2
  Updated:       2
  Ready:         2
  Available:     2

NAME                                                                      KIND        STATUS     AGE    INFO
⟳ devops-info-service-prod-devops-info-service                            Rollout     ✔ Healthy  127m   
└──# revision:1                                                                                         
   └──⧉ devops-info-service-prod-devops-info-service-77c99499c4           ReplicaSet  ✔ Healthy  127m   stable,active
      ├──□ devops-info-service-prod-devops-info-service-77c99499c4-mdxrv  Pod         ✔ Running  114m   ready:2/2
      └──□ devops-info-service-prod-devops-info-service-77c99499c4-52kl8  Pod         ✔ Running  2m33s  ready:2/2
```

![](/k8s/screenshots/prod1.png)

At this stage only the original stable revision existed. Because there was no new revision yet, both active and preview requests still pointed to the same version. This is expected before a second revision is introduced.

### 3.4 Test Preview vs Active

Port-forward both services:

```bash
kubectl port-forward svc/devops-info-service-prod-devops-info-service -n prod 8082:80
kubectl port-forward svc/devops-info-service-prod-devops-info-service-preview -n prod 8081:80
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl port-forward svc/devops-info-service-prod-devops-info-service -n prod 8082:80
>> 
Forwarding from 127.0.0.1:8082 -> 5000
Forwarding from [::1]:8082 -> 5000
Handling connection for 8082
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl port-forward svc/devops-info-service-prod-devops-info-service -n prod 8082:80
>> 
Forwarding from 127.0.0.1:8082 -> 5000
Forwarding from [::1]:8082 -> 5000
Handling connection for 8082
```

Then compare:

```bash
curl http://localhost:8082/
curl http://localhost:8081/
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> curl http://localhost:8081/          
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"application":{"environment":"prod","log_level":"INFO"},"config":{"config_file":"/config/config.json","loaded":true,"content":{"applicationName":"devops-info-service","environment":"prod","settings":{"featureFlags":{"debugEndpoints":"false","showVisitsInRoot":"true"},"logLevel":"INFO"}}},"persistence":{"visits_file":"/data/visits","visits_count":1},"system":{"hostname":"devops-info-service-prod-devops-info-service-77c99499c4-mdxrv","platform":"Linux","platform_version":"#1 SMP PREEMPT_DYNAMIC Thu Jun  5 18:30:46 UTC 2025","architecture":"x86_64","cpu_count":8,"python_version":"3.13.11"},"runtime":{"uptime_seconds":6808,"uptime_human":"1 hours, 53 minutes","current_time":"2026-04-20T17:29:45.434Z","timezone":"UTC"},"request":{"client_ip":"127.0.0.1","user_agent":"curl/8.18.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"},{"path":"/visits","method":"GET","description":"Current visits counter"},{"path":"/metrics","method":"GET","description":"Prometheus metrics"}]}
PS C:\Users\zagur\DevOps\DevOps-Core-Course> curl http://localhost:8082/
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"application":{"environment":"prod","log_level":"INFO"},"config":{"config_file":"/config/config.json","loaded":true,"content":{"applicationName":"devops-info-service","environment":"prod","settings":{"featureFlags":{"debugEndpoints":"false","showVisitsInRoot":"true"},"logLevel":"INFO"}}},"persistence":{"visits_file":"/data/visits","visits_count":2},"system":{"hostname":"devops-info-service-prod-devops-info-service-77c99499c4-mdxrv","platform":"Linux","platform_version":"#1 SMP PREEMPT_DYNAMIC Thu Jun  5 18:30:46 UTC 2025","architecture":"x86_64","cpu_count":8,"python_version":"3.13.11"},"runtime":{"uptime_seconds":6813,"uptime_human":"1 hours, 53 minutes","current_time":"2026-04-20T17:29:50.694Z","timezone":"UTC"},"request":{"client_ip":"127.0.0.1","user_agent":"curl/8.18.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"},{"path":"/visits","method":"GET","description":"Current visits counter"},{"path":"/metrics","method":"GET","description":"Prometheus metrics"}]}
PS C:\Users\zagur\DevOps\DevOps-Core-Course> 
```

Interpretation:
- both requests returned the same version because, at that moment, the rollout still had only one revision;
- therefore the preview service was available, but it was not yet serving a distinct new version;
- a real blue-green validation happens only after a new revision is created.

### 3.5 Promote Green to Active

```bash
kubectl argo rollouts promote devops-info-service-prod-devops-info-service -n prod
kubectl argo rollouts get rollout devops-info-service-prod-devops-info-service -n prod -w
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl argo rollouts promote devops-info-service-prod-devops-info-service -n prod
>> 
rollout 'devops-info-service-prod-devops-info-service' promoted
``

```bash
NAME                                                                      KIND        STATUS     AGE   INFO
⟳ devops-info-service-prod-devops-info-service                            Rollout     ✔ Healthy  131m  
└──# revision:1                                                                                        
   └──⧉ devops-info-service-prod-devops-info-service-77c99499c4           ReplicaSet  ✔ Healthy  131m  stable,active
      ├──□ devops-info-service-prod-devops-info-service-77c99499c4-mdxrv  Pod         ✔ Running  118m  ready:2/2
      └──□ devops-info-service-prod-devops-info-service-77c99499c4-52kl8  Pod         ✔ Running  7m2s  ready:2/2
Name:            devops-info-service-prod-devops-info-service
Namespace:       prod
Status:          ✔ Healthy
Strategy:        BlueGreen
Images:          devops-info-service:1.0.0 (stable, active)
Replicas:
  Desired:       2
  Current:       2
  Updated:       2
  Ready:         2
  Available:     2

NAME                                                                      KIND        STATUS     AGE   INFO
⟳ devops-info-service-prod-devops-info-service                            Rollout     ✔ Healthy  131m  
└──# revision:1                                                                                        
   └──⧉ devops-info-service-prod-devops-info-service-77c99499c4           ReplicaSet  ✔ Healthy  131m  stable,active
      ├──□ devops-info-service-prod-devops-info-service-77c99499c4-mdxrv  Pod         ✔ Running  118m  ready:2/2
      └──□ devops-info-service-prod-devops-info-service-77c99499c4-52kl8  Pod         ✔ Running  7m2s  ready:2/2
```

### 3.6 Instant Rollback

After updating the prod image tag, a real blue-green paused state appeared:

```bash
kubectl argo rollouts undo devops-info-service-prod-devops-info-service -n prod
kubectl argo rollouts get rollout devops-info-service-prod-devops-info-service -n prod -w
```

```bash
NAME                                                                      KIND        STATUS     AGE   INFO
⟳ devops-info-service-prod-devops-info-service                            Rollout     ॥ Paused   138m  
├──# revision:2                                                                                        
│  └──⧉ devops-info-service-prod-devops-info-service-89f54d898            ReplicaSet  ✔ Healthy  101s  preview
│     └──□ devops-info-service-prod-devops-info-service-89f54d898-qzl2d   Pod         ✔ Running  101s  ready:2/2
└──# revision:1                                                                                        
   └──⧉ devops-info-service-prod-devops-info-service-77c99499c4           ReplicaSet  ✔ Healthy  138m  stable,active
      ├──□ devops-info-service-prod-devops-info-service-77c99499c4-mdxrv  Pod         ✔ Running  126m  ready:2/2
      └──□ devops-info-service-prod-devops-info-service-77c99499c4-52kl8  Pod         ✔ Running  14m   ready:2/2
Name:            devops-info-service-prod-devops-info-service
Namespace:       prod
Status:          ॥ Paused
Message:         BlueGreenPause
Strategy:        BlueGreen
Images:          devops-info-service:1.0.0 (stable, active)
                 devops-info-service:prod_bluegreen (preview)
Replicas:
  Desired:       2
  Current:       3
  Updated:       1
  Ready:         2
  Available:     2
```

![](/k8s/screenshots/blueg.png)

![](/k8s/screenshots/image.png)

This is the important blue-green screenshot for the report. It clearly shows:
- revision 1 remained stable and active;
- revision 2 was deployed as preview;
- the rollout paused before promotion;
- production traffic was still protected from the new version.

## 4. Strategy Comparison

### Canary

Pros:
- gradual exposure to risk
- safer for customer-facing changes
- easier to observe behavior step by step

Cons:
- slower rollout process
- more operational steps
- without a traffic router, percentages are approximated through pod counts

### Blue-Green

Pros:
- instant switch between versions
- easy preview testing before promotion
- rollback is very fast

Cons:
- requires extra resources during preview
- all traffic switches at once on promotion

### Recommendation

- Use **canary** for risky application changes and staged validation.
- Use **blue-green** when preview testing is important and instant rollback is desired.
- For this project, dev is a good fit for canary experimentation, while prod is a good fit for blue-green validation and controlled promotion.

## 5. CLI Commands Reference

```bash
kubectl argo rollouts version
kubectl argo rollouts dashboard -n dev
kubectl argo rollouts list rollouts -n dev
kubectl argo rollouts get rollout <name> -n <namespace> -w
kubectl argo rollouts promote <name> -n <namespace>
kubectl argo rollouts abort <name> -n <namespace>
kubectl argo rollouts retry rollout <name> -n <namespace>
kubectl argo rollouts undo <name> -n <namespace>
```

Useful interpretation of the commands:
- `get rollout -w` shows revision trees and live status changes;
- `promote` continues a paused rollout;
- `abort` stops the current rollout and keeps the stable version;
- `retry rollout` restarts a previously aborted rollout;
- `undo` returns to a previous revision, but only if that revision exists in rollout history.

---

## 6. Conclusion

In this lab, the existing Helm-based application was upgraded from a standard Kubernetes deployment model to progressive delivery with Argo Rollouts.

The dev environment used a **canary strategy** with staged traffic shifting and manual approval at the first pause. This demonstrated how a new version can be introduced gradually and safely. The abort test also showed that a problematic update can be stopped before full rollout.

The prod environment used a **blue-green strategy** with active and preview services. This demonstrated how a new version can be deployed side-by-side with the current production version, validated through a preview endpoint, and only then promoted.

Overall, Argo Rollouts provided a much richer delivery model than a standard Deployment. It made rollout state visible, supported controlled promotion, and gave clear mechanisms for pausing, previewing, and stopping risky updates.
