{{/*
Expand the name of the chart.
*/}}
{{- define "devops-info-service.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "devops-info-service.fullname" -}}
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
Create chart label.
*/}}
{{- define "devops-info-service.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Selector labels.
*/}}
{{- define "devops-info-service.selectorLabels" -}}
app.kubernetes.io/name: {{ include "devops-info-service.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/*
Common labels.
*/}}
{{- define "devops-info-service.labels" -}}
helm.sh/chart: {{ include "devops-info-service.chart" . }}
{{ include "devops-info-service.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/*
Service account name.
*/}}
{{- define "devops-info-service.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "devops-info-service.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{/*
Secret name.
*/}}
{{- define "devops-info-service.secretName" -}}
{{- if .Values.secret.name -}}
{{- .Values.secret.name -}}
{{- else -}}
{{- printf "%s-credentials" (include "devops-info-service.fullname" .) -}}
{{- end -}}
{{- end -}}

{{/*
ConfigMap names.
*/}}
{{- define "devops-info-service.configFileConfigMapName" -}}
{{- printf "%s-config" (include "devops-info-service.fullname" .) -}}
{{- end -}}

{{- define "devops-info-service.envConfigMapName" -}}
{{- printf "%s-env" (include "devops-info-service.fullname" .) -}}
{{- end -}}

{{/*
PVC name.
*/}}
{{- define "devops-info-service.pvcName" -}}
{{- printf "%s-data" (include "devops-info-service.fullname" .) -}}
{{- end -}}

{{/*
Common environment variables.
*/}}
{{- define "devops-info-service.commonEnv" -}}
- name: HOST
  value: "0.0.0.0"
- name: PORT
  value: "{{ .Values.containerPort }}"
{{- end -}}
