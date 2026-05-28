"""
calibrate.py -- Scoring calibration tool.

Shows machine scores vs. Emmanuel's gut scores side by side.
After 10+ calibrations, prints weight adjustment recommendations.

Usage:
  python scripts/calibrate.py                   # start calibration session
  python scripts/calibrate.py --report          # show calibration history + recommendations
  python scripts/calibrate.py --adjust          # auto-apply recommended weight changes
"""

import sys
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
CAL_LOG = DATA_DIR / "calibration_log.jsonl"
JOBS_ARCHIVE = ROOT / "hephzibah-brain-temp" / "upwork" / "jobs" / "archive"


def load_calibration_log() -> list[dict]:
    if not CAL_LOG.exists():
        return []
    entries = []
    with open(CAL_LOG) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries


def save_calibration(entry: dict) -> None:
    with open(CAL_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def list_scored_jobs() -> list[Path]:
    """Find all job cards with composite scores."""
    if not JOBS_ARCHIVE.exists():
        return []
    return sorted(JOBS_ARCHIVE.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)


def extract_score_from_card(card_path: Path) -> int | None:
    """Extract composite_score from job card frontmatter."""
    content = card_path.read_text(encoding="utf-8")
    for line in content.split("\n"):
        if line.startswith("composite_score:"):
            try:
                return int(line.split(":")[1].strip())
            except ValueError:
                pass
    return None


def run_calibration_session() -> None:
    jobs = list_scored_jobs()
    if not jobs:
        print("No scored job cards found.")
        print("Run 'python scripts/intake.py' first to evaluate some jobs.")
        return

    existing_log = load_calibration_log()
    already_calibrated = {e["slug"] for e in existing_log}

    pending = [j for j in jobs if j.stem not in already_calibrated]

    if not pending:
        print(f"All {len(jobs)} job cards already calibrated.")
        print("Run 'python scripts/calibrate.py --report' to see results.")
        return

    print(f"\nCALIBRATION SESSION")
    print(f"Pending: {len(pending)} job cards to calibrate")
    print("Rate each job 0-100 based on your gut. 'q' to quit.\n")

    calibrated = 0
    for card in pending[:10]:  # max 10 per session
        machine_score = extract_score_from_card(card)
        if machine_score is None:
            continue

        title_line = ""
        for line in card.read_text(encoding="utf-8").split("\n"):
            if line.startswith("name:"):
                title_line = line.split(":", 1)[1].strip().strip('"')
                break

        print(f"Job: {title_line or card.stem}")
        print(f"Machine score: {machine_score}/100")
        print(f"Card: {card.name}")

        while True:
            gut = input("Your score (0-100) or 'q' to quit: ").strip().lower()
            if gut == "q":
                break
            try:
                gut_score = int(gut)
                if 0 <= gut_score <= 100:
                    break
                print("Enter a number 0-100")
            except ValueError:
                print("Enter a number 0-100 or 'q'")

        if gut == "q":
            break

        delta = machine_score - gut_score
        entry = {
            "date": datetime.now().date().isoformat(),
            "slug": card.stem,
            "title": title_line,
            "machine_score": machine_score,
            "emmanuel_score": gut_score,
            "delta": delta,
        }
        save_calibration(entry)
        calibrated += 1

        direction = "too high" if delta > 0 else "too low" if delta < 0 else "exact"
        print(f"  Logged. Machine was {abs(delta)} points {direction}.\n")

    print(f"\nCalibrated {calibrated} jobs this session.")
    if calibrated >= 3:
        print("Run 'python scripts/calibrate.py --report' to see patterns.")


def calibration_report() -> None:
    log = load_calibration_log()
    if not log:
        print("No calibration data yet. Run calibration session first.")
        return

    total = len(log)
    deltas = [e["delta"] for e in log]
    avg_delta = sum(deltas) / total
    abs_avg = sum(abs(d) for d in deltas) / total

    print(f"\nCALIBRATION REPORT")
    print(f"{'='*50}")
    print(f"Total calibrations:     {total}")
    print(f"Avg delta (machine-gut): {avg_delta:+.1f} pts")
    print(f"Avg absolute error:      {abs_avg:.1f} pts")

    if abs_avg <= 10:
        print(f"Accuracy: GOOD (within 10 pts on average)")
    elif abs_avg <= 20:
        print(f"Accuracy: FAIR (within 20 pts -- keep calibrating)")
    else:
        print(f"Accuracy: NEEDS WORK (>{abs_avg:.0f} pts off -- adjust weights)")

    print(f"\nRECENT CALIBRATIONS:")
    print(f"{'Title':<40} {'Machine':>8} {'Gut':>6} {'Delta':>7}")
    print("-" * 65)
    for e in log[-10:]:
        title = (e.get("title") or e.get("slug", ""))[:38]
        print(f"{title:<40} {e['machine_score']:>8} {e['emmanuel_score']:>6} {e['delta']:>+7}")

    # Bias detection
    print(f"\nBIAS ANALYSIS:")
    high_machine = [e for e in log if e["delta"] > 15]
    low_machine = [e for e in log if e["delta"] < -15]

    if len(high_machine) > len(log) * 0.4:
        print(f"  Machine scores TOO HIGH vs gut ({len(high_machine)}/{total} jobs).")
        print(f"  Consider: harder client_quality or job_quality thresholds.")
    elif len(low_machine) > len(log) * 0.4:
        print(f"  Machine scores TOO LOW vs gut ({len(low_machine)}/{total} jobs).")
        print(f"  Consider: relaxing scoring or reviewing red flag triggers.")
    else:
        print(f"  No strong bias detected. Scoring is balanced.")

    if total < 10:
        print(f"\n  Need {10 - total} more calibrations for reliable recommendations.")


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--report" in args:
        calibration_report()
    elif "--adjust" in args:
        print("ERROR: --adjust is not yet implemented.", file=sys.stderr)
        print("Review the --report output and manually adjust weights in qualify.py.", file=sys.stderr)
        sys.exit(1)
    else:
        run_calibration_session()
        if load_calibration_log():
            print("\nRun 'python scripts/calibrate.py --report' to see accuracy.")
