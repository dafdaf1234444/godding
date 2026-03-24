#!/usr/bin/env python3
"""
swarm_peer.py — Peer swarm discovery and coordination (GAP-1, F-SWARMER2).

Closes the inter-swarm coordination gap: swarms can register peers,
check compatibility, and exchange state via git remotes.

Usage:
    python3 tools/swarm_peer.py register <name> <git-url> [--note "..."]
    python3 tools/swarm_peer.py list
    python3 tools/swarm_peer.py check <name>          # run merge_compatibility against peer
    python3 tools/swarm_peer.py fetch <name>           # shallow-clone peer, read their state
    python3 tools/swarm_peer.py exchange <name>        # post bulletin + fetch peer bulletins
    python3 tools/swarm_peer.py sync <name>             # bidirectional state diff + merge report
    python3 tools/swarm_peer.py resolve <name>          # detect + classify conflicts, propose resolutions
    python3 tools/swarm_peer.py remove <name>
"""

import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PEERS_FILE = ROOT / "workspace" / "swarm-peers.json"
BULLETINS_DIR = ROOT / "experiments" / "inter-swarm" / "bulletins"


def load_peers() -> dict:
    if PEERS_FILE.exists():
        return json.loads(PEERS_FILE.read_text())
    return {"schema": "swarm-peers-v1", "peers": {}}


def save_peers(data: dict) -> None:
    PEERS_FILE.write_text(json.dumps(data, indent=2) + "\n")


def cmd_register(args: list[str]) -> None:
    if len(args) < 2:
        print("Usage: register <name> <git-url> [--note '...']")
        sys.exit(1)
    name, url = args[0], args[1]
    note = ""
    if "--note" in args:
        idx = args.index("--note")
        if idx + 1 < len(args):
            note = args[idx + 1]

    peers = load_peers()
    now = datetime.now(timezone.utc).isoformat()
    peers["peers"][name] = {
        "url": url,
        "registered": now,
        "last_check": None,
        "compatibility": None,
        "note": note,
    }
    save_peers(peers)
    print(f"Registered peer '{name}' at {url}")


def cmd_list(_args: list[str]) -> None:
    peers = load_peers()
    if not peers["peers"]:
        print("No peers registered. Use: swarm_peer.py register <name> <git-url>")
        return
    print(f"{'Name':<20} {'Compat':<12} {'Last Check':<22} URL")
    print("-" * 80)
    for name, info in sorted(peers["peers"].items()):
        compat = info.get("compatibility") or "unknown"
        last = (info.get("last_check") or "never")[:19]
        print(f"{name:<20} {compat:<12} {last:<22} {info['url']}")


def cmd_check(args: list[str]) -> None:
    if not args:
        print("Usage: check <name>")
        sys.exit(1)
    name = args[0]
    peers = load_peers()
    if name not in peers["peers"]:
        print(f"Unknown peer '{name}'. Register first.")
        sys.exit(1)

    url = peers["peers"][name]["url"]
    print(f"Checking compatibility with '{name}' ({url})...")

    with tempfile.TemporaryDirectory(prefix="swarm-peer-") as tmpdir:
        # Shallow clone peer repo
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--single-branch", url, tmpdir],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            print(f"FAIL: Could not clone {url}")
            print(result.stderr[:500])
            return

        # Check if it's a swarm
        peer_swarm = Path(tmpdir) / "SWARM.md"
        if not peer_swarm.exists():
            print(f"NOT A SWARM: {url} has no SWARM.md")
            peers["peers"][name]["compatibility"] = "not-swarm"
            peers["peers"][name]["last_check"] = datetime.now(timezone.utc).isoformat()
            save_peers(peers)
            return

        # Run merge_compatibility.py
        mc_path = ROOT / "tools" / "merge_compatibility.py"
        result = subprocess.run(
            [sys.executable, str(mc_path), tmpdir, "--json"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            print(f"merge_compatibility.py failed: {result.stderr[:300]}")
            return

        try:
            compat = json.loads(result.stdout)
            zone = compat.get("zone", "unknown")
            distance = compat.get("overall_distance", -1)
        except (json.JSONDecodeError, KeyError):
            zone = "parse-error"
            distance = -1

        now = datetime.now(timezone.utc).isoformat()
        peers["peers"][name]["compatibility"] = zone
        peers["peers"][name]["distance"] = distance
        peers["peers"][name]["last_check"] = now
        save_peers(peers)

        print(f"Zone: {zone} | Distance: {distance:.3f}")
        if zone == "HETEROSIS":
            print("  OPTIMAL for mutual swarming")
        elif zone == "CAUTIOUS":
            print("  Viable with careful arbitration")
        elif zone == "INCOMPATIBLE":
            print("  NOT viable — core axioms contradict")
        elif zone == "INBREEDING":
            print("  Too similar — low hybrid vigor expected")


def cmd_fetch(args: list[str]) -> None:
    if not args:
        print("Usage: fetch <name>")
        sys.exit(1)
    name = args[0]
    peers = load_peers()
    if name not in peers["peers"]:
        print(f"Unknown peer '{name}'.")
        sys.exit(1)

    url = peers["peers"][name]["url"]
    print(f"Fetching state from '{name}' ({url})...")

    with tempfile.TemporaryDirectory(prefix="swarm-peer-") as tmpdir:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--single-branch", url, tmpdir],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            print(f"FAIL: Could not clone {url}")
            return

        peer = Path(tmpdir)
        # Read key state files
        for rel in [
            "beliefs/PHILOSOPHY.md", "beliefs/CORE.md", "memory/INDEX.md",
            "tasks/FRONTIER.md", "tasks/NEXT.md",
        ]:
            p = peer / rel
            if p.exists():
                lines = p.read_text(errors="ignore").split("\n")
                header = lines[0] if lines else "(empty)"
                count = len(lines)
                print(f"  {rel}: {count}L — {header[:80]}")
            else:
                print(f"  {rel}: MISSING")

        # Count lessons and principles
        lessons = list((peer / "memory" / "lessons").glob("L-*.md")) if (peer / "memory" / "lessons").exists() else []
        tools_dir = list((peer / "tools").glob("*.py")) if (peer / "tools").exists() else []
        print(f"  Lessons: {len(lessons)} | Tools: {len(tools_dir)}")

        # Extract peer's active frontiers
        peer_frontier = peer / "tasks" / "FRONTIER.md"
        if peer_frontier.exists():
            ftext = peer_frontier.read_text(errors="ignore")
            resolved_idx = ftext.find("\n## Resolved")
            if resolved_idx > 0:
                ftext = ftext[:resolved_idx]
            peer_frontiers = re.findall(r"^- \*\*(\S+)\*\*:", ftext, re.MULTILINE)
            print(f"  Active frontiers: {len(peer_frontiers)} ({', '.join(peer_frontiers[:5])}{'...' if len(peer_frontiers) > 5 else ''})")
        else:
            print("  Active frontiers: MISSING (no FRONTIER.md)")

        # Check for bulletins from them
        peer_bulletins = peer / "experiments" / "inter-swarm" / "bulletins"
        if peer_bulletins.exists():
            bfiles = list(peer_bulletins.glob("*.md"))
            print(f"  Bulletins: {len(bfiles)} files")
        else:
            print("  Bulletins: none (no inter-swarm dir)")


def _extract_local_frontiers() -> list[str]:
    """Extract active frontier IDs + summaries from local FRONTIER.md."""
    frontier_path = ROOT / "tasks" / "FRONTIER.md"
    if not frontier_path.exists():
        return []
    text = frontier_path.read_text()
    resolved_idx = text.find("\n## Resolved")
    if resolved_idx > 0:
        text = text[:resolved_idx]
    frontiers = []
    for m in re.finditer(r"^- \*\*(\S+)\*\*:\s*(.+?)$", text, re.MULTILINE):
        frontiers.append(f"{m.group(1)}: {m.group(2).strip()[:120]}")
    return frontiers


def cmd_exchange(args: list[str]) -> None:
    if not args:
        print("Usage: exchange <name> [--push-bulletin]")
        sys.exit(1)
    push_bulletin = "--push-bulletin" in args
    args = [a for a in args if a != "--push-bulletin"]
    name = args[0]
    peers = load_peers()
    if name not in peers["peers"]:
        print(f"Unknown peer '{name}'.")
        sys.exit(1)

    url = peers["peers"][name]["url"]

    # 1. Post a bulletin about ourselves
    our_index = ROOT / "memory" / "INDEX.md"
    state_line = "unknown"
    if our_index.exists():
        for line in our_index.read_text().split("\n"):
            if "lessons" in line.lower() and "principles" in line.lower():
                state_line = line.strip()[:100]
                break

    # Extract our active frontiers for the exchange
    frontier_lines = _extract_local_frontiers()
    frontier_block = "\n".join(f"  - {f}" for f in frontier_lines) if frontier_lines else "(none)"

    BULLETINS_DIR.mkdir(parents=True, exist_ok=True)
    our_name = ROOT.name  # repo directory name as swarm identity
    bulletin_file = BULLETINS_DIR / f"peer-exchange-{name}.md"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    bulletin_content = (
        f"# Bulletin from: {our_name}\n"
        f"Date: {now}\n"
        f"Type: sibling-sync\n"
        f"Trust-Tier: T3\n\n"
        f"## Content\n"
        f"Peer exchange initiated with {name} ({url}).\n"
        f"Our state: {state_line}\n\n"
        f"## Active Frontiers ({len(frontier_lines)})\n"
        f"{frontier_block}\n\n"
        f"## Evidence\n"
        f"Automated peer exchange via swarm_peer.py\n---\n"
    )

    # Append (don't overwrite)
    with open(bulletin_file, "a") as f:
        f.write(bulletin_content)
    print(f"Posted exchange bulletin: {bulletin_file.name}")

    # 2. Fetch peer bulletins
    print(f"Fetching bulletins from '{name}'...")
    with tempfile.TemporaryDirectory(prefix="swarm-peer-") as tmpdir:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--single-branch", url, tmpdir],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            print(f"FAIL: Could not clone {url}")
            return

        peer_bulletins = Path(tmpdir) / "experiments" / "inter-swarm" / "bulletins"
        if not peer_bulletins.exists():
            print("  Peer has no bulletins directory")
            return

        imported = 0
        for bfile in sorted(peer_bulletins.glob("*.md")):
            dest = BULLETINS_DIR / f"from-{name}-{bfile.name}"
            if not dest.exists():
                dest.write_text(bfile.read_text(errors="ignore"))
                imported += 1

        print(f"  Imported {imported} new bulletins from {name}")

    # 3. Push our bulletin to peer via dedicated branch (F-SWARMER2 transport)
    if push_bulletin:
        _push_bulletin_to_peer(name, url, bulletin_file)

    now_iso = datetime.now(timezone.utc).isoformat()
    peers["peers"][name]["last_exchange"] = now_iso
    if push_bulletin:
        peers["peers"][name]["last_push"] = now_iso
    save_peers(peers)


def _push_bulletin_to_peer(name: str, url: str, bulletin_file: Path) -> None:
    """Push our bulletin to peer repo on a dedicated branch.

    Creates branch 'incoming/<our-name>' in the peer repo containing our
    bulletin. The peer can review and merge at their discretion — no force
    push, no main branch modification. Transport is git-native.
    """
    our_name = ROOT.name
    branch = f"incoming/{our_name}"
    print(f"Pushing bulletin to '{name}' on branch '{branch}'...")

    with tempfile.TemporaryDirectory(prefix="swarm-push-") as tmpdir:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--single-branch", url, tmpdir],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            print(f"  FAIL: Could not clone {url} for push")
            return

        subprocess.run(
            ["git", "checkout", "-B", branch],
            capture_output=True, text=True, cwd=tmpdir,
        )

        peer_bulletins = Path(tmpdir) / "experiments" / "inter-swarm" / "bulletins"
        peer_bulletins.mkdir(parents=True, exist_ok=True)
        dest = peer_bulletins / f"from-{our_name}.md"
        dest.write_text(bulletin_file.read_text())

        fp = _compute_state_fingerprint(ROOT)
        fp_file = peer_bulletins / f"fingerprint-{our_name}.json"
        fp_file.write_text(json.dumps(fp, indent=2, default=str) + "\n")

        subprocess.run(
            ["git", "add", "-A"], capture_output=True, text=True, cwd=tmpdir,
        )
        result = subprocess.run(
            ["git", "commit", "-m",
             f"[inter-swarm] bulletin from {our_name} to {name}"],
            capture_output=True, text=True, cwd=tmpdir,
        )
        if result.returncode != 0:
            print("  No changes to push (bulletin already up to date)")
            return

        result = subprocess.run(
            ["git", "push", "origin", branch],
            capture_output=True, text=True, cwd=tmpdir, timeout=60,
        )
        if result.returncode != 0:
            print(f"  FAIL: push rejected — {result.stderr.strip()[:200]}")
            return

        print(f"  Pushed bulletin to {name}:{branch}")


def _compute_state_fingerprint(root: Path) -> dict:
    """Extract structured state fingerprint from a swarm repo root."""
    fp: dict = {"frontiers": [], "beliefs": [], "phils": [], "lessons": [],
                "lesson_count": 0, "principle_count": 0, "tool_count": 0,
                "session": "unknown", "identity": "unknown"}

    # Identity (repo name)
    fp["identity"] = root.name

    # Session from NEXT.md or INDEX.md header
    for rel in ["tasks/NEXT.md", "memory/INDEX.md"]:
        p = root / rel
        if p.exists():
            header = p.read_text(errors="ignore").split("\n")[0]
            m = re.search(r"S(\d+)", header)
            if m:
                fp["session"] = f"S{m.group(1)}"
                break

    # Active frontiers (IDs only)
    frontier_path = root / "tasks" / "FRONTIER.md"
    if frontier_path.exists():
        text = frontier_path.read_text(errors="ignore")
        resolved_idx = text.find("\n## Resolved")
        if resolved_idx > 0:
            text = text[:resolved_idx]
        for m_f in re.finditer(r"^- \*\*(\S+)\*\*:", text, re.MULTILINE):
            fid = m_f.group(1)
            if not fid.startswith("~~"):
                fp["frontiers"].append(fid)

    # Beliefs from DEPS.md — format is B1, B2, B-EVAL1, etc.
    deps_path = root / "beliefs" / "DEPS.md"
    if deps_path.exists():
        for m_b in re.finditer(r"\b(B-?\w+\d+)\b", deps_path.read_text(errors="ignore")):
            bid = m_b.group(1)
            if bid.startswith("B") and bid not in fp["beliefs"]:
                fp["beliefs"].append(bid)

    # Philosophy claims — format is **[PHIL-N]**
    phil_path = root / "beliefs" / "PHILOSOPHY.md"
    if phil_path.exists():
        for m_p in re.finditer(r"\*\*\[PHIL-(\d+)\]\*\*", phil_path.read_text(errors="ignore")):
            fp["phils"].append(f"PHIL-{m_p.group(1)}")

    # Lesson IDs (last 50 by filename sort for recent comparison)
    lessons_dir = root / "memory" / "lessons"
    if lessons_dir.exists():
        all_lessons = sorted(lessons_dir.glob("L-*.md"))
        fp["lesson_count"] = len(all_lessons)
        fp["lessons"] = [lf.stem for lf in all_lessons[-50:]]

    # Principle count — format is P-NNN (plain, not bold) in themed sections
    principles_path = root / "memory" / "PRINCIPLES.md"
    if principles_path.exists():
        text_p = principles_path.read_text(errors="ignore")
        fp["principle_count"] = len(set(re.findall(r"\bP-\d{3}\b", text_p)))

    # Tool count
    tools_dir = root / "tools"
    if tools_dir.exists():
        fp["tool_count"] = len(list(tools_dir.glob("*.py")))

    return fp


def _diff_fingerprints(local: dict, peer: dict) -> dict:
    """Compute bidirectional diff between two state fingerprints."""
    diff: dict = {}

    for key in ["frontiers", "beliefs", "phils", "lessons"]:
        local_set = set(local.get(key, []))
        peer_set = set(peer.get(key, []))
        diff[f"{key}_only_local"] = sorted(local_set - peer_set)
        diff[f"{key}_only_peer"] = sorted(peer_set - local_set)
        diff[f"{key}_shared"] = sorted(local_set & peer_set)

    # Numeric comparisons
    for key in ["lesson_count", "principle_count", "tool_count"]:
        diff[f"{key}_local"] = local.get(key, 0)
        diff[f"{key}_peer"] = peer.get(key, 0)
        diff[f"{key}_delta"] = local.get(key, 0) - peer.get(key, 0)

    diff["local_session"] = local.get("session", "unknown")
    diff["peer_session"] = peer.get("session", "unknown")

    return diff


def cmd_sync(args: list[str]) -> None:
    """Bidirectional sync: compute state diff with a peer, generate sync report."""
    if not args:
        print("Usage: sync <name> [--post-bulletin]")
        sys.exit(1)
    name = args[0]
    post_bulletin = "--post-bulletin" in args

    peers = load_peers()
    if name not in peers["peers"]:
        print(f"Unknown peer '{name}'. Register first.")
        sys.exit(1)

    url = peers["peers"][name]["url"]
    print(f"=== BIDIRECTIONAL SYNC: {name} ({url}) ===\n")

    # 1. Compute local fingerprint
    local_fp = _compute_state_fingerprint(ROOT)
    print(f"Local state ({local_fp['identity']}): {local_fp['session']} | "
          f"{local_fp['lesson_count']}L {local_fp['principle_count']}P "
          f"{len(local_fp['frontiers'])}F {len(local_fp['phils'])}PHIL "
          f"{local_fp['tool_count']} tools")

    # 2. Clone peer and compute their fingerprint
    with tempfile.TemporaryDirectory(prefix="swarm-sync-") as tmpdir:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--single-branch", url, tmpdir],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            print(f"FAIL: Could not clone {url}")
            print(result.stderr[:300])
            return

        peer_root = Path(tmpdir)
        if not (peer_root / "SWARM.md").exists():
            print(f"NOT A SWARM: {url} has no SWARM.md")
            return

        peer_fp = _compute_state_fingerprint(peer_root)
        print(f"Peer state ({peer_fp['identity']}): {peer_fp['session']} | "
              f"{peer_fp['lesson_count']}L {peer_fp['principle_count']}P "
              f"{len(peer_fp['frontiers'])}F {len(peer_fp['phils'])}PHIL "
              f"{peer_fp['tool_count']} tools")

        # 3. Compute diff
        diff = _diff_fingerprints(local_fp, peer_fp)

        print(f"\n--- STATE DIFF ---")
        print(f"Sessions: local={diff['local_session']} peer={diff['peer_session']}")
        print(f"Lessons: local={diff['lesson_count_local']} peer={diff['lesson_count_peer']} "
              f"(delta={diff['lesson_count_delta']:+d})")
        print(f"Principles: local={diff['principle_count_local']} peer={diff['principle_count_peer']} "
              f"(delta={diff['principle_count_delta']:+d})")
        print(f"Tools: local={diff['tool_count_local']} peer={diff['tool_count_peer']} "
              f"(delta={diff['tool_count_delta']:+d})")

        # Frontiers
        if diff["frontiers_only_local"]:
            print(f"\nFrontiers only LOCAL ({len(diff['frontiers_only_local'])}):")
            for f_id in diff["frontiers_only_local"][:10]:
                print(f"  + {f_id}")
        if diff["frontiers_only_peer"]:
            print(f"\nFrontiers only PEER ({len(diff['frontiers_only_peer'])}):")
            for f_id in diff["frontiers_only_peer"][:10]:
                print(f"  - {f_id}")
        if diff["frontiers_shared"]:
            print(f"\nShared frontiers: {len(diff['frontiers_shared'])}")

        # Philosophy claims
        if diff["phils_only_local"]:
            print(f"\nPHIL claims only LOCAL ({len(diff['phils_only_local'])}): "
                  f"{', '.join(diff['phils_only_local'][:10])}")
        if diff["phils_only_peer"]:
            print(f"\nPHIL claims only PEER ({len(diff['phils_only_peer'])}): "
                  f"{', '.join(diff['phils_only_peer'][:10])}")

        # Recent lessons unique to each
        if diff["lessons_only_peer"]:
            print(f"\nRecent lessons only PEER ({len(diff['lessons_only_peer'])}):")
            for lid in diff["lessons_only_peer"][:10]:
                # Try to read the lesson title from peer
                lpath = peer_root / "memory" / "lessons" / f"{lid}.md"
                title = lid
                if lpath.exists():
                    first_line = lpath.read_text(errors="ignore").split("\n")[0]
                    title = first_line.lstrip("# ").strip()[:100]
                print(f"  → {title}")

        # 4. Sync report
        sync_report = {
            "schema": "swarm-sync-v1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "local": {"identity": local_fp["identity"], "session": local_fp["session"],
                      "lessons": local_fp["lesson_count"], "tools": local_fp["tool_count"]},
            "peer": {"identity": peer_fp["identity"], "name": name, "url": url,
                     "session": peer_fp["session"], "lessons": peer_fp["lesson_count"],
                     "tools": peer_fp["tool_count"]},
            "diff": {
                "frontiers_only_local": diff["frontiers_only_local"],
                "frontiers_only_peer": diff["frontiers_only_peer"],
                "frontiers_shared": len(diff["frontiers_shared"]),
                "phils_only_local": diff["phils_only_local"],
                "phils_only_peer": diff["phils_only_peer"],
                "lessons_only_peer": diff["lessons_only_peer"][:20],
                "lesson_delta": diff["lesson_count_delta"],
                "principle_delta": diff["principle_count_delta"],
                "tool_delta": diff["tool_count_delta"],
            },
            "merge_candidates": [],
        }

        # Identify merge candidates: peer lessons we don't have
        for lid in diff["lessons_only_peer"][:10]:
            lpath = peer_root / "memory" / "lessons" / f"{lid}.md"
            if lpath.exists():
                text = lpath.read_text(errors="ignore")
                # Extract domain and Sharpe if present
                from lesson_header import parse_domain_field
                _doms = parse_domain_field(text[:500])
                sharpe_m = re.search(r"Sharpe:\s*(\d+)", text)
                sync_report["merge_candidates"].append({
                    "id": lid,
                    "domain": _doms[0] if _doms else "unknown",
                    "sharpe": int(sharpe_m.group(1)) if sharpe_m else 0,
                    "first_line": text.split("\n")[0].lstrip("# ").strip()[:100],
                })

        # Save sync report
        sync_dir = ROOT / "workspace" / "sync-reports"
        sync_dir.mkdir(parents=True, exist_ok=True)
        report_path = sync_dir / f"sync-{name}-{datetime.now(timezone.utc).strftime('%Y%m%d')}.json"
        report_path.write_text(json.dumps(sync_report, indent=2) + "\n")
        print(f"\nSync report saved: {report_path.relative_to(ROOT)}")

        # 5. Post bulletin if requested
        if post_bulletin:
            BULLETINS_DIR.mkdir(parents=True, exist_ok=True)
            our_name = ROOT.name
            bulletin_file = BULLETINS_DIR / f"sync-{name}.md"
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            content = (
                f"\n---\n"
                f"# Bulletin from: {our_name}\n"
                f"Date: {now}\n"
                f"Type: sibling-sync\n"
                f"Trust-Tier: T3\n\n"
                f"## Content\n"
                f"Bidirectional sync with {name}.\n"
                f"Local: {local_fp['session']} {local_fp['lesson_count']}L | "
                f"Peer: {peer_fp['session']} {peer_fp['lesson_count']}L\n"
                f"Unique local frontiers: {len(diff['frontiers_only_local'])}\n"
                f"Unique peer frontiers: {len(diff['frontiers_only_peer'])}\n"
                f"Merge candidates: {len(sync_report['merge_candidates'])}\n\n"
                f"## Evidence\n"
                f"Automated bidirectional sync via swarm_peer.py sync\n"
            )
            with open(bulletin_file, "a") as bf:
                bf.write(content)
            print(f"Sync bulletin posted: {bulletin_file.name}")

        # Update peer record
        now_iso = datetime.now(timezone.utc).isoformat()
        peers["peers"][name]["last_sync"] = now_iso
        peers["peers"][name]["peer_session"] = peer_fp["session"]
        peers["peers"][name]["peer_lessons"] = peer_fp["lesson_count"]
        save_peers(peers)

    print(f"\n✓ Sync complete. Merge candidates: {len(sync_report['merge_candidates'])}")


def _classify_frontier_conflict(local_text: str, peer_text: str) -> dict:
    """Classify a frontier conflict between local and peer versions."""
    # Extract status keywords
    local_resolved = any(k in local_text.lower() for k in ["resolved", "confirmed", "falsified", "closed"])
    peer_resolved = any(k in peer_text.lower() for k in ["resolved", "confirmed", "falsified", "closed"])

    # Check for shared evidence markers
    local_lessons = set(re.findall(r"L-\d+", local_text))
    peer_lessons = set(re.findall(r"L-\d+", peer_text))
    shared_evidence = local_lessons & peer_lessons

    if local_resolved and peer_resolved:
        if shared_evidence:
            return {"type": "DUPLICATE", "resolution": "merge-keep-richer",
                    "detail": "Both resolved with shared evidence — keep version with more data"}
        return {"type": "CONTRADICTORY", "resolution": "adversarial-review",
                "detail": "Both claim resolution but different evidence — needs manual review"}
    elif local_resolved != peer_resolved:
        return {"type": "COMPLEMENTARY", "resolution": "adopt-resolution",
                "detail": "One resolved, one active — resolved version informs active"}
    elif shared_evidence:
        return {"type": "DUPLICATE", "resolution": "merge-deduplicate",
                "detail": "Both active with shared evidence — merge to avoid redundant work"}
    else:
        return {"type": "COMPLEMENTARY", "resolution": "split-parallel",
                "detail": "Both active, independent evidence — continue in parallel, sync later"}


def _classify_belief_conflict(local_text: str, peer_text: str, bid: str) -> dict:
    """Classify a belief conflict between local and peer belief text."""
    # Simple heuristic: check if texts share key phrases
    local_words = set(local_text.lower().split())
    peer_words = set(peer_text.lower().split())
    overlap = len(local_words & peer_words) / max(len(local_words | peer_words), 1)

    if overlap > 0.7:
        return {"type": "NEAR-DUPLICATE", "resolution": "merge-keep-newer",
                "detail": f"{bid}: >70% word overlap — versions converged independently"}
    elif overlap > 0.3:
        return {"type": "DIVERGENT", "resolution": "merge-with-arbitration",
                "detail": f"{bid}: partial overlap — beliefs diverged, needs lesson-backed arbitration"}
    else:
        return {"type": "CONTRADICTORY", "resolution": "challenge-required",
                "detail": f"{bid}: <30% overlap — fundamentally different claims, file mutual challenge"}


def cmd_resolve(args: list[str]) -> None:
    """Detect and classify conflicts with a peer swarm, propose resolutions."""
    if not args:
        print("Usage: resolve <name> [--json] [--apply]")
        sys.exit(1)
    name = args[0]
    output_json = "--json" in args

    peers = load_peers()
    if name not in peers["peers"]:
        print(f"Unknown peer '{name}'. Register first.")
        sys.exit(1)

    url = peers["peers"][name]["url"]
    print(f"=== CONFLICT RESOLUTION: {name} ({url}) ===\n")

    with tempfile.TemporaryDirectory(prefix="swarm-resolve-") as tmpdir:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--single-branch", url, tmpdir],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            print(f"FAIL: Could not clone {url}")
            return

        peer_root = Path(tmpdir)
        if not (peer_root / "SWARM.md").exists():
            print(f"NOT A SWARM: {url}")
            return

        local_fp = _compute_state_fingerprint(ROOT)
        peer_fp = _compute_state_fingerprint(peer_root)
        diff = _diff_fingerprints(local_fp, peer_fp)

        conflicts = []

        # --- 1. Frontier conflicts (shared frontiers with divergent state) ---
        print("--- Frontier Conflicts ---")
        shared_frontiers = diff["frontiers_shared"]
        frontier_conflicts = 0
        for fid in shared_frontiers:
            # Read local and peer frontier text for this ID
            local_text = ""
            peer_text = ""
            for fpath, text_store in [
                (ROOT / "tasks" / "FRONTIER.md", "local"),
                (peer_root / "tasks" / "FRONTIER.md", "peer"),
            ]:
                if fpath.exists():
                    content = fpath.read_text(errors="ignore")
                    # Extract the block for this frontier
                    pattern = rf"^- \*\*{re.escape(fid)}\*\*:(.+?)(?=^- \*\*|\Z)"
                    m = re.search(pattern, content, re.MULTILINE | re.DOTALL)
                    if m:
                        if text_store == "local":
                            local_text = m.group(1).strip()[:500]
                        else:
                            peer_text = m.group(1).strip()[:500]

            if local_text and peer_text:
                classification = _classify_frontier_conflict(local_text, peer_text)
                if classification["type"] != "DUPLICATE" or "shared evidence" not in classification.get("detail", ""):
                    frontier_conflicts += 1
                    conflicts.append({"scope": "frontier", "id": fid, **classification})
                    print(f"  {fid}: {classification['type']} → {classification['resolution']}")

        if frontier_conflicts == 0:
            print("  No frontier conflicts detected")

        # --- 2. Belief conflicts (shared beliefs with different content) ---
        print("\n--- Belief Conflicts ---")
        shared_beliefs = set(diff.get("beliefs_shared", []))
        belief_conflicts = 0

        local_deps = ROOT / "beliefs" / "DEPS.md"
        peer_deps = peer_root / "beliefs" / "DEPS.md"
        if local_deps.exists() and peer_deps.exists():
            local_deps_text = local_deps.read_text(errors="ignore")
            peer_deps_text = peer_deps.read_text(errors="ignore")

            for bid in sorted(shared_beliefs):
                # Extract belief block from each
                pattern = rf"(^|\n)(##?\s*{re.escape(bid)}[^\n]*\n(?:(?!^##?\s).*\n)*)"
                lm = re.search(pattern, local_deps_text)
                pm = re.search(pattern, peer_deps_text)
                if lm and pm:
                    classification = _classify_belief_conflict(
                        lm.group(2).strip()[:300], pm.group(2).strip()[:300], bid)
                    if classification["type"] != "NEAR-DUPLICATE":
                        belief_conflicts += 1
                        conflicts.append({"scope": "belief", "id": bid, **classification})
                        print(f"  {bid}: {classification['type']} → {classification['resolution']}")

        if belief_conflicts == 0:
            print("  No belief conflicts detected")

        # --- 3. Philosophy conflicts (PHIL claims unique to each) ---
        print("\n--- Philosophy Conflicts ---")
        phils_only_local = diff.get("phils_only_local", [])
        phils_only_peer = diff.get("phils_only_peer", [])
        phil_shared = diff.get("phils_shared", [])

        if phils_only_local:
            print(f"  Local-only claims ({len(phils_only_local)}): {', '.join(phils_only_local[:5])}")
            for pid in phils_only_local:
                conflicts.append({"scope": "philosophy", "id": pid,
                                  "type": "LOCAL-ONLY", "resolution": "propose-to-peer",
                                  "detail": f"{pid} exists locally but not in peer — propose for adoption"})
        if phils_only_peer:
            print(f"  Peer-only claims ({len(phils_only_peer)}): {', '.join(phils_only_peer[:5])}")
            for pid in phils_only_peer:
                conflicts.append({"scope": "philosophy", "id": pid,
                                  "type": "PEER-ONLY", "resolution": "evaluate-for-adoption",
                                  "detail": f"{pid} exists in peer but not locally — evaluate before adopting"})
        if not phils_only_local and not phils_only_peer:
            print("  No philosophy conflicts")

        # --- 4. Lane conflicts (both working same frontier) ---
        print("\n--- Lane Conflicts (active work) ---")
        lane_conflicts = _scan_lane_conflicts_for_resolve(peer_root)
        if lane_conflicts:
            for lc in lane_conflicts:
                print(f"  {lc['frontier']}: local={lc['local_lane']} peer={lc['peer_lane']} → {lc['resolution']}")
                conflicts.append({"scope": "lane", **lc})
        else:
            print("  No active lane conflicts")

        # --- Summary ---
        print(f"\n=== SUMMARY ===")
        print(f"Total conflicts: {len(conflicts)}")
        by_type = {}
        for c in conflicts:
            by_type[c["type"]] = by_type.get(c["type"], 0) + 1
        for t, count in sorted(by_type.items()):
            print(f"  {t}: {count}")

        by_resolution = {}
        for c in conflicts:
            by_resolution[c["resolution"]] = by_resolution.get(c["resolution"], 0) + 1
        print(f"\nResolution actions needed:")
        for r, count in sorted(by_resolution.items()):
            print(f"  {r}: {count}")

        # Save resolution report
        report = {
            "schema": "swarm-conflict-resolution-v1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "peer": name,
            "peer_url": url,
            "local_session": local_fp.get("session", "unknown"),
            "peer_session": peer_fp.get("session", "unknown"),
            "conflict_count": len(conflicts),
            "conflicts": conflicts,
            "by_type": by_type,
            "by_resolution": by_resolution,
        }

        resolve_dir = ROOT / "workspace" / "conflict-reports"
        resolve_dir.mkdir(parents=True, exist_ok=True)
        report_path = resolve_dir / f"resolve-{name}-{datetime.now(timezone.utc).strftime('%Y%m%d')}.json"
        report_path.write_text(json.dumps(report, indent=2) + "\n")
        print(f"\nReport saved: {report_path.relative_to(ROOT)}")

        if output_json:
            print(json.dumps(report, indent=2))

        return report


def _scan_lane_conflicts_for_resolve(peer_root: Path) -> list:
    """Detect lanes where local and peer are both actively working on same frontier."""
    conflicts = []

    # Read local SWARM-LANES.md for active lanes
    local_lanes = ROOT / "tasks" / "SWARM-LANES.md"
    peer_lanes = peer_root / "tasks" / "SWARM-LANES.md"

    if not local_lanes.exists() or not peer_lanes.exists():
        return conflicts

    def _extract_active_lanes(text: str) -> list[dict]:
        active = []
        for line in text.split("\n"):
            if "| ACTIVE |" in line or "| CLAIMED |" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 12:
                    lane_id = parts[2] if len(parts) > 2 else ""
                    # Extract frontier from Etc field
                    etc_field = parts[10] if len(parts) > 10 else ""
                    fm = re.search(r"frontier=(\S+?)(?:;|$)", etc_field)
                    frontier = fm.group(1) if fm else ""
                    if lane_id and frontier:
                        active.append({"lane_id": lane_id, "frontier": frontier})
        return active

    local_active = _extract_active_lanes(local_lanes.read_text(errors="ignore"))
    peer_active = _extract_active_lanes(peer_lanes.read_text(errors="ignore"))

    local_frontiers = {la["frontier"]: la["lane_id"] for la in local_active}
    peer_frontiers = {pa["frontier"]: pa["lane_id"] for pa in peer_active}

    shared = set(local_frontiers.keys()) & set(peer_frontiers.keys())
    for frontier in sorted(shared):
        conflicts.append({
            "frontier": frontier,
            "local_lane": local_frontiers[frontier],
            "peer_lane": peer_frontiers[frontier],
            "type": "ACTIVE-COLLISION",
            "resolution": "coordinate-or-split-scope",
            "detail": f"Both swarms actively working on {frontier} — coordinate scope split or merge findings",
        })

    return conflicts


def cmd_remove(args: list[str]) -> None:
    if not args:
        print("Usage: remove <name>")
        sys.exit(1)
    name = args[0]
    peers = load_peers()
    if name in peers["peers"]:
        del peers["peers"][name]
        save_peers(peers)
        print(f"Removed peer '{name}'")
    else:
        print(f"Peer '{name}' not found")


def _extract_identity_dimensions(root: Path) -> dict:
    """Extract identity dimensions from a swarm for negotiation (GAP-5, F-SWARMER2).

    Identity = what makes this swarm THIS swarm, not any swarm.
    Five dimensions: axioms, goals, methods, boundaries, lineage.
    """
    dims: dict = {
        "axioms": [],      # PHIL claims marked as axioms (identity-defining)
        "goals": [],       # PHIL-14 primary goals
        "methods": [],     # Core methods (from CORE.md)
        "boundaries": [],  # What this swarm refuses or constrains
        "lineage": {},     # Origin, age, scale — non-negotiable history
    }

    # Axioms: PHIL claims that are identity-defining (axiom in challenge table)
    phil_path = root / "beliefs" / "PHILOSOPHY.md"
    if phil_path.exists():
        phil_text = phil_path.read_text(errors="ignore")
        # Find axiom-tagged claims
        for m in re.finditer(r"\*\*\[PHIL-(\d+)\]\*\*\s*(.+?)(?=\n\n|\n\*\*\[PHIL|\Z)", phil_text, re.DOTALL):
            pid = f"PHIL-{m.group(1)}"
            claim_text = m.group(2).strip().split("\n")[0][:200]
            # Check if marked as axiom in challenge table or text
            if "axiom" in phil_text[m.start():m.end()+500].lower():
                dims["axioms"].append({"id": pid, "claim": claim_text, "type": "axiom"})
            elif "identity" in phil_text[m.start():m.end()+500].lower():
                dims["axioms"].append({"id": pid, "claim": claim_text, "type": "identity"})

        # Goals: PHIL-14 section — numbered goals with **bold** keywords
        goal_m = re.search(r"Primary goals.*?PHIL-14.*?\n(.*?)(?=\n## |\Z)", phil_text, re.DOTALL)
        if goal_m:
            for line in goal_m.group(1).splitlines():
                line = line.strip()
                if re.match(r"^\d+\.\s", line) or line.startswith("- **"):
                    dims["goals"].append(line[:200])

    # Methods: from CORE.md operating principles (numbered with **bold** headings)
    core_path = root / "beliefs" / "CORE.md"
    if core_path.exists():
        core_text = core_path.read_text(errors="ignore")
        for m in re.finditer(r"^\d+\.\s*\*\*(.+?)\*\*", core_text, re.MULTILINE):
            dims["methods"].append(m.group(1)[:100])

    # Boundaries: safety/constraint rules from CORE.md
    if core_path.exists():
        for m in re.finditer(r"(?:never|must not|refuse|forbidden|constraint)[^\n]*", core_text, re.I):
            dims["boundaries"].append(m.group(0).strip()[:150])

    # Lineage: non-negotiable history
    index_path = root / "memory" / "INDEX.md"
    if index_path.exists():
        idx_text = index_path.read_text(errors="ignore")
        session_m = re.search(r"S(\d+)", idx_text)
        if session_m:
            dims["lineage"]["sessions"] = int(session_m.group(1))
        lesson_m = re.search(r"(\d+)\s*(?:L|lessons?)", idx_text)
        if lesson_m:
            dims["lineage"]["lessons"] = int(lesson_m.group(1))

    genesis_path = root / "docs" / "GENESIS.md"
    if genesis_path.exists():
        dims["lineage"]["has_genesis"] = True

    return dims


def _negotiate_identity(local_dims: dict, peer_dims: dict) -> dict:
    """Produce identity negotiation report between two swarms.

    Negotiation rules (from F-MERGE1, L-1100):
    1. Axioms are NON-NEGOTIABLE — if they conflict, swarms are incompatible
    2. Goals can be MERGED if non-contradictory, or PARTITIONED if contradictory
    3. Methods are ADOPTABLE — either side can import
    4. Boundaries use STRICTEST-WINS (union of constraints)
    5. Lineage is PRESERVED — both histories survive (symbiogenesis, not absorption)
    """
    report: dict = {
        "compatibility": "UNKNOWN",
        "axiom_conflicts": [],
        "goal_alignment": [],
        "method_exchange": {"importable": [], "exportable": []},
        "boundary_union": [],
        "lineage_preserved": True,
        "negotiation_actions": [],
    }

    # 1. Axiom compatibility check (blocking)
    local_axiom_claims = {a["claim"][:80].lower() for a in local_dims["axioms"]}
    peer_axiom_claims = {a["claim"][:80].lower() for a in peer_dims["axioms"]}

    for la in local_dims["axioms"]:
        for pa in peer_dims["axioms"]:
            # Simple contradiction check: if both are axioms on same topic but different claim
            if la["id"] == pa["id"] and la["claim"][:80].lower() != pa["claim"][:80].lower():
                report["axiom_conflicts"].append({
                    "id": la["id"],
                    "local": la["claim"][:200],
                    "peer": pa["claim"][:200],
                    "verdict": "INCOMPATIBLE — axiom conflict requires human arbitration",
                })

    # 2. Goal alignment
    local_goals = set(g[:80].lower() for g in local_dims["goals"])
    peer_goals = set(g[:80].lower() for g in peer_dims["goals"])
    shared_goals = local_goals & peer_goals
    local_only = local_goals - peer_goals
    peer_only = peer_goals - local_goals

    if shared_goals:
        report["goal_alignment"].append(f"SHARED ({len(shared_goals)}): compatible, merge directly")
    if local_only:
        report["goal_alignment"].append(f"LOCAL-ONLY ({len(local_only)}): propose to peer or partition")
    if peer_only:
        report["goal_alignment"].append(f"PEER-ONLY ({len(peer_only)}): evaluate for adoption or partition")

    # 3. Method exchange
    local_methods = set(m.lower() for m in local_dims["methods"])
    peer_methods = set(m.lower() for m in peer_dims["methods"])
    report["method_exchange"]["importable"] = sorted(peer_methods - local_methods)[:10]
    report["method_exchange"]["exportable"] = sorted(local_methods - peer_methods)[:10]

    # 4. Boundary union (strictest wins)
    all_boundaries = set()
    for b in local_dims["boundaries"] + peer_dims["boundaries"]:
        all_boundaries.add(b[:100])
    report["boundary_union"] = sorted(all_boundaries)[:20]

    # 5. Compatibility verdict
    if report["axiom_conflicts"]:
        report["compatibility"] = "INCOMPATIBLE"
        report["negotiation_actions"].append(
            "BLOCK: Axiom conflicts detected. Human arbitration required before merge."
        )
    elif not shared_goals:
        report["compatibility"] = "ORTHOGONAL"
        report["negotiation_actions"].append(
            "PARTITION: No shared goals. Swarms can exchange methods but not merge identity."
        )
    else:
        report["compatibility"] = "COMPATIBLE"
        report["negotiation_actions"].extend([
            "MERGE axioms: union (no conflicts)",
            f"MERGE goals: {len(shared_goals)} shared + partition unique goals",
            f"EXCHANGE methods: import {len(report['method_exchange']['importable'])}, "
            f"export {len(report['method_exchange']['exportable'])}",
            f"MERGE boundaries: strictest-wins union ({len(report['boundary_union'])} total)",
            "PRESERVE lineage: both histories retained (symbiogenesis)",
        ])

    return report


def cmd_identity(args: list[str]) -> None:
    """GAP-5: Identity negotiation with a peer swarm (F-SWARMER2, L-1100).

    Compares identity dimensions (axioms, goals, methods, boundaries, lineage)
    and produces a negotiation protocol for safe merge.
    """
    if not args:
        print("Usage: identity <name> [--json]")
        print("  Compare identity dimensions and produce merge negotiation protocol.")
        sys.exit(1)

    name = args[0]
    output_json = "--json" in args

    peers = load_peers()
    if name not in peers["peers"]:
        print(f"Unknown peer '{name}'. Register first.")
        sys.exit(1)

    url = peers["peers"][name]["url"]
    print(f"=== IDENTITY NEGOTIATION: {name} ({url}) ===\n")

    with tempfile.TemporaryDirectory(prefix="swarm-identity-") as tmpdir:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--single-branch", url, tmpdir],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            print(f"FAIL: Could not clone {url}")
            return

        peer_root = Path(tmpdir)
        if not (peer_root / "SWARM.md").exists():
            print(f"NOT A SWARM: {url}")
            return

        local_dims = _extract_identity_dimensions(ROOT)
        peer_dims = _extract_identity_dimensions(peer_root)

        print(f"--- Local Identity ({len(local_dims['axioms'])} axioms, "
              f"{len(local_dims['goals'])} goals, {len(local_dims['methods'])} methods, "
              f"{len(local_dims['boundaries'])} boundaries) ---")
        for a in local_dims["axioms"][:5]:
            print(f"  [{a['type']}] {a['id']}: {a['claim'][:100]}")

        print(f"\n--- Peer Identity ({len(peer_dims['axioms'])} axioms, "
              f"{len(peer_dims['goals'])} goals, {len(peer_dims['methods'])} methods, "
              f"{len(peer_dims['boundaries'])} boundaries) ---")
        for a in peer_dims["axioms"][:5]:
            print(f"  [{a['type']}] {a['id']}: {a['claim'][:100]}")

        negotiation = _negotiate_identity(local_dims, peer_dims)

        print(f"\n--- Negotiation Result ---")
        print(f"  Compatibility: {negotiation['compatibility']}")

        if negotiation["axiom_conflicts"]:
            print(f"\n  AXIOM CONFLICTS ({len(negotiation['axiom_conflicts'])}):")
            for ac in negotiation["axiom_conflicts"]:
                print(f"    {ac['id']}: {ac['verdict']}")

        for ga in negotiation["goal_alignment"]:
            print(f"  Goals: {ga}")

        me = negotiation["method_exchange"]
        if me["importable"]:
            print(f"  Methods importable: {len(me['importable'])}")
        if me["exportable"]:
            print(f"  Methods exportable: {len(me['exportable'])}")

        print(f"  Boundary union: {len(negotiation['boundary_union'])} constraints")

        print(f"\n--- Actions ---")
        for action in negotiation["negotiation_actions"]:
            print(f"  → {action}")

        # Save report
        report = {
            "schema": "swarm-identity-negotiation-v1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "peer": name,
            "peer_url": url,
            "local_dimensions": {k: v if k != "lineage" else v
                                 for k, v in local_dims.items()},
            "peer_dimensions": {k: v if k != "lineage" else v
                                for k, v in peer_dims.items()},
            "negotiation": negotiation,
        }

        report_dir = ROOT / "workspace" / "identity-reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"identity-{name}-{datetime.now(timezone.utc).strftime('%Y%m%d')}.json"
        report_path.write_text(json.dumps(report, indent=2) + "\n")
        print(f"\nReport saved: {report_path.relative_to(ROOT)}")

        if output_json:
            print(json.dumps(report, indent=2))

        return report


COMMANDS = {
    "register": cmd_register,
    "list": cmd_list,
    "check": cmd_check,
    "fetch": cmd_fetch,
    "exchange": cmd_exchange,
    "sync": cmd_sync,
    "resolve": cmd_resolve,
    "identity": cmd_identity,
    "remove": cmd_remove,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("swarm_peer.py — Peer swarm discovery and coordination")
        print(f"Commands: {', '.join(COMMANDS)}")
        print("Usage: python3 tools/swarm_peer.py <command> [args...]")
        sys.exit(1)
    COMMANDS[sys.argv[1]](sys.argv[2:])


if __name__ == "__main__":
    main()
