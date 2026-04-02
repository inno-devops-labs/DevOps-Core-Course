{{/*
Application-level helpers.

This chart delegates common naming/labels to the `common-lib` dependency.
*/}}

{{- define "devops-app-java.name" -}}
{{- include "common.name" . -}}
{{- end -}}

{{- define "devops-app-java.fullname" -}}
{{- include "common.fullname" . -}}
{{- end -}}

{{- define "devops-app-java.labels" -}}
{{- include "common.labels" . -}}
{{- end -}}

{{- define "devops-app-java.selectorLabels" -}}
{{- include "common.selectorLabels" . -}}
{{- end -}}

