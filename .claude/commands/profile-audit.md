# /profile-audit — Upwork Profile Algorithmic Audit

## Role

You audit Emmanuel's Upwork profile against the algorithm's actual ranking signals — Ramshaw methodology, not generic advice. You output specific text to use, not vague guidance.

---

## Pipeline

### Step 1 — Run the audit

**Full audit:**
```
python scripts/profile_audit.py
```

**Single section:**
```
python scripts/profile_audit.py --section [title|overview|portfolio|skills|rate|jss]
```

**With current profile data (paste from Upwork):**
```
python scripts/profile_audit.py --profile '{"title": "...", "overview": "...", "rate": 45, "skills": []}'
```

**JSON output (for programmatic use):**
```
python scripts/profile_audit.py --json
```

---

### Step 2 — Read the output

The audit scores 7 sections by algorithm weight:

| Section | Weight | What the algorithm actually rewards |
|---|---|---|
| JSS | 30% | Score ≥ 90 for Top Rated; ≥ 80 for baseline visibility |
| Title | 20% | Keyword format: `Skill | Skill | Outcome/Niche` |
| Overview | 18% | Hook in first 2 lines, keyword density, human voice |
| Portfolio | 15% | Relevant items with keyword-aligned titles |
| Skills | 10% | 20 skills, tiered: core → adjacent → soft |
| Rate | 4% | Market positioning vs. category average |
| Completeness | 3% | Photo, education, all fields filled |

---

### Step 3 — Your strategic layer

After reading the audit output:

**Priority stack:** Which 3 changes would move the needle most in the next 7 days?

**Keyword saturation check:** The Ramshaw method — Emmanuel's target keyword should appear in: profile title, overview, portfolio titles, portfolio descriptions, skills section, work history titles, certifications. Count appearances. Minimum 8-10 times across the profile for the primary keyword to rank.

**The `www` filter note:** Once the profile is optimized, Emmanuel can find high-context jobs by typing `www` in Upwork Advanced Search "Any of these words" field. These are jobs with website URLs — perfect for full-audit Looms and they close at higher rates.

---

### Step 4 — Save the output

```
Save to: outputs/roasts/YYYY-MM-DD-profile-audit.md
```

Format:
```markdown
# Profile Audit — [Date]
**Command:** /profile-audit
**Status:** draft
---

## Overall Score
[weighted total] / 100

## Priority Actions (do these first)
1. [Most impactful — with exact text to use]
2.
3.

## Section Breakdown
[section-by-section findings]

## Exact Text Recommendations
[copy-paste ready title, overview hook, skills list]
```

Also update `hephzibah-brain-temp/upwork/identity/profile.md` with the audit date and priority actions.

---

## When to Run

- Before sending a proposal batch
- After adding new portfolio items
- Weekly while JSS is still building
- Whenever reply rate drops below 30% (that's an algorithm signal problem, not a proposal problem)
