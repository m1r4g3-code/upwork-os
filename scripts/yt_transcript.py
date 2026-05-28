"""
Fetch a YouTube transcript and save it to sources/transcripts/.

Usage:
  python scripts/yt_transcript.py <youtube_url_or_video_id>
  python scripts/yt_transcript.py <url> --cookies cookies.txt

If YouTube blocks your IP (RequestBlocked error), export your cookies:
  1. Install browser extension "Get cookies.txt LOCALLY" (Chrome/Firefox)
  2. Go to youtube.com while logged in
  3. Click the extension -> Export -> save as cookies.txt in the project root
  4. Re-run (auto-detected) or pass --cookies path/to/cookies.txt

Output: sources/transcripts/<video_id>.txt
"""

import sys
import re
import http.cookiejar
import requests
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

ROOT = Path(__file__).parent.parent
OUT_DIR = ROOT / "sources" / "transcripts"
DEFAULT_COOKIES = ROOT / "cookies.txt"


def extract_video_id(url_or_id: str) -> str:
    patterns = [
        r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url_or_id):
        return url_or_id
    raise ValueError(f"Could not extract video ID from: {url_or_id}")


def _make_session(cookies_path: Path) -> requests.Session:
    jar = http.cookiejar.MozillaCookieJar()
    jar.load(str(cookies_path), ignore_discard=True, ignore_expires=True)
    session = requests.Session()
    session.cookies = jar
    return session


def fetch_transcript(video_id: str, cookies_path: Path = None) -> str:
    if cookies_path and cookies_path.exists():
        print(f"Using cookies: {cookies_path}")
        session = _make_session(cookies_path)
        api = YouTubeTranscriptApi(http_client=session)
    else:
        api = YouTubeTranscriptApi()

    try:
        fetched = api.fetch(video_id)
        segments = fetched.snippets
    except NoTranscriptFound:
        transcript_list = api.list(video_id)
        transcript = next(iter(transcript_list))
        fetched = transcript.fetch()
        segments = fetched.snippets
    return " ".join(seg.text for seg in segments)


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    # Parse --cookies flag
    cookies_path = None
    if "--cookies" in args:
        idx = args.index("--cookies")
        cookies_path = Path(args[idx + 1])
        args = [a for a in args if a not in ("--cookies", str(cookies_path))]
    elif DEFAULT_COOKIES.exists():
        cookies_path = DEFAULT_COOKIES

    raw = args[0]
    video_id = extract_video_id(raw)
    print(f"Video ID: {video_id}")

    try:
        text = fetch_transcript(video_id, cookies_path)
    except TranscriptsDisabled:
        print("ERROR: Transcripts are disabled for this video.")
        sys.exit(1)
    except Exception as e:
        if "RequestBlocked" in type(e).__name__ or "IPBlocked" in type(e).__name__:
            print("ERROR: YouTube is blocking this IP.")
            print("Fix: export cookies from your browser and save to sources/yt_cookies.txt")
            print("Then re-run. See script docstring for instructions.")
        else:
            print(f"ERROR: {e}")
        sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{video_id}.txt"
    out_path.write_text(text, encoding="utf-8")

    print(f"Saved: {out_path}")
    print(f"Characters: {len(text):,}")
    print(f"Words: {len(text.split()):,}")


if __name__ == "__main__":
    main()
