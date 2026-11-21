import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { CaptionChunk } from '../types';

interface KineticCaptionProps {
  captions: CaptionChunk[];
  is9x16?: boolean;
}

export const KineticCaption: React.FC<KineticCaptionProps> = ({
  captions,
  is9x16 = true,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Find active caption chunk
  const activeCaption = captions.find(
    (c) => frame >= c.startFrame && frame <= c.endFrame
  );

  if (!activeCaption) {
    return null;
  }

  // Calculate local frame within this caption's lifespan
  const localFrame = frame - activeCaption.startFrame;

  // Snappy pop entrance: 0.94 -> 1.0
  const popScale = spring({
    frame: localFrame,
    fps,
    config: {
      damping: 15,
      mass: 0.5,
      stiffness: 220,
    },
  });

  const scale = interpolate(popScale, [0, 1], [0.94, 1.0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const opacity = interpolate(localFrame, [0, 3], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Split text into words and highlight punchline/emphasis word
  const words = activeCaption.text.trim().split(/\s+/);
  const targetHighlight = activeCaption.highlightWord?.toLowerCase();

  return (
    <div
      style={{
        position: 'absolute',
        bottom: is9x16 ? '420px' : '90px',
        left: 0,
        right: 0,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '0 48px',
        zIndex: 40,
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          transform: `scale(${scale})`,
          opacity,
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'center',
          alignItems: 'center',
          gap: '12px 14px',
          maxWidth: is9x16 ? '960px' : '1400px',
          textAlign: 'center',
          fontFamily: "'DM Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
          textShadow:
            '0 3px 12px rgba(0, 0, 0, 0.95), 0 1px 3px rgba(0, 0, 0, 0.9), 0 0 20px rgba(0, 0, 0, 0.7)',
        }}
      >
        {words.map((word, idx) => {
          // Clean punctuation for matching
          const cleanWord = word.replace(/[^a-zA-Z0-9]/g, '').toLowerCase();
          const isHighlighted =
            targetHighlight &&
            (cleanWord === targetHighlight ||
              targetHighlight.includes(cleanWord) ||
              cleanWord.includes(targetHighlight));

          return (
            <span
              key={`${activeCaption.id}-${idx}-${word}`}
              style={{
                color: isHighlighted ? '#FFE066' : '#FFFFFF',
                fontSize: is9x16 ? '54px' : '46px',
                fontWeight: 900,
                lineHeight: 1.15,
                letterSpacing: '-0.5px',
                textTransform: 'uppercase',
                display: 'inline-block',
                WebkitTextStroke: isHighlighted ? '2px #0E1013' : '1.5px #0E1013',
                textShadow: '0 4px 12px rgba(0, 0, 0, 0.95), 0 2px 4px rgba(0, 0, 0, 0.9)',
                filter: isHighlighted
                  ? 'drop-shadow(0 0 12px rgba(255, 224, 102, 0.7))'
                  : 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.8))',
              }}
            >
              {word}
            </span>
          );
        })}
      </div>
    </div>
  );
};
