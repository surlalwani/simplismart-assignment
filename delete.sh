
#!/bin/bash
# Set default namespace if not provided
# NAMESPACE="${1:-default}"
NAME="default-deployment"

# Delete ScaledObject
kubectl delete scaledobject $NAME-scaledobject

# Delete Service
kubectl delete service $NAME-service

# Delete Deployment
kubectl delete deployment $NAME
