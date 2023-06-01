from itertools import chain

import config
import json
import os
import re
import sys

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
    rbac_cr_data   = load_json_file(rbac_cr_file)['items']
    rbac_rb_data   = filter_bindings_bound_to_sa(load_json_file(rbac_rb_file))
    rbac_role_data = load_json_file(rbac_role_file)['items']

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
    role_rule_data_of_interest = [role for role in role_list if role['metadata']['name'] in role_names_of_interest ]
    
    if(len(role_rule_data_of_interest) > 0):
        role_details = [{'name':role['metadata']['name'], 'rules':[ {'resources': rules['resources'], 'verb_level': classify_rule_verb_level(rules['verbs'])} for rules in role['rules'] if 'resources' in rules.keys()  ]} for role in role_rule_data_of_interest ]
        return role_details
    else:
        return ""

def get_details(rbac_cr, rbac_role):
    if len(rbac_cr) > 1:
        print ("MORE THAN ONE CR")
        sys.exit(1)

    if len(rbac_role) > 1:
        print ("MORE THAN ONE ROLE")
        sys.exit(1)

    if len(rbac_role) > 0:
        rbac_role = rbac_role[0]
        rbac_role_name = rbac_role['name']

        rbac_role_admin_level_resources = ", ".join(sum([rbac_rule['resources'] for rbac_rule in rbac_role['rules'] if rbac_rule['verb_level'] == 'admin_level'], []) )
        rbac_role_write_level_resources = ", ".join(sum([rbac_rule['resources'] for rbac_rule in rbac_role['rules'] if rbac_rule['verb_level'] == 'write_level'], []) )
        rbac_role_read_level_resources  = ", ".join(sum([rbac_rule['resources'] for rbac_rule in rbac_role['rules'] if rbac_rule['verb_level'] == 'read_level'],  []) )
    else:
        rbac_role_name = " "
        rbac_role_admin_level_resources = " "
        rbac_role_write_level_resources = " "
        rbac_role_read_level_resources  = " "

    if len(rbac_cr) > 0:
        rbac_cr = rbac_cr[0]
        rbac_cr_name = rbac_cr['name']
        
        rbac_cr_admin_level_resources = ", ".join(sum([rbac_rule['resources']  for rbac_rule in rbac_cr['rules'] if rbac_rule['verb_level'] == 'admin_level'], []) )
        rbac_cr_write_level_resources = ", ".join(sum([rbac_rule['resources']  for rbac_rule in rbac_cr['rules'] if rbac_rule['verb_level'] == 'write_level'], []) )
        rbac_cr_read_level_resources  = ", ".join(sum([rbac_rule['resources']  for rbac_rule in rbac_cr['rules'] if rbac_rule['verb_level'] == 'read_level' ], []) )

        if rbac_cr_write_level_resources == "":
            rbac_cr_write_level_resources = " " 

        if rbac_cr_read_level_resources == "":
            rbac_cr_read_level_resources = " " 

    else:
        rbac_cr_name = " "
        rbac_cr_admin_level_resources = " "
        rbac_cr_write_level_resources = " "
        rbac_cr_read_level_resources  = " "

    rbac_string = "{}; {}; {}; {}; {}; {}; {}; {}".format( rbac_role_name, rbac_role_read_level_resources, rbac_role_write_level_resources, rbac_role_admin_level_resources, rbac_cr_name, rbac_cr_read_level_resources, rbac_cr_write_level_resources, rbac_cr_admin_level_resources ) 

    return rbac_string

def get_role_or_cluster_role_details_to_sa(service_account_name, binding_data, rbac_role_json_data):
    rbac_role_names_bound_to_intended_sa = get_roles_names_bound_to_sa(service_account_name, binding_data)
    rbac_role_to_intended_sa_rule_list   = get_role_details(rbac_role_names_bound_to_intended_sa, rbac_role_json_data)

    return rbac_role_to_intended_sa_rule_list

def get_sa_rbac_for_scenario(target_sa, scenario_descriptor):
    #LOAD JSON DATA FOR SCENARIO
    rbac_crb_to_sa, rbac_cr_json_data, rbac_rb_to_sa, rbac_role_json_data = load_scenario_data(scenario_descriptor)

    ###  LOGIC ###
    #GET THE CR DETAILS BOUND TO TARGET SA
    rbac_cr_to_intended_sa_rule_list    = get_role_or_cluster_role_details_to_sa(target_sa, rbac_crb_to_sa, rbac_cr_json_data)
    
    #GET ROLE NAMES BOUND TO TARGET SA
    rbac_roles_to_intended_sa_rule_list = get_role_or_cluster_role_details_to_sa(target_sa, rbac_rb_to_sa, rbac_role_json_data)
    
    rbac_data = get_details(rbac_cr_to_intended_sa_rule_list, rbac_roles_to_intended_sa_rule_list)
    
    return rbac_data

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("PROVIDE SERVICE_ACCOUNT_NAME AND SCENARIO")
        sys.exit(1)

    target_sa           = sys.argv[1]
    scenario_descriptor = sys.argv[2]

    rbac_for_scenario = get_sa_rbac_for_scenario(target_sa, scenario_descriptor)

    print( rbac_for_scenario)