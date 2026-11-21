export interface WordToken {
  word: string;
  start: number; // in seconds
  end: number;   // in seconds
  highlight?: boolean;
}

export interface CaptionChunk {
  id: string;
  text: string;
  startFrame: number;
  endFrame: number;
  highlightWord?: string;
  words?: WordToken[];
}

export interface ClipCut {
  id: string;
  sourceFile: string;      // relative to public/ e.g. "media/ep01/clip_01_cfr.mp4"
  sourceStartSec: number;  // offset in source clip
  sourceEndSec: number;    // end in source clip
  startFrame: number;      // timeline start frame
  durationFrames: number;  // timeline duration in frames
  speed?: number;          // playback speed factor (default: 1.0)
  volume?: number;         // clip audio volume (0.0 - 1.0)
}

export interface PunchZoomAction {
  id: string;
  startFrame: number;
  durationFrames: number;
  scale: number;           // e.g. 1.12
  originX?: number;        // percentage e.g. 50
  originY?: number;        // percentage e.g. 40
}

export interface CensorAction {
  id: string;
  startFrame: number;
  durationFrames: number;
  label?: string;          // default: "[CENSORED]"
  x?: number;              // percentage or pixel
  y?: number;
  width?: number;
  height?: number;
}

export interface InterstitialCardData {
  id: string;
  startFrame: number;
  durationFrames: number;
  title: string;
  subtitle?: string;
  tag?: string;
}

export interface MusicTrack {
  file: string;            // relative to public/
  volume: number;          // 0.0 to 1.0 (ducked: e.g. 0.12)
  startFrame: number;
}

export interface EditPlan {
  episodeId: string;
  title: string;
  fps: number;
  totalFrames: number;
  durationSec: number;
  format: '9x16' | '16x9';
  cuts: ClipCut[];
  captions: CaptionChunk[];
  punchZooms: PunchZoomAction[];
  censors: CensorAction[];
  interstitials: InterstitialCardData[];
  outro: {
    startFrame: number;
    durationFrames: number;
    teaserText: string;
    episodeNumber: string;
  };
  music?: MusicTrack;
}
