#!/usr/bin/env python3
"""open_lane.py — F-META1: enforce evidence fields at lane creation.

Appends an ACTIVE row to tasks/SWARM-LANES.md for a new lane ID.
Requires --expect and --artifact to be specified at creation time,
addressing the F-META1 finding that evidence fields (22% compliance
at S328) must be embedded at lane open, not only at closure.

Usage:
  python3 tools/open_lane.py --lane DOMEX-BRN-SXXX --session SXXX \\
      --frontier F-BRN2 --focus domains/brain \\
      --intent "F-BRN2 predictive coding audit" \\
      --expect "pred-coding-50-70%-operational" \\
      --artifact "experiments/brain/f-brn2-audit-sXXX.json"
"""

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nodes import NODE_AI_SESSION  # noqa: E402 — node model (SIG-1, L-814)

REPO_ROOT = Path(__file__).parent.parent
LANES_FILE = REPO_ROOT / "tasks" / "SWARM-LANES.md"
LANES_ARCHIVE = REPO_ROOT / "tasks" / "SWARM-LANES-ARCHIVE.md"

VALID_MODES = ("exploration", "hardening", "replication", "resolution", "falsification")
VALID_LEVELS = ("L1", "L2", "L3", "L4", "L5")
# SIG-39 meta-role enforcement: creation-time role tagging for meta DOMEX lanes.
# L-601: voluntary classification decays; creation-time enforcement sustains.
# L-879: 0% voluntary adoption over 219 sessions = mechanism is dead. Only structural enforcement works. # L-879
# L-630: Prevention > retroactive audit — substrate check at open_lane (not post-hoc). # L-630
VALID_META_ROLES = ("historian", "tooler", "experimenter")

# P-243 science quality: vague expect values that don't constitute pre-registration
VAGUE_EXPECT_PATTERNS = [
    r"^TBD$",
    r"^(?:expect\s+)?(?:CONFIRMED|confirmed)$",
    r"^(?:will\s+)?confirm",
    r"^(?:should\s+)?(?:be\s+)?(?:stable|similar|same)",
]


def lane_exists(lane_id: str) -> bool:
    with open(LANES_FILE) as f:
        for line in f:
            if not line.startswith("|"):
                continue
            cols = [c.strip() for c in line.split("|")]
            if len(cols) >= 3 and cols[2] == lane_id:
                return True
    return False


def get_frontier_previous_mode(frontier_id: str) -> tuple[str | None, int]:
    """Return (mode of most recent lane, wave count) for this frontier.

    Returns (None, 0) if first wave. Reads both active and archive lanes.
    Used to enforce mode declaration on 2nd+ wave (F-STR3, L-766, L-601).
    """
    if not frontier_id:
        return None, 0
    lanes: list[tuple[int, str]] = []
    for lanes_file in (LANES_FILE, LANES_ARCHIVE):
        if not lanes_file.exists():
            continue
        for line in lanes_file.read_text().splitlines():
            if not line.startswith("|") or line.startswith("| ---") or line.startswith("| Date"):
                continue
            cols = [c.strip() for c in line.split("|")]
            if len(cols) < 12:
                continue
            etc = cols[10] if len(cols) > 10 else ""
            # Handle comma/slash-separated multi-frontier lanes (L-818)
            fid_str_m = re.search(r"frontier=(F-[A-Z0-9,/\s-]+?)(?:;|$)", etc)
            if not fid_str_m or frontier_id not in re.findall(r"F-[A-Z0-9]+", fid_str_m.group(1)):
                continue
            sess_str = cols[3] if len(cols) > 3 else ""
            sess_m = re.search(r"S?(\d+)", sess_str)
            sess = int(sess_m.group(1)) if sess_m else 0
            # Prefer explicit mode=, then fall back to keyword inference on intent
            explicit_m = re.search(r"\bmode=(exploration|hardening|replication|resolution)\b", etc)
            if explicit_m:
                mode = explicit_m.group(1)
            else:
                intent_m = re.search(r"intent=([^;]+)", etc)
                intent = intent_m.group(1).lower() if intent_m else ""
                if any(kw in intent for kw in ("harden", "validat", "retest", "prospective",
                                                "verify", "audit", "replicat", "correct")):
                    mode = "hardening"
                elif any(kw in intent for kw in ("resolve", "close", "final", "build",
                                                  "implement", "integrat", "wire")):
                    mode = "resolution"
                else:
                    mode = "exploration"
            lanes.append((sess, mode))
    if not lanes:
        return None, 0
    lanes.sort(key=lambda x: x[0])
    return lanes[-1][1], len(lanes)


def append_open_row(
    lane_id: str,
    session: str,
    intent: str,
    expect: str,
    artifact: str,
    frontier: str,
    focus: str,
    check_mode: str,
    personality: str,
    scope_key: str,
    author: str,
    model: str,
    branch: str,
    domain: str,
    note: str,
    mode: str = "",
    level: str = "L2",
    role: str = "",
    self_apply: str = "",
) -> None:
    today = date.today().isoformat()

    # Build scope key from domain or explicit override
    if not scope_key and domain:
        scope_key = f"domains/{domain}/tasks/FRONTIER.md"
    elif not scope_key and focus.startswith("domains/"):
        scope_key = f"{focus}/tasks/FRONTIER.md" if not focus.endswith(".md") else focus

    # Determine domain_sync and memory_target
    if focus.startswith("domains/") or domain:
        domain_path = domain or focus.split("/")[1] if "/" in focus else focus
        memory_target = scope_key or f"domains/{domain_path}/tasks/FRONTIER.md"
        domain_fields = f"; domain_sync=queued; memory_target={memory_target}"
    else:
        domain_fields = ""

    # Build Etc column — L-703: stripped zero-information constant fields
    # (personality=domain-expert carried 0 bits; only include when non-default)
    # Coordination tags (available/blocked/next_step/human_open_item) are required
    # by maintenance.py contract check — include with defaults (resolves open_lane/
    # maintenance design conflict identified in DOMEX-STR-S401 meta-swarm).
    etc_parts = [
        f"focus={focus}",
        f"intent={intent}",
        f"check_mode={check_mode}",
        f"level={level}",
        "setup=active",
        "available=yes",
        "blocked=clear",
        "next_step=run-experiment",
        "human_open_item=no-escalations",
    ]
    if mode:
        etc_parts.append(f"mode={mode}")
    if role:
        etc_parts.append(f"role={role}")
    if self_apply:
        etc_parts.append(f"self_apply={self_apply}")
    if personality and personality != "domain-expert":
        etc_parts.append(f"personality={personality}")
    if frontier:
        etc_parts.append(f"frontier={frontier}")
    etc_parts += [
        f"expect={expect}",
        f"actual=TBD",
        f"diff=TBD",
        f"artifact={artifact}",
        f"progress=active",
    ]
    if domain_fields:
        etc_parts.append(domain_fields.lstrip("; "))

    etc = "; ".join(etc_parts)

    line = (
        f"| {today} | {lane_id} | {session} | {author} | {branch} | - | {model} | "
        f"claude-code+wsl | {scope_key} | {etc} | ACTIVE | {note} |\n"
    )
    with open(LANES_FILE, "a") as f:
        f.write(line)
    display = LANES_FILE.relative_to(REPO_ROOT) if LANES_FILE.is_relative_to(REPO_ROOT) else LANES_FILE
    print(f"Opened lane {lane_id} → {display} [ACTIVE]")
    print(f"  expect  : {expect}")
    print(f"  artifact: {artifact}")


def main():
    parser = argparse.ArgumentParser(
        description="Open a swarm lane with required evidence fields at creation time."
    )
    parser.add_argument("--lane", required=True, help="Lane ID, e.g. DOMEX-BRN-S331")
    parser.add_argument("--session", required=True, help="Current session tag, e.g. S331")
    parser.add_argument("--expect", required=True,
                        help="Predicted outcome before acting (required — F-META1 enforcement)")
    parser.add_argument("--artifact", required=True,
                        help="Path to experiment artifact to be produced (required — F-META1 enforcement)")
    parser.add_argument("--frontier", default="", help="Frontier ID(s) being advanced, e.g. F-BRN2")
    parser.add_argument("--intent", default="", help="Short intent label for Etc column")
    parser.add_argument("--focus", default="global", help="Scope focus, e.g. domains/brain (default: global)")
    parser.add_argument("--check-mode", default="objective",
                        choices=["objective", "historian", "verification", "coordination", "assumption"],
                        help="Check mode for this lane (default: objective)")
    parser.add_argument("--personality", default="domain-expert",
                        help="Agent personality profile (default: domain-expert)")
    parser.add_argument("--scope-key", default="", help="Override scope-key column (defaults to domain FRONTIER.md)")
    parser.add_argument("--domain", default="", help="Domain shortname for auto-filling domain fields")
    parser.add_argument("--note", default="",
                        help="Opening note for Notes column")
    parser.add_argument("--author", default=NODE_AI_SESSION,
                        help=f"Author node type (default: {NODE_AI_SESSION}, per NODES.md)")
    parser.add_argument("--model", default="claude-sonnet-4-6", help="Model used")
    parser.add_argument("--branch", default="master", help="Branch (default: master)")
    parser.add_argument("--level", default="L2", choices=list(VALID_LEVELS),
                        help=(
                            "Epistemic level of planned work (L-895, SIG-46): "
                            "L1=observation, L2=measurement (default), L3=strategy, "
                            "L4=architecture, L5=paradigm. L3+ lessons count as 2x in "
                            "dispatch yield to counteract measurement gravity."
                        ))
    parser.add_argument("--mode", default="", choices=list(VALID_MODES) + [""],
                        help=(
                            "Campaign wave mode: exploration | hardening | replication | resolution. "
                            "Recorded as mode= in Etc; preferred over intent= keyword inference. "
                            "Required for 2nd+ wave lanes (F-STR3, L-766)."
                        ))
    parser.add_argument("--role", default="", choices=list(VALID_META_ROLES) + [""],
                        help=(
                            "Meta-role for meta DOMEX lanes (SIG-39): historian | tooler | experimenter. "
                            "Recorded as role= in Etc; read by dispatch_optimizer.py for meta-role balance."
                        ))
    parser.add_argument("--self-apply", default="",
                        help=(
                            "PHIL-22 self-application statement: how will this finding feed back "
                            "into the swarm's own process? Required for L3+ lanes (L-950, SIG-48). "
                            "Example: 'If confirmed, wire threshold into dispatch_optimizer.py scoring'"
                        ))
    parser.add_argument("--force", action="store_true",
                        help="Open lane even if lane ID already exists (not recommended)")
    parser.add_argument("--skip-falsification-check", default="",
                        metavar="REASON",
                        help=(
                            "Override falsification-rate block with a stated reason. "
                            "Required when recent falsification rate is 0/N and this is not "
                            "a falsification lane. Reason is recorded in lane notes. "
                            "Example: --skip-falsification-check 'meta tooling session, no belief to falsify'"
                        ))
    args = parser.parse_args()

    if lane_exists(args.lane) and not args.force:
        print(f"ERROR: Lane {args.lane} already exists in SWARM-LANES.md.", file=sys.stderr)
        print("Use --force to open a duplicate row (not recommended).", file=sys.stderr)
        sys.exit(1)

    # L-908 maintenance gate: warn about stale ACTIVE lanes before creating new ones
    try:
        sess_num = int(re.search(r"\d+", args.session).group())
        stale_active = []
        for line in LANES_FILE.read_text().splitlines():
            if "| ACTIVE |" not in line:
                continue
            cols = [c.strip() for c in line.split("|")]
            if len(cols) < 12:
                continue
            lane_sess = re.search(r"S?(\d+)", cols[3])
            if lane_sess and sess_num - int(lane_sess.group(1)) > 3:
                stale_active.append(cols[2].strip())
        if stale_active:
            print(
                f"WARN: {len(stale_active)} stale ACTIVE lane(s) from >3 sessions ago: "
                f"{', '.join(stale_active[:3])}. Close or ABANDON before opening new lanes (L-908).",
                file=sys.stderr,
            )
    except Exception:
        pass

    # SIG-39 meta-role enforcement: detect meta lanes and suggest --role
    is_meta = "META" in args.lane.upper() or args.domain == "meta"
    if is_meta and not args.role:
        print(
            f"WARN: Meta DOMEX lane without --role. Meta-tooler is most underserved (13.7%). "
            f"Add --role historian|tooler|experimenter for dispatch visibility (SIG-39, L-601).",
            file=sys.stderr,
        )

    # FM-22 maintenance gate: check domain frontier staleness before creating new work
    # L-908: creation-maintenance asymmetry is the meta-failure-mode.
    # 81.4% of domain frontiers are >15s stale (S429 baseline).
    # Structural enforcement: block lane creation for deeply stale domains.
    if args.domain:
        try:
            domain_frontier = REPO_ROOT / "domains" / args.domain / "tasks" / "FRONTIER.md"
            if domain_frontier.exists():
                header_text = domain_frontier.read_text()[:500]
                # Prefer "Updated: S<N>" over "Seeded: S<N>" — seeded date is immutable
                sess_m = re.search(r"Updated:\s*S(\d+)", header_text) or re.search(r"S(\d+)", header_text)
                if sess_m:
                    last_update = int(sess_m.group(1))
                    frontier_age = int(re.search(r"\d+", args.session).group()) - last_update
                    if frontier_age > 50 and not args.force:
                        print(
                            f"BLOCKED: Domain '{args.domain}' frontier is {frontier_age} sessions stale "
                            f"(last update S{last_update}). FM-22 maintenance gate requires frontier "
                            f"maintenance before new work. Update the domain frontier first, or use "
                            f"--force to override (L-908, FM-22).",
                            file=sys.stderr,
                        )
                        sys.exit(1)
                    elif frontier_age > 30:
                        print(
                            f"WARN: Domain '{args.domain}' frontier is {frontier_age} sessions stale "
                            f"(last update S{last_update}). Consider updating domain FRONTIER.md "
                            f"before opening new work (FM-22, L-908).",
                            file=sys.stderr,
                        )
        except Exception:
            pass

    # P-274 creation-time enforcement: suggest matching global frontiers for domain lanes (L-938)
    if args.domain and not args.frontier:
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from frontier_crosslink import load_global_frontiers, load_domain_frontiers, compute_suggestions
            gf = load_global_frontiers()
            df = load_domain_frontiers()
            domain_only = {k: v for k, v in df.items() if v.get("domain") == args.domain}
            suggestions = compute_suggestions(domain_only, gf, min_overlap=8)[:3]
            if suggestions:
                top = [f"{s['domain_id']}→{s['global_id']}({s['overlap_count']}t)" for s in suggestions]
                print(f"INFO: Domain '{args.domain}' has global frontier candidates: {', '.join(top)} — add --frontier to link (P-274, L-938).", file=sys.stderr)
        except Exception:
            pass

    if not args.intent:
        args.intent = f"advance-{args.frontier}" if args.frontier else "swarm-work"
    if not args.note:
        args.note = f"Lane opened via open_lane.py. Frontier: {args.frontier or 'TBD'}."

    # P-243 science quality: reject vague --expect values (pre-registration enforcement)
    # Post-hoc threshold selection is the most common methodology weakness (L-804)
    for pattern in VAGUE_EXPECT_PATTERNS:
        if re.match(pattern, args.expect.strip(), re.IGNORECASE):
            print(
                f"ERROR: --expect value '{args.expect}' is too vague for pre-registration (P-243). "
                f"A falsifiable hypothesis must include: (1) a specific quantitative prediction, "
                f"(2) a threshold for confirmation/falsification. "
                f"Example: 'K_avg ~2.6 at N=724; S372 model holds within 5% OOS'",
                file=sys.stderr,
            )
            sys.exit(1)

    # P-243 science quality: check if expect contains a number (quantitative prediction)
    if not re.search(r"\d", args.expect):
        print(
            f"WARN: --expect '{args.expect[:60]}...' contains no numeric prediction. "
            f"P-243 requires quantitative thresholds for pre-registration. "
            f"Add a number (e.g., '>50%', '~2.6', 'n>=10', 'ΔBIC>10').",
            file=sys.stderr,
        )

    # P-243 falsification mandate: track recent lanes and enforce 1-in-5 adversarial ratio
    # L-601: advisory display = 0% adoption; blocking enforcement = near-100% (L-949)
    # Upgraded from WARN to ERROR to match structural enforcement pattern (PHIL-22/--self-apply).
    # S482 F-META18: debt tracking — skips accumulate cost, block after 3 consecutive
    debt_path = REPO_ROOT / "workspace" / "falsification-debt.json"
    try:
        debt = json.loads(debt_path.read_text())
    except (OSError, json.JSONDecodeError):
        debt = {"consecutive_skips": 0, "total_skips": 0,
                "last_skip_session": None, "last_falsification_session": None,
                "max_consecutive_before_block": 3}

    if args.mode == "falsification":
        print(
            f"INFO: Adversarial lane — explicitly testing against a belief/claim. "
            f"Target: prove the expect WRONG. Record DROP if falsified (P-243, L-804).",
        )
        # Clear debt on falsification lane
        debt["consecutive_skips"] = 0
        debt["last_falsification_session"] = args.session
        debt_path.write_text(json.dumps(debt, indent=2) + "\n")
    else:
        # Check debt: after max_consecutive_before_block skips, MUST falsify (no bypass)
        max_skips = debt.get("max_consecutive_before_block", 3)
        if debt.get("consecutive_skips", 0) >= max_skips:
            print(
                f"ERROR: Falsification debt exhausted ({debt['consecutive_skips']}/{max_skips} "
                f"consecutive non-falsification lanes). P-243 requires the NEXT lane to use "
                f"--mode falsification. Run 'python3 tools/dispatch_optimizer.py' to see "
                f"suggested falsification targets. No bypass available (L-601).",
                file=sys.stderr,
            )
            sys.exit(1)

        # Count recent falsification lanes vs total (last 20 sessions)
        recent_falsification = 0
        recent_total = 0
        sess_num_m = re.search(r"\d+", args.session)
        cur_sess = int(sess_num_m.group()) if sess_num_m else 0
        for lanes_file in (LANES_FILE, LANES_ARCHIVE):
            if not lanes_file.exists():
                continue
            for line in lanes_file.read_text().splitlines():
                if not line.startswith("|") or line.startswith("| ---") or line.startswith("| Date"):
                    continue
                cols = [c.strip() for c in line.split("|")]
                if len(cols) < 12:
                    continue
                etc = cols[10] if len(cols) > 10 else ""
                sess_m = re.search(r"S?(\d+)", cols[3] if len(cols) > 3 else "")
                if not sess_m:
                    continue
                sess = int(sess_m.group(1))
                if sess < max(1, cur_sess - 20):
                    continue
                recent_total += 1
                if "; mode=falsification" in etc or etc.startswith("mode=falsification"):
                    recent_falsification += 1
        falsif_rate = recent_falsification / recent_total if recent_total > 0 else 1.0
        if recent_total >= 5 and falsif_rate < 0.20:
            msg = (
                f"ERROR: "
                f"{recent_falsification}/{recent_total} recent lanes use mode=falsification "
                f"({falsif_rate:.0%} vs 20% target). "
                f"P-243 requires 1-in-5 adversarial lanes (L-601: voluntary → structural enforcement). "
                f"Options: (1) --mode falsification --expect '<belief> is FALSE because <reason>', "
                f"(2) --skip-falsification-check 'reason' to override with justification."
            )
            # L-601 structural enforcement: hard-block at <20%, not just at 0%
            # S483 F-META18 fix: advisory-only at >0% caused 1.1% actual rate (18x below target)
            if args.skip_falsification_check:
                # Increment debt on skip
                debt["consecutive_skips"] = debt.get("consecutive_skips", 0) + 1
                debt["total_skips"] = debt.get("total_skips", 0) + 1
                debt["last_skip_session"] = args.session
                debt_path.write_text(json.dumps(debt, indent=2) + "\n")
                remaining = max_skips - debt["consecutive_skips"]
                print(
                    f"INFO: Falsification-rate block overridden: '{args.skip_falsification_check}'. "
                    f"Debt: {debt['consecutive_skips']}/{max_skips} skips "
                    f"({remaining} remaining before mandatory falsification).",
                )
            else:
                print(msg, file=sys.stderr)
                sys.exit(1)

    # PHIL-22 enforcement: L3+ lanes must state self-application (L-950, SIG-48)
    # L-949: advisory display = 0% adoption; blocking enforcement = near-100%
    if args.level in ("L3", "L4", "L5") and not args.self_apply:
        print(
            f"ERROR: --self-apply is required for {args.level} lanes (PHIL-22, L-950). "
            f"State how this finding feeds back into the swarm's own process. "
            f"Example: --self-apply 'If confirmed, modify dispatch scoring to weight X'",
            file=sys.stderr,
        )
        sys.exit(1)

    # Wave-mode enforcement: require --mode for 2nd+ wave lanes (F-STR3, L-766, L-601)
    # L-601: voluntary protocols decay to structural floor at creation. Only creation-time
    # enforcement sustains. Mode enforcement was voluntary S390-S393 with 0% adoption.
    if args.frontier:
        prev_mode, wave_count = get_frontier_previous_mode(args.frontier)
        if prev_mode is not None:
            wave_num = wave_count + 1  # this lane is the next wave
            if not args.mode:
                print(
                    f"ERROR: {args.frontier} is on wave {wave_num} (last mode: {prev_mode}). "
                    f"--mode is required for 2nd+ wave lanes to prevent valley-of-death stalls "
                    f"(L-755/L-766/L-601). Choose: {', '.join(VALID_MODES)}",
                    file=sys.stderr,
                )
                sys.exit(1)
            elif args.mode == prev_mode:
                print(
                    f"WARN: mode={args.mode} repeats previous wave mode for {args.frontier} (wave {wave_num}). "
                    f"Mode-repeat is the #1 predictor of valley-of-death stalls (L-755/L-766). "
                    f"Consider a different mode: {', '.join(m for m in VALID_MODES if m != args.mode)}",
                    file=sys.stderr,
                )
            else:
                print(
                    f"INFO: mode shift {prev_mode} → {args.mode} for {args.frontier} (wave {wave_num}) — "
                    f"mode transition increases resolution probability (L-755)."
                )

    append_open_row(
        lane_id=args.lane,
        session=args.session,
        intent=args.intent,
        expect=args.expect,
        artifact=args.artifact,
        frontier=args.frontier,
        focus=args.focus,
        check_mode=args.check_mode,
        personality=args.personality,
        scope_key=args.scope_key,
        author=args.author,
        model=args.model,
        branch=args.branch,
        domain=args.domain,
        note=args.note,
        mode=args.mode,
        level=args.level,
        role=args.role,
        self_apply=getattr(args, 'self_apply', ''),
    )

    # Skeleton artifact creation (L-984, SIG-49): create experiment JSON template
    # at lane-open time so 'actual' is present as TBD from the start.
    # close_lane.py will error if 'actual' is still TBD on MERGED.
    artifact_path = REPO_ROOT / args.artifact
    if artifact_path.suffix == ".json" and not artifact_path.exists():
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        domain_val = args.domain or (args.focus.split("/")[1] if "/" in args.focus else args.focus)
        skeleton = {
            "experiment": args.lane,
            "frontier": args.frontier or "",
            "session": args.session,
            "domain": domain_val,
            "date": date.today().isoformat(),
            "expect": args.expect,
            "actual": "TBD",
            "diff": "TBD",
        }
        artifact_path.write_text(json.dumps(skeleton, indent=4) + "\n")
        print(f"  skeleton: {args.artifact} (fill 'actual' before MERGED)")


if __name__ == "__main__":
    main()
