
import argparse
import subprocess
import time
from kubernetes import config, client
from kubernetes.client.rest import ApiException


# Utility function to run shell commands
def run_command(command, check=True):
    try:
        result = subprocess.run(command, shell=True, check=check, text=True, capture_output=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e.stderr}")
        raise


# Connect to Kubernetes Cluster
def connect_to_cluster(kubeconfig_path="~/.kube/config"):
    try:
        config.load_kube_config(kubeconfig_path)
        print("✅ Connected to the Kubernetes cluster successfully.")
    except Exception as e:
        print("❌ Failed to connect to the Kubernetes cluster. Ensure kubeconfig is correctly configured.")
        raise


# Wait for all pods to be running
def wait_for_pods(namespace, label_selector, timeout=300):
    api_instance = client.CoreV1Api()
    print(f"⏳ Waiting for pods in namespace '{namespace}' to be running...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        pods = api_instance.list_namespaced_pod(namespace=namespace, label_selector=label_selector)
        not_ready_pods = [
            pod.metadata.name for pod in pods.items if pod.status.phase != "Running"
        ]
        if not not_ready_pods:
            print("✅ All pods are running.")
            return
        print(f"⏳ Waiting for pods: {not_ready_pods}...")
        time.sleep(10)
    raise TimeoutError("❌ Timeout waiting for pods to be running.")


# Ensure Helm is installed
def install_helm():
    try:
        run_command("helm version")
        print("✅ Helm is already installed.")
    except:
        print("Installing Helm...")
        run_command("curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash")
        print("✅ Helm installation completed.")


# Ensure namespace exists
def ensure_namespace_exists(namespace):
    api_instance = client.CoreV1Api()
    try:
        api_instance.read_namespace(name=namespace)
        print(f"✅ Namespace '{namespace}' already exists.")
    except ApiException as e:
        if e.status == 404:
            api_instance.create_namespace(body={"metadata": {"name": namespace}})
            print(f"✅ Namespace '{namespace}' created.")
        else:
            print(f"❌ Error checking namespace: {e}")
            raise


# Ensure KEDA is installed
def install_keda(namespace="keda"):
    print(f"Ensuring KEDA is installed in the namespace '{namespace}'...")
    ensure_namespace_exists(namespace)

    # Check if KEDA is already installed
    try:
        helm_list = run_command(f"helm list -n {namespace}")
        if "keda" in helm_list:
            print("✅ KEDA is already installed.")
            return
    except:
        pass

    run_command("helm repo add kedacore https://kedacore.github.io/charts")
    run_command("helm repo update")
    run_command(f"helm install keda kedacore/keda --namespace {namespace} --wait")
    print("✅ KEDA installation completed.")
    wait_for_pods(namespace, label_selector="app=keda")


# Check if a resource exists
def resource_exists(api_instance, method, *args, **kwargs):
    try:
        method(*args, **kwargs)
        return True
    except ApiException as e:
        if e.status == 404:
            return False
        raise


# Create or Update Deployment
def create_deployment(namespace, name, image, replicas, cpu_request, cpu_limit, memory_request, memory_limit, ports):
    api_instance = client.AppsV1Api()
    if resource_exists(api_instance, api_instance.read_namespaced_deployment, name, namespace):
        print(f"✅ Deployment '{name}' already exists. Skipping creation.")
        return

    deployment = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {"name": name, "namespace": namespace},
        "spec": {
            "replicas": replicas,
            "selector": {"matchLabels": {"app": name}},
            "template": {
                "metadata": {"labels": {"app": name}},
                "spec": {
                    "containers": [
                        {
                            "name": name,
                            "image": image,
                            "resources": {
                                "requests": {"cpu": cpu_request, "memory": memory_request},
                                "limits": {"cpu": cpu_limit, "memory": memory_limit},
                            },
                            "ports": [{"containerPort": port} for port in ports],
                        }
                    ]
                },
            },
        },
    }

    try:
        api_instance.create_namespaced_deployment(namespace=namespace, body=deployment)
        print(f"✅ Deployment '{name}' created.")
    except ApiException as e:
        print(f"❌ Error creating deployment: {e}")
        raise


# Create or Update Service
def create_service(namespace, name, ports):
    api_instance = client.CoreV1Api()
    service_name = f"{name}-service"
    if resource_exists(api_instance, api_instance.read_namespaced_service, service_name, namespace=namespace):
        print(f"✅ Service '{service_name}' already exists. Skipping creation.")
        return

    service = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {"name": service_name, "namespace": namespace},
        "spec": {
            "type": "NodePort",
            "selector": {"app": name},
            "ports": [{"port": port, "targetPort": port} for port in ports],
        },
    }

    try:
        api_instance.create_namespaced_service(namespace=namespace, body=service)
        print(f"✅ Service '{service_name}' created.")
    except ApiException as e:
        print(f"❌ Error creating service: {e}")
        raise


# Create or Update ScaledObject
def create_scaled_object(namespace, name, triggers):
    api_instance = client.CustomObjectsApi()
    scaled_object_name = f"{name}-scaledobject"
    if resource_exists(
        api_instance,
        api_instance.get_namespaced_custom_object,
        group="keda.sh",
        version="v1alpha1",
        namespace=namespace,
        plural="scaledobjects",
        name=scaled_object_name,
    ):
        print(f"✅ ScaledObject '{scaled_object_name}' already exists. Skipping creation.")
        return

    scaled_object = {
        "apiVersion": "keda.sh/v1alpha1",
        "kind": "ScaledObject",
        "metadata": {"name": scaled_object_name, "namespace": namespace},
        "spec": {
            "scaleTargetRef": {"name": name},
            "minReplicaCount": 1,
            "triggers": triggers,
        },
    }

    try:
        api_instance.create_namespaced_custom_object(
            group="keda.sh",
            version="v1alpha1",
            namespace=namespace,
            plural="scaledobjects",
            body=scaled_object,
        )
        print(f"✅ ScaledObject '{scaled_object_name}' created.")
    except ApiException as e:
        print(f"❌ Error creating ScaledObject: {e}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kubernetes Resource Automation")
    parser.add_argument("--image", required=True, help="Container image for the deployment.")
    parser.add_argument("--name", required=True, help="Name of the deployment.")
    parser.add_argument("--namespace", default="default", help="Namespace for the deployment.")
    parser.add_argument("--replicas", type=int, default=2, help="Number of replicas.")
    args = parser.parse_args()

    try:
        connect_to_cluster()
        install_helm()
        install_keda(namespace="keda")

        create_deployment(
            namespace=args.namespace,
            name=args.name,
            image=args.image,
            replicas=args.replicas,
            cpu_request="100m",
            cpu_limit="200m",
            memory_request="128Mi",
            memory_limit="256Mi",
            ports=[80],
        )
        create_service(namespace=args.namespace, name=args.name, ports=[80])
        create_scaled_object(
            namespace=args.namespace,
            name=args.name,
            triggers=[
                {"type": "cpu", "metadata": {"type": "Utilization", "value": "50"}},
                {"type": "memory", "metadata": {"type": "Utilization", "value": "50"}},
            ],
        )
    except Exception as e:
        print(f"❌ Error: {e}")
