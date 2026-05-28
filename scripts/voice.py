"""
voice.py -- Proposal voice calibration engine.

Scores a proposal draft against Emmanuel's voice guide.
Detects AI-smell phrases, checks structure, validates length.

Usage:
  python scripts/voice.py "<proposal text>"
  python scripts/voice.py --file <path-to-draft.txt>
  python scripts/voice.py --json "<proposal text>"   # output JSON
"""

import sys
import re
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
BRAIN = ROOT / "hephzibah-brain-temp"
VOICE_GUIDE = BRAIN / "upwork" / "identity" / "voice.md"
BEST_PROPOSALS = BRAIN / "upwork" / "proposals" / "best"

AI_SMELL_PHRASES = [
    "i would be delighted",
    "i am passionate about",
    "as per your requirements",
    "as per the requirements",
    "i hope to hear from you",
    "i look forward to hearing",
    "please feel free to reach out",
    "i would love the opportunity",
    "i am well-versed",
    "i am highly motivated",
    "i am a dedicated",
    "i believe i would be a perfect fit",
    "i am excited to",
    "thank you for considering",
    "i would be happy to discuss",
    "i am confident that",
    "leverage my expertise",
    "leveraging",
    "synergy",
    "holistic approach",
    "robust solution",
    "best-in-class",
    "cutting-edge",
    "going forward",
    "at the end of the day",
    "move the needle",
    "i think i could",
    "i believe i can",
    "i will try to",
    "i would try",
    "given the opportunity",
    "i have extensive experience",
    "with my expertise",
    "seasoned professional",
    "i have been working in",
    "as an experienced",
]

WEAKNESS_SIGNALS = [
    "i think i could",
    "i believe i can",
    "i'm not sure if",
    "if this sounds good to you",
    "i would try",
    "hopefully",
    "if you feel i'm a good fit",
]

CORPORATE_JARGON = [
    "leverage", "synergy", "holistic", "robust", "scalable", "best-in-class",
    "cutting-edge", "going forward", "move the needle", "circle back",
    "deep dive", "bandwidth", "low-hanging fruit", "paradigm shift",
]

STRONG_SIGNALS = [
    r"\d+",  # specific numbers
    r"\$\d+",  # money amounts
    r"built",
    r"shipped",
    r"delivered",
    r"reduced",
    r"increased",
    r"from .* to .*",
]

def score_hook(text: str) -> tuple[int, list[str]]:
    """Score the opening line."""
    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    if not lines:
        return 1, ["No content"]

    first_line = lines[0].lower()
    issues = []
    score = 7

    if first_line.startswith("i ") or first_line.startswith("hi,") or first_line.startswith("hello"):
        score -= 4
        issues.append("First word is 'I', 'Hi', or 'Hello' -- starts with you, not them")

    if any(phrase in first_line for phrase in ["i'm excited", "i am excited", "i came across",
                                                "i would like", "i'm interested", "i saw your"]):
        score -= 3
        issues.append("Generic opening -- sounds like every other proposal")

    if len(lines[0]) > 200:
        score -= 1
        issues.append("Hook is too long -- should be one punchy sentence")

    if "?" in lines[0]:
        score += 1

    return max(1, min(10, score)), issues


def score_voice(text: str) -> tuple[int, list[str], list[str]]:
    """Score overall voice quality. Returns (score, issues, good_signals)."""
    text_lower = text.lower()
    issues = []
    good_signals = []
    score = 8

    # AI-smell check
    found_ai_phrases = []
    for phrase in AI_SMELL_PHRASES:
        if phrase in text_lower:
            found_ai_phrases.append(f'"{phrase}"')
            score -= 1.5

    if found_ai_phrases:
        issues.append(f"AI-smell phrases detected: {', '.join(found_ai_phrases[:4])}")

    # Weakness signals
    found_weak = [p for p in WEAKNESS_SIGNALS if p in text_lower]
    if found_weak:
        score -= 2
        issues.append(f"Weakness signals: {', '.join([f'\"{p}\"' for p in found_weak[:2]])}")

    # Corporate jargon
    found_jargon = [j for j in CORPORATE_JARGON if re.search(r'\b' + re.escape(j) + r'\b', text_lower)]
    if found_jargon:
        score -= 1
        issues.append(f"Corporate jargon: {', '.join(found_jargon[:3])}")

    # Specificity check (good)
    has_numbers = bool(re.search(r'\d+', text))
    if has_numbers:
        score += 0.5
        good_signals.append("Contains specific numbers (proof)")

    has_money = bool(re.search(r'\$\d+', text))
    if has_money:
        score += 0.5
        good_signals.append("Specific monetary amount (proof)")

    action_verbs = ["built", "shipped", "delivered", "reduced", "increased", "solved",
                    "fixed", "automated", "integrated", "deployed"]
    found_verbs = [v for v in action_verbs if v in text_lower]
    if found_verbs:
        score += 0.5
        good_signals.append(f"Action verbs present: {', '.join(found_verbs[:3])}")

    # Question check (should have one)
    question_count = text.count("?")
    if question_count == 1:
        score += 0.5
        good_signals.append("One sharp question (good CTA structure)")
    elif question_count == 0:
        score -= 1
        issues.append("No question -- proposal doesn't open a conversation")
    elif question_count > 2:
        score -= 1
        issues.append(f"{question_count} questions -- too many, overwhelms the client")

    return max(1, min(10, round(score))), issues, good_signals


def score_diagnosis(text: str) -> tuple[int, list[str]]:
    """Score how well the proposal identifies the real problem."""
    text_lower = text.lower()
    issues = []
    score = 5

    # Indicators of real diagnosis
    diagnosis_signals = [
        r"the real (issue|problem|challenge|risk)",
        r"what this (actually|really) means",
        r"this (usually|often|typically) happens when",
        r"the (underlying|root) cause",
        r"what you're (actually|really) dealing with",
        r"this isn't just",
        r"beyond (just|the obvious)",
    ]
    found_diagnosis = [s for s in diagnosis_signals if re.search(s, text_lower)]
    if found_diagnosis:
        score += 3
    elif any(w in text_lower for w in ["because", "which means", "this suggests", "typically"]):
        score += 1

    # Generic description (no diagnosis)
    generic_signals = [
        "i can help you", "i can assist", "i can build", "i can create",
        "i have experience with", "i am skilled in",
    ]
    found_generic = [g for g in generic_signals if g in text_lower]
    if len(found_generic) >= 2:
        score -= 2
        issues.append("Mostly capability-claiming, not diagnosing -- '{}' etc.".format(found_generic[0]))

    # Specificity
    if re.search(r'\d+', text):
        score += 1

    return max(1, min(10, score)), issues


def score_length(text: str) -> tuple[int, list[str]]:
    """Score length appropriateness."""
    word_count = len(text.split())
    issues = []

    if 150 <= word_count <= 250:
        return 10, [f"Good length: {word_count} words"]
    elif 120 <= word_count < 150:
        return 7, [f"Slightly short ({word_count} words). Min 150."]
    elif 250 < word_count <= 320:
        return 6, [f"Slightly long ({word_count} words). Max 250."]
    elif word_count < 120:
        return 3, [f"Too short ({word_count} words). Diagnosis is thin."]
    else:
        return 2, [f"Too long ({word_count} words). Cut to 250 max."]


def score_cta(text: str) -> tuple[int, list[str]]:
    """Score the call-to-action quality."""
    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    if not lines:
        return 1, ["No content"]

    last_line = lines[-1].lower()
    issues = []
    score = 6

    if any(phrase in last_line for phrase in [
        "hope to hear", "look forward to hearing", "please feel free",
        "don't hesitate to contact", "available for a call", "happy to discuss further"
    ]):
        score -= 4
        issues.append(f"Weak CTA: '{lines[-1]}' -- this is a plea, not a conversation opener")

    if "?" in last_line:
        score += 3
        if len(last_line) > 30:
            issues.append("Good: ends with a specific question")
    elif "?" not in text[-200:]:
        score -= 2
        issues.append("No question near the end -- proposal doesn't open a conversation")

    generic_ctas = ["when can we start", "what are your thoughts", "let me know what you think"]
    if any(g in last_line for g in generic_ctas):
        score -= 1
        issues.append("CTA question is generic -- make it specific to their situation")

    return max(1, min(10, score)), issues


def analyze_proposal(text: str) -> dict:
    """Full voice analysis. Returns structured report."""
    hook_score, hook_issues = score_hook(text)
    voice_score, voice_issues, voice_good = score_voice(text)
    diag_score, diag_issues = score_diagnosis(text)
    length_score, length_issues = score_length(text)
    cta_score, cta_issues = score_cta(text)

    overall = round(hook_score * 0.15 + voice_score * 0.30 + diag_score * 0.25 + length_score * 0.10 + cta_score * 0.20)
    word_count = len(text.split())

    return {
        "overall_voice_score": overall,
        "send_ready": overall >= 7,
        "word_count": word_count,
        "scores": {
            "hook": hook_score,
            "voice": voice_score,
            "diagnosis": diag_score,
            "length": length_score,
            "cta": cta_score,
        },
        "issues": {
            "hook": hook_issues,
            "voice": voice_issues,
            "diagnosis": diag_issues,
            "length": length_issues,
            "cta": cta_issues,
        },
        "good_signals": voice_good,
    }


def print_report(report: dict) -> None:
    overall = report["overall_voice_score"]
    status = "SEND READY [OK]" if report["send_ready"] else "NEEDS REVISION [FIX]"

    print(f"\n{'='*50}")
    print(f"VOICE SCORE: {overall}/10 -- {status}")
    print(f"Word count: {report['word_count']} (target: 150-250)")
    print(f"{'='*50}")

    scores = report["scores"]
    print(f"\nSCORE BREAKDOWN:")
    print(f"  Hook (first line):    {scores['hook']}/10")
    print(f"  Voice authenticity:   {scores['voice']}/10")
    print(f"  Diagnosis quality:    {scores['diagnosis']}/10")
    print(f"  Length:               {scores['length']}/10")
    print(f"  CTA quality:          {scores['cta']}/10")

    all_issues = []
    for category, issues in report["issues"].items():
        all_issues.extend([(category, issue) for issue in issues if "Good" not in issue])

    if all_issues:
        print(f"\nISSUES TO FIX:")
        for category, issue in all_issues:
            print(f"  [{category.upper()}] {issue}")

    if report["good_signals"]:
        print(f"\nGOOD SIGNALS:")
        for signal in report["good_signals"]:
            print(f"  [+] {signal}")

    if overall < 7:
        print(f"\nDO NOT SEND. Fix the issues above. Target score: 7+")
    elif overall < 8:
        print(f"\nSend with minor cleanup.")
    else:
        print(f"\nStrong proposal. Send it.")
    print()


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        print(__doc__)
        sys.exit(1)

    output_json = False
    text = ""

    if "--json" in args:
        output_json = True
        args = [a for a in args if a != "--json"]

    if args[0] == "--file" and len(args) >= 2:
        text = Path(args[1]).read_text(encoding="utf-8")
    else:
        text = " ".join(args)

    if not text.strip():
        print("ERROR: No proposal text provided.", file=sys.stderr)
        sys.exit(1)

    report = analyze_proposal(text)

    if output_json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)
