from itertools import chain

import config
import json
import os
import re
import sys

target_sa = "azure-arc-kube-aad-proxy-sa"
scenario_descriptor = "1_arc_no_extensions"

##### CORE ####
admin_verb_list = ['*']
write_verb_list = ['approve', 'create', 'delete', 'deletecollection', 'escalate', 'impersonate', 'patch', 'proxy', 'sign', 'update']
read_verb_list  = ['get', 'list', 'watch']

def load_scenario_data(scenario_descriptor):
    scenario_files = [ os.path.join(config.rbac_folder, rbac_file) for rbac_file in os.listdir(config.rbac_folder) if scenario_descriptor in rbac_file]

    rbac_crb_file  = [ scenario_file for scenario_file in scenario_files if "_clusterrolebindings.json" in scenario_file ][0]
    rbac_cr_file   = [ scenario_file for scenario_file in scenario_files if "_clusterroles.json"        in scenario_file ][0]
    rbac_rb_file   = [ scenario_file for scenario_file in scenario_files if "_rolebindings.json"        in scenario_file ][0]
    rbac_role_file = [ scenario_file for scenario_file in scenario_files if "_roles.json"               in scenario_file ][0]

    rbac_crb_data  = filter_bindings_bound_to_sa(load_json_file(rbac_crb_file))
    rbac_rb_data   = filter_bindings_bound_to_sa(load_json_file(rbac_rb_file))
    rbac_cr_data   = load_json_file(rbac_cr_file)
    rbac_role_data = load_json_file(rbac_role_file)

    return rbac_crb_data, rbac_cr_data, rbac_rb_data, rbac_role_data 

def classify_rule_verb_level (verb_list):
    admin_verbs_in_list = [verb for verb in verb_list if verb in admin_verb_list]
    write_verbs_in_list = [verb for verb in verb_list if verb in write_verb_list]
    read_verbs_in_list  = [verb for verb in verb_list if verb in read_verb_list]
    
    if   len(admin_verbs_in_list) > 0:
        return "admin_level"
    elif len(write_verbs_in_list) > 0:
        return "write_level"
    elif len(read_verbs_in_list) > 0:
        return "read_level"   

def load_json_file(json_file):
    file_pointer = open(json_file)
    json_data    = json.load(file_pointer)

    return json_data

def filter_bindings_bound_to_sa(crb_or_rb_json_data):
    rbac_bindings_to_sa = [crb_or_rb for crb_or_rb in crb_or_rb_json_data['items'] if 'subjects' in crb_or_rb.keys() and len([subject for subject in crb_or_rb['subjects'] if subject['kind'] == 'ServiceAccount']) > 0]

    return rbac_bindings_to_sa

def get_roles_names_bound_to_sa(sa_name, role_data):
    role_names = [ rbac_bindings['roleRef']['name'] for rbac_bindings in role_data if len([subject for subject in rbac_bindings['subjects'] if subject['name'] == sa_name]) ]

    return role_names

def get_role_details(role_names_of_interest, role_list):
    role_rule_data_of_interest = [role for role in role_list['items'] if role['metadata']['name'] in role_names_of_interest ]
    role_details = [{'name':role['metadata']['name'], 'rules':[ {'resources': rules['resources'], 'verb_level': classify_rule_verb_level(rules['verbs'])} for rules in role['rules']]} for role in role_rule_data_of_interest ]

    return role_details

def print_details(rbac_roles_to_intended_sa_rule_list, role_type):

    if len(rbac_roles_to_intended_sa_rule_list) > 0:
        print("{} NAME; READ_RESOURCES; WRITE_RESOURCES; ADMIN_LEVEL".format(role_type))

    for rbac_role in rbac_roles_to_intended_sa_rule_list:
        rbac_role_name = rbac_role['name']

        admin_level_resources = ", ".join(sum([rbac_rule['resources'] for rbac_rule in rbac_role['rules'] if rbac_rule['verb_level'] == 'admin_level'], []) )
        write_level_resources = ", ".join(sum([rbac_rule['resources'] for rbac_rule in rbac_role['rules'] if rbac_rule['verb_level'] == 'write_level'], []) )
        read_level_resources  = ", ".join(sum([rbac_rule['resources'] for rbac_rule in rbac_role['rules'] if rbac_rule['verb_level'] == 'read_level'],  []) )
        print("{}; {}; {}; {}".format( rbac_role_name, read_level_resources, write_level_resources, admin_level_resources ) )

def get_role_details_to_sa(service_account_name):
    binding_data = rbac_rb_to_sa
    rbac_role_names_bound_to_intended_sa = get_roles_names_bound_to_sa(service_account_name, binding_data)
    rbac_role_to_intended_sa_rule_list   = get_role_details(rbac_role_names_bound_to_intended_sa, rbac_role_json_data)

    return rbac_cr_to_intended_sa_rule_list

def get_cr_details_to_sa(service_account_name):
    binding_data = rbac_crb_to_sa
    rbac_cr_names_bound_to_intended_sa   = get_roles_names_bound_to_sa(service_account_name, binding_data)
    rbac_cr_to_intended_sa_rule_list     = get_role_details(rbac_cr_names_bound_to_intended_sa, rbac_cr_json_data)

    return rbac_cr_to_intended_sa_rule_list

#LOAD JSON DATA FOR SCENARIO
rbac_crb_to_sa, rbac_cr_json_data, rbac_rb_to_sa, rbac_role_json_data = load_scenario_data(scenario_descriptor)

###  LOGIC ###
#GET THE CR DETAILS BOUND TO TARGET SA
rbac_cr_to_intended_sa_rule_list = get_cr_details_to_sa(target_sa)
print_details(rbac_cr_to_intended_sa_rule_list, "CLUSTER ROLES")


#GET ROLE NAMES BOUND TO TARGET SA
rbac_roles_to_intended_sa_rule_list = get_role_details_to_sa(target_sa)
print_details(rbac_roles_to_intended_sa_rule_list, "ROLES")

