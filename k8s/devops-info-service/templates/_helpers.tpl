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
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels — must match between Deployment and Service
*/}}
{{- define "devops-info-service.selectorLabels" -}}
app.kubernetes.io/name: {{ include "devops-info-service.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Name of the Helm-managed credentials Secret
*/}}
{{- define "devops-info-service.credentialsSecretName" -}}
{{- if .Values.credentialsSecret.name }}
{{- .Values.credentialsSecret.name }}
{{- else }}
{{- printf "%s-credentials" (include "devops-info-service.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Service account name
*/}}
{{- define "devops-info-service.serviceAccountName" -}}
{{- if .Values.serviceAccount.name }}
{{- .Values.serviceAccount.name }}
{{- else }}
{{- include "devops-info-service.fullname" . }}
{{- end }}
{{- end }}

{{/*
Lab 16 — initContainers: wait-for-DNS, then wget into shared emptyDir; app reads file at appMountPath.
*/}}
{{- define "devops-info-service.initContainersBlock" -}}
{{- if and .Values.initContainers.enabled (or .Values.initContainers.waitFor.enabled .Values.initContainers.download.enabled) }}
      initContainers:
{{- if .Values.initContainers.waitFor.enabled }}
        - name: init-wait-for-dns
          image: {{ .Values.initContainers.waitFor.image | quote }}
          command:
            - sh
            - -c
            - {{ printf "until nslookup %s >/dev/null 2>&1; do echo waiting; sleep 2; done" .Values.initContainers.waitFor.host | quote }}
{{- end }}
{{- if .Values.initContainers.download.enabled }}
        - name: init-download
          image: {{ .Values.initContainers.download.image | quote }}
          command:
            - sh
            - -c
            - {{ printf "set -e; wget -qO /init-work/%s %s; ls -la /init-work" .Values.initContainers.download.destName .Values.initContainers.download.url | quote }}
          volumeMounts:
            - name: init-work
              mountPath: /init-work
{{- end }}
{{- end }}
{{- end }}

{{- define "devops-info-service.initWorkVolume" -}}
{{- if and .Values.initContainers.enabled .Values.initContainers.download.enabled }}
        - name: init-work
          emptyDir: {}
{{- end }}
{{- end }}

{{- define "devops-info-service.initWorkAppVolumeMount" -}}
{{- if and .Values.initContainers.enabled .Values.initContainers.download.enabled }}
            - name: init-work
              mountPath: {{ .Values.initContainers.download.appMountPath | quote }}
              readOnly: true
{{- end }}
{{- end }}
