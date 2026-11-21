import React from 'react';
import { useCurrentFrame, staticFile, Audio, Sequence } from 'remotion';
import { CensorAction } from '../types';

interface CensorBarProps {
  censors: CensorAction[];
}

export const CensorBar: React.FC<CensorBarProps> = ({ censors }) => {
  const frame = useCurrentFrame();

  const activeCensor = censors.find(
    (c) => frame >= c.startFrame && frame <= c.startFrame + c.durationFrames
  );

  return (
    <>
      {/* Audio bleep for each censor sequence */}
      {censors.map((c) => (
        <Sequence
          key={`bleep_${c.id}`}
          from={c.startFrame}
          durationInFrames={c.durationFrames}
        >
          <Audio src={staticFile('sfx/censor_bleep.mp3')} volume={0.5} />
        </Sequence>
      ))}

      {/* Visual jitter bar */}
      {activeCensor && (
        <div
          style={{
            position: 'absolute',
            top: activeCensor.y !== undefined ? `${activeCensor.y}px` : '48%',
            left: activeCensor.x !== undefined ? `${activeCensor.x}px` : '50%',
            width: activeCensor.width !== undefined ? `${activeCensor.width}px` : '380px',
            height: activeCensor.height !== undefined ? `${activeCensor.height}px` : '85px',
            transform: `translate(-50%, -50%) translate(${(frame % 2 === 0 ? 1 : -1) * 2}px, ${(frame % 3 === 0 ? 1 : -1) * 1.5}px)`,
            zIndex: 60,
            backgroundColor: '#0E1013',
            borderRadius: '10px',
            border: '2px solid #FF4444',
            boxShadow: '0 0 28px rgba(255, 68, 68, 0.5), inset 0 0 16px rgba(0,0,0,0.9)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontFamily: "'Courier New', Courier, monospace, -apple-system, sans-serif",
          }}
        >
          <span
            style={{
              color: '#FFE066',
              fontSize: '30px',
              fontWeight: 900,
              letterSpacing: '4px',
              textTransform: 'uppercase',
              textShadow: '0 0 12px rgba(255, 224, 102, 0.8)',
            }}
          >
            {activeCensor.label || '[CENSORED]'}
          </span>
        </div>
      )}
    </>
  );
};
