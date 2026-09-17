#!/usr/bin/env python3
"""Render draft posts into one standalone HTML review page.

The page shows each draft the way it will look once published, with a checklist
of the example claims that still need confirming. It is a review aid only: it is
never committed, never deployed, and never linked from the repository.

Usage:
    python3 tools/preview.py spec.json out.html

spec.json is a list of drafts:
    [
      {
        "path":   "docs/blog/posts/2026-09-15-observability-for-developers.md",
        "pr":     18,
        "claims": ["first claim to confirm", "second claim"]
      }
    ]

Needs `markdown` and `pyyaml`, both already pulled in by mkdocs.
"""
import base64
import datetime
import json
import pathlib
import re
import sys

import markdown
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from diagrams import diagram_id, diagram_path, find_mermaid_blocks  # noqa: E402


def diagram_for(source, post_path):
    """Locate a rendered diagram.

    Prefer the tree the post itself lives in, so a draft on its own branch or in
    a worktree finds the image committed alongside it rather than whatever
    happens to be checked out here.
    """
    name = diagram_id(source) + ".png"
    for parent in pathlib.Path(post_path).resolve().parents:
        candidate = parent / "docs" / "assets" / "diagrams" / name
        if candidate.exists():
            return candidate
    return diagram_path(source)

FRONT_MATTER = re.compile(r"^---\n(.*?)\n---\n", re.S)
EXTENSIONS = [
    "admonition", "attr_list", "md_in_html", "tables", "footnotes", "abbr",
    "pymdownx.details", "pymdownx.inlinehilite", "pymdownx.highlight",
    "pymdownx.superfences", "pymdownx.tasklist",
]

STYLE = """
:root{
  --paper:#faf8f4; --surface:#fffefb; --ink:#1a2422; --ink-soft:#4a5754;
  --muted:#6f7b77; --rule:#e5e1d7; --rule-soft:#efece4;
  --teal:#0f766c; --teal-soft:#e6f1ef; --rust:#b0501f; --rust-soft:#fbefe7;
  --shadow:0 1px 2px rgba(26,36,34,.05), 0 8px 24px -16px rgba(26,36,34,.18);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --paper:#111614; --surface:#171d1b; --ink:#e9ebe6; --ink-soft:#bcc4c0;
    --muted:#8d9793; --rule:#2b3330; --rule-soft:#222927;
    --teal:#5fc9bc; --teal-soft:#152a27; --rust:#e08a5c; --rust-soft:#2a1d15;
    --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 24px -16px rgba(0,0,0,.6);
  }
}
:root[data-theme="dark"]{
  --paper:#111614; --surface:#171d1b; --ink:#e9ebe6; --ink-soft:#bcc4c0;
  --muted:#8d9793; --rule:#2b3330; --rule-soft:#222927;
  --teal:#5fc9bc; --teal-soft:#152a27; --rust:#e08a5c; --rust-soft:#2a1d15;
  --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 24px -16px rgba(0,0,0,.6);
}
*{box-sizing:border-box}
body{background:var(--paper); color:var(--ink);
  font-family:"Newsreader",Georgia,"Times New Roman",serif; font-size:19px; line-height:1.68;
  -webkit-font-smoothing:antialiased;}
.bar{position:sticky; top:env(safe-area-inset-top,0px); z-index:20;
  background:color-mix(in srgb,var(--paper) 96%,transparent);
  backdrop-filter:blur(10px); border-bottom:1px solid var(--rule);}
.bar-in{max-width:74ch; margin:0 auto; padding:10px 20px; display:flex; gap:10px;
  align-items:center; flex-wrap:wrap;}
.brand{font-family:"IBM Plex Sans",system-ui,sans-serif; font-size:11px; font-weight:600;
  letter-spacing:.12em; text-transform:uppercase; color:var(--muted); margin-right:auto;}
.tab{font-family:"IBM Plex Sans",system-ui,sans-serif; font-size:13px; line-height:1.3;
  display:flex; align-items:baseline; gap:7px; padding:7px 12px; border-radius:7px;
  border:1px solid var(--rule); background:var(--surface); color:var(--ink-soft);
  cursor:pointer; text-align:left; max-width:100%;}
.tab:hover{border-color:var(--teal)}
.tab[aria-selected="true"]{background:var(--teal-soft); border-color:var(--teal); color:var(--ink);}
.tab-n{font-weight:600; color:var(--teal); font-variant-numeric:tabular-nums;}
.tab-t{overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:26ch;}
.wrap{max-width:74ch; margin:0 auto; padding:0 20px; padding-block:0 72px;}
.head{padding-block:40px 6px; border-bottom:1px solid var(--rule-soft); margin-bottom:34px;}
.eyebrow{font-family:"IBM Plex Sans",system-ui,sans-serif; font-size:12px; color:var(--muted);
  display:flex; gap:8px; flex-wrap:wrap; align-items:center; margin:0 0 14px;}
.cat{color:var(--teal); font-weight:600; letter-spacing:.06em; text-transform:uppercase;
  font-size:11px;}
.dot{opacity:.45}
h1{font-size:clamp(30px,6vw,44px); line-height:1.14; font-weight:600; letter-spacing:-.015em;
  margin:0 0 16px; text-wrap:balance;}
.standfirst{font-size:20px; line-height:1.55; color:var(--ink-soft); font-style:italic;
  margin:0 0 18px;}
.tags{display:flex; gap:6px; flex-wrap:wrap; margin:0 0 22px;}
.tag{font-family:"IBM Plex Sans",system-ui,sans-serif; font-size:11px; color:var(--muted);
  border:1px solid var(--rule); border-radius:100px; padding:2px 9px;}
.post h2{font-size:26px; line-height:1.25; font-weight:600; letter-spacing:-.01em;
  margin:2.4em 0 .55em; text-wrap:balance;}
.post h2:first-child{margin-top:0}
.post p{margin:0 0 1.15em}
.post a{color:var(--teal); text-underline-offset:3px;}
.post strong{font-weight:600}
.post ul,.post ol{margin:0 0 1.15em; padding-left:1.35em}
.post li{margin-bottom:.45em}
.post code{font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:.82em;
  background:var(--rule-soft); padding:.12em .38em; border-radius:4px;}
.post pre{background:var(--surface); border:1px solid var(--rule); border-radius:9px;
  padding:16px 18px; overflow-x:auto; margin:0 0 1.3em;}
.post pre code{background:none; padding:0; font-size:13.5px; line-height:1.6;}
.tablewrap{overflow-x:auto; margin:0 0 1.4em; border:1px solid var(--rule); border-radius:9px;}
.post table{border-collapse:collapse; width:100%; font-family:"IBM Plex Sans",system-ui,sans-serif;
  font-size:14.5px;}
.post th,.post td{text-align:left; padding:11px 14px; border-bottom:1px solid var(--rule-soft);
  vertical-align:top;}
.post th{font-weight:600; font-size:12px; letter-spacing:.05em; text-transform:uppercase;
  color:var(--muted); background:var(--rule-soft);}
.post tr:last-child td{border-bottom:none}
.diagram{margin:0 0 1.4em; padding:14px; background:#fff; border:1px solid var(--rule);
  border-radius:9px; overflow-x:auto; text-align:center;}
.diagram img{max-width:100%; height:auto;}
.admonition{margin:0 0 1.4em; padding:16px 18px; border-radius:9px; background:var(--teal-soft);
  border-left:3px solid var(--teal); font-size:17.5px;}
.admonition-title{font-family:"IBM Plex Sans",system-ui,sans-serif; font-size:12px; font-weight:600;
  letter-spacing:.07em; text-transform:uppercase; color:var(--teal); margin:0 0 .7em;}
.admonition p:last-child{margin-bottom:0}
.verify{margin-top:52px; background:var(--rust-soft); border:1px solid var(--rust);
  border-radius:12px; padding:24px 22px; box-shadow:var(--shadow);}
.verify h2{font-size:21px; font-weight:600; margin:0 0 .5em;}
.verify-lead{font-size:16.5px; color:var(--ink-soft); margin:0 0 1.1em;}
.claims{list-style:none; margin:0 0 14px; padding:0; display:flex; flex-direction:column; gap:12px;}
.claims label{display:flex; gap:11px; align-items:flex-start; cursor:pointer;
  font-size:16.5px; line-height:1.5;}
.claims input{margin:5px 0 0; width:17px; height:17px; flex:0 0 auto; accent-color:var(--rust);}
.claims input:checked + span{color:var(--muted); text-decoration:line-through;
  text-decoration-color:var(--rust);}
.progress{font-family:"IBM Plex Sans",system-ui,sans-serif; font-size:12.5px; color:var(--muted);
  margin:0 0 16px; font-variant-numeric:tabular-nums;}
.actions{display:flex; gap:14px; align-items:center; flex-wrap:wrap;
  border-top:1px solid var(--rust); padding-top:16px;}
.btn{font-family:"IBM Plex Sans",system-ui,sans-serif; font-size:14px; font-weight:600;
  text-decoration:none; padding:9px 16px; border-radius:8px; display:inline-block;}
.btn.primary{background:var(--rust); color:var(--paper);}
.btn.primary:hover{filter:brightness(1.08)}
.hint{font-family:"IBM Plex Sans",system-ui,sans-serif; font-size:13px; color:var(--ink-soft);}
:focus-visible{outline:2px solid var(--teal); outline-offset:2px; border-radius:4px;}
@media (prefers-reduced-motion: reduce){*{transition:none!important; animation:none!important}}
@media (max-width:560px){
  body{font-size:18px}
  .tab-t{max-width:14ch}
  .standfirst{font-size:18px}
}
"""

SCRIPT = """
(function(){
  var meta = JSON.parse(document.getElementById("meta").textContent);
  var tabs = Array.prototype.slice.call(document.querySelectorAll(".tab"));

  function show(slug){
    tabs.forEach(function(t){
      var on = t.dataset.slug === slug;
      t.setAttribute("aria-selected", on ? "true" : "false");
      document.getElementById("pane-" + t.dataset.slug).hidden = !on;
    });
    window.scrollTo({top:0, behavior:"auto"});
    try{ localStorage.setItem("draftdesk.tab", slug); }catch(e){}
  }
  tabs.forEach(function(t){ t.addEventListener("click", function(){ show(t.dataset.slug); }); });

  function count(slug, n){
    var done = 0;
    for(var i=0;i<n;i++){
      var el = document.getElementById("c-" + slug + "-" + i);
      if(el && el.checked) done++;
    }
    var p = document.getElementById("prog-" + slug);
    if(p) p.textContent = done === n
      ? "All " + n + " confirmed. Ready when you are."
      : done + " of " + n + " confirmed.";
  }

  meta.forEach(function(m){
    for(var i=0;i<m.n;i++){
      (function(el, key){
        if(!el) return;
        try{ el.checked = localStorage.getItem("draftdesk." + key) === "1"; }catch(e){}
        el.addEventListener("change", function(){
          try{ localStorage.setItem("draftdesk." + key, el.checked ? "1" : "0"); }catch(e){}
          count(m.slug, m.n);
        });
      })(document.getElementById("c-" + m.slug + "-" + i), m.slug + "-" + i);
    }
    count(m.slug, m.n);
  });

  try{
    var saved = localStorage.getItem("draftdesk.tab");
    if(saved && document.getElementById("pane-" + saved)) show(saved);
  }catch(e){}

  Array.prototype.forEach.call(document.querySelectorAll(".post table"), function(t){
    if(t.parentElement && t.parentElement.classList.contains("tablewrap")) return;
    var w = document.createElement("div");
    w.className = "tablewrap";
    t.parentNode.insertBefore(w, t);
    w.appendChild(t);
  });
})();
"""


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def load(entry):
    path = pathlib.Path(entry["path"])
    raw = path.read_text(encoding="utf-8")
    match = FRONT_MATTER.match(raw)
    if not match:
        raise SystemExit(f"{path} has no front matter")
    meta = yaml.safe_load(match.group(1))
    body = raw[match.end():]
    words = len(body.split())
    body = body.replace("<!-- more -->", "")

    # Swap each diagram for its rendered image, embedded so the page stands alone.
    for block, source in reversed(list(find_mermaid_blocks(body))):
        png = diagram_for(source, path)
        if png.exists():
            uri = "data:image/png;base64," + base64.b64encode(png.read_bytes()).decode()
            rep = f'<figure class="diagram"><img src="{uri}" alt="Diagram from the post"></figure>'
        else:
            rep = '<p class="diagram"><em>Diagram not rendered yet.</em></p>'
        body = body[: block.start()] + rep + body[block.end():]

    created = meta["date"]["created"]
    if not isinstance(created, datetime.date):
        created = datetime.date.fromisoformat(str(created))
    return {
        "slug": meta["slug"],
        "title": meta["title"],
        "description": meta.get("description", ""),
        "category": (meta.get("categories") or ["Uncategorised"])[0],
        "tags": meta.get("tags") or [],
        "date": created.strftime("%B %-d, %Y"),
        "words": words,
        "minutes": max(1, round(words / 230)),
        "pr": entry["pr"],
        "claims": entry.get("claims", []),
        "html": markdown.markdown(body, extensions=EXTENSIONS),
    }


def build(posts, repo):
    tabs, panes = [], []
    for i, p in enumerate(posts):
        sel = "true" if i == 0 else "false"
        tabs.append(
            f'<button class="tab" id="tab-{p["slug"]}" role="tab" aria-selected="{sel}" '
            f'aria-controls="pane-{p["slug"]}" data-slug="{p["slug"]}">'
            f'<span class="tab-n">#{p["pr"]}</span>'
            f'<span class="tab-t">{esc(p["title"])}</span></button>')
        claims = "\n".join(
            f'<li><label><input type="checkbox" id="c-{p["slug"]}-{j}">'
            f'<span>{esc(c)}</span></label></li>'
            for j, c in enumerate(p["claims"]))
        tags = "".join(f'<span class="tag">{esc(str(t))}</span>' for t in p["tags"])
        panes.append(f'''<section class="pane" id="pane-{p['slug']}" role="tabpanel"
   aria-labelledby="tab-{p['slug']}"{'' if i == 0 else ' hidden'}>
  <header class="head">
    <p class="eyebrow"><span class="cat">{esc(p['category'])}</span><span class="dot">&middot;</span>
      <span>{esc(p['date'])}</span><span class="dot">&middot;</span>
      <span>{p['words']} words, about {p['minutes']} min</span></p>
    <h1>{esc(p['title'])}</h1>
    <p class="standfirst">{esc(p['description'])}</p>
    <p class="tags">{tags}</p>
  </header>
  <article class="post">
{p['html']}
  </article>
  <aside class="verify">
    <h2>Before you approve</h2>
    <p class="verify-lead">Each example below is written as your own experience but has not been
      confirmed by you. Tick the ones that are true. Say which are not and they will be rewritten
      before this goes out.</p>
    <ol class="claims">{claims}</ol>
    <p class="progress" id="prog-{p['slug']}"></p>
    <div class="actions">
      <a class="btn primary" href="https://github.com/{repo}/pull/{p['pr']}"
         target="_blank" rel="noopener">Open pull request #{p['pr']}</a>
      <span class="hint">Say <b>publish</b> to merge, or <b>approved, hold</b> to keep it open.</span>
    </div>
  </aside>
</section>''')

    meta = json.dumps([{"slug": p["slug"], "n": len(p["claims"])} for p in posts])
    meta_js = meta.replace("<", "\\u003c")
    tabs_html = "\n  ".join(tabs)
    panes_html = "\n".join(panes)
    fonts = ("https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@"
             "0,6..72,400;0,6..72,500;0,6..72,600;1,6..72,400"
             "&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap")
    return f'''<title>Draft Desk</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{fonts}">
<style>{STYLE}</style>

<div class="bar"><div class="bar-in">
  <span class="brand">Draft desk</span>
  <div role="tablist" aria-label="Pending drafts" style="display:flex;gap:8px;flex-wrap:wrap">
  {tabs_html}
  </div>
</div></div>

<main class="wrap">
{panes_html}
</main>

<script type="application/json" id="meta">{meta_js}</script>
<script>{SCRIPT}</script>'''


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    spec = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
    repo = "vivek-Itp/mydevexblog"
    posts = [load(e) for e in spec]
    out = pathlib.Path(sys.argv[2])
    out.write_text(build(posts, repo), encoding="utf-8")
    print(f"wrote {out} ({round(out.stat().st_size / 1024)} KB) "
          f"for {len(posts)} draft(s): {', '.join(p['slug'] for p in posts)}")


if __name__ == "__main__":
    main()
