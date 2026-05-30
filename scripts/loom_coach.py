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
import shutil
import tempfile
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# ── ffmpeg resolver ──────────────────────────────────────────────────────────

_FFMPEG_FALLBACK_DIRS = [
    # WinGet Gyan.FFmpeg (most common Windows install)
    str(Path.home() / "AppData/Local/Microsoft/WinGet/Packages"),
    # Chocolatey
    "C:/ProgramData/chocolatey/bin",
    # Scoop
    str(Path.home() / "scoop/shims"),
    # BlueStacks bundles ffmpeg
    "C:/Program Files/BlueStacks_nxt",
]

def _find_ffmpeg() -> str:
    # 1. On PATH
    found = shutil.which("ffmpeg")
    if found:
        return found
    # 2. WinGet install tree (Gyan.FFmpeg)
    winget_base = Path.home() / "AppData/Local/Microsoft/WinGet/Packages"
    if winget_base.exists():
        for pkg in winget_base.glob("Gyan.FFmpeg*"):
            exe = next(pkg.rglob("ffmpeg.exe"), None)
            if exe:
                return str(exe)
    # 3. Other fallback dirs
    for d in _FFMPEG_FALLBACK_DIRS[1:]:
        candidate = Path(d) / "ffmpeg.exe"
        if candidate.exists():
            return str(candidate)
    return ""


FFMPEG_EXE = _find_ffmpeg()


# ── Dependency checks ────────────────────────────────────────────────────────

def check_deps():
    missing = []
    try:
        import yt_dlp
    except ImportError:
        missing.append("yt-dlp  →  pip install yt-dlp")
    try:
        import faster_whisper
    except ImportError:
        missing.append("faster-whisper  →  pip install faster-whisper")
    try:
        import cv2
    except ImportError:
        try:
            from PIL import Image  # Pillow fallback for frame reading
        except ImportError:
            missing.append("opencv-python  →  pip install opencv-python-headless")
    # anthropic not required — visual analysis is done by Claude Code reading frames directly

    if not FFMPEG_EXE:
        missing.append("ffmpeg  →  winget install Gyan.FFmpeg  (then restart terminal)")

    if missing:
        print("\n  Missing dependencies:")
        for m in missing:
            print(f"    {m}")
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
        [FFMPEG_EXE, "-i", video_path, "-vn", "-acodec", "pcm_s16le",
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

    print("  Transcribing (first run downloads ~244MB for 'small' model)...")
    model = WhisperModel("small", device="cpu", compute_type="int8")

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

def _get_video_duration(video_path: str) -> float:
    result = subprocess.run(
        [FFMPEG_EXE, "-i", video_path],
        capture_output=True, text=True
    )
    output = result.stderr
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", output)
    if match:
        h, m, s = int(match.group(1)), int(match.group(2)), float(match.group(3))
        return h * 3600 + m * 60 + s
    return 0.0


def extract_frames(video_path: str, out_dir: str, interval_sec: int = 12) -> list:
    print(f"  Extracting frames every {interval_sec}s...")
    frames_dir = os.path.join(out_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)

    # Use ffmpeg to extract one frame every interval_sec seconds
    frame_pattern = os.path.join(frames_dir, "frame_%04d.jpg")
    result = subprocess.run(
        [FFMPEG_EXE, "-i", video_path,
         "-vf", f"fps=1/{interval_sec}",
         "-q:v", "2",  # JPEG quality (2=high)
         frame_pattern, "-y"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg frame extraction failed:\n{result.stderr}")

    # Collect frames and assign timestamps
    frame_files = sorted(Path(frames_dir).glob("frame_*.jpg"))
    duration = _get_video_duration(video_path)

    frame_data = []
    for i, fpath in enumerate(frame_files):
        timestamp_sec = i * interval_sec
        frame_data.append({
            "path": str(fpath),
            "timestamp": fmt_time(timestamp_sec),
        })

    print(f"  Extracted {len(frame_data)} frames from {fmt_time(duration)} video.")
    return frame_data


# ── Step 6: Save frames for Claude Code visual analysis ──────────────────────
# Visual coaching is done by Claude Code reading the saved frames directly —
# no external API key needed.

def save_frames(frame_data: list, output_dir: str) -> list:
    """Copy extracted frames to a persistent output directory."""
    frames_out = Path(output_dir) / "frames"
    frames_out.mkdir(parents=True, exist_ok=True)

    saved = []
    for fd in frame_data:
        src = Path(fd["path"])
        dst = frames_out / src.name
        shutil.copy2(src, dst)
        saved.append({"path": str(dst), "timestamp": fd["timestamp"]})

    print(f"  Frames saved to {frames_out} for visual review.")
    return saved


# ── Step 7: Generate report ──────────────────────────────────────────────────

def generate_report(url: str, speech: dict, frames: list) -> str:
    date = datetime.now().strftime("%Y-%m-%d")

    # Build filler word string
    if speech["fillers"]:
        filler_str = "  " + ", ".join(f'"{w}" x{c}' for w, c in
                                       sorted(speech["fillers"].items(), key=lambda x: -x[1]))
    else:
        filler_str = "  None detected."

    # Build pause string
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

    # Speech verdict
    issues = []
    if speech["wpm"] > 175:
        issues.append("Speaking too fast — slow down, especially in the diagnosis section.")
    elif speech["wpm"] < 110:
        issues.append("Speaking too slowly — pick up the pace, especially in the intro.")
    if speech["filler_total"] > 5:
        top_filler = max(speech["fillers"], key=speech["fillers"].get)
        issues.append(f"Filler words ({speech['filler_total']} total) — especially \"{top_filler}\". Pause instead.")
    if len(speech["pauses"]) > 4:
        issues.append(f"{len(speech['pauses'])} long pauses — some are fine, but too many break momentum.")

    speech_verdict = "\n".join(f"  {i+1}. {issue}" for i, issue in enumerate(issues)) if issues else "  Speech metrics look clean."

    # Frame list for visual review
    frame_list = "\n".join(
        f"  [{fd['timestamp']}] {fd['path']}"
        for fd in frames
    )

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

## SPEECH VERDICT

{speech_verdict}

---

## VISUAL ANALYSIS

Frames extracted every 12s. Run `/loom-review` then ask Claude Code to analyze the frames below.

FRAMES FOR REVIEW
{frame_list}

(Claude Code reads these images directly — ask: "analyze the frames from the last loom-review")

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

        # Save frames to persistent location (next to the report) for visual review
        report_dir = str(Path(output_path).parent)
        frames = save_frames(frame_data, report_dir)

        print("  Generating report...")
        report = generate_report(args.url, speech, frames)

        Path(output_path).write_text(report, encoding="utf-8")
        print(f"\n  Report saved: {output_path}")
        print(f"\n{'='*60}")
        print(f"  WPM: {speech['wpm']} ({speech['wpm_verdict']})")
        print(f"  Fillers: {speech['filler_total']}")
        print(f"  Pauses: {len(speech['pauses'])}")
        print(f"  Frames: {len(frames)} saved to {report_dir}/frames/")
        print(f"{'='*60}\n")
        print("  Next: ask Claude Code to analyze the frames for visual coaching.")

    return output_path


if __name__ == "__main__":
    main()
