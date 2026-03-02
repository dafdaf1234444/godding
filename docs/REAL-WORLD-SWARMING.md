# Real-World Swarming

Practical scope for what this swarm can execute in collaborative reality, not just local experiments.

## Objective

Turn incoming work (branches, PR-style diffs, repeated contributor traffic) into structured swarm execution:
- partition work safely
- parallelize where possible
- keep hot shared state coordinated
- leave reproducible artifacts for the next node

## What Is Swarmable Now

### 1) Multi-setup operation
- Host capability detection already exists: `python3 tools/maintenance.py --inventory`.
- Universal validation already exists: `bash tools/check.sh --quick`.
- Bridge files already support multiple tools (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.cursorrules`, `.windsurfrules`, Copilot instructions).

### 2) PR/branch intake planning
- New tool: `python3 tools/swarm_pr.py plan <base-ref> <head-ref>`
- Output includes:
  - change lanes (`core-state`, `tooling`, `docs`, `domains`, `experiments`, `workspace`, `other`)
  - recommended topology per lane (fanout-safe vs cooperative)
  - stable diff fingerprint (de-dup key)

### 3) Contributor PR spam handling
- Queue command: `python3 tools/swarm_pr.py enqueue <base-ref> <head-ref>`
- Queue view: `python3 tools/swarm_pr.py queue`
- Fingerprint-based de-dup prevents repeated intake of identical open diffs.

## Near-Term Swarm Targets

### A) Branch execution runner
Add a worktree-aware executor that takes a `swarm_pr plan` and runs lanes in parallel child sessions, then collects outputs into one reconciliation pass.

### B) CI-triggered intake (Implemented)
- Workflow: `.github/workflows/swarm-pr-intake.yml`
- Trigger: PR open/reopen/update/ready-for-review
- Behavior:
  - runs `python3 tools/swarm_pr.py plan <base-sha> <head-sha> --json`
  - uploads `swarm-pr-plan.json` + rendered summary markdown as workflow artifacts
  - posts/updates a sticky PR comment with mode + lane split

### C) Tool-native adapters
Standardize launch wrappers for each supported tool runtime so the same intake artifact can be executed by Codex, Claude, Copilot, etc. with the same protocol and checks.

### D) Baseline CI guard (Implemented)
- Workflow: `.github/workflows/swarm-check.yml`
- Trigger: pushes to `master/main` and all pull requests
- Behavior: runs `bash tools/check.sh --quick` as the minimum swarm integrity gate

## Later: External Data Integration

External data should be a gated lane, not default behavior:
- explicit source allowlist per task
- source citation + timestamp in artifacts
- cache raw payloads under `workspace/` for reproducibility
- separate factual ingestion from interpretation (two-step verification)

This keeps collaborative swarming auditable while still allowing real-world data use.

## Suggested Operating Loop (Contributor-Driven)

1. Fetch contributor branch.
2. Run intake planning:
   - `python3 tools/swarm_pr.py plan origin/master <contributor-branch>`
3. Queue it for swarm execution:
   - `python3 tools/swarm_pr.py enqueue origin/master <contributor-branch>`
4. Execute lanes (coordinator + fanout workers based on plan mode).
5. Reconcile and validate:
   - `bash tools/check.sh --quick`
6. Merge only after lane outputs are consistent and checks pass.

This is the minimum viable collaborative swarm loop for real branch/PR traffic.
