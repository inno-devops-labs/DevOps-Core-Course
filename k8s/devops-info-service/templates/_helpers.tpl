{{/*
Application-level helpers.

This chart delegates common naming/labels to the `common-lib` dependency.
*/}}

{{- define "devops-info-service.name" -}}
{{- include "common.name" . -}}
{{- end -}}

{{- define "devops-info-service.fullname" -}}
{{- include "common.fullname" . -}}
{{- end -}}

{{- define "devops-info-service.labels" -}}
{{- include "common.labels" . -}}
{{- end -}}

{{- define "devops-info-service.selectorLabels" -}}
{{- include "common.selectorLabels" . -}}
{{- end -}}

