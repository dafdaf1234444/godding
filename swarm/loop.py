#!/usr/bin/env python3
"""godding/swarm/loop.py — multi-agent paragraph-tightening loop.
Runs offline with no dependencies. If ANTHROPIC_API_KEY is set + `anthropic`
is installed, the drafter is upgraded; otherwise heuristics handle it.
Outputs:  data/changelog.json  data/metrics.json  data/last_run.json
"""
from __future__ import annotations
import argparse, dataclasses, datetime as dt, hashlib, json, os, random, re, sys, textwrap
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
PAGES_DIR = ROOT / "pages"
DATA_DIR = ROOT / "data"
CHANGELOG_FILE = DATA_DIR / "changelog.json"
METRICS_FILE = DATA_DIR / "metrics.json"
LAST_RUN_FILE = DATA_DIR / "last_run.json"

PAGES = [
    "belief.html","religion.html","politics.html","health.html",
    "sustainability.html","crime.html","ants.html","build.html","swarm.html",
    "reach.html","good-bad.html","now.html",
    # criminals.html is deliberately excluded — that page promises stable numbers.
]

WEASEL = ["very","really","basically","essentially","actually","literally",
          "obviously","clearly","of course","needless to say","kind of","sort of"]
HEDGE = ["might","may","could","perhaps","possibly","seems","appears"]
SUPERLATIVE = ["always","never","everyone","no one","nobody","all"]
GOOD_PARA_MIN, GOOD_PARA_MAX = 3, 90

@dataclasses.dataclass
class Diff:
    page: str
    target_paragraph: str
    proposed: str
    rationale: str
    agent: str

@dataclasses.dataclass
class Verdict:
    accept: bool
    reasons: list
    agent: str

def file_hash(p: Path): return hashlib.sha256(p.read_bytes()).hexdigest()[:12]
def now_iso(): return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def load_json(p: Path, default):
    if not p.exists(): return default
    try: return json.loads(p.read_text(encoding="utf-8"))
    except Exception: return default

def write_json(p: Path, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

P_TAG_RE = re.compile(r"<p\b[^>]*>(.*?)</p>", re.DOTALL | re.IGNORECASE)
def get_page_text(p: Path): return p.read_text(encoding="utf-8")
def list_paragraphs(html: str):
    return [(m.start(), m.end(), m.group(1)) for m in P_TAG_RE.finditer(html)]
def strip_tags(t): return re.sub(r"<[^>]+>", "", t)
def word_count(t): return len(re.findall(r"\b\w+\b", strip_tags(t)))
def replace_span(html, s, e, rep): return html[:s] + rep + html[e:]
def _wrap_keep_attrs(html, s, e, inner):
    block = html[s:e]
    m = re.match(r"<p\b([^>]*)>", block, re.IGNORECASE)
    attrs = m.group(1) if m else ""
    return f"<p{attrs}>{inner}</p>"

def heuristic_drafter(page: str, html: str):
    paras = list_paragraphs(html)
    if not paras: return None
    rng = random.Random(hash((page, dt.date.today().isoformat())))
    indices = list(range(len(paras))); rng.shuffle(indices)
    for idx in indices:
        s, e, inner = paras[idx]
        text = inner; words = word_count(text)
        if words < GOOD_PARA_MIN: continue
        # 1) drop weasel
        for w in WEASEL:
            pat = re.compile(rf"\b{re.escape(w)}\b\s*,?\s*", re.IGNORECASE)
            if pat.search(text):
                new_inner = re.sub(r"\s+", " ", pat.sub("", text, count=1)).strip()
                if new_inner and new_inner != text.strip():
                    return Diff(page=page, target_paragraph=text.strip()[:240],
                                proposed=_wrap_keep_attrs(html, s, e, new_inner),
                                rationale=f'remove weasel word "{w}".',
                                agent="drafter:heuristic")
        # 2) soften superlative (but not when used as a quantifier: "all three")
        for sw in SUPERLATIVE:
            pat = re.compile(rf"\b{re.escape(sw)}\b(?!\s+(?:\d+|of|three|four|five|six|seven|eight|nine|ten|two))",
                             re.IGNORECASE)
            if pat.search(text) and not any(h in text.lower() for h in HEDGE):
                rep = {"always":"usually","never":"rarely","everyone":"most people",
                       "no one":"almost no one","nobody":"almost nobody","all":"most"}[sw.lower()]
                new_inner = pat.sub(rep, text, count=1)
                if new_inner != text:
                    return Diff(page=page, target_paragraph=text.strip()[:240],
                                proposed=_wrap_keep_attrs(html, s, e, new_inner),
                                rationale=f'soften unqualified superlative "{sw}" → "{rep}".',
                                agent="drafter:heuristic")
        # 3) trim longest sentence in over-long paragraph
        if words > GOOD_PARA_MAX:
            sents = re.split(r"(?<=[\.!?])\s+", text.strip())
            if len(sents) >= 3:
                longest = max(range(len(sents)), key=lambda i: word_count(sents[i]))
                new_inner = " ".join(sents[:longest] + sents[longest+1:]).strip()
                if new_inner and new_inner != text.strip():
                    return Diff(page=page, target_paragraph=text.strip()[:240],
                                proposed=_wrap_keep_attrs(html, s, e, new_inner),
                                rationale="trim longest sentence in over-long paragraph.",
                                agent="drafter:heuristic")
    return None

def claude_drafter(page: str, html: str):
    if not os.environ.get("ANTHROPIC_API_KEY"): return None
    try: import anthropic
    except Exception: return None
    try:
        client = anthropic.Anthropic()
        paras = list_paragraphs(html)
        if not paras: return None
        idx = max(range(len(paras)), key=lambda i: word_count(paras[i][2]))
        s, e, inner = paras[idx]
        prompt = textwrap.dedent(f"""
        You are a copy editor for a punchy, opinionated personal site called "godding".
        Tighten exactly one paragraph below. Do NOT change its meaning. Do NOT
        introduce facts. Just trim weasel words, soften unsupported superlatives,
        and shorten if it's bloated. Reply ONLY with valid JSON:
        {{"new_paragraph": "...", "rationale": "..."}}.
        Paragraph:
        ---
        {strip_tags(inner)}
        ---
        """).strip()
        msg = client.messages.create(model="claude-haiku-4-5-20251001", max_tokens=600,
                                     messages=[{"role":"user","content":prompt}])
        raw = "".join(b.text for b in msg.content if hasattr(b, "text"))
        data = json.loads(raw[raw.find("{"): raw.rfind("}")+1])
        new_inner = data["new_paragraph"].strip()
        if not new_inner or new_inner == strip_tags(inner).strip(): return None
        return Diff(page=page, target_paragraph=strip_tags(inner).strip()[:240],
                    proposed=_wrap_keep_attrs(html, s, e, new_inner),
                    rationale=data.get("rationale", "tightened by drafter:claude"),
                    agent="drafter:claude")
    except Exception: return None

def critic_review(diff: Diff, html_before: str, html_after: str):
    reasons = []
    bw, aw = word_count(html_before), word_count(html_after)
    if aw > bw: reasons.append("post-edit text is longer; loop tightens, not expand.")
    if abs(aw-bw) > max(20, bw*0.20): reasons.append("change too large; paragraph-scale only.")
    inner = re.search(r"<p[^>]*>(.*?)</p>", diff.proposed, re.DOTALL).group(1)
    plain = strip_tags(inner).strip()
    if word_count(plain) < GOOD_PARA_MIN: reasons.append("proposed paragraph too short.")
    new_pairs = set(re.findall(r"\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b", plain))
    old_pairs = set(re.findall(r"\b([A-Z][a-z]+)\s+([A-Z][a-z]+)\b", strip_tags(diff.target_paragraph)))
    common = {("North","America"),("South","America"),("South","Asia"),
              ("South","East"),("New","York"),("Middle","East")}
    new_names = (new_pairs - old_pairs) - common
    if new_names: reasons.append(f"introduces new proper-noun pair(s) {sorted(new_names)}.")
    if re.search(r'"[^"]{40,}"', plain): reasons.append("contains long quoted string.")
    return Verdict(accept=len(reasons)==0,
                   reasons=reasons or ["clean tightening."],
                   agent="critic")

def fact_check(diff: Diff):
    nb = set(re.findall(r"\d[\d,\.%]*", diff.target_paragraph))
    inner = re.search(r"<p[^>]*>(.*?)</p>", diff.proposed, re.DOTALL).group(1)
    na = set(re.findall(r"\d[\d,\.%]*", strip_tags(inner)))
    added = na - nb
    if added: return Verdict(accept=False,
                             reasons=[f"introduces new numeric claim(s): {sorted(added)}"],
                             agent="fact-checker")
    return Verdict(accept=True, reasons=["no new facts."], agent="fact-checker")

def judge(diff, c, f):
    if c.accept and f.accept: return Verdict(accept=True, reasons=["accepted."], agent="judge")
    return Verdict(accept=False,
                   reasons=(["rejected by critic."] if not c.accept else []) +
                           (["rejected by fact-checker."] if not f.accept else []) +
                           c.reasons + f.reasons,
                   agent="judge")

def iterate_page(page: str, dry_run: bool):
    page_path = PAGES_DIR / page
    html_before = get_page_text(page_path)
    hash_before = file_hash(page_path)
    diff = claude_drafter(page, html_before) or heuristic_drafter(page, html_before)
    if diff is None:
        return {"page": page, "status": "no-op",
                "reason": "drafter found nothing worth tightening."}
    paras = list_paragraphs(html_before); target_idx = None
    for i,(s,e,inner) in enumerate(paras):
        if strip_tags(inner).strip().startswith(strip_tags(diff.target_paragraph)[:60]):
            target_idx = i; break
    if target_idx is None:
        return {"page": page, "status": "no-op",
                "reason": "could not relocate target paragraph."}
    s,e,_ = paras[target_idx]
    html_after = replace_span(html_before, s, e, diff.proposed)
    cv = critic_review(diff, html_before, html_after)
    fv = fact_check(diff)
    final = judge(diff, cv, fv)
    if not final.accept:
        return {"page": page, "status": "rejected", "rationale": diff.rationale,
                "agent": diff.agent, "reasons": final.reasons}
    if dry_run:
        return {"page": page, "status": "would-accept", "rationale": diff.rationale,
                "agent": diff.agent}
    page_path.write_text(html_after, encoding="utf-8")
    hash_after = file_hash(page_path)
    return {"page": page, "status": "accepted", "rationale": diff.rationale,
            "agent": diff.agent, "hash_before": hash_before, "hash_after": hash_after,
            "before_excerpt": diff.target_paragraph[:200]}

def run(once_page=None, dry_run=False):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    pages = [once_page] if once_page else PAGES[:]
    results = []
    for p in pages:
        if not (PAGES_DIR / p).exists(): results.append({"page": p, "status": "missing"}); continue
        results.append(iterate_page(p, dry_run))
    accepted = [r for r in results if r.get("status") == "accepted"]
    run_id = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    record = {
        "run_id": run_id, "timestamp": now_iso(), "dry_run": dry_run,
        "proposed_diffs": sum(1 for r in results if r.get("status") in ("accepted","rejected","would-accept")),
        "accepted_diffs": len(accepted),
        "pages": [r["page"] for r in accepted],
        "rationale": "; ".join(r.get("rationale","") for r in accepted)[:240] or "no diffs accepted this run.",
        "details": results,
    }
    if not dry_run and accepted:
        cl = load_json(CHANGELOG_FILE, [])
        cl.append({k: record[k] for k in ("run_id","timestamp","pages","accepted_diffs","proposed_diffs","rationale")})
        write_json(CHANGELOG_FILE, cl)
    write_json(LAST_RUN_FILE, record)
    metrics = load_json(METRICS_FILE, {"runs_total":0,"runs_with_accepted_diffs":0,
                                       "diffs_proposed_total":0,"diffs_accepted_total":0,
                                       "first_run":None,"last_run":None})
    metrics["runs_total"] += 1
    if accepted: metrics["runs_with_accepted_diffs"] += 1
    metrics["diffs_proposed_total"] += record["proposed_diffs"]
    metrics["diffs_accepted_total"] += record["accepted_diffs"]
    metrics["first_run"] = metrics["first_run"] or record["timestamp"]
    metrics["last_run"] = record["timestamp"]
    write_json(METRICS_FILE, metrics)
    return record

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--once", default=None)
    a = ap.parse_args()
    once = a.once
    if once and not once.endswith(".html"):
        once = once.split("=", 1)[-1] + ".html"
    elif once:
        once = once.split("=", 1)[-1]
    print(json.dumps(run(once_page=once, dry_run=a.dry_run), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
