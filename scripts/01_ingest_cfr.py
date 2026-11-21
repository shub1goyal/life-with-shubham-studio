#!/usr/bin/env python3
"""
scripts/01_ingest_cfr.py
========================
VFR -> 30fps CFR + 48kHz Loudnorm Normalizer.

Eliminates phone/WhatsApp Variable Frame Rate (VFR) audio-video desync:
- Transcodes all raw phone clips to strict Constant Frame Rate (30 fps, SAR 1:1)
- Resamples audio to 48,000 Hz, 2-channel stereo
- Applies 85Hz highpass filter to eliminate phone handling rumble
- Normalizes speech loudness to broadcast EBU R128 (-16 LUFS)
- Syncs normalized CFR proxies into public/media/<episode>/ for Remotion Studio
"""

import os
import re
import sys
import shutil
import argparse
import subprocess
from pathlib import Path

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


def run_command(cmd, desc=""):
    if desc:
        print(f"[*] {desc}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[!] Error executing: {cmd}")
        print(f"[!] Output: {result.stderr.strip() or result.stdout.strip()}")
        return False
    return True


def probe_clip(file_path):
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

    # Fallback via ffmpeg banner output
    try:
        res = subprocess.run(f'ffmpeg -i "{file_path}" -hide_banner', shell=True, capture_output=True, text=True)
        match = re.search(r"Duration:\s*(\d{2}):(\d{2}):(\d{2}\.\d+)", res.stderr)
        if match:
            h, m, s = match.groups()
            return int(h) * 3600 + int(m) * 60 + float(s)
    except Exception:
        pass

    return 0.0


def normalize_episode(episode: str):
    root_dir = Path(__file__).resolve().parent.parent
    raw_dir = root_dir / "media" / "01_raw_videos" / episode
    cfr_dir = root_dir / "media" / "02_normalized_cfr" / episode
    public_dir = root_dir / "public" / "media" / episode

    if not raw_dir.exists():
        print(f"[!] Raw directory not found: {raw_dir}")
        sys.exit(1)

    cfr_dir.mkdir(parents=True, exist_ok=True)
    public_dir.mkdir(parents=True, exist_ok=True)

    supported_extensions = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi"}
    raw_files = [
        f for f in raw_dir.iterdir()
        if f.is_file() and f.suffix.lower() in supported_extensions
    ]

    if not raw_files:
        print(f"[!] No video clips found in {raw_dir}")
        sys.exit(1)

    print(f"============================================================")
    print(f"🎬 Life with Shubham Studio — CFR Ingest & Normalization")
    print(f"   Episode: {episode}")
    print(f"   Found {len(raw_files)} raw clip(s)")
    print(f"============================================================")

    normalized_files = []

    for idx, raw_clip in enumerate(sorted(raw_files), start=1):
        clean_stem = raw_clip.stem.replace(" ", "_")
        output_name = f"{clean_stem}_cfr.mp4"
        output_cfr = cfr_dir / output_name
        output_public = public_dir / output_name

        print(f"\n[{idx}/{len(raw_files)}] Ingesting raw clip: {raw_clip.name}")
        raw_dur = probe_clip(raw_clip)
        print(f"    Raw Duration: {raw_dur:.2f}s")

        # FFmpeg command strictly enforcing 30fps CFR, setsar=1, 48kHz audio, highpass, loudnorm
        ffmpeg_cmd = (
            f'ffmpeg -y -i "{raw_clip}" '
            f'-vf "fps=30,setsar=1" '
            f'-vsync cfr '
            f'-c:v libx264 -preset fast -crf 18 '
            f'-c:a aac -ar 48000 -ac 2 '
            f'-af "highpass=f=85,loudnorm=I=-16:TP=-1.5:LRA=11" '
            f'"{output_cfr}"'
        )

        success = run_command(ffmpeg_cmd, desc=f"Converting to 30fps CFR + 48kHz broadcast audio")
        if not success:
            print(f"[!] Failed to normalize {raw_clip.name}")
            continue

        cfr_dur = probe_clip(output_cfr)
        print(f"    [+] CFR Normalized: {output_cfr.name} ({cfr_dur:.2f}s, exact 30fps)")

        # Sync to public/media/<episode>/
        try:
            shutil.copy2(output_cfr, output_public)
            print(f"    [+] Synced to Remotion Studio public asset: {output_public.relative_to(root_dir)}")
            normalized_files.append({
                "raw": str(raw_clip),
                "cfr": str(output_cfr),
                "public_rel": f"media/{episode}/{output_name}",
                "duration": cfr_dur,
            })
        except Exception as e:
            print(f"[!] Failed to copy to public dir: {e}")

    print(f"\n============================================================")
    print(f"✅ Ingest completed! {len(normalized_files)}/{len(raw_files)} clips ready for Remotion.")
    print(f"   Zero-desync rule enforced. Never feed raw VFR directly.")
    print(f"============================================================")
    return normalized_files


def main():
    parser = argparse.ArgumentParser(description="Ingest and normalize raw phone clips to 30fps CFR.")
    parser.add_argument("--episode", type=str, default="ep01", help="Episode ID (e.g. ep01)")
    args = parser.parse_args()

    normalize_episode(args.episode)


if __name__ == "__main__":
    main()
