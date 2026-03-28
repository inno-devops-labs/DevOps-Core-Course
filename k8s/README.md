# Kubernetes deployment for devops-info-service

## Architecture Overview

The application is deployed as a Kubernetes `Deployment` with **3 replicas** of the same Pod.
Each Pod runs the `devops-info-service` container on port `5000`.
A `NodePort` `Service` exposes the Pods on port `80` inside the cluster and on port `30080` externally.

Traffic flow:

`Client -> NodePort Service -> Pod (selected by label app=devops-info-service) -> FastAPI application`

Resource strategy:
- Requests: `100m CPU`, `128Mi memory`
- Limits: `200m CPU`, `256Mi memory`

This keeps the workload lightweight for minikube while still demonstrating production-style resource constraints.

## Manifest Files

### `k8s/deployment.yml`
Defines the application Deployment.

```bash
apiVersion: apps/v1
kind: Deployment
metadata:
  name: devops-info-service
  labels:
    app: devops-info-service
spec:
  replicas: 3
  minReadySeconds: 5
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: devops-info-service
  template:
    metadata:
      labels:
        app: devops-info-service
    spec:
      containers:
        - name: devops-info-service
          image: wkwtfigo/devops-info-service:latest
          imagePullPolicy: Always
          ports:
            - containerPort: 8000
              name: http
          env:
            - name: PYTHONUNBUFFERED
              value: "1"
            - name: PORT
              value: "8000"
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "200m"
              memory: "256Mi"
          startupProbe:
            httpGet:
              path: /health
              port: http
            periodSeconds: 5
            timeoutSeconds: 2
            failureThreshold: 24
          readinessProbe:
            httpGet:
              path: /health
              port: http
            periodSeconds: 5
            timeoutSeconds: 2
            failureThreshold: 6
          livenessProbe:
            httpGet:
              path: /health
              port: http
            periodSeconds: 10
            timeoutSeconds: 2
            failureThreshold: 6
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: false
            capabilities:
              drop: ["ALL"]
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        runAsGroup: 1000
```

Key choices:
- `replicas: 3` to satisfy the lab requirement and demonstrate load distribution.
- `strategy: RollingUpdate` with `maxSurge: 1` and `maxUnavailable: 0` to keep the app available during updates.
- `readinessProbe` and `livenessProbe` use `GET /health` to verify both startup readiness and runtime health.
- Requests and limits are set for CPU and memory.
- `runAsNonRoot: true` is used because the Docker image was already prepared as a non-root container in previous labs.

### `k8s/service.yml`
Defines the Service used to expose the Deployment.

```bash
apiVersion: v1
kind: Service
metadata:
  name: devops-info-service
  labels:
    app: devops-info-service
spec:
  type: NodePort
  selector:
    app: devops-info-service
  ports:
    - name: http
      protocol: TCP
      port: 80
      targetPort: 8000
      nodePort: 30080
```

Key choices:
- `type: NodePort` because this lab targets local access through minikube.
- `selector.app: devops-info-service` matches the Deployment labels.
- `port: 80` forwards to `targetPort: 8000` inside the container.
- `nodePort: 30080` is fixed for predictable access.

## Deployment Evidence

`kubectl get all`

![](/monitoring/docs/screenshots/k8s_all.png)

`kubectl get pods, svc`

![](/monitoring/docs/screenshots/k8s_pods_svc.png)

`kubectl describe deployment <name>`

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl describe deployment devops-info-service      
Name:                   devops-info-service
Namespace:              default
CreationTimestamp:      Thu, 19 Mar 2026 18:38:21 +0300
Labels:                 app=devops-info-service
Annotations:            deployment.kubernetes.io/revision: 9
Selector:               app=devops-info-service
Replicas:               5 desired | 5 updated | 5 total | 5 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        5
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Pod Template:
  Labels:       app=devops-info-service
  Annotations:  kubectl.kubernetes.io/restartedAt: 2026-03-19T19:11:46+03:00
  Containers:
   devops-info-service:
    Image:      wkwtfigo/devops-info-service:latest
    Port:       8000/TCP (http)
    Host Port:  0/TCP (http)
    Limits:
      cpu:     200m
      memory:  256Mi
    Requests:
      cpu:      100m
      memory:   128Mi
    Liveness:   http-get http://:http/health delay=0s timeout=2s period=10s #success=1 #failure=6
    Readiness:  http-get http://:http/health delay=0s timeout=2s period=5s #success=1 #failure=6
    Startup:    http-get http://:http/health delay=0s timeout=2s period=5s #success=1 #failure=24
    Environment:
      PYTHONUNBUFFERED:  1
      PORT:              8000
    Mounts:              <none>
  Volumes:               <none>
  Node-Selectors:        <none>
  Tolerations:           <none>
Conditions:
  Type           Status  Reason
  ----           ------  ------
  Available      True    MinimumReplicasAvailable
  Progressing    True    NewReplicaSetAvailable
OldReplicaSets:  devops-info-service-979f6f9dc (0/0 replicas created), devops-info-service-5cf79bf88d (0/0 replicas created), devops-info-service-5d66df6c8b (0/0 replicas created), devops-info-service-76bdfcdfd8 (0/0 replicas created), devops-info-service-6d799fdddc (0/0 replicas created), devops-info-service-58f77466d (0/0 replicas created), devops-info-service-7d69dd59bd (0/0 replicas created)
NewReplicaSet:   devops-info-service-57d4966859 (5/5 replicas created)
Events:
  Type    Reason             Age                 From                   Message
  ----    ------             ----                ----                   -------
  Normal  ScalingReplicaSet  43m (x35 over 61m)  deployment-controller  (combined from similar events): Scaled down replica set devops-info-service-7d69dd59bd from 1 to 0
```

**Screenshots:**

![](/monitoring/docs/screenshots/port_forward.png)
![](/monitoring/docs/screenshots/browser_clean.png)
![](/monitoring/docs/screenshots/browser_health.png)

or with `minikube`

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> minikube service devops-info-service --url
http://127.0.0.1:25870
❗  Because you are using a Docker driver on windows, the terminal needs to be open to run it.       
```

```C:\Users\zagur>curl http://127.0.0.1:25870/health
{"status":"healthy","timestamp":"2026-03-19T16:15:20.046Z","uptime_seconds":170}
C:\Users\zagur>curl http://127.0.0.1:25870
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"devops-info-service-57d4966859-f4g8x","platform":"Linux","platform_version":"#1 SMP PREEMPT_DYNAMIC Thu Jun  5 18:30:46 UTC 2025","architecture":"x86_64","cpu_count":8,"python_version":"3.13.11"},"runtime":{"uptime_seconds":148,"uptime_human":"0 hours, 2 minutes","current_time":"2026-03-19T16:15:25.531Z","timezone":"UTC"},"request":{"client_ip":"10.244.0.1","user_agent":"curl/8.18.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}
C:\Users\zagur>
```

### Cluster info
```bash
kubectl cluster-info
kubectl get nodes -o wide
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> minikube start 
😄  minikube v1.35.0 on Microsoft Windows 11 Home Single Language 10.0.26200.8037 Build 26200.8037
🎉  minikube 1.38.1 is available! Download it: https://github.com/kubernetes/minikube/releases/tag/v1.38.1
💡  To disable this notice, run: 'minikube config set WantUpdateNotification false'

✨  Automatically selected the docker driver. Other choices: virtualbox, ssh
📌  Using Docker Desktop driver with root privileges
👍  Starting "minikube" primary control-plane node in "minikube" cluster
🚜  Pulling base image v0.0.46 ...
💾  Downloading Kubernetes v1.32.0 preload ...
    > preloaded-images-k8s-v18-v1...:  333.57 MiB / 333.57 MiB  100.00% 27.30 M
🔥  Creating docker container (CPUs=2, Memory=4000MB) ...
❗  Failing to connect to https://registry.k8s.io/ from inside the minikube container
💡  To pull new external images, you may need to configure a proxy: https://minikube.sigs.k8s.io/docs/reference/networking/proxy/
🐳  Preparing Kubernetes v1.32.0 on Docker 27.4.1 ...
    ▪ Generating certificates and keys ...
    ▪ Booting up control plane ...
    ▪ Configuring RBAC rules ...
🔗  Configuring bridge CNI (Container Networking Interface) ...
🔎  Verifying Kubernetes components...
    ▪ Using image gcr.io/k8s-minikube/storage-provisioner:v5
🌟  Enabled addons: storage-provisioner, default-storageclass

❗  C:\Program Files\kubectl\kubectl.exe is version 1.34.0, which may have incompatibilities with Kubernetes 1.32.0.
    ▪ Want kubectl v1.32.0? Try 'minikube kubectl -- get pods -A'
🏄  Done! kubectl is now configured to use "minikube" cluster and "default" namespace by default
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl cluster-info
Kubernetes control plane is running at https://127.0.0.1:26928
CoreDNS is running at https://127.0.0.1:26928/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get nodes
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   49s   v1.32.0
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get namespaces
NAME              STATUS   AGE
default           Active   61s
kube-node-lease   Active   61s
kube-public       Active   61s
kube-system       Active   61s
PS C:\Users\zagur\DevOps\DevOps-Core-Course> 
```

### Resources
```bash
kubectl get all
kubectl get pods,svc -o wide
kubectl describe deployment devops-info-service
```

### Logs and health
```bash
kubectl logs deployment/devops-info-service
curl http://127.0.0.1:PORT/health
```

## Operations Performed

### Deploy
```bash
kubectl apply -f k8s/deployment.yml
kubectl apply -f k8s/service.yml
kubectl rollout status deployment/devops-info-service
kubectl get pods,svc -o wide
```

### Access service with minikube
```bash
minikube service devops-info-service --url
```

### Scale to 5 replicas
```bash
kubectl scale deployment/devops-info-service --replicas=5
kubectl get pods -w
kubectl rollout status deployment/devops-info-service
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl scale deployment/devops-info-service --replicas=5
deployment.apps/devops-info-service scaled
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get pods -w                    
NAME                                   READY   STATUS    RESTARTS   AGE
devops-info-service-57d4966859-97lqh   1/1     Running   0          11m
devops-info-service-57d4966859-9whgf   1/1     Running   0          10m
devops-info-service-57d4966859-f4g8x   1/1     Running   0          10m
devops-info-service-57d4966859-lqrnm   0/1     Running   0          13s
devops-info-service-57d4966859-w5pnn   0/1     Running   0          13s
devops-info-service-57d4966859-w5pnn   0/1     Running   0          16s
devops-info-service-57d4966859-w5pnn   1/1     Running   0          16s
devops-info-service-57d4966859-lqrnm   0/1     Running   0          21s
devops-info-service-57d4966859-lqrnm   1/1     Running   0          21s
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl rollout status deployment/devops-info-service
deployment "devops-info-service" successfully rolled out
```

### Rolling update
```bash
kubectl set env deployment/devops-info-service LAB_VERSION=v2
kubectl rollout status deployment/devops-info-service
kubectl rollout history deployment/devops-info-service
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl set env deployment/devops-info-service LAB_VERSION=v2
deployment.apps/devops-info-service env updated
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl rollout status deployment/devops-info-service
Waiting for deployment "devops-info-service" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "devops-info-service" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "devops-info-service" rollout to finish: 1 old replicas are pending termination...
deployment "devops-info-service" successfully rolled out
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl rollout history deployment/devops-info-service
deployment.apps/devops-info-service 
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
3         <none>
4         <none>
5         <none>
6         <none>
7         <none>
8         <none>

PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl get pods -w
NAME                                   READY   STATUS    RESTARTS   AGE
devops-info-service-7d69dd59bd-2hdh7   1/1     Running   0          2m4s
devops-info-service-7d69dd59bd-c66cg   1/1     Running   0          60s
devops-info-service-7d69dd59bd-gc4kv   1/1     Running   0          105s
devops-info-service-7d69dd59bd-tvdjp   1/1     Running   0          41s
devops-info-service-7d69dd59bd-zlklm   1/1     Running   0          81s
PS C:\Users\zagur\DevOps\DevOps-Core-Course> 
```

### Rollback
```bash
kubectl rollout undo deployment/devops-info-service
kubectl rollout status deployment/devops-info-service
kubectl rollout history deployment/devops-info-service
```

```bash
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl rollout undo deployment/devops-info-service
deployment.apps/devops-info-service rolled back
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl rollout status deployment/devops-info-service
>>
Waiting for deployment "devops-info-service" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "devops-info-service" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "devops-info-service" rollout to finish: 1 old replicas are pending termination...
deployment "devops-info-service" successfully rolled out
PS C:\Users\zagur\DevOps\DevOps-Core-Course> kubectl rollout history deployment/devops-info-service
deployment.apps/devops-info-service 
REVISION  CHANGE-CAUSE
1         <none>
2         <none>
3         <none>
4         <none>
5         <none>
6         <none>
8         <none>
9         <none>
```

## Production Considerations

### Health checks
`readinessProbe` prevents traffic from reaching a Pod before the application is ready.
`livenessProbe` helps Kubernetes restart a hung or unhealthy container.
Using `/health` is appropriate for a lightweight HTTP service.

```yml
readinessProbe:
    httpGet:
        path: /health
        port: http
    periodSeconds: 5
    timeoutSeconds: 2
    failureThreshold: 6
    livenessProbe:
    httpGet:
        path: /health
        port: http
    periodSeconds: 10
    timeoutSeconds: 2
    failureThreshold: 6
```

### Resource limits rationale
The application is small and suited for minikube, so low values were selected:
- request `100m/128Mi` ensures the Pod can be scheduled consistently;
- limit `200m/256Mi` prevents a single container from consuming too many local cluster resources.

```yml
resources:
    requests:
        cpu: "100m"
        memory: "128Mi"
    limits:
        cpu: "200m"
        memory: "256Mi"
```

### Production improvements
For a real production cluster I would additionally add:
- separate namespace;
- `startupProbe` if startup becomes slower;
- `HorizontalPodAutoscaler`;
- ConfigMap/Secret separation;
- Ingress with TLS;
- monitoring with Prometheus + Grafana;
- centralized logging with Loki/ELK.

### Monitoring and observability strategy
At minimum:
- application logs via `kubectl logs` during local development;
- cluster events via `kubectl describe`;
- Prometheus metrics endpoint if the app exposes one;
- Grafana dashboards for CPU, memory, restarts, and response times.

## Challenges & Solutions

**Problem:** After applying the Deployment, all Pods stayed in `Running` state but showed `0/1 Ready`. The application was not available through the Service.

**Solution:** I used `kubectl describe pod` to inspect the Pod state and events. This showed that both readiness and liveness probes were failing with `connection refused` on port `8000`. That meant Kubernetes could reach the Pod network, but nothing inside the container was actually listening on the expected port.

### 2) Liveness and readiness probes caused continuous restarts

**Problem:** Because the health checks kept failing, Kubernetes restarted the containers repeatedly. This made debugging difficult, because the container could disappear before I had time to inspect it with `kubectl exec`.

**Solution:** I temporarily removed the probes from the Deployment to stabilize the Pods and stop the restart loop. After the container stayed alive long enough for debugging, I re-checked the process inside it and confirmed that the issue was not caused by Kubernetes itself, but by how the application was started inside the image.

### 3) The container did not expose an HTTP server on port 8000

**Problem:** Inside the running container, the main process was `python app.py`, but the application did not actually open port `8000`. Requests to `127.0.0.1:8000` and `/health` returned `connection refused`.

**Solution:** I verified the running command with `cat /proc/1/cmdline` and tested connectivity from inside the container using Python socket and HTTP checks. This proved that the image was not starting a web server correctly. The fix was to ensure that the application runs as an HTTP service and listens on `0.0.0.0:8000`, so that Kubernetes probes and the Service can reach it.

## What I learned

This lab helped me understand:
- the difference between Pods, Deployments, and Services;
- declarative management with `kubectl apply`;
- why probes and resource limits matter;
- how Kubernetes performs scaling, rolling updates, and rollbacks.

