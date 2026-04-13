{{/*
Expand the name of the chart.
*/}}
{{- define "devops-info-service.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
Truncates at 63 chars because some Kubernetes name fields have limits.
*/}}
{{- define "devops-info-service.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "devops-info-service.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "devops-info-service.labels" -}}
helm.sh/chart: {{ include "devops-info-service.chart" . }}
{{ include "devops-info-service.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "devops-info-service.selectorLabels" -}}
app.kubernetes.io/name: {{ include "devops-info-service.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Service account name for the workload (Vault Kubernetes auth binds to this name).
*/}}
{{- define "devops-info-service.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "devops-info-service.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Secret object name for application credentials (Helm-managed).
*/}}
{{- define "devops-info-service.credentialsSecretName" -}}
{{- printf "%s-%s" (include "devops-info-service.fullname" .) .Values.credentialsSecret.nameSuffix | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
ConfigMap name for file-based application configuration.
*/}}
{{- define "devops-info-service.configFileName" -}}
{{- printf "%s-config" (include "devops-info-service.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
ConfigMap name for environment variables.
*/}}
{{- define "devops-info-service.envConfigName" -}}
{{- printf "%s-env" (include "devops-info-service.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
PersistentVolumeClaim name for application data.
*/}}
{{- define "devops-info-service.pvcName" -}}
{{- printf "%s-data" (include "devops-info-service.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}
