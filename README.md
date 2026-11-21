# 🎬 Life with Shubham Studio (`life-with-shubham-studio`)

> **Autonomous, Context-Aware, Zero-Desync AI Video Studio for 9:16 Instagram Reels / YouTube Shorts & 16:9 YouTube Vlogs.**  
> Built with **Remotion (TypeScript)**, **FFmpeg (CFR + 48kHz Normalization)**, **faster-whisper**, **librosa**, **PySceneDetect**, and **Gemini 2.5/Flash Multi-Modal AI**.

---

## 🏗️ Project Architecture

```
life-with-shubham-studio/
├── .agent/skills/                 # Installed SKILL.md files for all video skills
├── STYLE_TASTE.md                 # Locked editing taste, fonts, colors, pacing & banned clichés
├── media/
│   ├── 01_raw_videos/             # Raw phone/WhatsApp/gym/vlog clips grouped by episode (e.g., ep01/)
│   ├── 02_normalized_cfr/         # Auto-generated 30fps CFR + 48kHz loudnorm proxies (used by Remotion)
│   ├── 03_music_and_sfx/          # Background tracks, risers, whooshes, bleeps
│   └── 04_hyperframes_inserts/    # Standalone HTML/CSS/GSAP scenes rendered via HyperFrames
├── analysis/                      # Per-episode JSON manifests (transcripts, beats, Gemini EDLs)
├── public/                        # Symlink or synced assets served to Remotion Studio
│   ├── media/                     # Normalized episode proxies
│   └── edit_plan.json             # Currently active Edit Decision List (EDL)
├── src/                           # Remotion TypeScript compositions
│   ├── components/                # CornerBadge, KineticCaption, CensorBar, PunchZoom, InterstitialCard, OutroCard
│   ├── compositions/              # Reel9x16.tsx (1080x1920) & Vlog16x9.tsx (1920x1080)
│   └── Root.tsx
├── scripts/
│   ├── 01_ingest_cfr.py           # VFR -> 30fps CFR + 48kHz highpass/loudnorm normalizer
│   ├── 02_analyze_context.py      # faster-whisper + librosa + PySceneDetect + Gemini API -> edit_plan.json
│   └── 03_render_final.py         # Exports final MP4 to output/final_videos/
└── output/
    ├── previews/                  # Optional quick draft exports
    └── final_videos/              # Final mastered MP4s ready to post
```

---

## ⚡ Quick Start: How to Edit a New Episode

### Step 1: Drop Raw Videos
Create a folder for the episode inside `media/01_raw_videos/` (e.g. `media/01_raw_videos/ep01/`) and drop all raw phone recordings, WhatsApp clips, gym sets, or screen recordings.

```bash
# Example:
media/01_raw_videos/ep01/
  clip_01.mp4
  clip_02.mp4
```

### Step 2: Ingest & Eliminate Variable Frame Rate (VFR) Desync
Phones (especially iPhones and Android WhatsApp exports) record in Variable Frame Rate, which causes Remotion's frame-based timeline to drift out of sync with audio.
Run the CFR normalizer:
```bash
.\.venv\Scripts\python.exe scripts/01_ingest_cfr.py --episode ep01
```
This converts every clip into strict 30fps CFR, sets SAR=1, normalizes audio to 48kHz stereo with EBU R128 loudness (`loudnorm`), applies an 85Hz highpass filter to cut mic rumble, and syncs the files to `public/media/ep01/`.

### Step 3: Run Multi-Modal AI Context Analysis
Analyze the normalized footage for speech timestamps, dead air silences, scene cuts, musical beats, and Gemini-powered comedic hook detection:
```bash
.\.venv\Scripts\python.exe scripts/02_analyze_context.py --episode ep01
```
This generates `analysis/ep01/edit_plan.json` and updates `public/edit_plan.json` for live loading in Remotion Studio.

### Step 4: Preview Live in Browser (Mandatory Iteration Step)
Launch the Remotion Studio preview server:
```bash
npx remotion studio
```
Open **`http://localhost:3000`** in your browser.
- Switch between **`Reel9x16`** (1080×1920) and **`Vlog16x9`** (1920×1080).
- Scrub the timeline with frame accuracy.
- Watch captions, punch zooms, censor bars, and outro cards in real time with Hot Module Replacement (HMR).

### Step 5: Render Final MP4
When you are completely satisfied with the preview:
```bash
.\.venv\Scripts\python.exe scripts/03_render_final.py --episode ep01 --composition Reel9x16
```
The final mastered video will be saved to `output/final_videos/ep01_Reel9x16.mp4`.

---

## 🎨 Editing Taste & Rules (`STYLE_TASTE.md`)
* **0-Second Cold Open**: Reels start immediately on the best hook. No intro logos.
* **Minimal Corner Badge**: Subtle top-left episode pill (`LIFE WITH SHUBHAM | EP XX`).
* **Hinglish Captions**: 3–5 words per chunk, bold `DM Sans`, clean white text with `#FFE066` punchline highlight.
* **Obsidian Outro Card**: 2-second dark obsidian (`#0E1013`) teaser card for next episode.
* See [STYLE_TASTE.md](file:///D:/Content-Creation-Studio/STYLE_TASTE.md) for full guidelines.
