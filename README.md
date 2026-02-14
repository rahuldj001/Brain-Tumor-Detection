# Brain Tumor Detection with nnU-Net - Setup Guide

This guide will help you set up and run the Brain Tumor Detection application on your local machine.

## Prerequisites

Before you begin, ensure you have the following installed:
- **Python 3.8+**: [Download Python](https://www.python.org/downloads/)
- **Node.js & npm**: [Download Node.js](https://nodejs.org/)
- **Git**: [Download Git](https://git-scm.com/downloads)
- **CUDA (Optional)**: For GPU acceleration (highly recommended for faster inference).

## 1. Clone the Repository

```bash
git clone <your-repository-url>
cd Brain-Tumor-Detection
```

## 2. Backend Setup

1.  **Create a virtual environment** (recommended):
    ```bash
    python -m venv venv
    
    # Windows
    .\venv\Scripts\activate
    
    # macOS/Linux
    source venv/bin/activate
    ```

2.  **Install Python dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install nnU-Net**:
    ```bash
    pip install nnunetv2
    ```

4.  **Setup nnU-Net Weights**:
    - Download the pre-trained weights (Dataset002_BRATS19).
    - Extract them into a folder named `nnunet_weights` in the project root.
    - The structure should look like:
      ```
      nnunet_weights/
      └── Dataset002_BRATS19/
          └── nnUNetTrainer__nnUNetPlans__3d_fullres/
              └── ...
      ```

## 3. Frontend Setup

1.  **Navigate to the client directory**:
    ```bash
    cd client
    ```

2.  **Install dependencies**:
    ```bash
    npm install
    ```

## 4. Running the Application

You need to run both the backend (Flask) and frontend (React) servers.

### Terminal 1: Backend
From the project root directory:
```bash
# Ensure venv is activated
python app_nnunet.py
```
The backend will start at `http://127.0.0.1:5000`.

### Terminal 2: Frontend
From the `client` directory:
```bash
npm start
```
The frontend will start at `http://localhost:3000`.

## 5. Usage

1.  Open your browser and go to `http://localhost:3000`.
2.  Click "Browse Files" or drag & drop your MRI scans.
    - Supported formats: `.nii`, `.nii.gz`, `.jpg`, `.png`.
    - For best results, upload 4 `.nii` files (T1, T1ce, T2, FLAIR) for a single patient.
3.  Click "Analyze Scan".
4.  View the segmentation results, tumor statistics, and 3D overlay.

## Troubleshooting

-   **"nnU-Net initialization failed"**: Ensure you have installed `nnunetv2` and placed the weights in the correct folder.
-   **"Missing script: start"**: Make sure you are running `npm start` inside the `client` folder, not the root folder.

