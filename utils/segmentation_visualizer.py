"""
Segmentation Visualizer for Brain Tumor Detection

Creates color-coded overlays of tumor segmentation on original MRI scans.
Supports BraTS label scheme with distinct colors for each tumor region.
"""

import numpy as np
import cv2
from PIL import Image
from typing import Tuple, Dict, Optional
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


# BraTS Label Definitions
BRATS_LABELS = {
    0: "Background",
    1: "Edema",
    2: "Non-Enhancing Tumor",
    3: "Empty",  # Not used in BraTS
    4: "Enhancing Tumor"
}

# Color scheme for visualization (RGB + Alpha)
TUMOR_COLORS = {
    0: (0, 0, 0, 0),          # Background - transparent
    1: (0, 255, 0, 180),      # Edema - green with transparency
    2: (255, 255, 0, 180),    # Non-enhancing - yellow with transparency
    3: (128, 128, 128, 0),    # Empty - gray (not used)
    4: (255, 0, 0, 200)       # Enhancing - red with higher opacity
}

# Color scheme for matplotlib (normalized RGB)
TUMOR_COLORS_MPL = {
    0: (0, 0, 0, 0),
    1: (0, 1, 0, 0.7),
    2: (1, 1, 0, 0.7),
    3: (0.5, 0.5, 0.5, 0),
    4: (1, 0, 0, 0.8)
}


def extract_middle_slice(volume_3d: np.ndarray, axis: int = 2) -> np.ndarray:
    """
    Extract middle slice from 3D volume.
    
    Args:
        volume_3d: 3D numpy array (H, W, D)
        axis: Axis along which to extract (0=sagittal, 1=coronal, 2=axial)
        
    Returns:
        2D numpy array representing the middle slice
    """
    middle_idx = volume_3d.shape[axis] // 2
    
    if axis == 0:
        slice_2d = volume_3d[middle_idx, :, :]
    elif axis == 1:
        slice_2d = volume_3d[:, middle_idx, :]
    else:  # axis == 2
        slice_2d = volume_3d[:, :, middle_idx]
    
    return slice_2d


def normalize_for_display(image: np.ndarray) -> np.ndarray:
    """
    Normalize image to 0-255 range for display.
    
    Args:
        image: Input image array
        
    Returns:
        Normalized image as uint8
    """
    # Handle NaN and inf values
    image = np.nan_to_num(image, nan=0.0, posinf=0.0, neginf=0.0)
    
    # Normalize to 0-255
    img_min = np.min(image)
    img_max = np.max(image)
    
    if img_max > img_min:
        normalized = ((image - img_min) / (img_max - img_min) * 255).astype(np.uint8)
    else:
        normalized = np.zeros_like(image, dtype=np.uint8)
    
    return normalized


def create_colored_mask(segmentation: np.ndarray) -> np.ndarray:
    """
    Create RGB colored mask from segmentation labels.
    
    Args:
        segmentation: 2D array with label values (0, 1, 2, 4)
        
    Returns:
        RGB image (H, W, 3) with colored tumor regions
    """
    h, w = segmentation.shape
    colored_mask = np.zeros((h, w, 3), dtype=np.uint8)
    
    for label, color in TUMOR_COLORS.items():
        if label == 0:  # Skip background
            continue
        
        mask = (segmentation == label)
        colored_mask[mask] = color[:3]  # RGB only
    
    return colored_mask


def create_overlay(
    original_image: np.ndarray,
    segmentation_mask: np.ndarray,
    alpha: float = 0.5,
    colormap: Optional[Dict[int, Tuple]] = None
) -> np.ndarray:
    """
    Create overlay of segmentation on original image.
    
    Args:
        original_image: 2D grayscale image or 3D RGB image
        segmentation_mask: 2D segmentation with label values
        alpha: Transparency of overlay (0=transparent, 1=opaque)
        colormap: Optional custom color mapping
        
    Returns:
        RGB image with segmentation overlay
    """
    # Normalize original image to 0-255
    if len(original_image.shape) == 2:
        # Grayscale to RGB
        original_rgb = normalize_for_display(original_image)
        original_rgb = cv2.cvtColor(original_rgb, cv2.COLOR_GRAY2RGB)
    else:
        original_rgb = normalize_for_display(original_image)
    
    # Create colored segmentation mask
    if colormap is None:
        colored_seg = create_colored_mask(segmentation_mask)
    else:
        # Use custom colormap
        h, w = segmentation_mask.shape
        colored_seg = np.zeros((h, w, 3), dtype=np.uint8)
        for label, color in colormap.items():
            if label == 0:
                continue
            mask = (segmentation_mask == label)
            colored_seg[mask] = color[:3]
    
    # Blend original and segmentation
    overlay = cv2.addWeighted(original_rgb, 1 - alpha, colored_seg, alpha, 0)
    
    return overlay


def create_side_by_side(
    original_image: np.ndarray,
    segmentation_mask: np.ndarray,
    overlay_alpha: float = 0.5
) -> np.ndarray:
    """
    Create side-by-side comparison: original | overlay.
    
    Args:
        original_image: Original MRI scan (2D)
        segmentation_mask: Segmentation labels (2D)
        overlay_alpha: Transparency for overlay
        
    Returns:
        Combined image showing original and overlay side-by-side
    """
    # Normalize original
    original_rgb = normalize_for_display(original_image)
    original_rgb = cv2.cvtColor(original_rgb, cv2.COLOR_GRAY2RGB)
    
    # Create overlay
    overlay = create_overlay(original_image, segmentation_mask, alpha=overlay_alpha)
    
    # Concatenate horizontally
    combined = np.hstack([original_rgb, overlay])
    
    return combined


def create_legend_image(width: int = 300, height: int = 200) -> np.ndarray:
    """
    Create color legend image for tumor types.
    
    Args:
        width: Width of legend image
        height: Height of legend image
        
    Returns:
        RGB image with color legend
    """
    legend_img = np.ones((height, width, 3), dtype=np.uint8) * 255
    
    labels_to_show = [
        (4, "Enhancing Tumor (Active)", TUMOR_COLORS[4][:3]),
        (2, "Non-Enhancing Core (Necrotic)", TUMOR_COLORS[2][:3]),
        (1, "Edema (Swelling)", TUMOR_COLORS[1][:3])
    ]
    
    y_offset = 30
    for label_id, label_name, color in labels_to_show:
        # Draw color box
        cv2.rectangle(legend_img, (20, y_offset), (60, y_offset + 30), color, -1)
        cv2.rectangle(legend_img, (20, y_offset), (60, y_offset + 30), (0, 0, 0), 2)
        
        # Draw text
        cv2.putText(
            legend_img,
            label_name,
            (70, y_offset + 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 0),
            1,
            cv2.LINE_AA
        )
        
        y_offset += 50
    
    return legend_img


def save_visualization(
    original_image: np.ndarray,
    segmentation_mask: np.ndarray,
    output_path: str,
    include_legend: bool = True
) -> str:
    """
    Save complete visualization with original, overlay, and legend.
    
    Args:
        original_image: Original MRI scan
        segmentation_mask: Segmentation labels
        output_path: Path to save visualization
        include_legend: Whether to include color legend
        
    Returns:
        Path to saved visualization
    """
    # Create side-by-side
    side_by_side = create_side_by_side(original_image, segmentation_mask)
    
    if include_legend:
        # Create legend
        legend = create_legend_image(width=side_by_side.shape[1] // 3, height=side_by_side.shape[0])
        
        # Resize legend to match height
        legend_resized = cv2.resize(legend, (side_by_side.shape[1] // 3, side_by_side.shape[0]))
        
        # Concatenate with legend
        final_viz = np.hstack([side_by_side, legend_resized])
    else:
        final_viz = side_by_side
    
    # Save
    cv2.imwrite(output_path, cv2.cvtColor(final_viz, cv2.COLOR_RGB2BGR))
    
    return output_path


def image_to_base64(image: np.ndarray, format: str = 'PNG') -> str:
    """
    Convert numpy image to base64 string for web transfer.
    
    Args:
        image: RGB image array
        format: Image format (PNG, JPEG)
        
    Returns:
        Base64 encoded string
    """
    import base64
    from io import BytesIO
    
    # Convert to PIL Image
    pil_img = Image.fromarray(image)
    
    # Save to bytes buffer
    buffer = BytesIO()
    pil_img.save(buffer, format=format)
    buffer.seek(0)
    
    # Encode to base64
    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    
    # Add data URL prefix
    mime_type = f"image/{format.lower()}"
    data_url = f"data:{mime_type};base64,{img_base64}"
    
    return data_url


if __name__ == "__main__":
    # Test the visualizer
    print("Segmentation Visualizer - Test Mode")
    
    # Create dummy data for testing
    test_image = np.random.rand(256, 256) * 1000
    test_seg = np.zeros((256, 256), dtype=np.uint8)
    test_seg[50:100, 50:100] = 1  # Edema
    test_seg[60:90, 60:90] = 2     # Non-enhancing
    test_seg[70:80, 70:80] = 4     # Enhancing
    
    # Create overlay
    overlay = create_overlay(test_image, test_seg, alpha=0.5)
    print(f"Created overlay with shape: {overlay.shape}")
    
    # Create side-by-side
    side_by_side = create_side_by_side(test_image, test_seg)
    print(f"Created side-by-side with shape: {side_by_side.shape}")
