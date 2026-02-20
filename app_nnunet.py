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

# Classifier imports
try:
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
    import tensorflow as tf
    from tensorflow.keras.models import load_model
    CLASSIFIER_AVAILABLE = True
    
    class CustomDepthwiseConv2D(tf.keras.layers.DepthwiseConv2D):
        def __init__(self, **kwargs):
            kwargs.pop('groups', None)
            super().__init__(**kwargs)
except ImportError as e:
    print(f"Warning: TensorFlow not available for classification: {e}")
    CLASSIFIER_AVAILABLE = False

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
classifier_model = None


def initialize_classifier():
    """Initialize MobileNetV2 tumor classifier."""
    global classifier_model
    if not CLASSIFIER_AVAILABLE:
        print("TensorFlow not available, skipping classifier initialization")
        return False
    
    try:
        model_path = 'cnn_model.h5'
        if os.path.exists(model_path):
            print("Initializing classifier model...")
            classifier_model = load_model(
                model_path, 
                custom_objects={'DepthwiseConv2D': CustomDepthwiseConv2D},
                compile=False
            )
            print("✓ Classifier initialized successfully")
            return True
        else:
            print(f"Classifier model not found at {model_path}")
            return False
    except Exception as e:
        print(f"Error initializing classifier: {e}")
        import traceback
        traceback.print_exc()
        return False


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
            print(f"Weights not found locally. Attempting to download from S3...")
            
            WEIGHTS_URL = "https://brain-tumor-weights-2024.s3.us-east-1.amazonaws.com/weights.zip"
            WEIGHTS_ZIP_PATH = "weights.zip"
            
            try:
                import requests
                import zipfile
                
                # Download
                print(f"Downloading from {WEIGHTS_URL}...")
                with requests.get(WEIGHTS_URL, stream=True) as r:
                    r.raise_for_status()
                    with open(WEIGHTS_ZIP_PATH, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                
                # Unzip
                print("Unzipping weights...")
                with zipfile.ZipFile(WEIGHTS_ZIP_PATH, 'r') as zip_ref:
                    # Extract to nnunet_weights folder
                    zip_ref.extractall("nnunet_weights")
                    
                # Cleanup
                if os.path.exists(WEIGHTS_ZIP_PATH):
                    os.remove(WEIGHTS_ZIP_PATH)
                    
                print("✓ Weights downloaded and extracted successfully")
                
                # Verify path exists after extraction
                if not os.path.exists(NNUNET_WEIGHTS_PATH):
                    print(f"Error: Extraction failed to create expected path: {NNUNET_WEIGHTS_PATH}")
                    return False
                    
            except Exception as e:
                print(f"Error downloading weights: {e}")
                print(f"Please manually download weights to: {NNUNET_WEIGHTS_PATH}")
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
            
            # --- START CLASSIFICATION ---
            tumor_type = "No Tumor Detected"
            confidence = 0.0
            
            if display_stats["tumor_detected"]:
                if CLASSIFIER_AVAILABLE and classifier_model is not None:
                    try:
                        print("Running tumor classification on largest slice...")
                        # 1. Identify slice with maximum tumor area
                        tumor_mask = (segmentation_3d > 0).astype(int)
                        slice_areas = np.sum(tumor_mask, axis=(0, 1))
                        max_tumor_slice_idx = np.argmax(slice_areas)
                        
                        # 2. Extract that slice from T1ce (0001) or original (0000)
                        t1ce_path = os.path.join(input_dir, 'case_0000_0001.nii.gz')
                        if not os.path.exists(t1ce_path):
                            t1ce_path = os.path.join(input_dir, 'case_0000_0000.nii.gz')
                        
                        t1ce_nii = nib.load(t1ce_path)
                        t1ce_3d = t1ce_nii.get_fdata()
                        max_slice = t1ce_3d[:, :, max_tumor_slice_idx]
                        
                        # 3. Preprocess slice to 160x160x3
                        max_slice_norm = normalize_for_display(max_slice)
                        max_slice_rgb = cv2.cvtColor(max_slice_norm, cv2.COLOR_GRAY2RGB)
                        max_slice_resized = cv2.resize(max_slice_rgb, (160, 160))
                        
                        classifier_input = np.expand_dims(max_slice_resized, axis=0).astype('float32') / 255.0
                        
                        # 4. Predict
                        preds = classifier_model.predict(classifier_input, verbose=0)[0]
                        pred_class_idx = np.argmax(preds)
                        
                        TUMOR_TYPES = ['Glioma', 'Meningioma', 'No Tumor', 'Pituitary']
                        tumor_type = TUMOR_TYPES[pred_class_idx]
                        confidence = float(preds[pred_class_idx])
                        
                    except Exception as e:
                        print(f"Warning: Classification failed: {e}")
                        traceback.print_exc()
                        tumor_type = "Classification Error"
                        confidence = 0.0
                else:
                    tumor_type = "Classification Unavailable"
            else:
                print("No tumor detected in segmentation; skipping classification.")
            # --- END CLASSIFICATION ---
            
            # Prepare response
            response = {
                "success": True,
                "original_image": original_base64,
                "overlay_image": overlay_base64,
                "statistics": display_stats,
                "tumor_detected": display_stats["tumor_detected"],
                "tumor_type": tumor_type,
                "confidence": confidence,
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
        
    # Initialize Classifier
    initialize_classifier()
    
    print("=" * 60 + "\n")
    
    # Start Flask server
    app.run(host='0.0.0.0', port=5000, debug=False)
