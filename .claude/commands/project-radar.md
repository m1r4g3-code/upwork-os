# /project-radar — Portfolio Project Recommender

## Role

You surface the highest-ROI portfolio projects for Emmanuel to build next, ranked by market demand and portfolio gap. Every project recommendation comes with a full build spec, Loom script, and Upwork headline — ready to execute.

---

## Pipeline

### Step 1 — Run the radar

**Full radar (all projects, ranked):**
```
python scripts/project_radar.py
```

**Top N only:**
```
python scripts/project_radar.py --top 5
```

**Filter by niche:**
```
python scripts/project_radar.py --niche automation
python scripts/project_radar.py --niche fullstack
```

**Filter by build time (quick wins only):**
```
python scripts/project_radar.py --max-hours 12
```

**JSON output:**
```
python scripts/project_radar.py --json
```

---

### Step 2 — Read the output

Each project has:
- **Composite score** (Market Demand 35% + Proof Power 30% + Uniqueness 20% + Time ROI 15%)
- Full build spec (what to build, repo name, README notes)
- 60-second Loom video script (hook → problem → solution → result → CTA)
- Upwork portfolio headline (copy-paste ready)
- Upwork search terms the project attracts

---

### Step 3 — Your strategic layer

After reading the radar output:

**Niche alignment check:** Does the top recommendation align with Emmanuel's active niche in `hephzibah-brain-temp/upwork/identity/niche.md`? If there's a conflict, flag it.

**Keyword saturation:** Which Upwork search terms does this project target? Does Emmanuel already have portfolio items for those terms? Building a second item for the same keyword cluster compounds faster than building for a new term.

**Quick win vs. deep build:** Projects under 12 hours build time are quick wins — they add keyword coverage fast. Complex projects (40+ hours) are slower but carry more proof power. Recommend a mix.

**Loom priority:** Any project with a live demo component should be Loom-first — record the system working, not a screen of code.

---

### Step 4 — Save the output

The radar auto-saves to `outputs/strategy/YYYY-MM-DD-project-radar.md`.

After saving, report:
1. Top 3 recommendations with rationale
2. Which one to build first and why
3. Estimated time investment

---

## When to Run

- When deciding what to build next
- When portfolio feels thin for a specific niche
- Before applying to a new job category (build the proof first)
- Monthly — market demand shifts, project database is updated

---

## Building the Project

Once Emmanuel picks a project:
1. The build spec gives exact instructions (what to code, what the repo should look like)
2. Build it, push to GitHub, deploy a live demo if possible
3. Record the Loom using the provided script
4. Add to Upwork portfolio using the provided headline
5. Add skills from the project's stack to the Skills section

One keyword cluster, deep — this is how Ramshaw ranked #1 for N8N. Not breadth. Depth.
