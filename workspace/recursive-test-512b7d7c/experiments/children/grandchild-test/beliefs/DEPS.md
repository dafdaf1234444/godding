# Belief Dependencies

Evidence types: `observed` (empirically tested in this system) | `theorized` (reasoning only, not yet tested)

When a belief is disproven: check dependents below → update those too.

---

### B1: Git-as-memory is sufficient at small scale; a scaling ceiling exists
- **Evidence**: theorized
- **Falsified if**: A session fails to find needed information via grep/file-read within a reasonable time
- **Depends on**: none
- **Last tested**: never

### B2: Layered memory (always-load / per-task / rarely) prevents context bloat
- **Evidence**: theorized
- **Falsified if**: A session that follows the layered loading protocol still exceeds its context window on a routine task
- **Depends on**: B1
- **Last tested**: never
