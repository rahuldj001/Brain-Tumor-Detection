"""
Tumor Analyzer for Brain Tumor Segmentation

Calculates tumor statistics, volumes, and classifications from segmentation masks.
Provides quantitative metrics for clinical assessment.
"""

import numpy as np
from typing import Dict, Tuple, List, Optional


# BraTS label definitions
LABEL_NAMES = {
    0: "Background",
    1: "Edema",
    2: "Non-Enhancing Tumor",
    3: "Empty",
    4: "Enhancing Tumor"
}

# Composite regions (as defined in BraTS challenge)
COMPOSITE_REGIONS = {
    "Whole Tumor (WT)": [1, 2, 4],      # All tumor regions
    "Tumor Core (TC)": [2, 4],           # Non-enhancing + Enhancing
    "Enhancing Tumor (ET)": [4]          # Enhancing only
}


def calculate_voxel_volume(spacing: Tuple[float, float, float] = (1.0, 1.0, 1.0)) -> float:
    """
    Calculate volume of a single voxel in mm³.
    
    Args:
        spacing: Voxel spacing in mm (x, y, z)
        
    Returns:
        Volume in mm³
    """
    return spacing[0] * spacing[1] * spacing[2]


def count_voxels_per_label(segmentation: np.ndarray) -> Dict[int, int]:
    """
    Count number of voxels for each label.
    
    Args:
        segmentation: Segmentation array with label values
        
    Returns:
        Dictionary mapping label ID to voxel count
    """
    unique_labels, counts = np.unique(segmentation, return_counts=True)
    voxel_counts = dict(zip(unique_labels.astype(int), counts.astype(int)))
    
    return voxel_counts


def calculate_volumes(
    segmentation: np.ndarray,
    voxel_spacing: Tuple[float, float, float] = (1.0, 1.0, 1.0)
) -> Dict[str, float]:
    """
    Calculate volumes for each tumor region in cm³.
    
    Args:
        segmentation: 3D segmentation array
        voxel_spacing: Voxel spacing in mm (x, y, z)
        
    Returns:
        Dictionary with volumes in cm³ for each region
    """
    voxel_vol_mm3 = calculate_voxel_volume(voxel_spacing)
    voxel_vol_cm3 = voxel_vol_mm3 / 1000.0  # Convert mm³ to cm³
    
    voxel_counts = count_voxels_per_label(segmentation)
    
    volumes = {}
    
    # Individual label volumes
    for label_id, label_name in LABEL_NAMES.items():
        if label_id == 0 or label_id == 3:  # Skip background and empty
            continue
        
        voxel_count = voxel_counts.get(label_id, 0)
        volume_cm3 = voxel_count * voxel_vol_cm3
        volumes[label_name] = round(volume_cm3, 2)
    
    # Composite region volumes
    for region_name, label_ids in COMPOSITE_REGIONS.items():
        total_voxels = sum(voxel_counts.get(label_id, 0) for label_id in label_ids)
        volume_cm3 = total_voxels * voxel_vol_cm3
        volumes[region_name] = round(volume_cm3, 2)
    
    return volumes


def classify_tumor_type(segmentation: np.ndarray) -> Dict[str, any]:
    """
    Classify tumor based on segmentation composition.
    
    Args:
        segmentation: Segmentation array
        
    Returns:
        Dictionary with tumor classification info
    """
    voxel_counts = count_voxels_per_label(segmentation)
    
    # Get counts for each tumor type
    edema_count = voxel_counts.get(1, 0)
    nonenhancing_count = voxel_counts.get(2, 0)
    enhancing_count = voxel_counts.get(4, 0)
    total_tumor = edema_count + nonenhancing_count + enhancing_count
    
    # Determine dominant type
    if total_tumor == 0:
        dominant_type = "No Tumor Detected"
        severity = "None"
    else:
        # Find which type has most voxels
        type_counts = {
            "Edema": edema_count,
            "Non-Enhancing Tumor": nonenhancing_count,
            "Enhancing Tumor": enhancing_count
        }
        dominant_type = max(type_counts, key=type_counts.get)
        
        # Assess severity based on total volume
        if total_tumor < 1000:
            severity = "Small"
        elif total_tumor < 10000:
            severity = "Moderate"
        else:
            severity = "Large"
    
    # Calculate percentages
    if total_tumor > 0:
        edema_pct = round((edema_count / total_tumor) * 100, 1)
        nonenhancing_pct = round((nonenhancing_count / total_tumor) * 100, 1)
        enhancing_pct = round((enhancing_count / total_tumor) * 100, 1)
    else:
        edema_pct = nonenhancing_pct = enhancing_pct = 0.0
    
    classification = {
        "dominant_type": dominant_type,
        "severity": severity,
        "has_enhancing": enhancing_count > 0,
        "has_necrotic": nonenhancing_count > 0,
        "has_edema": edema_count > 0,
        "composition": {
            "edema_percent": edema_pct,
            "nonenhancing_percent": nonenhancing_pct,
            "enhancing_percent": enhancing_pct
        }
    }
    
    return classification


def get_tumor_statistics(
    segmentation: np.ndarray,
    voxel_spacing: Tuple[float, float, float] = (1.0, 1.0, 1.0)
) -> Dict[str, any]:
    """
    Get comprehensive tumor statistics.
    
    Args:
        segmentation: 3D segmentation array
        voxel_spacing: Voxel spacing in mm (x, y, z)
        
    Returns:
        Dictionary with complete tumor analysis
    """
    # Calculate volumes
    volumes = calculate_volumes(segmentation, voxel_spacing)
    
    # Classify tumor
    classification = classify_tumor_type(segmentation)
    
    # Get voxel counts
    voxel_counts = count_voxels_per_label(segmentation)
    
    # Combine all statistics
    statistics = {
        "volumes_cm3": volumes,
        "classification": classification,
        "voxel_counts": {
            "edema": voxel_counts.get(1, 0),
            "nonenhancing": voxel_counts.get(2, 0),
            "enhancing": voxel_counts.get(4, 0),
            "total_tumor": sum(voxel_counts.get(i, 0) for i in [1, 2, 4])
        },
        "summary": generate_summary(volumes, classification)
    }
    
    return statistics


def generate_summary(volumes: Dict[str, float], classification: Dict[str, any]) -> str:
    """
    Generate human-readable summary of tumor analysis.
    
    Args:
        volumes: Volume measurements
        classification: Tumor classification
        
    Returns:
        Summary string
    """
    dominant = classification["dominant_type"]
    severity = classification["severity"]
    total_vol = volumes.get("Whole Tumor (WT)", 0)
    
    if total_vol == 0:
        return "No tumor detected in the scan."
    
    summary = f"{severity} tumor detected with total volume of {total_vol} cm³. "
    summary += f"Dominant region: {dominant}. "
    
    if classification["has_enhancing"]:
        enhancing_vol = volumes.get("Enhancing Tumor", 0)
        summary += f"Active enhancing tumor present ({enhancing_vol} cm³). "
    
    if classification["has_necrotic"]:
        necrotic_vol = volumes.get("Non-Enhancing Tumor", 0)
        summary += f"Necrotic core detected ({necrotic_vol} cm³). "
    
    if classification["has_edema"]:
        edema_vol = volumes.get("Edema", 0)
        summary += f"Surrounding edema present ({edema_vol} cm³)."
    
    return summary


def format_for_display(statistics: Dict[str, any]) -> Dict[str, any]:
    """
    Format statistics for frontend display.
    
    Args:
        statistics: Raw statistics dictionary
        
    Returns:
        Formatted dictionary optimized for UI display (JSON-serializable)
    """
    volumes = statistics["volumes_cm3"]
    classification = statistics["classification"]
    
    # Convert numpy types to Python native types for JSON serialization
    display_data = {
        "tumor_detected": bool(volumes.get("Whole Tumor (WT)", 0) > 0),
        "total_volume": float(volumes.get("Whole Tumor (WT)", 0)),
        "dominant_type": str(classification["dominant_type"]),
        "severity": str(classification["severity"]),
        "regions": [
            {
                "name": "Enhancing Tumor",
                "volume": float(volumes.get("Enhancing Tumor", 0)),
                "color": "#FF0000",
                "description": "Active tumor growth"
            },
            {
                "name": "Non-Enhancing Tumor",
                "volume": float(volumes.get("Non-Enhancing Tumor", 0)),
                "color": "#FFFF00",
                "description": "Necrotic tumor core"
            },
            {
                "name": "Edema",
                "volume": float(volumes.get("Edema", 0)),
                "color": "#00FF00",
                "description": "Swelling around tumor"
            }
        ],
        "summary": str(statistics["summary"]),
        "classification": {
            "composition": {
                "edema_percent": float(classification["composition"]["edema_percent"]),
                "nonenhancing_percent": float(classification["composition"]["nonenhancing_percent"]),
                "enhancing_percent": float(classification["composition"]["enhancing_percent"])
            },
            "has_edema": bool(classification["has_edema"]),
            "has_necrotic": bool(classification["has_necrotic"]),
            "has_enhancing": bool(classification["has_enhancing"])
        }
    }
    
    return display_data


if __name__ == "__main__":
    # Test the analyzer
    print("Tumor Analyzer - Test Mode")
    
    # Create dummy segmentation
    test_seg = np.zeros((100, 100, 100), dtype=np.uint8)
    test_seg[30:60, 30:60, 30:60] = 1  # Edema
    test_seg[40:50, 40:50, 40:50] = 2  # Non-enhancing
    test_seg[42:48, 42:48, 42:48] = 4  # Enhancing
    
    # Calculate statistics
    stats = get_tumor_statistics(test_seg, voxel_spacing=(1.0, 1.0, 1.0))
    
    print("\nTumor Statistics:")
    print(f"Total Volume: {stats['volumes_cm3']['Whole Tumor (WT)']} cm³")
    print(f"Dominant Type: {stats['classification']['dominant_type']}")
    print(f"Severity: {stats['classification']['severity']}")
    print(f"\nSummary: {stats['summary']}")
