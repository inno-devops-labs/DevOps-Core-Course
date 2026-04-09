# Lab 11 Secret Management (Zavadskii Peter)

# Kubernetes Secrets (Task 1)

Secrets creation
```bash
abraham_barrett@Abrahams-Air Documents % kubectl create secret generic app-credentials \
  --from-literal=username=admin \
  --from-literal=password=secret123
secret/app-credentials created
abraham_barrett@Abrahams-Air Documents % kubectl get secret app-credentials -o yaml
apiVersion: v1
data:
  password: c2VjcmV0MTIz
  username: YWRtaW4=
kind: Secret
metadata:
  creationTimestamp: "2026-04-07T10:58:29Z"
  name: app-credentials
  namespace: default
  resourceVersion: "556"
  uid: b9eac8d2-fdce-450b-af38-cf93ffaf7d4b
type: Opaque
abraham_barrett@Abrahams-Air Documents % echo YWRtaW4= | base64 -d
admin%                        
```
Kubernetes Secrets are not encrypted at rest by default. They are only base64-encoded, which means they can be easily decoded if someone has access.

etcd encryption is a feature that encrypts Secrets before storing them in etcd (the Kubernetes database). It should be enabled in production environments to protect sensitive data from unauthorized access.

# Helm secret integration (Task 2)

To inject secrets as Environment variables I use 

```yaml
      envFrom:
            - secretRef:
                name: {{ include "devops-service.name" . }}-secret

```

After that I need to update the application version, which gives me an opportunity to obtain secrets from env
```bash
abraham_barrett@Abrahams-Air DevOps-Core-Course % helm upgrade --install dev k8s/devops-info-service 
Release "dev" has been upgraded. Happy Helming!
NAME: dev
LAST DEPLOYED: Wed Apr  8 23:26:54 2026
NAMESPACE: default
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
TEST SUITE: None
abraham_barrett@Abrahams-Air DevOps-Core-Course % kubectl get pods
NAME                             READY   STATUS    RESTARTS   AGE
devops-service-9db94f5b6-bt2fb   1/1     Running   0          33h
devops-service-9db94f5b6-rs9pr   1/1     Running   0          33h
devops-service-9db94f5b6-vx2vq   1/1     Running   0          33h
abraham_barrett@Abrahams-Air DevOps-Core-Course % kubectl exec -it devops-service-9db94f5b6-bt2fb  -- env | grep username
username=admin

```

These secrets are not visible 


```bash
abraham_barrett@Abrahams-Air DevOps-Core-Course % kubectl describe pod devops-service-9db94f5b6-b8g9s
Name:             devops-service-9db94f5b6-b8g9s
Namespace:        default
Priority:         0
Service Account:  default
Node:             minikube/192.168.49.2
Start Time:       Wed, 08 Apr 2026 23:38:20 +0300
Labels:           app=devops-service
                  pod-template-hash=9db94f5b6
Annotations:      <none>
Status:           Running
IP:               10.244.0.12
IPs:
  IP:           10.244.0.12
Controlled By:  ReplicaSet/devops-service-9db94f5b6
Containers:
  app:
    Container ID:   docker://429ea189644ee90618d0cd36d998a3de4a83556f5392326c29a0f85476c0e4af
    Image:          abrahambarrett228/lab02:latest
    Image ID:       docker-pullable://abrahambarrett228/lab02@sha256:ff4a7b2b082f8fa68caa395f865e938ed30671d377439092b6ecefe3b2873007
    Port:           5000/TCP
    Host Port:      0/TCP
    State:          Running
      Started:      Wed, 08 Apr 2026 23:38:20 +0300
    Ready:          True
    Restart Count:  0
    Limits:
      cpu:     200m
      memory:  256Mi
    Requests:
      cpu:      100m
      memory:   128Mi
    Liveness:   http-get http://:5000/health delay=10s timeout=1s period=10s #success=1 #failure=3
    Readiness:  http-get http://:5000/health delay=5s timeout=1s period=5s #success=1 #failure=3
    Environment Variables from:
      devops-service-secret  Secret  Optional: false
    Environment:
      HOST:  0.0.0.0
      PORT:  5000
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-flbqr (ro)
Conditions:
  Type                        Status
  PodReadyToStartContainers   True 
  Initialized                 True 
  Ready                       True 
  ContainersReady             True 
  PodScheduled                True 
Volumes:
  kube-api-access-flbqr:
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

CPU and memory configuration is defined in the resources section of ```values.yaml```, with environment-specific overrides in ```values-dev.yaml``` and ```values-prod.yaml``` to adjust resource usage for development and production. Requests determine how the scheduler places pods by ensuring enough available resources on a node and also define minimum guaranteed resources, while limits act as a hard cap where CPU can be throttled and exceeding memory results in an OOM kill. Resource values should be chosen based on actual usage (e.g., using kubectl top pod), leaving some headroom for spikes and aligning with performance requirements. Typically, development environments use lower values, while production sets requests near average usage and limits above peak. In this chart, defaults are set to ```100m``` CPU and ```128Mi``` memory for requests, and ```200m``` CPU and ```256Mi``` memory for limits.


# HashiCorp Vault integration (Task 3)

Adding vault repo
```bash
abraham_barrett@Abrahams-Air Documents % helm repo add hashicorp https://helm.releases.hashicorp.com
"hashicorp" has been added to your repositories
abraham_barrett@Abrahams-Air Documents % helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "hashicorp" chart repository
...Successfully got an update from the "prometheus-community" chart repository
Update Complete. ⎈Happy Helming!⎈
```

After that install vault and check that everything runs successfully
```bash
abraham_barrett@Abrahams-Air DevOps-Core-Course % helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"
NAME: vault
LAST DEPLOYED: Wed Apr  8 23:27:42 2026
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
abraham_barrett@Abrahams-Air DevOps-Core-Course % kubectl get pods
NAME                                    READY   STATUS              RESTARTS   AGE
devops-service-9db94f5b6-bt2fb          1/1     Running             0          33h
devops-service-9db94f5b6-rs9pr          1/1     Running             0          33h
devops-service-9db94f5b6-vx2vq          1/1     Running             0          33h
vault-0                                 0/1     ContainerCreating   0          16s
vault-agent-injector-848dd747d7-8wx2b   1/1     Running             0          17s

```

Add vault secret using terminal
```bash
abraham_barrett@Abrahams-Air DevOps-Core-Course % kubectl exec -it vault-0 -- /bin/sh
/ $ vault kv put secret/myapp/config \
>   username="admin" \
>   password="vault-secret"
====== Secret Path ======
secret/data/myapp/config

======= Metadata =======
Key                Value
---                -----
created_time       2026-04-08T20:28:46.106628085Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            1
/ $ vault auth enable kubernetes
Success! Enabled kubernetes auth method at: kubernetes/
/ $ vault policy write myapp-policy - <<EOF
> path "secret/data/myapp/config" {
>   capabilities = ["read"]
> }
> EOF
Success! Uploaded policy: myapp-policy
/ $ vault write auth/kubernetes/role/myapp-role \
>   bound_service_account_names=default \
>   bound_service_account_namespaces=default \
>   policies=myapp-policy \
>   ttl=1h
WARNING! The following warnings were returned from Vault:

  * Role myapp-role does not have an audience configured. While audiences are
  not required, consider specifying one if your use case would benefit from
  additional JWT claim verification.

```

Check that everything was added successfully
```bash
abraham_barrett@Abrahams-Air DevOps-Core-Course % kubectl exec -it  devops-service-9db94f5b6-b8g9s  -- ls /vault/secrets
config
```

Important fact : to connect vault to my application, I need to include such annotations in my deployment yaml 

```yaml
 annotations:
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: "myapp-role"
        vault.hashicorp.com/agent-inject-secret-config: "secret/data/myapp/config"
```

### sidecar injection pattern

The sidecar injection pattern adds an additional container (sidecar) to the same pod as the main application. In the case of Vault, the sidecar (Vault Agent) runs alongside the app, retrieves secrets securely from Vault, and writes them to a shared volume (e.g., /vault/secrets). This allows the application to access secrets without embedding credentials in code or environment variables, improving security and enabling dynamic secret updates.

# Security analysis


| Feature                | Kubernetes Secrets                  | HashiCorp Vault                     |
|----------------------|------------------------------------|-------------------------------------|
| Storage              | Stored in etcd                     | External secure storage             |
| Security             | Base64 encoded (not encrypted by default) | Strong encryption by default        |
| Access Control       | RBAC                               | Fine-grained policies               |
| Secret Rotation      | Manual                             | Automatic (built-in support)        |
| Injection Method     | Env vars / volumes                 | Sidecar / agent injection           |
| Audit Logging        | Limited                            | Detailed audit logs                 |
| Complexity           | Simple                             | More complex setup                  |
| Production Use       | Basic use cases                    | Enterprise-grade solution           |


- **Kubernetes Secrets** are simple and easy to use but less secure by default  
- **Vault** provides advanced security, dynamic secrets, and better control for production environments  

## When to Use Each Approach & Production Recommendations

Kubernetes Secrets are suitable for simple applications, development environments, or cases where security requirements are minimal and ease of use is a priority. They integrate natively with Kubernetes and are quick to set up, but require additional configuration (like etcd encryption) to be reasonably secure.

HashiCorp Vault should be used in production or any environment where strong security is required. It is ideal for managing sensitive data, supporting dynamic secrets, automatic rotation, fine-grained access control, and audit logging.

**Recommendation:** Use Kubernetes Secrets for basic or non-critical workloads, but for production systems, prefer Vault combined with Kubernetes for secure, scalable, and centralized secret management.