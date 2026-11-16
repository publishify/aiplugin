#!/usr/bin/env python3
"""The Publishify dashboard: one HTML page made from the board's checked notes, on the person's
computer or in their AI's sandbox. Uses no model and sends nothing anywhere.

  python3 dashboard.py strings [--language fa] [--work publishify-work]
      Prints the page's English strings as JSON, for the AI to translate when the person's
      language has no built-in translation. Save the translation as a JSON object
      {"English": "translation"} and pass it to render with --strings.

  python3 dashboard.py render [--title "Book"] [--language tr] [--strings FILE] [--note TEXT] [--work publishify-work]
      Reads units.json, measure.json, the roles' *.checked.json, merged.json and, when the board
      wrote it, characters.json from the work folder and writes dashboard.html there. The page
      works offline.

Ported from the Masthead dashboard (2026-11-10): the Wayfarer's Seven Stages clock, board notes,
key decisions, chapter bars, word and sentence patterns, every role's notes and the stage map.
The character map (people.py) is new in Publishify.
"""

import argparse
import glob
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from people import character_map  # noqa: E402
from text import _DIALOGUE  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "dashboard", "template.html")
PLACEHOLDER = "__PUBLISHIFY_DATA__"
BRAND = "Publishify"
VERSION = "2026-11-16.1"

LABELS = {
    "status": {"green": "Clear", "yellow": "Implicit", "gray": "Absent", "light": "Not written or not read"},
    "review": {"green": "Reviewed", "yellow": "Worth a look", "gray": "Not read"},
    "kinds": {"prose": "Prose", "draft": "Draft", "note": "Note", "raw": "Raw text", "missing": "Not written yet"},
    "states": {"complete": "Reviewed", "limited": "Limited review", "not_run": "Not run", "not_needed": "Not needed"},
    "modules": {"developmental": "Developmental editor", "spelling": "Spelling", "continuity": "Continuity", "reader": "Reader panel"},
    "roles": {"editor": "Editor", "reader": "Reader Panel"},
}
COLORS = {"green": "#2B8064", "yellow": "#EDBB4A", "red": "#C65D56", "gray": "#ADB4B1", "light": "#E4E6E1"}
METHOD = {
    "word_count": "Sequences of letters and numbers, headings excluded.",
    "repetitions": "Surface forms only; no stemming.",
    "scope": "Reviewed text only",
    "patterns": "Repetition is counted, not judged.",
}
STAGES = {
    "en": [
        ("Call", "What is missing, and how does the wayfarer answer the call?"),
        ("Guide", "Who shows the way, and what is being prepared?"),
        ("Threshold", "What is left behind, and why is there no way back?"),
        ("Trial", "How does the road test them, and what is the rule of the new world?"),
        ("Awakening", "What burned away, and what did they wake to?"),
        ("Reward", "What was the price, and who have they become?"),
        ("Return", "What do they bring home, and has home changed?"),
    ],
    "tr": [
        ("Çağrı", "Eksik olan ne, yolcu çağrıya nasıl cevap veriyor?"),
        ("Kılavuz", "Kim yol gösteriyor, ne hazırlanıyor?"),
        ("Eşik", "Neyi geride bırakıyor, geri dönüş neden yok?"),
        ("Sınav", "Yol onu nasıl sınıyor, yeni dünyanın kuralı ne?"),
        ("Uyanış", "Neyi yakıp neye uyandı?"),
        ("Ödül", "Bedeli ne, artık kim oldu?"),
        ("Dönüş", "Ocağa ne getiriyor, ocak değişti mi?"),
    ],
}
STAGE_COLOR = {"clear": "green", "implicit": "yellow", "absent": "gray", "not_written": "light"}
LOCATION = re.compile(r"^c(\d+)(?:p(\d+))?$")
MAX_DECISIONS = 3


class DashboardError(Exception):
    """A problem the person can fix; the message is safe to show."""


def _load(path, default=None):
    if not os.path.exists(path):
        if default is not None:
            return default
        raise DashboardError(f"Missing {os.path.basename(path)}. Run board.py prepare first.")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def role_of(name):
    """The role id behind whatever name the AI wrote."""
    n = str(name or "").lower()
    if "chief" in n:
        return "chief_editor"
    if "continu" in n:
        return "continuity"
    if "reader" in n:
        return "reader_panel"
    if "editor" in n:
        return "editor"
    return n


def ref(location, quote):
    m = LOCATION.match(str(location or ""))
    if not m or not quote:
        return None
    return {"chapter": f"c{m.group(1)}", "paragraph": int(m.group(2) or 0), "quote": quote}


def refs(evidence):
    return [r for r in (ref(e.get("location"), e.get("quote")) for e in evidence or []) if r]


def label_of(note):
    if role_of(note.get("role")) == "reader_panel":
        return "Reader reaction"
    if note.get("kind") == "strength":
        return "Working"
    return "Definite issue" if note.get("certainty") == "definite" else "Preference"


def _module_of(note):
    role = role_of(note.get("role"))
    if role == "continuity" or note.get("topic") == "consistency":
        return "continuity"
    if role == "reader_panel" or note.get("topic") == "reader":
        return "reader"
    if note.get("topic") == "language":
        return "spelling"
    return "developmental"


def _first_sentence(message):
    m = re.match(r"(.+?[.!?…])(?:\s|$)", str(message), flags=re.S)
    return m.group(1) if m else str(message)


def _chapter_stats(unit):
    ps = unit["paragraphs"]
    return {"paragraphs": len(ps), "dialogue": sum(1 for p in ps if _DIALOGUE.search(p))}


def build(work, title=None, language=None, generated_at=None, note=None):
    units_file = _load(os.path.join(work, "units.json"))
    measured = _load(os.path.join(work, "measure.json"))
    units = units_file["units"]
    language = language or units_file.get("language") or "en"
    if language == "und":
        language = "en"
    whole = measured.get("whole", {})

    roles = {}
    for path in sorted(glob.glob(os.path.join(work, "*.checked.json"))):
        data = _load(path)
        if isinstance(data, dict):
            role = role_of(data.get("role") or os.path.basename(path).split(".")[0])
            if role in roles:  # one file per reader: the panel is all of them together
                first = roles[role]
                first["notes"] = (first.get("notes") or []) + (data.get("notes") or [])
                first["summary"] = " ".join(x for x in [first.get("summary"), data.get("summary")] if x)
                first["stages"] = first.get("stages") or data.get("stages")
            else:
                roles[role] = data
    merged = _load(os.path.join(work, "merged.json"), default={})
    if not roles and not merged:
        raise DashboardError("No checked notes yet. Run board.py check for each role first.")

    if merged.get("notes"):
        notes = merged["notes"]
    else:
        notes = [dict(n, role=n.get("role") or r) for r, d in roles.items() for n in d.get("notes", [])]
    for r, d in roles.items():
        for n in d.get("notes", []):
            n.setdefault("role", r)

    read = set()
    for n in notes:
        for e in n.get("evidence") or []:
            m = LOCATION.match(str(e.get("location", "")))
            if m:
                read.add(f"c{m.group(1)}")
    # A role that ran read the whole work; notes only show where it spoke.
    ran = set(roles) | ({"chief_editor"} if merged else set())
    if ran - {"chief_editor"}:
        read = {u["id"] for u in units}

    chapters, shown = [], set()
    for u in units:
        here = [n for n in notes if any(r["chapter"] == u["id"] for r in refs(n.get("evidence")))]
        concerns = [n for n in here if n.get("kind") != "strength" and role_of(n.get("role")) != "reader_panel" and n.get("priority") != "low"]
        # A note that quotes several chapters is shown in full under the first; a later chapter shows
        # its next note, or only the first sentence when it has no other.
        concern = next((n for n in concerns if id(n) not in shown), concerns[0] if concerns else None)
        repeated = bool(concern) and id(concern) in shown
        if concern:
            shown.add(id(concern))
        status = "gray" if u["id"] not in read else "yellow" if concern else "green"
        stats = _chapter_stats(u)
        chapters.append(
            {
                "id": u["id"],
                "title": u.get("title") or (title if len(units) == 1 and title else f"#{u['id'][1:]}"),
                "kind": "prose",
                "evaluated": u["id"] in read,
                "locked": False,
                "word_count": u["words"],
                "paragraph_count": stats["paragraphs"],
                "dialogue_paragraphs": stats["dialogue"],
                "in_repetition_scope": True,
                "review": {
                    "chapter": u["id"],
                    "status": status,
                    "note": _first_sentence(concern["message"]) if repeated else (concern or {}).get("message", "—"),
                    "evidence": refs((concern or {}).get("evidence")),
                },
            }
        )

    stages_given = merged.get("stages") or next((d.get("stages") for d in roles.values() if d.get("stages")), None) or []
    names = STAGES.get(language.split("-")[0], STAGES["en"])
    stage_map = []
    for i, (name, function) in enumerate(names, start=1):
        found = [s for s in stages_given if int(s.get("no", 0) or 0) == i]
        last = found[-1] if found else None
        evidence = [r for r in (ref(s.get("location"), s.get("quote")) for s in found) if r]
        stage_map.append(
            {
                "id": i,
                "name": name,
                "function": function,
                "status": STAGE_COLOR.get((last or {}).get("state"), "light"),
                "chapters": sorted({r["chapter"] for r in evidence}, key=lambda c: int(c[1:])),
                "note": (last or {}).get("note", ""),
                "evidence": evidence,
            }
        )
    reached = [
        (int(r["chapter"][1:]), s["no"])
        for s in stages_given
        if s.get("state") in ("clear", "implicit")
        for r in [ref(s.get("location"), s.get("quote"))]
        if r
    ]
    current = None
    if reached:
        last_unit = max(u for u, _ in reached)
        here = [s for s in stages_given if (ref(s.get("location"), s.get("quote")) or {}).get("chapter") == f"c{last_unit}"]
        current = {
            "chapter": f"c{last_unit}",
            "merhale": sorted({int(s["no"]) for s in here}),
            "summary": "",
            "evidence": [r for r in (ref(s.get("location"), s.get("quote")) for s in here) if r],
        }

    def state(role):
        return "complete" if role in roles else "not_run"

    def module(mid, role):
        found = [n for n in notes if _module_of(n) == mid]
        if mid == "spelling":
            found += [
                {"kind": "problem", "certainty": "definite", "message": "", "wrong": s["wrong"], "right": s["right"],
                 "evidence": [{"location": s["location"], "quote": s["quote"]}]}
                for s in measured.get("spelling", [])
            ]
        return {
            "id": mid,
            "state": state(role) if mid != "spelling" else ("complete" if roles else "not_run"),
            "summary": "",
            "evidence": [],
            "findings": [
                {
                    "label": label_of(n),
                    "text": " · ".join(x for x in [f"{n['wrong']} → {n['right']}" if n.get("wrong") and n.get("right") else "", n.get("message", "")] if x),
                    "evidence": refs(n.get("evidence")),
                }
                for n in found
            ],
        }

    def opinion(role):
        d = roles.get(role, {})
        top = next((n for n in d.get("notes", [])), None)
        return {"state": state(role), "summary": d.get("summary", ""), "evidence": refs((top or {}).get("evidence"))[:1]}

    problems = [n for n in notes if n.get("kind") != "strength" and role_of(n.get("role")) != "reader_panel"]
    decisions = [{"label": label_of(n), "text": n.get("message", ""), "evidence": refs(n.get("evidence"))} for n in problems[:MAX_DECISIONS]]

    people = character_map(units, _load(os.path.join(work, "characters.json"), default={}), (units_file.get("language") or language).split("-")[0])
    if people:
        for link in people["links"]:
            link["evidence"] = refs(link["evidence"])

    sentences = whole.get("sentences", 0)
    total = sum(u["words"] for u in units)
    digest = hashlib.sha256("\n\n".join("\n\n".join(u["paragraphs"]) for u in units).encode("utf-8")).hexdigest()
    return {
        "project": {"title": title or os.path.splitext(units_file.get("source") or "")[0] or None, "note": note or ""},
        "locale": language,
        "metrics_sha256": digest,
        "summary": {
            "all_words": total,
            "prose_words": sum(u["words"] for u in units if u["id"] in read),
            "draft_words": 0,
            "note_words": 0,
            "chapter_count": len(units),
            "evaluated_chapters": len(read),
            "repetition_words": total,
            "sentence_count": sentences,
            "mean_sentence_words": round(total / sentences, 1) if sentences else 0,
            "long_sentences_35": whole.get("long_sentences", 0),
        },
        "lexical": {
            "content_words": [dict(w, refs=[]) for w in whole.get("frequent_words", [])],
            "all_frequent_words": None,
            "phrases": [dict(p, refs=[]) for p in whole.get("repetition_candidates", [])],
            "sentences": None,
            "patterns": None,
        },
        "method": METHOD,
        "chapters": chapters,
        "analysis": {
            "schema_version": 1,
            "mode": "board",
            "metrics_sha256": digest,
            "generated_at": generated_at,
            "coverage": {"read": len(read), "total": len(units)},
            "reading_mode": "independent",
            "journeys": bool(stages_given),
            "overview": merged.get("summary", ""),
            "current": current,
            "maps": {"merhale": stage_map},
            "stages_localized": language.split("-")[0] in STAGES and language.split("-")[0] != "en",
            "chapter_reviews": [],
            "opinions": {"editor": opinion("editor"), "reader": opinion("reader_panel")},
            "decisions": decisions,
            "disagreements": "",
            "characters": people,
            "modules": [
                module("developmental", "editor"),
                module("spelling", "editor"),
                module("continuity", "continuity"),
                module("reader", "reader_panel"),
            ],
        },
        "labels": LABELS,
        "colors": COLORS,
    }


# --- strings ------------------------------------------------------------------------------------

def template():
    with open(TEMPLATE, encoding="utf-8") as f:
        return f.read()


def _values(node):
    if isinstance(node, str):
        return [node]
    if isinstance(node, dict):
        return [v for x in node.values() for v in _values(x)]
    return []


def catalog(page, data=None):
    """Every English string the page can show: its markup, its script and the fixed report labels."""
    start, end = page.index("<body>"), page.index('<script id="dashboard-data"')
    body, script = page[start:end], page[end:]
    found = [m.strip() for m in re.findall(r">([^<>]+)<", body)]
    found += re.findall(r'aria-label="([^"]+)"', body)
    found += [json.loads(f'"{m}"') for m in re.findall(r'\bt\("((?:[^"\\]|\\.)*)"', script)]
    found += _values(LABELS) + _values(METHOD)
    found += ["Working", "Definite issue", "Preference", "Reader reaction"]
    found += [x for pair in STAGES["en"] for x in pair]
    return sorted({s for s in found if re.search(r"[^\W\d_]", s) and s != BRAND})


def _slots(s):
    return sorted(re.findall(r"\{(\w+)\}", s))


def clean_strings(raw):
    """Keeps translations that are text and carry the same {slots} as the English."""
    out = {}
    for k, v in (raw or {}).items():
        if isinstance(k, str) and isinstance(v, str) and v.strip() and _slots(k) == _slots(v):
            out[k] = v
    return out


def builtin_strings(language):
    path = os.path.join(HERE, "dashboard", f"strings.{language.split('-')[0]}.json")
    return _load(path) if os.path.exists(path) else None


def _embed(data):
    s = json.dumps(data, ensure_ascii=False)
    return s.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def render(data, strings=None, language="en"):
    page = template()
    if PLACEHOLDER not in page:
        raise DashboardError("The dashboard template is damaged.")
    for field in ("verdict", "ready_to_publish"):
        if field in data["analysis"]:
            raise DashboardError(f"A report cannot carry a verdict field: {field}")
    payload = dict(data, ui={"lang": language, "strings": clean_strings(strings)})
    return page.replace(PLACEHOLDER, _embed(payload))


def main(argv=None):
    p = argparse.ArgumentParser(prog="dashboard.py", description="Publishify dashboard")
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("strings")
    s.add_argument("--language", default=None)
    s.add_argument("--work", default="publishify-work")
    r = sub.add_parser("render")
    r.add_argument("--title", default=None)
    r.add_argument("--language", default=None)
    r.add_argument("--strings", default=None)
    r.add_argument("--note", default=None, help="One line shown in a strip at the top, e.g. what the sample was run on.")
    r.add_argument("--work", default="publishify-work")
    args = p.parse_args(argv)
    try:
        if args.command == "strings":
            lang = args.language or "en"
            have = builtin_strings(lang) or {}
            todo = [x for x in catalog(template()) if x not in have]
            print(json.dumps({"language": lang, "built_in": bool(have), "translate": todo}, ensure_ascii=False, indent=1))
            return 0
        from datetime import datetime, timezone

        data = build(args.work, args.title, args.language, datetime.now(timezone.utc).isoformat(), args.note)
        lang = data["locale"]
        strings = dict(builtin_strings(lang) or {})
        if args.strings:
            strings.update(_load(args.strings))
        missing = 0 if lang.startswith("en") else sum(1 for x in catalog(template()) if x not in strings)
        out = os.path.join(args.work, "dashboard.html")
        with open(out, "w", encoding="utf-8") as f:
            f.write(render(data, strings, lang))
        a = data["analysis"]
        print(json.dumps({
            "version": VERSION,
            "written": out,
            "language": lang,
            "untranslated_strings": missing,
            "chapters": len(data["chapters"]),
            "notes": sum(len(m["findings"]) for m in a["modules"]),
            "stages_mapped": sum(1 for s in a["maps"]["merhale"] if s["status"] != "light"),
            "characters_mapped": len((a.get("characters") or {}).get("nodes", [])),
            "next": "Offer dashboard.html to the person; it opens in any browser and works offline."
            + (" Some strings are in English: run `dashboard.py strings --language " + lang + "`, translate them and render again with --strings." if missing else ""),
        }, ensure_ascii=False, indent=1))
    except (DashboardError, FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
