import React from 'react';
import styled from 'styled-components';

const Container = styled.div`
  width: 100%;
  margin-top: 20px;
`;

const CardsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
`;

const StatCard = styled.div`
  background: linear-gradient(135deg, 
    ${({ gradientStart }) => gradientStart || 'rgba(60, 100, 180, 0.4)'} 0%, 
    ${({ gradientEnd }) => gradientEnd || 'rgba(40, 80, 160, 0.6)'} 100%);
  border-radius: 16px;
  padding: 20px;
  border: 1px solid ${({ borderColor }) => borderColor || 'rgba(100, 150, 255, 0.3)'};
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  gap: 16px;
  transition: transform 0.3s, box-shadow 0.3s;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
  }
`;

const IconContainer = styled.div`
  width: 60px;
  height: 60px;
  border-radius: 12px;
  background: ${({ bgColor }) => bgColor || 'rgba(255, 255, 255, 0.1)'};
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
`;

const StatContent = styled.div`
  flex: 1;
`;

const StatLabel = styled.div`
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 4px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const StatValue = styled.div`
  font-size: 28px;
  font-weight: 700;
  color: #ffffff;
  display: flex;
  align-items: baseline;
  gap: 4px;
`;

const StatUnit = styled.span`
  font-size: 16px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.8);
`;

const StatDescription = styled.div`
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 4px;
  font-weight: 400;
`;

const TumorStatistics = ({ statistics }) => {
  if (!statistics) {
    return null;
  }

  const { regions, total_volume } = statistics;

  // Define card configurations
  const cardConfigs = [
    {
      label: 'Enhancing Tumor',
      description: 'Active tumor growth',
      icon: '🔴',
      gradientStart: 'rgba(220, 60, 60, 0.4)',
      gradientEnd: 'rgba(180, 40, 40, 0.6)',
      borderColor: 'rgba(255, 100, 100, 0.4)',
      bgColor: 'rgba(255, 80, 80, 0.2)',
      volume: regions?.find(r => r.name === 'Enhancing Tumor')?.volume || 0
    },
    {
      label: 'Necrotic Core',
      description: 'Non-enhancing tumor',
      icon: '🟡',
      gradientStart: 'rgba(220, 180, 60, 0.4)',
      gradientEnd: 'rgba(180, 140, 40, 0.6)',
      borderColor: 'rgba(255, 220, 100, 0.4)',
      bgColor: 'rgba(255, 200, 80, 0.2)',
      volume: regions?.find(r => r.name === 'Non-Enhancing Tumor')?.volume || 0
    },
    {
      label: 'Edema',
      description: 'Swelling around tumor',
      icon: '🟢',
      gradientStart: 'rgba(60, 220, 120, 0.4)',
      gradientEnd: 'rgba(40, 180, 100, 0.6)',
      borderColor: 'rgba(100, 255, 150, 0.4)',
      bgColor: 'rgba(80, 255, 120, 0.2)',
      volume: regions?.find(r => r.name === 'Edema')?.volume || 0
    },
    {
      label: 'Total Tumor Volume',
      description: 'Combined volume',
      icon: '🧠',
      gradientStart: 'rgba(100, 140, 220, 0.4)',
      gradientEnd: 'rgba(60, 100, 180, 0.6)',
      borderColor: 'rgba(120, 170, 255, 0.4)',
      bgColor: 'rgba(100, 150, 255, 0.2)',
      volume: total_volume || 0
    }
  ];

  return (
    <Container>
      <CardsGrid>
        {cardConfigs.map((config, index) => (
          <StatCard
            key={index}
            gradientStart={config.gradientStart}
            gradientEnd={config.gradientEnd}
            borderColor={config.borderColor}
          >
            <IconContainer bgColor={config.bgColor}>
              {config.icon}
            </IconContainer>
            <StatContent>
              <StatLabel>{config.label}</StatLabel>
              <StatValue>
                {config.volume.toFixed(1)}
                <StatUnit>cm³</StatUnit>
              </StatValue>
              {config.description && (
                <StatDescription>{config.description}</StatDescription>
              )}
            </StatContent>
          </StatCard>
        ))}
      </CardsGrid>
    </Container>
  );
};

export default TumorStatistics;
