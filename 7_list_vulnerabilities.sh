source config.sh
source 0_environment_checks.sh

found_vulnerabilities="found_vulnerabilities.txt"
echo "" > $found_vulnerabilities

found_root_shell_vulnerabilities="found_root_shell_vulnerabilities.txt"
echo "" > $found_root_shell_vulnerabilities

for json_vulnerability_file in $(find $image_scan_folder -type f -name "*json")
do 
    jq -r ".Results[].Vulnerabilities[] | .VulnerabilityID, .Severity" $json_vulnerability_file 2> /dev/null | awk '/CVE/ {vulnerability_id=$1; getline; severity=$1; print severity " " vulnerability_id}' >> $found_vulnerabilities
done 

for root_shell_exploits in $(cat root_shell.exploits.txt)
do
    grep $root_shell_exploits $found_vulnerabilities >> $found_root_shell_vulnerabilities
done

for found_root_shell_vulnerabilities in $(cat $found_root_shell_vulnerabilities)
do
    grep $found_root_shell_vulnerabilities $image_scan_folder*txt
done