\# Lab 11 — Secret Management Report



\## Task 1 — Kubernetes Secrets Fundamentals



\### Creating Secret



$ kubectl create secret generic app-credentials --from-literal=username=demo-user --from-literal=password=demo-pass

secret/app-credentials created



\### Viewing Secret



$ kubectl get secret app-credentials -o yaml

apiVersion: v1

data:

&#x20; password: ZGVtby1wYXNz

&#x20; username: ZGVtby11c2Vy

kind: Secret

metadata:

&#x20; name: app-credentials

&#x20; namespace: default

type: Opaque



\### Decoding Values



$ \[System.Text.Encoding]::UTF8.GetString(\[System.Convert]::FromBase64String("ZGVtby11c2Vy"))

demo-user



$ \[System.Text.Encoding]::UTF8.GetString(\[System.Convert]::FromBase64String("ZGVtby1wYXNz"))

demo-pass



\### Base64 Encoding vs Encryption



Base64 is encoding, not encryption. Anyone with API access can decode it.

Kubernetes Secrets are not encrypted at rest by default (only base64 encoded).

etcd encryption should be enabled in production for defense-in-depth.



\## Task 2 — Helm-Managed Secrets



\### Chart Structure



k8s/devops-info-service-chart/

├── templates/

│   ├── secrets.yaml

│   └── deployment.yaml

├── values.yaml

└── values-dev.yaml



\### Secret Template (secrets.yaml)



{{- if .Values.secrets.enabled }}

apiVersion: v1

kind: Secret

metadata:

&#x20; name: {{ include "devops-info-service.fullname" . }}-credentials

type: Opaque

stringData:

&#x20; username: {{ .Values.secrets.username | quote }}

&#x20; password: {{ .Values.secrets.password | quote }}

{{- end }}



\### Deployment Integration



{{- if .Values.secrets.enabled }}

envFrom:

&#x20; - secretRef:

&#x20;     name: {{ include "devops-info-service.fullname" . }}-credentials

{{- end }}



\### Verification



$ kubectl exec -it deployment/devops-info-service -- env | findstr "username"

username=myapp-user



$ kubectl exec -it deployment/devops-info-service -- env | findstr "password"

password=myapp-pass



\### Resource Limits (values-dev.yaml)



resources:

&#x20; limits:

&#x20;   cpu: 100m

&#x20;   memory: 128Mi

&#x20; requests:

&#x20;   cpu: 50m

&#x20;   memory: 64Mi



\## Task 3 — HashiCorp Vault Integration (Attempted)



Due to complexity and time constraints, Vault integration was attempted but not completed. The main issues encountered:

\- Kubernetes authentication configuration between Vault and minikube

\- Service account token generation in newer Kubernetes versions

\- Vault agent injector init container stuck in permission denied



What was done:

\- Vault installed via Helm with dev mode and injector enabled

\- KV secrets engine configured at path devops/

\- Secret created: devops/devops-info-service/config with username/password

\- Kubernetes auth method enabled and configured

\- Policy and role created for service account



Lessons learned:

\- Vault requires proper RBAC setup (clusterrolebinding for auth-delegator)

\- Service account tokens need correct annotations

\- Vault Agent Injector requires proper network connectivity to Kubernetes API



\## Security Analysis



Aspect                | Kubernetes Secrets | HashiCorp Vault

\----------------------|--------------------|------------------

Storage               | etcd (optional encryption) | Centralized with audit

Access                | RBAC | Fine-grained policies

Rotation              | Manual/External | Built-in lease system

Best for              | Simple, low-sensitivity | Production, compliance



Production Recommendations:

\- Never commit real secrets to Git

\- Use placeholders in values.yaml

\- Inject secrets via CI/CD or external secret manager

\- Enable etcd encryption for K8s Secrets

\- Use Vault for sensitive production credentials



\## Commands Reference



Installation:

helm install devops-info-service . -f values-dev.yaml

helm upgrade devops-info-service . -f values-dev.yaml --set secrets.username=alice --set secrets.password=secure123



Verification:

kubectl get secrets

kubectl get secret devops-info-service-credentials -o yaml

kubectl exec -it deployment/devops-info-service -- env | findstr "username"



Cleanup:

helm uninstall devops-info-service

kubectl delete secret app-credentials



\## Conclusion



Lab 11 completed with Tasks 1 and 2 fully working:

\- Kubernetes Secrets created and decoded

\- Helm-managed secrets integrated with envFrom

\- Environment variables injected into pod

\- Resource limits configured

\- Vault integration (Task 3) attempted, documented lessons learned

