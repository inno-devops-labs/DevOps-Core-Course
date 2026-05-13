# Documentation

## Kubernetes Secrets

### Output of creating and viewing your secret

```bash
(devops) fountainer@Veronicas-MacBook-Air DevOps-Core-Course % kubectl create secret generic app-credentials --from-literal=username=fountainer --from-literal=password=‘mypass293i20@@nekf’
secret/app-credentials created
(devops) fountainer@Veronicas-MacBook-Air DevOps-Core-Course % kubectl get secret app-credentials  -o yaml
apiVersion: v1
data:
  password: 4oCYbXlwYXNzMjkzaTIwQEBuZWtm4oCZ
  username: Zm91bnRhaW5lcg==
kind: Secret
metadata:
  creationTimestamp: "2026-04-07T14:46:16Z"
  name: app-credentials
  namespace: default
  resourceVersion: "24859"
  uid: 6997ca85-68fa-4278-9d51-a6531df977e9
type: Opaque
```
### Decoded secret values demonstration

```bash
(devops) fountainer@Veronicas-MacBook-Air DevOps-Core-Course % echo "4oCYbXlwYXNzMjkzaTIwQEBuZWtm4oCZ" | base64 -d
‘mypass293i20@@nekf’%                                                                                                                                                    
(devops) fountainer@Veronicas-MacBook-Air DevOps-Core-Course % echo "Zm91bnRhaW5lcg==" | base64 -d
fountainer% 
```
### Explanation of base64 encoding vs encryption

- Encoding is when we use some publicly accesible algorithm to encode our data. The goal is keeping integrity and usability of the data, it is not really about security.

- In turn, Encryption is about securuty. It envolves encrypting with an algorithm that can be only resolved by a user who has an encryption key. 

## Helm Secret Integration

### Chart structure showing secrets.yaml

```bash
(devops) fountainer@Veronicas-MacBook-Air DevOps-Core-Course % tree app_python/k8s/app_python 
app_python/k8s/app_python
├── Chart.yaml
├── charts
├── templates
│   ├── _helpers.tpl
│   ├── deployment.yaml
│   ├── hooks
│   │   ├── post-install-job.yaml
│   │   └── pre-install-job.yaml
│   ├── secrets.yaml
│   └── service.yaml
├── values-dev.yaml
├── values-prod.yaml
└── values.yaml
```

### How secrets are consumed in deployment

- I have $secretName variable that is dynamically set to the name from the values.yaml and values I provide in the helm install command OR defaults to the value from helper. 

### Verification output (env vars in pod, excluding actual values)

- in pod I have correct env vars:

```bash
(devops) fountainer@Veronicas-MacBook-Air DevOps-Core-Course % kubectl exec -it mysecretrelease-app-python-7975557578-6zc9m -- sh
$ echo $PASSWORD
mypass293i20@@nekf
$ echo $USERNAME
fountainer
```

- and outside the secrets are hidden

from ```bash kubectl describe pod mysecretrelease-app-python-7975557578-6zc9m```

```bash
Environment:
      PASSWORD:  <set to the key 'password' in secret 'app-credentials'>  Optional: false
      USERNAME:  <set to the key 'username' in secret 'app-credentials'>  Optional: false
```


## Resource Management

### Resource limits configuration

```bash
resources:
    requests:
        cpu: {{ .Values.resources.requests.cpu }}
        memory: {{ .Values.resources.requests.memory }}
    limits:
        cpu: {{ .Values.resources.limits.cpu }}
        memory: {{ .Values.resources.limits.memory }}
```
- in values.yaml I have

```bash
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "500m"
    memory: "256Mi"
```

### Explanation of requests vs limits

- requests is a setting that shows kubernates how much resources are needed for a container to run
- limits show how much resources a container is allowed to use (max)

### How to choose appropriate values

- you should analyze what processes does your container run and how many cpu/memory it may need 
- values can be adjusted by observing the running container
- if you have multiple containers/pods you should constraint them in such a way that they all can work without throttling
- if the memory limit is too low the container can be killed right away

## Vault Integration

### Vault installation verification (kubectl get pods)

```bash
(devops) fountainer@Veronicas-MacBook-Air DevOps-Core-Course % kubectl get pod
NAME                                          READY   STATUS    RESTARTS   AGE
mysecretrelease-app-python-7975557578-6zc9m   1/1     Running   0          63m
mysecretrelease-app-python-7975557578-7l4tv   1/1     Running   0          63m
mysecretrelease-app-python-7975557578-bqnpd   1/1     Running   0          63m
mysecretrelease-app-python-7975557578-cjjcb   1/1     Running   0          63m
mysecretrelease-app-python-7975557578-st2jd   1/1     Running   0          63m
vault-0                                       1/1     Running   0          8m23s
vault-agent-injector-848dd747d7-qvgl2         1/1     Running   0          8m23s
```

### Policy and role configuration (sanitized)

- policy 

```bash
/ $ vault policy write myapp-policy /tmp/myapp-policy.hcl
Success! Uploaded policy: myapp-policy
/ $ vault policy read myapp-policy
path "secret/data/myapp/config" {
  capabilities = ["read"]
}
```

- role config 

```bash
vault write auth/kubernetes/role/myapp-role \
    bound_service_account_names=default \
    bound_service_account_namespaces=default \
    policies=myapp-policy \
    ttl=48h
```


### Proof of secret injection (show file exists, path structure)

```bash
(devops) fountainer@Veronicas-MacBook-Air DevOps-Core-Course % kubectl exec -it mysecretrelease-app-python-558b98bb9d-8299m -- /bin/sh
Defaulted container "app-python" out of: app-python, vault-agent, vault-agent-init (init)
$ ls -l /vault/secrets
total 4
-rw-r--r-- 1 100 newuser 180 Apr  7 23:55 config
$ cat /vault/secrets/config
data: map[password:mypass293i20@@nekf username:fountainer]
metadata: map[created_time:2026-04-07T23:32:33.85543147Z custom_metadata:<nil> deletion_time: destroyed:false version:1]
$ 
```

### Explanation of the sidecar injection pattern

- now every pod contains not only my app container but also vault sidecar container
- vault is able to authenticate in kubernates and inject secrets into the pod

## Security Analysis

### Comparison: K8s Secrets vs Vault

- kubernates secrets are just encoded into base 64 and everyone who gets access to the cluster can decode them and get sensitive data, on the other hand, vault provides data encryption that is much more safer since you need an encryption key to encrypt it

### When to use each approach

- encoding is good for keeping data usability and integrity, so different machines can use it (like for seeing special symbols on a web page), it is like... more secure than nothing, but not reeally secure

- vault encryption is needed for keeping sensitive data secure, like for storing passwords for the services on the virtual machines, etc

### Production recommendations

- in production you should always try to use strong encryption algorithms to keep your data secure
