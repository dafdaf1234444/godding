#!/usr/bin/env python3
"""
nk_null_model.py — Null-model test for swarm citation graph structure.

Tests whether the swarm's lesson citation network has genuinely non-random
structure or is consistent with uniform random citation.

K_avg (mean in-degree) = total_edges / N, fully determined by the out-degree
sequence. Instead we test STRUCTURAL metrics that vary across random graphs:
  - Max in-degree (hub concentration)
  - Gini coefficient (citation inequality)
  - Fraction zero-in-degree (isolation rate)

Usage:
    python3 tools/nk_null_model.py
    python3 tools/nk_null_model.py --verbose
    python3 tools/nk_null_model.py --trials 5000 --checkpoint 25
"""
import argparse, math, random, re, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from swarm_io import REPO_ROOT, read_text

LESSONS_DIR = REPO_ROOT / "memory" / "lessons"
CITE_RE = re.compile(r"\bL-(\d+)\b")
METRICS = [("k_max", "Max In-Degree (Hub)"), ("gini", "Gini (Inequality)"),
           ("frac_zero", "Frac Uncited (Isolation)")]

# ── Graph extraction ─────────────────────────────────────────────────────

def parse_citations() -> dict[int, set[int]]:
    """Parse L-*.md files, return {lesson_num: set of cited lesson nums}."""
    existing = set()
    for p in LESSONS_DIR.glob("L-*.md"):
        m = re.match(r"L-(\d+)\.md$", p.name)
        if m:
            existing.add(int(m.group(1)))
    graph: dict[int, set[int]] = {}
    for num in sorted(existing):
        path = LESSONS_DIR / f"L-{num:03d}.md"
        if not path.exists():
            path = LESSONS_DIR / f"L-{num}.md"
        text = read_text(path) if path.exists() else ""
        graph[num] = {int(m.group(1)) for m in CITE_RE.finditer(text)
                      if int(m.group(1)) != num and int(m.group(1)) in existing}
    return graph

def in_degrees(nodes: list[int], edges: dict[int, set[int]]) -> list[int]:
    ns = set(nodes)
    deg = {n: 0 for n in nodes}
    for s in nodes:
        for t in edges.get(s, set()):
            if t in ns:
                deg[t] += 1
    return [deg[n] for n in nodes]

def gini(vals: list[int]) -> float:
    n = len(vals)
    if n == 0: return 0.0
    s = sorted(vals); total = sum(s)
    if total == 0: return 0.0
    return (2.0 * sum((i+1)*v for i, v in enumerate(s))) / (n * total) - (n+1.0) / n

def metrics(degs: list[int]) -> dict[str, float]:
    n = len(degs)
    if n == 0: return {"k_avg": 0, "k_max": 0, "gini": 0, "frac_zero": 0}
    return {"k_avg": sum(degs)/n, "k_max": max(degs),
            "gini": gini(degs), "frac_zero": sum(1 for d in degs if d == 0) / n}

# ── Simulation ───────────────────────────────────────────────────────────

def simulate_one(nodes, out_degs, checkpoints, rng):
    """Simulate random citation graph, return metrics at each checkpoint."""
    in_d = {}; avail = []; ci = 0; res = []
    for i, node in enumerate(nodes):
        in_d[node] = 0
        k = out_degs[i]
        if k > 0 and avail:
            for t in rng.sample(avail, min(k, len(avail))):
                in_d[t] += 1
        avail.append(node)
        while ci < len(checkpoints) and len(avail) >= checkpoints[ci]:
            res.append(metrics([in_d[n] for n in avail])); ci += 1
    while len(res) < len(checkpoints):
        res.append(metrics(list(in_d.values())))
    return res

def run_null_model(graph, n_trials=1000, cp_every=50, verbose=False, seed=42):
    nodes = sorted(graph.keys())
    n = len(nodes)
    out_degs = [len(graph[nd]) for nd in nodes]
    cps = list(range(cp_every, n+1, cp_every))
    if cps and cps[-1] != n: cps.append(n)
    if not cps: cps = [n]

    # Observed metrics
    obs = [metrics(in_degrees(nodes[:cp], graph)) for cp in cps]

    # Null trajectories
    rng = random.Random(seed)
    null = []
    for t in range(n_trials):
        null.append(simulate_one(nodes, out_degs, cps, rng))
        if verbose and (t+1) % 200 == 0:
            print(f"  ... {t+1}/{n_trials} trials", file=sys.stderr)

    # Z-scores
    results = []
    for ci, cp in enumerate(cps):
        entry = {"n": cp, "obs": obs[ci]}
        for mk, _ in METRICS:
            ov = obs[ci][mk]
            nv = [null[t][ci][mk] for t in range(n_trials)]
            nm = sum(nv) / len(nv)
            ns = math.sqrt(sum((v-nm)**2 for v in nv) / len(nv))
            entry[mk] = {"obs": ov, "null_m": nm, "null_s": ns,
                          "z": (ov-nm)/ns if ns > 1e-12 else 0.0}
        results.append(entry)
    return results

# ── Output ───────────────────────────────────────────────────────────────

def print_summary(graph):
    n = len(graph); edges = sum(len(v) for v in graph.values())
    od = [len(v) for v in graph.values()]
    id_ = in_degrees(sorted(graph.keys()), graph)
    print(f"\n{'='*70}\nNK NULL MODEL — Citation Graph Randomness Test\n{'='*70}")
    print(f"\n-- Observed Graph --")
    print(f"  N={n}  Edges={edges}  K_avg={sum(id_)/n:.4f}  K_max={max(id_)}")
    print(f"  Gini={gini(id_):.4f}  Zero-out={sum(1 for d in od if d==0)} ({sum(1 for d in od if d==0)/n*100:.0f}%)"
          f"  Zero-in={sum(1 for d in id_ if d==0)} ({sum(1 for d in id_ if d==0)/n*100:.0f}%)")
    dist = Counter(od)
    print(f"  Out-degree dist (top 6):", end="")
    for deg, cnt in sorted(dist.items(), key=lambda x: -x[1])[:6]:
        print(f"  k={deg}:{cnt}", end="")
    print()

def sig(z):
    if abs(z)>3: return "***"
    if abs(z)>2: return "** "
    if abs(z)>1.5: return "*  "
    return "   "

def print_results(results, n_trials):
    for mk, ml in METRICS:
        print(f"\n-- {ml} ({n_trials} trials) --")
        print(f"  {'N':>5}  {'Obs':>9}  {'Null M':>9}  {'Null S':>9}  {'z':>7}  Sig")
        print(f"  {'─'*5}  {'─'*9}  {'─'*9}  {'─'*9}  {'─'*7}  {'─'*3}")
        for r in results:
            m = r[mk]
            fmt = ".0f" if mk == "k_max" else ".4f"
            o = f"{m['obs']:{fmt}}" ; nm = f"{m['null_m']:{fmt}}"
            print(f"  {r['n']:5d}  {o:>9}  {nm:>9}  {m['null_s']:9.4f}  {m['z']:7.3f}  {sig(m['z'])}")

    final = results[-1]
    print(f"\n{'='*70}\nVERDICT (N={final['n']}, K_avg={final['obs']['k_avg']:.4f})\n{'='*70}")
    any_sig = False
    for mk, ml in METRICS:
        m = final[mk]; z = m["z"]
        d = "above" if z > 0 else "below"
        label = "HIGHLY SIGNIFICANT" if abs(z)>3 else "SIGNIFICANT" if abs(z)>2 else \
                "MARGINAL" if abs(z)>1.5 else "Not significant"
        if abs(z) > 2: any_sig = True
        print(f"\n  {ml}: obs={m['obs']:.4f} null={m['null_m']:.4f}+/-{m['null_s']:.4f}"
              f" z={z:+.3f} ({d}) => {label}")

    print(f"\n  {'GENUINELY NON-RANDOM structure detected.' if any_sig else 'Consistent with random citation.'}")
    print(f"\n-- Notes --")
    print(f"  Null preserves: N, creation order, out-degree sequence.")
    print(f"  Null randomizes: citation targets (uniform over prior lessons).")
    print(f"  K_avg not tested (fixed by out-degree). Tests: hub size, inequality, isolation.")
    print(f"{'='*70}")

# ── Main ─────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Null-model test for citation graph")
    ap.add_argument("--trials", type=int, default=1000)
    ap.add_argument("--checkpoint", type=int, default=50)
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    if args.verbose: print("Parsing lesson files...", file=sys.stderr)
    graph = parse_citations()
    if not graph:
        print("ERROR: No lessons found in", LESSONS_DIR, file=sys.stderr); sys.exit(1)
    print_summary(graph)

    if args.verbose: print(f"\nRunning {args.trials} simulations...", file=sys.stderr)
    results = run_null_model(graph, args.trials, args.checkpoint, args.verbose, args.seed)
    print_results(results, args.trials)

if __name__ == "__main__":
    main()
