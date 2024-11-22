#!/bin/bash
# scripts/init_project.sh

# Create directory structure
mkdir -p jam/{config,core,consensus/{safrole,grandpa},crypto,network,pvm,services,storage,execution,api}
mkdir -p tests/{unit,integration,vectors}
mkdir -p scripts

# Create __init__.py files
find jam -type d -exec touch {}/__init__.py \;
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py