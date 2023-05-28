
sudo apt-get install wget apt-transport-https gnupg lsb-release -y > /dev/null

sudo mkdir -p /etc/apt/keyrings/
curl -fsSL https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo gpg --dearmor -o /etc/apt/keyrings/trivy.gpg > /dev/null
sudo install -m 0755 -d /etc/apt/keyrings
sudo chmod a+r /etc/apt/keyrings/trivy.gpg 

echo "deb [signed-by=/etc/apt/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee /etc/apt/sources.list.d/trivy.list > /dev/null
sudo apt-get update -y > /dev/null

sudo apt-get install trivy -y > /dev/null