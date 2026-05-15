\# Lab 13 — GitOps with ArgoCD



\## Task 1 — ArgoCD Installation \& Setup



\### Installation via Helm



helm repo add argo https://argoproj.github.io/argo-helm

helm repo update

kubectl create namespace argocd

helm install argocd argo/argo-cd --namespace argocd --set server.service.type=ClusterIP



\### Verification



kubectl get pods -n argocd

NAME                                                READY   STATUS      RESTARTS   AGE

argocd-application-controller-0                     1/1     Running     0          44s

argocd-applicationset-controller-8466bbdf48-49vpl   1/1     Running     0          45s

argocd-dex-server-5b97f65bfd-bznwn                  1/1     Running     0          45s

argocd-notifications-controller-68767c8f58-65t42    1/1     Running     0          45s

argocd-redis-75fb94c8-8t4pp                         1/1     Running     0          45s

argocd-redis-secret-init-7ctqs                      0/1     Completed   0          89s

argocd-repo-server-6c684bd96b-xmzll                 1/1     Running     0          45s

argocd-server-599cd4fb9c-xhwlv                      1/1     Running     0          44s



\### Admin Password



kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

dJKDJpZtaa8Dg2TK



\### Port Forward for UI Access



kubectl port-forward svc/argocd-server -n argocd 8080:443



\### ArgoCD CLI Installation



curl.exe -L -o argocd.exe https://github.com/argoproj/argo-cd/releases/latest/download/argocd-windows-amd64.exe

Move-Item -Path ".\\argocd.exe" -Destination "C:\\tools\\argocd.exe" -Force

$env:Path += ";C:\\tools"

argocd version



\### CLI Login



argocd login localhost:8080 --username admin --password dJKDJpZtaa8Dg2TK --insecure

argocd repo add https://github.com/nadiaa02/DevOps-Core-Course.git --username nadiaa02 --password YOUR\_TOKEN --insecure

argocd repo list



\## Task 2 — Application Deployment



\### Application Manifest (application.yaml)



apiVersion: argoproj.io/v1alpha1

kind: Application

metadata:

&#x20; name: devops-info-service

&#x20; namespace: argocd

spec:

&#x20; project: default

&#x20; source:

&#x20;   repoURL: https://github.com/nadiaa02/DevOps-Core-Course.git

&#x20;   targetRevision: lab13

&#x20;   path: k8s/devops-info-service-chart

&#x20;   helm:

&#x20;     valueFiles:

&#x20;       - values.yaml

&#x20; destination:

&#x20;   server: https://kubernetes.default.svc

&#x20;   namespace: default

&#x20; syncPolicy:

&#x20;   syncOptions:

&#x20;     - CreateNamespace=true



\### Deploy Application



kubectl apply -f k8s\\argocd\\application.yaml

argocd app sync devops-info-service



\### Application Status



argocd app list

NAME                        CLUSTER                         NAMESPACE  PROJECT  STATUS     HEALTH   SYNCPOLICY

argocd/devops-info-service  https://kubernetes.default.svc  default    default  OutOfSync  Healthy  Manual



\## Task 3 — Multi-Environment Deployment



\### Namespaces



kubectl create namespace dev

kubectl create namespace prod



\### Dev Application (application-dev.yaml)



apiVersion: argoproj.io/v1alpha1

kind: Application

metadata:

&#x20; name: devops-info-service-dev

&#x20; namespace: argocd

spec:

&#x20; project: default

&#x20; source:

&#x20;   repoURL: https://github.com/nadiaa02/DevOps-Core-Course.git

&#x20;   targetRevision: lab13

&#x20;   path: k8s/devops-info-service-chart

&#x20;   helm:

&#x20;     valueFiles:

&#x20;       - values.yaml

&#x20;       - values-dev.yaml

&#x20; destination:

&#x20;   server: https://kubernetes.default.svc

&#x20;   namespace: dev

&#x20; syncPolicy:

&#x20;   automated:

&#x20;     prune: true

&#x20;     selfHeal: true

&#x20;   syncOptions:

&#x20;     - CreateNamespace=true



\### Prod Application (application-prod.yaml)



apiVersion: argoproj.io/v1alpha1

kind: Application

metadata:

&#x20; name: devops-info-service-prod

&#x20; namespace: argocd

spec:

&#x20; project: default

&#x20; source:

&#x20;   repoURL: https://github.com/nadiaa02/DevOps-Core-Course.git

&#x20;   targetRevision: lab13

&#x20;   path: k8s/devops-info-service-chart

&#x20;   helm:

&#x20;     valueFiles:

&#x20;       - values.yaml

&#x20;       - values-prod.yaml

&#x20; destination:

&#x20;   server: https://kubernetes.default.svc

&#x20;   namespace: prod

&#x20; syncPolicy:

&#x20;   syncOptions:

&#x20;     - CreateNamespace=true



\### Deploy Both Environments



kubectl apply -f k8s\\argocd\\application-dev.yaml

kubectl apply -f k8s\\argocd\\application-prod.yaml

argocd app sync devops-info-service-dev

argocd app sync devops-info-service-prod



\### Verify Deployments



kubectl get pods -n dev

NAME                                       READY   STATUS    RESTARTS   AGE

devops-info-service-dev-558d5b5b5c-ql5bm   1/1     Running   0          100s



kubectl get pods -n prod

NAME                                        READY   STATUS    RESTARTS   AGE

devops-info-service-prod-6d48775df7-44s6f   1/1     Running   0          66s

devops-info-service-prod-6d48775df7-4d7gv   1/1     Running   0          33s

devops-info-service-prod-6d48775df7-gvppq   1/1     Running   0          99s



\### Environment Configuration Differences



Dev: replicaCount=1, relaxed resources (CPU 100m/Memory 128Mi limits), auto-sync enabled

Prod: replicaCount=3, production resources (CPU 500m/Memory 512Mi limits), manual sync



\## Task 4 — Self-Healing Test



\### Dev Environment (Auto-Sync Enabled)



kubectl scale deployment devops-info-service-dev -n dev --replicas=5

deployment.apps/devops-info-service-dev scaled



kubectl get deployment devops-info-service-dev -n dev

NAME                      READY   UP-TO-DATE   AVAILABLE   AGE

devops-info-service-dev   1/1     1            1           13m



Result: ArgoCD automatically reverted replicas back to 1 (Git state)



\### Prod Environment (Manual Sync)



kubectl scale deployment devops-info-service-prod -n prod --replicas=2

deployment.apps/devops-info-service-prod scaled



kubectl get deployment devops-info-service-prod -n prod

NAME                       READY   UP-TO-DATE   AVAILABLE   AGE

devops-info-service-prod   2/2     2            2           13m



Result: Manual change persisted because auto-sync is disabled for prod



\### ArgoCD Application Status



argocd app list

NAME                             CLUSTER                         NAMESPACE  PROJECT  STATUS     HEALTH       SYNCPOLICY

argocd/devops-info-service       https://kubernetes.default.svc  default    default  OutOfSync  Healthy      Manual

argocd/devops-info-service-dev   https://kubernetes.default.svc  dev        default  Synced     Healthy      Auto-Prune

argocd/devops-info-service-prod  https://kubernetes.default.svc  prod       default  Synced     Progressing  Manual



\## GitOps Principles Demonstrated



1\. Git as Single Source of Truth: All configurations stored in GitHub repository

2\. Declarative Configuration: Helm charts define desired state

3\. Continuous Sync: ArgoCD ensures cluster matches Git state

4\. Drift Detection: Manual changes detected and reverted (auto-sync) or flagged (manual)

5\. Multi-Environment: Dev (auto-sync) vs Prod (manual) with different configs



\## Sync Policies



\- Dev: Automated sync with prune and selfHeal for fast iteration

\- Prod: Manual sync requiring explicit approval for production changes



\## Conclusion



Lab 13 completed with:

\- ArgoCD installed and accessible via UI and CLI

\- Application deployed from Git repository

\- Multi-environment deployment (dev/prod) with different configurations

\- Self-healing demonstrated in dev environment

\- Manual sync policy for production environment

\- GitOps workflow proven with drift detection and correction

