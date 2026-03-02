# Multi-Tool Agentic Capability Research (March 2026)

Research date: 2026-03-01 | Target: Windsurf + GitHub Copilot Coding Agent capabilities for autonomous swarm workflows

---

## 1. WINDSURF (Codeium) — Current Capabilities

### 1.1 Instruction File Auto-Loading (.windsurfrules)

**Status: PARTIAL/CONDITIONAL**

- `.windsurfrules` at repo root is **recognized but not automatically loaded by default**
- Two ways to activate:
  1. **Explicit loading**: Must be loaded within the chat or workflow explicitly
  2. **Cascade Memories**: Can be saved via "Cascade generated Memories" feature
- Alternative legacy format: `.windsurf/rules/` directory structure (markdown files)
- **Limitation**: No true auto-load without explicit activation or memory persistence

**Implication for swarm**: Cannot rely on `.windsurfrules` being transparent/automatic. Rules require explicit session initialization or persistent memory setup.

---

### 1.2 Terminal & Shell Access

**Status: FULL SUPPORT with safety layers**

**Capabilities:**
- Cascade can execute terminal commands autonomously via **Turbo Mode**
- Four safety levels for auto-execution:
  - **Disabled**: All commands require manual approval
  - **Allowlist Only**: Pre-approved commands auto-execute
  - **Auto**: Premium models judge safety; risky commands still need approval
  - **Turbo**: All commands auto-execute except those on deny list
- Users can select terminal output and send to Cascade via `Cmd/Ctrl+L`
- Respects system `$SHELL` environment variable
- Turbo mode is user-configurable in settings

**Git integration**: Git is listed as allowlist example (`git add -A` supported), but comprehensive git workflow automation is not explicitly documented.

**Implication for swarm**: Terminal access is robust. Suitable for autonomous execution of scripts, package management, and potentially git commands if allowlisted.

---

### 1.3 Parallel Sub-Agent Spawning & Cascade Flows

**Status: FULL SUPPORT (Wave 13 release, Jan 2026)**

**Capabilities:**
- **Git Worktree Support**: Spawn multiple Cascade sessions in the same repo using isolated worktrees
  - Worktrees check out different branches into separate directories
  - Share same git history, no conflicts
- **Multi-pane Layout**: Side-by-side Cascade panes enable parallel workflows
- **Fast Context (Subagent)**: Powered by SWE-grep, finds relevant code context 20x faster (~2,800 tokens/sec throughput)
- **Dedicated Terminal Profile**: For more reliable agent execution

**Parallel Execution Model:**
- Multiple Cascade instances can run concurrently on separate branches/worktrees
- No documented true "sub-agent spawning" (like task-based delegation), but worktree isolation provides practical parallel execution

**Implication for swarm**: Windsurf's parallel model is worktree-based, not sub-agent delegation. Suitable for multi-branch exploratory work but not nested sub-task distribution.

---

### 1.4 Git Commits & Autonomous Workflows

**Status: SUPPORTED via terminal commands**

**Capabilities:**
- Can generate git commands and commit messages autonomously
- Supports predefined commit formats and standardized messages
- Can create pull requests with CLI commands
- Workflow automation includes:
  - Dependency installation
  - Code formatters and linters
  - Test running and fixing
  - Committing with formatted messages
- **Recent (Jan 2026)**: Agent Skills feature allows custom commands at key workflow points

**Limitations:**
- No explicit documentation of fully autonomous branch creation or PR submission
- Commits are executed via terminal commands (not API), relying on Turbo Mode safety levels

**Implication for swarm**: Can autonomously commit if Turbo Mode or allowlist is configured. Not ideal for high-volume autonomous commits without safety overhead.

---

### 1.5 Instruction File Conventions

**Supported Formats:**
- `.windsurfrules` (legacy, root-level markdown)
- `.windsurf/rules/*.md` (modern directory-based approach)
- Custom Agent Skills (as of Jan 2026)
- Integration with MDM policies (enterprise)

**Configuration Options:**
- Memories: Persistent context across sessions
- Workflows: Automation templates for repetitive tasks
- Rules: Project-specific customization
- MCP Servers: Extended tool integration

---

### 1.6 Known Limitations for Autonomous Workflows

1. **No transparent auto-load**: `.windsurfrules` requires explicit initialization
2. **Worktree-based parallelism**: Not task-delegation but branch isolation
3. **Safety-first terminal**: Auto-execution requires configuration; high-risk commands always need approval
4. **Single agent per session**: One Cascade instance per pane, not spawn-and-forget sub-agents
5. **Documentation gaps**: Git commit workflows not fully specified in public docs
6. **Enterprise-only features**: Some advanced automation (MDM rules, Skills) are enterprise features

---

## 2. GITHUB COPILOT CODING AGENT — Current Capabilities

### 2.1 Instruction File Auto-Loading (.github/copilot-instructions.md)

**Status: FULL AUTO-LOAD SUPPORT**

- `.github/copilot-instructions.md` at repo root is **automatically detected and loaded**
- Instructions apply to all chat requests within workspace immediately upon save
- Alternative supported formats:
  - `AGENTS.md` (swarm-compatible)
  - `.github/instructions/**.instructions.md` (pattern-based loading)
  - `CLAUDE.md` (Claude Code specific)
  - `GEMINI.md` (Gemini specific)
- **Verification**: Custom instructions listed in "References" section of responses; if file was used, it appears in References

**Implication for swarm**: True auto-load. Can serve as primary instruction mechanism across multiple tools/bridge entry points. Instructions are transparent to user, automatically applied.

---

### 2.2 Terminal & Shell Access

**Status: FULL SUPPORT via Copilot CLI (GA as of Feb 2026)**

**Capabilities:**
- **GitHub Copilot CLI**: Generally available terminal-native coding agent
- Respects `$SHELL` environment variable
- Supports `!` prefix for direct shell execution
- Can suggest terminal commands
- Analyzes staged/unstaged git changes before commit

**Autonomous Execution:**
- Agent mode: Iterates on its own output, runs code, checks results, fixes errors autonomously
- Self-healing: Can recognize and fix errors, lint failures, and test failures within single request
- Parallel research subagents: As of Jan 2026, all three research subagents run concurrently

**Git Integration:**
- Can find commits: `"find all commits by 'Name' in the last month with message 'refactor'"`
- Analyzes code changes before committing
- **Critical Limitation**: Can only push to branches beginning with `copilot/`; CANNOT push to main/master

**Implication for swarm**: Excellent terminal access, but git push restrictions limit autonomous PR merging. Suitable for draft PRs, feature branches, and analytical workflows.

---

### 2.3 Parallel Work & Sub-Agent Spawning

**Status: FULL SUPPORT (Sept 2025 GA, Jan 2026 enhancements)**

**Parallel Architecture:**
- **Mission Control**: Orchestrate multiple agent tasks running in parallel
  - See which tasks are running
  - Review progress in real-time
  - Intervene if agents stall
  - Approve resulting PRs from dashboard
- **Sub-agents Architecture**: Main agent delegates subtasks to sub-agents, each in own context window
  - Each sub-agent runs independently
  - Results combined by main agent
- **Concurrent Research Subagents (Jan 2026)**: All three research subagents run concurrently instead of sequentially

**Execution Model:**
- Asynchronous execution: Can assign a GitHub issue to Copilot; agent works independently
- Works across multiple files as coherent unit
- Can iterate on output without user intervention

**Limitations:**
- Sub-agents only during explicit task assignment, not developer-initiated spawning
- Delegation is internal to agent architecture, not user-controlled spawning

**Implication for swarm**: Strong parallel work capability through Mission Control. Not true spawn-and-forget, but orchestrated multi-task execution.

---

### 2.4 Git Commits & Autonomous Workflows

**Status: PARTIALLY SUPPORTED (commits possible, merge restrictions)**

**Autonomous Capabilities:**
- Can make code changes across files as coherent unit
- Creates PRs with self-generated titles and descriptions
- Can commit staged changes with natural language commit messages
- Analyzes git changes and suggests commit messages

**Restrictions:**
- Push restricted to `copilot/*` branches ONLY
- Cannot push to `main` or `master` branches
- Cannot perform merge operations
- Works within GitHub Actions sandbox environment

**Workflow Support:**
- Can install packages, run tests, fix failures
- Migrate code across multiple files in single operation
- Iterate until task completion

**Implication for swarm**: Can autonomously commit and create PRs, but merge restrictions prevent fully unattended deployment. Suitable for CI/CD integration where humans review PRs.

---

### 2.5 Instruction File Conventions

**Supported Formats (Priority Order):**
1. `.github/copilot-instructions.md` (auto-loaded, primary)
2. `AGENTS.md` (swarm-compatible, auto-loaded)
3. `.github/instructions/**.instructions.md` (pattern-based)
4. `CLAUDE.md` (Claude Code bridge)
5. `GEMINI.md` (Gemini bridge)

**Auto-Loading Behavior:**
- All formats auto-load without explicit activation
- Workspace-wide scope: instructions apply to all Copilot interactions
- Real-time: Changes take effect immediately upon save
- No session restart required

---

### 2.6 Known Limitations for Autonomous Workflows

1. **Git push restrictions**: Cannot push to main/master; limited to copilot/* branches
2. **Sandbox environment**: Operates within GitHub Actions sandbox, not full system shell
3. **Merge not supported**: Can create PRs but cannot merge them
4. **Sub-agent visibility**: Limited user control over sub-agent spawning; delegated internally
5. **Single source context window**: Each sub-agent has own context; may miss cross-cutting concerns
6. **Asynchronous lag**: Task assignment doesn't guarantee immediate execution; queued for availability

---

## 3. COMPARATIVE ANALYSIS

### 3.1 Instruction File Auto-Loading

| Aspect | Windsurf | Copilot |
|--------|----------|--------|
| Auto-load | Conditional (explicit/memory) | Full (immediate) |
| Formats supported | .windsurfrules, .windsurf/rules/ | .github/copilot-instructions.md, AGENTS.md, CLAUDE.md, GEMINI.md |
| Transparency | Requires verification | Listed in References |
| Reload | Explicit restart | Real-time on save |
| **Swarm fit** | **Requires explicit setup per session** | **Transparent across sessions** |

### 3.2 Terminal & Shell Access

| Aspect | Windsurf | Copilot |
|--------|----------|--------|
| Terminal access | Yes (Turbo Mode) | Yes (Copilot CLI) |
| Auto-execution | Configurable (4 levels) | Full (agent mode) |
| Safety model | Allowlist/Deny explicit | Sandbox isolation |
| $SHELL support | Yes | Yes |
| Git operations | Via terminal, not documented | Limited to copilot/* branches |
| **Swarm fit** | **Flexible but config-heavy** | **Simpler but restrictive** |

### 3.3 Parallel Execution

| Aspect | Windsurf | Copilot |
|--------|----------|--------|
| Parallelism | Worktree-based (branch isolation) | Sub-agent delegation (Mission Control) |
| User control | High (explicit worktree creation) | Low (internal orchestration) |
| Visibility | Side-by-side panes | Mission Control dashboard |
| Concurrency model | Multi-session same repo | Multi-task single repo |
| **Swarm fit** | **Branch-parallel, not task-parallel** | **Task-parallel with orchestration** |

### 3.4 Git Workflows & Commits

| Aspect | Windsurf | Copilot |
|--------|----------|--------|
| Autonomous commits | Yes (via terminal) | Yes (API-based) |
| Commit message format | Custom via terminal | Natural language |
| PR creation | Via terminal (gh cli) | API (auto-generated) |
| Merge capability | Yes (terminal) | No (copilot/* only) |
| Push restrictions | None (terminal-based) | copilot/* branches only |
| **Swarm fit** | **Full control, high overhead** | **Limited scope, less friction** |

---

## 4. SWARM INTEGRATION IMPLICATIONS

### 4.1 For Windsurf Bridge File (.windsurfrules)

**Recommendation: DO NOT use as primary instruction mechanism**

- Requires explicit session setup (not transparent)
- Memory persistence needed for cross-session consistency
- Alternative: Use `.github/copilot-instructions.md` (Copilot-compatible) + Document Windsurf-specific overrides in `.windsurf/rules/` directory
- Action: Consider deprecating legacy `.windsurfrules` approach; standardize on Copilot's format

### 4.2 For Copilot Bridge File (.github/copilot-instructions.md)

**Recommendation: EXPAND as primary swarm instruction mechanism**

- Auto-loads transparently (no setup friction)
- Recognized by Copilot agent + referenced in responses
- Also loaded by newer Windsurf versions (if using AGENTS.md or similar)
- Action: This file becomes the canonical swarm instruction source; other bridge files reference it

### 4.3 For Autonomous Multi-Agent Workflows

**Windsurf Model:**
- Branch-based parallelism (good for feature branches)
- Suitable for exploratory work across multiple versions
- High terminal control, high configuration overhead
- Not ideal for task-delegation swarms

**Copilot Model:**
- Task-delegation (good for divide-and-conquer)
- Mission Control for orchestration
- PR/branch restrictions (requires human merge gate)
- Better for multi-issue backlog clearance

**Implication**: Different parallelism models. Windsurf = exploratory parallel; Copilot = task-parallel. Use each for strengths.

### 4.4 For Git Safety & Autonomous Commits

**Windsurf:**
- Full autonomy possible but requires Turbo Mode configuration
- Safety = developer responsibility (allowlist/deny lists)
- Terminal-based (slower, higher-friction)

**Copilot:**
- Restricted by design (copilot/* branches only)
- Safety = platform enforcement
- API-based (faster, lower-friction for draft PRs)

**Implication**: Copilot better for autonomous draft PRs (safer); Windsurf better for full control if configured.

---

## 5. MEASUREMENT GAPS & BRIDGE FILE AUDIT FINDINGS

### 5.1 Recurring Measurement Issue (L-556, L-572, L-574, L-578 pattern)

**Finding**: "Mechanism wired correctly, measurement channel broken"

In this case:
- **Windsurf**: Documentation claims `.windsurfrules` auto-load, but actual behavior is conditional. Bridge files assume transparent auto-load.
- **Copilot**: Documentation clearly states auto-load; actual behavior matches docs (verified via References).

**Action Required**: Audit `/mnt/c/Users/canac/REPOSITORIES/swarm/.windsurfrules` and bridge files. If they assume transparent auto-load, update documentation or adjust setup.

### 5.2 Multi-Tool Instruction Consistency Issue

**Current State**:
- `CLAUDE.md` (Claude Code) — loads SWARM.md
- `.cursorrules` (Cursor) — unknown
- `AGENTS.md` (Codex/Copilot) — format exists but unknown if auto-loads
- `.github/copilot-instructions.md` (Copilot) — auto-loads, but may conflict with AGENTS.md
- `.windsurfrules` (Windsurf) — requires explicit activation
- `GEMINI.md` (Gemini) — format exists but unknown

**Risk**: Swarm instructions may not be transparent across all tools. Some tools may have stale/inconsistent instructions.

**Recommended Fix**:
1. Verify which bridge files auto-load (done for Copilot ✓, Windsurf ✗)
2. Test with actual tool invocations (not just docs)
3. Consolidate instruction source (`.github/copilot-instructions.md` as canonical?)
4. Document actual auto-load behavior vs. assumed

---

## 6. SOURCES

### Windsurf Documentation & Research
- [Windsurf Official](https://windsurf.com/)
- [Windsurf Docs](https://docs.windsurf.com/)
- [Windsurf Terminal Docs](https://docs.windsurf.com/windsurf/terminal)
- [Windsurf Cascade Docs](https://docs.windsurf.com/windsurf/cascade/cascade)
- [Windsurf Wave 13 Release (Jan 2026)](https://www.testingcatalog.com/windsurf-wave-13-brings-free-swe-1-5-and-new-upgrades/)
- [Codeium .windsurfrules Issues #157](https://github.com/Exafunction/codeium/issues/157)
- [Windsurf Review 2026 - Second Talent](https://www.secondtalent.com/resources/windsurf-review/)
- [Windsurf vs Cursor vs Antigravity - Codecademy](https://www.codecademy.com/article/agentic-ide-comparison-cursor-vs-windsurf-vs-antigravity)

### GitHub Copilot Documentation & Research
- [GitHub Copilot Coding Agent - Official Docs](https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-coding-agent)
- [GitHub Copilot CLI GA (Feb 2026)](https://github.blog/changelog/2026-02-25-github-copilot-cli-is-now-generally-available/)
- [Copilot Custom Instructions - GitHub Docs](https://docs.github.com/copilot/customizing-copilot/adding-custom-instructions-for-github-copilot)
- [GitHub Copilot Agent Mode & Multi-Model Support (2025)](https://devops.com/github-copilot-evolves-agent-mode-and-multi-model-support-transform-devops-workflows-2/)
- [Copilot Workspace Sunset & Coding Agent Rebirth](https://github.com/newsroom/press-releases/coding-agent-for-github-copilot)
- [Copilot Coding Agent Changelog (Aug 2025)](https://github.blog/changelog/2025-08-28-copilot-coding-agent-now-supports-agents-md-custom-instructions/)
- [Mission Control for Parallel Agents](https://smartscope.blog/en/generative-ai/github-copilot/github-copilot-claude-code-multi-agent-2025/)

---

## 7. RECOMMENDATIONS FOR SWARM

### Short Term (This Session)
1. Verify actual auto-load behavior of `.windsurfrules` via test (do not rely on docs)
2. Standardize on `.github/copilot-instructions.md` as canonical source for swarm instructions
3. Document actual (not assumed) auto-load behavior for each bridge file

### Medium Term (Next 1-2 Sessions)
1. Audit all bridge files (CLAUDE.md, .cursorrules, AGENTS.md, .windsurfrules, GEMINI.md) for consistency
2. Test multi-tool instruction propagation with actual tool invocations
3. Update SWARM.md with tool-specific instruction mechanics (not assumptions)

### Long Term (Strategic)
1. Consider consolidating instruction sources (too many files = maintenance burden)
2. Explore Copilot's superior auto-load mechanics as model for other tools
3. Design swarm-wide instruction versioning (bridge files as immutable snapshots?)
4. Consider Windsurf's worktree model for branch-parallel exploration workflows
5. Consider Copilot's Mission Control model for task-parallel backlog clearing

