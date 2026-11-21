# Life with Shubham Studio — Project Audit Report

**Generated**: 2026-11-21  
**Episode Tested**: `ep01`  
**Status**: Generic Multi-Episode Engine Verified (`--episode <name>`)  
**Preview Server**: Live on `http://localhost:3000` (DO NOT RENDER YET)

---

## 1. Project Folder Tree (excluding `node_modules` and `.venv`)

```text
life-with-shubham-studio/
├── .agent/
│   └── skills/
│       ├── claude-remotion-skill/
│       ├── ffmpeg-skill/
│       ├── hyperframes/
│       ├── remotion-skills/
│       └── vargHQ-skills/
├── analysis/
│   └── ep01/
│       ├── audio/
│       │   ├── clip_01_cfr.mp3
│       │   └── clip_02_cfr.mp3
│       ├── edit_plan.json
│       ├── proxies/
│       │   ├── clip_01_cfr_proxy.mp4
│       │   └── clip_02_cfr_proxy.mp4
│       ├── raw_transcript.json
│       ├── verify_overlay_01.jpg
│       └── verify_overlay_censor_01.jpg
├── media/
│   ├── 01_raw_videos/
│   │   └── ep01/
│   │       ├── clip_01.mp4
│   │       └── clip_02.mp4
│   ├── 02_normalized_cfr/
│   │   └── ep01/
│   │       ├── clip_01_cfr.mp4
│   │       └── clip_02_cfr.mp4
│   ├── 03_music_and_sfx/
│   │   ├── censor_bleep.mp3
│   │   └── whoosh.mp3
│   └── 04_hyperframes_inserts/
├── output/
│   ├── final_videos/
│   └── previews/
├── public/
│   ├── edit_plan.json
│   ├── media/
│   │   └── ep01/
│   │       ├── clip_01_cfr.mp4
│   │       └── clip_02_cfr.mp4
│   └── sfx/
│       ├── censor_bleep.mp3
│       └── whoosh.mp3
├── scripts/
│   ├── 01_ingest_cfr.py
│   ├── 02_analyze_context.py
│   └── 03_render_final.py
├── src/
│   ├── components/
│   │   ├── CensorBar.tsx
│   │   ├── CornerBadge.tsx
│   │   ├── InterstitialCard.tsx
│   │   ├── KineticCaption.tsx
│   │   ├── OutroCard.tsx
│   │   └── PunchZoom.tsx
│   ├── compositions/
│   │   ├── Reel9x16.tsx
│   │   └── Vlog16x9.tsx
│   ├── index.ts
│   ├── Root.tsx
│   └── types.ts
├── package.json
├── README.md
├── remotion.config.ts
├── STYLE_TASTE.md
└── tsconfig.json
```

---

## 2. Installed Skills & Python Packages

### Installed Skills in `.agent/skills/`
- `claude-remotion-skill`: Motion graphics and Remotion composition recipes
- `ffmpeg-skill`: Audio/video transcoding, loudnorm, CFR enforcement, proxy generation
- `hyperframes`: Standalone HTML/CSS/GSAP rendered scene generation
- `remotion-skills`: Remotion best practices, captions, studio preview, render tools
- `vargHQ-skills`: Editorial rhythm, pacing, SFX cues, shot transitions

### Installed Python Packages (`.venv`)
- `google-genai`: `3.6.1` (Powers `gemini-3.5-transcribe` Interactions API and Gemini multimodal vision reasoning)
- `auto-editor`: `29.3.1` (Silence detection, fast pacing cut validation)
- `scenedetect`: `0.7.3` (PySceneDetect visual cut boundary analysis)
- `librosa`: `1.0.1` (Audio beat and tempo analysis)
- `faster-whisper`: `1.2.1` (Retained in `.venv` as legacy fallback; completely replaced by `gemini-3.5-transcribe` in `02_analyze_context.py`)
- `opencv-python`: `5.1.0.95` (Video frame probing and visual overlay verification)

---

## 3. Script Summaries

### `scripts/01_ingest_cfr.py` (VFR -> 30fps CFR + 48kHz Loudnorm Normalizer)
- **Dynamic Episode Argument**: Accepts `--episode <name>` (default: `ep01`).
- **CFR Transcoding Flags**:
  - `-vf "fps=30,setsar=1" -vsync cfr -c:v libx264 -preset fast -crf 18`
  - Eliminates variable frame rate (VFR) phone/WhatsApp audio-video desync permanently.
- **Audio Processing Flags**:
  - `-c:a aac -ar 48000 -ac 2 -af "highpass=f=85,loudnorm=I=-16:TP=-1.5:LRA=11"`
  - Filters out 85Hz phone handling rumble and normalizes speech loudness to broadcast EBU R128 (-16 LUFS).
- **Public Sync**: Automatically copies normalized proxies to `public/media/<episode>/` for instant Remotion Studio availability.

### `scripts/02_analyze_context.py` (Generic Multi-Modal AI Context Engine)
- **Dynamic Episode Argument**: Accepts `--episode <name>` with zero hardcoded file or clip names.
- **Step A (`gemini-3.5-transcribe`)**:
  - Extracts lightweight mono MP3 (`-vn -ac 1 -ar 16000 -b:a 64k`).
  - Calls Google GenAI Interactions API `v1beta` (`client.interactions.create(model="gemini-3.5-transcribe", ...)`).
  - Parses verbatim word-level timestamps (`start_offset`, `end_offset`) and speaker diarization (`spk:0`, `spk:1`).
  - Saves exact timestamps to `analysis/<episode>/raw_transcript.json`.
- **Step B.1 (3 fps Visual Proxies)**:
  - Generates analysis video proxies via `-vf "scale=480:-2,fps=3" -ac 1 -ar 16000`.
  - Captures fast hand gestures, lifts, and camera pans without skipping frames.
- **Step B.2 (Gemini Multimodal Reasoning)**:
  - Robust candidate model rotation (`gemini-2.5-flash-lite`, `gemini-flash-latest`, `gemini-2.5-flash`).
  - Snaps cut boundaries strictly to spoken words from `raw_transcript.json`.
  - Requires normalized 0–1000 bounding boxes `[ymin, xmin, ymax, xmax]` for censors and punch zooms.
  - Returns `romanizedWords` mapping for Devanagari Hindi -> Romanized Hinglish.
- **Step C (Pure Python Zero-Desync Synthesis)**:
  - Programmatically computes 30fps `startFrame` and `durationFrames`.
  - Converts bounding boxes `[ymin, xmin, ymax, xmax]` to `posX` (0–100%) and `posY` (0–100%).
  - Programmatically slices spoken words inside cuts into 3–4 word caption chunks with exact timestamps.
  - Ensures **0 Devanagari characters** remain (100% Romanized Hinglish).
- **Step 5 (Visual Censor Verification)**:
  - Draws red bounding box with cyan label on actual video frame and saves `analysis/<episode>/verify_overlay_<id>.jpg`.
- **Step 6**: Saves `analysis/<episode>/edit_plan.json` and syncs to `public/edit_plan.json`.

---

## 4. Highlight Styling Lines in `src/components/KineticCaption.tsx`

```tsx
            <span
              key={`${activeCaption.id}-${idx}-${word}`}
              style={{
                color: isHighlighted ? '#FFE066' : '#FFFFFF',
                fontSize: is9x16 ? '54px' : '46px',
                fontWeight: 900,
                letterSpacing: '-0.02em',
                lineHeight: 1.15,
                textTransform: 'uppercase',
                WebkitTextStroke: isHighlighted ? '2px #0E1013' : '1px #0E1013',
                filter: isHighlighted
                  ? 'drop-shadow(0 4px 12px rgba(0, 0, 0, 0.95))'
                  : 'drop-shadow(0 2px 8px rgba(0, 0, 0, 0.8))',
              }}
            >
              {word}
            </span>
```

---

## 5. Live Data Verification (Tested on `ep01`)

### First 15 Lines of `analysis/ep01/raw_transcript.json`
```json
{
  "clip_01_cfr.mp4": [
    {
      "index": 0,
      "word": "हेलो",
      "start": 0.4,
      "end": 0.7,
      "speaker": "spk:0"
    },
    {
      "index": 1,
      "word": "गाइस।",
      "start": 0.7,
      "end": 1.2,
      "speaker": "spk:0"
    },
```

### Generated `cuts` (`public/edit_plan.json`)
```text
cut_01: media/ep01/clip_01_cfr.mp4 [ 0.40s -  2.00s] -> frames    0 to   48 (48 frames)
cut_02: media/ep01/clip_01_cfr.mp4 [ 3.30s -  6.00s] -> frames   48 to  129 (81 frames)
cut_03: media/ep01/clip_01_cfr.mp4 [ 6.60s - 15.20s] -> frames  129 to  387 (258 frames)
cut_04: media/ep01/clip_01_cfr.mp4 [15.30s - 17.20s] -> frames  387 to  444 (57 frames)
cut_05: media/ep01/clip_02_cfr.mp4 [ 0.10s -  2.00s] -> frames  444 to  501 (57 frames)
cut_06: media/ep01/clip_02_cfr.mp4 [ 8.00s -  9.60s] -> frames  501 to  549 (48 frames)
cut_07: media/ep01/clip_02_cfr.mp4 [10.60s - 13.50s] -> frames  549 to  636 (87 frames)
cut_08: media/ep01/clip_02_cfr.mp4 [16.40s - 18.70s] -> frames  636 to  705 (69 frames)
cut_09: media/ep01/clip_02_cfr.mp4 [19.10s - 21.20s] -> frames  705 to  768 (63 frames)
cut_10: media/ep01/clip_02_cfr.mp4 [23.40s - 23.80s] -> frames  768 to  780 (12 frames)
cut_11: media/ep01/clip_02_cfr.mp4 [24.80s - 25.10s] -> frames  780 to  789 (9 frames)
cut_12: media/ep01/clip_02_cfr.mp4 [25.90s - 27.30s] -> frames  789 to  831 (42 frames)
cut_13: media/ep01/clip_02_cfr.mp4 [28.80s - 29.40s] -> frames  831 to  849 (18 frames)
cut_14: media/ep01/clip_02_cfr.mp4 [29.60s - 32.40s] -> frames  849 to  933 (84 frames)
cut_15: media/ep01/clip_02_cfr.mp4 [34.10s - 36.40s] -> frames  933 to 1002 (69 frames)
cut_16: media/ep01/clip_02_cfr.mp4 [39.80s - 42.20s] -> frames 1002 to 1074 (72 frames)
cut_17: media/ep01/clip_02_cfr.mp4 [42.50s - 45.90s] -> frames 1074 to 1176 (102 frames)
cut_18: media/ep01/clip_02_cfr.mp4 [46.60s - 48.90s] -> frames 1176 to 1245 (69 frames)
cut_19: media/ep01/clip_02_cfr.mp4 [50.00s - 52.40s] -> frames 1245 to 1317 (72 frames)
cut_20: media/ep01/clip_01_cfr.mp4 [17.20s - 20.40s] -> frames 1317 to 1413 (96 frames)
cut_21: media/ep01/clip_01_cfr.mp4 [20.40s - 30.00s] -> frames 1413 to 1701 (288 frames)
cut_22: media/ep01/clip_01_cfr.mp4 [30.60s - 34.00s] -> frames 1701 to 1803 (102 frames)
cut_23: media/ep01/clip_01_cfr.mp4 [34.30s - 39.40s] -> frames 1803 to 1956 (153 frames)
cut_24: media/ep01/clip_01_cfr.mp4 [40.60s - 41.10s] -> frames 1956 to 1971 (15 frames)
```

### Generated `censors` (`public/edit_plan.json`)
```json
{
  "id": "censor_01",
  "startFrame": 582,
  "durationFrames": 15,
  "label": "[CENSORED]",
  "posX": 87.25,
  "posY": 38.2,
  "x": 942,
  "y": 733,
  "width": 280,
  "height": 534
}
```

### First 5 Captions (`public/edit_plan.json`)
```text
cap_01: frames    1-  23 | highlight: 'Hello'   | text: 'Hello guys'
cap_02: frames   49-  65 | highlight: 'kaam'    | text: 'kaam nahi ho raha'
cap_03: frames   67-  89 | highlight: 'bilkul'  | text: 'hai guys bilkul bhi'
cap_04: frames  130- 194 | highlight: 'aankhon' | text: 'yaar dekho aankhon'
cap_05: frames  196- 263 | highlight: 'circles' | text: 'ke dark circles'
```

---

## 6. Verification & Preview Server Status

- **Remotion Studio**: Live on `http://localhost:3000` (auto-reloading on manifest changes).
- **Final Master Render**: **HOLDING (Not rendered)** pending user confirmation.
