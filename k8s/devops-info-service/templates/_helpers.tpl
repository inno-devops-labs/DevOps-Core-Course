{{/*
Expand the name of the chart.
*/}}
{{- define "devops-info-service.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "devops-info-service.fullname" -}}
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
Create chart name and version as used by the chart label.
*/}}
{{- define "devops-info-service.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels.
*/}}
{{- define "devops-info-service.labels" -}}
helm.sh/chart: {{ include "devops-info-service.chart" . }}
{{ include "devops-info-service.selectorLabels" . }}
app.kubernetes.io/component: web
app.kubernetes.io/part-of: devops-core-course
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels.
*/}}
{{- define "devops-info-service.selectorLabels" -}}
app: {{ include "devops-info-service.name" . }}
app.kubernetes.io/name: {{ include "devops-info-service.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Return the ServiceAccount name used by the workload.
*/}}
{{- define "devops-info-service.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "devops-info-service.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Return the Secret name used by the workload.
*/}}
{{- define "devops-info-service.secretName" -}}
{{- if .Values.secret.existingSecret }}
{{- .Values.secret.existingSecret }}
{{- else if .Values.secret.name }}
{{- .Values.secret.name }}
{{- else }}
{{- printf "%s-secret" (include "devops-info-service.fullname" .) }}
{{- end }}
{{- end }}

{{/*
Render static environment variables.
*/}}
{{- define "devops-info-service.envVars" -}}
{{- range .Values.env }}
- name: {{ .name }}
  value: {{ .value | quote }}
{{- end }}
{{- end }}

{{/*
Render release metadata environment variables that make rollout revisions visible in responses.
*/}}
{{- define "devops-info-service.releaseEnvVars" -}}
- name: DEVOPS_SERVICE_VERSION
  value: {{ .Values.releaseMetadata.version | quote }}
- name: DEVOPS_RELEASE_TRACK
  value: {{ .Values.releaseMetadata.track | quote }}
{{- if .Values.releaseMetadata.color }}
- name: DEVOPS_RELEASE_COLOR
  value: {{ .Values.releaseMetadata.color | quote }}
{{- end }}
{{- end }}

{{/*
Return the preview Service name used by blue-green deployments.
*/}}
{{- define "devops-info-service.previewServiceName" -}}
{{- printf "%s-preview" (include "devops-info-service.fullname" .) }}
{{- end }}

{{/*
Return the headless Service name used by StatefulSets.
*/}}
{{- define "devops-info-service.headlessServiceName" -}}
{{- printf "%s-headless" (include "devops-info-service.fullname" .) }}
{{- end }}

{{/*
Return the AnalysisTemplate name used by canary deployments.
*/}}
{{- define "devops-info-service.analysisTemplateName" -}}
{{- printf "%s-success-rate" (include "devops-info-service.fullname" .) }}
{{- end }}

{{/*
Render the Vault Agent template used for bonus env-style secret files.
*/}}
{{- define "devops-info-service.vaultAgentTemplate" -}}
{{`{{- with secret "`}}{{ .Values.vault.secretPath }}{{`" -}}`}}
APP_USERNAME={{`{{ .Data.data.username }}`}}
APP_PASSWORD={{`{{ .Data.data.password }}`}}
{{`{{- end -}}`}}
{{- end }}

{{/*
Render Vault injector annotations when Vault integration is enabled.
*/}}
{{- define "devops-info-service.vaultAnnotations" -}}
{{- if .Values.vault.enabled }}
vault.hashicorp.com/agent-inject: "true"
vault.hashicorp.com/auth-path: {{ printf "auth/%s" .Values.vault.authPath | quote }}
vault.hashicorp.com/role: {{ .Values.vault.role | quote }}
vault.hashicorp.com/agent-inject-secret-config: {{ .Values.vault.secretPath | quote }}
vault.hashicorp.com/agent-inject-file-config: {{ .Values.vault.injectFileName | quote }}
vault.hashicorp.com/secret-volume-path-config: {{ .Values.vault.secretMountPath | quote }}
vault.hashicorp.com/agent-pre-populate-only: {{ ternary "true" "false" .Values.vault.agentPrePopulateOnly | quote }}
{{- if and .Values.vault.template.enabled (eq .Values.vault.template.format "env") }}
vault.hashicorp.com/agent-inject-template-config: |
{{ include "devops-info-service.vaultAgentTemplate" . | indent 2 }}
{{- end }}
{{- end }}
{{- end }}
