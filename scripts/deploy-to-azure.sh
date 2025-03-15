#!/bin/bash
# Script to build and deploy the JAM node to Azure Container Instances
set -e

# Configuration
RESOURCE_GROUP="tessera"
CONTAINER_NAME="tessera-node"
IMAGE_NAME="tessera.azurecr.io/tessera/jam-node:latest"
ACR_NAME="tessera"
CPU="2"
MEMORY="4"
DEBUG_MODE="true"  # Set to "true" for debugging, "false" for normal operation

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building Docker image for amd64 platform...${NC}"
docker buildx create --use --name amd64builder || echo "Builder already exists"
docker buildx build --no-cache --platform linux/amd64 -t $IMAGE_NAME --push .

echo -e "${GREEN}Pushing to Azure Container Registry...${NC}"
az acr login --name $ACR_NAME
docker push $IMAGE_NAME

echo -e "${GREEN}Checking if container exists...${NC}"
if az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME >/dev/null 2>&1; then
    echo -e "${YELLOW}Container exists, deleting...${NC}"
    az container delete --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --yes
fi

# Get ACR credentials
echo -e "${GREEN}Getting ACR credentials...${NC}"
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query "username" -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

if [ -z "$ACR_USERNAME" ] || [ -z "$ACR_PASSWORD" ]; then
    echo -e "${RED}Failed to get ACR credentials. Make sure you're logged in and have access to the ACR.${NC}"
    exit 1
fi

echo -e "${GREEN}Creating container in Azure...${NC}"
az container create \
    --resource-group $RESOURCE_GROUP \
    --name $CONTAINER_NAME \
    --image $IMAGE_NAME \
    --registry-login-server "$ACR_NAME.azurecr.io" \
    --registry-username "$ACR_USERNAME" \
    --registry-password "$ACR_PASSWORD" \
    --cpu $CPU \
    --memory $MEMORY \
    --environment-variables JAM_DEBUG=$DEBUG_MODE \
    --ports 30333 \
    --dns-name-label "tessera-jam-node" \
    --restart-policy Never \
    --os-type Linux

echo -e "${GREEN}Container created!${NC}"
echo -e "${GREEN}Container logs:${NC}"
az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME

if [ "$DEBUG_MODE" = "true" ]; then
    echo -e "${YELLOW}Container running in DEBUG mode${NC}"
    echo -e "${YELLOW}To access container shell:${NC}"
    echo -e "az container exec --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --exec-command /bin/bash"
    echo -e "${YELLOW}To view logs:${NC}"
    echo -e "az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME"
    echo -e "${YELLOW}To attach to container:${NC}"
    echo -e "az container attach --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME"
    
    # Let's try to exec into the container right away
    echo -e "${GREEN}Trying to access container shell...${NC}"
    echo -e "${YELLOW}(If this fails, wait a minute and try the command manually)${NC}"
    sleep 10
    az container exec --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --exec-command "/bin/bash -c 'ls -la /app/data || echo \"No data directory yet\"'"
fi 