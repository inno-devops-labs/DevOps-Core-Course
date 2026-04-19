# Kubernetes Deployment

## Architecture Overview
- 3–5 Pods running Python app
- NodePort Service exposing app
- Traffic flow:
  User → Service → Pods

## Manifest Files

### deployment.yml
- 3 replicas for high availability
- Resource limits to prevent overload
- Health checks for reliability

### service.yml
- NodePort for external access
- Routes traffic to Pods via labels

## Operations

### Deploy
kubectl apply -f k8s/

### Scale
kubectl scale deployment/my-python-app --replicas=5

### Update
kubectl apply -f k8s/deployment.yml

### Rollback
kubectl rollout undo deployment/my-python-app

## Production Considerations

- Health checks ensure uptime
- Resource limits prevent crashes
- Would add:
  - Ingress
  - Monitoring (Prometheus)
  - Logging

## Challenges

- Debugging pods → used:
  kubectl logs
  kubectl describe pod

- Learned:
  - Kubernetes is declarative
  - Services use labels

# Task 1 - Local Kubernets setup

### Install kubectl check  `cubectl version --client`

```bash
setterwars@setterwarsThinkPad-L13-Yoga-Gen-2:~/Documents/IU/DevOps-Core-Course$ kubectl version --client
Client Version: v1.30.14
Kustomize Version: v5.0.4-0.20230601165947-6ce0bf390ce3
setterwars@setterwarsThinkPad-L13-Yoga-Gen-2:~/Documents/IU/DevOps-Core-Course$ 
```

### Using of the `minikube`

- `minikube start --driver=docker` output

```bash
setterwars@setterwarsThinkPad-L13-Yoga-Gen-2:~/Documents/IU/DevOps-Core-Course$ minikube start --driver=docker
😄  minikube v1.38.1 on Ubuntu 25.10
✨  Using the docker driver based on user configuration
❗  Starting v1.39.0, minikube will default to "containerd" container runtime. See #21973 for more info.
📌  Using Docker driver with root privileges
👍  Starting "minikube" primary control-plane node in "minikube" cluster
🚜  Pulling base image v0.0.50 ...
💾  Downloading Kubernetes v1.35.1 preload ...
    > preloaded-images-k8s-v18-v1...:  272.45 MiB / 272.45 MiB  100.00% 16.46 M
    > gcr.io/k8s-minikube/kicbase...:  519.58 MiB / 519.58 MiB  100.00% 4.05 Mi
🔥  Creating docker container (CPUs=2, Memory=3700MB) ...
🐳  Preparing Kubernetes v1.35.1 on Docker 29.2.1 ...
🔗  Configuring bridge CNI (Container Networking Interface) ...
🔎  Verifying Kubernetes components...
    ▪ Using image gcr.io/k8s-minikube/storage-provisioner:v5
🌟  Enabled addons: storage-provisioner, default-storageclass

❗  /usr/bin/kubectl is version 1.30.14, which may have incompatibilities with Kubernetes 1.35.1.
    ▪ Want kubectl v1.35.1? Try 'minikube kubectl -- get pods -A'
🏄  Done! kubectl is now configured to use "minikube" cluster and "default" namespace by default

```

- `kubectl cluster-info` output

```bash
setterwars@setterwarsThinkPad-L13-Yoga-Gen-2:~/Documents/IU/DevOps-Core-Course$ kubectl cluster-info
Kubernetes control plane is running at https://192.168.49.2:8443
CoreDNS is running at https://192.168.49.2:8443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
setterwars@setterwarsThinkPad-L13-Yoga-Gen-2:~/Documents/IU/DevOps-Core-Course$ 
```

- `kubectl get nodes` output

```bash
setterwars@setterwarsThinkPad-L13-Yoga-Gen-2:~/Documents/IU/DevOps-Core-Course$ kubectl get nodes
NAME       STATUS   ROLES           AGE    VERSION
minikube   Ready    control-plane   118s   v1.35.1  
```

- `minicube status` 

```bash
setterwars@setterwarsThinkPad-L13-Yoga-Gen-2:~$ minikube status
minikube
type: Control Plane
host: Running
kubelet: Running
apiserver: Running
kubeconfig: Configured
```

#### Why minikube

Start with Minikube. The built-in dashboard and storage classes make learning easier.

# Task 2 - Application Deployment

- `kubectl apply -f k8s/deployment.yml` output

```bash
setterwars@setterwarsThinkPad-L13-Yoga-Gen-2:~/Documents/IU/DevOps-Core-Course$ kubectl apply -f k8s/deployment.yml
deployment.apps/my-python-app created

```

- `kubectl get deployments` output 

```bash
setterwars@setterwarsThinkPad-L13-Yoga-Gen-2:~/Documents/IU/DevOps-Core-Course$ kubectl get deployments.apps 
NAME            READY   UP-TO-DATE   AVAILABLE   AGE
my-python-app   3/3     3            3           6m47s
```

- ` kubectl get pods` output
```bash
kubectl get pods
deployment.apps/my-python-app unchanged
NAME                             READY   STATUS        RESTARTS      AGE
my-python-app-598569f8d4-n7nwf   1/1     Running       0             21s
my-python-app-598569f8d4-ppvw7   1/1     Running       0             11s
my-python-app-598569f8d4-zt6g4   1/1     Running       0             32s
```

# Task 3 - Service configuration 

## Apply and test commands outputs

- `kubectl apply -f k8s/service.yml` output
```bash
setterwars@setterwarsThinkPad-L13-Yoga-Gen-2:~/Documents/IU/DevOps-Core-Course$ kubectl apply -f k8s/service.yml
service/my-app-service created
```

- `kubectl get services` output

```bash
setterwars@setterwarsThinkPad-L13-Yoga-Gen-2:~/Documents/IU/DevOps-Core-Course$ kubectl get services
NAME             TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
kubernetes       ClusterIP   10.96.0.1       <none>        443/TCP        46h
my-app-service   NodePort    10.111.17.133   <none>        80:30080/TCP   82s
```

- `minikube service my-app-service` output

```bash
setterwars@setterwarsThinkPad-L13-Yoga-Gen-2:~/Documents/IU/DevOps-Core-Course$ minikube service my-app-service
┌───────────┬────────────────┬─────────────┬───────────────────────────┐
│ NAMESPACE │      NAME      │ TARGET PORT │            URL            │
├───────────┼────────────────┼─────────────┼───────────────────────────┤
│ default   │ my-app-service │ 80          │ http://192.168.49.2:30080 │
└───────────┴────────────────┴─────────────┴───────────────────────────┘
🎉  Opening service default/my-app-service in default browser...
```

*in browser*

```json
{
  "endpoints": [
    {
      "description": "Service information",
      "method": "GET",
      "path": "/"
    },
    {
      "description": "Health check",
      "method": "GET",
      "path": "/health"
    },
    {
      "description": "Prometheus metrics",
      "method": "GET",
      "path": "/metrics"
    }
  ],
  "request": {
    "client_ip": "10.244.0.1",
    "method": "GET",
    "path": "/",
    "user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 YaBrowser/26.3.0.0 Safari/537.36"
  },
  "runtime": {
    "current-time": "2026-03-22T16:14:11.182579+00:00",
    "timezone": "UTC",
    "uptime_human": "0 hours, 6 minutes",
    "uptime_seconds": 419
  },
  "service": {
    "description": "DevOps course info service",
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "system": {
    "architecture": "x86_64",
    "cpu_count": 8,
    "hostname": "my-python-app-598569f8d4-ppvw7",
    "platform": "Linux",
    "platform_version": "#19-Ubuntu SMP PREEMPT_DYNAMIC Fri Mar  6 14:02:58 UTC 2026",
    "python_version": "3.13.12"
  }
}
```

# Task 4 - Scaling and updates 

## Scaling

- `kubectl scale deployment/my-python-app --replicas=5` output

```bash
setterwars@setterwarsThinkPad-L13-Yoga-Gen-2:~/Documents/IU/DevOps-Core-Course$ kubectl scale deployment/my-python-app --replicas=5
deployment.apps/my-python-app scaled
```

- `kubectl get pods` output

```bash
setterwars@setterwarsThinkPad-L13-Yoga-Gen-2:~/Documents/IU/DevOps-Core-Course$ kubectl get pods
NAME                             READY   STATUS    RESTARTS   AGE
my-python-app-598569f8d4-6tgmn   1/1     Running   0          53s
my-python-app-598569f8d4-jl6r5   1/1     Running   0          53s
my-python-app-598569f8d4-n7nwf   1/1     Running   0          10m
my-python-app-598569f8d4-ppvw7   1/1     Running   0          10m
my-python-app-598569f8d4-zt6g4   1/1     Running   0          10m
```

## Roling updates

- `KUBE_EDITOR=nano kubectl edit deployment my-python-app` output

```bash
setterwars@setterwarsThinkPad-L13-Yoga-Gen-2:~/Documents/IU/DevOps-Core-Course$ KUBE_EDITOR=nano kubectl edit deployment my-python-app
deployment.apps/my-python-app edited
```

- `kubectl apply -f k8s/deployment.yml` output

```bash
deployment.apps/my-python-app configured
```

- `kubectl rollout status deployment/my-python-app` output

```bash
Waiting for deployment "my-python-app" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "my-python-app" rollout to finish: 4 out of 5 new replicas have been updated...
deployment "my-python-app" successfully rolled out
```

# Rollback

- `kubectl rollout undo deployment/my-python-app` output

```bash
deployment.apps/my-python-app rolled back
```

- `kubectl rollout status deployment/my-python-app` output

```bash
deployment "my-python-app" successfully rolled out
```