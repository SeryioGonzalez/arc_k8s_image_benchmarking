#!/bin/bash

source config.sh
source 0_environment_checks.sh

az connectedk8s connect -n $k8s_cluster_name -g $rg --kube-config $remote_cluster_kubeconfig -o none 