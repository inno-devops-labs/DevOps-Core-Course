# Lab 14 — Progressive Delivery with Argo Rollouts

## Argo Rollouts Setup

### Installation verification

```bash
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl create namespace argo-rollouts
Error from server (AlreadyExists): namespaces "argo-rollouts" already exists

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
customresourcedefinition.apiextensions.k8s.io/analysisruns.argoproj.io unchanged
customresourcedefinition.apiextensions.k8s.io/analysistemplates.argoproj.io unchanged
customresourcedefinition.apiextensions.k8s.io/clusteranalysistemplates.argoproj.io unchanged
customresourcedefinition.apiextensions.k8s.io/experiments.argoproj.io unchanged
customresourcedefinition.apiextensions.k8s.io/rollouts.argoproj.io unchanged
serviceaccount/argo-rollouts unchanged
clusterrole.rbac.authorization.k8s.io/argo-rollouts unchanged
clusterrole.rbac.authorization.k8s.io/argo-rollouts-aggregate-to-admin unchanged
clusterrole.rbac.authorization.k8s.io/argo-rollouts-aggregate-to-edit unchanged
clusterrole.rbac.authorization.k8s.io/argo-rollouts-aggregate-to-view unchanged
clusterrolebinding.rbac.authorization.k8s.io/argo-rollouts unchanged
configmap/argo-rollouts-config unchanged
secret/argo-rollouts-notification-secret unchanged
service/argo-rollouts-metrics unchanged
deployment.apps/argo-rollouts configured

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
serviceaccount/argo-rollouts-dashboard unchanged
clusterrole.rbac.authorization.k8s.io/argo-rollouts-dashboard unchanged
clusterrolebinding.rbac.authorization.k8s.io/argo-rollouts-dashboard unchanged
service/argo-rollouts-dashboard unchanged
deployment.apps/argo-rollouts-dashboard unchanged

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl get pods -n argo-rollouts
NAME                                      READY   STATUS    RESTARTS       AGE
argo-rollouts-5f64f8d68-q9p7p             1/1     Running   4 (170m ago)   10d
argo-rollouts-dashboard-755bbc64c-pt7rk   1/1     Running   2 (170m ago)   10d

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl argo rollouts version
  kubectl-argo-rollouts: v1.9.0+838d4e7
  BuildDate: 2026-03-20T21:08:11Z
  GitCommit: 838d4e792be666ec11bd0c80331e0c5511b5010e
  GitTreeState: clean
  GoVersion: go1.24.13
  Compiler: gc
  Platform: linux/amd64
```

### Dashboard access

Unfortunately, I can't access the UI. There is an endless loading process. I couldn't solve the problem.

## Canary Deployment

### Strategy configuration explained

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
spec:
  strategy:
    canary:
      steps:
        - setWeight: 20
        - pause: {}
        - setWeight: 40
        - pause: { duration: 30s }
        - setWeight: 60
        - pause: { duration: 30s }
        - setWeight: 80
        - pause: { duration: 30s }
        - setWeight: 100
...
```

### Step-by-step rollout progression

```bash
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl argo rollouts get rollout devops-info-service -n prod
kubectl get rs -n prod --sort-by=.metadata.creationTimestamp
Name:            devops-info-service
Namespace:       prod
Status:          ✔ Healthy
Strategy:        Canary
  Step:          9/9
  SetWeight:     100
  ActualWeight:  100
Images:          chaleshka/devops-info-service:2026.02.11 (stable)
Replicas:
  Desired:       3
  Current:       3
  Updated:       3
  Ready:         3
  Available:     3

NAME                                            KIND        STATUS     AGE  INFO
⟳ devops-info-service                           Rollout     ✔ Healthy  15m  
└──# revision:1                                                             
   └──⧉ devops-info-service-b94fc4795           ReplicaSet  ✔ Healthy  15m  stable
      ├──□ devops-info-service-b94fc4795-9jd2h  Pod         ✔ Running  15m  ready:1/1
      ├──□ devops-info-service-b94fc4795-gtn2n  Pod         ✔ Running  15m  ready:1/1
      └──□ devops-info-service-b94fc4795-kmncw  Pod         ✔ Running  15m  ready:1/1
NAME                            DESIRED   CURRENT   READY   AGE
devops-info-service-b94fc4795   3         3         3       15m
```
Changed configuuration
```bash
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ helm upgrade --install devops-info-service k8s/devops-info-service-chart \
  -n prod --create-namespace -f k8s/devops-info-service-chart/values-prod.yaml
Release "devops-info-service" has been upgraded. Happy Helming!
NAME: devops-info-service
...
Application accessibility verification

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl argo rollouts get rollout devops-info-service -n prod
Name:            devops-info-service
Namespace:       prod
Status:          ॥ Paused
Message:         CanaryPauseStep
Strategy:        Canary
  Step:          1/9
  SetWeight:     20
  ActualWeight:  20
Images:          chaleshka/devops-info-service:2026.02.11 (canary, stable)
Replicas:
  Desired:       5
  Current:       5
  Updated:       1
  Ready:         5
  Available:     5

NAME                                             KIND        STATUS     AGE  INFO
⟳ devops-info-service                            Rollout     ॥ Paused   17m  
├──# revision:2                                                              
│  └──⧉ devops-info-service-6844b5f56b           ReplicaSet  ✔ Healthy  52s  canary
│     └──□ devops-info-service-6844b5f56b-vq74r  Pod         ✔ Running  51s  ready:1/1
└──# revision:1                                                              
   └──⧉ devops-info-service-b94fc4795            ReplicaSet  ✔ Healthy  17m  stable
      ├──□ devops-info-service-b94fc4795-9jd2h   Pod         ✔ Running  17m  ready:1/1
      ├──□ devops-info-service-b94fc4795-gtn2n   Pod         ✔ Running  17m  ready:1/1
      ├──□ devops-info-service-b94fc4795-kmncw   Pod         ✔ Running  17m  ready:1/1
      └──□ devops-info-service-b94fc4795-qj6w8   Pod         ✔ Running  51s  ready:1/1

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl argo rollouts promote devops-info-service -n prod
rollout 'devops-info-service' promoted

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl argo rollouts get rollout devops-info-service -n prod
Name:            devops-info-service
Namespace:       prod
Status:          ◌ Progressing
Message:         more replicas need to be updated
Strategy:        Canary
  Step:          2/9
  SetWeight:     40
  ActualWeight:  25
Images:          chaleshka/devops-info-service:2026.02.11 (canary, stable)
Replicas:
  Desired:       5
  Current:       5
  Updated:       2
  Ready:         4
  Available:     4

NAME                                             KIND        STATUS         AGE    INFO
⟳ devops-info-service                            Rollout     ◌ Progressing  19m    
├──# revision:2                                                                    
│  └──⧉ devops-info-service-6844b5f56b           ReplicaSet  ◌ Progressing  2m46s  canary
│     ├──□ devops-info-service-6844b5f56b-vq74r  Pod         ✔ Running      2m45s  ready:1/1
│     └──□ devops-info-service-6844b5f56b-6d7rs  Pod         ✔ Running      4s     ready:0/1
└──# revision:1                                                                    
   └──⧉ devops-info-service-b94fc4795            ReplicaSet  ✔ Healthy      19m    stable
      ├──□ devops-info-service-b94fc4795-9jd2h   Pod         ✔ Running      19m    ready:1/1
      ├──□ devops-info-service-b94fc4795-gtn2n   Pod         ✔ Running      19m    ready:1/1
      ├──□ devops-info-service-b94fc4795-kmncw   Pod         ✔ Running      19m    ready:1/1
      └──□ devops-info-service-b94fc4795-qj6w8   Pod         ◌ Terminating  2m45s  ready:1/1

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl argo rollouts get rollout devops-info-service -n prod
Name:            devops-info-service
Namespace:       prod
Status:          ॥ Paused
Message:         CanaryPauseStep
Strategy:        Canary
  Step:          3/9
  SetWeight:     40
  ActualWeight:  40
Images:          chaleshka/devops-info-service:2026.02.11 (canary, stable)
Replicas:
  Desired:       5
  Current:       5
  Updated:       2
  Ready:         5
  Available:     5

NAME                                             KIND        STATUS         AGE    INFO
⟳ devops-info-service                            Rollout     ॥ Paused       19m    
├──# revision:2                                                                    
│  └──⧉ devops-info-service-6844b5f56b           ReplicaSet  ✔ Healthy      3m14s  canary
│     ├──□ devops-info-service-6844b5f56b-vq74r  Pod         ✔ Running      3m13s  ready:1/1
│     └──□ devops-info-service-6844b5f56b-6d7rs  Pod         ✔ Running      32s    ready:1/1
└──# revision:1                                                                    
   └──⧉ devops-info-service-b94fc4795            ReplicaSet  ✔ Healthy      19m    stable
      ├──□ devops-info-service-b94fc4795-9jd2h   Pod         ✔ Running      19m    ready:1/1
      ├──□ devops-info-service-b94fc4795-gtn2n   Pod         ✔ Running      19m    ready:1/1
      ├──□ devops-info-service-b94fc4795-kmncw   Pod         ✔ Running      19m    ready:1/1
      └──□ devops-info-service-b94fc4795-qj6w8   Pod         ◌ Terminating  3m13s  ready:1/1

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl argo rollouts promote devops-info-service -n prod
rollout 'devops-info-service' promoted

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl argo rollouts promote devops-info-service -n prod
rollout 'devops-info-service' promoted

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl argo rollouts promote devops-info-service -n prod
rollout 'devops-info-service' promoted

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl argo rollouts get rollout devops-info-service -n prod
Name:            devops-info-service
Namespace:       prod
Status:          ◌ Progressing
Message:         updated replicas are still becoming available
Strategy:        Canary
  Step:          9/9
  SetWeight:     100
  ActualWeight:  100
Images:          chaleshka/devops-info-service:2026.02.11 (canary)
Replicas:
  Desired:       5
  Current:       5
  Updated:       5
  Ready:         4
  Available:     4

NAME                                             KIND        STATUS         AGE    INFO
⟳ devops-info-service                            Rollout     ◌ Progressing  21m    
├──# revision:2                                                                    
│  └──⧉ devops-info-service-6844b5f56b           ReplicaSet  ◌ Progressing  4m46s  canary
│     ├──□ devops-info-service-6844b5f56b-vq74r  Pod         ✔ Running      4m45s  ready:1/1
│     ├──□ devops-info-service-6844b5f56b-6d7rs  Pod         ✔ Running      2m4s   ready:1/1
│     ├──□ devops-info-service-6844b5f56b-7px6w  Pod         ✔ Running      82s    ready:1/1
│     ├──□ devops-info-service-6844b5f56b-clflw  Pod         ✔ Running      38s    ready:1/1
│     └──□ devops-info-service-6844b5f56b-fcchv  Pod         ✔ Running      6s     ready:0/1
└──# revision:1                                                                    
   └──⧉ devops-info-service-b94fc4795            ReplicaSet  • ScaledDown   21m    stable
      └──□ devops-info-service-b94fc4795-gtn2n   Pod         ◌ Terminating  21m    ready:1/1
```

### Promotion and abort demonstration

```bash
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl argo rollouts get rollout devops-info-service -n prod
Name:            devops-info-service
Namespace:       prod
Status:          ✔ Healthy
Strategy:        Canary
  Step:          9/9
  SetWeight:     100
  ActualWeight:  100
Images:          chaleshka/devops-info-service:2026.02.11 (stable)
Replicas:
  Desired:       5
  Current:       5
  Updated:       5
  Ready:         5
  Available:     5

NAME                                             KIND        STATUS        AGE    INFO
⟳ devops-info-service                            Rollout     ✔ Healthy     27m    
├──# revision:2                                                                   
│  └──⧉ devops-info-service-6844b5f56b           ReplicaSet  ✔ Healthy     11m    stable
│     ├──□ devops-info-service-6844b5f56b-vq74r  Pod         ✔ Running     11m    ready:1/1
│     ├──□ devops-info-service-6844b5f56b-6d7rs  Pod         ✔ Running     8m19s  ready:1/1
│     ├──□ devops-info-service-6844b5f56b-7px6w  Pod         ✔ Running     7m37s  ready:1/1
│     ├──□ devops-info-service-6844b5f56b-clflw  Pod         ✔ Running     6m53s  ready:1/1
│     └──□ devops-info-service-6844b5f56b-fcchv  Pod         ✔ Running     6m21s  ready:1/1
└──# revision:1                                                                   
   └──⧉ devops-info-service-b94fc4795            ReplicaSet  • ScaledDown  27m  
```
Changed configuuration
```bash
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ helm upgrade --install devops-info-service k8s/devops-info-service-chart   -n prod --create-namespace -f k8s/devops-info-service-chart/values-prod.yaml

Release "devops-info-service" has been upgraded. Happy Helming!
NAME: devops-info-service
...
Application accessibility verification

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl argo rollouts get rollout devops-info-service -n prod
Name:            devops-info-service
Namespace:       prod
Status:          ॥ Paused
Message:         CanaryPauseStep
Strategy:        Canary
  Step:          1/9
  SetWeight:     20
  ActualWeight:  25
Images:          chaleshka/devops-info-service:2026.02.11 (canary, stable)
Replicas:
  Desired:       3
  Current:       4
  Updated:       1
  Ready:         4
  Available:     4

NAME                                             KIND        STATUS         AGE    INFO
⟳ devops-info-service                            Rollout     ॥ Paused       28m    
├──# revision:3                                                                    
│  └──⧉ devops-info-service-5769f759d5           ReplicaSet  ✔ Healthy      23s    canary
│     └──□ devops-info-service-5769f759d5-b5fwd  Pod         ✔ Running      23s    ready:1/1
├──# revision:2                                                                    
│  └──⧉ devops-info-service-6844b5f56b           ReplicaSet  ✔ Healthy      11m    stable
│     ├──□ devops-info-service-6844b5f56b-vq74r  Pod         ✔ Running      11m    ready:1/1
│     ├──□ devops-info-service-6844b5f56b-6d7rs  Pod         ◌ Terminating  8m52s  ready:1/1
│     ├──□ devops-info-service-6844b5f56b-7px6w  Pod         ✔ Running      8m10s  ready:1/1
│     ├──□ devops-info-service-6844b5f56b-clflw  Pod         ✔ Running      7m26s  ready:1/1
│     └──□ devops-info-service-6844b5f56b-fcchv  Pod         ◌ Terminating  6m54s  ready:1/1
└──# revision:1                                                                    
   └──⧉ devops-info-service-b94fc4795            ReplicaSet  • ScaledDown   28m    

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl argo rollouts abort devops-info-service -n prod
rollout 'devops-info-service' aborted

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl argo rollouts get rollout devops-info-service -n prod
Name:            devops-info-service
Namespace:       prod
Status:          ✖ Degraded
Message:         RolloutAborted: Rollout aborted update to revision 3
Strategy:        Canary
  Step:          0/9
  SetWeight:     0
  ActualWeight:  0
Images:          chaleshka/devops-info-service:2026.02.11 (stable)
Replicas:
  Desired:       3
  Current:       3
  Updated:       0
  Ready:         3
  Available:     3

NAME                                             KIND        STATUS         AGE    INFO
⟳ devops-info-service                            Rollout     ✖ Degraded     28m    
├──# revision:3                                                                    
│  └──⧉ devops-info-service-5769f759d5           ReplicaSet  • ScaledDown   36s    canary
│     └──□ devops-info-service-5769f759d5-b5fwd  Pod         ◌ Terminating  36s    ready:1/1
├──# revision:2                                                                    
│  └──⧉ devops-info-service-6844b5f56b           ReplicaSet  ✔ Healthy      11m    stable
│     ├──□ devops-info-service-6844b5f56b-vq74r  Pod         ✔ Running      11m    ready:1/1
│     ├──□ devops-info-service-6844b5f56b-7px6w  Pod         ✔ Running      8m23s  ready:1/1
│     └──□ devops-info-service-6844b5f56b-clflw  Pod         ✔ Running      7m39s  ready:1/1
└──# revision:1                                                                    
   └──⧉ devops-info-service-b94fc4795            ReplicaSet  • ScaledDown   28m
```

## Blue-Green Deployment

### Strategy configuration explained

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
spec:
  strategy:
    blueGreen:
      activeService: {{ include "devops-info-service.fullname" . }}
      previewService: {{ include "devops-info-service.fullname" . }}-preview
      autoPromotionEnabled: false
...
```

### Preview vs active service

Active service (blue) gets all prod requests. Preview service (green) is using for test new version.

```bash
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl get svc -n prod
NAME                          TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
devops-info-service           ClusterIP   10.102.2.69     <none>        80/TCP    94m
devops-info-service-preview   ClusterIP   10.107.44.116   <none>        80/TCP    94m
```

### Promotion process

After we test our "green" application, we can swap active service:

```bash
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl get svc devops-info-service -n prod -o jsonpath='{.spec.selector.rollouts-pod-template-hash}'; echo
6844b5f56b
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl get svc devops-info-service-preview -n prod -o jsonpath='{.spec.selector.rollouts-pod-template-hash}'; echo
5769f759d5
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl argo rollouts promote devops-info-service -n prod
rollout 'devops-info-service' promoted
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl get svc devops-info-service -n prod -o jsonpath='{.spec.selector.rollouts-pod-template-hash}'; echo
5769f759d5
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl get svc devops-info-service-preview -n prod -o jsonpath='{.spec.selector.rollouts-pod-template-hash}'; echo
5769f759d5
```

## Strategy Comparison

### When to use canary vs blue-green

Use canary when you want a gradual, controlled exposure to production traffic and time to observe behavior. Use blue-green when you need a fast switch with an easy rollback and you can run two versions at once.

### Pros and cons of each

Canary:
- Pros: reduced blast radius, gradual rollout with pauses, good for validating risky changes.
- Cons: longer rollout time, mixed versions in production, needs closer monitoring.

Blue-green:
- Pros: instant cutover, simple rollback, clean separation of old/new versions.
- Cons: needs extra capacity (two ReplicaSets), preview traffic is not real production.

### Your recommendation for different scenarios

For production changes with higher risk or unknown impact, use canary. 
For releases that need a quick switch and easy rollback (or a clean preview environment), use blue-green.

## CLI Commands Reference

### Useful commands you used

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
kubectl get pods -n argo-rollouts
kubectl argo rollouts version

helm upgrade --install devops-info-service k8s/devops-info-service-chart \
  -n prod --create-namespace -f k8s/devops-info-service-chart/values-prod.yaml

kubectl argo rollouts get rollout devops-info-service -n prod
kubectl argo rollouts promote devops-info-service -n prod
kubectl argo rollouts abort devops-info-service -n prod

kubectl get svc -n prod
kubectl get rs -n prod --sort-by=.metadata.creationTimestamp
kubectl get svc devops-info-service -n prod -o jsonpath='{.spec.selector.rollouts-pod-template-hash}'; echo
kubectl get svc devops-info-service-preview -n prod -o jsonpath='{.spec.selector.rollouts-pod-template-hash}'; echo
```
