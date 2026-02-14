#!/bin/bash

# EC2 Setup Script for Brain Tumor Detection (nnU-Net)
# Usage: ./setup_ec2.sh <S3_URI_TO_WEIGHTS_ZIP>
# Example: ./setup_ec2.sh s3://my-bucket/weights.zip

S3_WEIGHTS_URI=$1

if [ -z "$S3_WEIGHTS_URI" ]; then
    echo "Usage: ./setup_ec2.sh <S3_URI_TO_WEIGHTS_ZIP>"
    echo "Please provide the S3 URI where your weights ZIP file is stored."
    exit 1
fi

echo "============================================="
echo "Starting EC2 Setup for Brain Tumor Detection"
echo "============================================="

# 1. System Updates & Dependencies
echo "[1/5] Updating system and installing dependencies..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv awscli unzip

# 2. Python Environment Setup
echo "[2/5] Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install project requirements
echo "Installing Python packages from requirements.txt..."
pip install -r requirements.txt

# 3. AWS Configuration (Optional check)
echo "[3/5] Checking AWS identity..."
# We assume the EC2 instance has an IAM Role attached with S3 access.
# If not, 'aws s3 cp' will fail.
aws sts get-caller-identity > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "⚠️  Warning: AWS CLI not configured or missing IAM role."
    echo "    Make sure this EC2 instance has an IAM Role with S3 Read access."
fi

# 4. Download Weights from S3
echo "[4/5] Downloading model weights from S3..."
echo "      Source: $S3_WEIGHTS_URI"

# directory structure expected by app_nnunet.py:
# nnunet_weights/Dataset002_BRATS19/nnUNetTrainer__nnUNetPlans__3d_fullres
mkdir -p nnunet_weights

# Download the zip file
aws s3 cp "$S3_WEIGHTS_URI" weights.zip

if [ $? -eq 0 ]; then
    echo "✓ Download successful."
    echo "Unzipping weights..."
    # Unzip into nnunet_weights directory
    # Structure inside zip should ideally be: Dataset002_BRATS19/...
    unzip -o weights.zip -d nnunet_weights/
    rm weights.zip
else
    echo "✗ Error: Failed to download weights from S3."
    echo "  Please check the S3 URI and IAM permissions."
    exit 1
fi

# 5. Final Setup
echo "[5/5] Setup complete!"
echo "============================================="
echo "To start the application:"
echo "1. Activate environment: source venv/bin/activate"
echo "2. Run server:           gunicorn --bind 0.0.0.0:5000 app_nnunet:app"
echo "============================================="
