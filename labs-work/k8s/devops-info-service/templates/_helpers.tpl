{{/*
Expand the name of the chart.
Wraps the common library template.
*/}}
{{- define "devops-info-service.name" -}}
{{- include "common.name" . -}}
{{- end }}

{{/*
Create a default fully qualified app name.
Wraps the common library template.
*/}}
{{- define "devops-info-service.fullname" -}}
{{- include "common.fullname" . -}}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
Wraps the common library template.
*/}}
{{- define "devops-info-service.chart" -}}
{{- include "common.chart" . -}}
{{- end }}

{{/*
Common labels.
Wraps the common library template.
*/}}
{{- define "devops-info-service.labels" -}}
{{- include "common.labels" . -}}
{{- end }}

{{/*
Selector labels.
Wraps the common library template.
*/}}
{{- define "devops-info-service.selectorLabels" -}}
{{- include "common.selectorLabels" . -}}
{{- end }}

{{/*
Common environment variables for the application.
Demonstrates DRY principle via named templates.
*/}}
{{- define "devops-info-service.envVars" -}}
{{- range .Values.env }}
- name: {{ .name }}
  value: {{ .value | quote }}
{{- end }}
{{- end }}

{{/*
Init containers - shared across all workload kinds.
Renders empty when both download and waitFor are disabled.
*/}}
{{- define "devops-info-service.initContainers" -}}
{{- if .Values.initContainers.download.enabled }}
- name: init-download
  image: busybox:1.36
  command:
    - sh
    - -c
    - 'wget -O {{ .Values.initContainers.download.targetFile }} {{ .Values.initContainers.download.url }}'
  volumeMounts:
    - name: workdir
      mountPath: /work-dir
{{- end }}
{{- if .Values.initContainers.waitFor.enabled }}
- name: wait-for-service
  image: busybox:1.36
  command:
    - sh
    - -c
    - 'until nslookup {{ .Values.initContainers.waitFor.service }}; do echo "waiting for {{ .Values.initContainers.waitFor.service }}"; sleep 2; done'
{{- end }}
{{- end }}

{{/*
emptyDir workdir volume - only when download init container is enabled.
*/}}
{{- define "devops-info-service.workdirVolume" -}}
{{- if .Values.initContainers.download.enabled }}
- name: workdir
  emptyDir: {}
{{- end }}
{{- end }}

{{/*
workdir volumeMount for the main application container.
*/}}
{{- define "devops-info-service.workdirMount" -}}
{{- if .Values.initContainers.download.enabled }}
- name: workdir
  mountPath: /work-dir
{{- end }}
{{- end }}
