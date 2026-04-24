{{/*
Chart name
*/}}
{{- define "devops-python.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
Full name
*/}}
{{- define "devops-python.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{/*
Selector labels
*/}}
{{- define "devops-python.selectorLabels" -}}
app.kubernetes.io/name: {{ include "devops-python.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{/*
Common labels
*/}}
{{- define "devops-python.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
{{ include "devops-python.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/*
Secret resource name (Helm-managed or external)
*/}}
{{- define "devops-python.secretName" -}}
{{- if .Values.secrets.existingSecretName -}}
{{- .Values.secrets.existingSecretName -}}
{{- else -}}
{{- printf "%s-app-credentials" (include "devops-python.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{/*
Service account name
*/}}
{{- define "devops-python.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- default (include "devops-python.fullname" .) .Values.serviceAccount.name -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{/*
Non-secret container env (DRY) — Lab 11 bonus
*/}}
{{- define "devops-python.envVars" -}}
- name: HOST
  value: {{ .Values.env.HOST | quote }}
- name: PORT
  value: {{ .Values.env.PORT | quote }}
- name: LOG_FORMAT
  value: {{ .Values.env.LOG_FORMAT | quote }}
- name: VISITS_DATA_PATH
  value: {{ .Values.env.VISITS_DATA_PATH | quote }}
{{- end -}}

{{/*
Stable checksum input for env ConfigMap (Lab 12 bonus — pod restart on change)
*/}}
{{- define "devops-python.configEnvChecksum" -}}
{{- printf "%s|%s|%v" .Values.config.environment .Values.config.logLevel .Values.config.featureDebug -}}
{{- end -}}

{{- define "devops-python.analysisTemplateName" -}}
{{- printf "%s-health" (include "devops-python.fullname" .) -}}
{{- end -}}

