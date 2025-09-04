#!/bin/bash
set -e

# Obfuscate the code with PyArmor
pyarmor gen -O dist-obf -r jam

# Build the binary with PyInstaller
pyinstaller --clean Tessera.spec
