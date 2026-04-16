{
  "applicationName": "{{ include "devops-info-service.name" . }}",
  "environment": "{{ .Values.config.environment }}",
  "features": {
    "visitsCounter": {{ .Values.config.featureVisitsEnabled }},
    "metrics": {{ .Values.config.featureMetricsEnabled }}
  },
  "settings": {
    "logLevel": "{{ .Values.config.logLevel }}",
    "timezone": "UTC"
  }
}