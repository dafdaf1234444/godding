#!/usr/bin/env python3
"""deliberate.py — Lightweight multi-domain deliberation (council replacement).

Usage:
    python3 tools/deliberate.py "What structural mechanisms cause X?"
    python3 tools/deliberate.py "Why?" --domains meta,security,epistemology
    python3 tools/deliberate.py "How?" --session S529 --json
    python3 tools/deliberate.py "Q?" --template   # blank template only
"""

import argparse, json, re, subprocess, sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOMAINS_DIR = ROOT / "domains"
OUTPUT_DIR = ROOT / "experiments" / "deliberation"

sys.path.insert(0, str(ROOT / "tools"))
try:
    from swarm_io import session_number, read_text
except ImportError:
    def session_number():
        r = subprocess.run(["git", "log", "--oneline", "-50"], capture_output=True, text=True, cwd=ROOT)
        return max((int(m) for m in re.findall(r"\[S(\d+)\]", r.stdout)), default=0)
    def read_text(p):
        try: return p.read_text(encoding="utf-8", errors="replace")
        except Exception: return ""


def top_domains(n: int = 3) -> list[str]:
    """Get top-N domains from dispatch_optimizer --json."""
    try:
        r = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "dispatch_optimizer.py"), "--json"],
            capture_output=True, text=True, timeout=15, cwd=ROOT)
        ranked = json.loads(r.stdout)
        return [d["domain"] for d in ranked[:n]]
    except Exception:
        return ["meta", "epistemology", "security"]


def load_domain_context(domain: str) -> dict:
    """Load domain's DOMAIN.md summary and top frontier."""
    dpath = DOMAINS_DIR / domain
    ctx = {"domain": domain, "summary": "", "top_frontier": ""}
    dm = dpath / "DOMAIN.md"
    if dm.exists():
        lines = read_text(dm).splitlines()[:20]
        ctx["summary"] = "\n".join(l for l in lines if l.strip())
    fm = dpath / "tasks" / "FRONTIER.md"
    if fm.exists():
        m = re.search(r"\*\*(F[^\*]+)\*\*[:\s]+(.*)", read_text(fm))
        if m:
            ctx["top_frontier"] = f"{m.group(1)}: {m.group(2)[:120].strip()}"
    return ctx


def deliberate(question: str, domains: list[str], session: str,
               template_only: bool = False) -> dict:
    """Build deliberation structure."""
    now = datetime.now()
    result = {
        "id": f"delib-{session.lower()}-{now.strftime('%H%M')}",
        "session": session, "date": now.strftime("%Y-%m-%d"),
        "question": question, "domains": domains,
        "method": f"Parallel {len(domains)}-domain deliberation. Each domain investigates independently, then synthesize.",
        "perspectives": {},
        "synthesis": {"convergent_findings": [], "divergent_findings": [],
                      "root_cause": "", "prescribed_actions": []}
    }
    for d in domains:
        ctx = load_domain_context(d)
        result["perspectives"][d] = {
            "context": ctx["summary"][:200] if not template_only else "[loaded]", "top_frontier": ctx["top_frontier"],
            "finding": "" if template_only else f"[{d} perspective on: {question}]",
            "evidence": [], "cross_domain_signal": ""}
    return result


def main():
    ap = argparse.ArgumentParser(description="Lightweight multi-domain deliberation")
    ap.add_argument("question", help="Question to deliberate on")
    ap.add_argument("--domains", help="Comma-separated domain list (default: top-3)")
    ap.add_argument("--session", default=None, help="Session tag (default: auto-detect)")
    ap.add_argument("--json", action="store_true", dest="json_out", help="JSON output")
    ap.add_argument("--template", action="store_true", help="Output blank template only")
    args = ap.parse_args()

    session = args.session or f"S{session_number()}"
    domains = args.domains.split(",") if args.domains else top_domains(3)
    result = deliberate(args.question, domains, session, args.template)

    # Save artifact
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUTPUT_DIR / f"{result['id']}.json"
    out_file.write_text(json.dumps(result, indent=2) + "\n")

    if args.json_out:
        print(json.dumps(result, indent=2))
    else:
        lines = [f"# Deliberation: {args.question}",
                 f"Session: {session} | Domains: {', '.join(domains)}", ""]
        for d, p in result["perspectives"].items():
            lines.append(f"## [{d}]")
            if p["top_frontier"]:
                lines.append(f"  Frontier: {p['top_frontier']}")
            lines += [f"  Finding: {p['finding']}", f"  Evidence: {p['evidence']}",
                      f"  Cross-domain: {p['cross_domain_signal']}", ""]
        s = result["synthesis"]
        lines += ["## Synthesis", f"  Convergent: {s['convergent_findings']}",
                  f"  Divergent:  {s['divergent_findings']}",
                  f"  Root cause: {s['root_cause']}",
                  f"  Actions:    {s['prescribed_actions']}",
                  f"\nArtifact: {out_file.relative_to(ROOT)}"]
        print("\n".join(lines))


if __name__ == "__main__":
    main()
