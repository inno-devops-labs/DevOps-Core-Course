{{/*
Chart-local aliases around the shared library helpers.
*/}}
{{- define "devops-info-service.name" -}}
{{- include "common-lib.name" . -}}
{{- end -}}

{{- define "devops-info-service.fullname" -}}
{{- include "common-lib.fullname" . -}}
{{- end -}}

{{- define "devops-info-service.labels" -}}
{{- include "common-lib.labels" . -}}
{{- end -}}

{{- define "devops-info-service.selectorLabels" -}}
{{- include "common-lib.selectorLabels" . -}}
{{- end -}}
