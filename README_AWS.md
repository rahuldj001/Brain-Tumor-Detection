# AWS Deployment Guide for Brain Tumor Detection (nnU-Net)

This project has been optimized for AWS Elastic Beanstalk (Python platform).

## ⚠️ Important: Model Weights

The nnU-Net model weights are **too large** to be included in the git repository or simple deployment zip. You must ensure the weights are present on the server.

### Option 1: Included in Deployment (If < 500MB zip limit)
If you are uploading a ZIP file to AWS, you can include the `nnunet_weights` folder in the zip structure:

```
myapp.zip
├── app_nnunet.py
├── requirements.txt
├── Procfile
└── nnunet_weights/
    └── Dataset002_BRATS19/
        └── nnUNetTrainer__nnUNetPlans__3d_fullres/
            ├── checkpoint_final.pth
            └── ... (other files)
```

### Option 2: Download During Initialization (Recommended for S3)
If you store your weights in an S3 bucket, you should create an `.ebextensions` script to download them on deployment.

1. Create a folder `.ebextensions`
2. Add a config file (e.g., `01_download_weights.config`) that runs a command to download and extract weights from S3 to `nnunet_weights/`.

## 🚀 Deployment Steps

1. **Prepare ZIP**: Select all files in this directory (not the parent directory) and zip them.
   - Ensure `app_nnunet.py`, `Procfile`, and `requirements.txt` are at the root of the zip.
2. **Create Environment**:
   - Go to AWS Elastic Beanstalk console.
   - Create a new environment (Web Server environment).
   - Platform: **Python 3.10**.
   - Application Code: Upload your zip file.
3. **Configuration**:
   - Verify `WSGIPath` is set to `app_nnunet:app` (automatically handled by Procfile usually, but check configuration).
4. **Environment Variables** (Optional):
   - You can set `NNUNET_WEIGHTS_PATH` if you change the default location.

## 🛠 Troubleshooting

- **502 Bad Gateway**: Check logs (`/var/log/web.stdout.log`). It usually means the application failed to start (likely missing weights or memory issues).
- **Memory Errors**: nnU-Net is memory intensive. Ensure you use an instance type with at least **4GB RAM** (e.g., `t3.medium` or larger). `t2.micro` (free tier) WILL NOT WORK.
