#!/bin/bash

# Function to check if Metrics Server is installed
check_metrics_server() {
    if ! kubectl get apiservices | grep -q "metrics.k8s.io"; then
        echo "Error: Metrics Server is not installed in the cluster."
        echo "Please install Metrics Server to use 'kubectl top'"
        exit 1
    fi
}

# Function to get metrics for a specific namespace
get_namespace_pod_metrics() {
    local namespace="${1:-default}"
    
    echo "=== Pod Metrics for Namespace: $namespace ==="
    
    # Get pod metrics with CPU and memory usage
    kubectl top pod -n "$namespace"
}

# Function to get detailed metrics for a specific deployment
get_deployment_pod_metrics() {
    local namespace="${1:-default}"
    local deployment_name="$2"
    
    if [ -z "$deployment_name" ]; then
        echo "Error: Deployment name is required"
        exit 1
    fi
    
    echo "=== Pod Metrics for Deployment: $deployment_name in Namespace: $namespace ==="
    
    # Find pods associated with the deployment
    kubectl get pods -n "$namespace" -l "app=$deployment_name" | tail -n +2 | while read -r pod_name rest; do
        echo "--- Metrics for Pod: $pod_name ---"
        kubectl top pod "$pod_name" -n "$namespace"
    done
}

# Main script logic
main() {
    # Check if Metrics Server is installed
    check_metrics_server

    # Parse command-line arguments
    case "$1" in
        "--namespace")
            get_namespace_pod_metrics "$2"
            ;;
        "--deployment")
            get_deployment_pod_metrics "$3" "$2"
            ;;
        *)
            echo "Usage:"
            echo "  $0 --namespace [namespace_name]"
            echo "  $0 --deployment [deployment_name] --namespace [namespace_name]"
            exit 1
            ;;
    esac
}

# Call the main function with all script arguments
main "$@"