#!/bin/bash

echo "========================================="
echo "CONFIGMAP HOT RELOAD TEST"
echo "========================================="
echo

echo "Installing the release..."
helm upgrade --install hotreload-demo info-service-chart/ \
  -f info-service-chart/values-dev.yaml \
  --set vault.enabled=false \
  --wait

POD_NAME=$(kubectl get pods -l app.kubernetes.io/instance=hotreload-demo -o jsonpath='{.items[0].metadata.name}')
echo "Pod: $POD_NAME"
echo

echo "Current configuration:"
kubectl exec $POD_NAME -- cat /config/config.json | jq '.app.environment'
echo

echo "Changing ConfigMap (development -> staging)..."
sed -i '' 's/"environment": "development"/"environment": "staging"/' info-service-chart/files/config.json

echo "Updating the Helm release..."
helm upgrade hotreload-demo info-service-chart/ \
  -f info-service-chart/values-dev.yaml \
  --set vault.enabled=false \
  --wait

NEW_POD=$(kubectl get pods -l app.kubernetes.io/instance=hotreload-demo -o jsonpath='{.items[0].metadata.name}')
echo "New pod: $NEW_POD"
echo

echo "New configuration:"
kubectl exec $NEW_POD -- cat /config/config.json | jq '.app.environment'
echo

echo "Bringing it back (staging -> development)..."
sed -i '' 's/"environment": "staging"/"environment": "development"/' info-service-chart/files/config.json

helm upgrade hotreload-demo info-service-chart/ \
  -f info-service-chart/values-dev.yaml \
  --set vault.enabled=false \
  --wait

FINAL_POD=$(kubectl get pods -l app.kubernetes.io/instance=hotreload-demo -o jsonpath='{.items[0].metadata.name}')
echo "Final pod: $FINAL_POD"
kubectl exec $FINAL_POD -- cat /config/config.json | jq '.app.environment'

echo
echo "========================================="
echo "TEST COMPLETED"
echo "========================================="
