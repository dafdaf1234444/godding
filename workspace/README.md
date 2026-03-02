# Workspace

Code, tools, and experiments produced by the swarm.

## CLI

```bash
./workspace/swarm.sh status   # current state
./workspace/swarm.sh next     # what to work on
./workspace/swarm.sh health   # system health check
./workspace/swarm.sh wiki swarm --depth 1 --fanout 5   # wikipedia topic swarm report
```

## Bootstrap a new swarm

```bash
./workspace/genesis.sh ~/my-new-swarm "project-name"
cd ~/my-new-swarm
git init && git add CLAUDE.md beliefs memory tasks tools modes workspace experiments .gitignore && git commit -m "[S] init: genesis"
```

## NK analysis

```bash
# Python
python3 tools/nk_analyze.py <package-name>

# Go
python3 tools/nk_analyze_go.py <go-project-path>

# Installable package
pip install -e workspace/nk-analyze/
nk-analyze <package-name>
```

## Tools

All tools are in `tools/`. They are fully independent — zero imports between them, coordination via filesystem only. Run any tool with `python3 tools/<name>.py --help` for usage.
