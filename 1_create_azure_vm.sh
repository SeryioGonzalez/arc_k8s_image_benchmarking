#!/bin/bash

source config.sh
source 0_environment_checks.sh

set -e

echo "Creating RG $rg"
az group create --name $rg --location $region -o none

echo "Creating vnet $vnetName"
az network vnet create -g $rg -n $vnetName --address-prefixes $vnetPrefix --subnet-name $subnetName --subnet-prefix $subnetPrefix -o none

echo "Creating nsg for k8s node"
az network nsg create -g $rg -n $nsg_name -o none

echo "Creating nsg rule for k8s node"
az network nsg rule create -g $rg --nsg-name $nsg_name -n ssh_alternative --priority 200 --source-address-prefixes '*' --destination-port-ranges $ssh_vm_port --access Allow --protocol Tcp --description "Allow ssh on ports $ssh_vm_port" -o none
az network nsg rule create -g $rg --nsg-name $nsg_name -n k8s_api         --priority 210 --source-address-prefixes '*' --destination-port-ranges 6443         --access Allow --protocol Tcp --description "Allow k8s API port" -o none

export AZURE_K8S_WORKER_VM_NSG_ID=$(az network nsg show -g $rg -n $nsg_name --query id -o tsv )
export AZURE_APP_VM_SUBNET_ID=$(az network vnet subnet show -g $rg --vnet $vnetName --name $subnetName --query id -o tsv)

echo "Creating K8S node"
az deployment group create --no-wait --resource-group $rg --name "k8snode" --template-file "template-workers.json" --parameters \
	nsgId=$AZURE_K8S_WORKER_VM_NSG_ID \
	subnetId=$AZURE_APP_VM_SUBNET_ID \
	vmName=$vmName \
	vmPublicKey="$vm_public_key" \
	vmSize=$vmSize \
	cluster_name=$k8s_cluster_name \
	vmUser=$vmUser  -o none

echo "Waiting for VMs to be created"
sleep 100
echo "Continuing process"

echo "Checking K8S node Running"
VM_STATUS=$(az vm show -d -g $rg -n $vmName --query "powerState" -o tsv | awk '{print $2}')

if [ $VM_STATUS != "running" ]
then
	echo "$vmName is not running. Starting"
	az vm start -g $rg -n $vmName -o none
else
	echo "$vmName is running"
fi

echo "Configuring K8S Node"
echo "Setting SSH port to 22222"
az vm run-command invoke -g $rg -n $vmName --command-id RunShellScript --scripts "sed -i 's/#Port 22/Port 22222/' /etc/ssh/sshd_config; systemctl restart sshd" --query "value[0].displayStatus"
