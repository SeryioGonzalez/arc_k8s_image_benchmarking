#!/bin/bash

source config.sh
source 0_environment_checks.sh

vm_public_ip=$(az network public-ip show -n "$vmName-public-ip" -g $rg --query "ipAddress" -o tsv)
vm_private_ip=$(az vm show -d -g $rg -n $vmName --query "privateIps" -o tsv)

echo "Create kubeadm cluster"
ssh -p 22222 $vm_public_ip "sudo kubeadm init --apiserver-cert-extra-sans $vm_public_ip --pod-network-cidr $podsCidr &> /dev/null; mkdir -p $HOME/.kube; sudo cp /etc/kubernetes/admin.conf $HOME/.kube/config; sudo chown $(id -u):$(id -g) $HOME/.kube/config"


echo "Mind kube-flannel has hardcoded IP ranges for pods in a configmap"
ssh -p 22222 $vm_public_ip "kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml" &> /dev/null

ssh -p 22222 $vm_public_ip "kubectl taint node k8snode node-role.kubernetes.io/control-plane:NoSchedule-" &> /dev/null

echo "Bring kubeconfig"
scp -q -o StrictHostKeyChecking=no -P 22222 $vm_public_ip:/home/$vmUser/.kube/config $remote_cluster_kubeconfig

sed -i "s/$vm_private_ip/$vm_public_ip/" $remote_cluster_kubeconfig

echo "Delete files in output folder"
find $output_folder -type f -exec rm -f {} \;

echo "Cluster baseline ns"
kubectl --kubeconfig=$remote_cluster_kubeconfig get ns -o jsonpath="{.items[*].metadata.name}" | tr -s '[[:space:]]' '\n' > $cluster_baseline_namespaces