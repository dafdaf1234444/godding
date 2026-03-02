# Recordings

`recordings/` stores reproducible run/session recording artifacts as text or structured metadata.

## What belongs here
- Session transcripts and summaries (`.md`, `.txt`)
- Structured capture metadata (`.json`, `.yml`, `.yaml`)
- Lightweight logs/tables (`.log`, `.csv`, `.tsv`)

## File-type policy
- Allowed: `.md`, `.json`, `.txt`, `.csv`, `.tsv`, `.log`, `.yml`, `.yaml`
- Exceptions: `README.md`, `.gitkeep`

## Raw media policy
- Do not commit raw audio/video binaries here.
- Keep raw files outside git and commit a pointer file with capture time, storage location, checksum, and notes.

## Suggested layout
- `recordings/<source>/...`
- `recordings/<source>/<yyyy-mm-dd>-<topic>-s<session>.md`
