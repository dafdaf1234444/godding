# Session Tracker Agent History Enhancement

## Current State (Tool-Grade)
session_tracker.py collects per-session metrics: commits, files touched, structural changes, lessons/principles count, frontier state, entropy items. Includes Langton's lambda and predictive entropy analysis.

## Enhancement Design (Swarm-Grade)

### 1. Persistent Session Outcome Tracking
Add `workspace/session-outcomes.json` to track session efficiency patterns:
- Session productivity metrics (lessons/principles per hour)
- Knowledge density (proxy-K produced per commit)
- Frontier advancement rate (resolved/opened ratio)
- Cross-session efficiency trends

### 2. Session Pattern Recognition
Classify sessions into behavioral types:
- **EXPLORATION**: High frontier opening, low resolution
- **EXPLOITATION**: High frontier resolution, low opening
- **MAINTENANCE**: High file churn, low knowledge production
- **BREAKTHROUGH**: High lessons/principles, structural changes
- **CONSOLIDATION**: High principles, low lessons (compaction)

### 3. Behavioral Learning System
After 5+ sessions, identify patterns:
- **PRODUCTIVE** sessions (top 25% efficiency)
- **INEFFICIENT** sessions (bottom 25% efficiency)
- **BALANCED** sessions (knowledge + frontier progress)
- **STALLED** sessions (low output across metrics)

### 4. Predictive Early Warning
Mid-session checks for historical risk patterns:
- Low commit rate + high file churn = possible thrashing
- High frontier opening + low resolution = exploration overload
- Structural changes without knowledge = possible regression

### 5. Integration Points
- `orient.py` displays session efficiency trends
- `dispatch_optimizer.py` uses session patterns for domain routing
- `compact.py` triggers based on efficiency degradation patterns

## Implementation Pattern
Follow maintenance.py model:
- Add `--learn` flag for pattern analysis
- Add `--track` flag for mid-session monitoring
- Preserve existing metrics collection
- Add outcome persistence layer