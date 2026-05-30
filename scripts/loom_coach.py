"""
loom_coach.py — Loom video coaching tool

Downloads a Loom video, transcribes it, extracts frames,
and produces a structured coaching report covering:
  - Speech: WPM, filler words, pauses, pace variation
  - Visual: eye contact, framing, posture, lighting, screen layout
  - Transcript: full text with timestamps

Usage:
  python scripts/loom_coach.py <loom_url>
  python scripts/loom_coach.py <loom_url> --output outputs/roasts/my-loom.md
"""

import sys
import os
import re
import json
import base64
import shutil
import tempfile
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# ── Dependency checks ────────────────────────────────────────────────────────

def check_deps():
    missing = []
    try:
        import yt_dlp
    except ImportError:
        missing.append("yt-dlp (pip install yt-dlp)")
    try:
        import faster_whisper
    except ImportError:
        missing.append("faster-whisper (pip install faster-whisper)")
    try:
        import cv2
    except ImportError:
        missing.append("opencv-python (pip install opencv-python)")
    try:
        import anthropic
    except ImportError:
        missing.append("anthropic (pip install anthropic)")

    if shutil.which("ffmpeg") is None:
        missing.append("ffmpeg — download from https://ffmpeg.org/download.html and add to PATH")

    if missing:
        print("\n  Missing dependencies:")
        for m in missing:
            print(f"    pip install {m}" if "pip install" not in m else f"    {m}")
        sys.exit(1)


# ── Step 1: Download ─────────────────────────────────────────────────────────

def download_video(url: str, out_dir: str) -> str:
    import yt_dlp

    print(f"  Downloading video from {url}...")
    out_template = os.path.join(out_dir, "video.%(ext)s")

    ydl_opts = {
        "outtmpl": out_template,
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # Find the downloaded file
    for f in Path(out_dir).glob("video.*"):
        print(f"  Downloaded: {f.name}")
        return str(f)

    raise FileNotFoundError("Download completed but video file not found.")


# ── Step 2: Extract audio ────────────────────────────────────────────────────

def extract_audio(video_path: str, out_dir: str) -> str:
    audio_path = os.path.join(out_dir, "audio.wav")
    print("  Extracting audio...")
    result = subprocess.run(
        ["ffmpeg", "-i", video_path, "-vn", "-acodec", "pcm_s16le",
         "-ar", "16000", "-ac", "1", audio_path, "-y"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg audio extraction failed:\n{result.stderr}")
    return audio_path


# ── Step 3: Transcribe ───────────────────────────────────────────────────────

FILLER_WORDS = {
    "um", "uh", "uhh", "umm", "hmm", "like", "you know", "you know what i mean",
    "basically", "literally", "actually", "right", "so", "okay", "ok",
    "kind of", "sort of", "i mean", "anyway"
}

def transcribe(audio_path: str) -> dict:
    from faster_whisper import WhisperModel

    print("  Transcribing (this takes 1-2 min on first run, model downloads ~150MB)...")
    model = WhisperModel("base", device="cpu", compute_type="int8")

    segments_raw, info = model.transcribe(
        audio_path,
        word_timestamps=True,
        language="en"
    )

    segments = []
    all_words = []

    for seg in segments_raw:
        words = []
        for w in (seg.words or []):
            words.append({
                "word": w.word.strip(),
                "start": round(w.start, 2),
                "end": round(w.end, 2),
            })
            all_words.append(words[-1])
        segments.append({
            "start": round(seg.start, 2),
            "end": round(seg.end, 2),
            "text": seg.text.strip(),
            "words": words,
        })

    return {
        "duration": round(info.duration, 1),
        "language": info.language,
        "segments": segments,
        "words": all_words,
    }


# ── Step 4: Speech analysis ──────────────────────────────────────────────────

def fmt_time(seconds: float) -> str:
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m}:{s:02d}"


def analyze_speech(data: dict) -> dict:
    words = data["words"]
    segments = data["segments"]
    duration = data["duration"]

    total_words = len(words)
    wpm = round((total_words / duration) * 60) if duration > 0 else 0

    # Filler word detection
    fillers = {}
    text_lower = " ".join(w["word"].lower() for w in words)
    for fw in FILLER_WORDS:
        count = len(re.findall(r'\b' + re.escape(fw) + r'\b', text_lower))
        if count > 0:
            fillers[fw] = count
    filler_total = sum(fillers.values())

    # Long pauses (gap between word end and next word start > 1.5s)
    pauses = []
    for i in range(1, len(words)):
        gap = words[i]["start"] - words[i-1]["end"]
        if gap >= 1.5:
            pauses.append({
                "at": fmt_time(words[i-1]["end"]),
                "duration": round(gap, 1),
                "before": words[i-1]["word"],
                "after": words[i]["word"],
            })

    # Per-segment WPM to find fast/slow spots
    seg_wpm = []
    for seg in segments:
        seg_dur = seg["end"] - seg["start"]
        seg_words = len(seg["text"].split())
        if seg_dur > 0:
            seg_wpm.append({
                "start": fmt_time(seg["start"]),
                "end": fmt_time(seg["end"]),
                "wpm": round((seg_words / seg_dur) * 60),
                "text": seg["text"][:60] + ("..." if len(seg["text"]) > 60 else ""),
            })

    fast_segs = [s for s in seg_wpm if s["wpm"] > 180]
    slow_segs = [s for s in seg_wpm if s["wpm"] < 90 and s["wpm"] > 0]

    # Full transcript
    transcript = " ".join(seg["text"] for seg in segments)

    return {
        "duration": fmt_time(duration),
        "total_words": total_words,
        "wpm": wpm,
        "wpm_target": "130-160",
        "wpm_verdict": (
            "too fast" if wpm > 175 else
            "slightly fast" if wpm > 160 else
            "good" if wpm >= 130 else
            "too slow"
        ),
        "fillers": fillers,
        "filler_total": filler_total,
        "pauses": pauses,
        "fast_segments": fast_segs[:3],
        "slow_segments": slow_segs[:3],
        "transcript": transcript,
    }


# ── Step 5: Extract frames ───────────────────────────────────────────────────

def extract_frames(video_path: str, out_dir: str, interval_sec: int = 12) -> list:
    import cv2

    print(f"  Extracting frames every {interval_sec}s...")
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0

    frame_paths = []
    frame_interval = int(fps * interval_sec)

    frame_idx = 0
    saved = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % frame_interval == 0:
            timestamp = frame_idx / fps if fps > 0 else 0
            fname = os.path.join(out_dir, f"frame_{saved:03d}_{fmt_time(timestamp).replace(':', '_')}.jpg")
            cv2.imwrite(fname, frame)
            frame_paths.append({"path": fname, "timestamp": fmt_time(timestamp)})
            saved += 1
        frame_idx += 1

    cap.release()
    print(f"  Extracted {saved} frames from {fmt_time(duration)} video.")
    return frame_paths


# ── Step 6: Visual analysis via Claude Vision ────────────────────────────────

VISUAL_PROMPT = """You are a presentation coach reviewing a frame from someone's Loom video proposal.

Analyze this frame across these dimensions:

1. EYE CONTACT — are they looking at the camera/lens, or at their screen? Rate: direct / intermittent / avoiding
2. FRAMING — how are they positioned? Rate: centered / too close / too far / off-center / face cut off
3. POSTURE — body language. Rate: upright and confident / slouching / leaning / stiff / relaxed
4. LIGHTING — quality of light on their face. Rate: well lit / backlit / harsh / uneven / dark
5. ENERGY — do they look engaged or flat? Rate: engaged / neutral / flat / nervous
6. SCREEN VISIBLE — if they're screencasting, is the screen readable? Rate: clear / small / unreadable / not applicable

Output a JSON object like this (no markdown, raw JSON only):
{
  "eye_contact": "direct",
  "framing": "slightly off-center",
  "posture": "upright",
  "lighting": "well lit",
  "energy": "engaged",
  "screen_visible": "clear",
  "flag": null
}

For "flag": if there is one specific thing to fix in this frame, write a short sentence. Otherwise null.
Only flag things that would actually matter to a client watching this video."""


def analyze_frames(frame_data: list) -> list:
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        dotenv_path = Path(__file__).parent.parent / ".env"
        if dotenv_path.exists():
            for line in dotenv_path.read_text().splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    api_key = line.split("=", 1)[1].strip().strip('"')
                    break

    client = anthropic.Anthropic(api_key=api_key)
    results = []

    print(f"  Analyzing {len(frame_data)} frames with Claude Vision...")
    for i, fd in enumerate(frame_data):
        with open(fd["path"], "rb") as f:
            img_b64 = base64.standard_b64encode(f.read()).decode()

        try:
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=300,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": img_b64,
                            },
                        },
                        {"type": "text", "text": VISUAL_PROMPT},
                    ],
                }],
            )
            raw = resp.content[0].text.strip()
            # Strip markdown code blocks if present
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
            analysis = json.loads(raw)
        except Exception as e:
            analysis = {"error": str(e)}

        results.append({
            "timestamp": fd["timestamp"],
            "path": fd["path"],
            **analysis,
        })
        sys.stdout.write(f"    frame {i+1}/{len(frame_data)} done\r")
        sys.stdout.flush()

    print()
    return results


# ── Step 7: Generate report ──────────────────────────────────────────────────

def generate_report(url: str, speech: dict, visuals: list) -> str:
    date = datetime.now().strftime("%Y-%m-%d")

    # Aggregate visual metrics
    eye_counts = {}
    framing_counts = {}
    posture_counts = {}
    lighting_counts = {}
    energy_counts = {}
    flags = []

    for v in visuals:
        for key, counter in [
            ("eye_contact", eye_counts),
            ("framing", framing_counts),
            ("posture", posture_counts),
            ("lighting", lighting_counts),
            ("energy", energy_counts),
        ]:
            val = v.get(key, "unknown")
            counter[val] = counter.get(val, 0) + 1
        if v.get("flag"):
            flags.append(f"  [{v['timestamp']}] {v['flag']}")

    def dominant(counter):
        if not counter:
            return "unknown"
        return max(counter, key=counter.get)

    # Build filler word string
    filler_str = ""
    if speech["fillers"]:
        filler_str = "  " + ", ".join(f'"{w}" x{c}' for w, c in
                                       sorted(speech["fillers"].items(), key=lambda x: -x[1]))
    else:
        filler_str = "  None detected."

    # Build pause string
    pause_str = ""
    if speech["pauses"]:
        pause_str = "\n".join(
            f"  [{p['at']}] {p['duration']}s pause (after \"{p['before']}\")"
            for p in speech["pauses"][:5]
        )
    else:
        pause_str = "  None detected."

    # Fast/slow segments
    fast_str = "\n".join(
        f"  [{s['start']}] {s['wpm']} WPM — \"{s['text']}\""
        for s in speech["fast_segments"]
    ) or "  None."
    slow_str = "\n".join(
        f"  [{s['start']}] {s['wpm']} WPM — \"{s['text']}\""
        for s in speech["slow_segments"]
    ) or "  None."

    # Frame-by-frame visual table
    frame_table = ""
    for v in visuals:
        flag_note = f" — {v['flag']}" if v.get("flag") else ""
        frame_table += (
            f"  [{v['timestamp']}] "
            f"eyes:{v.get('eye_contact','?')} | "
            f"frame:{v.get('framing','?')} | "
            f"posture:{v.get('posture','?')} | "
            f"light:{v.get('lighting','?')} | "
            f"energy:{v.get('energy','?')}"
            f"{flag_note}\n"
        )

    # Verdict
    issues = []
    if speech["wpm"] > 175:
        issues.append("Speaking too fast — slow down, especially in the diagnosis section.")
    elif speech["wpm"] < 110:
        issues.append("Speaking too slowly — pick up the pace, especially in the intro.")
    if speech["filler_total"] > 5:
        top_filler = max(speech["fillers"], key=speech["fillers"].get)
        issues.append(f"Filler words ({speech['filler_total']} total) — especially \"{top_filler}\". Pause instead.")
    if len(speech["pauses"]) > 4:
        issues.append(f"{len(speech['pauses'])} long pauses detected — some are fine, but too many break momentum.")
    if dominant(eye_counts) not in ("direct", "intermittent"):
        issues.append("Eye contact is weak — look at the camera lens, not the screen or your notes.")
    if dominant(framing_counts) not in ("centered",):
        issues.append(f"Framing: {dominant(framing_counts)} — reposition your camera.")
    if dominant(lighting_counts) in ("backlit", "dark"):
        issues.append(f"Lighting: {dominant(lighting_counts)} — fix your light source before rerecording.")
    if dominant(energy_counts) in ("flat", "neutral"):
        issues.append("Energy reads as flat — add more vocal variation, especially on key points.")

    if not issues:
        verdict = "No major issues. Clean recording, send it."
    else:
        verdict = "\n".join(f"  {i+1}. {issue}" for i, issue in enumerate(issues))

    report = f"""# Loom Coaching Report
**Date:** {date}
**Command:** /loom-review
**URL:** {url}

---

## SPEECH ANALYSIS

  Duration:      {speech['duration']}
  Total words:   {speech['total_words']}
  Avg pace:      {speech['wpm']} WPM ({speech['wpm_verdict']} — target {speech['wpm_target']})

FILLER WORDS ({speech['filler_total']} total)
{filler_str}

LONG PAUSES (1.5s+)
{pause_str}

FAST SEGMENTS (>180 WPM — slow these down)
{fast_str}

SLOW SEGMENTS (<90 WPM — pick up the pace)
{slow_str}

---

## VISUAL ANALYSIS

  Eye contact:   {dominant(eye_counts)}
  Framing:       {dominant(framing_counts)}
  Posture:       {dominant(posture_counts)}
  Lighting:      {dominant(lighting_counts)}
  Energy:        {dominant(energy_counts)}

FRAME BY FRAME
{frame_table}
FLAGS TO FIX
{chr(10).join(flags) if flags else "  None."}

---

## VERDICT

{verdict}

---

## TRANSCRIPT

{speech['transcript']}
"""
    return report


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Loom coaching tool")
    parser.add_argument("url", help="Loom share URL")
    parser.add_argument("--output", help="Output file path (default: outputs/roasts/YYYY-MM-DD-loom-review.md)")
    parser.add_argument("--frame-interval", type=int, default=12,
                        help="Seconds between frame extractions (default: 12)")
    args = parser.parse_args()

    check_deps()

    date = datetime.now().strftime("%Y-%m-%d")
    output_path = args.output or f"outputs/roasts/{date}-loom-review.md"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        print(f"\n  Loom Coach starting...")
        print(f"  URL: {args.url}\n")

        video_path = download_video(args.url, tmp)
        audio_path = extract_audio(video_path, tmp)

        print("  Transcribing audio...")
        transcript_data = transcribe(audio_path)
        speech = analyze_speech(transcript_data)

        frame_data = extract_frames(video_path, tmp, args.frame_interval)
        visuals = analyze_frames(frame_data)

        print("  Generating report...")
        report = generate_report(args.url, speech, visuals)

        Path(output_path).write_text(report, encoding="utf-8")
        print(f"\n  Report saved: {output_path}")
        print(f"\n{'='*60}")
        print(f"  WPM: {speech['wpm']} ({speech['wpm_verdict']})")
        print(f"  Fillers: {speech['filler_total']}")
        print(f"  Pauses: {len(speech['pauses'])}")
        print(f"{'='*60}\n")

    return output_path


if __name__ == "__main__":
    main()
