Lab 14 — Progressive Delivery with Argo Rollouts



Task 1 — Argo Rollouts Fundamentals



Installation

kubectl create namespace argo-rollouts

kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml



Verification

kubectl get pods -n argo-rollouts

NAME READY STATUS RESTARTS AGE

argo-rollouts-5f64f8d68-lmtk5 1/1 Running 0 3m40s

argo-rollouts-dashboard-755bbc64c-sqps2 1/1 Running 0 59s



Dashboard Access

kubectl port-forward -n argo-rollouts svc/argo-rollouts-dashboard 8080:3100



Dashboard available at: http://localhost:8080



Rollout vs Deployment

Rollout CRD extends Deployment with:



Canary and Blue-Green strategies



Traffic shifting and weighted routing



Pause and resume capabilities



Automatic rollback based on metrics



Analysis and experimentation



Task 2 — Canary Deployment



Canary Strategy Configuration

yaml

strategy:

&#x20; canary:

&#x20;   steps:

&#x20;   - setWeight: 20

&#x20;   - pause: {}

&#x20;   - setWeight: 40

&#x20;   - pause: {duration: 30}

&#x20;   - setWeight: 60

&#x20;   - pause: {duration: 30}

&#x20;   - setWeight: 80

&#x20;   - pause: {duration: 30}

&#x20;   - setWeight: 100

Rollout Creation

helm install devops-info-service . -f values-dev.yaml

kubectl get rollout -n default

NAME DESIRED CURRENT UP-TO-DATE AVAILABLE AGE

devops-info-service 1 1 1 1 43s



Canary Update Test

helm upgrade devops-info-service . -f values-dev.yaml --set image.tag=lab12

kubectl get rollout devops-info-service -n default -w

NAME DESIRED CURRENT UP-TO-DATE AVAILABLE AGE

devops-info-service 1 2 1 2 43s

devops-info-service 1 2 1 2 53s

devops-info-service 1 1 1 1 83s



Rollout Progress

kubectl get rollout devops-info-service -n default

NAME DESIRED CURRENT UP-TO-DATE AVAILABLE AGE

devops-info-service 1 1 1 1 104s



Pods After Canary Update

kubectl get pods | findstr devops-info-service

devops-info-service-564c5cc986-2p6pg 1/1 Running 0 102s

devops-info-service-7646d97b44-qq6t8 1/1 Running 0 103s



Task 3 — Blue-Green Deployment



Blue-Green Strategy Configuration

yaml

strategy:

&#x20; blueGreen:

&#x20;   activeService: devops-info-service-active

&#x20;   previewService: devops-info-service-preview

&#x20;   autoPromotionEnabled: true

&#x20;   autoPromotionSeconds: 30

Services for Blue-Green

kubectl get svc | findstr "active|preview"

devops-info-service-active NodePort 10.105.110.62 <none> 80:31503/TCP

devops-info-service-preview NodePort 10.106.18.8 <none> 80:31414/TCP



Blue-Green Rollout Creation

kubectl get rollout -n default

NAME DESIRED CURRENT UP-TO-DATE AVAILABLE AGE

devops-info-service 1 1 1 1 12m

devops-info-service-bluegreen 1 1 1 6s



Blue-Green Update Test

helm upgrade devops-info-service . -f values-dev.yaml --set image.tag=lab12

kubectl get rollout devops-info-service-bluegreen -n default -w

NAME DESIRED CURRENT UP-TO-DATE AVAILABLE AGE

devops-info-service-bluegreen 1 2 1 1 73s

devops-info-service-bluegreen 1 2 1 1 77s

devops-info-service-bluegreen 1 1 1 1 107s



Blue-Green Rollout Status

kubectl get rollout devops-info-service-bluegreen -n default

NAME DESIRED CURRENT UP-TO-DATE AVAILABLE AGE

devops-info-service-bluegreen 1 1 1 1 2m13s



Pods After Blue-Green Update

kubectl get pods | findstr bluegreen

devops-info-service-bluegreen-564c5cc986-kmxk6 1/1 Running 0 86s

devops-info-service-bluegreen-5db979d869-gt7x7 1/1 Terminating 0 2m6s



Task 4 — Strategy Comparison



Canary Strategy

Pros:



Gradual traffic shifting reduces risk



Real production traffic validation



Can rollback at any step



Metrics-based decisions possible



Cons:



Takes longer to complete



Requires ingress/load balancer for traffic splitting



More complex configuration



Best for:



Web applications with high traffic



When you need real-world validation



Critical systems requiring gradual rollout



Blue-Green Strategy

Pros:



Instant switch between versions



Full environment for testing



Immediate rollback capability



Simpler traffic management



Cons:



Requires double resources during update



Preview environment may need production-like data



Switch can be abrupt



Best for:



API services



Database schema changes



When you can accept double resource usage



Need quick rollback



Rollout Events

kubectl describe rollout devops-info-service-bluegreen -n default

Events:

RolloutAddedToInformer Rollout resource added to informer

RolloutUpdated Rollout updated to revision 1

NewReplicaSetCreated Created ReplicaSet

SwitchService Switched selector for service

ScalingReplicaSet Scaled up ReplicaSet

RolloutCompleted Rollout completed update



Commands Reference

Get rollouts: kubectl get rollout -n default

Describe rollout: kubectl describe rollout <name> -n default

Watch rollout: kubectl get rollout <name> -n default -w

Get rollout YAML: kubectl get rollout <name> -n default -o yaml

List pods: kubectl get pods | findstr <name>

View services: kubectl get svc | findstr "active|preview"



Conclusion

Lab 14 completed with:



Argo Rollouts controller installed and running



Canary strategy with multi-step traffic shifting



Blue-green strategy with active/preview services



Successful progressive delivery updates



Understanding of when to use each strategy

