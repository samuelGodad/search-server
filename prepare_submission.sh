#!/bin/bash

# Create submission directory
mkdir -p submission

# Copy source files
cp -r src submission/
cp -r tests submission/
cp config.ini submission/
cp setup_ubuntu.sh submission/
cp setup_ssl.sh submission/
cp run_tests.sh submission/
cp README.md submission/

# Remove unnecessary files and directories
rm -rf submission/src/__pycache__
rm -rf submission/tests/__pycache__
rm -rf submission/tests/.pytest_cache

# Create zip file
cd submission
zip -r ../search_server_submission.zip *
cd ..

# Clean up
rm -rf submission

echo "Submission package created: search_server_submission.zip" 