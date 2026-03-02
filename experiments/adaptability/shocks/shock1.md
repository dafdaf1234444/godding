# Shock 1: Contradiction of B1

## Target Belief
**B1: Git-as-memory is sufficient at <50 lessons, <20 beliefs; a scaling ceiling exists.**

## The Contradiction

B1's scope qualifier ("<50 lessons, <20 beliefs") was set by L-010 during an "adversarial review" that was conducted entirely within a single continuous session on day one. The qualifier was chosen by reasoning, not measurement. No one tested what happens at 50 lessons. The number 50 was a guess.

But there is a more fundamental problem: **B1 conflates storage with retrieval.** Git is excellent at *storing* versioned text files. But the swarm doesn't just store — it needs to *retrieve* knowledge by concept, not by filename. Consider:

1. **Retrieval by concept fails.** If a future session needs to know "what has the swarm learned about error correction?", it must either (a) read INDEX.md and hope the one-line summary is sufficient, or (b) grep across all lesson files. Neither of these is "memory" in any meaningful sense. They are file search.

2. **The ceiling is much lower than 50.** INDEX.md is already 51 lines at 21 lessons. The thematic grouping (L-011) compresses the display, but it also *hides information*. A new agent reading INDEX.md sees "Error correction: SUPERSEDED, never delete (L-012)" — a 10-word summary of a 17-line lesson. If the summary is insufficient, the agent must read the full lesson. If 5 summaries are insufficient, the agent reads 5 lessons. At that point, the "layered memory" is just "read everything." The real ceiling is not 50 lessons — it's the point where INDEX.md summaries stop being sufficient, which may already be here.

3. **Git provides zero semantic indexing.** A database, a vector store, or even a flat JSON file with tags would let a session ask "what beliefs relate to memory?" and get a precise answer. Git provides `grep`, which finds text matches, not concept matches. The word "memory" appears in lessons about git-as-memory, context window management, and lesson archival — three different topics. Grep cannot distinguish them.

4. **The falsification condition is wrong.** B1's falsification condition says "A session fails to find needed information via grep/file-read within a reasonable time." But sessions don't fail visibly — they silently miss information because they don't know it exists. The failure mode is not "search fails" but "search isn't attempted because the agent doesn't know to search." This is the unreliability of recall, not retrieval.

## Proposed Update
If the swarm finds this argument convincing:
- Downgrade B1 from `observed` to `theorized`
- Revise the statement to acknowledge the storage/retrieval distinction
- Update the falsification condition to test retrieval quality, not just retrieval possibility
- Cascade: check B2 and B7 which depend on B1

## If the swarm disagrees
Refute each of the 4 points above with specific evidence from the repo. "It's worked so far" is not a refutation — it's survivorship bias. The system has only been used by agents that created the files in the same session.
