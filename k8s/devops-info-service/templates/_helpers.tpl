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
Common labels
*/}}
{{- define "devops-info-service.labels" -}}
helm.sh/chart: {{ include "devops-info-service.chart" . }}
{{ include "devops-info-service.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels — must match Service selector and Deployment pod template.
*/}}
{{- define "devops-info-service.selectorLabels" -}}
app.kubernetes.io/name: {{ include "devops-info-service.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
ServiceAccount name for Vault Kubernetes auth.
*/}}
{{- define "devops-info-service.serviceAccountName" -}}
{{- if .Values.serviceAccount.name }}
{{- .Values.serviceAccount.name }}
{{- else }}
{{- printf "%s-sa" (include "devops-info-service.fullname" .) }}
{{- end }}
{{- end }}

{{/*
Name of the Helm-managed Secret holding app credentials.
*/}}
{{- define "devops-info-service.credentialsSecretName" -}}
{{- printf "%s-credentials" (include "devops-info-service.fullname" .) }}
{{- end }}

{{/*
ConfigMap holding files/config.json
*/}}
{{- define "devops-info-service.configMapFileName" -}}
{{- printf "%s-config" (include "devops-info-service.fullname" .) }}
{{- end }}

{{/*
ConfigMap for envFrom (APP_NAME, APP_ENV, LOG_LEVEL)
*/}}
{{- define "devops-info-service.configMapEnvName" -}}
{{- printf "%s-env" (include "devops-info-service.fullname" .) }}
{{- end }}

{{/*
PVC for visit counter data
*/}}
{{- define "devops-info-service.pvcName" -}}
{{- printf "%s-data" (include "devops-info-service.fullname" .) }}
{{- end }}
