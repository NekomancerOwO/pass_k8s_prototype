Repository for the PASS Kubernetes execution prototype. Requires Minikube and Docker to be installed. Additionally the minikube ingress-ngix addon must be installed in order to use the Ingress object.

./build.sh [example_process] builds all docker images in the example_process folder.

./run.sh [example_process] [process_instance] applies all YAML configuration files in the example_process folder, starting the process. All Kubernetes objects will be created inside the [example_process]-[process_instance] namespace.

./terminate.sh deletes all Kubernetes objects off every namespace. Alternatively "kubectl delete namespace [example_process]-[process_instance]" can be used to delete a single namespace.
