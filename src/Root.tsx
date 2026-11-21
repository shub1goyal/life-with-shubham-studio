import React from 'react';
import { Composition } from 'remotion';
import { Reel9x16 } from './compositions/Reel9x16';
import { Vlog16x9 } from './compositions/Vlog16x9';
import { EditPlan } from './types';

// Fallback edit plan if none exists yet
export const fallbackEditPlan: EditPlan = {
  episodeId: 'PREVIEW',
  title: 'WAITING FOR CONTEXT ANALYSIS',
  fps: 30,
  totalFrames: 150,
  durationSec: 5,
  format: '9x16',
  cuts: [],
  captions: [],
  punchZooms: [],
  censors: [],
  interstitials: [],
  outro: {
    startFrame: 90,
    durationFrames: 60,
    teaserText: 'Run scripts/02_analyze_context.py to generate timeline.',
    episodeNumber: 'PREVIEW',
  },
};

// Try loading active edit plan from public/edit_plan.json, fallback if not yet present
let initialEditPlan: EditPlan = fallbackEditPlan;
try {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const loadedPlan = require('../public/edit_plan.json');
  if (loadedPlan && loadedPlan.cuts && loadedPlan.cuts.length > 0) {
    initialEditPlan = loadedPlan;
  }
} catch (e) {
  // Use fallback plan until first analysis run
}

export const RemotionRoot: React.FC = () => {
  const durationInFrames = Math.max(initialEditPlan.totalFrames || 300, 30);

  return (
    <>
      {/* 9:16 Instagram Reel / YouTube Shorts Composition */}
      <Composition
        id="Reel9x16"
        component={Reel9x16 as React.FC<Record<string, unknown>>}
        durationInFrames={durationInFrames}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          editPlan: initialEditPlan,
        }}
      />

      {/* 16:9 YouTube Vlog Composition */}
      <Composition
        id="Vlog16x9"
        component={Vlog16x9 as React.FC<Record<string, unknown>>}
        durationInFrames={durationInFrames}
        fps={30}
        width={1920}
        height={1080}
        defaultProps={{
          editPlan: initialEditPlan,
        }}
      />
    </>
  );
};
