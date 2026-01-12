#!/bin/bash
# Deploy Tessera testnet to Azure Container Instances
# Uses Azure ACR Build (cloud build) - no local Docker required
#
# Usage:
#   ./scripts/deploy-testnet.sh                           # Without telemetry
#   ./scripts/deploy-testnet.sh <telemetry_host:port>     # With telemetry
#
set -e

# Configuration
RESOURCE_GROUP="tessera-testnet-rg"
LOCATION="eastus"
ACR_NAME="tesseratestnetacr"
ACI_NAME="tessera-testnet"
DNS_LABEL="tessera-testnet"
TELEMETRY_HOST="${1:-}"

echo "=== Deploying Tessera Testnet to Azure ==="

# Get ACR credentials
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer -o tsv)
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

# Step 1: Build image via Azure Cloud Build
echo "[1/3] Building Tessera image via ACR (cloud build)..."
az acr build --registry $ACR_NAME --platform linux/amd64 --image tessera:latest .

# Step 2: Delete existing ACI
echo "[2/3] Cleaning existing deployment..."
az container delete --resource-group $RESOURCE_GROUP --name $ACI_NAME --yes 2>/dev/null || true

# Step 3: Deploy
echo "[3/3] Deploying container..."
if [ -n "$TELEMETRY_HOST" ]; then
    echo "  Telemetry: $TELEMETRY_HOST"
fi

az container create \
  --resource-group $RESOURCE_GROUP \
  --name $ACI_NAME \
  --image $ACR_LOGIN_SERVER/tessera:latest \
  --registry-login-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --cpu 4 --memory 8 \
  --ports 19800 \
  --ip-address Public \
  --dns-name-label $DNS_LABEL \
  --environment-variables TELEMETRY_HOST="$TELEMETRY_HOST" \
  --restart-policy Always \
  --location $LOCATION

# Output
FQDN=$(az container show --resource-group $RESOURCE_GROUP --name $ACI_NAME --query ipAddress.fqdn -o tsv)
echo ""
echo "=== Tessera Testnet Deployed ==="
echo "RPC: http://$FQDN:19800"
echo ""
echo "Verify: curl -X POST -H 'Content-Type: application/json' -d '{\"jsonrpc\":\"2.0\",\"method\":\"bestBlock\",\"params\":[],\"id\":1}' http://$FQDN:19800"
