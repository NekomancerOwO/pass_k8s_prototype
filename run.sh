#Starts a PASS process instance by running all subjects inside the specified folder. For example:
# "run.sh example_process 1" will start all subjects in the example process folder under the namespace "example-process-1"
# Kubernetes does not allow '_' symbols in namespace names so they are automatically converted to '-'

PROCESS_FOLDER=$1
INSTANCE_NAME=$2

NAMESPACE="${PROCESS_FOLDER}-${INSTANCE_NAME}"
NAMESPACE="${NAMESPACE//_/-}"

kubectl delete namespace "$NAMESPACE" --ignore-not-found
kubectl create namespace "$NAMESPACE"

kubectl label namespace "$NAMESPACE" type=pass_process

find "$PROCESS_FOLDER/" -name "*.yaml" | while read file; do
  echo "Applying $file in namespace $NAMESPACE..."
  kubectl apply -f "$file" -n "$NAMESPACE"
done
