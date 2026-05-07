{{/*
ServiceAccount name used by the pod and by Vault Kubernetes auth role binding.
*/}}
{{- define "devops-info-service.serviceAccountName" -}}
{{- if .Values.serviceAccount.name }}
{{- .Values.serviceAccount.name }}
{{- else }}
{{- include "common-lib.fullname" . }}
{{- end }}
{{- end }}

{{/*
Shared env snippets (DRY): chart/release metadata for verification and logs.
*/}}
{{- define "devops-info-service.extraEnv" -}}
- name: CHART_NAME
  value: {{ .Chart.Name | quote }}
- name: RELEASE_NAME
  value: {{ .Release.Name | quote }}
{{- end }}

{{/*
Lab 16: init containers (wait-for-DNS + wget to shared emptyDir). Requires busybox.
*/}}
{{- define "devops-info-service.initContainers" -}}
{{- if .Values.initContainers.enabled }}
      initContainers:
{{- if .Values.initContainers.waitForService.enabled }}
        - name: wait-for-service
          image: {{ .Values.initContainers.busyboxImage | quote }}
          command:
            - sh
            - -c
            - until nslookup {{ .Values.initContainers.waitForService.host | quote }} >/dev/null 2>&1; do echo waiting for {{ .Values.initContainers.waitForService.host | quote }}; sleep 2; done
{{- end }}
{{- if .Values.initContainers.download.enabled }}
        - name: init-download
          image: {{ .Values.initContainers.busyboxImage | quote }}
          command:
            - sh
            - -c
            - wget -q -O /work/{{ .Values.initContainers.download.destFile }} {{ .Values.initContainers.download.url | quote }}
          volumeMounts:
            - name: init-shared
              mountPath: /work
{{- end }}
{{- end }}
{{- end }}

{{/*
emptyDir shared between init-download and main (read-only in app container).
*/}}
{{- define "devops-info-service.initVolume" -}}
{{- if and .Values.initContainers.enabled .Values.initContainers.download.enabled }}
        - name: init-shared
          emptyDir: {}
{{- end }}
{{- end }}

{{/*
Main app mount for init-download artifact.
*/}}
{{- define "devops-info-service.initVolumeMount" -}}
{{- if and .Values.initContainers.enabled .Values.initContainers.download.enabled }}
            - name: init-shared
              mountPath: {{ .Values.initContainers.sharedVolumeMountPath | quote }}
              readOnly: true
{{- end }}
{{- end }}
