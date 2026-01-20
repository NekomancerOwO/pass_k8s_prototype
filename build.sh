#!/bin/bash
# Automatically builds the base subject and input pool images in Minikube, as well as all subjects in the specified folder

PROCESS_FOLDER=$1

eval $(minikube docker-env)

echo "Building subject base image..."
docker build -t base_subject ./core/base_subject_image

echo "Building input pool image..."
docker build -t input_pool ./core/input_pool_image

for subject_dir in ./"$PROCESS_FOLDER"/*; do
    if [ -d "$subject_dir" ]; then
        subject_name=$(basename "$subject_dir")
        echo "Building image for $subject_name..."
        docker build -t "$subject_name" "$subject_dir"
    fi
done

echo "All images built for Minikube!"
