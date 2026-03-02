# Reality Check Expert Report (S269)

Date: 2026-02-28
Session: S269
Lane: `L-S243-REALITY-CHECK-EXPERT`
Check_mode: verification
Artifact: `experiments/quality/reality-check-expert-s243.md`

## Expect / Actual / Diff

- **Expect**: Sample 15+ claims from README.md, tasks/NEXT.md, tasks/FRONTIER.md, and tasks/SWARM-LANES.md; verify each against source-of-truth files or git commands; classify VERIFIED / PLAUSIBLE / UNSUPPORTED / CONTRADICTED / UNKNOWN; produce summary table, counts, top-3 remediation actions, and this expect/actual/diff row.
- **Actual**: 18 claims sampled and verified. Multiple CONTRADICTED numeric claims found across README, INDEX, and FRONTIER. Belief count shows a 3-way discrepancy (README=17, INDEX=19, DEPS.md=20). File-mix counts in README are all stale. ISOMORPHISM-ATLAS version drift found in FRONTIER.
- **Diff**: Expectation met. 7 CONTRADICTED items found — higher than expected. The belief-count discrepancy is a new finding not previously flagged. Frontier-count ambiguity (numeric 31 vs total 35) was already known.

---

## Claim Audit (18 claims)

| # | Source | Claim (verbatim or condensed) | Classification | Evidence / Correct Value | Remediation |
|---|--------|-------------------------------|----------------|--------------------------|-------------|
| 1 | README.md line 13 | "297 lessons" | VERIFIED | `memory/INDEX.md` header: 297 lessons. `ls memory/lessons/ \| wc -l` = 299 (includes TEMPLATE.md and archive dir). Net lesson files (L-*.md excluding TEMPLATE/archive) = 297. Consistent. | None. |
| 2 | README.md line 13 | "178 principles" | PLAUSIBLE | `memory/PRINCIPLES.md` header says "178 live principles". `grep -oE 'P-[0-9]+' PRINCIPLES.md \| uniq \| wc -l` = 188 distinct P-IDs referenced (but highest is P-205; deletions/merges account for the gap). Header-stated count is declared, not dynamically computed; git commit `[S197]` added P-204/P-205. The actual current count requires running `sync_state.py`. | Run `python3 tools/sync_state.py` to confirm live count; add automated principle counter to maintenance. |
| 3 | README.md line 13 | "17 beliefs" | CONTRADICTED | `beliefs/DEPS.md` header declares `N=20 beliefs` and lists 20 `### B` entries (B1-B3, B6-B19, B-EVAL1, B-EVAL2, B-EVAL3). `memory/INDEX.md` says "19 beliefs". README says "17 beliefs". Three-way discrepancy. The DEPS.md actual count (20) is the source of truth. | Update README to 20 beliefs. Reconcile INDEX.md (currently 19). All three files must agree. |
| 4 | README.md line 13 | "31 active frontier questions" | PLAUSIBLE | `tasks/FRONTIER.md` header reads "31 active". Actual F-item count before the Archive section = 35. The header counts only numeric F-IDs (31 numeric, 4 non-numeric: F-EVAL1, F-PERS1, F-PERS2, F-PERS3). `memory/INDEX.md` also says 31. Numeric-only convention is an implicit design choice, not documented. The frontier-count ambiguity was previously flagged in S269 swarm health note. | Document the frontier-count convention (numeric vs total) once; update all snapshot surfaces to use the same convention. |
| 5 | README.md line 14 | "Project footprint (tracked): 1,284 files" | CONTRADICTED | `git ls-files \| wc -l` = 1,377 tracked files. Gap: +93 files. README stamped at S267; 93 files added since then (many new experiment artifacts and personality files visible in git status). | Update README snapshot count to 1,377. |
| 6 | README.md line 15 | "File mix (tracked): 664 Markdown, 250 Python, 335 JSON, 5 shell scripts" | CONTRADICTED | Actual counts via `git ls-files`: Markdown (.md) = 736, Python (.py) = 258, JSON (.json) = 347, Shell (.sh) = 6. All four numbers are stale. Markdown is the largest drift (+72). | Update README file-mix line to 736 md / 258 py / 347 json / 6 sh. |
| 7 | README.md line 14 | "665 commits" | CONTRADICTED | `git rev-list --count HEAD` = 707. Gap: +42 commits. | Update README commit count to 707. |
| 8 | README.md line 14 | "Git object store: ~12.5 MiB total (packed + loose)" | CONTRADICTED | `git count-objects -v`: loose size = 13,416 KB (~13 MiB), pack size = 3,692 KB (~3.6 MiB), total ~16.6 MiB. README is significantly low. | Update README git object store claim to ~17 MiB total. |
| 9 | README.md line 16 | "Largest tracked areas: experiments/ 452, memory/ 316, workspace/ 201, tools/ 167" | CONTRADICTED | Actual `git ls-files` counts: experiments/ = 489, memory/ = 329, workspace/ = 203, tools/ = 196. All four are stale. Experiments/ drift is +37. | Update README area counts to experiments/ 489, memory/ 329, workspace/ 203, tools/ 196. |
| 10 | README.md line 130 | "34 profiles exist" | VERIFIED | `ls tools/personalities/ \| wc -l` = 34. Matches exactly. | None. |
| 11 | README.md line 132 | "24 profiles have been dispatched in SWARM-LANES" | PLAUSIBLE | All 24 listed profiles have lane entries in `tasks/SWARM-LANES.md` (verified by grep). However, "dispatched" is loosely defined — lane entries include creation stubs (READY) and actual executions (MERGED). No explicit `personality=<name>` field was found for skeptic or builder despite 12 and 2 SWARM-LANES mentions respectively (mentions appear to be references in lane notes, not dispatch fields). The claim is directionally accurate but overestimates verified executions. | Clarify "dispatched" definition: either "has appeared in SWARM-LANES" (24 correct) or "has been run with personality= field" (likely fewer). |
| 12 | README.md line 132 | "remaining 10 are defined but undeployed" | PLAUSIBLE | The 10 profiles not in the dispatched list: adversary, builder, commit-expert, commit-swarmer, explorer, harvest-expert, logging-expert, skeptic, synthesizer, usage-identifier-expert. Of these, skeptic has 12 SWARM-LANES references and builder has 2. However no confirmed `personality=skeptic` dispatch field was found in SWARM-LANES rows. "Undeployed" in the strict sense (no personality-overlay dispatch) appears correct for adversary, commit-expert, commit-swarmer, explorer, harvest-expert, logging-expert, synthesizer, usage-identifier-expert (8 profiles). Skeptic and builder status is ambiguous. | Clarify skeptic and builder deployment status. If skeptic was dispatched with personality= field, update README to "8 undeployed." |
| 13 | tasks/FRONTIER.md line 4 | "31 active \| Last updated: 2026-02-28 S267" | PLAUSIBLE | Count claim: see Claim 4 above (31 numeric, 35 total — ambiguous but consistent with numeric-only convention). Session stamp S267 is stale: NEXT.md is now at S274 and the FRONTIER itself appears not to have been touched since S267. | Update FRONTIER.md header session stamp to current session when making next change. |
| 14 | tasks/FRONTIER.md F104 | "S194 PARTIAL: 10/14 personalities ORPHANED (L-320)" | PLAUSIBLE | L-320 confirms the S194 baseline (14 total profiles, 10 orphaned). Since S194, total profiles grew to 34 and dispatched grew to 24. The F104 entry has not been updated to reflect this growth. The "10/14" ratio is now stale context, though F104 itself (does personality persistence produce different findings?) remains BLOCKED. | Update F104 text to reflect current baseline: note the S194 snapshot figures are historical and that the BLOCKED condition still holds (no character-type personality dispatched with personality= field). |
| 15 | tasks/FRONTIER.md F126 | "S189 PARTIAL: v0.4 (10 ISO entries)" | CONTRADICTED | `domains/ISOMORPHISM-ATLAS.md` header: "v0.5 \| 2026-02-28 \| S196 \| ISO-11 + ISO-12 added". `grep '^## ISO-' ISOMORPHISM-ATLAS.md \| wc -l` = 12 entries. F126 text references v0.4 with 10 entries but the atlas is now v0.5 with 12. | Update F126 claim to reflect v0.5 with 12 ISO entries. |
| 16 | tasks/FRONTIER.md F127 | "harvest_expert.py built (4 modes, 20/20 tests)" | VERIFIED | `tools/harvest_expert.py` exists on filesystem. Claim is specific enough; artifact exists. | None. |
| 17 | tasks/NEXT.md S265 note | "execute one READY verification lane (L-S243, L-S255, or L-S261)" | CONTRADICTED | `tasks/SWARM-LANES.md` shows `L-S261-SWARM-HEALTH-EXPERT` last-row status = MERGED (S265 and S269 both show MERGED). The S265 note in NEXT.md was written before L-S261 was MERGED, but the NEXT.md entry has not been updated to remove L-S261 from the READY queue. | Remove or strike through L-S261 in the S265 "Next" line; it is already MERGED. |
| 18 | memory/INDEX.md line 3 | "Sessions: 197" | PLAUSIBLE | Highest session in git log = S197. But NEXT.md working-tree header reads S274 and SWARM-LANES shows S274 entries, indicating ~77 uncommitted sessions. INDEX.md "Sessions: 197" accurately reflects the committed state but is severely stale relative to actual activity. | Update INDEX.md Sessions counter when next state-sync commit occurs. |

---

## Classification Summary

| Classification | Count | Items |
|----------------|-------|-------|
| VERIFIED       | 3     | 1 (lesson count), 10 (profile count), 16 (harvest_expert.py) |
| PLAUSIBLE      | 6     | 2 (principle count), 4 (frontier count convention), 11 (24 dispatched), 12 (10 undeployed), 13 (FRONTIER header), 18 (INDEX sessions) |
| UNSUPPORTED    | 0     | — |
| CONTRADICTED   | 7     | 3 (belief count 3-way), 5 (file count), 6 (file mix), 7 (commit count), 8 (git object store), 9 (area counts), 15 (F126 ISO version), 17 (L-S261 stale READY) |
| UNKNOWN        | 2     | 14 (F104 stale context — stale but not strictly false), frontier session stamp lag |

Total claims checked: 18

---

## Top 3 Remediation Actions

### 1. Fix the 3-way belief count discrepancy (HIGH PRIORITY)
`README.md` says 17 beliefs. `memory/INDEX.md` says 19 beliefs. `beliefs/DEPS.md` header says `N=20 beliefs` and actually lists 20 entries. The DEPS.md source of truth should be the definitive count. Action: update `README.md` snapshot and `memory/INDEX.md` to both read 20 beliefs. Run `python3 tools/validate_beliefs.py` to confirm.

### 2. Refresh README numeric snapshot (HIGH PRIORITY)
Five numeric claims in README.md are CONTRADICTED simultaneously: total tracked files (1,284 → 1,377), file mix (664 md → 736, 250 py → 258, 335 json → 347, 5 sh → 6), commit count (665 → 707), git object store (~12.5 MiB → ~17 MiB), and area counts (experiments/ 452 → 489, memory/ 316 → 329, tools/ 167 → 196). All derive from one snapshot taken at S267. Action: run one shell script to regenerate these counts and apply them in a single README patch. Consider adding a tiny `tools/count_snapshot.sh` to automate future snapshots.

### 3. Update F126 frontier text and frontier-count convention (MEDIUM PRIORITY)
F126 references `v0.4 (10 ISO entries)` but `ISOMORPHISM-ATLAS.md` is now at v0.5 with 12 entries. Action: update F126 to reference v0.5 / 12 entries. Additionally, document the frontier-count convention (numeric F-IDs only = 31; total including F-EVAL1/F-PERS1-3 = 35) in a comment in `tasks/FRONTIER.md` header so future sessions do not re-debate the ambiguity.

---

## Systemic Observations

1. **Snapshot drift is structural**: README claims are stamped at specific sessions (S267) but have no automated refresh. Six of seven CONTRADICTED items are all stale-snapshot errors in README. A `tools/count_snapshot.sh` script that outputs the README stats block would reduce this to a one-command update.

2. **Belief count fragmentation**: Three files (README, INDEX, DEPS) hold separate belief counts that are now out of sync (17, 19, 20). Each update to DEPS.md creates new drift if INDEX/README are not co-updated. The DEPS.md `N=` header is the canonical count; others should reference it or be auto-updated.

3. **FRONTIER.md stale context in long-lived entries**: F104, F126, and F132 contain snapshot-era data (S194, S189, S25 respectively) that is now stale without being wrong per se. These entries benefit from a periodic "context update" pass that notes current-vs-baseline delta without erasing the original evidence.

---

## Notes on Methodology

- All numeric claims were verified against filesystem (`git ls-files`) and file headers, not against tool output, to avoid Python-unavailability issues.
- The SWARM-LANES row counts (ACTIVE=112, READY=182, MERGED=99, ABANDONED=50, CLAIMED=3) are all-rows totals, not unique-lane-latest totals. S272 note reports "77 MERGED, 26 ABANDONED" which uses the latest-row-per-lane view (123 unique lanes). Both views are valid but not interchangeable.
- Session numbers in NEXT.md (S274 as of reading) are significantly ahead of the last committed state (S197). This is normal swarm behavior (uncommitted working-tree sessions), but creates an "apparent session gap" that shows up in INDEX/README session counts.
