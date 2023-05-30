source config.sh
source 0_environment_checks.sh

vm_public_ip=$(az network public-ip show -n "$vmName-public-ip" -g $rg --query "ipAddress" -o tsv)

echo "Checking if trivy is installed"
trivy_output=$(ssh -p 22222 $vm_public_ip "trivy -v 2>&1 >/dev/null")
if [ "$trivy_output" = "bash: trivy: command not found" ]
then
    echo "Trivy is not installed. Installing"
    install_script=$trivy_install_script
    scp -q -o StrictHostKeyChecking=no -P 22222 $install_script $vm_public_ip:/home/$vmUser/$install_script
    ssh -p 22222 $vm_public_ip "chmod +x /home/$vmUser/$install_script; /home/$vmUser/$install_script"
else
    echo "Trivy is installed"
fi

echo "Listing all deployed images in K8S cluster"
find $output_folder -type f -name "*pod_images.txt" -exec awk '{print $4}' {} \; | sort | uniq > $all_image_list_file

mkdir -p $image_scan_folder

image_id=0
for image in $(cat $all_image_list_file)
do
    echo "Scaning $image"
    ssh -p 22222 $vm_public_ip "trivy image -q $image"         > $image_scan_folder$image_id"_image_scan.txt"
    ssh -p 22222 $vm_public_ip "trivy image -q $image -f json" > $image_scan_folder$image_id"_image_scan.json"
    image_id=$((image_id+1))
done
