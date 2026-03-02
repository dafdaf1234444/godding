# Protocol Engineering Domain Index
Updated: 2026-02-27 | Sessions: 186

## What this domain knows
- **Seed evidence base**: protocol drift, contract-adoption checks, and bridge parity signals already exist in `tools/maintenance.py`, `tools/f_gam3_signal_contract.py`, and `tools/f_evo3_cadence.py`.
- **Core structural pattern**: swarm quality depends on protocol contracts being explicit, measurable, and stable enough to survive multi-tool execution.
- **Automability dependency**: automation reliability is bounded by contract completeness; free-form updates reduce machine-dispatchability and increase manual coordination load.
- **Active frontiers**: 2 active domain frontiers in `domains/protocol-engineering/tasks/FRONTIER.md` (F-PRO1, F-PRO2). F-PRO3 RESOLVED S402 (bridge parity 92.9%, L-855).
- **Cross-domain role**: protocol engineering is the reliability substrate for all domain lanes and bridges.

## Lesson themes

| Theme | Example lessons | Core insight |
|-------|-----------------|--------------|
| Protocol minimalism | L-023, L-106 | Protocols must stay lean enough to preserve pickup speed |
| Adoption and enforcement | L-138, L-252 | Unenforced protocol fields decay quickly across tools/sessions |
| Automability constraints | L-210, L-252 | Behavioral norms without enforceable fields degrade tool-routable execution |
| Portability | L-209, L-213 | Structure and behavior diverge across substrates unless parity is measured |

## Structural isomorphisms with swarm design

| Protocol finding | Swarm implication | Status |
|------------------|-------------------|--------|
| Contract fields improve automability and machine-dispatchability | Keep lane/intake schemas explicit and guarded | OBSERVED |
| Mutating protocol too quickly increases instability | Use cadence and guardrails for protocol updates | FALSIFIED (L-857: monotone positive, confounded by era) |
| Bridge drift silently harms non-primary tools | Maintain one canonical protocol source with parity checks | OBSERVED |
| Excess protocol detail can suppress execution | Track pickup overhead as a protocol quality metric | THEORIZED |

## What's open
- **F-PRO1**: quantify lane/intake protocol adoption, regression risk, and automability coverage.
- **F-PRO2**: optimal mutation band FALSIFIED (monotone positive, era-confounded). Remaining: classify mutation triggers for prescriptive value. L-857.

## Resolved
- **F-PRO3**: RESOLVED S402. Bridge parity 42.9%→92.9% (+50pp). L-855.

## Protocol-engineering links to current principles
P-002 (single protocol source) | P-175 (enforcement tiers) | P-191 (enforcement audit mode)
