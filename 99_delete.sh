#!/bin/bash

source config.sh

echo "Deleting RG $rg"
az group delete --name $rg -y --no-wait 2> /dev/null

echo "Changing rg"
if [ $rg  = "seryiokubeRG" ]
then
    old_rg="seryiokubeRG"
    new_rg="sergiokubeRG"
else
    old_rg="sergiokubeRG"
    new_rg="seryiokubeRG"
fi

sed -i "s/rg=\"$old_rg\"/rg=\"$new_rg\"/" config.sh

echo "Removing kubeconfig $remote_cluster_kubeconfig"
rm -rf $remote_cluster_kubeconfig

echo "Flushing directory $output_folder"
find $output_folder -type f -exec rm -f {} \;
