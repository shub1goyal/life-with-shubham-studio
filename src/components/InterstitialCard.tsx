import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { InterstitialCardData } from '../types';

interface InterstitialCardProps {
  interstitials: InterstitialCardData[];
}

export const InterstitialCard: React.FC<InterstitialCardProps> = ({ interstitials }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const active = interstitials.find(
    (item) => frame >= item.startFrame && frame < item.startFrame + item.durationFrames
  );

  if (!active) {
    return null;
  }

  const localFrame = frame - active.startFrame;

  // Spring scale entrance
  const entrance = spring({
    frame: localFrame,
    fps,
    config: {
      damping: 16,
      mass: 0.5,
      stiffness: 180,
    },
  });

  const scale = interpolate(entrance, [0, 1], [0.92, 1.0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Fade out during last 6 frames
  const fadeOutStart = active.durationFrames - 6;
  const opacity = interpolate(
    localFrame,
    [0, 6, fadeOutStart, active.durationFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        zIndex: 55,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(14, 16, 19, 0.94)',
        opacity,
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
      }}
    >
      <div
        style={{
          transform: `scale(${scale})`,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          padding: '48px 64px',
          maxWidth: '850px',
          borderRadius: '24px',
          backgroundColor: '#16191E',
          border: '1px solid rgba(255, 224, 102, 0.25)',
          boxShadow: '0 24px 64px rgba(0, 0, 0, 0.8), 0 0 30px rgba(255, 224, 102, 0.1)',
          fontFamily: "'DM Sans', 'Inter', -apple-system, sans-serif",
        }}
      >
        {active.tag && (
          <span
            style={{
              color: '#FFE066',
              fontSize: '18px',
              fontWeight: 800,
              letterSpacing: '2px',
              textTransform: 'uppercase',
              marginBottom: '16px',
            }}
          >
            {active.tag}
          </span>
        )}
        <h2
          style={{
            color: '#FFFFFF',
            fontSize: '44px',
            fontWeight: 800,
            lineHeight: 1.2,
            margin: '0 0 16px 0',
            letterSpacing: '-0.5px',
          }}
        >
          {active.title}
        </h2>
        {active.subtitle && (
          <p
            style={{
              color: 'rgba(255, 255, 255, 0.7)',
              fontSize: '24px',
              fontWeight: 500,
              margin: 0,
              lineHeight: 1.4,
            }}
          >
            {active.subtitle}
          </p>
        )}
      </div>
    </div>
  );
};
