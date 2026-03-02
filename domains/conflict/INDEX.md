# Conflict Domain Index
Domain: conflict | Created: S189 | 2026-02-28
Agent: conflict-expert

## What's here
Conflict detection, resolution, and prevention at the inter-swarm layer.
Canonical taxonomy: `domains/conflict/DOMAIN.md` (10-case, 3-tier from F110).
Canonical meta-source: `experiments/architecture/f110-meta-coordination.md`

## Active frontiers: 0 (all resolved)

## Resolved frontiers
- **F-CON1** RESOLVED S348: merge-on-close eliminated bloat 3.72x→1.00x. C1=0%, C3=0.
- **F-CON2** RESOLVED S363: claim.py 82% C-EDIT reduction (37.5%→6.7%). CE-4 prevented. L-656/L-657.
- **F-CON3** RESOLVED S349: constitution monitor FP 0%, TP 100% (n=6). Production-ready.

## Experiments
- `experiments/conflict/f-con1-*` — bloat/merge measurements
- `experiments/conflict/f-con2-*` — concurrent edit prevention
- `experiments/conflict/f-con3-*` — constitution monitor

## Lessons sourced
- L-093: first lane collision (lesson numbering CRDT conflict)
- L-234: WSL mass-deletion (git add -A catastrophic staged delete)
- L-237: anti-repeat protocol (duplicate work detection)
- L-265: concurrent convergence as validation signal
- L-283: anti-repeat — every S187 priority already done

## Cross-domain links
- domains/game-theory/ — Nash equilibrium contracts (F-CON2)
- domains/distributed-systems/ — CRDT patterns (A3)
- domains/protocol-engineering/ — mediator protocol (F-CON1)
- experiments/architecture/f110-meta-coordination.md — canonical taxonomy
