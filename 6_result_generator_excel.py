from itertools import chain

import config
import json
import os
import re
import analyze_rbac

def process_result_line(result_line):
    processed_result_line = re.sub('[:()a-zA-Z,]', '', result_line.strip()).lstrip()
    processed_result_line = re.sub('  ', ' ', processed_result_line).split(" ")[1:]
    
    processed_result_line_int = [eval(i) for i in processed_result_line]

    return processed_result_line_int

def get_image_data_dict_list_from_file(image_list_file):
    image_lines = [re.sub(r"\s+", " ", line.replace("\n", "")) for line in open(image_list_file, 'r').readlines()]

    images = []
    for image_line in image_lines:
        image = {}
        image['namespace']           = image_line.split(" ")[0]
        image['pod_name']            = image_line.split(" ")[1]
        image['container_name']      = image_line.split(" ")[2]
        image['image']               = image_line.split(" ")[3]
        image['pod_service_account'] = image_line.split(" ")[4]

        #Process entries
        image['pod_name'] = re.sub(r"-[a-z0-9]{8,10}-[a-z0-9]{5}$", "", image['pod_name'])
        
        if 'registry.k8s.io' in image['image'] or 'kube-flannel' == image['namespace']:
            continue


        images.append( image)
    
    return images

def load_scanned_image_data():
    #This dictionary has the number of vulnerabilities per image
    image_scan_results = {}
    image_scan_files = [ os.path.join(config.image_scan_folder, image_scan_file) for image_scan_file in os.listdir(config.image_scan_folder) if ".txt" in image_scan_file]
    
    # Load image scan results
    for image_scan_file in image_scan_files:
        lines_in_file = open(image_scan_file, 'r').readlines()
        
        #Get the second line with image FQDN
        lines_of_interes_in_file = [lines_in_file[1].strip().split(" ")[0]]
        
        #Get all lines with Total:
        results_in_file = [process_result_line(line_in_file) for line_in_file in lines_in_file if 'Total:' in line_in_file]

        if len(results_in_file) > 1:
            results_in_file = [sum(column) for column in zip(*results_in_file)]
        else:
            results_in_file = list(chain(*results_in_file))

        lines_of_interes_in_file.extend(results_in_file)

        image_scan_results[lines_of_interes_in_file[0]] = {}
        image_scan_results[lines_of_interes_in_file[0]]['UNKNOWN']  = lines_of_interes_in_file[1]
        image_scan_results[lines_of_interes_in_file[0]]['LOW']      = lines_of_interes_in_file[2]
        image_scan_results[lines_of_interes_in_file[0]]['MEDIUM']   = lines_of_interes_in_file[3]
        image_scan_results[lines_of_interes_in_file[0]]['HIGH']     = lines_of_interes_in_file[4]
        image_scan_results[lines_of_interes_in_file[0]]['CRITICAL'] = lines_of_interes_in_file[5]

    return image_scan_results

def print_image_scan_result():
    #Read image scan data
    print (" -- PRINTING FOUND IMAGE VULNERABILITIES --")

    print("IMAGE_FQDN, UNKNOWN_VULNERABILITIES, LOW_VULNERABILITIES, MEDIUM_VULNERABILITIES, HIGH_VULNERABILITIES, CRITICAL_VULNERABILITES")
    image_scan_results = load_scanned_image_data()
    for image_key in image_scan_results.keys():
        image_url = image_key
        image_unknown_vulnerabilities  = image_scan_results[image_key]['UNKNOWN']
        image_low_vulnerabilities      = image_scan_results[image_key]['LOW']
        image_medium_vulnerabilities   = image_scan_results[image_key]['MEDIUM']
        image_high_vulnerabilities     = image_scan_results[image_key]['HIGH']
        image_critical_vulnerabilities = image_scan_results[image_key]['CRITICAL']

        image_vulnerability_data = "{},{},{},{},{},{}".format(image_url, image_unknown_vulnerabilities, image_low_vulnerabilities, image_medium_vulnerabilities, image_high_vulnerabilities, image_critical_vulnerabilities)

        print(image_vulnerability_data)

def get_extension_image_files():
    #Get all output files with image list suffix
    output_folder_images_file_list = [ config.output_folder + output_file for output_file in os.listdir(config.output_folder) if config.pod_image_file_name_suffix in output_file ]

    #Remove Arc base image file from extension image files
    output_folder_extension_images_file_list = [ output_folder_images_file for output_folder_images_file in output_folder_images_file_list if output_folder_images_file not in [config.image_list_cluster_baseline, config.image_list_cluster_arc_no_extensions]   ]

    return output_folder_extension_images_file_list

def get_extension_images(extension_images_file, arc_baseline_images):
    extension_images = get_image_data_dict_list_from_file(extension_images_file)
    exclusive_images_in_extension = [extension_image for extension_image in extension_images if extension_image not in arc_baseline_images]

    return exclusive_images_in_extension

#Get base Arc images
arc_baseline_images = get_image_data_dict_list_from_file(config.image_list_cluster_arc_no_extensions)

#print_image_scan_result()

#PRINT ARC BASE IMAGES
print ("")
print (" -- PRINTING FOUND IMAGES --")
print("ELEMENT; NAMESPACE; POD NAME; CONTAINER NAME; IMAGE FQDN; POD SERVICE ACCOUNT")
for arc_baseline_image in arc_baseline_images:
    rbac_data = analyze_rbac.get_sa_rbac_for_scenario(arc_baseline_image['pod_service_account'], "1_arc_no_extensions")
    image_data = "AzArc K8S Agent;{};{};{};{};{};{}".format(arc_baseline_image['namespace'], arc_baseline_image['pod_name'], arc_baseline_image['container_name'], arc_baseline_image['image'], arc_baseline_image['pod_service_account'], rbac_data)
    print(image_data)

output_folder_extension_images_file_list = get_extension_image_files()

#Load extension images
for extension_images_file in output_folder_extension_images_file_list:
    #Load a list of dictionaries with image data
    extension_images = get_extension_images(extension_images_file, arc_baseline_images)
    #Get extension name
    extension_name = extension_images_file.replace(config.output_folder, "").replace(config.pod_image_file_name_suffix, "")

    for extension_image in extension_images:
        image_data = "{} Arc extension,{},{},{},{},{}".format(extension_name, extension_image['namespace'], extension_image['pod_name'], extension_image['container_name'], extension_image['image'], extension_image['pod_service_account'])
        print(image_data)
