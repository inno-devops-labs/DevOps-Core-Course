{{/*
Expand the name of the chart.
*/}}
{{- define "devops-app-py.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "devops-app-py.fullname" -}}
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
{{- define "devops-app-py.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "devops-app-py.labels" -}}
helm.sh/chart: {{ include "devops-app-py.chart" . }}
{{ include "devops-app-py.selectorLabels" . }}
{{- if (or .Values.image.tag .Chart.AppVersion) }}
app.kubernetes.io/version: {{ .Values.image.tag | default .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: {{ .Values.partOf }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "devops-app-py.selectorLabels" -}}
app.kubernetes.io/name: {{ include "devops-app-py.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the service name.
*/}}
{{- define "devops-app-py.serviceName" -}}
{{- printf "%s-service" (include "devops-app-py.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create the headless service name for StatefulSet pod identity.
*/}}
{{- define "devops-app-py.headlessServiceName" -}}
{{- printf "%s-headless" (include "devops-app-py.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create the blue-green preview service name.
*/}}
{{- define "devops-app-py.previewServiceName" -}}
{{- default (printf "%s-preview" (include "devops-app-py.serviceName" .)) .Values.rollout.blueGreen.previewService.name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create the AnalysisTemplate name.
*/}}
{{- define "devops-app-py.analysisTemplateName" -}}
{{- default (printf "%s-health-check" (include "devops-app-py.fullname" .)) .Values.rollout.analysis.templateName | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create the secret name.
*/}}
{{- define "devops-app-py.secretName" -}}
{{- printf "%s-secret" (include "devops-app-py.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create the file ConfigMap name.
*/}}
{{- define "devops-app-py.fileConfigMapName" -}}
{{- printf "%s-config" (include "devops-app-py.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create the env ConfigMap name.
*/}}
{{- define "devops-app-py.envConfigMapName" -}}
{{- printf "%s-env" (include "devops-app-py.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create the PVC name.
*/}}
{{- define "devops-app-py.pvcName" -}}
{{- printf "%s-data" (include "devops-app-py.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create the service account name.
*/}}
{{- define "devops-app-py.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "devops-app-py.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Render the workload pod template shared by Deployments and Rollouts.
*/}}
{{- define "devops-app-py.podTemplate" -}}
{{- $envVars := include "devops-app-py.envVars" . | trim }}
{{- $vaultAnnotations := include "devops-app-py.vaultAnnotations" . | trim }}
{{- $configChecksums := include "devops-app-py.configChecksums" . | trim }}
{{- $usesStatefulSet := and .Values.statefulset.enabled (not .Values.rollout.enabled) }}
metadata:
  {{- if or $vaultAnnotations $configChecksums .Values.podAnnotations }}
  annotations:
    {{- if $vaultAnnotations }}
    {{- $vaultAnnotations | nindent 4 }}
    {{- end }}
    {{- if $configChecksums }}
    {{- $configChecksums | nindent 4 }}
    {{- end }}
    {{- with .Values.podAnnotations }}
    {{- toYaml . | nindent 4 }}
    {{- end }}
  {{- end }}
  labels:
    {{- include "devops-app-py.selectorLabels" . | nindent 4 }}
    app.kubernetes.io/part-of: {{ .Values.partOf }}
    {{- with .Values.podLabels }}
    {{- toYaml . | nindent 4 }}
    {{- end }}
spec:
  serviceAccountName: {{ include "devops-app-py.serviceAccountName" . }}
  containers:
    - name: {{ include "devops-app-py.name" . }}
      image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
      imagePullPolicy: {{ .Values.image.pullPolicy }}
      ports:
        - name: http
          containerPort: {{ .Values.containerPort }}
          protocol: TCP
      {{- if or .Values.config.file.enabled .Values.persistence.enabled }}
      volumeMounts:
        {{- if .Values.config.file.enabled }}
        - name: config-volume
          mountPath: {{ .Values.config.mountPath | quote }}
          readOnly: true
        {{- end }}
        {{- if .Values.persistence.enabled }}
        - name: data-volume
          mountPath: {{ .Values.persistence.mountPath | quote }}
        {{- end }}
      {{- end }}
      {{- if or .Values.config.env.enabled .Values.secrets.enabled }}
      envFrom:
        {{- if .Values.config.env.enabled }}
        - configMapRef:
            name: {{ include "devops-app-py.envConfigMapName" . }}
        {{- end }}
        {{- if .Values.secrets.enabled }}
        - secretRef:
            name: {{ include "devops-app-py.secretName" . }}
        {{- end }}
      {{- end }}
      {{- if $envVars }}
      env:
        {{- $envVars | nindent 8 }}
      {{- end }}
      {{- with .Values.livenessProbe }}
      livenessProbe:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.readinessProbe }}
      readinessProbe:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.resources }}
      resources:
        {{- toYaml . | nindent 8 }}
      {{- end }}
  {{- if or .Values.config.file.enabled (and .Values.persistence.enabled (not $usesStatefulSet)) }}
  volumes:
    {{- if .Values.config.file.enabled }}
    - name: config-volume
      configMap:
        name: {{ include "devops-app-py.fileConfigMapName" . }}
    {{- end }}
    {{- if and .Values.persistence.enabled (not $usesStatefulSet) }}
    - name: data-volume
      persistentVolumeClaim:
        claimName: {{ include "devops-app-py.pvcName" . }}
    {{- end }}
  {{- end }}
{{- end }}

{{/*
Render non-secret environment variables.
*/}}
{{- define "devops-app-py.envVars" -}}
{{- range .Values.env }}
- name: {{ .name }}
  value: {{ .value | quote }}
{{- end }}
{{- end }}

{{/*
Render the chart-managed config.json file.
*/}}
{{- define "devops-app-py.renderedConfigJson" -}}
{{- tpl (.Files.Get "files/config.json") . -}}
{{- end }}

{{/*
Render pod checksum annotations for config-driven rollouts.
*/}}
{{- define "devops-app-py.configChecksums" -}}
{{- if .Values.config.file.enabled }}
checksum/config-file: {{ include "devops-app-py.renderedConfigJson" . | sha256sum | quote }}
{{- end }}
{{- if .Values.config.env.enabled }}
checksum/config-env: {{ toJson .Values.config.env.data | sha256sum | quote }}
{{- end }}
{{- end }}

{{/*
Render Vault injector annotations.
*/}}
{{- define "devops-app-py.vaultAnnotations" -}}
{{- if .Values.vault.enabled }}
vault.hashicorp.com/agent-inject: "true"
vault.hashicorp.com/role: {{ .Values.vault.role | quote }}
vault.hashicorp.com/agent-inject-secret-config: {{ .Values.vault.secretPath | quote }}
vault.hashicorp.com/agent-inject-file-config: {{ .Values.vault.templateFile | quote }}
vault.hashicorp.com/agent-inject-template-config: |
  {{ "{{- with secret \"" }}{{ .Values.vault.secretPath }}{{ "\" -}}" }}
  APP_USERNAME={{ "{{ .Data.data.APP_USERNAME }}" }}
  APP_PASSWORD={{ "{{ .Data.data.APP_PASSWORD }}" }}
  APP_API_KEY={{ "{{ .Data.data.APP_API_KEY }}" }}
  {{ "{{- end }}" }}
{{- end }}
{{- end }}

{{/*
Create the pre-install hook job name.
*/}}
{{- define "devops-app-py.preInstallJobName" -}}
{{- printf "%s-pre-install" (include "devops-app-py.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create the post-install hook job name.
*/}}
{{- define "devops-app-py.postInstallJobName" -}}
{{- printf "%s-post-install" (include "devops-app-py.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}
