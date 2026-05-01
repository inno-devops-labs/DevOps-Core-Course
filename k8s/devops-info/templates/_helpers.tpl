{{/*
Expand the name of the chart.
*/}}
{{- define "devops-info.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "devops-info.fullname" -}}
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
{{- define "devops-info.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "devops-info.labels" -}}
helm.sh/chart: {{ include "devops-info.chart" . }}
{{ include "devops-info.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "devops-info.selectorLabels" -}}
app.kubernetes.io/name: {{ include "devops-info.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "devops-info.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "devops-info.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Canary steps for Rollout (Lab 14): optional web analysis after first canary slice when rollout.analysis.enabled.
*/}}
{{- define "devops-info.canarySteps" -}}
{{- if .Values.rollout.analysis.enabled }}
- setWeight: 20
- analysis:
    templates:
      - templateName: {{ include "devops-info.fullname" . }}-health
- setWeight: 40
- pause:
    duration: 30s
- setWeight: 60
- pause:
    duration: 30s
- setWeight: 80
- pause:
    duration: 30s
- setWeight: 100
{{- else }}
{{- toYaml .Values.rollout.canary.steps }}
{{- end }}
{{- end }}

{{/*
Lab 16: optional DNS host for wait-for-Service init (defaults to this chart's ClusterIP Service).
*/}}
{{- define "devops-info.waitForServiceHost" -}}
{{- if .Values.initContainers.waitForService.host }}
{{- .Values.initContainers.waitForService.host }}
{{- else }}
{{- printf "%s.%s.svc.cluster.local" (include "devops-info.fullname" .) .Release.Namespace }}
{{- end }}
{{- end }}

{{/*
Lab 16: initContainers — wget to shared emptyDir, then wait until Service DNS resolves.
*/}}
{{- define "devops-info.initContainers" -}}
- name: init-download
  image: {{ .Values.initContainers.download.image | quote }}
  command:
    - sh
    - -c
    - >-
      wget -q -O /work-dir/{{ .Values.initContainers.download.filename }}
      {{ .Values.initContainers.download.url | quote }}
      && echo "downloaded to /work-dir/{{ .Values.initContainers.download.filename }}"
  volumeMounts:
    - name: init-workdir
      mountPath: /work-dir
- name: init-wait-service
  image: {{ .Values.initContainers.waitForService.image | quote }}
  command:
    - sh
    - -c
    - |
      set -eu
      HOST="{{ include "devops-info.waitForServiceHost" . }}"
      echo "waiting for DNS: ${HOST}"
      until nslookup "${HOST}" >/dev/null 2>&1; do sleep 2; done
      echo "DNS ready for ${HOST}"
{{- end }}

{{/*
Common environment variables for DRY templates.
*/}}
{{- define "devops-info.envVars" -}}
- name: HOST
  value: {{ .Values.env.host | quote }}
- name: PORT
  value: {{ .Values.env.port | quote }}
- name: DEBUG
  value: {{ .Values.env.debug | quote }}
- name: APP_ENV
  value: {{ .Values.env.appEnv | quote }}
- name: LOG_LEVEL
  value: {{ .Values.env.logLevel | quote }}
- name: VISITS_FILE
  value: "/data/visits"
{{- end }}
