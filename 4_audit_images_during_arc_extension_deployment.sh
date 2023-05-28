source config.sh
source 0_environment_checks.sh

function get_cluster_images {
    output_file=$1

    temp_file=".tmp"
    echo "" > $temp_file

    for namespace in $(kubectl --kubeconfig=$remote_cluster_kubeconfig get ns -o jsonpath="{.items[*].metadata.name}" | tr -s '[[:space:]]' '\n' )
    do
        for pod_name in $(kubectl --kubeconfig=$remote_cluster_kubeconfig get pods -n $namespace -o jsonpath="{.items[*].metadata.name}")
        do    
            #Each deployment will add a suffix in the pod name in K8S per replicaset and pod
            deployment_id_suffix=$(echo $pod_name | egrep -v "\-agent$" | egrep -o "\-[a-z0-9]{8,10}\-[a-z0-9]{5}$|-[a-z0-9]{5}$|-[a-z0-9]{14}$")

            if [ $deployment_id_suffix"qqqq" != "qqqq" ]
            then
                #We remove the deployment_id_suffix from the pod
                normalized_pod_name=$(echo $pod_name | sed "s/$deployment_id_suffix//")
            else
                #Nothing to normalize. Just copy
                normalized_pod_name=$pod_name
            fi

            service_account_name_in_pod=$(kubectl --kubeconfig=$remote_cluster_kubeconfig get pod -n $namespace $pod_name -o=jsonpath='{.spec.serviceAccountName}')
            kubectl --kubeconfig=$remote_cluster_kubeconfig get pod -n $namespace $pod_name -o=jsonpath='{range .spec.containers[*]}{.name}{"\t"}{.image}{"\n"}{end}' |
                awk -v k8s_namespace=$namespace -v pod_name=$normalized_pod_name -v service_account_name_in_pod=$service_account_name_in_pod '{container_name=$1; image_name=$2; print k8s_namespace " " pod_name " " container_name " " image_name " " service_account_name_in_pod}' >> $temp_file
        
        done    
    done

    sort $temp_file | column -t > $output_file
    rm $temp_file
}

function reset_cluster_and_arc {
    source 88_reset_kubeadm_and_arc.sh
    source 3_start_kubeadm_cluster.sh
}

function reset_cluster_and_connect_to_arc {
    source 88_reset_kubeadm_and_arc.sh
    source 3_start_kubeadm_cluster.sh
    source AUX_connect_cluster_to_arc.sh
}

function reset_arc_connection {
    source AUX_reset_cluster_arc_connection.sh
}

function reset_arc_extensions {
    source AUX_reset_arc_extensions.sh
}

echo "Cluster baseline images"
reset_arc_connection
get_cluster_images $image_list_cluster_baseline

echo "Cluster images once connected to arc but before arc extension provision"
source AUX_connect_cluster_to_arc.sh
get_cluster_images $image_list_cluster_arc_no_extensions

echo "We start installing Arc extensions"
while read arc_extension_data
do
    #Delete any previous arc extension
    echo "Removing any previous arc extension"
    reset_arc_extensions

    extension_type=$(echo $arc_extension_data | awk '{print $1}')
    extension_name=$(echo $arc_extension_data | awk '{print $2}')
    echo "Installing extension $extension_name of type $extension_type"
    az k8s-extension create --cluster-name $k8s_cluster_name -g $rg --cluster-type connectedClusters --name "$extension_name" --extension-type "$extension_type" --no-wait 
    sleep 10

    echo "Checking readiness of extension type $extension_type"
    creating=true
    while $creating
    do  
        provisioning_state=$(az k8s-extension show --cluster-name $k8s_cluster_name -g $rg --cluster-type connectedClusters --name "$extension_name" --query "provisioningState" -o tsv)

        if [ $provisioning_state != "Creating" ]
        then
            creating=false
        fi

        sleep 3

    done

    echo "Extension type $extension_type passed creating. Collecting provisioned images"
    extension_images_file=$output_folder$extension_name".pod_images.txt"
    get_cluster_images $extension_images_file

done < $arc_extension_list_file

