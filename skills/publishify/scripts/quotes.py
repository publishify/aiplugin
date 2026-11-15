"""Quote check (v5 L6): every note must quote the work exactly. Ported from the Publishify
platform (board/core/src/text/quote.ts). Typography is relaxed (curly quotes, dashes, ellipsis,
spaces); letters and letter case never are.
"""

import re

from text import canonical

_TYPOGRAPHY = {
    "“": '"', "”": '"', "„": '"', "‟": '"', "«": '"', "»": '"',
    "‘": "'", "’": "'", "‚": "'", "‛": "'", "—": "-", "–": "-", "‑": "-",
}


def _relax(chars):
    out, source = [], []
    for i, c in enumerate(chars):
        if c.isspace():
            if not out or out[-1] != " ":
                out.append(" ")
                source.append(i)
        elif c == "…":
            out.extend("...")
            source.extend([i, i, i])
        else:
            out.append(_TYPOGRAPHY.get(c, c))
            source.append(i)
    return out, source


def _positions(hay, needle):
    n = len(needle)
    first = needle[0]
    return [i for i in range(len(hay) - n + 1) if hay[i] == first and hay[i : i + n] == needle]


def _resolve(candidates, chars, hint):
    chosen = [r for r in candidates if hint and r[0] >= hint[0] and r[1] <= hint[1]] if len(candidates) > 1 and hint else candidates
    if len(chosen) == 1:
        s, e = chosen[0]
        return {"status": "found", "range": [s, e], "original": "".join(chars[s:e])}
    return {"status": "ambiguous", "count": len(chosen) or len(candidates)}


def find_quote(text, quote, hint=None):
    """Finds a quote; the range is in Unicode code points."""
    chars = list(canonical(text))
    target = list(canonical(quote).strip())
    if not target:
        return {"status": "missing"}
    exact = _positions(chars, target)
    if exact:
        return _resolve([(s, s + len(target)) for s in exact], chars, hint)
    relaxed, source = _relax(chars)
    needle, _ = _relax(target)
    found = _positions(relaxed, needle)
    if not found:
        return {"status": "missing"}
    ranges = [(source[s], source[s + len(needle) - 1] + 1) for s in found]
    return _resolve(ranges, chars, hint)


_LOCATION = re.compile(r"^c(\d+)(?:p(\d+))?$")


def check_quote(units, location, quote):
    """Checks one quote against the split work. Looks in the given paragraph first, then the
    chapter, then the whole work, and says where it was found."""
    by_id = {u["id"]: u for u in units}
    m = _LOCATION.match((location or "").strip().lower())
    places = []
    if m:
        unit = by_id.get(f"c{m.group(1)}")
        if unit and m.group(2):
            k = int(m.group(2)) - 1
            if 0 <= k < len(unit["paragraphs"]):
                places.append((f"{unit['id']}p{k + 1}", unit["paragraphs"][k]))
        if unit:
            places.extend((f"{unit['id']}p{k + 1}", p) for k, p in enumerate(unit["paragraphs"]))
    places.extend((f"{u['id']}p{k + 1}", p) for u in units for k, p in enumerate(u["paragraphs"]))
    seen = set()
    for where, paragraph in places:
        if where in seen:
            continue
        seen.add(where)
        result = find_quote(paragraph, quote)
        if result["status"] in ("found", "ambiguous"):
            return {
                "status": "found",
                "location": where,
                "moved": bool(m) and where != location.strip().lower(),
                "original": result.get("original", quote.strip()),
            }
    return {"status": "missing"}
