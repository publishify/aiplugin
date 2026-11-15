"""The character map: who appears, how often, and with whom. The board names the characters; this
code does the counting and the layout, so the map is the same every time. Standard library only.

characters.json, written by the board into the work folder:
  {"characters": [{"name": "Dorothy", "aliases": ["Dorothy", "the girl"]}],
   "relations": [{"a": "Dorothy", "b": "Toto", "label": "her dog", "location": "c1p3", "quote": "..."}]}
"""

import math
import re

from quotes import check_quote
from text import lower

# Languages that add endings straight onto a name ("tilki" → "tilkinin").
_SUFFIXING = {"tr", "az", "fi", "hu", "ku"}
_MIN_STEM = 4
_MAX_SUFFIX = 5
MAX_CHARACTERS = 40
WIDTH, HEIGHT = 1000, 620


def _pattern(aliases, language):
    parts = []
    for alias in sorted({lower(a.strip(), language) for a in aliases if a and a.strip()}, key=len, reverse=True):
        stem = re.escape(alias)
        if language in _SUFFIXING and len(alias) >= _MIN_STEM:
            stem += rf"[^\W\d_]{{0,{_MAX_SUFFIX}}}"
        parts.append(stem)
    return re.compile(rf"(?<![^\W_])(?:{'|'.join(parts)})(?![^\W_])") if parts else None


def _layout(nodes, links):
    """A small force layout with a fixed start, so the same book always draws the same map."""
    n = len(nodes)
    if not n:
        return
    order = sorted(range(n), key=lambda i: -nodes[i]["count"])
    pos = {}
    for rank, i in enumerate(order):
        if rank == 0:
            pos[i] = [0.0, 0.0]
        else:
            angle = 2.399963 * rank  # golden angle: an even spiral
            r = 0.25 + 0.75 * math.sqrt(rank / n)
            pos[i] = [r * math.cos(angle), r * math.sin(angle)]
    index = {node["id"]: i for i, node in enumerate(nodes)}
    top = max((l["count"] for l in links), default=1) or 1
    k = 1.1 / math.sqrt(n)
    for step in range(300):
        heat = 0.1 * (1 - step / 300)
        move = {i: [0.0, 0.0] for i in pos}
        for i in pos:
            for j in pos:
                if i >= j:
                    continue
                dx, dy = pos[i][0] - pos[j][0], pos[i][1] - pos[j][1]
                d = math.hypot(dx, dy) or 0.01
                f = k * k / d
                move[i][0] += dx / d * f
                move[i][1] += dy / d * f
                move[j][0] -= dx / d * f
                move[j][1] -= dy / d * f
        for l in links:
            i, j = index[l["a"]], index[l["b"]]
            dx, dy = pos[i][0] - pos[j][0], pos[i][1] - pos[j][1]
            d = math.hypot(dx, dy) or 0.01
            f = d * d / k * (0.3 + 0.7 * l["count"] / top)
            move[i][0] -= dx / d * f
            move[i][1] -= dy / d * f
            move[j][0] += dx / d * f
            move[j][1] += dy / d * f
        for i in pos:
            move[i][0] -= pos[i][0] * 0.05
            move[i][1] -= pos[i][1] * 0.05
            d = math.hypot(*move[i]) or 0.01
            pos[i][0] += move[i][0] / d * min(d, heat)
            pos[i][1] += move[i][1] / d * min(d, heat)
    xs, ys = [p[0] for p in pos.values()], [p[1] for p in pos.values()]
    span_x, span_y = (max(xs) - min(xs)) or 1, (max(ys) - min(ys)) or 1
    pad = 90
    for i, node in enumerate(nodes):
        node["x"] = round(pad + (pos[i][0] - min(xs)) / span_x * (WIDTH - 2 * pad)) if n > 1 else WIDTH // 2
        node["y"] = round(pad + (pos[i][1] - min(ys)) / span_y * (HEIGHT - 2 * pad)) if n > 1 else HEIGHT // 2


def character_map(units, given, language="en"):
    """Counts made by code from the characters the board named. Returns None when none were named."""
    listed = [c for c in (given or {}).get("characters", []) if isinstance(c, dict) and str(c.get("name", "")).strip()]
    listed = listed[:MAX_CHARACTERS]
    if not listed:
        return None
    people = []
    for n, c in enumerate(listed, start=1):
        name = str(c["name"]).strip()
        aliases = [name] + [a for a in c.get("aliases") or [] if isinstance(a, str)]
        people.append({"id": f"k{n}", "name": name, "pattern": _pattern(aliases, language), "note": str(c.get("note") or "")})

    seen = {p["id"]: {} for p in people}  # id → chapter → paragraphs
    together = {}  # (a, b) → chapter → paragraphs
    for u in units:
        for paragraph in u["paragraphs"]:
            text = lower(paragraph, language)
            here = [p["id"] for p in people if p["pattern"] and p["pattern"].search(text)]
            for pid in here:
                seen[pid][u["id"]] = seen[pid].get(u["id"], 0) + 1
            for i, a in enumerate(here):
                for b in here[i + 1 :]:
                    pair = together.setdefault((a, b), {})
                    pair[u["id"]] = pair.get(u["id"], 0) + 1

    nodes = [
        {"id": p["id"], "name": p["name"], "note": p["note"], "count": sum(seen[p["id"]].values()), "chapters": list(seen[p["id"]])}
        for p in people
        if seen[p["id"]]
    ]
    present = {node["id"] for node in nodes}
    by_name = {lower(p["name"], language): p["id"] for p in people}
    labels = {}
    for r in (given or {}).get("relations", []):
        if not isinstance(r, dict):
            continue
        a, b = by_name.get(lower(str(r.get("a", "")), language)), by_name.get(lower(str(r.get("b", "")), language))
        if not a or not b or a == b or a not in present or b not in present:
            continue
        found = check_quote(units, str(r.get("location", "")), str(r.get("quote", "")))
        if found["status"] != "found":
            continue  # a tie the work does not show is not drawn
        key = tuple(sorted((a, b), key=lambda x: int(x[1:])))
        labels.setdefault(key, []).append({"label": str(r.get("label") or ""), "location": found["location"], "quote": found["original"]})

    links = []
    for key in sorted(set(together) | set(labels), key=lambda k: (int(k[0][1:]), int(k[1][1:]))):
        chapters = together.get(key, {})
        links.append(
            {
                "a": key[0],
                "b": key[1],
                "count": sum(chapters.values()),
                "chapters": list(chapters),
                "labels": [x["label"] for x in labels.get(key, []) if x["label"]],
                "evidence": [{"location": x["location"], "quote": x["quote"]} for x in labels.get(key, [])],
            }
        )
    _layout(nodes, links)
    return {"nodes": nodes, "links": links}
