# Kubernetes Lab 9

## Task 1 - Local Kubernetes Setup

I used `minikube` because it was in Arch Linux extra repo (`kind` is only in AUR), integrates cleanly with the Docker driver, and has more features.

<details>
<summary>Cluster setup verification output</summary>

```text
$ minikube status
minikube
type: Control Plane
host: Running
kubelet: Running
apiserver: Running
kubeconfig: Configured


$ kubectl cluster-info
Kubernetes control plane is running at https://192.168.49.2:8443
CoreDNS is running at https://192.168.49.2:8443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.

$ kubectl get nodes -o wide
NAME       STATUS   ROLES           AGE     VERSION   INTERNAL-IP    EXTERNAL-IP   OS-IMAGE                         KERNEL-VERSION      CONTAINER-RUNTIME
minikube   Ready    control-plane   2m45s   v1.35.1   192.168.49.2   <none>        Debian GNU/Linux 12 (bookworm)   6.19.10-1-cachyos   docker://29.2.1

$ kubectl get namespaces
NAME              STATUS   AGE
default           Active   3m9s
kube-node-lease   Active   3m9s
kube-public       Active   3m9s
kube-system       Active   3m9s
```

</details>

## Task 2 - Application Deployment

The deployment uses `localt0aster/devops-app-py:1.9-dev` with 3 replicas, rolling updates, and resource requests and limits. The current manifest uses `GET /health` for liveness and `GET /ready` for readiness.

<details>
<summary>Deployment rollout verification output</summary>

```text
$ kubectl delete deployment devops-app-py --cascade=foreground --wait=true
deployment.apps "devops-app-py" deleted from default namespace

$ kubectl apply -f k8s/deployment.yml
deployment.apps/devops-app-py created

$ kubectl rollout status deployment/devops-app-py --timeout=180s
Waiting for deployment "devops-app-py" rollout to finish: 0 of 3 updated replicas are available...
Waiting for deployment "devops-app-py" rollout to finish: 1 of 3 updated replicas are available...
Waiting for deployment "devops-app-py" rollout to finish: 2 of 3 updated replicas are available...
deployment "devops-app-py" successfully rolled out

$ kubectl get deployment devops-app-py
NAME            READY   UP-TO-DATE   AVAILABLE   AGE
devops-app-py   3/3     3            3           8s

$ kubectl get pods -l app.kubernetes.io/name=devops-app-py -o wide
NAME                             READY   STATUS    RESTARTS   AGE   IP           NODE       NOMINATED NODE   READINESS GATES
devops-app-py-76fc7985df-jq2tr   1/1     Running   0          8s    10.244.0.14   minikube   <none>           <none>
devops-app-py-76fc7985df-jwpsf   1/1     Running   0          8s    10.244.0.13   minikube   <none>           <none>
devops-app-py-76fc7985df-nwr58   1/1     Running   0          8s    10.244.0.12   minikube   <none>           <none>

$ kubectl describe deployment devops-app-py
Name:                   devops-app-py
Namespace:              default
CreationTimestamp:      Fri, 27 Mar 2026 05:16:21 +0300
Labels:                 app.kubernetes.io/name=devops-app-py
                        app.kubernetes.io/part-of=devops-core-s26
Annotations:            deployment.kubernetes.io/revision: 1
Selector:               app.kubernetes.io/name=devops-app-py
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  1 max unavailable, 1 max surge
Pod Template:
  Labels:  app.kubernetes.io/name=devops-app-py
           app.kubernetes.io/part-of=devops-core-s26
  Containers:
   devops-app-py:
    Image:      localt0aster/devops-app-py:1.9-dev
    Port:       5000/TCP (http)
    Host Port:  0/TCP (http)
    Limits:
      cpu:     250m
      memory:  256Mi
    Requests:
      cpu:      100m
      memory:   128Mi
    Liveness:   http-get http://:http/health delay=10s timeout=2s period=10s #success=1 #failure=3
    Readiness:  http-get http://:http/ready delay=5s timeout=2s period=5s #success=1 #failure=3
    Environment:
      HOST:        0.0.0.0
      PORT:        5000
    Mounts:        <none>
  Volumes:         <none>
  Node-Selectors:  <none>
  Tolerations:     <none>
Conditions:
  Type           Status  Reason
  ----           ------  ------
  Available      True    MinimumReplicasAvailable
  Progressing    True    NewReplicaSetAvailable
OldReplicaSets:  <none>
NewReplicaSet:   devops-app-py-76fc7985df (3/3 replicas created)
Events:
  Type    Reason             Age   From                   Message
  ----    ------             ----  ----                   -------
  Normal  ScalingReplicaSet  9s    deployment-controller  Scaled up replica set devops-app-py-76fc7985df from 0 to 3
```

</details>
