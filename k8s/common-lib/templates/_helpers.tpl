{{/*
Expand the chart name.
*/}}
{{- define "common-lib.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a chart+version string for labels.
*/}}
{{- define "common-lib.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create the fully qualified app name.
*/}}
{{- define "common-lib.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{/*
Selector labels shared across charts.
*/}}
{{- define "common-lib.selectorLabels" -}}
app.kubernetes.io/name: {{ include "common-lib.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- if .Values.component }}
app.kubernetes.io/component: {{ .Values.component }}
{{- end }}
{{- if .Values.partOf }}
app.kubernetes.io/part-of: {{ .Values.partOf }}
{{- end }}
{{- end -}}

{{/*
Standard labels shared across charts.
*/}}
{{- define "common-lib.labels" -}}
helm.sh/chart: {{ include "common-lib.chart" . }}
{{ include "common-lib.selectorLabels" . }}
app.kubernetes.io/version: {{ default .Chart.AppVersion .Values.image.tag | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}
