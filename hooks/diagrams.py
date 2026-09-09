"""MkDocs hook: replace mermaid code blocks with their rendered PNG when one exists.

Rendered images are what allow posts to be imported into Medium and dev.to,
which cannot run the browser-side mermaid renderer. If a diagram has not been
rendered yet, the mermaid block is left alone and the site draws it live.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from diagrams import diagram_path, find_mermaid_blocks  # noqa: E402


def on_page_markdown(markdown, page, config, files):
    out = markdown
    for match, source in reversed(list(find_mermaid_blocks(markdown))):
        png = diagram_path(source)
        if not png.exists():
            continue
        url = config["site_url"].rstrip("/") + "/assets/diagrams/" + png.name
        replacement = f'<figure class="diagram" markdown="1">\n![Diagram]({url})\n</figure>'
        out = out[: match.start()] + replacement + out[match.end():]
    return out
