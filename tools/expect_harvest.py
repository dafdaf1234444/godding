#!/usr/bin/env python3
"""Expect Harvest — Expectation Calibration Tracker.
Parses session notes and lane Etc for expect/actual/diff records.
Computes hit rate, direction bias, per-domain calibration, temporal trend.
Usage: python3 tools/expect_harvest.py [--report|--json]
"""
import argparse, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.domain_map import LANE_ABBREV_TO_DOMAIN, resolve_lane_domain

ROOT = Path(__file__).resolve().parent.parent
NEXT_MD, NEXT_ARCHIVE = ROOT / "tasks/NEXT.md", ROOT / "tasks/NEXT-ARCHIVE.md"
LANES_FILE = ROOT / "tasks/SWARM-LANES.md"
WRONG_KW = ["WRONG", "FALSIFIED", "FAIL", "INVERTED", "WORSENED"]
PARTIAL_KW = ["PARTIALLY CONFIRMED", "PARTIALLY", "PARTIAL", "partially"]
CONFIRMED_KW = ["CONFIRMED", "confirmed", "PASS", "exceeded", "precisely",
                "matches", "Ratio matches", "Correctly predicted"]
CONFIRM_RE = re.compile(
    r"(?:Expected|Predicted).{3,80}(?:got|—)\s.{3,80}"
    r"(?:stronger|exceeded|better|larger|precisely|within|exonerated"
    r"|EXCEEDED|confirmed|PASS|close|correct)", re.I)
EXPECT_GOT_RE = re.compile(r"(?:Expected|Predicted).{3,80}(?:got\b|—\s*got)", re.I)
OVER_KW = ["WRONG", "WORSE than expected", "got transient", "INVERTED",
           "WORSENED", "6x worse"]
UNDER_KW = ["exceeded", "stronger", "better", "larger", "FAR exceeded",
            "EXCEEDED", "precisely"]

def classify_diff(d):
    if not d: return "unclassified"
    for kw in WRONG_KW:
        if kw in d:
            return "partial" if any(k in d for k in CONFIRMED_KW) else "wrong"
    for kw in PARTIAL_KW:
        if kw in d: return "partial"
    for kw in CONFIRMED_KW:
        if kw in d: return "confirmed"
    if CONFIRM_RE.search(d): return "confirmed"
    if "Did NOT predict" in d or "NOT predicted" in d: return "partial"
    if EXPECT_GOT_RE.search(d): return "partial"
    return "unclassified"

def direction_bias(d):
    if not d: return "neutral"
    ov = sum(1 for k in OVER_KW if k in d)
    un = sum(1 for k in UNDER_KW if k in d)
    un += len(re.findall(r"Did NOT predict|NOT predicted", d))
    return "overconfident" if ov > un else ("underconfident" if un > ov else "neutral")

def _session(s):
    m = re.search(r"\bS(\d+)", s)
    return int(m.group(1)) if m else 0

def _normalize_domain(raw: str) -> str:
    """Map raw domain abbreviation to canonical domain name via domain_map."""
    up = raw.upper().strip()
    return LANE_ABBREV_TO_DOMAIN.get(up, raw.lower())

def _domain_lane(text):
    m = re.search(r"DOMEX-([A-Z]+)-S\d+", text)
    if m:
        resolved = resolve_lane_domain(m.group(0))
        if resolved: return resolved
        return _normalize_domain(m.group(1))
    m = re.search(r"\*\*dispatch\*\*:\s*(\S+)", text)
    if m:
        raw = re.sub(r"[^a-zA-Z-]", "", m.group(1))
        return _normalize_domain(raw)
    return "unknown"

def _domain_etc(etc):
    for pat in [r"intent=advance-F-([A-Z]+)", r"focus=domains/([^;]+)",
                r"frontier=F-([A-Z]+)"]:
        m = re.search(pat, etc)
        if m:
            raw = m.group(1).strip()
            if "/" not in raw:
                return _normalize_domain(raw)
            return raw.lower().rstrip("/")
    return "unknown"

def _record(src, sess, dom, lane, exp, act, diff):
    return {"source": src, "session": sess, "domain": dom, "lane": lane,
            "expect": exp, "actual": act, "diff": diff,
            "classification": classify_diff(diff), "bias": direction_bias(diff)}


def parse_session_notes(path):
    if not path.exists(): return []
    records = []
    for block in re.split(r"(?=^## S\d+)", path.read_text(encoding="utf-8", errors="replace"), flags=re.MULTILINE):
        hm = re.match(r"^## (S\d+\S*)\s+session note\s*\(([^)]*)\)", block)
        if not hm: continue
        session, title = _session(hm.group(1)), hm.group(2)
        ll = next((l for l in block.splitlines() if "**lane**:" in l or "**dispatch**:" in l), title)
        lm = re.search(r"DOMEX-\S+-S\d+\w*", ll)
        e = a = d = ""
        for line in block.splitlines():
            if line.startswith("- **expect**:"): e = line.split(":", 1)[1].strip()
            elif line.startswith("- **actual**:"): a = line.split(":", 1)[1].strip()
            elif line.startswith("- **diff**:"): d = line.split(":", 1)[1].strip()
        if e or a:
            records.append(_record("session_note", session, _domain_lane(ll),
                                   lm.group(0) if lm else "", e, a, d))
    return records

def parse_lane_etc(path):
    if not path.exists(): return []
    records = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith("|"): continue
        cols = [c.strip() for c in line.split("|")]
        if len(cols) < 12 or "expect=" not in cols[10]: continue
        fields = {}
        for part in cols[10].split("; "):
            if "=" in part:
                k, v = part.split("=", 1); fields[k.strip()] = v.strip()
        ex = fields.get("expect", "")
        if not ex: continue
        records.append(_record("lane_etc", _session(cols[3] if len(cols) > 3 else ""),
                               _domain_etc(cols[10]), cols[2].strip(),
                               ex, fields.get("actual", ""), fields.get("diff", "")))
    return records

def compute_metrics(records):
    n = len(records)
    if not n: return {"total": 0}
    counts = {"confirmed": 0, "partial": 0, "wrong": 0, "unclassified": 0}
    bias = {"overconfident": 0, "underconfident": 0, "neutral": 0}
    domains = {}
    for r in records:
        counts[r["classification"]] += 1; bias[r["bias"]] += 1
        d = domains.setdefault(r["domain"],
            {"confirmed": 0, "partial": 0, "wrong": 0, "unclassified": 0, "total": 0})
        d[r["classification"]] += 1; d["total"] += 1
    cl = n - counts["unclassified"]
    sess = sorted(set(r["session"] for r in records if r["session"] > 0))
    trend = {"note": "insufficient data"}
    if len(sess) >= 4:
        mid = sess[len(sess) // 2]
        def _hr(rs):
            c = sum(1 for r in rs if r["classification"] == "confirmed")
            t = sum(1 for r in rs if r["classification"] != "unclassified")
            return round(c / t, 3) if t else 0
        ea, la = [r for r in records if 0 < r["session"] <= mid], [r for r in records if r["session"] > mid]
        trend = {"early": f"S1-S{mid}", "late": f"S{mid+1}+", "early_hit": _hr(ea),
                 "late_hit": _hr(la), "early_n": len(ea), "late_n": len(la),
                 "improving": _hr(la) > _hr(ea)}
    return {"total": n, "classified": cl, **counts,
            "hit_rate": round(counts["confirmed"] / cl, 3) if cl else 0,
            "partial_rate": round(counts["partial"] / cl, 3) if cl else 0,
            "wrong_rate": round(counts["wrong"] / cl, 3) if cl else 0,
            "bias": bias, "per_domain": domains, "trend": trend}

def print_report(m, records):
    W = 60
    print("=" * W); print("  EXPECTATION CALIBRATION REPORT"); print("=" * W)
    if not m["total"]: print("\n  No records found."); return
    print(f"\n  Records:      {m['total']} ({m['classified']} classified)")
    print(f"  Hit rate:     {m['hit_rate']:.1%} confirmed")
    print(f"  Partial:      {m['partial_rate']:.1%}")
    print(f"  Wrong:        {m['wrong_rate']:.1%}")
    print(f"  Unclassified: {m['unclassified']}")
    b = m["bias"]
    ratio = f"{b['underconfident']/b['overconfident']:.1f}:1" if b['overconfident'] else "inf:1"
    print(f"\n  Direction bias:  over={b['overconfident']}  under={b['underconfident']}  neutral={b['neutral']}")
    print(f"  Underconf ratio: {ratio} (target <5:1)")
    tr = m["trend"]
    if "note" not in tr:
        print(f"\n  Temporal trend: {'IMPROVING' if tr['improving'] else 'DECLINING'}")
        print(f"    {tr['early']} (n={tr['early_n']}): {tr['early_hit']:.1%}")
        print(f"    {tr['late']} (n={tr['late_n']}): {tr['late_hit']:.1%}")
    dom = sorted(m["per_domain"].items(), key=lambda x: x[1]["total"], reverse=True)
    print(f"\n  Per-domain calibration (top 10 of {len(dom)}):")
    print(f"    {'Domain':<20} {'N':>4} {'Hit%':>6} {'Wrong%':>7}")
    print(f"    {'-'*20} {'-'*4} {'-'*6} {'-'*7}")
    for name, d in dom[:10]:
        cl = d["total"] - d["unclassified"]
        print(f"    {name:<20} {d['total']:>4} {d['confirmed']/cl if cl else 0:>5.0%} {d['wrong']/cl if cl else 0:>6.0%}")
    print()

def main():
    ap = argparse.ArgumentParser(description="Expect Harvest — calibration tracker")
    ap.add_argument("--report", action="store_true", help="Human-readable report")
    ap.add_argument("--json", action="store_true", help="JSON output")
    args = ap.parse_args()
    if not args.report and not args.json: args.report = True
    records = parse_session_notes(NEXT_MD) + parse_session_notes(NEXT_ARCHIVE) + parse_lane_etc(LANES_FILE)
    seen, deduped = set(), []
    for r in records:
        key = (r["session"], r["lane"], r["source"])
        if key not in seen: seen.add(key); deduped.append(r)
    metrics = compute_metrics(deduped)
    if args.json:
        print(json.dumps({"metrics": metrics, "record_count": len(deduped)}, indent=2))
    if args.report: print_report(metrics, deduped)

if __name__ == "__main__":
    main()
