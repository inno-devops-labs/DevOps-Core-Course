Lab 10 Solution - Helm Chart for DevOps Info Service

Chart: devops-info-service
Version: 0.1.0

Install dev: helm install dev-release devops-info-service -f devops-info-service/values-dev.yaml
Install prod: helm install prod-release devops-info-service -f devops-info-service/values-prod.yaml

Uninstall: helm uninstall <release-name>