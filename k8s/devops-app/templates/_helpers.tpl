{{/*
Create chart name and version used by the labels.
*/}}
{{- define "devops-app.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 -}}
{{- end -}}

{{/*
Common labels
*/}}
{{- define "devops-app.labels" -}}
helm.sh/chart: {{ include "devops-app.chart" . }}
{{ include "devops-app.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/*
Selector labels
*/}}
{{- define "devops-app.selectorLabels" -}}
app.kubernetes.io/name: {{ include "devops-app.fullname" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/*
Create the name of the app
*/}}
{{- define "devops-app.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 -}}
{{- end -}}
{{- end -}}

{{/*
Create chart name
*/}}
{{- define "devops-app.name" -}}
{{- default .Chart.Name .Values.nameOverride -}}
{{- end -}}
