import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { PunchZoomAction } from '../types';

interface PunchZoomProps {
  punchZooms: PunchZoomAction[];
  children: React.ReactNode;
}

export const PunchZoom: React.FC<PunchZoomProps> = ({ punchZooms, children }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Find active punch zoom
  const activeZoom = punchZooms.find(
    (z) => frame >= z.startFrame && frame < z.startFrame + z.durationFrames
  );

  let scale = 1.0;
  let originX = 50;
  let originY = 50;

  if (activeZoom) {
    originX = activeZoom.originX ?? 50;
    originY = activeZoom.originY ?? 50;

    // Instant or snappy micro-spring
    const localFrame = frame - activeZoom.startFrame;
    const punchProgress = spring({
      frame: localFrame,
      fps,
      config: {
        damping: 18,
        mass: 0.4,
        stiffness: 280,
      },
    });

    scale = interpolate(punchProgress, [0, 1], [1.0, activeZoom.scale || 1.12]);
  }

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        transform: `scale(${scale})`,
        transformOrigin: `${originX}% ${originY}%`,
        transition: 'transform 0.05s ease-out',
        willChange: 'transform',
      }}
    >
      {children}
    </div>
  );
};
