import json
from pathlib import Path

# 1. Raw transcript first 20 words
raw_path = Path("analysis/ep01/raw_transcript.json")
raw = json.loads(raw_path.read_text(encoding="utf-8"))
clip1_words = raw.get("clip_01_cfr.mp4", [])[:20]

print("=" * 65)
print("🎙️ FIRST 20 WORDS FROM GEMINI-3.5-TRANSCRIBE (analysis/ep01/raw_transcript.json)")
print("=" * 65)
for w in clip1_words:
    s = w["start"]
    e = w["end"]
    spk = w["speaker"]
    idx = w["index"]
    word = w["word"]
    print(f"[{s:5.2f}s - {e:5.2f}s] ({spk}) idx={idx:2d}: '{word}'")

# 2. Public edit plan
plan_path = Path("public/edit_plan.json")
plan = json.loads(plan_path.read_text(encoding="utf-8"))

print("\n" + "=" * 65)
print("🎬 EDIT PLAN SUMMARY (public/edit_plan.json)")
print("=" * 65)
print(f"Title:         {plan.get('title')}")
print(f"Total Frames:  {plan.get('totalFrames')} frames ({plan.get('durationSec')}s @ {plan.get('fps')}fps)")
print(f"Cuts:          {len(plan.get('cuts', []))}")
print(f"Captions:      {len(plan.get('captions', []))}")
print(f"Censors:       {len(plan.get('censors', []))}")
print(f"Punch Zooms:   {len(plan.get('punchZooms', []))}")

print("\n" + "=" * 65)
print("✂️ FINAL CUTS")
print("=" * 65)
for c in plan.get("cuts", []):
    cid = c["id"]
    src = c["sourceFile"]
    s = c["sourceStartSec"]
    e = c["sourceEndSec"]
    sf = c["startFrame"]
    df = c["durationFrames"]
    print(f"{cid:>6s}: {src} [{s:5.2f}s - {e:5.2f}s] -> frames {sf:4d} to {sf+df:4d} ({df} frames)")

print("\n" + "=" * 65)
print("🛡️ CENSORS")
print("=" * 65)
for censor in plan.get("censors", []):
    print(json.dumps(censor, indent=2))

print("\n" + "=" * 65)
print("🔎 PUNCH ZOOMS")
print("=" * 65)
for pz in plan.get("punchZooms", []):
    print(json.dumps(pz, indent=2))

print("\n" + "=" * 65)
print("💬 FIRST 5 CAPTIONS")
print("=" * 65)
for cap in plan.get("captions", [])[:5]:
    cid = cap["id"]
    sf = cap["startFrame"]
    ef = cap["endFrame"]
    txt = cap["text"]
    hl = cap["highlightWord"]
    print(f"{cid}: frames {sf:4d}-{ef:4d} | highlight: '{hl}' | text: '{txt}'")

# Check for Devanagari in public/edit_plan.json
plan_str = json.dumps(plan, ensure_ascii=False)
devanagari = [ch for ch in plan_str if '\u0900' <= ch <= '\u097F']
print("\n" + "=" * 65)
print("🔡 DEVANAGARI SCRIPT AUDIT")
print("=" * 65)
print(f"Remaining Devanagari characters in public/edit_plan.json: {len(devanagari)}")
if devanagari:
    print(f"Found characters: {devanagari[:10]}")
else:
    print("SUCCESS: 100% of captions are Romanized Hinglish! Zero Devanagari characters remain.")

# Outro
print("\n" + "=" * 65)
print("🏁 OUTRO")
print("=" * 65)
print(json.dumps(plan.get("outro", {}), indent=2))
