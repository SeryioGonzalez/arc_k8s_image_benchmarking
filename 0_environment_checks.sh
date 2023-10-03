#!/bin/bash

## THINGS YOU HAVE TO CHANGE - CHECKS AT THE BOTTOM
vm_public_key=$(cat $PUBLIC_KEY_FILE)
subscription_id=$AZURE_SUBSCRIPTION_ID_POC

#SAFETY CHECKS OFTHINGS I NEED
# Public key file is provided
if [ -z $PUBLIC_KEY_FILE ]
then
    echo 'ERROR: You need an environment variable named PUBLIC_KEY_FILE'
    echo "Export it before using this script or add it to your bashrc file"
    exit
fi

# Subscription_id is provided
if [ -z $subscription_id ]
then
    echo 'ERROR: You need an environment variable named subscription_id'
    echo "Export it before using this script or add it to your bashrc file"
    exit
fi

# Logged-in to Azure
az account show &> /dev/null;
if [ $? -ne 0 ]
then
    echo 'ERROR: You need to perform az login'
    exit
fi

az account set -s $subscription_id
