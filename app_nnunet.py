from flask import Flask, json, request, jsonify
from flask_cors import CORS
import numpy as np
import os
import tempfile
import shutil
from pathlib import Path
import traceback
import cv2

# nnU-Net imports
try:
    import torch
    from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor
    import nibabel as nib
    NNUNET_AVAILABLE = True
except ImportError as e:
    print(f"Warning: nnU-Net not available: {e}")
    print("Falling back to VGG16 model")
    NNUNET_AVAILABLE = False

# Utility imports
from utils.image_converter import prepare_nnunet_input, convert_base64_to_image
from utils.segmentation_visualizer import extract_middle_slice, create_overlay, image_to_base64, normalize_for_display
from utils.tumor_analyzer import get_tumor_statistics, format_for_display

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# Configuration
UPLOAD_FOLDER = 'temp_uploads'
PREDICTION_FOLDER = 'temp_predictions'
NNUNET_WEIGHTS_PATH = 'nnunet_weights/Dataset002_BRATS19/nnUNetTrainer__nnUNetPlans__3d_fullres'

# Create necessary directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PREDICTION_FOLDER, exist_ok=True)

# Global predictor variable
predictor = None


def initialize_nnunet():
    """Initialize nnU-Net predictor."""
    global predictor
    
    if not NNUNET_AVAILABLE:
        print("nnU-Net not available, skipping initialization")
        return False
    
    try:
        print("Initializing nnU-Net predictor...")
        
        # Check if weights exist
        if not os.path.exists(NNUNET_WEIGHTS_PATH):
            print(f"Error: nnU-Net weights not found at {NNUNET_WEIGHTS_PATH}")
            return False
        
        # Initialize predictor with CPU-optimized settings
        # For faster inference on CPU: reduce tile overlap, disable augmentations
        predictor = nnUNetPredictor(
            tile_step_size=0.8,  # Increased from 0.5 for faster inference (less overlap)
            use_gaussian=False,   # Disabled for speed
            use_mirroring=False,  # Disabled for speed (test-time augmentation)
            device=torch.device('cuda' if torch.cuda.is_available() else 'cpu'),
            verbose=False,
            verbose_preprocessing=False,
            allow_tqdm=True
        )
        
        # Load model
        predictor.initialize_from_trained_model_folder(
            NNUNET_WEIGHTS_PATH,
            use_folds=(0,),  # Use fold_0 weights
            checkpoint_name='checkpoint_final.pth'
        )
        
        device_name = "GPU" if torch.cuda.is_available() else "CPU"
        print(f"✓ nnU-Net initialized successfully on {device_name}")
        if not torch.cuda.is_available():
            print("⚠ Running on CPU - inference will be slower (~2-5 minutes per case)")
            print("  For faster inference, use a GPU-enabled system")
        return True
        
    except Exception as e:
        print(f"Error initializing nnU-Net: {e}")
        traceback.print_exc()
        return False


@app.route('/home', methods=['GET'])
def home():
    """Health check endpoint."""
    status = {
        "status": "running",
        "model": "nnU-Net" if predictor is not None else "VGG16 (fallback)",
        "device": "GPU" if torch.cuda.is_available() else "CPU" if NNUNET_AVAILABLE else "N/A"
    }
    return jsonify(status)


@app.route("/predict", methods=['POST'])
def predict():
    """
    Main prediction endpoint for brain tumor segmentation.
    
    Accepts:
    - 1-4 images (base64 encoded or file upload)
    - Supports JPG, PNG, NII formats
    
    Returns:
    - Segmentation overlay (base64)
    - Tumor statistics
    - Classification results
    """
    print("=" * 60)
    print("Prediction request received")
    
    try:
        # Parse request data
        data = request.get_json() if request.is_json else request.form
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Extract images from request
        image_data_list = data.get('image', data.get('images', []))
        
        if not image_data_list:
            return jsonify({"error": "No images provided"}), 400
        
        # Ensure it's a list
        if not isinstance(image_data_list, list):
            image_data_list = [image_data_list]
        
        print(f"Received {len(image_data_list)} image(s)")
        
        # Create temporary directory for this request
        temp_dir = tempfile.mkdtemp(dir=UPLOAD_FOLDER)
        input_dir = os.path.join(temp_dir, 'input')
        output_dir = os.path.join(temp_dir, 'output')
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            # Save uploaded images
            image_paths = []
            for idx, img_data in enumerate(image_data_list):
                temp_path = os.path.join(temp_dir, f'upload_{idx}')
                # convert_base64_to_image will add the correct extension
                actual_path = convert_base64_to_image(img_data, temp_path)
                image_paths.append(actual_path)
                print(f"  Saved image {idx + 1}: {os.path.basename(actual_path)}")

            
            # Prepare nnU-Net input (converts to NIfTI, creates 4 channels)
            print("Preparing nnU-Net input...")
            prepare_nnunet_input(image_paths, input_dir, case_id="case_0000")
            
            # Run nnU-Net inference with CPU-optimized settings
            print("Running nnU-Net inference...")
            predictor.predict_from_files(
                list_of_lists_or_source_folder=input_dir,
                output_folder_or_list_of_truncated_output_files=output_dir,
                save_probabilities=False,
                overwrite=True,
                num_processes_preprocessing=1,  # Single process for CPU
                num_processes_segmentation_export=1,  # Single process for CPU
                folder_with_segs_from_prev_stage=None,
                num_parts=1,
                part_id=0
            )
            
            print("✓ Inference complete")
            
            # Load segmentation result
            seg_file = os.path.join(output_dir, 'case_0000.nii.gz')
            if not os.path.exists(seg_file):
                # Try without .gz
                seg_file = os.path.join(output_dir, 'case_0000.nii')
            
            if not os.path.exists(seg_file):
                return jsonify({"error": "Segmentation output not found"}), 500
            
            seg_nii = nib.load(seg_file)
            segmentation_3d = seg_nii.get_fdata().astype(np.uint8)
            
            print(f"Segmentation shape: {segmentation_3d.shape}")
            
            # Extract middle slice for visualization
            seg_slice = extract_middle_slice(segmentation_3d, axis=2)
            
            # Load original image for overlay
            original_nii = nib.load(os.path.join(input_dir, 'case_0000_0000.nii.gz'))
            original_3d = original_nii.get_fdata()
            original_slice = extract_middle_slice(original_3d, axis=2)
            
            # Create overlay visualization
            print("Creating visualization...")
            overlay_image = create_overlay(original_slice, seg_slice, alpha=0.5)
            overlay_base64 = image_to_base64(overlay_image, format='PNG')
            
            # Create original image visualization (RGB)
            # Normalize and convert to RGB directly to ensure it's not black
            print(f"Original slice range: min={np.min(original_slice)}, max={np.max(original_slice)}")
            original_normalized = normalize_for_display(original_slice)
            # cv2.cvtColor requires the image to be uint8 or float32. normalize_for_display returns uint8.
            original_rgb_image = cv2.cvtColor(original_normalized, cv2.COLOR_GRAY2RGB)
            print(f"Original RGB range: min={np.min(original_rgb_image)}, max={np.max(original_rgb_image)}")
            
            original_base64 = image_to_base64(original_rgb_image, format='PNG')
            
            # Calculate tumor statistics
            print("Calculating tumor statistics...")
            statistics = get_tumor_statistics(segmentation_3d, voxel_spacing=(1.0, 1.0, 1.0))
            display_stats = format_for_display(statistics)
            
            # Prepare response
            response = {
                "success": True,
                "original_image": original_base64,
                "overlay_image": overlay_base64,
                "statistics": display_stats,
                "tumor_detected": display_stats["tumor_detected"],
                "message": statistics["summary"]
            }
            
            print("✓ Prediction successful")
            print(f"  Tumor detected: {display_stats['tumor_detected']}")
            print(f"  Total volume: {display_stats['total_volume']} cm³")
            print("=" * 60)
            
            return jsonify(response)
        
        finally:
            # Cleanup temporary files
            try:
                shutil.rmtree(temp_dir)
                print("✓ Cleaned up temporary files")
            except Exception as e:
                print(f"Warning: Could not clean up temp dir: {e}")
    
    except Exception as e:
        print(f"✗ Error during prediction: {e}")
        traceback.print_exc()
        print("=" * 60)
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Prediction failed. Please try again."
        }), 500


@app.route("/", methods=['POST'])
def legacy_predict():
    """
    Legacy endpoint for backward compatibility.
    Redirects to new /predict endpoint.
    """
    return predict()


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("Brain Tumor Detection - nnU-Net Edition")
    print("=" * 60)
    
    # Initialize nnU-Net
    if initialize_nnunet():
        print("\n✓ Server ready with nnU-Net model")
    else:
        print("\n✗ nnU-Net initialization failed")
        print("Please install dependencies: pip install -r requirements.txt")
    
    print("=" * 60 + "\n")
    
    # Start Flask server
    app.run(port=5000, debug=False)
