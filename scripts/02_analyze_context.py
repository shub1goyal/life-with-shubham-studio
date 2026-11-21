#!/usr/bin/env python3
"""
scripts/02_analyze_context.py
=============================
Multi-Modal AI Context Engine for Life with Shubham Studio.

Upgrades:
1. Universal & Generic: Works on any episode (--episode <name>) with no hardcoded clip names.
2. Step A: Transcribe via gemini-3.5-transcribe (Interactions API v1beta).
   - Extracts lightweight mono MP3 audio proxy via FFmpeg (-vn -ac 1 -ar 16000 -b:a 64k).
   - Uploads to Gemini File API and calls client.interactions.create with verbatim word-level timestamps & speaker diarization.
   - Saves exact {index, word, start, end, speaker} to analysis/<episode>/raw_transcript.json.
   - Hard exit (sys.exit(1)) on failure—zero dummy/mock fallback.
3. Step B: Generate 3 fps analysis proxies via FFmpeg (-vf 'scale=480:-2,fps=3' -ac 1 -ar 16000).
   - Uploads proxies to Gemini 2.5 Flash with the raw transcript.
   - Asks Gemini for cuts snapped to transcript words, censors with [ymin, xmin, ymax, xmax] 0-1000 bounding boxes,
     punchZooms with focal point / bounding boxes, outro teaser, and romanizedWords mapping.
4. Step C (PURE PYTHON):
   - Replaces any Devanagari script words with clean Romanized Hinglish while preserving 100% of the exact timestamps.
   - Programmatically computes startFrame/durationFrames at 30fps.
   - Converts bounding boxes to posX/posY (0-100%).
   - Slices real words into 3-4 word synchronized captions chunks with high-contrast highlightWord.
5. Step 5: Visual verification of censor overlays (analysis/<episode>/verify_overlay_<id>.jpg).
6. Step 6: Writes analysis/<episode>/edit_plan.json and syncs to public/edit_plan.json.
"""

import os
import re
import sys
import json
import time
import shutil
import argparse
import subprocess
from pathlib import Path
from dotenv import load_dotenv

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


# Devanagari transliteration fallback dictionary for Hindi consonants & vowels
DEVANAGARI_MAP = {
    'क': 'k', 'ख': 'kh', 'ग': 'g', 'घ': 'gh', 'ङ': 'ng',
    'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'ny',
    'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n',
    'त': 't', 'थ': 'th', 'द': 'd', 'ध': 'dh', 'न': 'n',
    'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh', 'म': 'm',
    'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v', 'श': 'sh',
    'ष': 'sh', 'स': 's', 'ह': 'h',
    'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ee', 'उ': 'u',
    'ऊ': 'oo', 'ऋ': 'ri', 'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au',
    'ा': 'a', 'ि': 'i', 'ी': 'ee', 'ु': 'u', 'ू': 'oo',
    'ृ': 'ri', 'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au',
    'ं': 'n', 'ँ': 'n', 'ः': 'h', '्': '', '़': '', '।': '.', '॥': '.'
}


def transliterate_devanagari_fallback(text: str) -> str:
    """Fallback transliterator ensuring zero Devanagari characters remain in captions."""
    res = []
    i = 0
    consonants = 'कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसह'
    vowels = 'ािीुूृेैोौ'
    while i < len(text):
        ch = text[i]
        if ch in DEVANAGARI_MAP:
            if ch in consonants:
                next_ch = text[i+1] if i + 1 < len(text) else ''
                if next_ch == '्':
                    res.append(DEVANAGARI_MAP[ch])
                    i += 2
                    continue
                elif next_ch in vowels:
                    res.append(DEVANAGARI_MAP[ch] + DEVANAGARI_MAP[next_ch])
                    i += 2
                    continue
                else:
                    res.append(DEVANAGARI_MAP[ch] + ('a' if i + 1 < len(text) and text[i+1] not in ' ।!?,.' else ''))
            else:
                res.append(DEVANAGARI_MAP[ch])
        else:
            res.append(ch)
        i += 1
    return "".join(res)


def probe_clip_duration(file_path: Path) -> float:
    """Accurately probe video duration using OpenCV or FFmpeg."""
    if CV2_AVAILABLE:
        try:
            cap = cv2.VideoCapture(str(file_path))
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
            cap.release()
            if fps > 0 and frame_count > 0:
                return float(frame_count / fps)
        except Exception:
            pass
    try:
        res = subprocess.run(
            f'ffmpeg -i "{file_path}" -hide_banner',
            shell=True,
            capture_output=True,
            text=True
        )
        match = re.search(r"Duration:\s*(\d{2}):(\d{2}):(\d{2}\.\d+)", res.stderr)
        if match:
            h, m, s = match.groups()
            return int(h) * 3600 + int(m) * 60 + float(s)
    except Exception:
        pass
    return 30.0


def step_a_transcribe(clips: list, analysis_dir: Path, client) -> dict:
    """
    Step A: Transcribe via gemini-3.5-transcribe (Interactions API v1beta).
    - Extracts lightweight mono MP3 audio file with FFmpeg (-vn -ac 1 -ar 16000 -b:a 64k).
    - Uploads MP3 to Gemini File API.
    - Calls client.interactions.create(
          model="gemini-3.5-transcribe",
          input=[{"type": "audio", "uri": f.uri, "mime_type": f.mime_type or "audio/mpeg"}],
          generation_config={
              "transcription_config": {
                  "language_codes": [],
                  "mode": {
                      "type": "verbatim",
                      "diarization_mode": "speaker",
                      "timestamp_granularities": ["word"]
                  }
              }
          }
      )
    - IMPORTANT API RULES: Never set mode: "smart" and never pass custom_vocabulary
      alongside timestamp_granularities or diarization_mode (causes HTTP 400).
    - Parses word_info annotations (text, start_offset, end_offset, speaker), converts
      offsets to float seconds, and saves to analysis/<episode>/raw_transcript.json.
    """
    print("\n" + "=" * 60, flush=True)
    print("🎙️  STEP A: gemini-3.5-transcribe Speech Transcription (Interactions API)", flush=True)
    print("=" * 60, flush=True)

    transcript_path = analysis_dir / "raw_transcript.json"
    if transcript_path.exists() and transcript_path.stat().st_size > 10:
        try:
            with open(transcript_path, "r", encoding="utf-8") as f:
                cached = json.load(f)
            if all(c.name in cached and len(cached[c.name]) > 0 for c in clips):
                print(f"[+] Found existing valid raw_transcript.json from gemini-3.5-transcribe ({len(cached)} clips). Using it.", flush=True)
                return cached
        except Exception:
            pass

    audio_dir = analysis_dir / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    raw_transcript = {}

    for clip in clips:
        clip_name = clip.name
        mp3_path = audio_dir / f"{clip.stem}.mp3"

        print(f"[*] Extracting mono MP3 for {clip_name} -> {mp3_path.name}...", flush=True)
        cmd = [
            "ffmpeg", "-y",
            "-i", str(clip),
            "-vn",
            "-ac", "1",
            "-ar", "16000",
            "-b:a", "64k",
            str(mp3_path)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print(f"[!] Warning: FFmpeg audio extraction error for {clip_name}: {res.stderr[:200]}", flush=True)
            cmd_basic = f'ffmpeg -y -i "{clip}" -vn -ac 1 -ar 16000 -b:a 64k "{mp3_path}"'
            subprocess.run(cmd_basic, shell=True, check=True)

        size_kb = mp3_path.stat().st_size / 1024
        print(f"    [+] Created audio proxy: {mp3_path.name} ({size_kb:.1f} KB)", flush=True)

        print(f"[*] Uploading {mp3_path.name} to Gemini File API...", flush=True)
        f_audio = client.files.upload(file=str(mp3_path))
        while f_audio.state.name == "PROCESSING":
            time.sleep(1.0)
            f_audio = client.files.get(name=f_audio.name)
        mime_type = f_audio.mime_type or "audio/mpeg"
        print(f"    [+] Uploaded {f_audio.name} ({f_audio.state.name}, mime: {mime_type})", flush=True)

        print(f"[*] Calling gemini-3.5-transcribe (Interactions API v1beta)...", flush=True)
        t_trans = time.time()
        try:
            resp = client.interactions.create(
                model="gemini-3.5-transcribe",
                input=[{"type": "audio", "uri": f_audio.uri, "mime_type": mime_type}],
                generation_config={
                    "transcription_config": {
                        "language_codes": [],
                        "mode": {
                            "type": "verbatim",
                            "diarization_mode": "speaker",
                            "timestamp_granularities": ["word"]
                        }
                    }
                }
            )
            print(f"    [+] Transcription received in {time.time() - t_trans:.1f}s", flush=True)
        except Exception as e:
            print(f"[FATAL] gemini-3.5-transcribe failed on {clip_name}: {e}", file=sys.stderr, flush=True)
            sys.exit(1)

        clip_words = []
        w_idx = 0
        for step in getattr(resp, "steps", []):
            for content in getattr(step, "content", []):
                for ann in getattr(content, "annotations", []):
                    if getattr(ann, "type", None) == "word_info" or hasattr(ann, "start_offset"):
                        w_text = str(getattr(ann, "text", "")).strip()
                        if not w_text:
                            continue
                        start_raw = getattr(ann, "start_offset", "0s")
                        end_raw = getattr(ann, "end_offset", "0s")
                        start_s = float(str(start_raw).rstrip("s"))
                        end_s = float(str(end_raw).rstrip("s"))
                        speaker = getattr(ann, "speaker", "spk:0")
                        clip_words.append({
                            "index": w_idx,
                            "word": w_text,
                            "start": round(start_s, 3),
                            "end": round(end_s, 3),
                            "speaker": speaker
                        })
                        w_idx += 1

        if not clip_words:
            print(f"[FATAL] gemini-3.5-transcribe produced 0 words for {clip_name}. Aborting.", file=sys.stderr, flush=True)
            sys.exit(1)

        raw_transcript[clip_name] = clip_words
        print(f"    [+] {clip_name}: {len(clip_words)} words parsed with exact timestamps & speaker tags", flush=True)

    # Save to analysis/<episode>/raw_transcript.json
    transcript_path = analysis_dir / "raw_transcript.json"
    with open(transcript_path, "w", encoding="utf-8") as f:
        json.dump(raw_transcript, f, indent=2, ensure_ascii=False)

    print(f"[+] Saved raw transcript: {transcript_path}", flush=True)
    return raw_transcript


def step_b_generate_proxies(clips: list, proxies_dir: Path) -> list:
    """
    Step B.1: Generate 3 fps analysis proxies via FFmpeg:
    -vf 'scale=480:-2,fps=3' -ac 1 -ar 16000
    """
    print("\n" + "=" * 60, flush=True)
    print("🎞️  STEP B.1: Generate 3 fps Analysis Proxies via FFmpeg", flush=True)
    print("=" * 60, flush=True)

    proxies_dir.mkdir(parents=True, exist_ok=True)
    proxy_paths = []

    for clip in clips:
        proxy_path = proxies_dir / f"{clip.stem}_proxy.mp4"
        proxy_paths.append(proxy_path)

        if proxy_path.exists() and proxy_path.stat().st_size > 1024:
            size_mb = proxy_path.stat().st_size / (1024 * 1024)
            print(f"    [+] Using existing proxy: {proxy_path.name} ({size_mb:.2f} MB)", flush=True)
            continue

        print(f"[*] Generating proxy for {clip.name} -> {proxy_path.name}...", flush=True)
        cmd = [
            "ffmpeg", "-y",
            "-i", str(clip),
            "-vf", "scale=480:-2,fps=3",
            "-ac", "1",
            "-ar", "16000",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "28",
            "-c:a", "aac",
            str(proxy_path)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            print(f"[!] Warning: FFmpeg proxy generation error for {clip.name}: {res.stderr[:200]}", flush=True)
            cmd_basic = f'ffmpeg -y -i "{clip}" -vf "scale=480:-2,fps=3" -ac 1 -ar 16000 "{proxy_path}"'
            subprocess.run(cmd_basic, shell=True, check=True)

        size_mb = proxy_path.stat().st_size / (1024 * 1024)
        print(f"    [+] Created proxy: {proxy_path.name} ({size_mb:.2f} MB)", flush=True)

    return proxy_paths


def step_b_query_gemini(proxy_paths: list, transcript_path: Path, episode: str, clips: list, client) -> dict:
    """
    Step B.2: Upload 3 fps proxies + raw transcript text to Gemini 2.5 Flash.
    Instruct Gemini to:
    1. Select cuts snapped strictly to real spoken words from raw_transcript.json.
    2. Identify censors with normalized [ymin, xmin, ymax, xmax] 0-1000 bounding boxes.
    3. Identify punchZooms with focal point or bounding box.
    4. Provide romanizedWords mapping (index -> Romanized Hinglish word) for any Devanagari words.
    5. Provide outroTeaser.
    """
    print("\n" + "=" * 60, flush=True)
    print("🤖 STEP B.2: Gemini Multimodal Reasoning Engine (Gemini 2.5 Flash)", flush=True)
    print("=" * 60, flush=True)

    uploaded_files = []
    for proxy in proxy_paths:
        print(f"[*] Uploading proxy {proxy.name} to Gemini File API...", flush=True)
        f = client.files.upload(file=str(proxy))
        while f.state.name == "PROCESSING":
            time.sleep(1.0)
            f = client.files.get(name=f.name)
        print(f"    [+] {proxy.name} ready ({f.state.name}: {f.name})", flush=True)
        uploaded_files.append(f)

    # Read transcript text directly to pass in the prompt
    transcript_text = transcript_path.read_text(encoding="utf-8")
    clip_names = [c.name for c in clips]

    prompt = f"""
You are the lead viral short-form video editor for 'Life with Shubham', a deadpan, relatable Hinglish mini-vlog and creator series (covering gym, travel, office, masti, and educational creator content).
Analyze the attached 3 fps video proxies and the following verbatim word-level transcript for episode: '{episode}'.
Source Clips available: {clip_names}

RAW TRANSCRIPT DATA (from gemini-3.5-transcribe):
{transcript_text}

TASK: Synthesize a viral, punchy 30-45 second 9:16 vertical Reel edit plan from these clips.

REQUIREMENTS:
1. CUTS:
   - Zero fluff, 0-second cold-open hook: Start immediately with the most engaging spoken line, relatable reaction, or visual surprise from the transcript and video.
   - Eliminate dead air, awkward pauses, and silent delays (> 0.25s).
   - Maintain high narrative momentum: Build an engaging story arc (Hook -> Setup -> Escalation/Action/Masti -> Punchline/Climax -> Relatable Outro).
   - Snap cut start and end timestamps strictly to real spoken words from raw_transcript.json or exact visual motion boundaries.
   - Total Reel duration must be between 30 and 45 seconds.
   - For each cut, specify:
     "sourceClip": exact filename from {clip_names},
     "sourceStartSec": float seconds in source clip,
     "sourceEndSec": float seconds in source clip,
     "description": brief note describing the moment.

2. CENSORS:
   - Visually scan the video proxies for any unbroadcastable gestures (e.g., middle finger gestures), private information, or graphic content that must be censored.
   - For every such moment, specify:
     "sourceClip": filename where the gesture occurs,
     "sourceStartSec": exact start timestamp in seconds,
     "sourceEndSec": exact end timestamp in seconds,
     "box_2d": [ymin, xmin, ymax, xmax] as normalized integers 0-1000 tightly enclosing the gesture/object (where 0,0 is top-left, 1000,1000 is bottom-right),
     "label": "[CENSORED]"

3. PUNCH ZOOMS:
   - Identify deadpan punchlines, comedic pauses, unexpected realizations, or key focal moments to emphasize with 1.12x-1.20x punch zoom.
   - For each punch zoom, specify:
     "sourceClip": filename,
     "sourceStartSec": float seconds,
     "sourceEndSec": float seconds,
     "scale": float (between 1.12 and 1.20),
     "box_2d": [ymin, xmin, ymax, xmax] (0-1000 scale) bounding box or focal point for the subject/face

4. ROMANIZATION (CRITICAL FOR HINGLISH REELS):
   - If any words in RAW TRANSCRIPT DATA are in Devanagari Hindi script, provide a dictionary 'romanizedWords' mapping the clip filename and word index to its natural, punchy Romanized Hinglish spelling (e.g. "काम" -> "kaam", "नहीं" -> "nahi", "पीएफ" -> "PF", "गाइस" -> "guys", "यार" -> "yaar", "देखो" -> "dekho", "चल" -> "chal", "रहा" -> "raha", "है" -> "hai"):
     "romanizedWords": {{
       "{clip_names[0]}": {{
         "0": "Hello",
         "1": "guys",
         "2": "kaam",
         "3": "nahi",
         "4": "ho",
         "5": "raha",
         "6": "hai"
       }}
     }}
   - Python will use this mapping to replace the Devanagari text in the captions while strictly preserving 100% of the word's original start and end timestamps.

5. OUTRO TEASER:
   - A witty 1-liner hook teasing the next episode or concluding the theme.

Output strictly valid JSON with this schema:
{{
  "episodeTitle": "Creative Title Based On Footage",
  "cuts": [
    {{
      "sourceClip": "{clip_names[0]}",
      "sourceStartSec": 0.0,
      "sourceEndSec": 3.0,
      "description": "Cold open hook"
    }}
  ],
  "censors": [
    {{
      "sourceClip": "{clip_names[-1]}",
      "sourceStartSec": 3.2,
      "sourceEndSec": 5.0,
      "box_2d": [420, 380, 580, 560],
      "label": "[CENSORED]",
      "reason": "Unbroadcastable gesture"
    }}
  ],
  "punchZooms": [
    {{
      "sourceClip": "{clip_names[0]}",
      "sourceStartSec": 10.0,
      "sourceEndSec": 12.5,
      "scale": 1.15,
      "box_2d": [180, 320, 520, 680]
    }}
  ],
  "romanizedWords": {{
    "{clip_names[0]}": {{
      "0": "Hello",
      "1": "guys"
    }}
  }},
  "outroTeaser": "Next episode teaser line..."
}}
"""

    print("[*] Querying Gemini for Multimodal Decision Making...", flush=True)
    t_gen = time.time()
    candidate_models = ["gemini-2.5-flash-lite", "gemini-flash-latest", "gemini-2.5-flash"]
    data = None
    last_err = None

    for model_name in candidate_models:
        for attempt in range(1, 3):
            try:
                print(f"[*] Calling {model_name} (attempt {attempt}/2)...", flush=True)
                res = client.models.generate_content(
                    model=model_name,
                    contents=uploaded_files + [prompt],
                    config={"response_mime_type": "application/json"}
                )
                print(f"[+] Gemini ({model_name}) response received in {time.time() - t_gen:.1f}s", flush=True)
                raw_text = res.text.strip()
                if raw_text.startswith("```"):
                    raw_text = re.sub(r"^```(?:json)?\n?", "", raw_text)
                    raw_text = re.sub(r"\n?```$", "", raw_text)
                data = json.loads(raw_text)
                if data and data.get("cuts"):
                    return data
            except Exception as e:
                last_err = e
                print(f"[!] {model_name} attempt {attempt} failed: {e}", file=sys.stderr, flush=True)
                time.sleep(2.0 * attempt)
        print(f"[!] Moving to next model fallback after errors on {model_name}...", flush=True)

    print(f"[!] All Gemini candidate models failed: {last_err}", file=sys.stderr, flush=True)
    return None


def resolve_clip(clip_identifier, clips, clip_map, clip_stem_map):
    """Safely map any clip identifier (filename, stem, index, partial path) to a Path object."""
    if isinstance(clip_identifier, int) and 0 <= clip_identifier < len(clips):
        return clips[clip_identifier]
    if isinstance(clip_identifier, str):
        p = Path(clip_identifier)
        if p.name in clip_map:
            return clip_map[p.name]
        if p.stem in clip_stem_map:
            return clip_stem_map[p.stem]
        clean_stem = p.stem.replace("_cfr", "").replace("_proxy", "")
        if clean_stem in clip_stem_map:
            return clip_stem_map[clean_stem]
    return clips[0] if clips else None


def step_c_build_edit_plan(
    gemini_data: dict,
    raw_transcript: dict,
    clips: list,
    episode: str,
    fps: int = 30
) -> tuple:
    """
    Step C (PURE PYTHON):
    - Replaces Devanagari script words with clean Romanized Hinglish from Gemini's romanizedWords
      mapping, keeping 100% of the exact timestamps.
    - Programmatically computes startFrame/durationFrames at 30fps.
    - Converts bounding boxes to posX/posY (0-100%).
    - Slices real words into 3-4 word synchronized captions chunks with high-contrast highlightWord.
    """
    print("\n" + "=" * 60, flush=True)
    print("📐 STEP C: Pure Python Zero-Desync Timeline & EDL Synthesis", flush=True)
    print("=" * 60, flush=True)

    # -------------------------------------------------------------
    # Romanize Devanagari words to clean Hinglish using Gemini's mapping + fallback
    # -------------------------------------------------------------
    romanized_map = gemini_data.get("romanizedWords", {})
    for clip_name, words in raw_transcript.items():
        clip_roman = romanized_map.get(clip_name, {})
        for w in words:
            idx_str = str(w.get("index", 0))
            rep = clip_roman.get(idx_str) or romanized_map.get(f"{clip_name}_{idx_str}")
            if not rep and idx_str in romanized_map and isinstance(romanized_map[idx_str], str):
                rep = romanized_map[idx_str]
            orig_word = w["word"].strip().strip("।,!?.")
            if not rep and orig_word in clip_roman:
                rep = clip_roman[orig_word]
            if not rep and orig_word in romanized_map and isinstance(romanized_map[orig_word], str):
                rep = romanized_map[orig_word]
            if rep:
                w["word"] = str(rep).strip()
            # If any Devanagari character remains, apply transliteration fallback
            if any('\u0900' <= ch <= '\u097F' for ch in w["word"]):
                w["word"] = transliterate_devanagari_fallback(w["word"])

    # Build clip lookup mappings
    clip_map = {c.name: c for c in clips}
    clip_stem_map = {}
    for c in clips:
        clip_stem_map[c.stem] = c
        clip_stem_map[c.stem.replace("_cfr", "")] = c
        clip_stem_map[c.stem.replace("_proxy", "")] = c

    clip_durations = {c.name: probe_clip_duration(c) for c in clips}

    raw_cuts = gemini_data.get("cuts", [])
    if not raw_cuts:
        raise ValueError("No cuts found in Gemini response!")

    timeline_cuts = []
    current_frame = 0

    for idx, c in enumerate(raw_cuts):
        clip_id = c.get("sourceClip") or c.get("sourceFile") or c.get("sourceClipIndex")
        src_file = resolve_clip(clip_id, clips, clip_map, clip_stem_map) or clips[0]

        clip_dur = clip_durations.get(src_file.name, 30.0)
        start_sec = max(0.0, float(c.get("sourceStartSec", 0.0)))
        end_sec = min(clip_dur, max(start_sec + 0.3, float(c.get("sourceEndSec", start_sec + 2.5))))
        dur_sec = end_sec - start_sec
        dur_frames = int(round(dur_sec * fps))

        cut_id = f"cut_{idx+1:02d}"
        public_rel = f"media/{episode}/{src_file.name}"

        cut_entry = {
            "id": cut_id,
            "sourceFile": public_rel,
            "sourceClipName": src_file.name,
            "sourceStartSec": round(start_sec, 2),
            "sourceEndSec": round(end_sec, 2),
            "startFrame": current_frame,
            "durationFrames": dur_frames,
            "volume": 1.0
        }
        timeline_cuts.append(cut_entry)
        current_frame += dur_frames

    print(f"[+] Computed {len(timeline_cuts)} timeline cuts ({current_frame} frames, {current_frame/fps:.2f}s)", flush=True)

    # -------------------------------------------------------------
    # Auto-build captions by slicing real transcript words into 3-4 word chunks
    # -------------------------------------------------------------
    print("[*] Slicing real transcript words into 3-4 word synchronized caption chunks...", flush=True)
    captions = []
    cap_id_counter = 1

    stop_words = {
        "hai", "ho", "ka", "ke", "ki", "ko", "se", "me", "mein", "par", "to",
        "bhi", "tha", "thi", "the", "a", "an", "the", "is", "in", "it", "to",
        "for", "of", "and", "or", "aur", "ya", "yeh", "woh", "jo", "hum", "tum",
        "meri", "mera", "mere", "apna", "apne", "apni", "kya", "kyun", "kab"
    }

    for cut in timeline_cuts:
        clip_name = cut["sourceClipName"]
        clip_words = raw_transcript.get(clip_name, [])

        cut_start = cut["sourceStartSec"]
        cut_end = cut["sourceEndSec"]

        # Filter words overlapping this cut
        cut_matched_words = [
            w for w in clip_words
            if (cut_start - 0.15) <= ((w["start"] + w["end"]) / 2.0) <= (cut_end + 0.15)
        ]

        if not cut_matched_words:
            continue

        # Slice matched words into chunks of 3 to 4 words
        i = 0
        while i < len(cut_matched_words):
            remaining = len(cut_matched_words) - i
            if remaining == 5:
                chunk_size = 3
            elif remaining == 4:
                chunk_size = 4
            elif remaining <= 3:
                chunk_size = remaining
            else:
                chunk_size = 3 if (remaining % 3 == 0 or remaining % 4 != 0) else 4

            chunk = cut_matched_words[i : i + chunk_size]
            i += chunk_size

            chunk_text = " ".join(w["word"] for w in chunk).strip()
            if not chunk_text:
                continue

            w_start = chunk[0]["start"]
            w_end = chunk[-1]["end"]

            rel_start_sec = max(0.0, w_start - cut_start)
            rel_end_sec = max(rel_start_sec + 0.2, min(cut_end - cut_start, w_end - cut_start))

            start_f = cut["startFrame"] + int(round(rel_start_sec * fps)) + 1
            end_f = max(start_f + 8, cut["startFrame"] + int(round(rel_end_sec * fps)) - 1)

            # Clamp inside cut boundary
            start_f = max(cut["startFrame"], start_f)
            end_f = min(cut["startFrame"] + cut["durationFrames"], end_f)

            # Determine highlightWord
            clean_words = [re.sub(r"[^\w]", "", w["word"]) for w in chunk]
            non_stop = [w for w in clean_words if w.lower() not in stop_words and len(w) > 2]
            if non_stop:
                highlight = max(non_stop, key=len)
            else:
                highlight = clean_words[-1] if clean_words else chunk_text.split()[-1]

            captions.append({
                "id": f"cap_{cap_id_counter:02d}",
                "text": chunk_text,
                "startFrame": start_f,
                "endFrame": end_f,
                "highlightWord": highlight,
                "words": [
                    {
                        "word": w["word"],
                        "start": round(w["start"], 3),
                        "end": round(w["end"], 3)
                    }
                    for w in chunk
                ]
            })
            cap_id_counter += 1

    print(f"[+] Synthesized {len(captions)} synchronized Hinglish kinetic caption chunks", flush=True)

    # -------------------------------------------------------------
    # Compute Censors & Convert Bounding Boxes to posX/posY (0-100%)
    # -------------------------------------------------------------
    print("[*] Processing censors and converting bounding boxes to posX/posY (0-100%)...", flush=True)
    raw_censors = gemini_data.get("censors", [])
    timeline_censors = []

    for idx, c in enumerate(raw_censors):
        clip_id = c.get("sourceClip") or c.get("sourceFile") or c.get("sourceClipIndex")
        c_src_file = resolve_clip(clip_id, clips, clip_map, clip_stem_map) or (clips[-1] if clips else None)
        c_start_sec = float(c.get("sourceStartSec", 0.0))
        c_end_sec = float(c.get("sourceEndSec", c_start_sec + 2.0))

        # Find matching cut
        matched_cut = None
        for cut in timeline_cuts:
            if c_src_file and cut["sourceClipName"] == c_src_file.name:
                if not (c_end_sec <= cut["sourceStartSec"] or c_start_sec >= cut["sourceEndSec"]):
                    matched_cut = cut
                    break

        if not matched_cut:
            for cut in timeline_cuts:
                if c_src_file and cut["sourceClipName"] == c_src_file.name:
                    matched_cut = cut
                    c_start_sec = max(cut["sourceStartSec"], c_start_sec)
                    c_end_sec = min(cut["sourceEndSec"], max(c_start_sec + 1.0, c_end_sec))
                    break

        if not matched_cut:
            continue

        rel_start = max(0.0, c_start_sec - matched_cut["sourceStartSec"])
        rel_end = min(matched_cut["sourceEndSec"] - matched_cut["sourceStartSec"], c_end_sec - matched_cut["sourceStartSec"])
        dur_sec = max(0.5, rel_end - rel_start)

        start_f = matched_cut["startFrame"] + int(round(rel_start * fps))
        dur_f = max(15, int(round(dur_sec * fps)))

        # Parse bounding box [ymin, xmin, ymax, xmax] (0-1000 scale)
        bbox = c.get("box_2d", [380, 380, 620, 620])
        if isinstance(bbox, dict):
            ymin = float(bbox.get("ymin", 380))
            xmin = float(bbox.get("xmin", 380))
            ymax = float(bbox.get("ymax", 620))
            xmax = float(bbox.get("xmax", 620))
        elif isinstance(bbox, (list, tuple)) and len(bbox) == 4:
            ymin, xmin, ymax, xmax = [float(v) for v in bbox]
        else:
            ymin, xmin, ymax, xmax = 380.0, 380.0, 620.0, 620.0

        # Convert to center posX / posY in percent (0-100%)
        centerX_pct = round(((xmin + xmax) / 2.0) / 10.0, 2)
        centerY_pct = round(((ymin + ymax) / 2.0) / 10.0, 2)

        # Scale for 1080x1920 Reel composition
        x_px = int(round(centerX_pct / 100.0 * 1080))
        y_px = int(round(centerY_pct / 100.0 * 1920))
        width_px = max(280, int(round(((xmax - xmin) / 1000.0) * 1080 * 1.25)))
        height_px = max(75, int(round(((ymax - ymin) / 1000.0) * 1920 * 1.15)))

        censor_id = f"censor_{idx+1:02d}"
        censor_entry = {
            "id": censor_id,
            "startFrame": start_f,
            "durationFrames": dur_f,
            "label": c.get("label", "[CENSORED]"),
            "posX": centerX_pct,
            "posY": centerY_pct,
            "x": x_px,
            "y": y_px,
            "width": width_px,
            "height": height_px,
            "_sourceClipPath": str(c_src_file) if c_src_file else "",
            "_sampleSec": (c_start_sec + c_end_sec) / 2.0,
            "_bbox": [ymin, xmin, ymax, xmax]
        }
        timeline_censors.append(censor_entry)

    print(f"[+] Placed {len(timeline_censors)} unbroadcastable gesture censors with exact posX/posY coordinates", flush=True)

    # -------------------------------------------------------------
    # Compute Punch Zooms
    # -------------------------------------------------------------
    print("[*] Processing comedic punch zooms...", flush=True)
    raw_zooms = gemini_data.get("punchZooms", [])
    timeline_zooms = []

    for idx, z in enumerate(raw_zooms):
        clip_id = z.get("sourceClip") or z.get("sourceFile") or z.get("sourceClipIndex")
        z_src_file = resolve_clip(clip_id, clips, clip_map, clip_stem_map) or (clips[0] if clips else None)
        z_start_sec = float(z.get("sourceStartSec", 0.0))
        z_end_sec = float(z.get("sourceEndSec", z_start_sec + 2.0))

        matched_cut = None
        for cut in timeline_cuts:
            if z_src_file and cut["sourceClipName"] == z_src_file.name:
                if not (z_end_sec <= cut["sourceStartSec"] or z_start_sec >= cut["sourceEndSec"]):
                    matched_cut = cut
                    break

        if not matched_cut:
            continue

        rel_start = max(0.0, z_start_sec - matched_cut["sourceStartSec"])
        rel_end = min(matched_cut["sourceEndSec"] - matched_cut["sourceStartSec"], z_end_sec - matched_cut["sourceStartSec"])
        dur_sec = max(0.5, rel_end - rel_start)

        start_f = matched_cut["startFrame"] + int(round(rel_start * fps))
        dur_f = max(15, int(round(dur_sec * fps)))

        scale = float(z.get("scale", 1.15))
        scale = max(1.08, min(1.25, scale))

        originX = 50.0
        originY = 45.0
        if "box_2d" in z and isinstance(z["box_2d"], (list, tuple)) and len(z["box_2d"]) == 4:
            b = [float(v) for v in z["box_2d"]]
            originX = round(((b[1] + b[3]) / 2.0) / 10.0, 1)
            originY = round(((b[0] + b[2]) / 2.0) / 10.0, 1)
        elif "focalPoint" in z and isinstance(z["focalPoint"], (list, tuple)) and len(z["focalPoint"]) == 2:
            fy, fx = [float(v) for v in z["focalPoint"]]
            originY = round(fy / 10.0 if fy > 1.0 else fy * 100.0, 1)
            originX = round(fx / 10.0 if fx > 1.0 else fx * 100.0, 1)

        timeline_zooms.append({
            "id": f"zoom_{idx+1:02d}",
            "startFrame": start_f,
            "durationFrames": dur_f,
            "scale": scale,
            "originX": originX,
            "originY": originY
        })

    print(f"[+] Placed {len(timeline_zooms)} comedic punch zooms", flush=True)

    # -------------------------------------------------------------
    # 2-Second Obsidian Outro Card (#0E1013)
    # -------------------------------------------------------------
    outro_frames = 60
    outro_teaser = gemini_data.get("outroTeaser", f"Next episode coming soon... Stay tuned.")
    outro = {
        "startFrame": current_frame,
        "durationFrames": outro_frames,
        "teaserText": outro_teaser,
        "episodeNumber": episode.upper()
    }

    total_frames = current_frame + outro_frames
    duration_sec = round(total_frames / fps, 2)

    # Clean internal keys
    clean_cuts = [
        {k: v for k, v in cut.items() if not k.startswith("_") and k != "sourceClipName"}
        for cut in timeline_cuts
    ]
    clean_censors = [
        {k: v for k, v in c.items() if not k.startswith("_")}
        for c in timeline_censors
    ]

    title = gemini_data.get("episodeTitle", f"Episode {episode.upper()}")
    manifest = {
        "episodeId": episode.upper(),
        "title": f"LIFE WITH SHUBHAM | {episode.upper()} - {title}",
        "fps": fps,
        "totalFrames": total_frames,
        "durationSec": duration_sec,
        "format": "9x16",
        "cuts": clean_cuts,
        "captions": captions,
        "punchZooms": timeline_zooms,
        "censors": clean_censors,
        "interstitials": [],
        "outro": outro
    }

    return manifest, timeline_censors


def step_5_verify_censor_overlays(timeline_censors: list, analysis_dir: Path):
    """
    Step 5: If censors non-empty, draw bounding box on a sample frame and save
    analysis/<episode_name>/verify_overlay_<id>.jpg.
    """
    if not timeline_censors:
        print("[*] No censors to verify.", flush=True)
        return

    print("\n" + "=" * 60, flush=True)
    print("🔍 STEP 5: Visual Verification of Censor Overlays", flush=True)
    print("=" * 60, flush=True)

    for c in timeline_censors:
        censor_id = c["id"]
        clip_path = c.get("_sourceClipPath")
        sample_sec = c.get("_sampleSec", 0.0)
        bbox = c.get("_bbox", [380, 380, 620, 620])
        ymin, xmin, ymax, xmax = [float(v) for v in bbox]

        if not clip_path or not Path(clip_path).exists():
            continue

        frame = None
        if CV2_AVAILABLE:
            try:
                cap = cv2.VideoCapture(clip_path)
                cap.set(cv2.CAP_PROP_POS_MSEC, sample_sec * 1000.0)
                ret, frame = cap.read()
                cap.release()
            except Exception:
                frame = None

        if frame is None:
            temp_jpg = analysis_dir / f"temp_{censor_id}.jpg"
            cmd = f'ffmpeg -y -ss {sample_sec:.2f} -i "{clip_path}" -vframes 1 -q:v 2 "{temp_jpg}"'
            subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if temp_jpg.exists() and CV2_AVAILABLE:
                frame = cv2.imread(str(temp_jpg))
                temp_jpg.unlink(missing_ok=True)

        if frame is not None and CV2_AVAILABLE:
            h, w = frame.shape[:2]
            x1 = max(0, min(w - 1, int(round((xmin / 1000.0) * w))))
            y1 = max(0, min(h - 1, int(round((ymin / 1000.0) * h))))
            x2 = max(x1 + 10, min(w, int(round((xmax / 1000.0) * w))))
            y2 = max(y1 + 10, min(h, int(round((ymax / 1000.0) * h))))

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 4)
            label_text = c.get("label", "[CENSORED]")
            cv2.putText(
                frame,
                label_text,
                (x1, max(35, y1 - 12)),
                cv2.FONT_HERSHEY_DUPLEX,
                1.0,
                (0, 224, 255),
                2,
                cv2.LINE_AA
            )

            out_img = analysis_dir / f"verify_overlay_{censor_id}.jpg"
            cv2.imwrite(str(out_img), frame)
            print(f"[+] Saved visual censor verification frame: {out_img}", flush=True)

            num_suffix = censor_id.split("_")[-1]
            out_num = analysis_dir / f"verify_overlay_{num_suffix}.jpg"
            if out_num != out_img:
                cv2.imwrite(str(out_num), frame)


def main():
    parser = argparse.ArgumentParser(description="Multi-Modal AI Context Engine for Life with Shubham Studio.")
    parser.add_argument("--episode", type=str, default="ep01", help="Episode ID (e.g. ep01)")
    args = parser.parse_args()

    episode = args.episode.lower().strip()
    root_dir = Path(__file__).resolve().parent.parent

    load_dotenv(root_dir / ".env")

    if not GENAI_AVAILABLE:
        print("[FATAL] google-genai package is not installed in .venv. Run pip install google-genai", file=sys.stderr, flush=True)
        sys.exit(1)

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("[FATAL] GEMINI_API_KEY or GOOGLE_API_KEY not found in .env", file=sys.stderr, flush=True)
        sys.exit(1)

    client = genai.Client(api_key=api_key, vertexai=False, http_options={"api_version": "v1beta"})

    norm_dir = root_dir / "media" / "02_normalized_cfr" / episode
    if not norm_dir.exists():
        print(f"[FATAL] Normalized media folder not found: {norm_dir}", file=sys.stderr, flush=True)
        print(f"        Please run scripts/01_ingest_cfr.py --episode {episode} first!", file=sys.stderr, flush=True)
        sys.exit(1)

    clips = sorted(list(norm_dir.glob("*_cfr.mp4")))
    if not clips:
        clips = sorted(list(norm_dir.glob("*.mp4")))
    if not clips:
        print(f"[FATAL] No video clips found in {norm_dir}", file=sys.stderr, flush=True)
        sys.exit(1)

    analysis_dir = root_dir / "analysis" / episode
    analysis_dir.mkdir(parents=True, exist_ok=True)
    proxies_dir = analysis_dir / "proxies"

    print("=" * 60, flush=True)
    print("🎬 Life with Shubham Studio — Context Analysis & Timeline Synthesis")
    print(f"   Episode:          {episode}")
    print(f"   Normalized Clips: {len(clips)} -> {[c.name for c in clips]}")
    print(f"   Analysis Dir:     {analysis_dir.relative_to(root_dir)}")
    print("=" * 60, flush=True)

    # STEP A: gemini-3.5-transcribe transcription (Interactions API v1beta)
    raw_transcript = step_a_transcribe(clips, analysis_dir, client)
    transcript_path = analysis_dir / "raw_transcript.json"

    # STEP B.1: Generate 3 fps analysis proxies
    proxy_paths = step_b_generate_proxies(clips, proxies_dir)

    # STEP B.2: Query Gemini 2.5 Flash with proxies + transcript
    gemini_data = step_b_query_gemini(proxy_paths, transcript_path, episode, clips, client)

    if not gemini_data or not gemini_data.get("cuts"):
        print("[FATAL] Gemini API did not return valid cuts for edit plan.", file=sys.stderr, flush=True)
        sys.exit(1)

    # STEP C (PURE PYTHON): Romanize Devanagari, compute timeline, convert bounding boxes, slice words
    manifest, timeline_censors = step_c_build_edit_plan(gemini_data, raw_transcript, clips, episode, fps=30)

    # STEP 5: Visual Verification of Censors
    step_5_verify_censor_overlays(timeline_censors, analysis_dir)

    # STEP 6: Write analysis/<episode>/edit_plan.json and copy to public/edit_plan.json
    manifest_path = analysis_dir / "edit_plan.json"
    public_manifest_path = root_dir / "public" / "edit_plan.json"

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"\n[+] Saved episode edit plan: {manifest_path.relative_to(root_dir)}", flush=True)

    public_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(manifest_path, public_manifest_path)
    print(f"[+] Synced to Remotion preview manifest: {public_manifest_path.relative_to(root_dir)}", flush=True)

    public_ep_dir = root_dir / "public" / "media" / episode
    public_ep_dir.mkdir(parents=True, exist_ok=True)
    for clip in clips:
        target_clip = public_ep_dir / clip.name
        if not target_clip.exists():
            shutil.copyfile(clip, target_clip)

    print("\n" + "=" * 60)
    print("✨ Analysis & Timeline Build Complete!")
    print(f"   Episode:        {manifest['episodeId']} - {manifest['title']}")
    print(f"   Total Timeline: {manifest['totalFrames']} frames ({manifest['durationSec']}s @ {manifest['fps']}fps)")
    print(f"   Cuts:           {len(manifest['cuts'])}")
    print(f"   Captions:       {len(manifest['captions'])}")
    print(f"   Censors:        {len(manifest['censors'])}")
    print(f"   Punch Zooms:    {len(manifest['punchZooms'])}")
    print("=" * 60, flush=True)


if __name__ == "__main__":
    main()
