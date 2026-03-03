"""Centralized lesson metadata parser (L-1035: parallel-parser antipattern fix).

Handles both plain format (Session: S441) and Markdown-bold format (**Session**: S441).
All tools that parse lesson metadata should import from here to avoid format-drift.

Usage:
    from lesson_meta import parse_meta
    meta = parse_meta(text)  # returns dict with session, domain, level, etc.
"""
import re


# Canonical pattern for any metadata field that may or may not be bolded
def _field(name: str) -> str:
    """Return regex pattern for metadata field (plain or **bold**)."""
    return rf"\*{{0,2}}{name}\*{{0,2}}:\s*"


# Pre-compiled patterns for common fields
_SESSION_PAT = re.compile(_field("Session") + r"S?(\d+)")
_DOMAIN_PAT = re.compile(_field("[Dd]omain") + r"([^\n|*]+)")
_LEVEL_PAT = re.compile(_field("[Ll]evel") + r"([^\n|*]+)")
# Cites: may appear standalone (^Cites: ...) or inline (| **Cites**: ... |)
_CITES_PAT = re.compile(_field("Cites?") + r"([^|\n]+)")
_SHARPE_PAT = re.compile(_field("Sharpe") + r"(\d+)")
_CONFIDENCE_PAT = re.compile(_field("Confidence") + r"([^\n|*]+)", re.IGNORECASE)
_ISO_PAT = re.compile(_field("ISO") + r"([^\n|*]+)")
_TITLE_PAT = re.compile(r"^#+\s+L-\d+[:\s—–-]*(.+)", re.MULTILINE)


def parse_meta(text: str) -> dict:
    """Parse metadata from a lesson file's text content.

    Returns a dict with keys: session, domain, level, cites_refs, cites_text,
    sharpe, confidence, iso, title. Missing fields are None.
    """
    m_sess = _SESSION_PAT.search(text)
    m_dom = _DOMAIN_PAT.search(text)
    m_level = _LEVEL_PAT.search(text)
    m_cites = _CITES_PAT.search(text)
    m_sharpe = _SHARPE_PAT.search(text)
    m_conf = _CONFIDENCE_PAT.search(text)
    m_iso = _ISO_PAT.search(text)
    m_title = _TITLE_PAT.search(text)

    cites_text = m_cites.group(1).strip() if m_cites else None
    cites_refs = re.findall(r"\bL-(\d+)\b", cites_text) if cites_text else []

    domain_raw = m_dom.group(1).strip() if m_dom else None
    # Remove trailing ** from bold format capture
    domain_clean = re.sub(r"\*+$", "", domain_raw).strip() if domain_raw else None

    return {
        "session": int(m_sess.group(1)) if m_sess else None,
        "domain": domain_clean,
        "level": m_level.group(1).strip().rstrip("*").strip() if m_level else None,
        "cites_text": cites_text,
        "cites_refs": cites_refs,
        "sharpe": int(m_sharpe.group(1)) if m_sharpe else None,
        "confidence": m_conf.group(1).strip().rstrip("*").strip() if m_conf else None,
        "iso": m_iso.group(1).strip().rstrip("*").strip() if m_iso else None,
        "title": m_title.group(1).strip() if m_title else None,
    }
