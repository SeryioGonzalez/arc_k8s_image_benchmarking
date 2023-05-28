#!/bin/bash

source config.sh
az connectedk8s delete -n $k8s_cluster_name -g $rg --kube-config $remote_cluster_kubeconfig --kube-context kubernetes-admin@kubernetes -y

vm_public_ip=$(az network public-ip show -n "$vmName-public-ip" -g $rg --query "ipAddress" -o tsv)

echo "Reset kubeadm custer"
ssh -p 22222 $vm_public_ip "sudo kubeadm reset -f &> /dev/null"

echo "Reset IPTABLES"
ssh -p 22222 $vm_public_ip "sudo iptables -F"

echo "Remove remote kubeconfig"
ssh -p 22222 $vm_public_ip "rm $HOME/.kube/config"

echo "Remove local kubeconfig"
rm $remote_cluster_kubeconfig
