"""
Image Converter Utility for nnU-Net Integration

Converts various image formats (JPG, PNG, NIfTI) to nnU-Net-compatible format.
Supports hybrid multi-modality approach: accepts 1-4 images and duplicates if needed.
"""

import os
import numpy as np
import nibabel as nib
import SimpleITK as sitk
from PIL import Image
import cv2
from typing import List, Tuple, Optional


def convert_2d_to_3d_nifti(image_2d: np.ndarray, num_slices: int = 16) -> np.ndarray:
    """
    Convert 2D image to pseudo-3D volume by stacking slices.
    
    Args:
        image_2d: 2D numpy array (H, W) or (H, W, C)
        num_slices: Number of slices to create in z-dimension
        
    Returns:
        3D numpy array (H, W, num_slices) or (H, W, num_slices, C)
    """
    if len(image_2d.shape) == 2:
        # Grayscale: (H, W) -> (H, W, num_slices)
        volume_3d = np.stack([image_2d] * num_slices, axis=2)
    elif len(image_2d.shape) == 3:
        # RGB: (H, W, C) -> (H, W, num_slices, C)
        volume_3d = np.stack([image_2d] * num_slices, axis=2)
    else:
        raise ValueError(f"Unexpected image shape: {image_2d.shape}")
    
    return volume_3d


def load_image_as_array(image_path: str) -> np.ndarray:
    """
    Load image from various formats and return as numpy array.
    
    Args:
        image_path: Path to image file (.jpg, .png, .nii, .nii.gz)
        
    Returns:
        Numpy array of the image
    """
    ext = os.path.splitext(image_path.lower())[1]
    
    if ext in ['.nii', '.gz']:
        # Load NIfTI file
        nii_img = nib.load(image_path)
        img_array = nii_img.get_fdata()
        return img_array
    
    elif ext in ['.jpg', '.jpeg', '.png', '.bmp']:
        # Load standard image formats
        img = Image.open(image_path).convert('L')  # Convert to grayscale
        img_array = np.array(img, dtype=np.float32)
        return img_array
    
    else:
        raise ValueError(f"Unsupported image format: {ext}")


def create_multimodal_input(images: List[np.ndarray], target_channels: int = 4) -> np.ndarray:
    """
    Create multi-channel input for nnU-Net from 1-4 images.
    Duplicates images if fewer than target_channels provided.
    
    Args:
        images: List of 3D numpy arrays (each is H x W x D)
        target_channels: Number of channels required (default: 4 for BraTS)
        
    Returns:
        4D numpy array (C x H x W x D) where C = target_channels
    """
    num_images = len(images)
    
    if num_images == 0:
        raise ValueError("At least one image must be provided")
    
    # Ensure all images have the same shape
    reference_shape = images[0].shape
    for i, img in enumerate(images):
        if img.shape != reference_shape:
            raise ValueError(f"Image {i} has shape {img.shape}, expected {reference_shape}")
    
    # Create channel list
    channels = []
    
    if num_images >= target_channels:
        # Use first target_channels images
        channels = images[:target_channels]
    else:
        # Duplicate images to reach target_channels
        channels = images.copy()
        
        # Fill remaining channels by cycling through provided images
        while len(channels) < target_channels:
            idx = len(channels) % num_images
            channels.append(images[idx])
    
    # Stack along channel dimension: (C, H, W, D)
    multimodal_volume = np.stack(channels, axis=0)
    
    return multimodal_volume


def normalize_image(image: np.ndarray, method: str = 'zscore') -> np.ndarray:
    """
    Normalize image intensities.
    
    Args:
        image: Input image array
        method: Normalization method ('zscore', 'minmax', 'percentile')
        
    Returns:
        Normalized image array
    """
    if method == 'zscore':
        # Z-score normalization (mean=0, std=1)
        mean = np.mean(image)
        std = np.std(image)
        if std > 0:
            normalized = (image - mean) / std
        else:
            normalized = image - mean
            
    elif method == 'minmax':
        # Min-max normalization to [0, 1]
        min_val = np.min(image)
        max_val = np.max(image)
        if max_val > min_val:
            normalized = (image - min_val) / (max_val - min_val)
        else:
            normalized = np.zeros_like(image)
            
    elif method == 'percentile':
        # Percentile-based normalization (clip outliers)
        p1, p99 = np.percentile(image, [1, 99])
        normalized = np.clip(image, p1, p99)
        normalized = (normalized - p1) / (p99 - p1) if p99 > p1 else normalized
        
    else:
        raise ValueError(f"Unknown normalization method: {method}")
    
    return normalized.astype(np.float32)


def prepare_nnunet_input(
    image_paths: List[str],
    output_dir: str,
    case_id: str = "case_0000"
) -> str:
    """
    Prepare input folder structure for nnU-Net inference.
    
    nnU-Net expects:
    - Input folder with files named: {case_id}_0000.nii.gz, {case_id}_0001.nii.gz, etc.
    - Each file is one modality/channel
    
    Args:
        image_paths: List of 1-4 image file paths
        output_dir: Directory to save prepared files
        case_id: Case identifier (default: "case_0000")
        
    Returns:
        Path to the prepared input directory
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Load all images
    images = []
    for img_path in image_paths:
        img_array = load_image_as_array(img_path)
        
        # Convert 2D to 3D if needed
        if len(img_array.shape) == 2:
            img_array = convert_2d_to_3d_nifti(img_array, num_slices=16)
        
        # Normalize
        img_array = normalize_image(img_array, method='zscore')
        
        images.append(img_array)
    
    # Create 4-channel input
    multimodal_volume = create_multimodal_input(images, target_channels=4)
    
    # Save each channel as separate NIfTI file
    for channel_idx in range(4):
        channel_data = multimodal_volume[channel_idx]  # Shape: (H, W, D)
        
        # Create NIfTI image
        nii_img = nib.Nifti1Image(channel_data, affine=np.eye(4))
        
        # Save with nnU-Net naming convention
        output_filename = f"{case_id}_{channel_idx:04d}.nii.gz"
        output_path = os.path.join(output_dir, output_filename)
        nib.save(nii_img, output_path)
        
        print(f"Saved channel {channel_idx} to {output_path}")
    
    return output_dir


def convert_base64_to_image(base64_string: str, output_path: str) -> str:
    """
    Convert base64 encoded image to file.
    
    Args:
        base64_string: Base64 encoded image string (with or without data URL prefix)
        output_path: Path to save the decoded image
        
    Returns:
        Path to saved image file
    """
    import base64
    import re
    
    # Extract MIME type and base64 data
    mime_type = None
    if base64_string.startswith('data:'):
        # Format: data:image/png;base64,iVBORw0KG...
        match = re.match(r'data:([^;]+);base64,(.+)', base64_string)
        if match:
            mime_type = match.group(1)
            base64_data = match.group(2)
        else:
            # Fallback: just split on comma
            base64_data = base64_string.split(',', 1)[1] if ',' in base64_string else base64_string
    else:
        base64_data = base64_string
    
    # Decode base64
    try:
        img_data = base64.b64decode(base64_data)
    except Exception as e:
        raise ValueError(f"Failed to decode base64 data: {e}")
    
    # Determine file extension from MIME type or output path
    if mime_type:
        ext_map = {
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/png': '.png',
            'image/bmp': '.bmp',
            'application/octet-stream': '.nii',  # For .nii files
        }
        ext = ext_map.get(mime_type, '.jpg')
        
        # Update output path with correct extension
        base_path = os.path.splitext(output_path)[0]
        output_path = base_path + ext
    
    # Save to file
    with open(output_path, 'wb') as f:
        f.write(img_data)
    
    return output_path



if __name__ == "__main__":
    # Test the converter
    print("Image Converter Utility - Test Mode")
    
    # Example usage:
    # image_paths = ["scan1.jpg", "scan2.jpg"]
    # output_dir = prepare_nnunet_input(image_paths, "temp_input", "patient_001")
    # print(f"Prepared input in: {output_dir}")
