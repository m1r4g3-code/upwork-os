# /loom-review — Loom Video Coaching

## Role

You analyze Emmanuel's recorded Loom videos for speech quality, visual presentation, and delivery coaching. This is a pre-send quality gate — run this before any Loom goes to a client.

---

## What Gets Analyzed

**Speech (from Whisper transcription):**
- Words per minute — overall pace + per-segment variation
- Filler words — "um", "uh", "like", "you know", "basically", "right", "so", etc.
- Long pauses (1.5s+) — timestamped
- Fast segments (>180 WPM) — where to slow down
- Slow segments (<90 WPM) — where to pick up

**Visual (Claude Vision on extracted frames):**
- Eye contact — direct / intermittent / avoiding
- Framing — centered / too close / too far / off-center
- Posture — upright / slouching / leaning / stiff
- Lighting — well lit / backlit / harsh / dark
- Energy — engaged / neutral / flat / nervous
- Screen readability — if screencasting

---

## How to Run

```
python scripts/loom_coach.py <loom_url>
python scripts/loom_coach.py <loom_url> --output outputs/roasts/YYYY-MM-DD-slug.md
python scripts/loom_coach.py <loom_url> --frame-interval 8
```

First run downloads the Whisper base model (~150MB, one-time).

---

## Pipeline

```
1. yt-dlp downloads the Loom video
2. ffmpeg extracts audio as 16kHz mono WAV
3. faster-whisper transcribes with word-level timestamps
4. Speech metrics calculated from timestamps
5. opencv extracts frames every 12 seconds
6. Claude Vision (claude-haiku) analyzes each frame
7. Report generated to outputs/roasts/
```

---

## When to Run

- Before sending ANY Loom to a client
- After recording a new proposal Loom
- When reviewing a Loom that didn't get a reply

---

## Output Format

```
SPEECH ANALYSIS
  Duration / WPM / verdict

FILLER WORDS
  "um" x3, "like" x2 ...

LONG PAUSES
  [0:34] 2.1s pause ...

FAST/SLOW SEGMENTS
  [0:12] 195 WPM — slow down here

VISUAL ANALYSIS
  Eye contact / Framing / Posture / Lighting / Energy

FRAME BY FRAME
  [0:00] eyes:direct | frame:centered | ...

VERDICT
  Numbered list of what to fix before sending.
```

---

## Dependencies

```
pip install faster-whisper opencv-python yt-dlp
ffmpeg — add to PATH (https://ffmpeg.org/download.html)
```

---

## Wikilinks

[[voice]] · [[write-proposal]] · [[proposal-framework]]
