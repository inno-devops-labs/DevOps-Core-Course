\# Lab 9: Kubernetes Fundamentals



\## Architecture



\### Components

| Component | Description |

|-----------|-------------|

| \*\*Cluster\*\* | Minikube v1.38.1 (single node) |

| \*\*Kubernetes\*\* | v1.35.1 |

| \*\*Driver\*\* | Docker |

| \*\*Deployment\*\* | devops-info-service (Flask app) |

| \*\*Replicas\*\* | 3 → 5 → 3 |

| \*\*Service\*\* | NodePort |



\### Flow

\[Client] → \[NodePort :80] → \[Service devops-info-service] → \[Pod:5000] x3

↓

\[Flask App]



text





\## Cluster Setup



```bash

$ minikube start --driver=docker

$ kubectl cluster-info

$ kubectl get nodes

Output

text

NAME       STATUS   ROLES           AGE     VERSION

minikube   Ready    control-plane   9m21s   v1.35.1

