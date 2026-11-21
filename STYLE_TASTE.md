# Life with Shubham — Style & Editing Taste Blueprint

> **Canonical Bible**: Locked aesthetic, motion principles, caption guidelines, audio design, and prohibited clichés for all "Life with Shubham" content (9:16 Instagram Reels / YouTube Shorts & 16:9 YouTube Vlogs).

---

## 1. Tone & Brand Identity

* **Vibe**: Relatable, grounded, deadpan, observational, self-deprecating yet high agency.
* **Core Themes**: Daily developer life, startup hustle, tech office banter, Day-1 gym journey, late-night debugging reality vs expectation.
* **Language**: Natural conversational **Hinglish** (authentic Delhi-NCR/Bangalore spoken rhythm; e.g., *"Bhai yeh bug kahan se aaya"*, *"Gym chale to theek, par leg day pe death pakki"*).
* **Persona**: The unfiltered friend who codes, goes to the gym, and documents real life without fake motivational fluff.

---

## 2. Pacing, Structure & Intros

### 9:16 Vertical (Reels / Shorts)
* **0-Second Cold Open**:
  * **Zero fluff, zero logo animations, zero "Hey guys welcome back"**.
  * Clip starts at `0.00s` on the highest-energy audio peak, funniest line, or sharpest visual question.
  * First 1.5 seconds must trigger immediate curiosity or laughs.
* **Minimal Corner Badge**:
  * Top-left corner: `LIFE WITH SHUBHAM | EP XX` (Subtle pill, semi-transparent dark glass background `#0E1013` at 70% opacity, clean typography, safe from Instagram profile/header UI).
* **Rhythm & Jump Cuts**:
  * Dead air `> 0.45s` is strictly eliminated.
  * Micro-punch zooms ($1.08\times$ to $1.15\times$) on punchlines, comedic pauses, or realizations.
  * Every cut lands on natural cadence or beat transients.
* **Outro (Reels / Shorts)**:
  * Strict 1.5–2.0 second dark obsidian card (`#0E1013`) with subtle glowing accent.
  * Hook teaser: *"Next episode: Kal subah 6 AM leg day... agar utha toh."*

### 16:9 Horizontal (YouTube Vlogs)
* **Cold Open**: 10–18 second montage of the episode's most chaotic or hilarious moments.
* **Title Card**: 2–3s sleek HyperFrames / Remotion animated chapter card (`LIFE WITH SHUBHAM`).
* **Narrative Arc**: Setup $\to$ Struggle/Banter $\to$ Micro-climax $\to$ Honest reflection $\to$ Teaser outro.

---

## 3. Typography & Captions

* **Primary Font**: `DM Sans` (fallback: `Inter`, `system-ui`). Weight: Bold (700 / 800).
* **Chunk Size**: Strict **3 to 5 words** per chunk. Never display long multi-line paragraphs.
* **Color Palette**:
  * Base text: Crisp Clean White (`#FFFFFF`).
  * Punchline / Key Emphasis Word: Punchy Golden Sunflower Yellow (`#FFE066`).
  * Contrast & Readability: Solid 3px–4px subtle dark stroke/drop-shadow (`rgba(0, 0, 0, 0.85)` with blur `4px`).
* **Vertical Safe Zones**:
  * 9:16 Reels/Shorts: Centered horizontally, positioned at $y \approx 1350\text{px} - 1450\text{px}$ (upper-lower third), safely clear of Instagram's bottom caption/audio ticker and right-side action buttons (like/comment/share).
* **Animation Style**:
  * Snappy scale pop ($0.95 \to 1.0$) on word reveal using spring physics (`damping: 15, mass: 0.5`).
  * **Strictly Banned**: Neon rainbow karaoke, distracting bouncy wiggle text, TikTok emoji explosion every millisecond.

---

## 4. Visual Polish & Special Effects

* **Color Grade**:
  * Natural, rich, slightly warm skin tones.
  * Deep blacks without crushed shadow detail. Contrast ratio enhanced for mobile OLED displays.
* **Punch Zooms**:
  * Default: $1.0\times$ (full view).
  * Comedic / emphasis: $1.10\times$–$1.15\times$ instant switch or quick spring zoom on key words.
* **Censor Overlays (`CensorBar`)**:
  * Obsidian matte bar (`#0E1013`) or pixelated blur with bold text `[CENSORED]` in `#FFE066` or `#FF5555`.
  * Accompanied by classic 1kHz bleep SFX or TV glitch.
* **HyperFrames Inserts**:
  * Used for interstitial reality checks, mock code diffs, or stat trackers (e.g., *"Bugs Fixed: 0 | Chai Consumed: 4"*).

---

## 5. Audio Hierarchy & Sound Design

* **Zero Desync Discipline**: All audio must be normalized to 48,000 Hz, stereo, with standard EBU R128 loudness (`loudnorm=I=-16:TP=-1.5:LRA=11`) and high-pass filtered at 85 Hz to remove phone mic handling rumble.
* **Audio Levels**:
  * **Dialogue / Voiceover**: Primary focus, mastered to $-14$ to $-16$ LUFS. Crisp, clear, centered.
  * **Background Music**: Low-fi chill beats or subtle comedic acoustic rhythm ducked to $-18\text{dB}$ to $-24\text{dB}$ under speech; rises to $-12\text{dB}$ during montage silences.
  * **Foley & Sound Effects**: Whooshes on cuts ($-16\text{dB}$), subtle pops on caption appearances ($-20\text{dB}$), punchline rimshots/bleeps ($-10\text{dB}$).

---

## 6. Prohibited Clichés & Anti-Patterns (BANNED LIST)

1. ❌ **No "Wait for the end" or "Watch till the end" text**.
2. ❌ **No aggressive "Subscribe / Follow / Like" begging overlays**.
3. ❌ **No generic upbeat royalty-free corporate ukulele/whistle music**.
4. ❌ **No neon rainbow spinning captions** (MrBeast copycat overload).
5. ❌ **No un-normalized raw VFR phone video** directly inside Remotion (leads to drift).
6. ❌ **No robotic AI voiceovers** — authentic real human audio only.
7. ❌ **No automatic final export without local browser review** on Remotion Studio (`http://localhost:3000`).
