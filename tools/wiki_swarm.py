#!/usr/bin/env python3
"""Wiki Swarm — fetch Wikipedia articles and extract swarm-relevant knowledge.

Usage:
    python3 tools/wiki_swarm.py <topic> [--depth N] [--fanout N] [--relevance] [--output PATH]

Examples:
    python3 tools/wiki_swarm.py "Homomorphism"
    python3 tools/wiki_swarm.py "Category theory" --depth 2 --fanout 3
    python3 tools/wiki_swarm.py "Stigmergy" --relevance  # include swarm relevance hints
"""

import argparse
import json
import re
import sys
import textwrap
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

WIKI_API = "https://en.wikipedia.org/w/api.php"
WIKI_REST = "https://en.wikipedia.org/api/rest_v1"


def wiki_api(params: dict) -> dict:
    """Call Wikipedia's action API."""
    params.setdefault("format", "json")
    url = f"{WIKI_API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "SwarmBot/1.0 (research)"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def wiki_summary(title: str) -> dict:
    """Fetch page summary via REST API."""
    encoded = urllib.parse.quote(title.replace(" ", "_"), safe="")
    url = f"{WIKI_REST}/page/summary/{encoded}"
    req = urllib.request.Request(url, headers={"User-Agent": "SwarmBot/1.0 (research)"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"title": title, "extract": f"[fetch failed: {e}]"}


def get_sections(title: str) -> list:
    """Get article section structure."""
    data = wiki_api({"action": "parse", "page": title, "prop": "sections"})
    return data.get("parse", {}).get("sections", [])


def get_wikitext(title: str) -> str:
    """Get raw wikitext of article."""
    data = wiki_api({"action": "parse", "page": title, "prop": "wikitext"})
    return data.get("parse", {}).get("wikitext", {}).get("*", "")


def get_links(title: str, limit: int = 50) -> list:
    """Get internal links from article (namespace 0 = main articles)."""
    data = wiki_api({"action": "parse", "page": title, "prop": "links"})
    links = data.get("parse", {}).get("links", [])
    return [l["*"] for l in links if l.get("ns", 0) == 0][:limit]


def get_see_also(wikitext: str) -> list:
    """Extract See also links from wikitext."""
    m = re.search(r"==\s*See also\s*==(.+?)(?===\s*\w|\Z)", wikitext, re.DOTALL)
    if not m:
        return []
    section = m.group(1)
    return re.findall(r"\[\[([^\]|]+?)(?:\|[^\]]+?)?\]\]", section)


def get_categories(title: str) -> list:
    """Get article categories."""
    data = wiki_api({"action": "parse", "page": title, "prop": "categories"})
    cats = data.get("parse", {}).get("categories", [])
    return [c.get("*", "").replace("_", " ") for c in cats
            if not c.get("hidden")]


def clean_wikitext_brief(wikitext: str, max_chars: int = 2000) -> str:
    """Strip wikitext markup for a readable summary."""
    text = wikitext
    # Remove refs
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", text, flags=re.DOTALL)
    text = re.sub(r"<ref[^/]*/>", "", text)
    # Remove templates (simple — nested templates may survive)
    text = re.sub(r"\{\{[^}]{0,200}\}\}", "", text)
    # Convert links
    text = re.sub(r"\[\[[^|\]]+\|([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    # Convert math
    text = re.sub(r"<math[^>]*>(.*?)</math>", r"$\1$", text, flags=re.DOTALL)
    # Remove remaining HTML
    text = re.sub(r"<[^>]+>", "", text)
    # Clean whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()[:max_chars]


def extract_definition(wikitext: str) -> str:
    """Extract the Definition section (or intro if no Definition heading)."""
    m = re.search(r"==\s*Definition\s*==(.+?)(?===\s)", wikitext, re.DOTALL)
    if m:
        return clean_wikitext_brief(m.group(1), 1500)
    # Fallback: intro (before first ==)
    m = re.search(r"^(.+?)(?===)", wikitext, re.DOTALL)
    if m:
        return clean_wikitext_brief(m.group(1), 1000)
    return clean_wikitext_brief(wikitext, 800)


def crawl_topic(title: str, depth: int = 1, fanout: int = 5,
                visited: set = None) -> dict:
    """Recursively crawl a Wikipedia topic."""
    if visited is None:
        visited = set()

    canon = title.replace(" ", "_")
    if canon in visited:
        return {"title": title, "skipped": True}
    visited.add(canon)

    summary_data = wiki_summary(title)
    result = {
        "title": summary_data.get("title", title),
        "url": f"https://en.wikipedia.org/wiki/{canon}",
        "summary": summary_data.get("extract", ""),
        "description": summary_data.get("description", ""),
    }

    if depth <= 0:
        return result

    # Get deeper content for root/important pages
    wikitext = get_wikitext(title)
    result["definition"] = extract_definition(wikitext)
    result["sections"] = [s["line"] for s in get_sections(title)]
    result["categories"] = get_categories(title)

    # Determine related pages: prefer See also, supplement with links
    see_also = get_see_also(wikitext)
    all_links = get_links(title, limit=100)

    # Prioritize: see_also first, then links not in see_also
    related_titles = list(dict.fromkeys(see_also + all_links))[:fanout]
    result["related_sampled"] = related_titles

    # Recurse
    result["children"] = []
    for child_title in related_titles:
        child = crawl_topic(child_title, depth=depth - 1, fanout=fanout,
                            visited=visited)
        result["children"].append(child)

    return result


def render_markdown(tree: dict, current_depth: int = 0) -> str:
    """Render crawl tree as markdown."""
    lines = []
    indent = ""
    title = tree["title"]
    url = tree["url"]

    if tree.get("skipped"):
        lines.append(f"{indent}### {title} (already visited)")
        return "\n".join(lines)

    heading = "#" * min(current_depth + 2, 4)
    lines.append(f"{heading} {title} (depth {current_depth})")
    lines.append(f"- URL: {url}")

    if tree.get("description"):
        lines.append(f"- Description: {tree['description']}")

    lines.append(f"- Summary: {tree['summary']}")

    if tree.get("sections"):
        lines.append(f"- Sections: {', '.join(tree['sections'][:10])}")

    if tree.get("definition"):
        lines.append(f"\n**Definition excerpt:**\n")
        # Indent definition
        for dline in tree["definition"].split("\n")[:15]:
            lines.append(f"> {dline}")

    if tree.get("related_sampled"):
        lines.append(f"- Related pages sampled: {', '.join(tree['related_sampled'])}")

    if tree.get("categories"):
        lines.append(f"- Categories: {', '.join(tree['categories'][:8])}")

    lines.append("")

    for child in tree.get("children", []):
        lines.append(render_markdown(child, current_depth + 1))

    return "\n".join(lines)


def format_output(tree: dict, topic: str, depth: int, fanout: int,
                  include_relevance: bool = False) -> str:
    """Format complete wiki swarm output."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    header = textwrap.dedent(f"""\
    # Wiki Swarm: {topic}

    - Resolved topic: `{tree['title']}`
    - Topic source: `auto`
    - Depth: {depth}
    - Fanout: {fanout}
    - Language: `en`
    - Generated: {now}

    """)

    body = render_markdown(tree, current_depth=0)

    relevance = ""
    if include_relevance:
        relevance = textwrap.dedent("""
        ---

        ## Swarm relevance (auto-generated hints)

        Analyze this article for:
        1. **Structural isomorphisms**: What swarm concepts does this map onto?
        2. **Operational imports**: What operations/algorithms could swarm adopt?
        3. **Falsification targets**: What claims does this challenge?
        4. **Vocabulary imports**: What terms give swarm better precision?
        5. **Kernel detection**: What is the "same structure" being preserved — and what is lost?
        """)

    return header + body + relevance


def main():
    parser = argparse.ArgumentParser(description="Wiki Swarm — fetch and analyze Wikipedia for swarm knowledge")
    parser.add_argument("topic", help="Wikipedia article title or search term")
    parser.add_argument("--depth", type=int, default=1, help="Crawl depth (default: 1)")
    parser.add_argument("--fanout", type=int, default=5, help="Related pages per article (default: 5)")
    parser.add_argument("--relevance", action="store_true", help="Include swarm relevance hints")
    parser.add_argument("--output", "-o", type=str, help="Output file path (default: stdout + auto-save)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of markdown")
    args = parser.parse_args()

    print(f"[wiki_swarm] Crawling: {args.topic} (depth={args.depth}, fanout={args.fanout})", file=sys.stderr)

    tree = crawl_topic(args.topic, depth=args.depth, fanout=args.fanout)

    if args.json:
        output = json.dumps(tree, indent=2, ensure_ascii=False)
    else:
        output = format_output(tree, args.topic, args.depth, args.fanout, args.relevance)

    # Determine output path
    if args.output:
        out_path = Path(args.output)
    else:
        slug = re.sub(r"[^a-z0-9]+", "-", args.topic.lower()).strip("-")
        out_path = Path("workspace/notes") / f"wiki-{slug}.md"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(output, encoding="utf-8")
    print(f"[wiki_swarm] Saved to: {out_path}", file=sys.stderr)

    # Also print to stdout
    print(output)


if __name__ == "__main__":
    main()
