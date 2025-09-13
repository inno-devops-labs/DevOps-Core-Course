# Task 1

## minikube start

```bash
[~/innop/spr2025/dev-ops/S25-core-course-labs/k8s]$ minikube start

😄  minikube v1.34.0 on Arch
🎉  minikube 1.35.0 is available! Download it: https://github.com/kubernetes/minikube/releases/tag/v1.35.0
💡  To disable this notice, run: 'minikube config set WantUpdateNotification false'

✨  Automatically selected the docker driver. Other choices: none, ssh
📌  Using Docker driver with root privileges
👍  Starting "minikube" primary control-plane node in "minikube" cluster
🚜  Pulling base image v0.0.45 ...
💾  Downloading Kubernetes v1.31.0 preload ...
    > preloaded-images-k8s-v18-v1...:  326.69 MiB / 326.69 MiB  100.00% 12.64 M
    > gcr.io/k8s-minikube/kicbase...:  487.90 MiB / 487.90 MiB  100.00% 12.24 M
🔥  Creating docker container (CPUs=2, Memory=2200MB) ...

❌  Exiting due to RSRC_DOCKER_STORAGE: Docker is out of disk space! (/var is at 100% of capacity). You can pass '--force' to skip this check.
💡  Suggestion:

    Try one or more of the following to free up space on the device:

    1. Run "docker system prune" to remove unused Docker data (optionally with "-a")
    2. Increase the storage allocated to Docker for Desktop by clicking on:
    Docker icon > Preferences > Resources > Disk Image Size
    3. Run "minikube ssh -- docker system prune" if using the Docker container runtime
🍿  Related issue: https://github.com/kubernetes/minikube/issues/9024

```

## switch kubectl context to minikube

```bash
[~/innop/spr2025/dev-ops/S25-core-course-labs/k8s]$ kubectl config use-context minikube

Switched to context "minikube".

```

## create app-python deployment

```bash

[~/innop/spr2025/dev-ops/S25-core-course-labs/k8s]$ kubectl create deployment app-python --image=adeepresession/app_python:v1.1

deployment.apps/app-python created

```

## expose app-python port

```bash

[~/innop/spr2025/dev-ops/S25-core-course-labs/k8s]$ kubectl expose deployment app-python --type=LoadBalancer --port=8080

service/app-python exposed

```

## creating a route to services

```bash

[~/innop/spr2025/dev-ops/S25-core-course-labs/k8s]$ minikube tunnel

Status:
        machine: minikube
        pid: 1569246
        route: 10.96.0.0/12 -> 192.168.49.2
        minikube: Running
        services: [app-python]
    errors:
                minikube: no errors
                router: no errors
                loadbalancer emulator: no errors
```

## check pods and services

```bash
[~/innop/spr2025/dev-ops/S25-core-course-labs/k8s]$ kubectl get pods,svc

NAME                              READY   STATUS    RESTARTS   AGE
pod/app-python-778c948c88-2hc7h   1/1     Running   0          3m51s

NAME                 TYPE           CLUSTER-IP     EXTERNAL-IP    PORT(S)          AGE
service/app-python   LoadBalancer   10.101.80.19   10.101.80.19   8080:31598/TCP   2m43s
service/kubernetes   ClusterIP      10.96.0.1      <none>         443/TCP          11m

```

## get a response from the app

```bash
[~/innop/spr2025/dev-ops/S25-core-course-labs/k8s]$ curl 10.101.80.19:8080

<!doctype html>
<html lang="en">

<head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Python web app</title>
</head>

<body>
        <h1>Current Time in Moscow</h1>
        <p>2025-02-24 12:04:48</p>
</body>

</html>
```

## clean up services and pods

```bash

[~/innop/spr2025/dev-ops/S25-core-course-labs/k8s]$ kubectl delete deployment app-python
deployment.apps "app-python" deleted

[~/innop/spr2025/dev-ops/S25-core-course-labs/k8s]$ kubectl delete service app-python
service "app-python" deleted

[~/innop/spr2025/dev-ops/S25-core-course-labs/k8s]$ kubectl get svc,pods
NAME                 TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)   AGE
service/kubernetes   ClusterIP   10.96.0.1    <none>        443/TCP   53m


```

# Task 2

## creating services from manifests

```bash

[~/innop/spr2025/dev-ops/S25-core-course-labs/k8s]$ kubectl apply -f app-python
deployment.apps/app-python created
service/app-python created

[~/innop/spr2025/dev-ops/S25-core-course-labs/k8s]$ kubectl get svc,pods
NAME                 TYPE           CLUSTER-IP      EXTERNAL-IP     PORT(S)          AGE
service/app-python   LoadBalancer   10.101.107.56   10.101.107.56   8080:30613/TCP   56s
service/kubernetes   ClusterIP      10.96.0.1       <none>          443/TCP          55m

NAME                            READY   STATUS    RESTARTS   AGE
pod/app-python-f69df9f7-jkxl2   1/1     Running   0          56s
pod/app-python-f69df9f7-szb6h   1/1     Running   0          56s
pod/app-python-f69df9f7-z7v5x   1/1     Running   0          56s

```

## getting service urls

```bash

[~/innop/spr2025/dev-ops/S25-core-course-labs/k8s]$ minikube service --all
|-----------|------------|-------------|---------------------------|
| NAMESPACE |    NAME    | TARGET PORT |            URL            |
|-----------|------------|-------------|---------------------------|
| default   | app-python | http/8080   | http://192.168.49.2:30613 |
|-----------|------------|-------------|---------------------------|
|-----------|------------|-------------|--------------|
| NAMESPACE |    NAME    | TARGET PORT |     URL      |
|-----------|------------|-------------|--------------|
| default   | kubernetes |             | No node port |
|-----------|------------|-------------|--------------|
😿  service default/kubernetes has no node port
❗  Services [default/kubernetes] have type "ClusterIP" not meant to be exposed, however for local development minikube allows you to access this !
🎉  Opening service default/app-python in default browser...
Opening in existing browser session.
🏃  Starting tunnel for service kubernetes.
|-----------|------------|-------------|------------------------|
| NAMESPACE |    NAME    | TARGET PORT |          URL           |
|-----------|------------|-------------|------------------------|
| default   | kubernetes |             | http://127.0.0.1:44265 |
|-----------|------------|-------------|------------------------|
🎉  Opening service default/kubernetes in default browser...
Opening in existing browser session.
❗  Because you are using a Docker driver on linux, the terminal needs to be open to run it.

```

## check that python app is available

```bash

[~/innop/spr2025/dev-ops/S25-core-course-labs/k8s]$ curl http://192.168.49.2:30613
<!doctype html>
<html lang="en">

<head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <title>Python web app</title>
</head>

<body>
        <h1>Current Time in Moscow</h1>
        <p>2025-02-24 12:16:02</p>
</body>

</html>%


```
