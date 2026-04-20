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

### 1.3 Dashboard Access

```bash
kubectl argo rollouts dashboard -n dev
```

Open:

```text
http://localhost:3100/rollouts
```

### 1.4 Rollout vs Deployment

A Rollout replaces a standard Deployment when progressive delivery is needed. The pod template, selectors, probes, resources, and container spec remain almost identical, but the resource kind changes from `Deployment` to `Rollout`, and the `strategy` section gains advanced rollout options such as `canary` or `blueGreen`, manual promotion, abort, preview service handling, and controlled rollback.

## 2. Canary Deployment

### 2.1 Helm Changes

Files changed:
- `templates/deployment.yaml` wrapped with `if not .Values.rollout.enabled`
- `templates/rollout.yaml` added
- `templates/service-canary.yaml` added
- `values.yaml` / `values-dev.yaml` updated

### 2.2 Canary Strategy

Dev environment uses canary rollout:

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

### 2.3 Deploy Canary Version

```bash
helm lint k8s/devops-info-service
helm template devops-info-service-dev k8s/devops-info-service -f k8s/devops-info-service/values-dev.yaml
```

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

### 2.4 Trigger a Canary Update

Change the pod template, for example by updating `image.tag` in `values-dev.yaml` or modifying an env var in the chart, commit and push it, then sync again.

```bash
git add .
git commit -m "lab14: trigger canary rollout"
git push
argocd app sync devops-info-service-dev --prune
kubectl argo rollouts get rollout devops-info-service-dev-devops-info-service -n dev -w
```

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
- first pause at 20% requires manual promotion;
- next pauses at 40%, 60%, and 80% continue automatically after 30 seconds each;
- rollout ends at 100%.

### 2.6 Abort / Rollback Test

During the rollout, abort it:

```bash
kubectl argo rollouts abort devops-info-service-dev-devops-info-service -n dev
kubectl argo rollouts get rollout devops-info-service-dev-devops-info-service -n dev -w
```

Optional retry:

```bash
kubectl argo rollouts retry rollout devops-info-service-dev-devops-info-service -n dev
```

![](/k8s/screenshots/after_abort.png)

## 3. Blue-Green Deployment

### 3.1 Helm Changes

Prod environment uses blue-green rollout:
- active service: existing main service
- preview service: `templates/service-preview.yaml`
- strategy defined in `values-prod.yaml`

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

After promotion, trigger another update and abort it, or use undo:

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
