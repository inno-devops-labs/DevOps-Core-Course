{{/*
Expand the name of the chart.
*/}}
{{- define "go-app.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "go-app.fullname" -}}
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
{{- define "go-app.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels - uses library chart
*/}}
{{- define "go-app.labels" -}}
{{ include "common-lib.labels" . }}
{{- end }}

{{/*
Selector labels - uses library chart
*/}}
{{- define "go-app.selectorLabels" -}}
{{ include "common-lib.selectorLabels" . }}
{{- end }}
