#!/bin/bash

source config.sh
source 0_environment_checks.sh

#Remove all extensions in AZ CLI
for arc_extension_name in $(az k8s-extension list --cluster-name $k8s_cluster_name -g $rg --cluster-type connectedClusters --query "[].name" -o tsv)
do
    az k8s-extension delete -n $arc_extension_name --cluster-name $k8s_cluster_name -g $rg --cluster-type connectedClusters -y
done

#Remove all new ns
for current_ns in $(kubectl --kubeconfig=$remote_cluster_kubeconfig get ns -o jsonpath="{.items[*].metadata.name}" | tr -s '[[:space:]]' '\n' | grep -v azure-arc)
do
    grep $current_ns $cluster_baseline_namespaces > /dev/null

    if [ $? -ne 0 ]
    then
        echo "Deleting ns $current_ns"
        kubectl --kubeconfig=$remote_cluster_kubeconfig delete ns $current_ns
    fi

done