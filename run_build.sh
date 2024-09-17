#!/bin/bash

# Build the package
python -m build

# Uninstall existing package
pip uninstall -y pyopengenai

# Install the newly built package
pip install dist/pyopengenai-0.1.6-py3-none-any.whl

echo "Build and installation completed."