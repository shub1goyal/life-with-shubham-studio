import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';

interface OutroCardProps {
  startFrame: number;
  durationFrames: number;
  teaserText?: string;
  episodeNumber?: string;
}

export const OutroCard: React.FC<OutroCardProps> = ({
  startFrame,
  durationFrames,
  teaserText = 'Kal subah 6 AM leg day... agar utha toh.',
  episodeNumber = 'EP 01',
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (frame < startFrame) {
    return null;
  }

  const localFrame = frame - startFrame;

  const entrance = spring({
    frame: localFrame,
    fps,
    config: {
      damping: 18,
      mass: 0.6,
      stiffness: 150,
    },
  });

  const opacity = interpolate(localFrame, [0, 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const scale = interpolate(entrance, [0, 1], [0.95, 1.0]);

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        zIndex: 90,
        backgroundColor: '#0E1013',
        opacity,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '60px',
        fontFamily: "'DM Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
      }}
    >
      <div
        style={{
          transform: `scale(${scale})`,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          maxWidth: '880px',
        }}
      >
        {/* Subtle glowing pill */}
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 20px',
            borderRadius: '9999px',
            backgroundColor: 'rgba(255, 224, 102, 0.1)',
            border: '1px solid rgba(255, 224, 102, 0.3)',
            marginBottom: '32px',
          }}
        >
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: '#FFE066',
            }}
          />
          <span
            style={{
              color: '#FFE066',
              fontSize: '16px',
              fontWeight: 800,
              letterSpacing: '1.5px',
              textTransform: 'uppercase',
            }}
          >
            END OF {episodeNumber}
          </span>
        </div>

        {/* Series Title */}
        <h1
          style={{
            color: '#FFFFFF',
            fontSize: '56px',
            fontWeight: 900,
            letterSpacing: '-1px',
            margin: '0 0 24px 0',
            textTransform: 'uppercase',
          }}
        >
          LIFE WITH SHUBHAM
        </h1>

        {/* Teaser text box */}
        <div
          style={{
            marginTop: '16px',
            padding: '24px 32px',
            borderRadius: '16px',
            backgroundColor: '#16191E',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            boxShadow: '0 12px 32px rgba(0, 0, 0, 0.4)',
          }}
        >
          <p
            style={{
              color: 'rgba(255, 255, 255, 0.5)',
              fontSize: '16px',
              fontWeight: 700,
              letterSpacing: '1px',
              textTransform: 'uppercase',
              margin: '0 0 8px 0',
            }}
          >
            Next Episode Preview
          </p>
          <p
            style={{
              color: '#FFE066',
              fontSize: '28px',
              fontWeight: 700,
              margin: 0,
              lineHeight: 1.3,
            }}
          >
            &ldquo;{teaserText}&rdquo;
          </p>
        </div>
      </div>
    </div>
  );
};
