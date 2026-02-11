# Helm

This document records the Helm fundamentals and the chart implementation for the Kubernetes application, including installation, chart creation, hooks, and validation outputs.

Dudinov Mikhail @ez4gotit

## Installing Helm

```sh
wget https://get.helm.sh/helm-v3.17.1-linux-amd64.tar.gz
tar zxvf helm-v3.17.1-linux-amd64.tar.gz
sudo mv linux-amd64/helm /usr/local/bin/helm
```
![alt text](image-2.png)

## Create Helm Chart
```sh
cd k8s/
helm create helm-python
```

### Change `values.yaml`
```yaml
image:
  repository: petrel312/flask_app
  tag: "latest"
service:
  type: ClusterIP
  port: 5000
```

```sh
helm install helm-python ./helm-python
```
```text
NAME: helm-python
LAST DEPLOYED: Wed Mar 12 04:58:22 2025
NAMESPACE: default
STATUS: deployed
REVISION: 1
NOTES:
1. Get the application URL by running these commands:
  export POD_NAME=$(kubectl get pods --namespace default -l "app.kubernetes.io/name=helm-python,app.kubernetes.io/instance=helm-python" -o jsonpath="{.items[0].metadata.name}")
  export CONTAINER_PORT=$(kubectl get pod --namespace default $POD_NAME -o jsonpath="{.spec.containers[0].ports[0].containerPort}")
  echo "Visit http://127.0.0.1:8080 to use your application"
  kubectl --namespace default port-forward $POD_NAME 8080:$CONTAINER_PORT
```

Check:
```sh
helm list
```
![alt text](image-3.png)

## Access the Application

```sh
minikube service helm-python
```
```text
|-----------|-------------|-------------|--------------|
| NAMESPACE |    NAME     | TARGET PORT |     URL      |
|-----------|-------------|-------------|--------------|
| default   | helm-python |             | No node port |
|-----------|-------------|-------------|--------------|
service default/helm-python has no node port
Services [default/helm-python] have type "ClusterIP" not meant to be exposed, however for local development minikube allows you to access this.
Starting tunnel for service helm-python.
|-----------|-------------|-------------|------------------------|
| NAMESPACE |    NAME     | TARGET PORT |          URL           |
|-----------|-------------|-------------|------------------------|
| default   | helm-python |             | http://127.0.0.1:37613 |
|-----------|-------------|-------------|------------------------|
Opening service default/helm-python in default browser...
http://127.0.0.1:37613
Because you are using a Docker driver on linux, the terminal needs to be open to run it.
```
![alt text](image-4.png)

## Output for `get pods,svc`
```text
NAME                              READY   STATUS    RESTARTS      AGE
pod/helm-python-9966b5d8b-nx9n4   1/1     Running   0             11m

NAME                  TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
service/helm-python   ClusterIP   10.110.23.151   <none>        5000/TCP         11m
service/kubernetes    ClusterIP   10.96.0.1       <none>        443/TCP          9d
```

## Chart Hooks

### Create pre and post install .yaml files
```yaml
piVersion: v1
kind: Pod
metadata:
   name: preinstall-hook
   annotations:
       "helm.sh/hook": "pre-install"
       "helm.sh/hook-delete-policy": "before-hook-creation"
spec:
  containers:
  - name: pre-install-container
    image: busybox
    imagePullPolicy: IfNotPresent
    command: ['sh', '-c', 'echo The pre-install hook is running && sleep 20' ]
  restartPolicy: Never
  terminationGracePeriodSeconds: 0
```
```yaml
apiVersion: v1
kind: Pod
metadata:
   name: postinstall-hook
   annotations:
       "helm.sh/hook": "post-install"
       "helm.sh/hook-delete-policy": "before-hook-creation"
spec:
  containers:
  - name: post-install-container
    image: busybox
    imagePullPolicy: Always
    command: ['sh', '-c', 'echo The post-install hook is running && sleep 15' ]
  restartPolicy: Never
  terminationGracePeriodSeconds: 0

```

### Troubleshoot Hooks
```sh
helm lint helm-python
```
```text
==> Linting helm-python
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

```sh
helm install --dry-run helm-hooks helm-python
```
```text
NAME: helm-hooks
LAST DEPLOYED: Wed Mar 12 05:48:18 2025
NAMESPACE: default
STATUS: pending-install
REVISION: 1
HOOKS:
---
# Source: helm-python/templates/post-install.yaml
apiVersion: v1
kind: Pod
metadata:
   name: postinstall-hook
   annotations:
       "helm.sh/hook": "post-install"
       "helm.sh/hook-delete-policy": "before-hook-creation"
spec:
  containers:
  - name: post-install-container
    image: busybox
    imagePullPolicy: Always
    command: ['sh', '-c', 'echo The post-install hook is running && sleep 15' ]
  restartPolicy: Never
  terminationGracePeriodSeconds: 0
---
# Source: helm-python/templates/pre-install.yaml
apiVersion: v1
kind: Pod
metadata:
   name: preinstall-hook
   annotations:
       "helm.sh/hook": "pre-install"
       "helm.sh/hook-delete-policy": "before-hook-creation"
spec:
  containers:
  - name: pre-install-container
    image: busybox
    imagePullPolicy: IfNotPresent
    command: ['sh', '-c', 'echo The pre-install hook is running && sleep 20' ]
  restartPolicy: Never
  terminationGracePeriodSeconds: 0
---
# Source: helm-python/templates/tests/test-connection.yaml
apiVersion: v1
kind: Pod
metadata:
  name: "helm-hooks-helm-python-test-connection"
  labels:
    helm.sh/chart: helm-python-0.1.0
    app.kubernetes.io/name: helm-python
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
      args: ['helm-hooks-helm-python:5000']
  restartPolicy: Never
MANIFEST:
---
# Source: helm-python/templates/serviceaccount.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: helm-hooks-helm-python
  labels:
    helm.sh/chart: helm-python-0.1.0
    app.kubernetes.io/name: helm-python
    app.kubernetes.io/instance: helm-hooks
    app.kubernetes.io/version: "1.16.0"
    app.kubernetes.io/managed-by: Helm
automountServiceAccountToken: true
---
# Source: helm-python/templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: helm-hooks-helm-python
  labels:
    helm.sh/chart: helm-python-0.1.0
    app.kubernetes.io/name: helm-python
    app.kubernetes.io/instance: helm-hooks
    app.kubernetes.io/version: "1.16.0"
    app.kubernetes.io/managed-by: Helm
spec:
  type: ClusterIP
  ports:
    - port: 5000
      targetPort: http
      protocol: TCP
      name: http
  selector:
    app.kubernetes.io/name: helm-python
    app.kubernetes.io/instance: helm-hooks
---
# Source: helm-python/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: helm-hooks-helm-python
  labels:
    helm.sh/chart: helm-python-0.1.0
    app.kubernetes.io/name: helm-python
    app.kubernetes.io/instance: helm-hooks
    app.kubernetes.io/version: "1.16.0"
    app.kubernetes.io/managed-by: Helm
spec:
  replicas: 1
  selector:
    matchLabels:
      app.kubernetes.io/name: helm-python
      app.kubernetes.io/instance: helm-hooks
  template:
    metadata:
      labels:
        helm.sh/chart: helm-python-0.1.0
        app.kubernetes.io/name: helm-python
        app.kubernetes.io/instance: helm-hooks
        app.kubernetes.io/version: "1.16.0"
        app.kubernetes.io/managed-by: Helm
    spec:
      serviceAccountName: helm-hooks-helm-python
      containers:
        - name: helm-python
          image: "petrel312/flask_app:latest"
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 5000
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
  export POD_NAME=$(kubectl get pods --namespace default -l "app.kubernetes.io/name=helm-python,app.kubernetes.io/instance=helm-hooks" -o jsonpath="{.items[0].metadata.name}")
  export CONTAINER_PORT=$(kubectl get pod --namespace default $POD_NAME -o jsonpath="{.spec.containers[0].ports[0].containerPort}")
  echo "Visit http://127.0.0.1:8080 to use your application"
  kubectl --namespace default port-forward $POD_NAME 8080:$CONTAINER_PORT
```

```sh
helm install helm-hooks helm-python
kubectl get po
```
```text
NAME                                      READY   STATUS      RESTARTS      AGE
helm-hooks-helm-python-65499654d6-ds5fr   1/1     Running     0             36s
helm-python-9966b5d8b-nx9n4               1/1     Running     1 (13m ago)   51m
postinstall-hook                          0/1     Completed   0             36s
preinstall-hook                           0/1     Completed   0             59s
```

### Output
#### `kubectl get po`
```sh
kubectl get po
```
```text
NAME                                      READY   STATUS      RESTARTS      AGE
helm-hooks-helm-python-65499654d6-ds5fr   1/1     Running     0             36s
helm-python-9966b5d8b-nx9n4               1/1     Running     1 (13m ago)   51m
postinstall-hook                          0/1     Completed   0             36s
preinstall-hook                           0/1     Completed   0             59s
```

#### `kubectl describe po <preinstall_hook_name>`
```sh
kubectl describe po preinstall-hook
```
```text
Name:             preinstall-hook
Namespace:        default
Priority:         0
Service Account:  default
Node:             minikube/192.168.49.2
Start Time:       Wed, 12 Mar 2025 05:48:39 +0000
Labels:           <none>
Annotations:      helm.sh/hook: pre-install
                  helm.sh/hook-delete-policy: before-hook-creation
Status:           Succeeded
IP:               10.244.0.47
IPs:
  IP:  10.244.0.47
Containers:
  pre-install-container:
    Container ID:  docker://4fef06f34191cf14da12fe8eaa8ec6fbb3c265eca3ed1ca695bf896c9d8ebb7c
    Image:         busybox
    Image ID:      docker-pullable://busybox@sha256:498a000f370d8c37927118ed80afe8adc38d1edcbfc071627d17b25c88efcab0
    Port:          <none>
    Host Port:     <none>
    Command:
      sh
      -c
      echo The pre-install hook is running && sleep 20
    State:          Terminated
      Reason:       Completed
      Exit Code:    0
      Started:      Wed, 12 Mar 2025 05:48:40 +0000
      Finished:     Wed, 12 Mar 2025 05:49:00 +0000
    Ready:          False
    Restart Count:  0
    Environment:    <none>
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-hcmq8 (ro)
Conditions:
  Type                        Status
  PodReadyToStartContainers   False
  Initialized                 True
  Ready                       False
  ContainersReady             False
  PodScheduled                True
Volumes:
  kube-api-access-hcmq8:
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
  Type    Reason     Age   From               Message
  ----    ------     ----  ----               -------
  Normal  Scheduled  86s   default-scheduler  Successfully assigned default/preinstall-hook to minikube
  Normal  Pulled     85s   kubelet            Container image "busybox" already present on machine
  Normal  Created    85s   kubelet            Created container: pre-install-container
  Normal  Started    85s   kubelet            Started container pre-install-container
```

#### `kubectl describe po <postinstall_hook_name>`
```sh
kubectl describe po postinstall-hook
```
```text
Name:             postinstall-hook
Namespace:        default
Priority:         0
Service Account:  default
Node:             minikube/192.168.49.2
Start Time:       Wed, 12 Mar 2025 05:49:02 +0000
Labels:           <none>
Annotations:      helm.sh/hook: post-install
                  helm.sh/hook-delete-policy: before-hook-creation
Status:           Succeeded
IP:               10.244.0.49
IPs:
  IP:  10.244.0.49
Containers:
  post-install-container:
    Container ID:  docker://8507cb844c8a353b10fd0cd2bb0dcf876b1ffe927d9ed694ade0d0d50465dab5
    Image:         busybox
    Image ID:      docker-pullable://busybox@sha256:498a000f370d8c37927118ed80afe8adc38d1edcbfc071627d17b25c88efcab0
    Port:          <none>
    Host Port:     <none>
    Command:
      sh
      -c
      echo The post-install hook is running && sleep 15
    State:          Terminated
      Reason:       Completed
      Exit Code:    0
      Started:      Wed, 12 Mar 2025 05:49:05 +0000
      Finished:     Wed, 12 Mar 2025 05:49:20 +0000
    Ready:          False
    Restart Count:  0
    Environment:    <none>
    Mounts:
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-jwsnk (ro)
Conditions:
  Type                        Status
  PodReadyToStartContainers   False
  Initialized                 True
  Ready                       False
  ContainersReady             False
  PodScheduled                True
Volumes:
  kube-api-access-jwsnk:
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
  Normal  Scheduled  2m11s  default-scheduler  Successfully assigned default/postinstall-hook to minikube
  Normal  Pulling    2m10s  kubelet            Pulling image "busybox"
  Normal  Pulled     2m8s   kubelet            Successfully pulled image "busybox" in 2.201s (2.201s including waiting). Image size: 4269694 bytes.
  Normal  Created    2m8s   kubelet            Created container: post-install-container
  Normal  Started    2m8s   kubelet            Started container post-install-container
```

### Hook Delete Policy. Cleanup
Change `"helm.sh/hook-delete-policy"` to `hook-succeeded` in post and pre install files
```sh
vim helm-python/templates/post-install.yaml
vim helm-python/templates/pre-install.yaml
```
```yaml
"helm.sh/hook-delete-policy": "hook-succeeded"
```

```sh
kubectl get po
```
```text
NAME                                      READY   STATUS    RESTARTS      AGE
helm-hooks-helm-python-65499654d6-tvbsg   1/1     Running   0             39s
helm-python-9966b5d8b-nx9n4               1/1     Running   1 (22m ago)   60m
python-app-6d8dbb66cd-gnwwx               1/1     Running   0             15m
python-app-6d8dbb66cd-kksvb               1/1     Running   0             15m
python-app-6d8dbb66cd-rgg8s               1/1     Running   0             15m
python-app-6d8dbb66cd-t5p64               1/1     Running   0             15m
```

```sh
kubectl get pods,svc
```
![alt text](image-5.png)

## Checklist

- Helm installed and verified
- Helm chart created and configured
- Application deployed and accessible
- Hooks implemented and validated
- Hook deletion policy applied
- Outputs captured and documented