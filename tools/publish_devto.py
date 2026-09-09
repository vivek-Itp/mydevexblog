#!/usr/bin/env python3
"""Publish (or update) every published blog post on dev.to.

Runs in the deploy workflow after the site is live. Each post is matched to an
existing dev.to article by its canonical URL, so re-running is safe: new posts
are created, changed posts are updated, nothing is duplicated.

Environment:
    DEVTO_API_KEY   required; if empty the script exits without doing anything
    SITE_URL        base URL of the blog, e.g. https://vivek-itp.github.io/mydevexblog/
    DRY_RUN=1       write the converted markdown to ./devto-preview/ instead of publishing
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from diagrams import ROOT, diagram_path, find_mermaid_blocks  # noqa: E402

POSTS = ROOT / "docs" / "blog" / "posts"
API = "https://dev.to/api"
FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)
ADMONITION_RE = re.compile(r'^!!! +(\w+)(?: +"([^"]*)")?[ \t]*\n((?:(?:    .*|[ \t]*)\n)+)', re.M)


def load_post(path: Path):
    text = path.read_text(encoding="utf-8")
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return None, text
    return yaml.safe_load(m.group(1)) or {}, text[m.end():]


def slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def canonical_url(meta: dict, site_url: str) -> str:
    created = meta["date"]["created"] if isinstance(meta.get("date"), dict) else meta["date"]
    if not isinstance(created, date):
        created = date.fromisoformat(str(created))
    slug = meta.get("slug") or slugify(meta["title"])
    return f"{site_url.rstrip('/')}/blog/{created:%Y/%m/%d}/{slug}/"


def convert_admonitions(md: str) -> str:
    def repl(m):
        kind, title, body = m.group(1), m.group(2), m.group(3)
        lines = [l[4:] if l.startswith("    ") else l.strip() for l in body.strip("\n").split("\n")]
        heading = title or kind.capitalize()
        quoted = [f"> **{heading}**", ">"] + [("> " + l) if l.strip() else ">" for l in lines]
        return "\n".join(quoted) + "\n\n"
    return ADMONITION_RE.sub(repl, md)


def convert_diagrams(md: str, site_url: str) -> str:
    out = md
    for match, source in reversed(list(find_mermaid_blocks(md))):
        png = diagram_path(source)
        if png.exists():
            url = f"{site_url.rstrip('/')}/assets/diagrams/{png.name}"
            rep = f"![Diagram]({url})"
        else:
            rep = "*(Diagram available in the original post.)*"
        out = out[: match.start()] + rep + out[match.end():]
    return out


def to_devto(meta: dict, body: str, site_url: str) -> dict:
    url = canonical_url(meta, site_url)
    md = body.replace("<!-- more -->", "").strip()
    md = convert_admonitions(md)
    md = convert_diagrams(md, site_url)
    md = re.sub(r"\n{3,}", "\n\n", md)
    md += f"\n\n---\n\n*Originally published at [{url}]({url}).*\n"
    tags = []
    for t in meta.get("tags") or []:
        clean = re.sub(r"[^a-z0-9]", "", str(t).lower())
        if clean and clean not in tags:
            tags.append(clean)
    return {
        "title": meta["title"],
        "body_markdown": md,
        "published": True,
        "canonical_url": url,
        "description": (meta.get("description") or "")[:150],
        "tags": tags[:4],
    }


def api(method: str, path: str, key: str, payload=None):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        API + path, data=data, method=method,
        headers={"api-key": key, "Content-Type": "application/json", "Accept": "application/vnd.forem.api-v1+json",
                 "User-Agent": "mydevexblog-publisher"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode("utf-8") or "null")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        raise SystemExit(f"dev.to API {method} {path} failed: {e.code} {body}")


def main() -> int:
    key = os.environ.get("DEVTO_API_KEY", "").strip()
    site_url = os.environ.get("SITE_URL", "https://vivek-itp.github.io/mydevexblog/")
    dry = os.environ.get("DRY_RUN") == "1"
    if not key and not dry:
        print("DEVTO_API_KEY not set; skipping dev.to publish")
        return 0

    posts = []
    for path in sorted(POSTS.glob("*.md")):
        meta, body = load_post(path)
        if not meta or meta.get("draft") or path.name.startswith("draft-"):
            continue
        posts.append(to_devto(meta, body, site_url))

    if dry:
        out = ROOT / "devto-preview"
        out.mkdir(exist_ok=True)
        for a in posts:
            (out / (slugify(a["title"]) + ".md")).write_text(
                "---\n" + yaml.safe_dump({k: v for k, v in a.items() if k != "body_markdown"}, sort_keys=False)
                + "---\n\n" + a["body_markdown"], encoding="utf-8")
        print(f"dry run: wrote {len(posts)} articles to {out}")
        return 0

    existing = {}
    page = 1
    while True:
        batch = api("GET", f"/articles/me/all?per_page=100&page={page}", key)
        if not batch:
            break
        for art in batch:
            if art.get("canonical_url"):
                existing[art["canonical_url"]] = art["id"]
        if len(batch) < 100:
            break
        page += 1

    for a in posts:
        aid = existing.get(a["canonical_url"])
        if aid:
            api("PUT", f"/articles/{aid}", key, {"article": a})
            print(f"updated  {a['title']}")
        else:
            res = api("POST", "/articles", key, {"article": a})
            print(f"created  {a['title']} -> {res.get('url')}")
        time.sleep(4)  # stay well inside dev.to's write rate limit
    return 0


if __name__ == "__main__":
    sys.exit(main())
