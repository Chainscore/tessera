#!/bin/bash
# Script to build and deploy individual JAM node to Azure Container Instances
#
# Usage:
#   export GITHUB_TOKEN="your_github_token_here"  # Required for private submodules
#   ./scripts/deploy-6-nodes-to-azure.sh
#
# Prerequisites:
#   - Docker with buildx support
#   - Azure CLI logged in
#   - Access to tessera.azurecr.io
#   - GitHub token with access to private submodules
#
set -e

# Configuration
RESOURCE_GROUP="tessera"
IMAGE_NAME="tessera.azurecr.io/tessera/jam-single-node:latest"
ACR_NAME="tessera"
CPU="2"
MEMORY="4"
DEBUG_MODE="true"  # Set to "true" for debugging, "false" for normal operation

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Init only the required submodules
if [ -z "${GITHUB_TOKEN:-}" ]; then
  echo -e "${YELLOW}Warning: GITHUB_TOKEN not set"
  git submodule init deps/tsrkit-pvm
  git submodule init deps/py-ark-vrf
  git submodule init deps/rockstore
  git submodule init deps/tsrkit-asm
  git submodule init deps/tsrkit-types
else
  echo -e "${GREEN}Init required submodules only..."
  git -c "url.https://x-access-token:${GITHUB_TOKEN}@github.com/.insteadOf=https://github.com/" \
    submodule update --recursive --depth 0 \
    deps/tsrkit-pvm deps/py-ark-vrf deps/rockstore deps/tsrkit-asm deps/tsrkit-types
fi

# Update those submodules using the token for auth
git -c "url.https://x-access-token:${GITHUB_TOKEN}@github.com/.insteadOf=https://github.com/" \
  submodule update --recursive --depth 0 \
  deps/tsrkit-pvm deps/py-ark-vrf deps/rockstore deps/tsrkit-asm deps/tsrkit-types

echo -e "${GREEN}Ensure az and docker are available...${NC}"
command -v az >/dev/null || { echo -e "${RED}az CLI not found${NC}"; exit 1; }
command -v docker >/dev/null || { echo -e "${RED}docker not found${NC}"; exit 1; }

echo -e "${GREEN}Login to Azure (if not already)...${NC}"
az account show >/dev/null || { echo -e "${YELLOW}Please run 'az login' first${NC}"; exit 1; }

echo -e "${GREEN}Login to ACR: $ACR_NAME...${NC}"
az acr login --name "$ACR_NAME" || { echo -e "${RED}az acr login failed${NC}"; exit 1; }

echo -e "${GREEN}Preparing buildx builder...${NC}"
docker buildx create --use --name amd64builder 2>/dev/null || docker buildx use amd64builder || true

# Build
echo -e "${GREEN}Building and pushing image: $IMAGE_NAME${NC}"
BUILD_CMD=(docker buildx build --no-cache --platform linux/amd64 -f Dockerfile.node -t "$IMAGE_NAME" --push .)
if [ -n "${GITHUB_TOKEN:-}" ]; then
  BUILD_CMD+=(--build-arg "GITHUB_TOKEN=$GITHUB_TOKEN")
fi
"${BUILD_CMD[@]}"

echo -e "${GREEN}Prepare ACR credentials for ACI (if needed)${NC}"
ACR_USERNAME=$(az acr credential show --name "$ACR_NAME" --query "username" -o tsv 2>/dev/null || true)
ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query "passwords[0].value" -o tsv 2>/dev/null || true)

REGISTRY_ARGS=()
if [ -n "$ACR_USERNAME" ] && [ -n "$ACR_PASSWORD" ]; then
  REGISTRY_ARGS=(--registry-login-server "$ACR_NAME.azurecr.io" --registry-username "$ACR_USERNAME" --registry-password "$ACR_PASSWORD")
else
  echo -e "${YELLOW}ACR admin creds not available. Will rely on subscription-level pull permissions (recommended).${NC}"
fi

#echo -e "${GREEN}Deleting existing container if present...${NC}"
#if az container show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME" >/dev/null 2>&1; then
#  az container delete --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME" --yes
#fi

nodes=(
  "40000 19800 envs/40000.env tessera-node-alice"
  "40001 19801 envs/40001.env tessera-node-bob"
  "40002 19802 envs/40002.env tessera-node-charlie"
  "40003 19803 envs/40003.env tessera-node-dave"
  "40004 19804 envs/40004.env tessera-node-eve"
  "40005 19805 envs/40005.env tessera-node-fergie"
)

for node in "${nodes[@]}"; do
  read -r udp_port tcp_port envfile CONTAINER_NAME <<< "$node"

  echo "$udp_port, $tcp_port, $envfile $CONTAINER_NAME"

  # Check if container already exists
  echo -e "${GREEN}Checking if $CONTAINER_NAME container exists...${NC}"

  if az container show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME" >/dev/null 2>&1; then
    echo -e "${YELLOW} $CONTAINER_NAME container exists — attempting graceful restart to pick up latest image...${NC}"

    MAX_RETRIES=3
    RETRY_COUNT=0
    RESTARTED=false

    while [ $RETRY_COUNT -lt $MAX_RETRIES ] && [ "$RESTARTED" != "true" ]; do
      echo -e "${YELLOW}Restart attempt $((RETRY_COUNT+1))/${MAX_RETRIES}${NC}"
      if az container restart --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME"; then
        RESTARTED=true
        echo -e "${GREEN}Restart command succeeded.${NC}"
      else
          RETRY_COUNT=$((RETRY_COUNT+1))
          if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            echo -e "${RED}Restart command failed. Retrying in 30s...${NC}"
            sleep 30
          else
            echo -e "${RED}Failed to restart container after ${MAX_RETRIES} attempts. Fetching logs for debugging...${NC}"
            exit 1
        fi
      fi
    done
  else
    echo "Container $CONTAINER_NAME does not exist, creating new container instance..."
    # For new deployments, create the container from scratch
    MAX_RETRIES=3
    RETRY_COUNT=0
    CREATED=false


    while [ $RETRY_COUNT -lt $MAX_RETRIES ] && [ "$CREATED" != "true" ]; do
      echo "Attempt $(($RETRY_COUNT+1)) to create $CONTAINER_NAME container instance..."
      if az container create --resource-group "$RESOURCE_GROUP" --file "deploy-yml/${CONTAINER_NAME}.yaml" "${REGISTRY_ARGS[@]}"; then
        CREATED=true
        echo "Container $CONTAINER_NAME created successfully! "
      else
        echo "Failed to create $CONTAINER_NAME container. Retrying in 30 seconds..."
        RETRY_COUNT=$((RETRY_COUNT+1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
          sleep 30
        else
          echo "Failed to create $CONTAINER_NAME container after $MAX_RETRIES attempts."
        fi
      fi
    done
  fi

  # Status
  sleep 10
  STATUS=$(az container show --resource-group "$RESOURCE_GROUP" --name "$CONTAINER_NAME" --query "instanceView.state" -o tsv 2>/dev/null || echo "")
  if [ "$STATUS" = "Running" ]; then
    echo -e "${GREEN}Container is Running${NC}"
  else
    echo -e "${YELLOW}Container status: $STATUS${NC}"
  fi

  echo -e "${YELLOW}To see container logs (if Running):${NC}"
  echo "az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME"

  if [ "$DEBUG_MODE" = "true" ]; then
    echo -e "${YELLOW}To exec into container (if Running):${NC}"
    echo "az container exec --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --exec-command /bin/bash"
  fi
done
