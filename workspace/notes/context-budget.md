# Context Budget Validation

Generated: 2026-02-25 | Sub-agent analysis for TASK-009

## CONTEXT.md Claims vs Actual

| File         | Claimed lines | Actual lines | Claimed chars (est) | Actual chars | Delta     |
|--------------|---------------|--------------|---------------------|--------------|-----------|
| CLAUDE.md    | ~50           | 92           | —                   | 5,434        | +84% lines |
| CORE.md      | ~32           | 33           | —                   | 2,964        | ~accurate  |
| INDEX.md     | ~55           | 60           | —                   | 3,739        | +9% lines  |
| Task file    | ~20           | 10–23        | —                   | varies       | ~accurate  |
| Protocol overhead | ~20      | unclear      | —                   | —            | unclear    |
| **Total**    | **~180 lines**| **~205 lines** (using avg task=18) | **~700 tokens** | **~3,400 tokens** | **+14% lines, ~+386% tokens** |

## Token Estimation

A common heuristic for English text with markdown is ~4 characters per token, or roughly 0.75 tokens per word. Using the character counts:

| File       | Chars  | Est. tokens (chars/4) | Est. tokens (word-based) |
|------------|--------|----------------------|-------------------------|
| CLAUDE.md  | 5,434  | ~1,360               | ~1,100                  |
| CORE.md    | 2,964  | ~740                 | ~600                    |
| INDEX.md   | 3,739  | ~935                 | ~750                    |
| Task file  | ~800   | ~200                 | ~160                    |
| **Total**  | **~12,937** | **~3,235**      | **~2,610**              |

Conservative estimate: **~2,600–3,400 tokens** of mandatory session-start load.

## Analysis

### Line count errors
- **CLAUDE.md is the biggest miss.** The estimate says ~50 lines, but the actual file is 92 lines. This is because CLAUDE.md has grown significantly since v0.1 — Rule 8, parallel agent guidance, NEXT.md references, and protocol list expansions were all added. The estimate was never updated.
- **CORE.md and INDEX.md** are reasonably close to their estimates. INDEX.md grew from ~55 to 60 lines, which is within noise.
- **Task files** vary (10–23 lines observed), so ~20 is a fair average.

### Token count error (the major issue)
- CONTEXT.md claims "~700 tokens" for the mandatory load. The actual figure is approximately **2,600–3,400 tokens** depending on the tokenizer.
- The 700-token claim is off by **3.7–4.9x**. This is a significant underestimate.
- Likely cause: the original author may have estimated tokens as roughly lines * 4 (assuming ~4 tokens/line). But the actual files have dense prose lines averaging ~50–60 characters each, which yields ~12–15 tokens per line, not 4.

### "Protocol overhead" line item
- The ~20 lines / implied tokens for "protocol overhead" is vague and unverifiable. It presumably covers the system-reminder injection of CLAUDE.md content, but that is already counted in the CLAUDE.md line count. If it means something else (tool preambles, conversation framing), it is likely a larger number than 20 lines.

## Headroom Assessment

### What is the effective context?
Claude Code (Opus 4) has a 200K-token context window. However, effective usable context is smaller due to:
- System prompt overhead (tool definitions, instructions) — estimated ~2,000–5,000 tokens
- Conversation history accumulation (each tool call + response: ~200–2,000 tokens)
- Response generation reserve — model needs space to generate output

Practical working context for a session with heavy tool use: **~150,000–180,000 tokens**.

### Mandatory load impact
- Mandatory session-start read: ~3,000 tokens (0.015–0.020 of working context)
- This is **negligible**. Even at 5x the estimate, 3,000 tokens out of 150,000+ is under 2%.

### When does it become a problem?
The mandatory load is NOT the bottleneck. The real context consumers are:
1. **Conversation history** — a session with 50 tool calls averaging 500 tokens each = 25,000 tokens just in tool responses
2. **File reads during work** — reading 10 lesson files (~200 lines each) = ~5,000 tokens
3. **Accumulated thinking** — model's own outputs in the conversation

The mandatory load becomes problematic only if it grows to ~10,000+ tokens (would require CLAUDE.md growing to ~300+ lines, INDEX.md to ~200+ lines, etc.). At current growth rates this is far away.

### Real risks
1. **INDEX.md growth** — currently 60 lines with 22 lessons. At 50+ lessons, INDEX.md could double. Still manageable.
2. **CLAUDE.md growth** — already 92 lines and the most bloated file. Each new protocol, rule, or guidance section adds lines. This is the file most likely to cause issues at maturity.
3. **NEXT.md + task file** — these reset each session so they are bounded.

## Recommendations

1. **Fix the token estimate in CONTEXT.md**: Change "~700 tokens" to "~3,000 tokens". Still small, but accuracy matters for epistemic discipline.
2. **Fix the CLAUDE.md line estimate**: Change "~50 lines" to "~92 lines" (or "~90 lines").
3. **Add a growth warning**: Note that CLAUDE.md is the fastest-growing mandatory file and should be monitored. Consider splitting guidance into a separate file that is only loaded on-demand.
4. **Clarify "protocol overhead"**: Either remove this line item or define exactly what it covers.
5. **Reframe the concern**: The real context risk is conversation-history accumulation, not mandatory load. CONTEXT.md already hints at this but could be more explicit.

## Summary

The mandatory session-start context load is approximately **3,000 tokens** — about 4x larger than the claimed 700 tokens, but still only ~2% of the effective context window. There is substantial headroom. The CLAUDE.md line count is 84% larger than documented. The token estimate is the most dangerously wrong figure in CONTEXT.md because future sessions might rely on it for planning decisions. The fix is straightforward: update the numbers.
