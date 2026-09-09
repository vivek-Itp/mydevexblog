#!/usr/bin/env python3
"""Render every mermaid block in the blog posts to a PNG under docs/assets/diagrams/.

Uses mermaid-cli through npx, so Node.js is required. A rendered PNG is kept
in the repo and reused until the diagram source changes. Run it after writing
or editing a post that contains a diagram:

    python tools/render_diagrams.py
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagrams import ROOT, DIAGRAM_DIR, diagram_path, find_mermaid_blocks  # noqa: E402

POSTS = ROOT / "docs" / "blog" / "posts"
PUPPETEER_CONFIG = ROOT / "tools" / "puppeteer-config.json"

# Prefer a preinstalled browser when one is available; otherwise mermaid-cli
# downloads its own.
for candidate in (
    os.environ.get("PUPPETEER_EXECUTABLE_PATH"),
    "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
    shutil.which("chromium"),
    shutil.which("chromium-browser"),
    shutil.which("google-chrome"),
):
    if candidate and Path(candidate).exists():
        os.environ["PUPPETEER_EXECUTABLE_PATH"] = candidate
        break


def render(source: str, out: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "diagram.mmd"
        src.write_text(source.strip() + "\n", encoding="utf-8")
        cmd = [
            "npx", "--yes", "@mermaid-js/mermaid-cli",
            "-i", str(src), "-o", str(out),
            "-p", str(PUPPETEER_CONFIG),
            "-b", "white", "-s", "2", "-t", "neutral",
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)


def main() -> int:
    DIAGRAM_DIR.mkdir(parents=True, exist_ok=True)
    rendered = skipped = 0
    for post in sorted(POSTS.glob("*.md")):
        for _, source in find_mermaid_blocks(post.read_text(encoding="utf-8")):
            out = diagram_path(source)
            if out.exists():
                skipped += 1
                continue
            print(f"rendering {out.name} from {post.name}")
            try:
                render(source, out)
                rendered += 1
            except subprocess.CalledProcessError as e:
                print(e.stderr, file=sys.stderr)
                print(f"FAILED: {post.name}", file=sys.stderr)
                return 1
    print(f"done: {rendered} rendered, {skipped} already up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
