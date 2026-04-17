{{/* Expand the name of the chart. */}}
{{- define "python-app.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Create a default fully qualified app name. */}}
{{- define "python-app.fullname" -}}
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

{{/* Chart name and version. */}}
{{- define "python-app.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/* Common labels. */}}
{{- define "python-app.labels" -}}
helm.sh/chart: {{ include "python-app.chart" . }}
{{ include "python-app.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/* Selector labels. */}}
{{- define "python-app.selectorLabels" -}}
app.kubernetes.io/name: {{ include "python-app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/* Service account name. */}}
{{- define "python-app.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "python-app.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/* Secret name. */}}
{{- define "python-app.secretName" -}}
{{- default (printf "%s-secret" (include "python-app.fullname" .)) .Values.secrets.name }}
{{- end }}


{{/* ConfigMap name for file-based config. */}}
{{- define "python-app.configFileName" -}}
{{- default (printf "%s-config" (include "python-app.fullname" .)) .Values.configMap.file.name }}
{{- end }}

{{/* ConfigMap name for env config. */}}
{{- define "python-app.configEnvName" -}}
{{- default (printf "%s-env" (include "python-app.fullname" .)) .Values.configMap.env.name }}
{{- end }}

{{/* PVC name. */}}
{{- define "python-app.pvcName" -}}
{{- if .Values.persistence.existingClaim }}
{{- .Values.persistence.existingClaim }}
{{- else }}
{{- printf "%s-data" (include "python-app.fullname" .) }}
{{- end }}
{{- end }}


{{/* Preview Service name for blue-green strategy. */}}
{{- define "python-app.previewServiceName" -}}
{{- printf "%s-preview" (include "python-app.fullname" .) }}
{{- end }}
