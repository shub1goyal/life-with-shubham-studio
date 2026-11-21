import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';

interface CornerBadgeProps {
  episodeNumber?: string;
  seriesTitle?: string;
  subtitle?: string;
}

export const CornerBadge: React.FC<CornerBadgeProps> = ({
  episodeNumber = 'EP 01',
  seriesTitle = 'LIFE WITH SHUBHAM',
  subtitle,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Gentle slide and spring entrance over first 12 frames
  const entrance = spring({
    frame,
    fps,
    config: {
      damping: 16,
      mass: 0.6,
      stiffness: 140,
    },
  });

  const opacity = interpolate(frame, [0, 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const translateY = interpolate(entrance, [0, 1], [-20, 0]);

  return (
    <div
      style={{
        position: 'absolute',
        top: 60,
        left: 50,
        zIndex: 50,
        opacity,
        transform: `translateY(${translateY}px)`,
        display: 'inline-flex',
        alignItems: 'center',
        gap: '8px',
        padding: '10px 18px',
        borderRadius: '9999px',
        backgroundColor: 'rgba(14, 16, 19, 0.78)',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
        border: '1px solid rgba(255, 255, 255, 0.12)',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.35)',
        fontFamily: "'DM Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
      }}
    >
      {/* Live recording dot */}
      <span
        style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          backgroundColor: '#FFE066',
          boxShadow: '0 0 10px #FFE066',
        }}
      />
      <span
        style={{
          color: '#FFFFFF',
          fontSize: '18px',
          fontWeight: 800,
          letterSpacing: '1.2px',
          textTransform: 'uppercase',
        }}
      >
        {seriesTitle}
      </span>
      <span
        style={{
          color: 'rgba(255, 255, 255, 0.35)',
          fontSize: '18px',
          fontWeight: 400,
        }}
      >
        |
      </span>
      <span
        style={{
          color: '#FFE066',
          fontSize: '18px',
          fontWeight: 700,
          letterSpacing: '0.8px',
        }}
      >
        {episodeNumber}
      </span>
      {subtitle && (
        <span
          style={{
            marginLeft: '6px',
            color: 'rgba(255, 255, 255, 0.65)',
            fontSize: '15px',
            fontWeight: 500,
          }}
        >
          • {subtitle}
        </span>
      )}
    </div>
  );
};
