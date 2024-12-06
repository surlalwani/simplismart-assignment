# Kubernetes Deployment Automation

## Project Overview

This project provides a comprehensive automation solution for deploying and managing applications on Kubernetes clusters, featuring:
- Automated deployment creation
- Service generation
- KEDA (Kubernetes Event-Driven Autoscaling) integration
- Metrics collection and monitoring

## Prerequisites

- Python 3.7+
- Kubernetes Cluster
- `kubectl` installed and configured
- Helm 3
- KEDA (will be installed automatically)

## Key Components

### 1. Deployment Automation Script (`deployment_automation.py`)

#### Features
- Connects to Kubernetes cluster
- Installs Helm and KEDA automatically
- Creates deployments with configurable:
  - Replicas
  - Resource limits
  - Container ports
- Generates NodePort services
- Creates KEDA ScaledObjects for advanced autoscaling

#### Autoscaling Triggers
The script configures KEDA ScaledObjects with:
- CPU Utilization scaling
- Memory Utilization scaling

### 2. Metrics Collection Script (`metrics.sh`)

#### Features
- Checks for Metrics Server installation
- Retrieves pod-level metrics for:
  - Entire namespaces
  - Specific deployments

## Usage

### Deployment Automation

```bash
python deployment_automation.py \
  --image your-container-image \
  --name your-app-name \
  --namespace your-namespace \
  --replicas 2
```

### Metrics Collection

#### Get Namespace Metrics
```bash
./metrics.sh --namespace default
```

#### Get Deployment Metrics
```bash
./metrics.sh --deployment your-deployment-name --namespace default
```

## Configuration Options

### Deployment Automation
- `--image`: Container image (required)
- `--name`: Deployment name (required)
- `--namespace`: Kubernetes namespace (default: 'default')
- `--replicas`: Number of replicas (default: 2)

### Default Resource Limits
- CPU Request: 100m
- CPU Limit: 200m
- Memory Request: 128Mi
- Memory Limit: 256Mi

## Suggested Improvements
1. Add more granular KEDA scaling triggers
2. Implement logging and error tracking
3. Support for custom resource limits via CLI
4. Add Prometheus metrics integration
5. Create a configuration file for default settings

## Dependencies
- `kubernetes` Python library
- `helm`
- `kubectl`
- KEDA

## Troubleshooting
- Ensure kubeconfig is correctly set up
- Verify Metrics Server is installed for `kubectl top`
- Check KEDA installation in the cluster