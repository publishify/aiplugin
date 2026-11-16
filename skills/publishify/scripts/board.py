#!/usr/bin/env python3
"""Publishify board scripts. Run on the person's computer or in their AI's code sandbox; nothing
here sends the work anywhere.

  python3 board.py prepare BOOK.docx [--form novel] [--work publishify-work]
      Reads the file (docx, epub, md, txt), splits it into chapters (c1, c2…) and paragraphs
      (c1p1…), measures it, and writes units.json, measure.json and facts.json into the work
      folder. Prints a short summary.

  python3 board.py check NOTES.json [--work publishify-work]
      Checks every quote of every note against the work. Drops notes whose quote is not in the
      work, fixes a location when the quote is elsewhere, writes NOTES.checked.json.

  python3 board.py merge ROLE1.json ROLE2.json … [--work publishify-work]
      For the editor-in-chief: checks quotes, joins all roles' notes, removes exact repeats and
      orders them high, medium, low. Writes merged.json.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from facts import fact_lines, life_checks, name_variants  # noqa: E402
from quotes import check_quote  # noqa: E402
from text import TextError, body, detect_language, measure, read_file, spelling, split  # noqa: E402

VERSION = "2026-11-15.1"


def _write(work, name, data):
    os.makedirs(work, exist_ok=True)
    path = os.path.join(work, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    return path


def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def prepare(path, form, work):
    raw = read_file(path)
    units, confidence = split(raw, form)
    if not units:
        raise TextError("The file has no readable text.")
    whole = "\n\n".join(body(u) for u in units)
    language = detect_language(whole)
    simple = [{"id": u["id"], "body": body(u)} for u in units]
    facts = {
        "fact_lines": fact_lines(simple),
        "name_variants": name_variants(simple),
        "life_checks": life_checks(simple),
    }
    measured = measure(whole, language if language != "und" else "en")
    _write(work, "units.json", {"version": VERSION, "source": os.path.basename(path), "language": language, "extractor": raw["extractor"], "units": units})
    _write(work, "measure.json", {"whole": measured, "spelling": spelling(units, language)})
    _write(work, "facts.json", facts)
    return {
        "version": VERSION,
        "work_folder": work,
        "language": language,
        "chapters_found": confidence == "high",
        "chapters": [{"id": u["id"], "title": u["title"], "paragraphs": len(u["paragraphs"]), "words": u["words"]} for u in units],
        "words": measured["words"],
        "long_sentences": measured["long_sentences"],
        "dialogue_ratio": round(measured["dialogue_ratio"], 2),
        "spelling_candidates": len(_load(os.path.join(work, "measure.json"))["spelling"]),
        "fact_lines": len(facts["fact_lines"]),
        "name_variants": [f"{v['rare']}~{v['common']}" for v in facts["name_variants"]],
        "life_checks": len(facts["life_checks"]),
        "next": "Read units.json for the text with locations; the continuity checker reads facts.json; the editor reads measure.json.",
    }


def _notes_of(data):
    if isinstance(data, list):
        return [n for d in data for n in _notes_of(d)]
    if isinstance(data, dict) and isinstance(data.get("notes"), list):
        role = data.get("role")
        return [dict(n, role=n.get("role", role)) for n in data["notes"] if isinstance(n, dict)]
    return []


def _check_notes(notes, units):
    kept, dropped, moved = [], 0, 0
    for n in notes:
        evidence = n.get("evidence") or []
        ok, fixed = bool(evidence), []
        for e in evidence:
            r = check_quote(units, str(e.get("location", "")), str(e.get("quote", "")))
            if r["status"] != "found":
                ok = False
                break
            moved += 1 if r["moved"] else 0
            fixed.append({"location": r["location"], "quote": r["original"]})
        if ok:
            kept.append(dict(n, evidence=fixed, quotes_checked=True))
        else:
            dropped += 1
    return kept, dropped, moved


def _check_stages(stages, units):
    """A stage keeps its state; its quote is checked like any other, and one the work does not
    hold is taken out so the page never shows it."""
    out, unproven = [], 0
    for s in stages:
        if not isinstance(s, dict):
            continue
        s = dict(s)
        if s.get("quote"):
            r = check_quote(units, str(s.get("location", "")), str(s["quote"]))
            if r["status"] == "found":
                s["location"], s["quote"] = r["location"], r["original"]
            else:
                s.pop("quote", None)
                s.pop("location", None)
                unproven += 1
        out.append(s)
    return out, unproven


def _is_reader(note):
    return "reader" in str(note.get("role") or "").lower()


def check(path, work):
    units = _load(os.path.join(work, "units.json"))["units"]
    data = _load(path)
    kept, dropped, moved = _check_notes(_notes_of(data), units)
    out = dict(data, notes=kept) if isinstance(data, dict) else {"notes": kept}
    stages_unproven = 0
    if isinstance(data, dict) and isinstance(data.get("stages"), list):
        out["stages"], stages_unproven = _check_stages(data["stages"], units)
    target = _write(os.path.dirname(os.path.abspath(path)), os.path.basename(path).replace(".json", "") + ".checked.json", out)
    return {"kept": len(kept), "dropped": dropped, "locations_fixed": moved, "stages_without_quote": stages_unproven, "written": target}


_RANK = {"high": 0, "medium": 1, "low": 2}


def merge(paths, work):
    units = _load(os.path.join(work, "units.json"))["units"]
    datas = [_load(p) for p in paths]
    kept, dropped, _ = _check_notes(_notes_of(datas), units)
    seen, merged = set(), []
    for n in kept:
        key = (n.get("kind"), tuple((e["location"], e["quote"]) for e in n["evidence"]))
        if not _is_reader(n):  # a reader's reaction stays, even on a quote another note uses
            if key in seen:
                continue
            seen.add(key)
        merged.append(n)
    merged.sort(key=lambda n: (_RANK.get(n.get("priority"), 3), 0 if n.get("kind") == "problem" else 1))
    stages = next((d.get("stages") for d in datas if isinstance(d, dict) and d.get("stages")), None)
    out = {"role": "editor-in-chief", "notes": merged}
    if stages:
        out["stages"] = _check_stages(stages, units)[0]
    target = _write(work, "merged.json", out)
    return {"notes": len(merged), "dropped_for_quotes": dropped, "repeats_removed": len(kept) - len(merged), "written": target}


def main(argv=None):
    p = argparse.ArgumentParser(prog="board.py", description="Publishify board scripts")
    sub = p.add_subparsers(dest="command", required=True)
    a = sub.add_parser("prepare")
    a.add_argument("file")
    a.add_argument("--form", default="novel", choices=["novel", "novella", "stories"])
    a.add_argument("--work", default="publishify-work")
    b = sub.add_parser("check")
    b.add_argument("notes")
    b.add_argument("--work", default="publishify-work")
    c = sub.add_parser("merge")
    c.add_argument("notes", nargs="+")
    c.add_argument("--work", default="publishify-work")
    args = p.parse_args(argv)
    try:
        if args.command == "prepare":
            result = prepare(args.file, args.form, args.work)
        elif args.command == "check":
            result = check(args.notes, args.work)
        else:
            result = merge(args.notes, args.work)
    except (TextError, FileNotFoundError, json.JSONDecodeError) as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
