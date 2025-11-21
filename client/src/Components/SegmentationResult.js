import React from 'react';
import styled from 'styled-components';

const Container = styled.div`
  width: 100%;
  background: linear-gradient(135deg, #1a1f3a 0%, #0f1419 100%);
  border-radius: 20px;
  padding: 0;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
`;

const Header = styled.div`
  background: linear-gradient(135deg, rgba(30, 60, 114, 0.8) 0%, rgba(42, 82, 152, 0.6) 100%);
  backdrop-filter: blur(10px);
  padding: 20px 30px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid rgba(100, 150, 255, 0.2);
`;

const HeaderTitle = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 24px;
  font-weight: 600;
  color: #ffffff;
`;

const BrainIcon = styled.div`
  font-size: 32px;
`;

const Legend = styled.div`
  display: flex;
  gap: 20px;
  align-items: center;
`;

const LegendItem = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #e0e0e0;
`;

const ColorDot = styled.div`
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: ${props => props.color};
  box-shadow: 0 0 10px ${props => props.color};
`;

const ViewersContainer = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  padding: 30px;
  background: rgba(15, 20, 35, 0.6);
`;

const ViewerCard = styled.div`
  background: linear-gradient(135deg, rgba(20, 30, 50, 0.9) 0%, rgba(10, 15, 25, 0.95) 100%);
  border-radius: 16px;
  padding: 20px;
  border: 1px solid rgba(100, 150, 255, 0.15);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(10px);
`;

const ViewerTitle = styled.div`
  font-size: 14px;
  font-weight: 600;
  color: #a0b0d0;
  margin-bottom: 15px;
  text-transform: uppercase;
  letter-spacing: 1px;
`;

const ImageContainer = styled.div`
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  background: #000;
  border-radius: 12px;
  overflow: hidden;
  border: 2px solid rgba(100, 150, 255, 0.3);
  box-shadow: inset 0 0 30px rgba(0, 0, 0, 0.8);
`;

const ScanImage = styled.img`
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
`;

const Crosshair = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  
  &::before, &::after {
    content: '';
    position: absolute;
    background: rgba(100, 150, 255, 0.4);
  }
  
  &::before {
    left: 50%;
    top: 0;
    bottom: 0;
    width: 1px;
  }
  
  &::after {
    top: 50%;
    left: 0;
    right: 0;
    height: 1px;
  }
`;

const Controls = styled.div`
  display: flex;
  gap: 8px;
  margin-top: 12px;
  justify-content: center;
  align-items: center;
`;

const ControlButton = styled.button`
  background: rgba(60, 100, 180, 0.3);
  border: 1px solid rgba(100, 150, 255, 0.4);
  color: #a0c0ff;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.3s;
  
  &:hover {
    background: rgba(80, 120, 200, 0.5);
    border-color: rgba(120, 170, 255, 0.6);
  }
`;

const Slider = styled.input`
  flex: 1;
  max-width: 200px;
  height: 4px;
  border-radius: 2px;
  background: rgba(60, 100, 180, 0.3);
  outline: none;
  
  &::-webkit-slider-thumb {
    appearance: none;
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: #4a90ff;
    cursor: pointer;
    box-shadow: 0 0 10px rgba(74, 144, 255, 0.8);
  }
`;

const Message = styled.div`
  padding: 20px 30px;
  background: rgba(30, 60, 114, 0.3);
  border-top: 1px solid rgba(100, 150, 255, 0.2);
  color: #c0d0f0;
  font-size: 18px;
  line-height: 1.6;
`;

const SegmentationResult = ({ originalImage, overlayImage, message }) => {
  const [zoom, setZoom] = React.useState(1);
  const [rotation, setRotation] = React.useState(0);

  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev + 0.5, 3));
  };

  const handleRotate = () => {
    setRotation(prev => (prev + 90) % 360);
  };

  const handleSliderChange = (e) => {
    // Map 0-100 to 1x-3x zoom
    const value = parseInt(e.target.value);
    const newZoom = 1 + (value / 50);
    setZoom(newZoom);
  };

  const imageStyle = {
    transform: `scale(${zoom}) rotate(${rotation}deg)`,
    transition: 'transform 0.3s ease'
  };

  return (
    <Container>
      <Header>
        <HeaderTitle>
          <BrainIcon>🧠</BrainIcon>
          Brain Tumor Segmentation Analysis
        </HeaderTitle>
        <Legend>
          <LegendItem>
            <ColorDot color="#ff4444" />
            Enhancing Tumor
          </LegendItem>
          <LegendItem>
            <ColorDot color="#ffff44" />
            Necrotic Core
          </LegendItem>
          <LegendItem>
            <ColorDot color="#44ff44" />
            Edema
          </LegendItem>
        </Legend>
      </Header>

      <ViewersContainer>
        <ViewerCard>
          <ViewerTitle>Original MRI Scan</ViewerTitle>
          <ImageContainer>
            <ScanImage
              src={originalImage}
              alt="Original MRI scan"
              style={imageStyle}
            />
            <Crosshair />
          </ImageContainer>
          <Controls>
            <ControlButton onClick={handleZoomIn}>🔍 Zoom +</ControlButton>
            <ControlButton onClick={handleRotate}>↻ Rotate</ControlButton>
            <Slider
              type="range"
              min="0"
              max="100"
              value={(zoom - 1) * 50}
              onChange={handleSliderChange}
            />
          </Controls>
        </ViewerCard>

        <ViewerCard>
          <ViewerTitle>Segmentation Overlay</ViewerTitle>
          <ImageContainer>
            <ScanImage
              src={overlayImage}
              alt="Segmentation overlay"
              style={imageStyle}
            />
            <Crosshair />
          </ImageContainer>
          <Controls>
            <ControlButton onClick={handleZoomIn}>🔍 Zoom +</ControlButton>
            <ControlButton onClick={handleRotate}>↻ Rotate</ControlButton>
            <Slider
              type="range"
              min="0"
              max="100"
              value={(zoom - 1) * 50}
              onChange={handleSliderChange}
            />
          </Controls>
        </ViewerCard>
      </ViewersContainer>

      {message && (
        <Message>{message}</Message>
      )}
    </Container>
  );
};

export default SegmentationResult;
