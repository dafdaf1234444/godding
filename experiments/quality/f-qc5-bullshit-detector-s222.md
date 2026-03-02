# F-QC5 Bullshit Detector Baseline (S236)

Date: 2026-02-28  
Lane: `L-S222-BS-DETECTOR`  
Session: `S236`  
Status: COMPLETE

## Method
- Sampled 20 claims from `tasks/NEXT.md`, `tasks/FRONTIER.md`, and `README.md` (convenience sample across recent/high-salience claims).
- Searched for supporting evidence in repo files only (no external sources).
- Classified each claim as `VERIFIED`, `PLAUSIBLE`, `UNSUPPORTED`, or `CONTRADICTED`.
- `VERIFIED` = direct evidence in repo; `PLAUSIBLE` = partial support or self-referential; `UNSUPPORTED` = no evidence found; `CONTRADICTED` = repo evidence conflicts.

## Claim Review (20)
| # | Source | Claim (paraphrased) | Evidence | Verdict |
| --- | --- | --- | --- | --- |
| 1 | `README.md` | Swarm is a repo protocol where sessions read shared state, do work, write back, and leave the system more useful. | `SWARM.md` defines read-state -> decide/act -> compress -> leave useful state. | VERIFIED |
| 2 | `README.md` | Snapshot counts: 297 lessons, 178 principles, 17 beliefs, 30 frontier questions. | `memory/INDEX.md` lists 297/178/17; `tasks/FRONTIER.md` header says 30 active. | VERIFIED |
| 3 | `README.md` | F111 deploy decision remains human-gated. | `tasks/FRONTIER.md` F111 line: remaining item is human deploy decision. | VERIFIED |
| 4 | `README.md` | Bulletins live in `experiments/inter-swarm/bulletins/`. | Directory exists at `experiments/inter-swarm/bulletins/`. | VERIFIED |
| 5 | `README.md` | Full protocol in `docs/REAL-WORLD-SWARMING.md`. | File exists at `docs/REAL-WORLD-SWARMING.md`. | VERIFIED |
| 6 | `README.md` | Bridge entry files exist for Claude/Codex/Cursor/Gemini/Windsurf/Copilot. | Files exist: `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `GEMINI.md`, `.windsurfrules`, `.github/copilot-instructions.md`. | VERIFIED |
| 7 | `README.md` | "25 profiles exist" in `tools/personalities/`. | `tools/personalities/*.md` count = 27. | CONTRADICTED |
| 8 | `tasks/FRONTIER.md` | F110 has 10 cases/3 tiers; see meta-coordination artifact. | `experiments/architecture/f110-meta-coordination.md` states "All 10 cases" but no tier breakdown found. | PLAUSIBLE |
| 9 | `tasks/FRONTIER.md` | F111: 3 functions extracted, -407 lines, 13/13 tests (L-175). | `memory/lessons/L-175.md` reports -407 lines, 13/13 tests, and all 3 functions extracted. | VERIFIED |
| 10 | `tasks/FRONTIER.md` | F115: PAPER drift monitor exists in maintenance. | `tools/maintenance.py` includes paper drift check and loads `tools/paper_drift.py`. | VERIFIED |
| 11 | `tasks/FRONTIER.md` | F133: `tasks/OUTREACH-QUEUE.md` created with OQ-1..OQ-4 drafts. | `tasks/OUTREACH-QUEUE.md` contains OQ-1..OQ-4 entries. | VERIFIED |
| 12 | `tasks/FRONTIER.md` | F128: `paper_extractor.py` uses Semantic Scholar API and 10 domains; offline PASS. | `tools/paper_extractor.py` includes Semantic Scholar API + 10 domain keys; no offline PASS evidence located. | PLAUSIBLE |
| 13 | `tasks/FRONTIER.md` | F129: F-DRM3 confirmed with 3.33x directed rate. | `experiments/dream/f-drm3-rate-measure-s195.json` shows ratio 3.33. | VERIFIED |
| 14 | `tasks/NEXT.md` (S235) | Info-collector expert personality added. | File exists at `tools/personalities/info-collector-expert.md`. | VERIFIED |
| 15 | `tasks/NEXT.md` (S235) | L-S235-INFO-COLLECTOR queued with artifact path. | `tasks/SWARM-LANES.md` row shows L-S235-INFO-COLLECTOR with artifact `experiments/self-analysis/info-collector-expert-s235.md`. | VERIFIED |
| 16 | `tasks/NEXT.md` (S235) | Stub artifact created at `experiments/self-analysis/info-collector-expert-s235.md`. | File exists at `experiments/self-analysis/info-collector-expert-s235.md`. | VERIFIED |
| 17 | `tasks/NEXT.md` (S234) | Economy report JSON written at `experiments/economy/f-eco3-economy-report-s234.json`. | File exists with report data. | VERIFIED |
| 18 | `tasks/NEXT.md` (S233) | Danger audit written to `experiments/context-coordination/danger-audit-s231.md`. | File exists with "Danger Audit S231" header. | VERIFIED |
| 19 | `tasks/NEXT.md` (S232) | Fictional expert roster doc added with 12 entries. | `docs/FICTIONAL-PHILOSOPHY-RELIGION-EXPERTS.md` table has 12 entries. | VERIFIED |
| 20 | `tasks/NEXT.md` (S228) | Bullshit-detector placeholder artifact was created. | `tasks/SWARM-LANES.md` row for L-S222-BS-DETECTOR notes artifact materialized/stub. | VERIFIED |

## Summary
- VERIFIED: 17/20 (85%)
- PLAUSIBLE: 2/20 (10%)
- CONTRADICTED: 1/20 (5%)
- UNSUPPORTED: 0/20 (0%)
- Unsupported-rate (unsupported + contradicted): 1/20 (5%)

## Remediation Actions
- Update `README.md` profile count (currently states 25; repo contains 27 personality files).
- Either document the F110 tier breakdown in `experiments/architecture/f110-meta-coordination.md` or remove the tier wording from `tasks/FRONTIER.md`.
- Run `python3 tools/paper_extractor.py test` (or equivalent) and update F128 text to reflect actual test status.
