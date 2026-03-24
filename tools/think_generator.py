#!/usr/bin/env python3
"""think_generator.py — Generator-based cognitive pipeline for the swarm.

Restructures swarm thinking as composable generators that yield intermediate
products. Each cognitive mode is a generator; stacking composes them into
pipelines. Side effects (unexpected connections, tangential discoveries)
are captured and routed back into the swarm.

Modes (the cognitive pipeline stages):
  REACH  — extend to unknown territory (blind spots, frontier edges)
  INFO   — gather data about reached areas (lessons, principles, domains)
  USE    — apply gathered info to current tasks (actionable routing)
  THINK  — reason about implications, contradictions, patterns
  DREAM  — free association across domains (creative synthesis)
  REPAIR — fix inconsistencies found by previous modes

Each generator yields ThinkProduct objects. Products have a main output
and a list of side_effects. Side effects from any stage feed back into
the pipeline — they ARE the swarm swarming its own thinking.

Stacking: generators compose left-to-right. The output of one feeds
the input of the next. Default stack: reach|info|think|dream|repair.
Custom stacks via --stack "reach|dream|repair".

Usage:
    python3 tools/think_generator.py                    # default stack
    python3 tools/think_generator.py --stack "reach|dream"  # custom stack
    python3 tools/think_generator.py --mode think       # single mode
    python3 tools/think_generator.py --json             # machine-readable
    python3 tools/think_generator.py --side-effects     # show only side effects
    python3 tools/think_generator.py --feed-back        # route side effects to signals

External: Haskell lazy evaluation (Peyton Jones 1987); Unix pipes (McIlroy 1964);
  iterator protocol (Python PEP 234); monadic composition (Wadler 1992);
  cognitive architecture (ACT-R, Anderson 2007); dual-process theory (Kahneman 2011).
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Generator, List, Optional, Dict, Any

ROOT = Path(__file__).resolve().parent.parent
LESSONS_DIR = ROOT / "memory" / "lessons"
PRINCIPLES_FILE = ROOT / "memory" / "PRINCIPLES.md"
FRONTIER_FILE = ROOT / "tasks" / "FRONTIER.md"
CHALLENGES_FILE = ROOT / "tasks" / "CHALLENGES.md"

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SideEffect:
    """A tangential discovery from the thinking process."""
    source_mode: str
    kind: str  # "connection", "gap", "contradiction", "resonance", "repair_target"
    content: str
    targets: List[str] = field(default_factory=list)  # IDs of related items

    def __str__(self):
        t = f" → {', '.join(self.targets)}" if self.targets else ""
        return f"[{self.source_mode}:{self.kind}]{t} {self.content}"


@dataclass
class ThinkProduct:
    """Output yielded by a cognitive generator."""
    mode: str
    content: str
    evidence: List[str] = field(default_factory=list)
    side_effects: List[SideEffect] = field(default_factory=list)
    feeds_into: List[str] = field(default_factory=list)  # which modes should consume this
    depth: int = 0  # stack depth (0=first generator, 1=second, etc.)

    def __str__(self):
        se = f" (+{len(self.side_effects)} side effects)" if self.side_effects else ""
        return f"[{self.mode} d={self.depth}]{se} {self.content[:120]}"


# ---------------------------------------------------------------------------
# Corpus loaders (shared with dream.py / brain_extractor.py patterns)
# ---------------------------------------------------------------------------

def load_lessons() -> List[Dict]:
    lessons = []
    if not LESSONS_DIR.exists():
        return lessons
    for f in sorted(LESSONS_DIR.glob("L-*.md"),
                    key=lambda p: int(re.search(r'\d+', p.stem).group())):
        text = f.read_text(encoding="utf-8", errors="replace")
        num = int(re.search(r'\d+', f.stem).group())
        title_m = re.match(r'#\s*L-\d+:\s*(.+)', text)
        title = title_m.group(1).strip() if title_m else ""
        domain_m = re.search(r'(?:^|\|)\s*(?:\*\*)?domain(?:\*\*)?\s*:\s*([^|\n,*>]+)',
                             text, re.MULTILINE | re.IGNORECASE)
        domain = domain_m.group(1).strip() if domain_m else ""
        cited = list(set(re.findall(r'[PBL]-\d+', text)))
        status_m = re.search(r'(?:^|\|)\s*(?:\*\*)?status(?:\*\*)?\s*:\s*([^|\n,*>]+)',
                             text, re.MULTILINE | re.IGNORECASE)
        status = status_m.group(1).strip() if status_m else ""
        lessons.append({"id": f"L-{num}", "num": num, "title": title,
                        "domain": domain, "cited": cited, "status": status,
                        "text": text[:500]})
    return lessons


def load_principles() -> List[Dict]:
    principles = []
    if not PRINCIPLES_FILE.exists():
        return principles
    text = PRINCIPLES_FILE.read_text(encoding="utf-8", errors="replace")
    first_section = text.find('\n## ')
    if first_section > 0:
        text = text[first_section:]
    for raw in re.split(r' \| |\n', text):
        m = re.search(r'\b(P-\d+)\s+(.+)', raw.strip())
        if m:
            pid, body = m.group(1), m.group(2).strip()[:300]
            if 'superseded' not in body[:60].lower() and 'dropped' not in body[:60].lower():
                principles.append({"id": pid, "text": body})
    return principles


def load_frontiers() -> List[Dict]:
    frontiers = []
    if not FRONTIER_FILE.exists():
        return frontiers
    text = FRONTIER_FILE.read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r'\*\*(F[-\w]+)\*\*:\s*(.+?)(?:OPEN|CLOSED|RESOLVED)',
                         text, re.DOTALL):
        fid, desc = m.group(1), m.group(2).strip()[:200]
        frontiers.append({"id": fid, "desc": desc})
    return frontiers


def load_challenges() -> List[Dict]:
    challenges = []
    if not CHALLENGES_FILE.exists():
        return challenges
    text = CHALLENGES_FILE.read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r'\*\*(C\d+)\*\*[:\s]+(.+?)(?:\n|$)', text):
        cid, desc = m.group(1), m.group(2).strip()[:200]
        challenges.append({"id": cid, "desc": desc})
    return challenges


# ---------------------------------------------------------------------------
# Cognitive mode generators
# ---------------------------------------------------------------------------

def gen_reach(corpus: Dict, incoming: List[ThinkProduct] = None
              ) -> Generator[ThinkProduct, None, None]:
    """REACH — scan for what's unknown. Extend boundaries.

    Looks for: blind spots (domains with few lessons), frontier edges,
    uncited principles, isolated clusters.
    """
    lessons = corpus["lessons"]
    principles = corpus["principles"]
    frontiers = corpus["frontiers"]

    # Domain coverage gaps
    from collections import Counter
    domain_counts = Counter(l["domain"].lower() for l in lessons if l["domain"])
    all_domains = set(domain_counts.keys())
    sparse_domains = [(d, n) for d, n in domain_counts.items() if n <= 3]

    if sparse_domains:
        sparse_domains.sort(key=lambda x: x[1])
        side_effects = [
            SideEffect("reach", "gap", f"Sparse domain '{d}' has only {n} lessons",
                        targets=[]) for d, n in sparse_domains[:5]
        ]
        yield ThinkProduct(
            mode="reach",
            content=f"Found {len(sparse_domains)} sparse domains (≤3 lessons each). "
                    f"Sparsest: {', '.join(d for d, _ in sparse_domains[:3])}",
            evidence=[f"{d}:{n}L" for d, n in sparse_domains[:5]],
            side_effects=side_effects,
            feeds_into=["info", "dream"],
        )

    # Uncited principles = unreached territory
    all_cited = set(pid for l in lessons for pid in l["cited"] if pid.startswith("P-"))
    uncited = [p for p in principles if p["id"] not in all_cited]
    if uncited:
        yield ThinkProduct(
            mode="reach",
            content=f"{len(uncited)} principles with zero lesson citations — "
                    f"territory mapped but never walked",
            evidence=[p["id"] for p in uncited[:8]],
            side_effects=[
                SideEffect("reach", "gap", f"{p['id']} uncited: {p['text'][:60]}",
                           targets=[p["id"]]) for p in uncited[:5]
            ],
            feeds_into=["info", "use"],
        )

    # Frontier staleness
    if frontiers:
        yield ThinkProduct(
            mode="reach",
            content=f"{len(frontiers)} open frontiers — edges of known territory",
            evidence=[f["id"] for f in frontiers[:10]],
            side_effects=[],
            feeds_into=["think"],
        )

    # If incoming products exist, extend from their side effects
    if incoming:
        for product in incoming:
            for se in product.side_effects:
                if se.kind in ("gap", "contradiction"):
                    yield ThinkProduct(
                        mode="reach",
                        content=f"Extending from {se.source_mode} {se.kind}: {se.content[:80]}",
                        evidence=se.targets,
                        side_effects=[],
                        feeds_into=["info"],
                    )


def gen_info(corpus: Dict, incoming: List[ThinkProduct] = None
             ) -> Generator[ThinkProduct, None, None]:
    """INFO — gather data about reached areas.

    Reads lessons related to incoming reach products. Densifies knowledge
    around the areas that reach identified as sparse or unknown.
    """
    lessons = corpus["lessons"]

    # If incoming reach products identified sparse domains, gather info about them
    target_domains = set()
    target_principles = set()
    if incoming:
        for product in incoming:
            for ev in product.evidence:
                if ":" in ev and ev.endswith("L"):
                    target_domains.add(ev.split(":")[0])
                elif ev.startswith("P-"):
                    target_principles.add(ev)

    # Gather domain summaries for target domains
    if target_domains:
        for domain in list(target_domains)[:5]:
            domain_lessons = [l for l in lessons if l["domain"].lower() == domain]
            if domain_lessons:
                titles = [l["title"][:50] for l in domain_lessons[:5]]
                yield ThinkProduct(
                    mode="info",
                    content=f"Domain '{domain}': {len(domain_lessons)} lessons — "
                            f"{'; '.join(titles)}",
                    evidence=[l["id"] for l in domain_lessons],
                    side_effects=[],
                    feeds_into=["think", "use"],
                )

    # Gather principle context for uncited principles
    if target_principles:
        for pid in list(target_principles)[:5]:
            # Find lessons that COULD cite this principle (keyword overlap)
            from collections import Counter
            p_text = ""
            for p in corpus["principles"]:
                if p["id"] == pid:
                    p_text = p["text"]
                    break
            if not p_text:
                continue
            p_words = {w.lower() for w in re.findall(r'\b\w{5,}\b', p_text)}
            candidates = []
            for l in lessons:
                l_words = {w.lower() for w in re.findall(r'\b\w{5,}\b', l["title"])}
                overlap = p_words & l_words
                if len(overlap) >= 2:
                    candidates.append((l, overlap))
            if candidates:
                yield ThinkProduct(
                    mode="info",
                    content=f"{pid} has {len(candidates)} lessons with keyword overlap "
                            f"but no citation — citation gap",
                    evidence=[c["id"] for c, _ in candidates[:5]],
                    side_effects=[
                        SideEffect("info", "connection",
                                   f"{c['id']} could cite {pid} (shared: {', '.join(sorted(o)[:3])})",
                                   targets=[c["id"], pid])
                        for c, o in candidates[:3]
                    ],
                    feeds_into=["use", "repair"],
                )

    # General info: recent lesson status distribution
    from collections import Counter
    status_counts = Counter(l["status"].upper()[:10] for l in lessons if l["status"])
    if status_counts:
        yield ThinkProduct(
            mode="info",
            content=f"Lesson status distribution: {dict(status_counts.most_common(5))}",
            evidence=[],
            side_effects=[],
            feeds_into=["think"],
        )


def gen_use(corpus: Dict, incoming: List[ThinkProduct] = None
            ) -> Generator[ThinkProduct, None, None]:
    """USE — apply gathered info to current tasks.

    Routes information products to actionable outputs: which tasks benefit,
    which tools to run, which files to edit.
    """
    if not incoming:
        yield ThinkProduct(
            mode="use",
            content="No incoming products to apply — generator needs upstream input",
            evidence=[],
            side_effects=[],
            feeds_into=["reach"],
        )
        return

    actions = []
    for product in incoming:
        if product.mode == "info":
            for se in product.side_effects:
                if se.kind == "connection":
                    actions.append(f"Wire citation: {se.content[:80]}")
                elif se.kind == "gap":
                    actions.append(f"Fill gap: {se.content[:80]}")
        elif product.mode == "think":
            for se in product.side_effects:
                if se.kind == "contradiction":
                    actions.append(f"Resolve contradiction: {se.content[:80]}")
                elif se.kind == "resonance":
                    actions.append(f"Write crosslink: {se.content[:80]}")
        elif product.mode == "dream":
            for se in product.side_effects:
                actions.append(f"Dream routing: {se.content[:80]}")

    if actions:
        yield ThinkProduct(
            mode="use",
            content=f"{len(actions)} actionable items from upstream generators",
            evidence=[],
            side_effects=[
                SideEffect("use", "repair_target", a, targets=[])
                for a in actions[:10]
            ],
            feeds_into=["repair"],
        )

    # Direct application: products with evidence pointing to specific IDs
    for product in incoming:
        if product.evidence:
            yield ThinkProduct(
                mode="use",
                content=f"Apply {product.mode} finding to: {', '.join(product.evidence[:5])}",
                evidence=product.evidence[:5],
                side_effects=[],
                feeds_into=[],
            )


def gen_think(corpus: Dict, incoming: List[ThinkProduct] = None
              ) -> Generator[ThinkProduct, None, None]:
    """THINK — reason about implications, contradictions, patterns.

    The analytical generator. Looks for logical relationships between
    incoming products and the existing corpus.
    """
    lessons = corpus["lessons"]
    principles = corpus["principles"]

    # Cross-product contradiction detection
    if incoming and len(incoming) >= 2:
        # Check if any two products reference the same entity with different claims
        entities = {}
        for product in incoming:
            for ev in product.evidence:
                if ev not in entities:
                    entities[ev] = []
                entities[ev].append(product)
        conflicts = {k: v for k, v in entities.items() if len(v) >= 2}
        for entity, products in list(conflicts.items())[:3]:
            yield ThinkProduct(
                mode="think",
                content=f"Entity {entity} referenced by {len(products)} upstream products — "
                        f"potential tension between {products[0].mode} and {products[1].mode}",
                evidence=[entity],
                side_effects=[
                    SideEffect("think", "contradiction",
                               f"{entity}: {products[0].content[:40]} vs {products[1].content[:40]}",
                               targets=[entity])
                ],
                feeds_into=["repair"],
            )

    # Pattern detection across incoming products
    if incoming:
        from collections import Counter
        mode_counts = Counter(p.mode for p in incoming)
        all_side_effects = [se for p in incoming for se in p.side_effects]
        kind_counts = Counter(se.kind for se in all_side_effects)

        if kind_counts:
            dominant_kind = kind_counts.most_common(1)[0]
            yield ThinkProduct(
                mode="think",
                content=f"Side-effect pattern: {dominant_kind[0]} dominates "
                        f"({dominant_kind[1]}/{len(all_side_effects)} = "
                        f"{dominant_kind[1]*100//max(len(all_side_effects),1)}%). "
                        f"The pipeline is mostly finding {dominant_kind[0]}s.",
                evidence=[],
                side_effects=[
                    SideEffect("think", "resonance",
                               f"Pipeline produces {dominant_kind[0]}s — "
                               f"is this the swarm's current cognitive need?",
                               targets=[])
                ],
                feeds_into=["dream", "use"],
            )

    # Structural reasoning: principle-to-lesson ratio imbalances
    from collections import Counter
    domain_lesson_count = Counter(l["domain"].lower() for l in lessons if l["domain"])
    domain_principle_refs = Counter()
    for l in lessons:
        for pid in l["cited"]:
            if pid.startswith("P-"):
                domain_principle_refs[l["domain"].lower()] += 1

    theory_heavy = []  # many principle refs, few lessons
    empiric_heavy = []  # many lessons, few principle refs
    for domain in set(domain_lesson_count.keys()) | set(domain_principle_refs.keys()):
        lc = domain_lesson_count.get(domain, 0)
        pc = domain_principle_refs.get(domain, 0)
        if lc > 0 and pc / max(lc, 1) > 0.8:
            theory_heavy.append(domain)
        elif lc > 5 and pc / max(lc, 1) < 0.1:
            empiric_heavy.append(domain)

    if theory_heavy or empiric_heavy:
        yield ThinkProduct(
            mode="think",
            content=f"Theory-heavy domains (>80% P-refs): {theory_heavy[:3]}. "
                    f"Empiric-heavy (>5L, <10% P-refs): {empiric_heavy[:3]}.",
            evidence=theory_heavy[:3] + empiric_heavy[:3],
            side_effects=[
                SideEffect("think", "gap",
                           f"Empiric domain '{d}' needs principle anchoring",
                           targets=[]) for d in empiric_heavy[:3]
            ],
            feeds_into=["use", "repair"],
        )


def gen_dream(corpus: Dict, incoming: List[ThinkProduct] = None
              ) -> Generator[ThinkProduct, None, None]:
    """DREAM — free association across domains. Creative synthesis.

    Unlike think (analytical), dream makes associative leaps:
    juxtapose distant concepts, find resonance by sound/shape/feel,
    not by logic. The generator that produces novel combinations.
    """
    lessons = corpus["lessons"]
    principles = corpus["principles"]

    # Cross-domain juxtaposition: take two distant domains and find resonance
    from collections import Counter
    domain_counts = Counter(l["domain"].lower() for l in lessons if l["domain"])
    domains = list(domain_counts.keys())

    if len(domains) >= 2:
        import hashlib
        # Deterministic but session-varying selection
        seed_text = str(len(lessons)) + str(len(principles))
        seed = int(hashlib.md5(seed_text.encode()).hexdigest()[:8], 16)
        d1 = domains[seed % len(domains)]
        d2 = domains[(seed * 7 + 3) % len(domains)]
        if d1 == d2 and len(domains) > 1:
            d2 = domains[(domains.index(d1) + 1) % len(domains)]

        l1 = [l for l in lessons if l["domain"].lower() == d1]
        l2 = [l for l in lessons if l["domain"].lower() == d2]
        if l1 and l2:
            # Word overlap between domain titles
            w1 = set()
            for l in l1:
                w1.update(w.lower() for w in re.findall(r'\b\w{5,}\b', l["title"]))
            w2 = set()
            for l in l2:
                w2.update(w.lower() for w in re.findall(r'\b\w{5,}\b', l["title"]))
            shared = w1 & w2 - {
                "swarm", "lesson", "system", "based", "about", "model",
                "pattern", "structure", "process", "measure", "domain",
                "context", "behavior", "adoption", "approach", "change",
                "analysis", "framework", "signal", "threshold", "target",
                "evidence", "metric", "detection", "monitor", "level",
                "failure", "quality", "score", "value", "state", "phase",
                "effect", "growth", "scale", "internal", "external",
                "session", "principle", "belief", "frontier", "dispatch",
            }
            if len(shared) >= 2:  # require ≥2 non-generic shared words
                yield ThinkProduct(
                    mode="dream",
                    content=f"Dream resonance: '{d1}' × '{d2}' share vocabulary: "
                            f"{', '.join(sorted(shared)[:5])}. "
                            f"Is there an unnamed isomorphism?",
                    evidence=[l1[0]["id"], l2[0]["id"]],
                    side_effects=[
                        SideEffect("dream", "resonance",
                                   f"Unnamed ISO candidate: {d1} ↔ {d2} "
                                   f"via {', '.join(sorted(shared)[:3])}",
                                   targets=[l1[0]["id"], l2[0]["id"]])
                    ],
                    feeds_into=["think", "use"],
                )

    # Dream from side effects of upstream generators — amplify the unexpected
    if incoming:
        side_effects = [se for p in incoming for se in p.side_effects]
        # Find side effects that connect to multiple targets
        multi_target = [se for se in side_effects if len(se.targets) >= 2]
        if multi_target:
            se = multi_target[0]
            yield ThinkProduct(
                mode="dream",
                content=f"Amplifying multi-target side effect: {se.content[:100]} — "
                        f"what if this connection is the central pattern?",
                evidence=se.targets,
                side_effects=[
                    SideEffect("dream", "resonance",
                               f"Promoted from side effect to candidate pattern: {se.content[:60]}",
                               targets=se.targets)
                ],
                feeds_into=["think", "use"],
            )

    # Free-form: what if the most-cited principle is wrong?
    citation_counts = Counter()
    for l in lessons:
        for pid in l["cited"]:
            if pid.startswith("P-"):
                citation_counts[pid] += 1
    if citation_counts:
        top_p = citation_counts.most_common(1)[0]
        yield ThinkProduct(
            mode="dream",
            content=f"Dream challenge: {top_p[0]} is cited {top_p[1]} times — "
                    f"most-cited principle. What if it's an attractor, not a truth? "
                    f"What would the swarm look like without it?",
            evidence=[top_p[0]],
            side_effects=[
                SideEffect("dream", "contradiction",
                           f"Most-cited {top_p[0]} ({top_p[1]}x) — confirmation attractor risk",
                           targets=[top_p[0]])
            ],
            feeds_into=["think", "repair"],
        )


def gen_repair(corpus: Dict, incoming: List[ThinkProduct] = None
               ) -> Generator[ThinkProduct, None, None]:
    """REPAIR — fix inconsistencies found by previous modes.

    Takes contradictions, gaps, and repair_targets from upstream and
    produces concrete repair actions.
    """
    if not incoming:
        yield ThinkProduct(
            mode="repair",
            content="No upstream products — nothing to repair",
            evidence=[],
            side_effects=[],
            feeds_into=[],
        )
        return

    repairs = []
    for product in incoming:
        for se in product.side_effects:
            if se.kind == "contradiction":
                repairs.append({
                    "type": "contradiction",
                    "action": f"Investigate and resolve: {se.content[:80]}",
                    "targets": se.targets,
                    "source": product.mode,
                })
            elif se.kind == "gap":
                repairs.append({
                    "type": "gap",
                    "action": f"Fill gap: {se.content[:80]}",
                    "targets": se.targets,
                    "source": product.mode,
                })
            elif se.kind == "connection":
                repairs.append({
                    "type": "citation",
                    "action": f"Wire missing citation: {se.content[:80]}",
                    "targets": se.targets,
                    "source": product.mode,
                })
            elif se.kind == "repair_target":
                repairs.append({
                    "type": "action",
                    "action": se.content[:100],
                    "targets": se.targets,
                    "source": product.mode,
                })

    if repairs:
        by_type = {}
        for r in repairs:
            by_type.setdefault(r["type"], []).append(r)

        yield ThinkProduct(
            mode="repair",
            content=f"{len(repairs)} repairs identified: "
                    + ", ".join(f"{len(v)} {k}" for k, v in by_type.items()),
            evidence=[t for r in repairs for t in r["targets"][:2]],
            side_effects=[],
            feeds_into=[],
        )

        # Yield individual repair items
        for r in repairs[:10]:
            yield ThinkProduct(
                mode="repair",
                content=f"[{r['type']}] {r['action']}",
                evidence=r["targets"],
                side_effects=[],
                feeds_into=[],
            )


# ---------------------------------------------------------------------------
# Generator stacking engine
# ---------------------------------------------------------------------------

MODES = {
    "reach": gen_reach,
    "info": gen_info,
    "use": gen_use,
    "think": gen_think,
    "dream": gen_dream,
    "repair": gen_repair,
}

DEFAULT_STACK = ["reach", "info", "think", "dream", "repair"]


def run_stack(stack: List[str], corpus: Dict, verbose: bool = True
              ) -> List[ThinkProduct]:
    """Execute a stacked generator pipeline.

    Each generator receives the corpus + all products from previous generators.
    Side effects accumulate and feed forward. The stack is the thinking process.
    """
    all_products: List[ThinkProduct] = []
    all_side_effects: List[SideEffect] = []

    for depth, mode_name in enumerate(stack):
        gen_fn = MODES.get(mode_name)
        if not gen_fn:
            print(f"  ⚠ Unknown mode: {mode_name}", file=sys.stderr)
            continue

        if verbose:
            print(f"\n{'─' * 60}")
            print(f"  ◆ {mode_name.upper()} (depth={depth})")
            print(f"{'─' * 60}")

        # Feed all previous products as incoming
        incoming = all_products if all_products else None
        stage_products = []

        for product in gen_fn(corpus, incoming):
            product.depth = depth
            stage_products.append(product)
            all_side_effects.extend(product.side_effects)

            if verbose:
                print(f"  {product}")
                for se in product.side_effects:
                    print(f"    ↳ {se}")

        all_products.extend(stage_products)

        if verbose and not stage_products:
            print(f"  (no products)")

    return all_products


def collect_side_effects(products: List[ThinkProduct]) -> List[SideEffect]:
    """Extract all side effects from a pipeline run."""
    return [se for p in products for se in p.side_effects]


def side_effects_to_signals(side_effects: List[SideEffect]) -> List[Dict]:
    """Convert side effects into swarm signal format for feed-back."""
    signals = []
    for se in side_effects:
        signal_type = {
            "connection": "discovery",
            "gap": "question",
            "contradiction": "challenge",
            "resonance": "discovery",
            "repair_target": "prescription",
        }.get(se.kind, "observation")
        signals.append({
            "type": signal_type,
            "content": se.content,
            "source": f"think_generator:{se.source_mode}",
            "targets": se.targets,
        })
    return signals


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generator-based cognitive pipeline for the swarm")
    parser.add_argument("--stack", type=str, default=None,
                        help="Custom stack: 'reach|info|think' (pipe-separated modes)")
    parser.add_argument("--mode", type=str, default=None,
                        help="Run a single mode (reach/info/use/think/dream/repair)")
    parser.add_argument("--json", action="store_true",
                        help="Machine-readable JSON output")
    parser.add_argument("--side-effects", action="store_true",
                        help="Show only side effects (the feed-back channel)")
    parser.add_argument("--feed-back", action="store_true",
                        help="Route side effects back as swarm signals")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress per-product output, show only summary")
    args = parser.parse_args()

    # Determine stack
    if args.mode:
        stack = [args.mode]
    elif args.stack:
        stack = [s.strip() for s in args.stack.split("|")]
    else:
        stack = DEFAULT_STACK

    # Validate
    for mode in stack:
        if mode not in MODES:
            print(f"Error: unknown mode '{mode}'. "
                  f"Available: {', '.join(MODES.keys())}", file=sys.stderr)
            sys.exit(1)

    verbose = not args.json and not args.quiet

    if verbose:
        print(f"=== THINK GENERATOR ===")
        print(f"Stack: {' → '.join(m.upper() for m in stack)}")

    # Load corpus
    corpus = {
        "lessons": load_lessons(),
        "principles": load_principles(),
        "frontiers": load_frontiers(),
        "challenges": load_challenges(),
    }

    if verbose:
        print(f"Corpus: {len(corpus['lessons'])}L  {len(corpus['principles'])}P  "
              f"{len(corpus['frontiers'])}F  {len(corpus['challenges'])}C")

    # Run the stacked pipeline
    products = run_stack(stack, corpus, verbose=verbose)
    side_effects = collect_side_effects(products)

    # Output
    if args.json:
        output = {
            "stack": stack,
            "products": [asdict(p) for p in products],
            "side_effects": [asdict(se) for se in side_effects],
            "summary": {
                "total_products": len(products),
                "total_side_effects": len(side_effects),
                "by_mode": {},
                "by_kind": {},
            }
        }
        from collections import Counter
        mode_counts = Counter(p.mode for p in products)
        kind_counts = Counter(se.kind for se in side_effects)
        output["summary"]["by_mode"] = dict(mode_counts)
        output["summary"]["by_kind"] = dict(kind_counts)
        print(json.dumps(output, indent=2, default=str))
        return

    if args.side_effects:
        print(f"\n=== SIDE EFFECTS ({len(side_effects)}) ===")
        for se in side_effects:
            print(f"  {se}")
        return

    # Summary
    from collections import Counter
    print(f"\n{'═' * 60}")
    print(f"  PIPELINE SUMMARY")
    print(f"{'═' * 60}")
    print(f"  Products: {len(products)}")
    print(f"  Side effects: {len(side_effects)}")

    mode_counts = Counter(p.mode for p in products)
    print(f"  By mode: {dict(mode_counts)}")

    kind_counts = Counter(se.kind for se in side_effects)
    if kind_counts:
        print(f"  By kind: {dict(kind_counts)}")

    # Feed-back routing
    if args.feed_back and side_effects:
        signals = side_effects_to_signals(side_effects)
        print(f"\n--- FEED-BACK: {len(signals)} signals ---")
        for sig in signals:
            print(f"  [{sig['type']}] {sig['content'][:80]}")
        # Could wire to swarm_signal.py here
        print(f"\n  Use: python3 tools/swarm_signal.py post <type> '<content>'")
        print(f"  to route these into the signal system.")
    elif side_effects:
        print(f"\n  Side effects available. Use --feed-back to route as signals.")
        print(f"  Side effects ARE the mechanism — they serve swarm swarm.")


if __name__ == "__main__":
    main()
