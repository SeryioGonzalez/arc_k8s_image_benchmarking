#PUT VARIABLES ONLY FOR PYTHON INTERWORKING

## THINGS YOU MIGHT WANT TO CHANGE
rg="sergiokubeRG"
region="westeurope"
vmUser="sergio"

## THINGS YOU MIGHT NOT NEED TO CHANGE
vnetName="k8svnet"
subnetName="k8ssubnet"
vnetPrefix="10.0.0.0/16"
subnetPrefix="10.0.0.0/24"
podsCidr="10.244.0.0/16"

vmSize="Standard_D4s_v3"
vmName="k8snode"
#DO NOT CHANGE VM SSH PORT HERE. THIS IS HARDCODED
ssh_vm_port="22222"

nsg_name="k8snsg"
k8s_cluster_name="k8s-cluster"
remote_cluster_kubeconfig="temp/k8s-kubeconfig"
arc_extension_list_file="arc_extension_list.txt"

#INSTALLERS
kubeadm_install_script="INSTALL_kubeadm_cluster.sh"
trivy_install_script="INSTALL_trivy_scanner.sh"

#FOLDERS
output_folder="output/"
image_scan_folder="output/image_scans/"
rbac_folder="output/rbac/"

#FILES
#MIND FOLDERS ARE DUPLICATED FOR PYTHON AND BASH COMPATIBILITY
pod_image_file_name_suffix=".pod_images.txt"
cluster_baseline_namespaces="output/0_cluster_baseline.namespaces.txt"
image_list_cluster_baseline="output/0_cluster_baseline.pod_images.txt"
image_list_cluster_arc_no_extensions="output/1_arc_no_extension.pod_images.txt"
all_image_list_file="output/all_images.txt"
trivy_results_file="output/trivy_image_scan.txt"


