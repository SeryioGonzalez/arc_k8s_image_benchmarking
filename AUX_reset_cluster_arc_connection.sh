#!/bin/bash

source config.sh
source 0_environment_checks.sh

for arc_cluster_connection_name in $(az connectedk8s list -g $rg --query "[].name" -o tsv)
do
    az connectedk8s delete -n $k8s_cluster_name -g $rg --kube-config $remote_cluster_kubeconfig -y 
done