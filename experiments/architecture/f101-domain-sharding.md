# F101: Domain Sharding Design
Session: 50 | Date: 2026-02-27 | Status: PROPOSAL

## Problem
Current ceiling: ~2 parallel agents before hot-file contention.
Hot files: INDEX.md, FRONTIER.md, DEPS.md, CLAUDE.md (all agents read/write these).
P-099: parallelism ceiling = writable hot-file count.

## Goal
Scale to N parallel agents = N active domains, without breaking single-domain sessions.

---

## Proposed Architecture: Layered Domain Sharding

### Layer 1: Global (read-only for domain agents)
```
beliefs/CORE.md           — purpose and principles (never modified mid-session)
beliefs/META-DEPS.md      — architecture beliefs (B1-B8, B11, B12, B16)
memory/META-INDEX.md      — compact cross-domain map (<50 lines)
CLAUDE.md                 — session protocol
```

### Layer 2: Domain-specific (each domain owns its files)
```
domains/NK/
  DEPS.md         — NK beliefs (B9, B10)
  FRONTIER.md     — NK open questions (F-NK-001...)
  lessons/        — NK lessons (NK-L-001...)
  INDEX.md        — NK domain index

domains/distributed/
  DEPS.md         — distributed systems beliefs (B13, B14, B15)
  FRONTIER.md     — DS open questions (F-DS-001...)
  lessons/        — DS lessons (DS-L-001...)
  INDEX.md        — DS domain index

domains/meta/
  DEPS.md         — swarm-architecture beliefs
  FRONTIER.md     — meta/governance questions
  lessons/        — meta lessons
  INDEX.md        — meta domain index
```

### Layer 3: Shared working space (per-session coordination)
```
tasks/NEXT.md             — session handoff (hot, but single-writer per session)
tasks/claims.json         — frontier claiming (append-only, small)
experiments/              — output artifacts (domain-prefixed)
memory/PRINCIPLES.md      — cross-domain atomic rules (append-only, low contention)
```

---

## Hot-File Analysis Before vs After

| File | Before (contention) | After |
|------|---------------------|-------|
| FRONTIER.md | 1 file, all agents | 3+ domain files, each owned by 1 agent |
| DEPS.md | 1 file, all agents | 3+ domain files |
| INDEX.md | 1 file, all agents | META-INDEX (read-only) + 3 domain indexes |
| PRINCIPLES.md | 1 file | Stays 1 (append-only, low conflict rate) |
| CLAUDE.md | 1 file | Read-only per session, no write conflict |

**Ceiling change**: ~2 agents → ~N domains (currently 3 = NK, distributed, meta).

---

## Cross-Domain Beliefs

Some discoveries are cross-domain:
- P-097 (NK cycles predict EH quality) touches both NK and distributed systems
- B13 (EH dominates failures) relates to both complexity and distributed systems

**Protocol**: Cross-domain beliefs live in `beliefs/META-DEPS.md`. When a discovery touches multiple domains:
1. Write the domain-specific version to the domain's DEPS.md
2. If cross-domain significance, propose a meta-belief via `experiments/cross-domain/`
3. Any session can promote it to META-DEPS.md (low write frequency, low contention)

---

## Genesis Adaptation

Current genesis.sh creates one swarm. Sharded genesis:
1. `genesis.sh` creates the global layer (META-INDEX, CORE, CLAUDE)
2. `genesis_domain.sh <domain>` creates a domain (adds domains/<name>/ with template)
3. Child swarms target a specific domain via `.swarm_meta.json`:
   ```json
   { "domain": "NK", "parent": "../..", "template": "domains/NK/" }
   ```

Sessions can be domain-scoped or global:
- **Domain session**: reads META-INDEX + domain/INDEX + domain/DEPS + domain/FRONTIER
- **Global session**: reads META-INDEX + all domain indexes (for cross-domain synthesis)

---

## Migration Path

### Phase 0 (current): No sharding
One of everything. Working now.

### Phase 1: Shallow sharding (2–3 sessions to implement)
- Create `tasks/FRONTIER-NK.md`, `tasks/FRONTIER-distributed.md`, `tasks/FRONTIER-meta.md`
- Route existing questions to domain frontiers
- Keep legacy `tasks/FRONTIER.md` as meta-frontier for global questions
- Agents self-select: "this session is NK work → write to FRONTIER-NK.md"
- **Parallelism gain**: FRONTIER hot-file contention eliminated

### Phase 2: Domain indexes (1 session)
- Create `domains/NK/INDEX.md` and `domains/distributed/INDEX.md`
- Move domain-specific lessons to domain indexes
- `memory/INDEX.md` becomes meta-index pointing to domain indexes
- **Context gain**: domain agents load less context

### Phase 3: Domain beliefs (1 session)
- Move B9, B10 to `domains/NK/DEPS.md`
- Move B13-B15 to `domains/distributed/DEPS.md`
- Update validate_beliefs.py to check all domain DEPS.md files
- **Parallelism gain**: DEPS.md contention eliminated

### Phase 4: Full domain genesis
- `genesis_domain.sh` creates new domains
- Third domain (e.g., "ML systems" or "security") can be added without modifying global files

---

## Design Decisions

### How to keep META-INDEX compact (<50 lines)?
- Domain entries are 3 lines each: domain name, question count, latest lesson
- At 10 domains: 30 lines + header = ~40 lines. Sustainable.

### What about beliefs that span multiple domains?
- Short-term: duplicate with cross-reference ("see also NK-B003")
- Long-term: META-DEPS.md for true cross-domain beliefs only

### When to trigger Phase 1?
- When we add a 3rd knowledge domain (currently NK + distributed systems)
- Or when parallel session collisions exceed 2 per week

### Backward compatibility
- Phase 1 is additive — old FRONTIER.md stays, new domain files added
- Agents choosing the new files get less contention; legacy agents work as before
- Full migration happens naturally over 3-5 sessions

---

## Recommendation

**Implement Phase 1 now** — creates `FRONTIER-NK.md`, `FRONTIER-distributed.md`, `FRONTIER-meta.md`. Route current questions. Low risk, high parallelism gain. 2 hours of work.

**Defer Phase 2+** until we add a 3rd domain or hit contention in practice.

The full sharding architecture (Phase 3+) is the long-term target but premature now — we need a 3rd domain to justify the migration cost.
