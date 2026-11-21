#!/usr/bin/env python3
"""
scripts/03_render_final.py
==========================
Final Mastered MP4 Exporter for Life with Shubham Studio.

Renders final broadcast-quality MP4 using Remotion:
- Strict 30fps constant frame rate
- H.264 video codec with CRF 18 (visually lossless)
- AAC 48kHz stereo audio
- Output saved to output/final_videos/<episode>_<composition>.mp4
"""

import sys
import shutil
import argparse
import subprocess
from pathlib import Path


def render_composition(episode: str, composition: str = "Reel9x16", crf: int = 18):
    root_dir = Path(__file__).resolve().parent.parent
    output_dir = root_dir / "output" / "final_videos"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_filename = f"{episode}_{composition}.mp4"
    output_path = output_dir / output_filename

    manifest_file = root_dir / "public" / "edit_plan.json"
    if not manifest_file.exists():
        print(f"[!] Active edit plan not found at {manifest_file}")
        print("    Please run scripts/02_analyze_context.py first!")
        sys.exit(1)

    print("============================================================")
    print(f"🚀 Life with Shubham Studio — Final Master Render")
    print(f"   Episode:     {episode}")
    print(f"   Composition: {composition}")
    print(f"   Destination: {output_path.relative_to(root_dir)}")
    print(f"   CRF:         {crf} (High Quality H.264)")
    print("============================================================")

    # Remotion render command
    cmd = (
        f'npx remotion render src/index.ts {composition} '
        f'"{output_path}" '
        f'--codec h264 '
        f'--crf {crf} '
        f'--audio-codec aac '
        f'--overwrite'
    )

    print(f"[*] Executing Remotion render...")
    result = subprocess.run(cmd, shell=True, text=True)

    if result.returncode == 0 and output_path.exists():
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print("\n============================================================")
        print(f"🎉 RENDER SUCCESSFUL!")
        print(f"   File: {output_path}")
        print(f"   Size: {size_mb:.2f} MB")
        print("   Ready to publish to Instagram Reels / YouTube Shorts / Vlogs!")
        print("============================================================")
        return str(output_path)
    else:
        print("\n[!] Render failed. Check the logs above for details.")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Render final mastered MP4 video via Remotion.")
    parser.add_argument("--episode", type=str, default="ep01", help="Episode ID (e.g. ep01)")
    parser.add_argument("--composition", type=str, default="Reel9x16", choices=["Reel9x16", "Vlog16x9"], help="Composition ID to render")
    parser.add_argument("--crf", type=int, default=18, help="H.264 CRF quality level (default: 18)")
    args = parser.parse_args()

    render_composition(args.episode, args.composition, args.crf)


if __name__ == "__main__":
    main()
