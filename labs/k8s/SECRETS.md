# Lab 11

## Kubernetes Secrets

```bash
$ kubectl create secret generic app-credentials --from-literal=username=admin --from-literal=password=supersecret

secret/app-credentials created

$ kubectl get secret app-credentials -o yaml

apiVersion: v1
data:
  password: c3VwZXJzZWNyZXQ=
  username: YWRtaW4=
kind: Secret
metadata:
  creationTimestamp: "2026-04-07T08:44:04Z"
  name: app-credentials
  namespace: default
  resourceVersion: "10180"
  uid: 3bae00f5-5bc8-46e9-811c-d5545579785d
type: Opaque

$ echo "c3VwZXJzZWNyZXQ=" | base64 -d

supersecret
```

- Base64 encoding is just transformation of data, which is easily reversible, while encryption requires key, without which, data is unreadable.


## Helm Secret Integration

### Structure:

```
simple-app-chart/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── secrets.yaml
    ├── deployment.yaml
    └── _helpers.tpl
```
### Secrets consumation:

-`templates/deployment.yaml`
```bash
spec:
  containers:
    - name: {{ .Chart.Name }}
      envFrom:
        - secretRef:
            name: {{ include "simple-app-chart.fullname" . }}-secret
```
This injects all keys from the referenced Secret as environment variables into the container.

### Verification output:

```bash
$ kubectl get secrets

NAME                                       TYPE                 DATA   AGE
app-credentials                            Opaque               2      7m49s
sh.helm.release.v1.simple-app-release.v1   helm.sh/release.v1   1      5d19h

```

(Secrets exist and injected but not written in pods)

```bash

$ kubectl describe pod $POD_NAME | grep -A10 "Environment:"
    Environment:               <none>
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-s5hfj (ro)
Conditions:
  Type                        Status
  PodReadyToStartContainers   True 
  Initialized                 True 
  Ready                       True 
  ContainersReady             True 
  PodScheduled                True 
Volumes:
--
    Environment:               <none>
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-6c5nl (ro)
Conditions:
  Type                        Status
  PodReadyToStartContainers   True 
  Initialized                 True 
  Ready                       True 
  ContainersReady             True 
  PodScheduled                True 
Volumes:
--
    Environment:               <none>
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-l8wjv (ro)
Conditions:
  Type                        Status
  PodReadyToStartContainers   True 
  Initialized                 True 
  Ready                       True 
  ContainersReady             True 
  PodScheduled                True 
Volumes:
--
    Environment:               <none>
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-76k7f (ro)
Conditions:
  Type                        Status
  PodReadyToStartContainers   True 
  Initialized                 True 
  Ready                       True 
  ContainersReady             True 
  PodScheduled                True 
Volumes:
--
    Environment:               <none>
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-2trz8 (ro)
Conditions:
  Type                        Status
  PodReadyToStartContainers   True 
  Initialized                 True 
  Ready                       True 
  ContainersReady             True 
  PodScheduled                True 
Volumes:
```

## Resource Management

-`values.yaml`

```bash
resources:
  requests:
    memory: "64Mi"
    cpu: "100m"
  limits:
    memory: "128Mi"
    cpu: "200m"
```

### Requests vs limits
Requests ensure predictable performance while limits prevent a single pod from starving others.

### Choose appropriate values
Start with realistic estimates based on application testing:

- For a typical web app: cpu: 100-200m, memory: 128-256Mi.

- For batch jobs or data processing: higher requests may be needed.

- Use kubectl top pod and monitoring tools to adjust over time.

## Vault integration

### Entire process proof:

```bash
$ helm install vault . -n vault --create-namespace \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true"

NAME: vault
LAST DEPLOYED: Tue Apr  7 12:28:50 2026
NAMESPACE: vault
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

$ kubectl get pods -n vault

NAME                                   READY   STATUS    RESTARTS   AGE
vault-0                                1/1     Running   0          19s
vault-agent-injector-8c76487db-w54v5   1/1     Running   0          19s

$ kubectl exec -it vault-0 -n vault -- /bin/sh

/ $ vault auth enable kubernetes
Success! Enabled kubernetes auth method at: kubernetes/

/ $ vault write auth/kubernetes/config \
>     kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443"
Success! Data written to: auth/kubernetes/config

/ $ vault policy write myapp-policy - <<EOF
> path "secret/data/myapp/*" {
>     capabilities = ["read"]
> }
> EOF
Success! Uploaded policy: myapp-policy

/ $ vault kv put secret/myapp/config username="db-user" password="secure-password-123"

====== Secret Path ======
secret/data/myapp/config

======= Metadata =======
Key                Value
---                -----
created_time       2026-04-07T09:31:25.575203708Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            1

/ $ vault write auth/kubernetes/role/myapp-role \
>     bound_service_account_names=default \
>     bound_service_account_namespaces=default \
>     policies=myapp-policy \
>     ttl=24h

WARNING! The following warnings were returned from Vault:

  * Role myapp-role does not have an audience configured. While audiences are
  not required, consider specifying one if your use case would benefit from
  additional JWT claim verification.

/ $ exit

$ helm upgrade myapp ./simple-app-chart

Release "myapp" has been upgraded. Happy Helming!
NAME: myapp
LAST DEPLOYED: Tue Apr  7 12:33:29 2026
NAMESPACE: default
STATUS: deployed
REVISION: 2
DESCRIPTION: Upgrade complete
TEST SUITE: None

$ kubectl get pods -w

NAME                                READY   STATUS    RESTARTS   AGE
myapp-simple-app-64bc66dc99-7rz5k   2/2     Running   0          45s
myapp-simple-app-64bc66dc99-bjw8q   2/2     Running   0          28s
myapp-simple-app-64bc66dc99-d2b2l   2/2     Running   0          40s
myapp-simple-app-64bc66dc99-hrj8b   2/2     Running   0          34s
myapp-simple-app-64bc66dc99-twfhb   2/2     Running   0          21s

$ POD_NAME=$(kubectl get pods -l app.kubernetes.io/instance=myapp -o jsonpath='{.items[0].metadata.name}')')
kubectl exec -it $POD_NAME -- /bin/sh

Defaulted container "simple-app" out of: simple-app, vault-agent, vault-agent-init (init)

$ cat /vault/secrets/config

data: map[password:secure-password-123 username:db-user]
metadata: map[created_time:2026-04-07T09:31:25.575203708Z custom_metadata:<nil> deletion_time: destroyed:false version:1]

$ exit

```

### Sidecar injection pattern

- The Vault Agent Injector mutates pods that have specific annotations.

- It adds a sidecar container (the Vault Agent) to the pod.

- The sidecar authenticates to Vault using the Kubernetes Service Account, retrieves the requested secrets, and writes them to a shared volume (/vault/secrets).

- The main container can then read secrets from that volume as files.

Benefits: secrets never hit the pod spec, they are dynamically renewed, and the main container does not need Vault client code.

## Security analysis

### K8s Secrets vs Vault

#### K8s Secrets when:

- You need simple, non‑dynamic credentials (e.g., static API keys, basic auth).

- Your security requirements are low to moderate and you enable etcd encryption.

- You want to avoid additional infrastructure.

#### Vault when:

- You need dynamic, short‑lived credentials (e.g., database passwords rotated automatically).

- Strict audit and compliance requirements exist (PCI, HIPAA).

- Multiple applications/services need different secret access policies.

### Production recommendations

1) Always enable etcd encryption for Kubernetes Secrets in production.

2) Use RBAC to restrict who can read Secrets – limit to only required namespaces/service accounts.

3) Never commit real secrets to Git – use placeholders + external secret injection.

4) For high‑security environments, prefer Vault with Kubernetes auth and short TTLs.

5) Monitor access – enable audit logging for both K8s API and Vault.

6) Regularly rotate secrets – Vault can automate this; for K8s Secrets, use a controller like Reloader or a CI/CD pipeline.