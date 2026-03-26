# Task 5 - Documentation

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Kubernetes Cluster                      │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    NodePort Service                       │  │
│  │              python-app-service:30080                     |  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                     Deployment                            │  │
│  │                      python-app                           │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │  │
│  │  │  Pod 1  │  │  Pod 2  │  │  Pod 3  │  │  Pod 4  │       │  │
│  │  │ :5000   │  │ :5000   │  │ :5000   │  │ :5000   │       │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │  │
│  │                       3-5 replicas                        │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Architecture components:**
- Deployment: Manages 3-5 replicas of application with rolling update strategy
- Service: NodePort type, which opens access on 30080 port
- Pods: Containers with Python Flask app on 5000 port 
- Resources: Every pod is limited by 256Mi of memory and 200m CPU

**Resource Allocation:**
- Memory requests: 128Mi
- Memory limits: 256Mi
- CPU requests: 100m
- CPU limits: 200m

## 2. Manifest Files
`deployment.yml` key settings:
- 3 replicas: Provides high availability
- Resource requests/limits: Prevents starvation and ensures proper planning
- Liveness probe: Checks /health every 10 seconds, restarts container if error occurs
- Readiness probe: Checks /ready every 5 seconds, removes pod from service service if it's not ready.

`service.yml` key settings:
- NodePort: Allows access from outside the cluster
- selector: Binds service to pods by label app: python-app
- targetPort: Мapps port 80 service by port 5000 of container

## 3. Deployment Evidence
Check resources:
![kubectl](screenshots/kubectl%202.png)
![kubectl-service](screenshots/kuberctl%20service%203.png)
![endpoints](screenshots/check%20enpoints%203.png)

## 4. Operations Performed
**Initial setup**:
![scaling](screenshots/cluster%20setup%201.png)

**Scaling to 5 Replicas**:
![scaling](screenshots/pods%20scale%204.png)

**Rolling Update**:
![rolling-update](screenshots/rollout%20update%204.png)

**Rollback**:
![rollback](screenshots/rollback%204.png)

**Service Access**:
```
# Getting service URL
minikube service python-app-service --url

# Access through browser
open $(minikube service python-app-service --url)
```

![check](screenshots/browser%20check.png)

## 5. Production Considerations
1. What health checks did you implement and why?
    - Implemented Health Checks:

    **Liveness Probe (`/health`):**
    ```yaml
    livenessProbe:
        httpGet:
            path: /health
            port: 5000
        initialDelaySeconds: 20
        periodSeconds: 10
        timeoutSeconds: 5
        failureThreshold: 3
    ```

    **Readiness Probe (/ready):**
    ```yaml
    readinessProbe:
    httpGet:
        path: /ready
        port: 5000
    initialDelaySeconds: 15
    periodSeconds: 5
    timeoutSeconds: 5
    successThreshold: 1
    failureThreshold: 3
    ```

    Why this probes:
    |Probe | Purpose | Why Implemented |
    | ---- | ------- | --------------- |
    |Liveness | Determines whether the container needs to be restarted. | Without this, the container with the suspended application would have continued to work, but did not respond to requests. Liveness probe restarts it automatically, providing self-healing. |
    |Readiness | Determines whether the pod is ready to receive traffic. | When starting, the application needs time to initialize (download configuration, establish connections). Readiness probe ensures that the pod does not receive traffic until it is fully ready, preventing 5xx errors. |

2. Resource limits rationale
    - **Current сonfiguration**
    ```yaml
    resources:
    requests:
        memory: "128Mi"
        cpu: "100m"
    limits:
        memory: "256Mi"
        cpu: "200m"
    ```

    - Why these values?

    | Resource | Request | Limit | Rationale |
    | -------- | ------- | ----- | --------- |
    | Memory   | 128Mi   | 256Mi | A Flask application with prometheus metrics consumes ~80-100Mi in normal mode. The 128Mi guarantees stable operation even under light load. 256Mi leaves 100% margin for peak loads, garbage collection, and prevents OOM kills. |
    | CPU | 100m | 200m | The application does not perform heavy calculations (HTTP processing only). 100m is enough to process ~100-200 requests/sec. The 200m limit prevents the monopolization of the CPU in case of possible problems (for example, an infinite loop or a CPU leak). | 

3. How would you improve this for production?
    - **Horizontal Pod Autoscaler (HPA)**. Automatic scaling, depending on CPU/memory metrics
    - **Pod Disruption Budget (PDB)**. Guarantees accessibility during voluntary evacuations
    - **ConfigMaps for Configuration**. Removing the configuration from the image for flexibility.

4. Monitoring and observability strategy
    - **Metrics collection**.
        - `/metrics` endpoint with Prometheus metrics (Counter, Histogram, Gauge)
        - Custom metrics
        - Grafana Dashboards
        - Centralized logging with Loki

    - **Observability Stack Architecture**:
    ```
    ┌───────────────────────────────────────────────────────┐
    │                    Observability Stack                │
    ├───────────────────────────────────────────────────────┤
    │                                                       │
    │  ┌──────────────┐                   ┌──────────────┐  │
    │  │  Prometheus  │                   │     Loki     │  │
    │  │   Metrics    │                   │    Logs      │  │
    │  └──────────────┘                   └──────────────┘  │
    │         │                                   │         │
    │         └────────────────|––––––––––––––––––┘         |
    │                          |                            │
    │                  ┌──────────────┐                     │
    │                  │   Grafana    │                     │
    │                  │  Dashboards  │                     │
    │                  └──────────────┘                     │
    └───────────────────────────────────────────────────────┘
    ```

## 6. Challenges & Solutions
### Issue 1: InvalidImageName Error
Problem: Pods failed to start with `InvalidImageName` error 

Solution: Replaced ${{ secrets.DOCKERHUB_USERNAME }} with my actual username

### Issue 2: CrashLoopBackOff from Missing /ready Endpoint
Problem: Pods were constantly restarting.

Solution: Added /ready endpoint to app.py, because this endpoint didn't exist

### Issue 3: Port Mismatch Between Container and Probes
Problem: Probes failed due to port inconsistency

Solution: Application was listening on port 5000, but probes were configured for port 8000, so that I fixed port in all probes and containerPort

### What I Learned:
- Kubernetes Requires Explicit Image Names,
- Readiness and Liveness Probes Are Critical
- Port Consistency is Mandatory
