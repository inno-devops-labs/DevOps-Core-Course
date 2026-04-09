{{- define "devops-info-service.secretName" -}}
{{- if .Values.secret.name -}}
{{- .Values.secret.name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-secret" (include "common-lib.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "devops-info-service.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- if .Values.serviceAccount.name -}}
{{- .Values.serviceAccount.name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- include "common-lib.fullname" . -}}
{{- end -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{- define "devops-info-service.envVars" -}}
- name: PORT
  value: {{ .Values.env.port | quote }}
- name: SERVICE_NAME
  value: {{ .Values.env.serviceName | quote }}
- name: SERVICE_VERSION
  value: {{ .Values.env.serviceVersion | quote }}
- name: SERVICE_DESCRIPTION
  value: {{ .Values.env.serviceDescription | quote }}
- name: SERVICE_FRAMEWORK
  value: {{ .Values.env.serviceFramework | quote }}
{{- end -}}

{{- define "devops-info-service.vaultAnnotations" -}}
{{- if .Values.vault.enabled -}}
vault.hashicorp.com/agent-inject: "true"
vault.hashicorp.com/role: {{ .Values.vault.role | quote }}
vault.hashicorp.com/agent-inject-secret-config: {{ .Values.vault.secretPath | quote }}
vault.hashicorp.com/agent-inject-template-config: |
  {{`{{- with secret "`}}{{ .Values.vault.secretPath }}{{`" -}}`}}
  APP_USERNAME={{`{{ .Data.data.username }}`}}
  APP_PASSWORD={{`{{ .Data.data.password }}`}}
  APP_API_KEY={{`{{ .Data.data.api_key }}`}}
  {{`{{- end }}`}}
{{- if .Values.vault.agentInjectCommand }}
vault.hashicorp.com/agent-inject-command-config: {{ .Values.vault.agentInjectCommand | quote }}
{{- end }}
{{- end -}}
{{- end -}}
