{{/*
Expand the name of the chart.
*/}}
{{- define "devops-info.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "devops-info.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Chart label.
*/}}
{{- define "devops-info.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Selector labels.
*/}}
{{- define "devops-info.selectorLabels" -}}
app.kubernetes.io/name: {{ include "devops-info.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Common labels.
*/}}
{{- define "devops-info.labels" -}}
helm.sh/chart: {{ include "devops-info.chart" . }}
{{ include "devops-info.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Secret name.
*/}}
{{- define "devops-info.secretName" -}}
{{- if .Values.secrets.nameOverride }}
{{- .Values.secrets.nameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-secret" (include "devops-info.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Service account name.
*/}}
{{- define "devops-info.serviceAccountName" -}}
{{- if .Values.serviceAccount.nameOverride }}
{{- .Values.serviceAccount.nameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-sa" (include "devops-info.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
ConfigMap name for file-based config.
*/}}
{{- define "devops-info.configFileConfigMapName" -}}
{{- printf "%s-config-file" (include "devops-info.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
ConfigMap name for environment variables.
*/}}
{{- define "devops-info.configEnvConfigMapName" -}}
{{- printf "%s-config-env" (include "devops-info.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
PersistentVolumeClaim name.
*/}}
{{- define "devops-info.pvcName" -}}
{{- if .Values.persistence.nameOverride }}
{{- .Values.persistence.nameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-data" (include "devops-info.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
