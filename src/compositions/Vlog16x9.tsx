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

export interface Vlog16x9Props {
  editPlan?: EditPlan;
}

export const Vlog16x9: React.FC<Vlog16x9Props> = ({ editPlan }) => {
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
    <AbsoluteFill style={{ backgroundColor: '#0B0D0F', overflow: 'hidden' }}>
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
                    objectFit: 'contain',
                    backgroundColor: '#000000',
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
            volume={music.volume ?? 0.12}
          />
        </Sequence>
      )}

      {/* 3. Subtle Vignette */}
      <AbsoluteFill
        style={{
          pointerEvents: 'none',
          boxShadow: 'inset 0 0 100px rgba(0, 0, 0, 0.5)',
          zIndex: 30,
        }}
      />

      {/* 4. Corner Badge */}
      <CornerBadge
        episodeNumber={episodeId.toUpperCase()}
        seriesTitle="LIFE WITH SHUBHAM"
        subtitle={title !== 'LIFE WITH SHUBHAM' ? title : undefined}
      />

      {/* 5. Captions (16:9 safe zone) */}
      <KineticCaption captions={captions} is9x16={false} />

      {/* 6. Censor Bar */}
      <CensorBar censors={censors} />

      {/* 7. Interstitial Chapter Cards */}
      <InterstitialCard interstitials={interstitials} />

      {/* 8. 2-Second Outro */}
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
