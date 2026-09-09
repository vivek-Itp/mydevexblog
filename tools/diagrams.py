"""Shared helpers for turning mermaid code blocks in posts into PNG images.

Every mermaid block is identified by a short hash of its source, so the same
diagram always maps to the same file name and nothing is rendered twice.
"""
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIAGRAM_DIR = ROOT / "docs" / "assets" / "diagrams"
MERMAID_RE = re.compile(r"^```mermaid[ \t]*\n(.*?)\n```[ \t]*$", re.M | re.S)


def diagram_id(source: str) -> str:
    return hashlib.sha256(source.strip().encode("utf-8")).hexdigest()[:12]


def diagram_path(source: str) -> Path:
    return DIAGRAM_DIR / f"{diagram_id(source)}.png"


def find_mermaid_blocks(markdown: str):
    """Yield (match, source) for every mermaid fence in the markdown."""
    for m in MERMAID_RE.finditer(markdown):
        yield m, m.group(1)
