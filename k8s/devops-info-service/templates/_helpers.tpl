{{/*
Resolve the Kubernetes Secret name for application credentials.
*/}}
{{- define "devops-info-service.secretName" -}}
{{- default (printf "%s-secret" (include "common-lib.fullname" .)) .Values.secrets.name -}}
{{- end -}}

{{/*
Resolve the service account name used by the workload.
*/}}
{{- define "devops-info-service.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "common-lib.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{/*
Resolve ConfigMap names used for Lab 12.
*/}}
{{- define "devops-info-service.fileConfigMapName" -}}
{{- printf "%s-config" (include "common-lib.fullname" .) -}}
{{- end -}}

{{- define "devops-info-service.envConfigMapName" -}}
{{- printf "%s-env" (include "common-lib.fullname" .) -}}
{{- end -}}

{{/*
Resolve the PersistentVolumeClaim name for visits storage.
*/}}
{{- define "devops-info-service.pvcName" -}}
{{- printf "%s-data" (include "common-lib.fullname" .) -}}
{{- end -}}

{{/*
Common environment variables shared by the application container.
*/}}
{{- define "devops-info-service.envVars" -}}
{{- range .Values.env }}
- name: {{ .name }}
  value: {{ .value | quote }}
{{- end }}
{{- if .Values.vault.enabled }}
- name: VAULT_SECRETS_FILE
  value: {{ printf "%s/%s" .Values.vault.secretVolumePath .Values.vault.injectFileName | quote }}
- name: VAULT_SECRET_PATH
  value: {{ .Values.vault.secretPath | quote }}
{{- end }}
{{- end -}}

{{/*
Vault Agent Injector annotations for file-based secret rendering.
*/}}
{{- define "devops-info-service.vaultAnnotations" -}}
vault.hashicorp.com/agent-inject: "true"
vault.hashicorp.com/agent-inject-status: "update"
vault.hashicorp.com/auth-path: {{ .Values.vault.authPath | quote }}
vault.hashicorp.com/role: {{ .Values.vault.role | quote }}
vault.hashicorp.com/secret-volume-path: {{ .Values.vault.secretVolumePath | quote }}
vault.hashicorp.com/agent-inject-secret-config: {{ .Values.vault.secretPath | quote }}
vault.hashicorp.com/agent-inject-file-config: {{ .Values.vault.injectFileName | quote }}
{{- if .Values.vault.staticSecretRenderInterval }}
vault.hashicorp.com/template-static-secret-render-interval: {{ .Values.vault.staticSecretRenderInterval | quote }}
{{- end }}
vault.hashicorp.com/agent-inject-template-config: |
  {{ "{{- with secret " }}{{ .Values.vault.secretPath | quote }}{{ " -}}" }}
  APP_USERNAME={{ "{{ .Data.data.username }}" }}
  APP_PASSWORD={{ "{{ .Data.data.password }}" }}
  API_TOKEN={{ "{{ .Data.data.api_token }}" }}
  {{ "{{- end }}" }}
{{- if .Values.vault.agentInjectCommand }}
vault.hashicorp.com/agent-inject-command-config: {{ .Values.vault.agentInjectCommand | quote }}
{{- end }}
{{- end -}}

{{/*
Resolve Argo Rollouts-related resource names.
*/}}
{{- define "devops-info-service.rolloutName" -}}
{{- include "common-lib.fullname" . -}}
{{- end -}}

{{- define "devops-info-service.canaryServiceName" -}}
{{- printf "%s-%s" (include "common-lib.fullname" .) .Values.rollout.canary.canaryServiceSuffix -}}
{{- end -}}

{{- define "devops-info-service.stableServiceName" -}}
{{- printf "%s-%s" (include "common-lib.fullname" .) .Values.rollout.canary.stableServiceSuffix -}}
{{- end -}}

{{- define "devops-info-service.previewServiceName" -}}
{{- printf "%s-%s" (include "common-lib.fullname" .) .Values.rollout.blueGreen.previewServiceSuffix -}}
{{- end -}}

{{- define "devops-info-service.analysisTemplateName" -}}
{{- printf "%s-%s" (include "common-lib.fullname" .) .Values.rollout.analysis.templateSuffix -}}
{{- end -}}
