# Swarm Structure and File-Type Policy

This file is the canonical layout contract for swarm folders that hold reusable references and run recordings.

## Intent
- Keep durable source references separate from run artifacts.
- Keep recordings reproducible without storing heavy raw media in git.
- Make file-type expectations explicit so maintenance can validate them.

## Folder Roles
- `references/`: curated external-source notes, citations, and structured reference metadata.
- `recordings/`: session/run transcripts, observation logs, and pointer metadata for non-text captures.
- `experiments/`: executable experiment outputs and result artifacts.

## Allowed File Types
- `references/`: `.md`, `.json`, `.txt`, `.csv`, `.tsv`, `.bib`, `.yml`, `.yaml`
- `recordings/`: `.md`, `.json`, `.txt`, `.csv`, `.tsv`, `.log`, `.yml`, `.yaml`
- Shared exceptions: `README.md`, `.gitkeep`

Any other extension in these folders should be treated as out-of-policy and flagged by maintenance.

## Naming Guidance
- Use stable, searchable names: `<topic>-s<session>.<ext>` when tied to a swarm session.
- Use date-prefixed names for chronological recordings: `<yyyy-mm-dd>-<topic>-s<session>.<ext>`.
- Keep topic slugs lowercase with hyphens.

## Raw Media Handling
- Do not commit large raw audio/video captures into `recordings/`.
- Store raw media outside the repo and commit a small pointer record (`.md` or `.json`) with:
  - capture date/time
  - source location (path/URL)
  - checksum if available
  - short interpretation notes
