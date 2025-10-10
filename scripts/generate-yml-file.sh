#!/bin/bash
# Script to create yaml files for deployment

set -euo pipefail

nodes=(
  "40000 19800 envs/40000.env tessera-node-alice eastus"
  "40001 19801 envs/40001.env tessera-node-bob westus"
  "40002 19802 envs/40002.env tessera-node-charlie westeurope"
  "40003 19803 envs/40003.env tessera-node-dave northeurope"
  "40004 19804 envs/40004.env tessera-node-eve eastasia"
  "40005 19805 envs/40005.env tessera-node-fergie centralindia"
)

# Configuration
RESOURCE_GROUP="tessera"
IMAGE_NAME="tessera.azurecr.io/tessera/jam-single-node:latest"
ACR_NAME="tessera"
CPU="2"
MEMORY="4"
DEBUG_MODE="true"  # Set to "true" for debugging, "false" for normal operation

for node in "${nodes[@]}"; do
  read -r udp_port tcp_port envfile CONTAINER_NAME LOCATION <<< "$node"

  echo "Preparing: udp=$udp_port tcp=$tcp_port env=$envfile name=$CONTAINER_NAME"
  YAML_PATH="${CONTAINER_NAME}.yaml"

  cat > "deploy-yml/$YAML_PATH" <<EOF
apiVersion: 2021-10-01
location: ${LOCATION}
name: ${CONTAINER_NAME}
properties:
  containers:
    - name: ${CONTAINER_NAME}
      properties:
        image: ${IMAGE_NAME}
        command:
          - /usr/local/bin/node-entrypoint.sh
          - ${envfile}
        ports:
          - port: ${tcp_port}
            protocol: TCP
          - port: ${udp_port}
            protocol: UDP
        resources:
          requests:
            cpu: ${CPU}
            memoryInGb: ${MEMORY}
        environmentVariables:
          - name: JAM_DEBUG
            value: "${DEBUG_MODE}"
  osType: Linux
  restartPolicy: Never
  ipAddress:
    type: Public
    dnsNameLabel: ${CONTAINER_NAME}
    ports:
      - port: ${tcp_port}
        protocol: TCP
      - port: ${udp_port}
        protocol: UDP
EOF
done
