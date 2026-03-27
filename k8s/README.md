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

## Task 3 - Service Configuration

The Service uses type `NodePort` and targets the Deployment Pods with the `app.kubernetes.io/name=devops-app-py` label. It exposes service port `80` and forwards traffic to container port `5000` on a fixed NodePort, `30080`.

For connectivity verification, I used `kubectl port-forward service/devops-app-py-service 8080:80`. I tested `minikube service ... --url` first, but in this Docker-driver setup the returned node IP was not directly reachable from the host, so port-forward was the practical local-access path.

<details>
<summary>Service verification output</summary>

```text
$ kubectl apply -f k8s/service.yml
service/devops-app-py-service unchanged

$ kubectl get services
NAME                    TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)        AGE
devops-app-py-service   NodePort    10.110.168.128   <none>        80:30080/TCP   32s
kubernetes              ClusterIP   10.96.0.1        <none>        443/TCP        80m

$ kubectl describe service devops-app-py-service
Name:                     devops-app-py-service
Namespace:                default
Labels:                   app.kubernetes.io/name=devops-app-py
                          app.kubernetes.io/part-of=devops-core-s26
Annotations:              <none>
Selector:                 app.kubernetes.io/name=devops-app-py
Type:                     NodePort
IP Family Policy:         SingleStack
IP Families:              IPv4
IP:                       10.110.168.128
IPs:                      10.110.168.128
Port:                     http  80/TCP
TargetPort:               5000/TCP
NodePort:                 http  30080/TCP
Endpoints:                10.244.0.12:5000,10.244.0.13:5000,10.244.0.14:5000
Session Affinity:         None
External Traffic Policy:  Cluster
Internal Traffic Policy:  Cluster
Events:                   <none>

$ kubectl get endpoints devops-app-py-service
Warning: v1 Endpoints is deprecated in v1.33+; use discovery.k8s.io/v1 EndpointSlice
NAME                    ENDPOINTS                                            AGE
devops-app-py-service   10.244.0.12:5000,10.244.0.13:5000,10.244.0.14:5000   32s

$ kubectl port-forward service/devops-app-py-service 8080:80
Forwarding from 127.0.0.1:8080 -> 5000
Forwarding from [::1]:8080 -> 5000
Handling connection for 8080
Handling connection for 8080
Handling connection for 8080
Handling connection for 8080

$ curl -fsSL 127.0.0.1:8080 | jq .service.name
"devops-info-service"

$ curl -fsSL 127.0.0.1:8080/health | jq .status
"healthy"

$ curl -fsSL 127.0.0.1:8080/ready | jq .status
"ready"

$ curl -fsSL 127.0.0.1:8080/metrics | head -n 12
# HELP http_requests_total Total HTTP requests handled by the service.
# TYPE http_requests_total counter
http_requests_total{endpoint="/ready",method="GET",status_code="200"} 180.0
http_requests_total{endpoint="/health",method="GET",status_code="200"} 90.0
http_requests_total{endpoint="/",method="GET",status_code="200"} 2.0
http_requests_total{endpoint="/metrics",method="GET",status_code="200"} 1.0
# HELP http_requests_created Total HTTP requests handled by the service.
# TYPE http_requests_created gauge
http_requests_created{endpoint="/ready",method="GET",status_code="200"} 1.7745777896655755e+09
http_requests_created{endpoint="/health",method="GET",status_code="200"} 1.7745778018120363e+09
http_requests_created{endpoint="/",method="GET",status_code="200"} 1.7745779956714542e+09
http_requests_created{endpoint="/metrics",method="GET",status_code="200"} 1.7745779957933705e+09
```

</details>
