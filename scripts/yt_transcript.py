"""
Fetch a YouTube transcript and save it to sources/transcripts/.

Method 1 (fast): youtube_transcript_api — works when IP is not blocked
Method 2 (fallback): yt-dlp — bypasses IP blocks, uses auto-generated captions

Usage:
  python scripts/yt_transcript.py <youtube_url_or_video_id>
  python scripts/yt_transcript.py <url> --cookies data/Yt_cookies.json

Cookie formats supported:
  - JSON array (from browser extension exports)
  - Netscape cookies.txt (from "Get cookies.txt LOCALLY" extension)

Auto-detected cookie files: data/Yt_cookies.json → cookies.txt

Output: sources/transcripts/<video_id>.txt
"""

import sys
import json
import re
import subprocess
import http.cookiejar
import requests
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

ROOT = Path(__file__).parent.parent
OUT_DIR = ROOT / "sources" / "transcripts"
DEFAULT_COOKIES_JSON = ROOT / "data" / "Yt_cookies.json"
DEFAULT_COOKIES_TXT  = ROOT / "cookies.txt"


def extract_video_id(url_or_id: str) -> str:
    for pattern in [r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})"]:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url_or_id):
        return url_or_id
    raise ValueError(f"Could not extract video ID from: {url_or_id}")


def _find_default_cookies() -> Path | None:
    if DEFAULT_COOKIES_JSON.exists():
        return DEFAULT_COOKIES_JSON
    if DEFAULT_COOKIES_TXT.exists():
        return DEFAULT_COOKIES_TXT
    return None


def _make_session(cookies_path: Path) -> requests.Session:
    session = requests.Session()
    if cookies_path.suffix.lower() == ".json":
        with open(cookies_path, encoding="utf-8") as f:
            raw = json.load(f)
        for c in raw:
            name, value, domain = c.get("name",""), c.get("value",""), c.get("domain","")
            if name and value:
                session.cookies.set(name, value, domain=domain)
        print(f"  Cookies (JSON): {len(raw)} entries from {cookies_path.name}")
    else:
        jar = http.cookiejar.MozillaCookieJar()
        jar.load(str(cookies_path), ignore_discard=True, ignore_expires=True)
        session.cookies = jar
        print(f"  Cookies (Netscape): {cookies_path.name}")
    return session


def _parse_vtt(vtt_text: str) -> str:
    """Convert VTT subtitle file to clean plain text, deduplicating repeated lines."""
    lines = vtt_text.splitlines()
    seen = set()
    words = []
    for line in lines:
        # Skip headers, timestamps, blank lines
        if not line.strip() or line.startswith("WEBVTT") or "-->" in line:
            continue
        # Strip inline timing tags like <00:00:01.200><c> and </c>
        clean = re.sub(r"<[^>]+>", "", line).strip()
        if not clean or clean in seen:
            continue
        seen.add(clean)
        words.append(clean)
    return " ".join(words)


def fetch_via_api(video_id: str, cookies_path: Path | None) -> str | None:
    """Try youtube_transcript_api. Returns text or None if IP-blocked."""
    try:
        if cookies_path and cookies_path.exists():
            session = _make_session(cookies_path)
            api = YouTubeTranscriptApi(http_client=session)
        else:
            api = YouTubeTranscriptApi()
        try:
            fetched = api.fetch(video_id)
        except NoTranscriptFound:
            transcript = next(iter(api.list(video_id)))
            fetched = transcript.fetch()
        return " ".join(seg.text for seg in fetched.snippets)
    except TranscriptsDisabled:
        print("  API: transcripts disabled for this video.")
        return None
    except Exception as e:
        if "RequestBlocked" in type(e).__name__ or "IPBlocked" in type(e).__name__:
            print("  API: IP blocked by YouTube. Trying yt-dlp fallback...")
            return None
        print(f"  API error: {e}")
        return None


def fetch_via_ytdlp(video_id: str) -> str | None:
    """Use yt-dlp to download auto-generated subtitles and parse them."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    vtt_pattern = OUT_DIR / f"{video_id}.en.vtt"

    # Remove stale VTT if present
    if vtt_pattern.exists():
        vtt_pattern.unlink()

    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--write-auto-sub",
        "--sub-lang", "en",
        "--skip-download",
        "--sub-format", "vtt",
        "--quiet",
        "--no-warnings",
        "-o", str(OUT_DIR / "%(id)s"),
        url,
    ]

    print("  yt-dlp: downloading auto-captions...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if not vtt_pattern.exists():
        print(f"  yt-dlp: failed — {result.stderr[:200] if result.stderr else 'no output file'}")
        return None

    vtt_text = vtt_pattern.read_text(encoding="utf-8")
    vtt_pattern.unlink()  # clean up raw VTT
    text = _parse_vtt(vtt_text)
    if not text:
        print("  yt-dlp: VTT parsed but empty.")
        return None
    print(f"  yt-dlp: got {len(text.split()):,} words.")
    return text


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    cookies_path = None
    if "--cookies" in args:
        idx = args.index("--cookies")
        cookies_path = Path(args[idx + 1])
        args = [a for a in args if a not in ("--cookies", str(cookies_path))]
    else:
        cookies_path = _find_default_cookies()

    raw = args[0]
    video_id = extract_video_id(raw)
    print(f"Video ID: {video_id}")

    # Method 1: API
    print("Trying youtube_transcript_api...")
    text = fetch_via_api(video_id, cookies_path)

    # Method 2: yt-dlp fallback
    if text is None:
        text = fetch_via_ytdlp(video_id)

    if text is None:
        print("ERROR: Both methods failed.")
        print("Options: use a VPN, switch to mobile hotspot, or paste the transcript manually.")
        sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{video_id}.txt"
    out_path.write_text(text, encoding="utf-8")

    print(f"Saved: {out_path}")
    print(f"Words: {len(text.split()):,}")


if __name__ == "__main__":
    main()
