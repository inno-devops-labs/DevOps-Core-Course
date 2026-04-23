# Lab 13 - Local Validation Evidence

Generated on `2026-04-23T23:32:51+03:00`.

This file contains only local, reproducible checks from the current workspace.

## Repository Context

```bash
$ git branch --show-current
lab13
```

```bash
$ git rev-parse --short HEAD
711d355
```

## Tool Versions

```bash
$ helm version
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.25.8", KubeClientVersion:"v1.35"}
```

## Helm Validation

```bash
$ helm lint k8s/devops-info
==> Linting k8s/devops-info
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

```bash
$ helm template devops-info k8s/devops-info -f k8s/devops-info/values.yaml >/dev/null && echo 'base render: ok'
base render: ok
```

```bash
$ helm template devops-info-dev k8s/devops-info -f k8s/devops-info/values.yaml -f k8s/devops-info/values-dev.yaml >/dev/null && echo 'dev render: ok'
dev render: ok
```

```bash
$ helm template devops-info-prod k8s/devops-info -f k8s/devops-info/values.yaml -f k8s/devops-info/values-prod.yaml >/dev/null && echo 'prod render: ok'
prod render: ok
```

## ArgoCD Manifests

```bash
$ sed -n '1,200p' k8s/argocd/application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: devops-info
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: https://github.com/ebortsov/DevOps-Core-Course.git
    targetRevision: lab13
    path: k8s/devops-info
    helm:
      releaseName: devops-info
      valueFiles:
        - values.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: devops-gitops
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
```

```bash
$ sed -n '1,200p' k8s/argocd/application-dev.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: devops-info-dev
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: https://github.com/ebortsov/DevOps-Core-Course.git
    targetRevision: lab13
    path: k8s/devops-info
    helm:
      releaseName: devops-info-dev
      valueFiles:
        - values.yaml
        - values-dev.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: dev
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

```bash
$ sed -n '1,200p' k8s/argocd/application-prod.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: devops-info-prod
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: https://github.com/ebortsov/DevOps-Core-Course.git
    targetRevision: lab13
    path: k8s/devops-info
    helm:
      releaseName: devops-info-prod
      valueFiles:
        - values.yaml
        - values-prod.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: prod
  syncPolicy:
    syncOptions:
      - CreateNamespace=true
```

```bash
$ sed -n '1,240p' k8s/argocd/applicationset.yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: devops-info-envs
  namespace: argocd
spec:
  goTemplate: true
  goTemplateOptions:
    - missingkey=error
  generators:
    - list:
        elements:
          - env: dev
            namespace: dev
            releaseName: devops-info-dev
            valuesFile: values-dev.yaml
            autoSync: "true"
          - env: prod
            namespace: prod
            releaseName: devops-info-prod
            valuesFile: values-prod.yaml
            autoSync: "false"
  template:
    metadata:
      name: 'devops-info-{{ .env }}'
      finalizers:
        - resources-finalizer.argocd.argoproj.io
    spec:
      project: default
      source:
        repoURL: https://github.com/ebortsov/DevOps-Core-Course.git
        targetRevision: lab13
        path: k8s/devops-info
        helm:
          releaseName: '{{ .releaseName }}'
          valueFiles:
            - values.yaml
            - '{{ .valuesFile }}'
      destination:
        server: https://kubernetes.default.svc
        namespace: '{{ .namespace }}'
      syncPolicy:
        syncOptions:
          - CreateNamespace=true
  templatePatch: |
    {{- if eq .autoSync "true" }}
    spec:
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
    {{- end }}
```

