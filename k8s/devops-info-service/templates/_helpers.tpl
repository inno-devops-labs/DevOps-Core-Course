{{/*
Chart-local aliases around the shared library helpers.
*/}}
{{- define "devops-info-service.name" -}}
{{- include "common-lib.name" . -}}
{{- end -}}

{{- define "devops-info-service.fullname" -}}
{{- include "common-lib.fullname" . -}}
{{- end -}}

{{- define "devops-info-service.labels" -}}
{{- include "common-lib.labels" . -}}
{{- end -}}

{{- define "devops-info-service.selectorLabels" -}}
{{- include "common-lib.selectorLabels" . -}}
{{- end -}}

{{- define "devops-info-service.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "devops-info-service.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{- define "devops-info-service.secretName" -}}
{{- default (printf "%s-secret" (include "devops-info-service.fullname" .)) .Values.secret.name -}}
{{- end -}}

{{- define "devops-info-service.envVars" -}}
- name: HOST
  value: {{ .Values.app.host | quote }}
- name: PORT
  value: {{ .Values.app.port | quote }}
- name: SERVICE_NAME
  value: {{ .Values.app.serviceName | quote }}
- name: SERVICE_VERSION
  value: {{ .Values.app.serviceVersion | quote }}
- name: SERVICE_DESCRIPTION
  value: {{ .Values.app.serviceDescription | quote }}
- name: SERVICE_FRAMEWORK
  value: {{ .Values.app.serviceFramework | quote }}
{{- with .Values.extraEnv }}
{{ toYaml . }}
{{- end }}
{{- end -}}

{{- define "devops-info-service.vaultAnnotations" -}}
{{- if .Values.vault.enabled }}
vault.hashicorp.com/agent-inject: "true"
vault.hashicorp.com/role: {{ .Values.vault.role | quote }}
vault.hashicorp.com/agent-inject-secret-{{ .Values.vault.fileName }}: {{ .Values.vault.secretPath | quote }}
vault.hashicorp.com/secret-volume-path-{{ .Values.vault.fileName }}: {{ .Values.vault.mountPath | quote }}
vault.hashicorp.com/agent-inject-template-{{ .Values.vault.renderedFileName }}: |
  {{`{{- with secret "`}}{{ .Values.vault.secretPath }}{{`" -}}`}}
  {{ upper .Values.vault.templateKeys.username }}={{`{{ .Data.data.`}}{{ .Values.vault.templateKeys.username }}{{` }}`}}
  {{ upper .Values.vault.templateKeys.password }}={{`{{ .Data.data.`}}{{ .Values.vault.templateKeys.password }}{{` }}`}}
  {{`{{- end -}}`}}
{{- if .Values.vault.injectCommand }}
vault.hashicorp.com/agent-inject-command-{{ .Values.vault.renderedFileName }}: {{ .Values.vault.injectCommand | quote }}
{{- end }}
{{- end }}
{{- end -}}
