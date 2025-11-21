# nnU-Net Brain Tumor Segmentation - Setup Script
# Run this script to complete the installation and setup

Write-Host "=" -NoNewline; Write-Host ("=" * 59)
Write-Host "nnU-Net Brain Tumor Segmentation - Setup"
Write-Host "=" -NoNewline; Write-Host ("=" * 59)

# Step 1: Install nnunetv2
Write-Host "`n[1/3] Installing nnunetv2..."
pip install nnunetv2

# Step 2: Set up nnU-Net environment variables
Write-Host "`n[2/3] Setting up nnU-Net environment variables..."

$projectRoot = $PSScriptRoot
$nnunetRaw = Join-Path $projectRoot "nnunet_data\nnUNet_raw"
$nnunetPreprocessed = Join-Path $projectRoot "nnunet_data\nnUNet_preprocessed"
$nnunetResults = Join-Path $projectRoot "nnunet_weights"

# Create directories if they don't exist
New-Item -ItemType Directory -Force -Path $nnunetRaw | Out-Null
New-Item -ItemType Directory -Force -Path $nnunetPreprocessed | Out-Null

# Set environment variables for current session
$env:nnUNet_raw = $nnunetRaw
$env:nnUNet_preprocessed = $nnunetPreprocessed
$env:nnUNet_results = $nnunetResults

Write-Host "  nnUNet_raw = $nnunetRaw"
Write-Host "  nnUNet_preprocessed = $nnunetPreprocessed"
Write-Host "  nnUNet_results = $nnunetResults"

# Step 3: Verify installation
Write-Host "`n[3/3] Verifying installation..."

# Check if model weights exist
$weightsPath = Join-Path $nnunetResults "Dataset002_BRATS19\nnUNetTrainer__nnUNetPlans__3d_fullres"
if (Test-Path $weightsPath) {
    Write-Host "  ✓ Model weights found at: $weightsPath"
} else {
    Write-Host "  ✗ Warning: Model weights not found at: $weightsPath"
    Write-Host "    Make sure Dataset002_BRATS19.zip is extracted to nnunet_weights/"
}

# Check Python packages
Write-Host "`n  Checking Python packages..."
$packages = @("torch", "nnunetv2", "nibabel", "SimpleITK", "flask", "flask-cors")
foreach ($pkg in $packages) {
    $result = pip show $pkg 2>$null
    if ($result) {
        Write-Host "    ✓ $pkg installed"
    } else {
        Write-Host "    ✗ $pkg NOT installed"
    }
}

Write-Host "`n" + ("=" * 60)
Write-Host "Setup Complete!"
Write-Host ("=" * 60)

Write-Host "`nNext steps:"
Write-Host "  1. Start the backend:  python app_nnunet.py"
Write-Host "  2. Start the frontend: cd client && npm start"
Write-Host "  3. Open browser:       http://localhost:3000"

Write-Host "`nNote: Environment variables are set for this session only."
Write-Host "To make them permanent, add them to your system environment variables."
Write-Host "`n"
