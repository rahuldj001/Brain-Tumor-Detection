
import { ThemeProvider } from "styled-components";
import { useState } from "react";
import { darkTheme, } from "./utils/themes";
import styled from 'styled-components';
import ImageUpload from "./Components/ImageUpload";
import ImagesCard from "./Components/ImagesCard";
import Loader from "./Components/Loader/Loader";
import ResultCard from "./Components/ResultCard";
import SegmentationResult from "./Components/SegmentationResult";
import TumorStatistics from "./Components/TumorStatistics";
import axios from 'axios';
import { Images } from "./data";
import { useEffect } from "react";


const Body = styled.div`
  display: flex; 
  align-items: center;
  flex-direction: column;
  width: 100vw;
  min-height: 100vh;
  background: linear-gradient(135deg, #0f1419 0%, #1a1f3a 50%, #0f1419 100%);
  overflow-y: scroll;
  overflow-x: hidden;
`;

const Heading = styled.div`
  font-size: 48px;
  @media (max-width: 530px) {
    font-size: 32px;
  }
  font-weight: 700;
  color: #ffffff;
  margin: 3% 0px 2% 0px;
  text-align: center;
  text-shadow: 0 0 30px rgba(74, 144, 255, 0.5);
  display: flex;
  align-items: center;
  gap: 16px;
`;

const Container = styled.div`
  max-width: 1400px;
  width: 100%;
  display: flex; 
  justify-content: center;
  flex-direction: column;
  gap: 30px;
  padding: 2% 3% 6% 3%;
  
  @media (max-width: 1100px) {
    padding: 2% 2% 6% 2%;
  }
`;

const Centered = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 50vh;
`;

const Section = styled.div`
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 30px;
  align-items: center;
`;

const UploadSection = styled(Section)`
  max-width: 800px;
  margin: 0 auto;
`;

const ResultsSection = styled(Section)`
  max-width: 1400px;
  margin: 0 auto;
  animation: fadeIn 0.5s ease-in;
  
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }
`;

const TextCenter = styled.div`
  font-size: 18px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.7);
  text-align: center;
  margin: 10px 0;
`;

const SelectedImages = styled.div`
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 16px;
  margin: 20px 0;
`;

const Button = styled.button`
  min-height: 50px;
  padding: 0 40px;
  border-radius: 12px;
  border: none;
  background: linear-gradient(135deg, #4a90ff 0%, #357abd 100%);
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 15px rgba(74, 144, 255, 0.4);
  text-transform: uppercase;
  letter-spacing: 1px;
  
  &:hover {
    background: linear-gradient(135deg, #5aa0ff 0%, #458acd 100%);
    box-shadow: 0 6px 20px rgba(74, 144, 255, 0.6);
    transform: translateY(-2px);
  }
  
  &:active {
    transform: translateY(0);
  }
  
  &:disabled {
    background: #ccc;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 20px;
  justify-content: center;
  margin-top: 10px;
`;

const Typo = styled.div`
  font-size: 24px;
  font-weight: 600;
  color: #ffffff;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  
  &::before {
    content: '';
    display: block;
    width: 4px;
    height: 24px;
    background: #4a90ff;
    border-radius: 2px;
  }
`;

const ResultWrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
`;



function App() {
  const [images, setImages] = useState([]);
  const [predictions, setPredictions] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showPrediction, setShowPrediction] = useState(false);

  const generatePrediction = async () => {
    setLoading(true);
    setShowPrediction(false);

    try {
      const formData = new FormData();
      images.forEach((img, index) => {
        formData.append('images', img.base64_file);
      });

      const response = await axios.post("http://127.0.0.1:5000/predict", {
        images: images.map(img => img.base64_file)
      });

      setPredictions(response.data);
      setShowPrediction(true);
    } catch (error) {
      console.error("Error generating prediction:", error);
      alert("Error generating prediction. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const generateNewImages = () => {
    const randomImage = Images[Math.floor(Math.random() * Images.length)];
    // Convert sample image format to match upload format
    const formattedImage = {
      base64_file: randomImage.img, // Assuming data.js has base64 or url
      file_name: `Sample_${Math.floor(Math.random() * 1000)}.jpg`,
      file_type: 'image/jpeg'
    };
    setImages([formattedImage]);
    setShowPrediction(false);
  };

  useEffect(() => {
    // Optional: Load a sample on start
    // generateNewImages();
  }, []);

  return (
    <ThemeProvider theme={darkTheme}>
      <Body>
        <Heading>Brain Tumor Detector 🧠</Heading>
        <Container>
          {loading ? (
            <Centered>
              <Loader />
            </Centered>
          ) : (
            <>
              <UploadSection>
                <ImageUpload images={images} setImages={setImages} />

                {images.length > 0 && (
                  <>
                    <ButtonGroup>
                      <Button onClick={() => generateNewImages()}>
                        Try Sample Data
                      </Button>
                      <Button onClick={generatePrediction}>
                        Analyze Scan
                      </Button>
                    </ButtonGroup>
                  </>
                )}

                {images.length === 0 && (
                  <Button onClick={() => generateNewImages()} style={{ background: 'rgba(255,255,255,0.1)', boxShadow: 'none', border: '1px solid rgba(255,255,255,0.2)' }}>
                    Load Sample Data
                  </Button>
                )}
              </UploadSection>

              {showPrediction && predictions && (
                <ResultsSection>
                  <Typo>Analysis Results</Typo>

                  {predictions.overlay_image && (
                    <SegmentationResult
                      originalImage={predictions.original_image || images[0]?.base64_file}
                      overlayImage={predictions.overlay_image}
                      message={predictions.message}
                    />
                  )}

                  {predictions.statistics && (
                    <TumorStatistics statistics={predictions.statistics} />
                  )}
                </ResultsSection>
              )}
            </>
          )}
        </Container>
      </Body>
    </ThemeProvider>
  );
}

export default App;
