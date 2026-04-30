# Lab 14 - Progressive Delivery with Argo Rollouts

## Argo Rollouts Setup

Install the controller:

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
```

Install the kubectl plugin on Linux:

```bash
curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64
chmod +x kubectl-argo-rollouts-linux-amd64
sudo mv kubectl-argo-rollouts-linux-amd64 /usr/local/bin/kubectl-argo-rollouts
```

Verify the plugin and controller:

```
$ kubectl argo rollouts version
kubectl-argo-rollouts: v1.9.0+838d4e7
  BuildDate: 2026-03-20T21:08:11Z
  GitCommit: 838d4e792be666ec11bd0c80331e0c5511b5010e
  GitTreeState: clean
  GoVersion: go1.24.13
  Compiler: gc
  Platform: linux/amd64

$ kubectl get pods -n argo-rollouts
NAME                                      READY   STATUS    RESTARTS   AGE
argo-rollouts-5f64f8d68-wcbdz             1/1     Running   0          20m
argo-rollouts-dashboard-755bbc64c-4zl4t   1/1     Running   0          16m
```

Install and access the dashboard:

```bash
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
```

## Canary Deployment

The canary strategy sends a fraction of traffic to the new version. Dev uses canary by default. The steps in `values.yaml` are:

```yaml
rollout:
  strategy: canary
  canary:
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
```

Traffic starts at 20% to the canary. The first pause has no duration, so it waits for a manual promotion. After promotion it continues through 40%, 60%, and 80% with 30-second pauses. Then it reaches 100% and the rollout completes.

Install with dev values:

```
$ helm install myapp-dev k8s/devops-info-service \
    -f k8s/devops-info-service/values-dev.yaml \
    --set service.nodePort=30083
NAME: myapp-dev
LAST DEPLOYED: Thu Apr 30 22:23:47 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
devops-info-service release myapp-dev.
service type: NodePort
Access: http://<node-ip>:30083
minikube: minikube service myapp-dev-devops-info-service --url
```

Initial rollout is healthy at step 8/8 (100%) since no update happened yet:

```
$ kubectl argo rollouts get rollout myapp-dev-devops-info-service
Name:            myapp-dev-devops-info-service
Namespace:       default
Status:          ✔ Healthy
Strategy:        Canary
  Step:          8/8
  SetWeight:     100
  ActualWeight:  100
Images:          iucapstonead/devops-info-service:latest (stable)
Replicas:
  Desired:       1
  Current:       1
  Updated:       1
  Ready:         1
  Available:     1

NAME                                                       KIND        STATUS     AGE  INFO
⟳ myapp-dev-devops-info-service                            Rollout     ✔ Healthy  26s
└──# revision:1
   └──⧉ myapp-dev-devops-info-service-6d5755b7cd           ReplicaSet  ✔ Healthy  26s  stable
      └──□ myapp-dev-devops-info-service-6d5755b7cd-qbwdr  Pod         ✔ Running  26s  ready:1/1
```

Trigger a new rollout by changing the image tag:

```
$ helm upgrade myapp-dev k8s/devops-info-service \
    -f k8s/devops-info-service/values-dev.yaml \
    --set service.nodePort=30083 --set image.tag=v2
Release "myapp-dev" has been upgraded. Happy Helming!
NAME: myapp-dev
LAST DEPLOYED: Thu Apr 30 22:24:29 2026
NAMESPACE: default
STATUS: deployed
REVISION: 2
```

Rollout is now at step 0/8, paused at 20% weight, waiting for manual promotion:

```
$ kubectl argo rollouts get rollout myapp-dev-devops-info-service
Name:            myapp-dev-devops-info-service
Namespace:       default
Status:          ◌ Progressing
Message:         old replicas are pending termination
Strategy:        Canary
  Step:          0/8
  SetWeight:     20
  ActualWeight:  0
Images:          iucapstonead/devops-info-service:latest (stable)
                 iucapstonead/devops-info-service:v2 (canary)
Replicas:
  Desired:       1
  Current:       2
  Updated:       1
  Ready:         1
  Available:     1

NAME                                                       KIND        STATUS          AGE  INFO
⟳ myapp-dev-devops-info-service                            Rollout     ◌ Progressing   39s
├──# revision:2
│  └──⧉ myapp-dev-devops-info-service-7844d7549c           ReplicaSet  ◌ Progressing   8s   canary
│     └──□ myapp-dev-devops-info-service-7844d7549c-c5xbk  Pod         ⚠ ErrImagePull  8s   ready:0/1
└──# revision:1
   └──⧉ myapp-dev-devops-info-service-6d5755b7cd           ReplicaSet  ✔ Healthy       39s  stable
      └──□ myapp-dev-devops-info-service-6d5755b7cd-qbwdr  Pod         ✔ Running       39s  ready:1/1
```

Abort during the rollout to test rollback:

```
$ kubectl argo rollouts abort myapp-dev-devops-info-service
rollout 'myapp-dev-devops-info-service' aborted
```

After abort the canary is scaled down and all traffic returns to stable:

```
$ kubectl argo rollouts get rollout myapp-dev-devops-info-service
Name:            myapp-dev-devops-info-service
Namespace:       default
Status:          ✖ Degraded
Message:         RolloutAborted: Rollout aborted update to revision 2
Strategy:        Canary
  Step:          0/8
  SetWeight:     0
  ActualWeight:  0
Images:          iucapstonead/devops-info-service:latest (stable)
Replicas:
  Desired:       1
  Current:       1
  Updated:       0
  Ready:         1
  Available:     1

NAME                                                       KIND        STATUS      AGE  INFO
⟳ myapp-dev-devops-info-service                            Rollout     ✖ Degraded  91s
├──# revision:2
│  └──⧉ myapp-dev-devops-info-service-7844d7549c           ReplicaSet  • ScaledDown 60s  canary
└──# revision:1
   └──⧉ myapp-dev-devops-info-service-6d5755b7cd           ReplicaSet  ✔ Healthy   91s  stable
      └──□ myapp-dev-devops-info-service-6d5755b7cd-qbwdr  Pod         ✔ Running   91s  ready:1/1
```

Retry after an abort:

```
$ kubectl argo rollouts retry rollout myapp-dev-devops-info-service
rollout 'myapp-dev-devops-info-service' retried
```

## Blue-Green Deployment

The blue-green strategy runs two full sets of pods: the active version and the preview version. Prod uses blue-green. The active service routes production traffic. The preview service routes to the new version for testing before promotion.

Install with prod values:

```
$ helm install myapp-prod k8s/devops-info-service \
    -f k8s/devops-info-service/values-prod.yaml \
    -n prod --set service.nodePort=30084
NAME: myapp-prod
LAST DEPLOYED: Thu Apr 30 22:26:18 2026
NAMESPACE: prod
STATUS: deployed
REVISION: 1
```

Two services are created. The active service is `myapp-prod-devops-info-service`. The preview service is `myapp-prod-devops-info-service-preview`.

```
$ kubectl get svc -n prod
NAME                                     TYPE       CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
myapp-prod-devops-info-service           NodePort   10.98.164.60     <none>        80:30084/TCP   59s
myapp-prod-devops-info-service-preview   NodePort   10.105.239.60    <none>        80:30388/TCP   59s
python-app-prod-devops-info-service      NodePort   10.110.120.228   <none>        80:30082/TCP   6d23h
```

Initial state - stable and active on the same revision:

```
$ kubectl argo rollouts get rollout myapp-prod-devops-info-service -n prod
Name:            myapp-prod-devops-info-service
Namespace:       prod
Status:          ✔ Healthy
Strategy:        BlueGreen
Images:          iucapstonead/devops-info-service:latest (stable, active)
Replicas:
  Desired:       5
  Current:       5
  Updated:       5
  Ready:         5
  Available:     5

NAME                                                        KIND        STATUS     AGE  INFO
⟳ myapp-prod-devops-info-service                            Rollout     ✔ Healthy  35s
└──# revision:1
   └──⧉ myapp-prod-devops-info-service-79bd8fd757           ReplicaSet  ✔ Healthy  35s  stable,active
      ├──□ myapp-prod-devops-info-service-79bd8fd757-btrbg  Pod         ✔ Running  35s  ready:1/1
      ├──□ myapp-prod-devops-info-service-79bd8fd757-c2mnl  Pod         ✔ Running  35s  ready:1/1
      ├──□ myapp-prod-devops-info-service-79bd8fd757-pm6f9  Pod         ✔ Running  35s  ready:1/1
      ├──□ myapp-prod-devops-info-service-79bd8fd757-vrfnt  Pod         ✔ Running  35s  ready:1/1
      └──□ myapp-prod-devops-info-service-79bd8fd757-zdfkj  Pod         ✔ Running  35s  ready:1/1
```

After triggering a new revision, a preview replica set starts and the active set keeps serving:

```
$ kubectl argo rollouts get rollout myapp-prod-devops-info-service -n prod
Name:            myapp-prod-devops-info-service
Namespace:       prod
Status:          ◌ Progressing
Message:         active service cutover pending
Strategy:        BlueGreen
Images:          iucapstonead/devops-info-service:latest (stable, active)
                 iucapstonead/devops-info-service:v2 (preview)
Replicas:
  Desired:       5
  Current:       15
  Updated:       5
  Ready:         5
  Available:     5

NAME                                                        KIND        STATUS               AGE  INFO
⟳ myapp-prod-devops-info-service                            Rollout     ◌ Progressing        91s
├──# revision:3
│  └──⧉ myapp-prod-devops-info-service-7b5f96dfbd           ReplicaSet  ◌ Progressing        8s   preview
│     ├──□ myapp-prod-devops-info-service-7b5f96dfbd-54psp  Pod         ◌ ContainerCreating  8s   ready:0/1
│     ├──□ myapp-prod-devops-info-service-7b5f96dfbd-5j8jj  Pod         ◌ ContainerCreating  8s   ready:0/1
│     ├──□ myapp-prod-devops-info-service-7b5f96dfbd-6l727  Pod         ◌ ContainerCreating  8s   ready:0/1
│     ├──□ myapp-prod-devops-info-service-7b5f96dfbd-rmpkr  Pod         ◌ ContainerCreating  8s   ready:0/1
│     └──□ myapp-prod-devops-info-service-7b5f96dfbd-sbwgl  Pod         ◌ ContainerCreating  8s   ready:0/1
└──# revision:1
   └──⧉ myapp-prod-devops-info-service-79bd8fd757           ReplicaSet  ✔ Healthy            91s  stable,active
      ├──□ myapp-prod-devops-info-service-79bd8fd757-btrbg  Pod         ✔ Running            91s  ready:1/1
      ├──□ myapp-prod-devops-info-service-79bd8fd757-c2mnl  Pod         ✔ Running            91s  ready:1/1
      ├──□ myapp-prod-devops-info-service-79bd8fd757-pm6f9  Pod         ✔ Running            91s  ready:1/1
      ├──□ myapp-prod-devops-info-service-79bd8fd757-vrfnt  Pod         ✔ Running            91s  ready:1/1
      └──□ myapp-prod-devops-info-service-79bd8fd757-zdfkj  Pod         ✔ Running            91s  ready:1/1
```

Test the preview service before promoting:

```bash
kubectl port-forward svc/myapp-prod-devops-info-service-preview 8081:80 -n prod
curl http://localhost:8081/health
```

Promote when ready:

```
$ kubectl argo rollouts promote myapp-prod-devops-info-service -n prod
rollout 'myapp-prod-devops-info-service' promoted
```

Undo (roll back) after promotion:

```
$ kubectl argo rollouts undo myapp-prod-devops-info-service -n prod
rollout 'myapp-prod-devops-info-service' undo
```

After undo the stable revision stays active and a new preview starts to restore the previous image:

```
$ kubectl argo rollouts get rollout myapp-prod-devops-info-service -n prod
Name:            myapp-prod-devops-info-service
Namespace:       prod
Status:          ◌ Progressing
Message:         active service cutover pending
Strategy:        BlueGreen
Images:          iucapstonead/devops-info-service:latest (stable, active)
                 iucapstonead/devops-info-service:v2 (preview)
Replicas:
  Desired:       5
  Current:       15
  Updated:       5
  Ready:         5
  Available:     5

NAME                                                        KIND        STATUS               AGE   INFO
⟳ myapp-prod-devops-info-service                            Rollout     ◌ Progressing        2m5s
├──# revision:4
│  └──⧉ myapp-prod-devops-info-service-78ccd67c78           ReplicaSet  ◌ Progressing        53s   preview
│     ├──□ myapp-prod-devops-info-service-78ccd67c78-h4vtt  Pod         ◌ ContainerCreating  3s    ready:0/1
│     ├──□ myapp-prod-devops-info-service-78ccd67c78-kgg4m  Pod         ◌ ContainerCreating  3s    ready:0/1
│     ├──□ myapp-prod-devops-info-service-78ccd67c78-pl6gz  Pod         ◌ ContainerCreating  3s    ready:0/1
│     ├──□ myapp-prod-devops-info-service-78ccd67c78-s957m  Pod         ◌ ContainerCreating  3s    ready:0/1
│     └──□ myapp-prod-devops-info-service-78ccd67c78-ts6lv  Pod         ◌ ContainerCreating  3s    ready:0/1
└──# revision:1
   └──⧉ myapp-prod-devops-info-service-79bd8fd757           ReplicaSet  ✔ Healthy            2m5s  stable,active
      ├──□ myapp-prod-devops-info-service-79bd8fd757-btrbg  Pod         ✔ Running            2m5s  ready:1/1
      ├──□ myapp-prod-devops-info-service-79bd8fd757-c2mnl  Pod         ✔ Running            2m5s  ready:1/1
      ├──□ myapp-prod-devops-info-service-79bd8fd757-pm6f9  Pod         ✔ Running            2m5s  ready:1/1
      ├──□ myapp-prod-devops-info-service-79bd8fd757-vrfnt  Pod         ✔ Running            2m5s  ready:1/1
      └──□ myapp-prod-devops-info-service-79bd8fd757-zdfkj  Pod         ✔ Running            2m5s  ready:1/1
```

## Strategy Comparison

Use canary when the change needs gradual validation under real traffic. Canary lets a small percentage of users hit the new version first. If something breaks, only that fraction is affected. It needs more time because of the step-by-step process.

Use blue-green when the switch must be instant and testable before going live. Blue-green requires twice the resources during the transition because both versions run at full replica count. Rollback is immediate by switching the active service selector.

For this service, canary suits dev where quick iteration matters. Blue-green suits prod where instant rollback is needed.

## CLI Commands Reference

Get rollout status:

```bash
kubectl argo rollouts get rollout <name> [-n <namespace>] [-w]
```

List all rollouts:

```
$ kubectl get rollouts
NAME                            DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
myapp-dev-devops-info-service   1         1         1            1           4m44s

$ kubectl get rollouts -n prod
NAME                             DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
myapp-prod-devops-info-service   5         15        5            5           2m11s
```

Promote to next step:

```bash
kubectl argo rollouts promote <name> [-n <namespace>]
```

Abort a rollout:

```bash
kubectl argo rollouts abort <name> [-n <namespace>]
```

Retry after abort:

```bash
kubectl argo rollouts retry rollout <name> [-n <namespace>]
```

Undo (roll back) after promotion:

```bash
kubectl argo rollouts undo <name> [-n <namespace>]
```

Describe a rollout:

```bash
kubectl describe rollout <name> [-n <namespace>]
```
