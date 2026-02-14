import React from 'react'
import styled from 'styled-components';
import { useState } from 'react';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';

const Container = styled.div`
    width: 100%;
    min-height: 300px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 16px;
    align-items: center;
    border: 3px dashed rgba(100, 150, 255, 0.4);
    border-radius: 20px;
    background: linear-gradient(135deg, rgba(30, 60, 114, 0.3) 0%, rgba(20, 40, 80, 0.4) 100%);
    backdrop-filter: blur(10px);
    padding: 40px 20px;
    transition: all 0.3s;
    cursor: pointer;
    
    &:hover {
        border-color: rgba(120, 170, 255, 0.6);
        background: linear-gradient(135deg, rgba(40, 70, 124, 0.4) 0%, rgba(30, 50, 90, 0.5) 100%);
        transform: translateY(-2px);
    }
`;

const IconWrapper = styled.div`
    animation: float 3s ease-in-out infinite;
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
`;

const Title = styled.div`
    font-size: 24px;
    font-weight: 700;
    color: #ffffff;
    text-align: center;
`;

const SubTitle = styled.div`
    font-size: 14px;
    color: rgba(255, 255, 255, 0.7);
    text-align: center;
    line-height: 1.6;
    max-width: 400px;
`;

const FileTypeBadges = styled.div`
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    justify-content: center;
`;

const Badge = styled.span`
    padding: 6px 12px;
    border-radius: 20px;
    background: rgba(100, 150, 255, 0.2);
    border: 1px solid rgba(100, 150, 255, 0.4);
    color: #a0c0ff;
    font-size: 12px;
    font-weight: 600;
`;

const UploadButton = styled.label`
    font-size: 16px;
    font-weight: 600;
    color: #ffffff;
    cursor: pointer;
    padding: 14px 32px;
    border-radius: 12px;
    background: linear-gradient(135deg, #4a90ff 0%, #357abd 100%);
    transition: all 0.3s;
    box-shadow: 0 4px 15px rgba(74, 144, 255, 0.4);
    
    &:hover {
        background: linear-gradient(135deg, #5aa0ff 0%, #458acd 100%);
        box-shadow: 0 6px 20px rgba(74, 144, 255, 0.6);
        transform: translateY(-2px);
    }
    
    &:active {
        transform: translateY(0px);
    }
`;

const HiddenInput = styled.input`
    display: none;
`;

const FileList = styled.div`
    width: 100%;
    max-width: 500px;
    margin-top: 16px;
`;

const FileItem = styled.div`
    background: rgba(30, 60, 114, 0.4);
    border: 1px solid rgba(100, 150, 255, 0.3);
    border-radius: 12px;
    padding: 12px 16px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    color: #e0e0ff;
    font-size: 13px;
`;

const FileName = styled.span`
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
`;

const FileSize = styled.span`
    color: rgba(255, 255, 255, 0.6);
    font-size: 11px;
    margin-left: 12px;
`;

const ImageUpload = ({ images, setImages }) => {

    const handleFileChange = async (event) => {
        const files = Array.from(event.target.files);

        if (files.length === 0) return;

        const processedFiles = await Promise.all(
            files.map(async (file) => {
                return new Promise((resolve) => {
                    const reader = new FileReader();
                    reader.onload = (e) => {
                        resolve({
                            base64_file: e.target.result,
                            file_name: file.name,
                            file_type: file.type || 'application/octet-stream',
                            file_size: file.size
                        });
                    };
                    reader.readAsDataURL(file);
                });
            })
        );

        setImages(processedFiles);
    };

    const formatFileSize = (bytes) => {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    };

    return (
        <>
            <Container onClick={() => document.getElementById('file-upload').click()}>
                <IconWrapper>
                    <CloudUploadIcon sx={{ fontSize: "80px", color: "#4a90ff" }} />
                </IconWrapper>
                <Title>Upload Brain MRI Scan(s)</Title>
                <SubTitle>
                    Drag and drop files here or click to browse<br />
                    Upload 1-4 images for optimal analysis
                </SubTitle>
                <FileTypeBadges>
                    <Badge>.NII</Badge>
                    <Badge>.NII.GZ</Badge>
                    <Badge>.JPG</Badge>
                    <Badge>.PNG</Badge>
                </FileTypeBadges>
                <UploadButton htmlFor="file-upload" onClick={(e) => e.stopPropagation()}>
                    Browse Files
                </UploadButton>
                <HiddenInput
                    id="file-upload"
                    type="file"
                    accept=".nii,.nii.gz,.jpg,.jpeg,.png"
                    multiple
                    onChange={handleFileChange}
                />
            </Container>

            {images && images.length > 0 && (
                <FileList>
                    {images.map((img, index) => (
                        <FileItem key={index}>
                            <FileName>📄 {img.file_name}</FileName>
                            <FileSize>{formatFileSize(img.file_size || 0)}</FileSize>
                        </FileItem>
                    ))}
                </FileList>
            )}
        </>
    )
}

export default ImageUpload