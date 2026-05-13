{{/*
Expand the name of the chart.
*/}}
{{- define "mychart.name" -}}
{{- default .Chart.Name .Values.nameOverride | replace "_" "-" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "mychart.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | replace "_" "-" | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := include "mychart.name" . }}
{{- printf "%s-%s" .Release.Name $name | replace "_" "-" | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Chart name and version.
*/}}
{{- define "mychart.chart" -}}
{{ .Chart.Name }}-{{ .Chart.Version }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "mychart.selectorLabels" -}}
app.kubernetes.io/name: {{ include "mychart.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Common labels.
*/}}
{{- define "mychart.labels" -}}
helm.sh/chart: {{ include "mychart.chart" . }}
{{ include "mychart.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Service name helper.
*/}}
{{- define "mychart.serviceName" -}}
{{ include "mychart.fullname" . }}-service
{{- end }}