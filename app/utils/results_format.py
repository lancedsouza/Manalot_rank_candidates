"""Plain-text lines for the post-ingestion results view (ISS-43)."""


def format_keywords_header(keywords):
    return f"JD Keywords: {', '.join(keywords)} [{len(keywords)} keywords]"


def format_result_row(name, email, matches, total):
    """`<name> <email> | <pct>% or <matched>/<total> | <resume> vs <JD> (<sim>%), ...` (ISS-43)."""
    who = " ".join(p for p in (name, email) if p) or "Unknown candidate"
    pct = (len(matches) / total * 100) if total else 0
    pairs = ", ".join(
        f"{m.candidate_skill} vs {m.jd_skill} ({m.similarity * 100:.0f}%)" for m in matches
    ) or "no keyword matches"
    return f"{who} | {pct:.0f}% or {len(matches)}/{total} | {pairs}"
