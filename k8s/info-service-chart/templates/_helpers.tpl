{{/*
Common labels
*/}}
{{- define "info-service.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
{{ include "info-service.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "info-service.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "info-service.selectorLabels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "info-service.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "info-service.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Resource limits helper
*/}}
{{- define "info-service.resources" -}}
{{- if .Values.resources }}
resources:
  requests:
    memory: {{ .Values.resources.requests.memory }}
    cpu: {{ .Values.resources.requests.cpu }}
  limits:
    memory: {{ .Values.resources.limits.memory }}
    cpu: {{ .Values.resources.limits.cpu }}
{{- end }}
{{- end }}

{{/*
Vault annotations wrapper
*/}}
{{- define "info-service.vault.annotations" -}}
{{- include "common-lib.vault.annotations" (dict "ctx" $ "secretPath" .Values.vault.secretPath "role" .Values.vault.role) }}
# Template for environment variables (.env format)
{{- include "common-lib.vault.template.env" (dict "ctx" $ "secretPath" .Values.vault.secretPath) }}
# Template for JSON config
{{- include "common-lib.vault.template.json" (dict "ctx" $ "secretPath" .Values.vault.secretPath) }}
# Template for YAML config
{{- include "common-lib.vault.template.yaml" (dict "ctx" $ "secretPath" .Values.vault.secretPath) }}
{{- if .Values.vault.autoReload }}
# Auto-reload on secret update
{{- include "common-lib.vault.command" $ }}
vault.hashicorp.com/agent-inject-secret-config: "{{ .Values.vault.secretPath }}"
vault.hashicorp.com/agent-inject-secret-extra: "{{ .Values.vault.secretPath }}?version=1"
{{- end }}
{{- end }}