import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Sequence,
  staticFile,
  useVideoConfig,
  Video,
} from 'remotion';
import { EditPlan } from '../types';
import { CornerBadge } from '../components/CornerBadge';
import { KineticCaption } from '../components/KineticCaption';
import { CensorBar } from '../components/CensorBar';
import { PunchZoom } from '../components/PunchZoom';
import { InterstitialCard } from '../components/InterstitialCard';
import { OutroCard } from '../components/OutroCard';

export interface Reel9x16Props {
  editPlan?: EditPlan;
}

export const Reel9x16: React.FC<Reel9x16Props> = ({ editPlan }) => {
  const { fps } = useVideoConfig();

  const cuts = editPlan?.cuts ?? [];
  const captions = editPlan?.captions ?? [];
  const punchZooms = editPlan?.punchZooms ?? [];
  const censors = editPlan?.censors ?? [];
  const interstitials = editPlan?.interstitials ?? [];
  const outro = editPlan?.outro;
  const music = editPlan?.music;
  const episodeId = editPlan?.episodeId ?? 'EP 01';
  const title = editPlan?.title ?? 'LIFE WITH SHUBHAM';

  return (
    <AbsoluteFill style={{ backgroundColor: '#000000', overflow: 'hidden' }}>
      {/* 1. Base Video Track with PunchZooms */}
      <PunchZoom punchZooms={punchZooms}>
        <AbsoluteFill>
          {cuts.map((cut) => {
            const startFromFrame = Math.round(cut.sourceStartSec * fps);
            const endAtFrame = Math.round(cut.sourceEndSec * fps);

            return (
              <Sequence
                key={cut.id}
                from={cut.startFrame}
                durationInFrames={cut.durationFrames}
              >
                <Video
                  src={staticFile(cut.sourceFile)}
                  startFrom={startFromFrame}
                  endAt={endAtFrame}
                  volume={cut.volume ?? 1.0}
                  style={{
                    width: '100%',
                    height: '100%',
                    objectFit: 'cover',
                  }}
                />
              </Sequence>
            );
          })}
        </AbsoluteFill>
      </PunchZoom>

      {/* 2. Background Music with Ducking */}
      {music && (
        <Sequence from={music.startFrame || 0}>
          <Audio
            src={staticFile(music.file)}
            volume={music.volume ?? 0.15}
          />
        </Sequence>
      )}

      {/* 3. Subtle Vignette for mobile contrast */}
      <AbsoluteFill
        style={{
          pointerEvents: 'none',
          boxShadow: 'inset 0 0 120px rgba(0, 0, 0, 0.45)',
          zIndex: 30,
        }}
      />

      {/* 4. Top-Left Minimal Corner Badge */}
      <CornerBadge
        episodeNumber={episodeId.toUpperCase()}
        seriesTitle="LIFE WITH SHUBHAM"
        subtitle={title !== 'LIFE WITH SHUBHAM' ? title : undefined}
      />

      {/* 5. Hinglish Kinetic Captions */}
      <KineticCaption captions={captions} is9x16={true} />

      {/* 6. Comedic Censor Bars */}
      <CensorBar censors={censors} />

      {/* 7. Comedic Interstitial Cards */}
      <InterstitialCard interstitials={interstitials} />

      {/* 8. 2-Second Dark Obsidian Outro Card */}
      {outro && (
        <OutroCard
          startFrame={outro.startFrame}
          durationFrames={outro.durationFrames}
          teaserText={outro.teaserText}
          episodeNumber={outro.episodeNumber || episodeId.toUpperCase()}
        />
      )}
    </AbsoluteFill>
  );
};
