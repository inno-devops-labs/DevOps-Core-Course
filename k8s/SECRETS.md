# Lab 11 — Kubernetes Secrets & HashiCorp Vault

## Kubernetes Secrets

### Output of creating and viewing your secret

```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl create secret generic app-credentials --from-literal=username=chal --from-literal=password=password_for_DevOps
secret/app-credentials created

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl get secret app-credentials -o yaml
apiVersion: v1
data:
  password: cGFzc3dvcmRfZm9yX0Rldk9wcw==
  username: Y2hhbA==
kind: Secret
metadata:
  creationTimestamp: "2026-04-07T10:51:54Z"
  name: app-credentials
  namespace: default
  resourceVersion: "73594"
  uid: b0b13aea-21ef-4aa9-9bc7-b37a01e78c2a
type: Opaque
```

### Decoded secret values demonstration

```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl get secret app-credentials -o jsonpath='{.data.username}' | base64 -d && echo
chal

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl get secret app-credentials -o jsonpath='{.data.password}' | base64 -d && echo
password_for_DevOps
```

### Explanation of base64 encoding vs encryption

Base64 encoding is a data transformation that can be easily reversed.
Encryption is the transformation of data into a set of bytes that cannot be read without a specific key.

## Helm Secret Integration

### Chart structure showing secrets.yaml

```text
devops-info-service-chart/
├── Chart.yaml
├── values.yaml               # Contains default secret placeholders
├── values-dev.yaml           # Dev overrides (including secret values)
├── values-prod.yaml          # Prod overrides (including secret values)
└── templates/
    ├── _helpers.tpl
    ├── deployment.yaml       # Uses envFrom + secretRef
    ├── service.yaml
    ├── secrets.yaml          # Secret template resource
    ├── NOTES.txt
    └── hooks/
        ├── pre-install-job.yaml
        └── post-install-job.yaml
```

### How secrets are consumed in deployment

The chart creates a Secret from values and injects it into the application pod:

1. `templates/secrets.yaml` creates `{{ include "devops-info-service.fullname" . }}-secret`.
2. `templates/deployment.yaml` uses `envFrom.secretRef` to load all Secret keys into container environment variables.
3. Values are provided via `values.yaml` and overridden via environment-specific values files.

Commands used:

```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ helm lint k8s/devops-info-service-chart
==> Linting k8s/devops-info-service-chart
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ helm template dev-release k8s/devops-info-service-chart -f k8s/devops-info-service-chart/values-dev.yaml
---
# Source: devops-info-service/templates/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: dev-release-devops-info-service-secret
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: dev-release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
type: Opaque
stringData:
  APP_USERNAME: "chal"
  APP_PASSWORD: "password_for_DevOps"
---
# Source: devops-info-service/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: dev-release-devops-info-service
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: dev-release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  type: NodePort
  selector:
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: dev-release
  ports:
    - protocol: TCP
      port: 80
      targetPort: 5000
      nodePort: 30080
---
# Source: devops-info-service/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dev-release-devops-info-service
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: dev-release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: devops-info-service
      app.kubernetes.io/instance: dev-release
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      annotations:
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: "devops-info-role"
        vault.hashicorp.com/agent-inject-secret-config: "secret/data/myapp/config"
      labels:
        app.kubernetes.io/name: devops-info-service
        app.kubernetes.io/instance: dev-release
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
      containers:
        - name: devops-info-service
          image: "chaleshka/devops-info-service:latest"
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 5000
              protocol: TCP
          env:
            - name: HOST
              value: "0.0.0.0"
            - name: PORT
              value: "5000"
          envFrom:
            - secretRef:
                name: dev-release-devops-info-service-secret
          resources:
            limits:
              cpu: 100m
              memory: 128Mi
            requests:
              cpu: 50m
              memory: 64Mi
          livenessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 5
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 5
            periodSeconds: 5
---
# Source: devops-info-service/templates/hooks/post-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "dev-release-devops-info-service-post-install"
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: dev-release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-weight": "5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    metadata:
      labels:
        app.kubernetes.io/name: devops-info-service
        app.kubernetes.io/instance: dev-release
    spec:
      restartPolicy: Never
      containers:
        - name: post-install-smoke
          image: busybox:1.36
          command: ['sh', '-c', 'echo Post-install validation && sleep 10 && echo Validation passed']
---
# Source: devops-info-service/templates/hooks/pre-install-job.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: "dev-release-devops-info-service-pre-install"
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: dev-release
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": hook-succeeded
spec:
  template:
    metadata:
      labels:
        app.kubernetes.io/name: devops-info-service
        app.kubernetes.io/instance: dev-release
    spec:
      restartPolicy: Never
      containers:
        - name: pre-install-check
          image: busybox:1.36
          command: ['sh', '-c', 'echo Pre-install task running && sleep 10 && echo Pre-install completed']

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ helm upgrade --install dev-release k8s/devops-info-service-chart -f k8s/devops-info-service-chart/values-dev.yaml
Release "dev-release" does not exist. Installing it now.
NAME: dev-release
LAST DEPLOYED: Tue Apr  7 14:17:56 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
Thank you for installing devops-info-service.

Release: dev-release
Namespace: default

Your application should expose:
- GET /
- GET /health

Useful commands:
        kubectl get pods -n default
        kubectl get svc -n default
Service type is NodePort.

Access options:
1. Minikube:
         minikube service dev-release-devops-info-service -n default --url

2. Manual NodePort access:
         export NODE_PORT=$(kubectl get svc dev-release-devops-info-service -n default -o jsonpath='{.spec.ports[0].nodePort}')
         export NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
         echo "http://${NODE_IP}:${NODE_PORT}/"
         curl -i "http://${NODE_IP}:${NODE_PORT}/health"

Troubleshooting:
        kubectl describe deployment dev-release-devops-info-service -n default
        kubectl logs -n default deployment/dev-release-devops-info-service



Required Sections:

Chart Overview

Chart structure explanation
Key template files and their purpose
Values organization strategy


Configuration Guide

Important values and their purpose
How to customize for different environments
Example installations with different configurations


Hook Implementation

What hooks you implemented and why
Hook execution order and weights
Deletion policies explanation


Installation Evidence

helm list output
kubectl get all showing deployed resources
Hook execution output (kubectl get jobs, kubectl describe job)
Different environment deployments (dev vs prod)


Operations

Installation commands used
How to upgrade a release
How to rollback
How to uninstall


Testing & Validation

helm lint output
helm template verification
Dry-run output
Application accessibility verification

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl get secret | grep dev-release
dev-release-devops-info-service-secret   Opaque               2      21s
sh.helm.release.v1.dev-release.v1        helm.sh/release.v1   1      34s
```

### Verification output (env vars in pod, excluding actual values)

```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ POD=$(kubectl get pod -l app.kubernetes.io/instance=dev-release -l app.kubernetes.io/name=devops-info-service -o jsonpath='{.items[0].metadata.name}')')

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl exec -it "$POD" -- sh -c 'env | grep APP_'
APP_USERNAME=chal
APP_PASSWORD=password_for_DevOps

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl describe pod "$POD"
Name:             dev-release-devops-info-service-56c646fb5d-r2hpx
Namespace:        default
Priority:         0
Service Account:  default
Node:             minikube/192.168.49.2
Start Time:       Tue, 07 Apr 2026 14:18:11 +0300
Labels:           app.kubernetes.io/instance=dev-release
                  app.kubernetes.io/name=devops-info-service
                  pod-template-hash=56c646fb5d
Annotations:      <none>
Status:           Running
IP:               10.244.0.60
IPs:
  IP:           10.244.0.60
Controlled By:  ReplicaSet/dev-release-devops-info-service-56c646fb5d
Containers:
  devops-info-service:
    Container ID:   docker://ab0077778c365d8126f2940bea39315be65bdd655752d4b6ed59f2d43412896d
    Image:          chaleshka/devops-info-service:latest
    Image ID:       docker-pullable://chaleshka/devops-info-service@sha256:32d83a5d1e952c9a7bd34e2bc44c035a1e3eea613aa1fb04121197217174486d
    Port:           5000/TCP
    Host Port:      0/TCP
    State:          Running
      Started:      Tue, 07 Apr 2026 14:18:12 +0300
    Ready:          True
    Restart Count:  0
    Limits:
      cpu:     100m
      memory:  128Mi
    Requests:
      cpu:      50m
      memory:   64Mi
    Liveness:   http-get http://:5000/health delay=5s timeout=1s period=10s #success=1 #failure=3
    Readiness:  http-get http://:5000/health delay=5s timeout=1s period=5s #success=1 #failure=3
    Environment Variables from:
      dev-release-devops-info-service-secret  Secret  Optional: false
    Environment:
      HOST:  0.0.0.0
      PORT:  5000
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-8jqqz (ro)
Conditions:
  Type                        Status
  PodReadyToStartContainers   True 
  Initialized                 True 
  Ready                       True 
  ContainersReady             True 
  PodScheduled                True 
Volumes:
  kube-api-access-8jqqz:
    Type:                    Projected (a volume that contains injected data from multiple sources)
    TokenExpirationSeconds:  3607
    ConfigMapName:           kube-root-ca.crt
    Optional:                false
    DownwardAPI:             true
QoS Class:                   Burstable
Node-Selectors:              <none>
Tolerations:                 node.kubernetes.io/not-ready:NoExecute op=Exists for 300s
                             node.kubernetes.io/unreachable:NoExecute op=Exists for 300s
Events:                      <none>
```

## Resource Management

### Resource limits configuration

```
# values
resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
    
# values-dev
resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi
    
# values-prod
resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 200m
    memory: 256Mi
```

### Explanation of requests vs limits

`requests` define guaranteed minimum CPU/memory used by the scheduler when placing pods.

`limits` define maximum CPU/memory a container may consume.

### How to choose appropriate values

1. Start with baseline values.
2. Measure average CPU and memory usage under real traffic.
3. Tune queries to approximate typical usage and maintain limits above peak levels.
4. Retest after each update and load profile change.

## Vault Integration

### Vault installation verification (kubectl get pods)

Commands used:

```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ helm repo add hashicorp https://helm.releases.hashicorp.com
"hashicorp" has been added to your repositories

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ helm repo update
Hang tight while we grab the latest from your chart repositories...
...Unable to get an update from the "prometheus-community" chart repository (https://prometheus-community.github.io/helm-charts):
        unexpected EOF
...Successfully got an update from the "hashicorp" chart repository
Error: failed to update the following repositories: [https://prometheus-community.github.io/helm-charts]

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"
level=WARN msg="unable to find exact version; falling back to closest available version" chart=vault requested="" selected=0.32.0
NAME: vault
LAST DEPLOYED: Tue Apr  7 14:21:56 2026
NAMESPACE: default
STATUS: deployed
REVISION: 1
DESCRIPTION: Install complete
NOTES:
Thank you for installing HashiCorp Vault!

Now that you have deployed Vault, you should look over the docs on using
Vault with Kubernetes available here:

https://developer.hashicorp.com/vault/docs


Your release is named vault. To learn more about the release, try:

  $ helm status vault
  $ helm get manifest vault

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl get pods
NAME                                               READY   STATUS    RESTARTS   AGE
dev-release-devops-info-service-56c646fb5d-r2hpx   1/1     Running   0          4m56s
vault-0                                            1/1     Running   0          70s
vault-agent-injector-848dd747d7-8qtlf              1/1     Running   0          70s
```

### Policy and role configuration (sanitized)

Commands used:

```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl exec -it vault-0 -- sh

/ $ vault secrets enable -path=secret kv-v2
Error enabling: Error making API request.

URL: POST http://127.0.0.1:8200/v1/sys/mounts/secret
Code: 400. Errors:

* path is already in use at secret/

/ $ vault kv put secret/myapp/config username="chal" password="vault-password"
====== Secret Path ======
secret/data/myapp/config

======= Metadata =======
Key                Value
---                -----
created_time       2026-04-07T11:27:21.242992137Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            1

/ $ vault auth enable kubernetes
Success! Enabled kubernetes auth method at: kubernetes/

/ $ vault policy write app-policy - <<'EOF'
> path "secret/data/myapp/config" {
> capabilities = ["read"]
> }
> EOF
Success! Uploaded policy: app-policy

/ $ vault write auth/kubernetes/role/devops-info-role \
>   bound_service_account_names=default \
>   bound_service_account_namespaces=default \
>   policies=app-policy \
>   ttl=24h
WARNING! The following warnings were returned from Vault:

  * Role devops-info-role does not have an audience configured. While
  audiences are not required, consider specifying one if your use case would
  benefit from additional JWT 

/ $ vault read auth/kubernetes/role/devops-info-role
Key                                         Value
---                                         -----
alias_name_source                           serviceaccount_uid
bound_service_account_names                 [default]
bound_service_account_namespace_selector    n/a
bound_service_account_namespaces            [default]
policies                                    [app-policy]
token_bound_cidrs                           []
token_explicit_max_ttl                      0s
token_max_ttl                               0s
token_no_default_policy                     false
token_num_uses                              0
token_period                                0s
token_policies                              [app-policy]
token_ttl                                   24h
token_type                                  default
ttl                                         24h

/ $ vault policy read app-policy
path "secret/data/myapp/config" {
capabilities = ["read"]
}
```

### Proof of secret injection (show file exists, path structure)

Commands used:

```
andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ helm upgrade --install dev-release k8s/devops-info-service-chart -f k8s/devops-info-service-chart/values-dev.yaml
Release "dev-release" has been upgraded. Happy Helming!
NAME: dev-release
LAST DEPLOYED: Tue Apr  7 17:39:00 2026
NAMESPACE: default
STATUS: deployed
REVISION: 5
DESCRIPTION: Upgrade complete
TEST SUITE: None
NOTES:
Thank you for installing devops-info-service.

Release: dev-release
Namespace: default

Your application should expose:
- GET /
- GET /health

Useful commands:
        kubectl get pods -n default
        kubectl get svc -n default
Service type is NodePort.

Access options:
1. Minikube:
         minikube service dev-release-devops-info-service -n default --url

2. Manual NodePort access:
         export NODE_PORT=$(kubectl get svc dev-release-devops-info-service -n default -o jsonpath='{.spec.ports[0].nodePort}')
         export NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
         echo "http://${NODE_IP}:${NODE_PORT}/"
         curl -i "http://${NODE_IP}:${NODE_PORT}/health"

Troubleshooting:
        kubectl describe deployment dev-release-devops-info-service -n default
        kubectl logs -n default deployment/dev-release-devops-info-service



Required Sections:

Chart Overview

Chart structure explanation
Key template files and their purpose
Values organization strategy


Configuration Guide

Important values and their purpose
How to customize for different environments
Example installations with different configurations


Hook Implementation

What hooks you implemented and why
Hook execution order and weights
Deletion policies explanation


Installation Evidence

helm list output
kubectl get all showing deployed resources
Hook execution output (kubectl get jobs, kubectl describe job)
Different environment deployments (dev vs prod)


Operations

Installation commands used
How to upgrade a release
How to rollback
How to uninstall


Testing & Validation

helm lint output
helm template verification
Dry-run output
Application accessibility verification

POD=$(kubectl get pod -l app.kubernetes.io/instance=dev-release -l app.kubernetes.io/name=devops-info-service -o jsonpath='{.items[0].metadata.name}')

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl get pod "$POD" -o jsonpath='{.metadata.annotations}' | tr ',' '\n' | grep vault
"vault.hashicorp.com/agent-inject":"true"
"vault.hashicorp.com/agent-inject-secret-config":"secret/data/myapp/config"
"vault.hashicorp.com/agent-inject-status":"injected"
"vault.hashicorp.com/role":"devops-info-role"}

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl get pod "$POD" -o jsonpath='{.spec.containers[*].name}' && echo
devops-info-service vault-agent

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl get pod "$POD" -o jsonpath='{.spec.initContainers[*].name}' && echo
vault-agent-init

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl exec -it "$POD" -- ls -la /vault/secrets
Defaulted container "devops-info-service" out of: devops-info-service, vault-agent, vault-agent-init (init)
total 8
drwxrwxrwt 2 root root      60 Apr  7 14:38 .
drwxr-xr-x 3 root root    4096 Apr  7 14:38 ..
-rw-r--r-- 1  100 appuser  171 Apr  7 14:38 config

andpe@chale:/mnt/g/DevOps/DevOps-Core-Course$ kubectl exec -it "$POD" -- cat /vault/secrets/config
Defaulted container "devops-info-service" out of: devops-info-service, vault-agent, vault-agent-init (init)
data: map[password:vault-password username:chal]
metadata: map[created_time:2026-04-07T11:27:21.242992137Z custom_metadata:<nil> deletion_time: destroyed:false version:1]
```

## Security Analysis

### Comparison: K8s Secrets vs Vault

Kubernetes Secrets:
- Simple and native to Kubernetes.
- Good for basic and low-complexity workloads.
- Limited lifecycle controls unless combined with additional tooling.

Vault:
- Centralized secret management and auditing.
- Fine-grained policies, dynamic credentials, and rotation capabilities.
- Better fit for production systems with strict security requirements.

### When to use each approach

Use Kubernetes Secrets when:
- Environment is simple.
- Secrets are static and low-risk.
- Operational simplicity is priority.

Use Vault when:
- Production workloads require strong governance.
- Secret rotation, audit trails, and policy control are required.ъ

### Production recommendations

- Never store real credentials in Git repositories.
- Use placeholders in values files and inject real secrets at deploy time.
- Prefer dedicated service accounts per workload.
- Use Vault (or equivalent) for critical secrets and rotation workflows.
- Audit secret access regularly and review policy scope.
