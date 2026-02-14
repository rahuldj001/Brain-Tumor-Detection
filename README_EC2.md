# Deploying to AWS EC2 (Plain Virtual Machine)

This guide explains how to deploy the **nnU-Net Brain Tumor Detection** app on a standard AWS EC2 instance (Ubuntu).

## Prerequisites

1.  **AWS Account**
2.  **Model Weights**: You must have your trained model weights (the `Dataset002_BRATS19` folder) zipped and uploaded to an S3 bucket.
    -   Example S3 URI: `s3://my-brain-tumor-bucket/weights.zip`
    -   **Important**: Zip the *folder* `Dataset002_BRATS19`, not just the contents.

## Step 1: Launch EC2 Instance

1.  Go to **EC2 Dashboard** > **Launch Instance**.
2.  **OS**: Ubuntu Server 22.04 LTS (recommended).
3.  **Instance Type**: `t3.medium` (4GB RAM) or larger.
    -   *Warning*: `t2.micro` (1GB) is likely too small and may crash.
4.  **Key Pair**: Select an existing key or create a new one (to SSH into the server).
5.  **Network Settings**: Allow HTTP (Port 80) and Custom TCP (Port 5000).
6.  **IAM Instance Profile** (CRITICAL):
    -   Create a new IAM Role with `AmazonS3ReadOnlyAccess`.
    -   Attach this role to your EC2 instance in the Advanced Details section.
    -   *Why?* This allows the EC2 instance to download your weights from S3 without hardcoding API keys.

## Step 2: Prepare the Code

1.  SSH into your instance:
    ```bash
    ssh -i "your-key.pem" ubuntu@ec2-xx-xx-xx-xx.compute-1.amazonaws.com
    ```
2.  Clone your repository or upload your files.
    ```bash
    git clone <your-repo-url>
    cd <repo-folder>
    ```

## Step 3: Run Setup Script

We have provided a script `setup_ec2.sh` to automate the dependencies and weight download.

1.  Make the script executable:
    ```bash
    chmod +x setup_ec2.sh
    ```
2.  Run the script with your S3 path:
    ```bash
    ./setup_ec2.sh s3://your-bucket-name/weights.zip
    ```

## Step 4: Start the Server

Once setup is complete:

1.  Activate the virtual environment:
    ```bash
    source venv/bin/activate
    ```
2.  Start the application with Gunicorn:
    ```bash
    # Run in background (production mode)
    gunicorn --bind 0.0.0.0:5000 app_nnunet:app --daemon
    ```

The application is now running on port 5000!

## Step 5: Access the App

check your EC2 Security Group allows inbound traffic on port 5000.
Visit: `http://<your-ec2-public-ip>:5000`

## Optional: Set up Nginx (Mock production)

To serve on port 80 (standard HTTP) instead of 5000, install Nginx:

```bash
sudo apt install nginx
```

Configure Nginx to proxy requests to localhost:5000.
