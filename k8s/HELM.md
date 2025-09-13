![image](https://github.com/user-attachments/assets/c0cdeb0e-cb5d-4f69-b4d6-ee410961b715)# Task 1

## creating helm chart for python-app

![image](https://github.com/user-attachments/assets/cb97cdb9-97ba-458a-b223-2809d9a455c8)

## check helm pod on k8s dashboard

![image](https://github.com/user-attachments/assets/8ae74a93-690b-440d-b3d6-0b89d28885d8)

## check that python-app is available

![image](https://github.com/user-attachments/assets/0a0bda8c-f619-4b5f-bc2c-aea0e73133c1)

![image](https://github.com/user-attachments/assets/cf298d8c-dfec-4822-bc25-cd179345a45c)

## kubectl get po,svc

![image](https://github.com/user-attachments/assets/f708f8da-cfc7-465d-8c80-d91534a8646f)

# Task 2

## `helm lint` after adding pre-install and post-install hooks

![image](https://github.com/user-attachments/assets/525efe89-c597-439c-8f94-0db14abe4378)

## helm install --dry-run helm-hooks ./helm-python-app

```bash
[~/innop/spr2025/dev-ops/S25-core-course-labs/k8s]$ helm install --dry-run helm-hooks ./helm-python-app
NAME: helm-hooks
LAST DEPLOYED: Wed Feb 26 12:26:10 2025
NAMESPACE: default
STATUS: pending-install
REVISION: 1
HOOKS:
---
# Source: helm-python-app/templates/tests/test-connection.yaml
apiVersion: v1
kind: Pod
metadata:
  name: "helm-hooks-helm-python-app-test-connection"
  labels:
    helm.sh/chart: helm-python-app-0.1.0
    app.kubernetes.io/name: helm-python-app
    app.kubernetes.io/instance: helm-hooks
    app.kubernetes.io/version: "1.16.0"
    app.kubernetes.io/managed-by: Helm
  annotations:
    "helm.sh/hook": test
spec:
  containers:
    - name: wget
      image: busybox
      command: ['wget']
      args: ['helm-hooks-helm-python-app:8080']
  restartPolicy: Never
---
# Source: helm-python-app/templates/post-install-hook.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: post-install-hook
  annotations:
    "helm.sh/hook": post-install
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: post-install-job
          image: busybox
          command: ["sh", "-c", "echo post-install-hook running; sleep 20"]
---
# Source: helm-python-app/templates/pre-install-hook.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: pre-install-hook
  annotations:
    "helm.sh/hook": pre-install
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: pre-install-job
          image: busybox
          command: ["sh", "-c", "echo pre-install-hook running; sleep 20"]
MANIFEST:
---
# Source: helm-python-app/templates/serviceaccount.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: helm-hooks-helm-python-app
  labels:
    helm.sh/chart: helm-python-app-0.1.0
    app.kubernetes.io/name: helm-python-app
    app.kubernetes.io/instance: helm-hooks
    app.kubernetes.io/version: "1.16.0"
    app.kubernetes.io/managed-by: Helm
automountServiceAccountToken: true
---
# Source: helm-python-app/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: helm-hooks-helm-python-app
  labels:
    helm.sh/chart: helm-python-app-0.1.0
    app.kubernetes.io/name: helm-python-app
    app.kubernetes.io/instance: helm-hooks
    app.kubernetes.io/version: "1.16.0"
    app.kubernetes.io/managed-by: Helm
spec:
  type: ClusterIP
  ports:
    - port: 8080
      targetPort: http
      protocol: TCP
      name: http
  selector:
    app.kubernetes.io/name: helm-python-app
    app.kubernetes.io/instance: helm-hooks
---
# Source: helm-python-app/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: helm-hooks-helm-python-app
  labels:
    helm.sh/chart: helm-python-app-0.1.0
    app.kubernetes.io/name: helm-python-app
    app.kubernetes.io/instance: helm-hooks
    app.kubernetes.io/version: "1.16.0"
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: helm-python-app
      app.kubernetes.io/instance: helm-hooks
  template:
    metadata:
      labels:
        helm.sh/chart: helm-python-app-0.1.0
        app.kubernetes.io/name: helm-python-app
        app.kubernetes.io/instance: helm-hooks
        app.kubernetes.io/version: "1.16.0"
        app.kubernetes.io/managed-by: Helm
    spec:
      serviceAccountName: helm-hooks-helm-python-app
      containers:
        - name: helm-python-app
          image: "adeepresession/app_python:v1.1"
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 8080
              protocol: TCP
          livenessProbe:
            httpGet:
              path: /
              port: http
          readinessProbe:
            httpGet:
              path: /
              port: http

NOTES:
1. Get the application URL by running these commands:
  export POD_NAME=$(kubectl get pods --namespace default -l "app.kubernetes.io/name=helm-python-app,app.kubernetes.io/instance=helm-hooks" -o jsonpath="{.items[0].metadata.name}")
  export CONTAINER_PORT=$(kubectl get pod --namespace default $POD_NAME -o jsonpath="{.spec.containers[0].ports[0].containerPort}")
  echo "Visit http://127.0.0.1:8080 to use your application"
  kubectl --namespace default port-forward $POD_NAME 8080:$CONTAINER_PORT

```

## kubectl get po

![image](https://github.com/user-attachments/assets/029272e0-70a8-466d-854c-498504b4999f)

## kubectl describe po post-install-hook-4b2rz

```bash
[~/innop/spr2025/dev-ops/S25-core-course-labs/k8s]$ kubectl describe po post-install-hook-4b2rz
Name:             post-install-hook-4b2rz
Namespace:        default
Priority:         0
Service Account:  default
Node:             minikube/192.168.49.2
Start Time:       Wed, 26 Feb 2025 12:25:29 +0300
Labels:           batch.kubernetes.io/controller-uid=7e62e467-12f5-4d6c-b99c-49e9189cdb9f
                  batch.kubernetes.io/job-name=post-install-hook
                  controller-uid=7e62e467-12f5-4d6c-b99c-49e9189cdb9f
                  job-name=post-install-hook
Annotations:      <none>
Status:           Succeeded
IP:               10.244.0.30
IPs:
  IP:           10.244.0.30
Controlled By:  Job/post-install-hook
Containers:
  post-install-job:
    Container ID:  docker://7d0b062e1fbdf15c857eb4ddc63c5ba4340c2bfd0eea42884421018236a0bb5c
    Image:         busybox
    Image ID:      docker-pullable://busybox@sha256:498a000f370d8c37927118ed80afe8adc38d1edcbfc071627d17b25c88efcab0
    Port:          <none>
    Host Port:     <none>
    Command:
      sh
      -c
      echo post-install-hook running; sleep 20
    State:          Terminated
      Reason:       Completed
      Exit Code:    0
      Started:      Wed, 26 Feb 2025 12:25:31 +0300
      Finished:     Wed, 26 Feb 2025 12:25:51 +0300
    Ready:          False
    Restart Count:  0
    Environment:    <none>
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-nghns (ro)
Conditions:
  Type                        Status
  PodReadyToStartContainers   False
  Initialized                 True
  Ready                       False
  ContainersReady             False
  PodScheduled                True
Volumes:
  kube-api-access-nghns:
    Type:                    Projected (a volume that contains injected data from multiple sources)
    TokenExpirationSeconds:  3607
    ConfigMapName:           kube-root-ca.crt
    ConfigMapOptional:       <nil>
    DownwardAPI:             true
QoS Class:                   BestEffort
Node-Selectors:              <none>
Tolerations:                 node.kubernetes.io/not-ready:NoExecute op=Exists for 300s
                             node.kubernetes.io/unreachable:NoExecute op=Exists for 300s
Events:
  Type    Reason     Age    From               Message
  ----    ------     ----   ----               -------
  Normal  Scheduled  2m56s  default-scheduler  Successfully assigned default/post-install-hook-4b2rz to minikube
  Normal  Pulling    2m56s  kubelet            Pulling image "busybox"
  Normal  Pulled     2m54s  kubelet            Successfully pulled image "busybox" in 1.554s (1.554s including waiting). Image size: 4269678 bytes.
  Normal  Created    2m54s  kubelet            Created container post-install-job
  Normal  Started    2m54s  kubelet            Started container post-install-job
```

## kubectl describe po pre-install-hook-p4jmr

```bash
[~/innop/spr2025/dev-ops/S25-core-course-labs/k8s]$ kubectl describe po pre-install-hook-p4jmr
Name:             pre-install-hook-p4jmr
Namespace:        default
Priority:         0
Service Account:  default
Node:             minikube/192.168.49.2
Start Time:       Wed, 26 Feb 2025 12:25:04 +0300
Labels:           batch.kubernetes.io/controller-uid=ee3ddbc3-e610-4d57-9c3c-58bee5e245e1
                  batch.kubernetes.io/job-name=pre-install-hook
                  controller-uid=ee3ddbc3-e610-4d57-9c3c-58bee5e245e1
                  job-name=pre-install-hook
Annotations:      <none>
Status:           Succeeded
IP:               10.244.0.28
IPs:
  IP:           10.244.0.28
Controlled By:  Job/pre-install-hook
Containers:
  pre-install-job:
    Container ID:  docker://8c9b9b92ea89b3cd6163630b4c39c5ed6d28d2b93ca598955e3392d4addb13e3
    Image:         busybox
    Image ID:      docker-pullable://busybox@sha256:498a000f370d8c37927118ed80afe8adc38d1edcbfc071627d17b25c88efcab0
    Port:          <none>
    Host Port:     <none>
    Command:
      sh
      -c
      echo pre-install-hook running; sleep 20
    State:          Terminated
      Reason:       Completed
      Exit Code:    0
      Started:      Wed, 26 Feb 2025 12:25:06 +0300
      Finished:     Wed, 26 Feb 2025 12:25:26 +0300
    Ready:          False
    Restart Count:  0
    Environment:    <none>
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-4mm4t (ro)
Conditions:
  Type                        Status
  PodReadyToStartContainers   False
  Initialized                 True
  Ready                       False
  ContainersReady             False
  PodScheduled                True
Volumes:
  kube-api-access-4mm4t:
    Type:                    Projected (a volume that contains injected data from multiple sources)
    TokenExpirationSeconds:  3607
    ConfigMapName:           kube-root-ca.crt
    ConfigMapOptional:       <nil>
    DownwardAPI:             true
QoS Class:                   BestEffort
Node-Selectors:              <none>
Tolerations:                 node.kubernetes.io/not-ready:NoExecute op=Exists for 300s
                             node.kubernetes.io/unreachable:NoExecute op=Exists for 300s
Events:
  Type    Reason     Age    From               Message
  ----    ------     ----   ----               -------
  Normal  Scheduled  3m49s  default-scheduler  Successfully assigned default/pre-install-hook-p4jmr to minikube
  Normal  Pulling    3m49s  kubelet            Pulling image "busybox"
  Normal  Pulled     3m47s  kubelet            Successfully pulled image "busybox" in 1.56s (1.56s including waiting). Image size: 4269678 bytes.
  Normal  Created    3m47s  kubelet            Created container pre-install-job
  Normal  Started    3m47s  kubelet            Started container pre-install-job
```

## adding annotation to delete hooks on success

```yaml
annotations:
    "helm.sh/hook": post-install
    "helm.sh/hook-delete-policy": hook-succeeded
```

now hooks are automatically cleared up

![image](https://github.com/user-attachments/assets/d94308f1-d312-4a74-b3ba-455a67e1d6fb)
