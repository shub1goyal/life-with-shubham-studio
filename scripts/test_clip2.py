import sys
import traceback
import time

try:
    import av
    _orig = av.open
    def _safe(*a, **k):
        k.pop("metadata_errors", None)
        return _orig(*a, **k)
    av.open = _safe
except:
    pass

from faster_whisper import WhisperModel

print("Loading model...", flush=True)
m = WhisperModel("small", device="cpu", compute_type="int8")
print("Model loaded. Transcribing clip_02_cfr.mp4...", flush=True)

t0 = time.time()
try:
    segs, info = m.transcribe("media/02_normalized_cfr/ep01/clip_02_cfr.mp4", word_timestamps=True)
    print("Language detected:", info.language, flush=True)
    words = []
    for s in segs:
        print(f"Segment: {s.start:.2f} -> {s.end:.2f}: {s.text}", flush=True)
        if s.words:
            for w in s.words:
                words.append((w.word.strip(), round(w.start, 2), round(w.end, 2)))
    print(f"Total words: {len(words)} in {time.time()-t0:.1f}s", flush=True)
except Exception as e:
    print(f"Error during transcription: {e}", flush=True)
    traceback.print_exc()
