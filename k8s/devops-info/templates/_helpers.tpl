{{/* Expand chart name. */}}
{{- define "devops-info.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Create a fully qualified app name. */}}
{{- define "devops-info.fullname" -}}
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

{{/* Create chart label value. */}}
{{- define "devops-info.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Common labels. */}}
{{- define "devops-info.labels" -}}
helm.sh/chart: {{ include "devops-info.chart" . }}
{{ include "devops-info.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/* Labels used for selectors. */}}
{{- define "devops-info.selectorLabels" -}}
app.kubernetes.io/name: {{ include "devops-info.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app: {{ include "devops-info.name" . }}
{{- end }}

{{/* Create service account name. */}}
{{- define "devops-info.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- if .Values.serviceAccount.name }}
{{- .Values.serviceAccount.name }}
{{- else }}
{{- include "devops-info.fullname" . }}
{{- end }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/* Create secret name. */}}
{{- define "devops-info.secretName" -}}
{{- if .Values.secrets.name }}
{{- .Values.secrets.name }}
{{- else }}
{{- printf "%s-credentials" (include "devops-info.fullname" .) }}
{{- end }}
{{- end }}

{{/* Create config file ConfigMap name. */}}
{{- define "devops-info.configFileConfigMapName" -}}
{{- printf "%s-config" (include "devops-info.fullname" .) }}
{{- end }}

{{/* Create env ConfigMap name. */}}
{{- define "devops-info.configEnvConfigMapName" -}}
{{- printf "%s-env" (include "devops-info.fullname" .) }}
{{- end }}

{{/* Create persistence claim name. */}}
{{- define "devops-info.persistenceClaimName" -}}
{{- if .Values.persistence.existingClaim }}
{{- .Values.persistence.existingClaim }}
{{- else }}
{{- printf "%s-data" (include "devops-info.fullname" .) }}
{{- end }}
{{- end }}

{{/* Active service name for rollout strategies. */}}
{{- define "devops-info.activeServiceName" -}}
{{- if and .Values.rollout.enabled (eq .Values.rollout.strategy "blueGreen") .Values.rollout.blueGreen.activeService }}
{{- .Values.rollout.blueGreen.activeService }}
{{- else }}
{{- include "devops-info.fullname" . }}
{{- end }}
{{- end }}

{{/* Preview service name for blue-green strategy. */}}
{{- define "devops-info.previewServiceName" -}}
{{- if .Values.rollout.blueGreen.previewService }}
{{- .Values.rollout.blueGreen.previewService }}
{{- else }}
{{- printf "%s-preview" (include "devops-info.fullname" .) }}
{{- end }}
{{- end }}

{{/* Headless service name for StatefulSet. */}}
{{- define "devops-info.headlessServiceName" -}}
{{- if .Values.statefulset.headlessService.name }}
{{- .Values.statefulset.headlessService.name }}
{{- else }}
{{- printf "%s-headless" (include "devops-info.fullname" .) }}
{{- end }}
{{- end }}
