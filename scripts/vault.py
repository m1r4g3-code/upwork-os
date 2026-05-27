"""
vault.py — Brain read/write operations.

Handles reading nodes, updating frontmatter, creating new nodes, and git sync.
Claude uses this to write memory nodes back to the brain.

Usage:
  python scripts/vault.py read <node-slug>
  python scripts/vault.py write <node-slug> --data '{"key": "value"}'
  python scripts/vault.py create <node-slug> --type <entity_type> --sensitivity <level>
  python scripts/vault.py commit "<message>"
  python scripts/vault.py sync   # pull + push
"""

import sys
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent
BRAIN = ROOT / "hephzibah-brain-temp"

DOMAIN_PATHS = {
    "me": BRAIN / "me",
    "concepts": BRAIN / "concepts",
    "outreach": BRAIN / "outreach",
    "upwork": BRAIN / "upwork",
    "clients": BRAIN / "clients",
    "learning": BRAIN / "learning",
    "content": BRAIN / "content",
}

SENSITIVITY_LEVELS = ["public", "private", "sensitive"]
ENTITY_TYPES = ["person", "company", "tool", "concept", "platform", "skill", "place", "domain", "job", "proposal"]


def find_node(slug: str) -> Path | None:
    """Find a node file by slug across all brain domains."""
    slug_variants = [slug, slug.replace("-", "_"), slug.replace("_", "-")]
    for domain_path in DOMAIN_PATHS.values():
        for variant in slug_variants:
            candidates = list(domain_path.rglob(f"{variant}.md"))
            if candidates:
                return candidates[0]
    # Try direct path
    direct = BRAIN / f"{slug}.md"
    if direct.exists():
        return direct
    return None


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from markdown content."""
    if not content.startswith("---"):
        return {}, content

    end = content.find("---", 3)
    if end == -1:
        return {}, content

    fm_text = content[3:end].strip()
    body = content[end + 3:].strip()

    fm = {}
    current_key = None
    current_list = None

    for line in fm_text.split("\n"):
        if not line.strip():
            continue
        if line.startswith("  ") and current_list is not None:
            current_list.append(line.strip().lstrip("- "))
        elif ":" in line and not line.startswith(" "):
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            if val == "":
                current_list = []
                fm[key] = current_list
                current_key = key
            else:
                current_list = None
                if val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                elif val.lower() == "true":
                    val = True
                elif val.lower() == "false":
                    val = False
                elif val.isdigit():
                    val = int(val)
                fm[key] = val
                current_key = key

    return fm, body


def format_frontmatter(fm: dict) -> str:
    """Format a dict back to YAML frontmatter."""
    lines = ["---"]
    for key, val in fm.items():
        if isinstance(val, list):
            if not val:
                lines.append(f"{key}: []")
            else:
                lines.append(f"{key}:")
                for item in val:
                    if isinstance(item, dict):
                        lines.append(f"  - target: \"{item.get('target', '')}\"")
                        for k, v in item.items():
                            if k != "target":
                                lines.append(f"    {k}: {json.dumps(v) if isinstance(v, str) else v}")
                    else:
                        lines.append(f"  - {item}")
        elif isinstance(val, bool):
            lines.append(f"{key}: {'true' if val else 'false'}")
        elif isinstance(val, dict):
            lines.append(f"{key}:")
            for k, v in val.items():
                lines.append(f"  {k}: {v}")
        elif isinstance(val, str) and any(c in val for c in [":", "#", "["]):
            lines.append(f'{key}: "{val}"')
        else:
            lines.append(f"{key}: {val}")
    lines.append("---")
    return "\n".join(lines)


def read_node(slug: str) -> None:
    """Read and print a brain node."""
    node = find_node(slug)
    if not node:
        print(f"ERROR: Node '{slug}' not found in brain.", file=sys.stderr)
        sys.exit(1)

    content = node.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(content)
    print(f"# Node: {node.relative_to(BRAIN)}")
    print(f"# Sensitivity: {fm.get('sensitivity', 'unknown')}")
    print(f"# Type: {fm.get('entity_type', 'unknown')}")
    print()
    print(content)


def update_node_frontmatter(slug: str, updates: dict) -> None:
    """Update specific frontmatter fields in a node."""
    node = find_node(slug)
    if not node:
        print(f"ERROR: Node '{slug}' not found.", file=sys.stderr)
        sys.exit(1)

    content = node.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(content)
    fm.update(updates)
    fm["last_updated"] = datetime.now().date().isoformat()

    new_content = format_frontmatter(fm) + "\n\n" + body
    node.write_text(new_content, encoding="utf-8")
    print(f"Updated: {node.relative_to(BRAIN)}")


def append_to_node(slug: str, section_header: str, content: str) -> None:
    """Append content to a node (append-only rule)."""
    node = find_node(slug)
    if not node:
        print(f"ERROR: Node '{slug}' not found.", file=sys.stderr)
        sys.exit(1)

    existing = node.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(existing)
    fm["last_updated"] = datetime.now().date().isoformat()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    append_text = f"\n\n### {section_header} — {timestamp}\n\n{content}"

    new_content = format_frontmatter(fm) + "\n\n" + body + append_text
    node.write_text(new_content, encoding="utf-8")
    print(f"Appended to: {node.relative_to(BRAIN)}")


def create_node(slug: str, domain: str, entity_type: str, sensitivity: str, name: str = "") -> None:
    """Create a new node from scratch."""
    if entity_type not in ENTITY_TYPES:
        print(f"ERROR: Invalid entity_type '{entity_type}'. Use: {ENTITY_TYPES}", file=sys.stderr)
        sys.exit(1)
    if sensitivity not in SENSITIVITY_LEVELS:
        print(f"ERROR: Invalid sensitivity '{sensitivity}'. Use: {SENSITIVITY_LEVELS}", file=sys.stderr)
        sys.exit(1)

    domain_path = DOMAIN_PATHS.get(domain, BRAIN / domain)
    domain_path.mkdir(parents=True, exist_ok=True)
    node_path = domain_path / f"{slug}.md"

    if node_path.exists():
        print(f"ERROR: Node already exists at {node_path}", file=sys.stderr)
        sys.exit(1)

    fm = {
        "sensitivity": sensitivity,
        "entity_type": entity_type,
        "name": name or slug.replace("-", " ").title(),
        "aliases": [],
        "last_updated": datetime.now().date().isoformat(),
        "relationships": [],
    }

    content = format_frontmatter(fm) + f"\n\n# {fm['name']}\n\n[Content here]\n\n---\n\n## Wikilinks\n\n[[{slug}]]\n"
    node_path.write_text(content, encoding="utf-8")
    print(f"Created: {node_path.relative_to(BRAIN)}")


def git_sync(message: str = "") -> None:
    """Pull, stage, commit, and push brain changes."""
    try:
        # Pull first
        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            cwd=BRAIN, capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"WARNING: git pull issue: {result.stderr}", file=sys.stderr)

        if not message:
            message = f"upwork: sync brain — {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        # Stage all changes in brain
        subprocess.run(["git", "add", "."], cwd=BRAIN, check=True)

        # Check if there's anything to commit
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=BRAIN, capture_output=True, text=True
        )
        if not status.stdout.strip():
            print("Brain is up to date. Nothing to commit.")
            return

        # Commit
        subprocess.run(["git", "commit", "-m", message], cwd=BRAIN, check=True)

        # Push
        result = subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=BRAIN, capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"Brain synced: '{message}'")
        else:
            print(f"Push failed (may need auth): {result.stderr}", file=sys.stderr)

    except subprocess.CalledProcessError as e:
        print(f"Git error: {e}", file=sys.stderr)


def commit_brain(message: str) -> None:
    """Stage and commit current brain changes without pushing."""
    subprocess.run(["git", "add", "."], cwd=BRAIN, check=True)
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=BRAIN, capture_output=True, text=True
    )
    if not status.stdout.strip():
        print("Nothing to commit.")
        return
    subprocess.run(["git", "commit", "-m", message], cwd=BRAIN, check=True)
    print(f"Committed: '{message}'")


if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        print(__doc__)
        sys.exit(0)

    command = args[0]

    if command == "read" and len(args) >= 2:
        read_node(args[1])

    elif command == "append" and len(args) >= 4:
        append_to_node(args[1], args[2], args[3])

    elif command == "update" and len(args) >= 3:
        try:
            updates = json.loads(args[2])
            update_node_frontmatter(args[1], updates)
        except json.JSONDecodeError:
            print("ERROR: --data must be valid JSON", file=sys.stderr)
            sys.exit(1)

    elif command == "create" and len(args) >= 5:
        create_node(
            slug=args[1],
            domain=args[2],
            entity_type=args[3],
            sensitivity=args[4],
            name=" ".join(args[5:]) if len(args) > 5 else ""
        )

    elif command == "commit" and len(args) >= 2:
        commit_brain(" ".join(args[1:]))

    elif command == "sync":
        message = " ".join(args[1:]) if len(args) > 1 else ""
        git_sync(message)

    else:
        print(__doc__)
        sys.exit(1)
