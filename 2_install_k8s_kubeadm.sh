#!/bin/bash

source config.sh
source 0_environment_checks.sh

install_script=$kubeadm_install_script

vm_public_ip=$(az network public-ip show -n "$vmName-public-ip" -g $rg --query "ipAddress" -o tsv)
scp -q -o StrictHostKeyChecking=no -P 22222 $install_script $vm_public_ip:/home/$vmUser/$install_script

ssh -p 22222 $vm_public_ip "chmod +x /home/$vmUser/$install_script; /home/$vmUser/$install_script"
