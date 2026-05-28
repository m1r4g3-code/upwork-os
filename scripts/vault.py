"""
vault.py -- Brain read/write operations.

Handles reading nodes, updating frontmatter, creating new nodes, and git sync.
Claude uses this to write memory nodes back to the brain.

Usage:
  python scripts/vault.py read <node-slug>
  python scripts/vault.py update <node-slug> '{"key": "value"}'
  python scripts/vault.py append <node-slug> <section-header> <content>
  python scripts/vault.py create <node-slug> <domain> <entity_type> <sensitivity> [name]
  python scripts/vault.py commit "<message>"
  python scripts/vault.py sync [message]
"""

import sys
import json
import shutil
import subprocess
import yaml
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
ENTITY_TYPES = [
    "person", "company", "tool", "concept", "platform",
    "skill", "place", "domain", "job", "proposal",
]

# In-memory node index -- built once, invalidated on create
_node_index: dict[str, Path] = {}


def _build_index() -> None:
    _node_index.clear()
    for domain in DOMAIN_PATHS.values():
        if domain.exists():
            for f in domain.rglob("*.md"):
                _node_index[f.stem] = f
    for f in BRAIN.glob("*.md"):
        _node_index[f.stem] = f


def find_node(slug: str) -> Path | None:
    if not _node_index:
        _build_index()
    if slug in _node_index:
        return _node_index[slug]
    alt = slug.replace("-", "_") if "-" in slug else slug.replace("_", "-")
    return _node_index.get(alt)


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter using pyyaml. Safe round-trips nested structures."""
    if not content.startswith("---"):
        return {}, content
    end = content.find("---", 3)
    if end == -1:
        return {}, content
    try:
        fm = yaml.safe_load(content[3:end]) or {}
    except yaml.YAMLError as e:
        print(f"WARNING: YAML parse error in frontmatter: {e}", file=sys.stderr)
        fm = {}
    body = content[end + 3:].strip()
    return fm, body


def format_frontmatter(fm: dict) -> str:
    """Serialize dict to YAML frontmatter block. Preserves insertion order."""
    try:
        yaml_str = yaml.dump(
            fm,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            indent=2,
        )
    except yaml.YAMLError as e:
        print(f"WARNING: YAML serialization error: {e}", file=sys.stderr)
        yaml_str = ""
    return f"---\n{yaml_str}---"


def _atomic_write(path: Path, content: str) -> None:
    """Write to a temp file then rename -- prevents partial writes on crash."""
    tmp = path.with_suffix(".tmp")
    try:
        tmp.write_text(content, encoding="utf-8")
        shutil.move(str(tmp), str(path))
    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise


def read_node(slug: str) -> None:
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
    node = find_node(slug)
    if not node:
        print(f"ERROR: Node '{slug}' not found.", file=sys.stderr)
        sys.exit(1)
    content = node.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(content)
    fm.update(updates)
    fm["last_updated"] = datetime.now().date().isoformat()
    new_content = format_frontmatter(fm) + "\n\n" + body
    _atomic_write(node, new_content)
    print(f"Updated: {node.relative_to(BRAIN)}")


def append_to_node(slug: str, section_header: str, content: str) -> None:
    node = find_node(slug)
    if not node:
        print(f"ERROR: Node '{slug}' not found.", file=sys.stderr)
        sys.exit(1)
    existing = node.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(existing)
    fm["last_updated"] = datetime.now().date().isoformat()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    append_text = f"\n\n### {section_header} -- {timestamp}\n\n{content}"
    new_content = format_frontmatter(fm) + "\n\n" + body + append_text
    _atomic_write(node, new_content)
    print(f"Appended to: {node.relative_to(BRAIN)}")


def create_node(slug: str, domain: str, entity_type: str, sensitivity: str, name: str = "") -> None:
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
    content = (
        format_frontmatter(fm)
        + f"\n\n# {fm['name']}\n\n[Content here]\n\n---\n\n## Wikilinks\n\n[[{slug}]]\n"
    )
    _atomic_write(node_path, content)
    _node_index[slug] = node_path  # keep index consistent
    print(f"Created: {node_path.relative_to(BRAIN)}")


def git_sync(message: str = "") -> None:
    try:
        result = subprocess.run(
            ["git", "pull", "origin", "main"],
            cwd=BRAIN, capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"WARNING: git pull issue: {result.stderr}", file=sys.stderr)

        if not message:
            message = f"upwork: sync brain -- {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        subprocess.run(["git", "add", "."], cwd=BRAIN, check=True)
        status = subprocess.run(
            ["git", "status", "--porcelain"], cwd=BRAIN, capture_output=True, text=True,
        )
        if not status.stdout.strip():
            print("Brain is up to date. Nothing to commit.")
            return

        subprocess.run(["git", "commit", "-m", message], cwd=BRAIN, check=True)
        result = subprocess.run(
            ["git", "push", "origin", "main"], cwd=BRAIN, capture_output=True, text=True,
        )
        if result.returncode == 0:
            print(f"Brain synced: '{message}'")
        else:
            print(f"Push failed (may need auth): {result.stderr}", file=sys.stderr)
    except subprocess.CalledProcessError as e:
        print(f"Git error: {e}", file=sys.stderr)


def commit_brain(message: str) -> None:
    subprocess.run(["git", "add", "."], cwd=BRAIN, check=True)
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=BRAIN, capture_output=True, text=True,
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
            print("ERROR: data must be valid JSON", file=sys.stderr)
            sys.exit(1)

    elif command == "create" and len(args) >= 5:
        create_node(
            slug=args[1],
            domain=args[2],
            entity_type=args[3],
            sensitivity=args[4],
            name=" ".join(args[5:]) if len(args) > 5 else "",
        )

    elif command == "commit" and len(args) >= 2:
        commit_brain(" ".join(args[1:]))

    elif command == "sync":
        message = " ".join(args[1:]) if len(args) > 1 else ""
        git_sync(message)

    else:
        print(__doc__)
        sys.exit(1)
