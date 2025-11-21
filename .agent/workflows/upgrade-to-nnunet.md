---
description: Upgrade from VGG16 to nnU-Net for brain tumor segmentation
---

# Upgrade to nnU-Net Model - Implementation Guide

## Prerequisites
- nnU-Net trained weights (Dataset002_BRATS19 or similar)
- .nii format dataset for testing
- Python environment with nnunetv2 installed

## Step 1: Install Required Dependencies

```bash
pip install nnunetv2
pip install nibabel
pip install SimpleITK
pip install scikit-image
```

## Step 2: Set Up nnU-Net Environment Variables

You need to configure nnU-Net paths:

```bash
# Windows PowerShell
$env:nnUNet_raw = "C:\Users\Home\Downloads\Brain-Tumor-Detection-main (1)\Brain-Tumor-Detection-main\nnunet_data\nnUNet_raw"
$env:nnUNet_preprocessed = "C:\Users\Home\Downloads\Brain-Tumor-Detection-main (1)\Brain-Tumor-Detection-main\nnunet_data\nnUNet_preprocessed"
$env:nnUNet_results = "C:\Users\Home\Downloads\Brain-Tumor-Detection-main (1)\Brain-Tumor-Detection-main\nnunet_weights"
```

## Step 3: Organize Your nnU-Net Weights

Place your trained model weights in this structure:
```
nnunet_weights/
└── Dataset002_BRATS19/  # Or your dataset name
    └── nnUNetTrainer__nnUNetPlans__3d_fullres/
        └── fold_0/  # or fold_all
            ├── checkpoint_final.pth
            └── plans.json
```

## Step 4: Create Utility Functions

### A. Image Converter (`utils/image_converter.py`)
Converts JPG/PNG to NIfTI format for nnU-Net processing

### B. Visualization Module (`utils/visualization.py`)
Creates overlay of segmentation on original image

## Step 5: Update Flask Backend (`app.py`)

Replace the VGG16 model loading and prediction with:
- nnU-Net inference pipeline
- Image format conversion
- Segmentation post-processing
- Overlay generation

## Step 6: Update React Frontend

Modify the UI to display:
- Original image
- Segmentation overlay
- Tumor statistics (volume, location)
- Multi-class visualization (if applicable)

## Step 7: Test the Pipeline

Test with:
1. .nii files (native format)
2. .jpg/.png files (converted format)
3. Multiple slices (if 3D volume)

## Expected Improvements

| Metric | Current (VGG16) | nnU-Net |
|--------|----------------|---------|
| Task | Binary classification | Pixel-wise segmentation |
| Accuracy | ~58% | 85-95% (typical for BraTS) |
| Output | Probability score | Precise tumor boundaries |
| Clinical Value | Low | High (surgical planning) |

## Notes
- nnU-Net expects 3D volumes, so 2D images need special handling
- You may need to create pseudo-3D volumes from single slices
- Consider using nnU-Net's 2D configuration if you only have 2D data
