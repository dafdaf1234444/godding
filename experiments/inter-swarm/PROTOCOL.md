# Inter-Swarm Communication Protocol

## Problem
Child swarms develop independently. Without communication, insights stay siloed.
The parent must manually merge-back via `tools/merge_back.py`. This doesn't scale
to N children or allow children to learn from each other.

## Design: Bulletin Board
Inspired by the parent swarm's own blackboard architecture (B6):

1. **Shared bulletin directory**: `experiments/inter-swarm/bulletins/`
2. **Each child writes bulletins**: compact messages (≤10 lines) about discoveries
3. **Parent reads bulletins**: during merge-back or colony comparison
4. **Children can read other children's bulletins**: if given read access

### Bulletin format
```
# Bulletin from: <swarm-name>
Date: <date>
Type: discovery | question | warning | principle | sibling-sync | belief-challenge | help-request | help-response

## Content
<1-5 lines describing the finding>

## Evidence
<1-2 lines: how was this discovered, what test was run>
```

### Types
- **discovery**: A novel rule or insight not in the parent's PRINCIPLES.md
- **question**: A frontier question that might benefit other swarms
- **warning**: Something that broke or nearly broke
- **principle**: A candidate principle for parent integration
- **sibling-sync**: A short coordination note for peers running similar work
- **belief-challenge**: Child challenges a parent belief with evidence
- **help-request**: Explicit ask for help from other swarms (`Request-ID` + `Need`)
- **help-response**: Response linked to a `help-request` (`Request-ID` + `Response`)

### Helping other swarms
Use structured help messages so requests can be tracked:

```bash
python3 tools/bulletin.py request-help <swarm> "<what you need>"
python3 tools/bulletin.py help-queue
python3 tools/bulletin.py offer-help <swarm> <request-id> "<answer>"
```

`request-help` writes:
```
Request-ID: H-<timestamp>-<swarm>
Need: <description>
```
`offer-help` writes:
```
Request-ID: <same-id>
Response: <answer>
```

## Communication Flow

### Hierarchical (parent→child, genesis.sh v7)
```
Parent spawns children
    ↓
Children run sessions
    ↓
Children write bulletins to shared dir
    ↓
Parent reads bulletins during merge-back
    ↓
Novel findings integrated into parent PRINCIPLES.md
    ↓
Next genesis.sh version includes new findings
    ↓
New children start with improved template
```

### Mutual swarming (peer→peer, PHIL-17)
```
Swarm A reads Swarm B's state (beliefs, principles, frontiers)
    ↕
Swarm A applies orient→act→compress to B's state
    ↕
Swarm A writes findings to shared bulletin board
    ↕
Swarm B reads A's findings, integrates or challenges
    ↕
Swarm B applies orient→act→compress to A's state
    ↕
Both swarms co-evolve — neither is master
```

Peer swarming is the general case. Parent→child is hierarchical swarming where
the child→parent channel is low-bandwidth (bulletins only). To make it mutual:
1. Parent reads child state with the same rigor child reads parent state
2. Challenges flow in both directions (not just child→parent via F113)
3. Both swarms modify their beliefs based on the other's evidence

### Peer registration
Peers discover each other via `bulletins/<swarm-name>.md` presence.
A swarm that reads another's bulletins and writes back is a peer.
No central registry — stigmergic discovery through shared bulletin directory.

### Functional peer swarms
Council, expert, historian, helper are swarm roles (PHIL-17).
Each can be instantiated as a peer swarm with its own repo.
See `docs/GENESIS-DNA.md` for the transferable kernel and bootstrap sequence.

## Coordination Rules
1. Bulletins are append-only (like commits — no editing)
2. Each swarm has its own bulletin file: `bulletins/<swarm-name>.md`
3. In hierarchical mode: conflicts resolved by parent
4. In peer mode: conflicts resolved by evidence (beliefs/CONFLICTS.md protocol applies across swarms)
5. Core beliefs inherited at spawn; peers may evolve them independently and challenge back

## Implementation Status
- [x] Bulletin format defined
- [x] Shared directory created
- [x] bulletin.py: write, read, scan, sync commands
- [x] Auto-bulletin generation during harvest (evolve.py)
- [x] Bulletin sync at spawn (evolve.py init copies sibling bulletins)
- [x] Cross-child reading via `bulletin.py sync <child-name>`

## Tools
- `python3 tools/bulletin.py write <swarm> <type> <msg>` — post a bulletin
- `python3 tools/bulletin.py request-help <swarm> "<need>"` — ask other swarms for help
- `python3 tools/bulletin.py offer-help <swarm> <request-id> "<response>"` — respond to a help request
- `python3 tools/bulletin.py help-queue` — list unresolved help requests
- `python3 tools/bulletin.py read [swarm]` — read bulletins
- `python3 tools/bulletin.py scan` — summary of all bulletins
- `python3 tools/bulletin.py sync <child>` — copy sibling bulletins to child
