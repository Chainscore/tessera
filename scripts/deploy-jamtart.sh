#!/bin/bash
set -e

# Configuration
RESOURCE_GROUP="tessera-testnet-rg"
LOCATION="eastus"
ACR_NAME="tesseratestnetacr"
ACI_NAME="jamtart"

echo "=== Deploying Jamtart (Telemetry) to Azure ==="

# Step 1: Ensure ACR Login (Skipped - using Cloud Build)
# echo "[1/4] Logging into ACR..."
# az acr login --name $ACR_NAME

ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer -o tsv)
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

# Step 2: Build and Push Images using ACR (Cloud Build)
echo "[2/4] Building and Pushing Images via ACR..."

# Import Postgres image directly from Docker Hub to ACR (server-side copy)
# This avoids pulling to local machine and pushing back
echo "Importing Postgres image..."
az acr import --name $ACR_NAME --source docker.io/library/postgres:16-alpine --image postgres:16-alpine-amd64 --force

# Build Jamtart Backend in the cloud
echo "Building Jamtart Backend..."
az acr build --registry $ACR_NAME --platform linux/amd64 --image tart-backend:latest ./jamtart

# Step 3: Delete existing ACI if exists
echo "[3/4] Checking/Cleaning existing deployment..."
az container delete --resource-group $RESOURCE_GROUP --name $ACI_NAME --yes 2>/dev/null || true

# Step 4: Deploy ACI
echo "[4/4] Deploying Container Group..."

# Ensure we have the postgres image in ACR (sanity check/push)
# We assume it was pushed earlier as tesseratestnetacr.azurecr.io/postgres:16-alpine-amd64
# If not, we might need to pull and push it again, but let's assume it's there from previous steps.

cat > jamtart-deploy.yaml << EOF
apiVersion: '2021-10-01'
name: $ACI_NAME
location: $LOCATION
properties:
  osType: Linux
  restartPolicy: Always
  ipAddress:
    type: Public
    ports:
      - port: 8080
        protocol: TCP
      - port: 9000
        protocol: TCP
    dnsNameLabel: jamtart-${RANDOM}
  imageRegistryCredentials:
    - server: $ACR_LOGIN_SERVER
      username: $ACR_USERNAME
      password: $ACR_PASSWORD
  containers:
    - name: postgres
      properties:
        image: $ACR_LOGIN_SERVER/postgres:16-alpine-amd64
        ports:
          - port: 5432
            protocol: TCP
        environmentVariables:
          - name: POSTGRES_USER
            value: tart
          - name: POSTGRES_PASSWORD
            value: tart_password
          - name: POSTGRES_DB
            value: tart_telemetry
        resources:
          requests:
            cpu: 0.5
            memoryInGB: 1
    - name: tart-backend
      properties:
        image: $ACR_LOGIN_SERVER/tart-backend:latest
        ports:
          - port: 8080
            protocol: TCP
          - port: 9000
            protocol: TCP
        environmentVariables:
          - name: DATABASE_URL
            value: postgres://tart:tart_password@localhost:5432/tart_telemetry
          - name: TELEMETRY_BIND
            value: 0.0.0.0:9000
          - name: API_BIND
            value: 0.0.0.0:8080
        resources:
          requests:
            cpu: 0.5
            memoryInGB: 1
EOF

az container create --resource-group $RESOURCE_GROUP --file jamtart-deploy.yaml

# Output Results
FQDN=$(az container show --resource-group $RESOURCE_GROUP --name $ACI_NAME --query ipAddress.fqdn -o tsv)
echo ""
echo "=== Jamtart Deployed Successfully ==="
echo "Dashboard API: http://$FQDN:8080"
echo "Telemetry URL: $FQDN:9000"
echo ""
echo "Run: curl http://$FQDN:8080/api/health"
