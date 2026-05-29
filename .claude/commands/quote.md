# /quote — Pricing Calculator + SOW Investment Block

## Role

You generate pricing for a project — either a bid recommendation against a posted budget, or a full tiered SOW investment block after a discovery call. You do not guess. You run the calculator and interpret the output.

---

## Two Modes

### Bid Mode — "Client posted a budget. Should I bid? At what price?"

```
python scripts/quote.py --bid [client_budget] --type [project_type] --complexity [level]
```

**Project types:** `integration` · `automation` · `pipeline` · `agent` · `fullstack` · `scraper` · `crm` · `custom`

**Complexity:** `simple` · `medium` · `complex` · `enterprise`

**Example:**
```
python scripts/quote.py --bid 1500 --type automation --complexity medium
```

Read the output:
- Whether the budget is viable at Emmanuel's rate
- The recommended bid price
- Whether to bid at all, counter, or skip on price

---

### SOW Mode — "Discovery call done. Generate the investment section."

```
python scripts/quote.py --sow --type [project_type] --complexity [level]
```

With tool cost estimation (for automation projects):
```
python scripts/quote.py --sow --type automation --complexity complex --tools "n8n:0.05,openai:0.02" --volume 200
```

With manual hours (for custom scope):
```
python scripts/quote.py --sow --type custom --hours 40 --complexity medium
```

This outputs the full tiered pricing block — Core / Full / Premium tiers — ready to paste into the SOW document.

---

## After Running

1. Read the calculator output
2. Apply strategic judgment:
   - Is the budget range realistic for the client's stated needs?
   - Which tier should Emmanuel recommend? (Usually Full — Core looks cheap, Premium needs more trust)
   - Payment schedule: 40% upfront / 30% midpoint / 30% on completion (Ramshaw model)
3. Output the investment block formatted for the SOW:

```
INVESTMENT

  Core     $[N]   Essential deliverables only
  Full     $[N]   Core + optimization, docs, 1-week support     ← RECOMMENDED
  Premium  $[N]   Full + 30-day support, training, 1 change order

  Payment: 40% upfront · 30% at midpoint · 30% on delivery
```

4. Save the full quote to `outputs/strategy/YYYY-MM-DD-[client]-[slug]-quote.md`

---

## Pricing Principles

- Never anchor to the client's posted budget — run the calculator from scope and complexity, then compare
- If client budget < Emmanuel's minimum viable price: say so clearly, offer a reduced scope at that price or skip
- The range on any quote should close to a fixed number once Emmanuel reviews the existing work/setup
- Payment terms are non-negotiable: 50% upfront minimum on fixed projects (or 40/30/30 on phased)

---

## When to Run

- Before writing any SOW
- After every discovery call (run within 24 hours while context is fresh)
- When a client asks "how much?" in chat — run this first, then answer
