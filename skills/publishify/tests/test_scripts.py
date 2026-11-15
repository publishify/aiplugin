"""The platform's TypeScript tests (board/core/test, 2026-11-14), ported one for one, plus the
quote check and merge used by the board. Run: python3 -m unittest discover -s tests"""

import io
import json
import os
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import board  # noqa: E402
from facts import fact_lines, name_variants, names  # noqa: E402
from quotes import check_quote, find_quote  # noqa: E402
from text import MAX_UNIT_CHARS, TextError, canonical, measure, paragraphs, read_docx, read_epub, read_plain, split  # noqa: E402


def zipped(files):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for name, content in files.items():
            z.writestr(name, content)
    return buf.getvalue()


class Canonical(unittest.TestCase):
    def test_line_endings_and_unicode(self):
        self.assertEqual(canonical("a\r\nb\rc"), "a\nb\nc")
        self.assertEqual(canonical("ş"), "ş")

    def test_paragraphs(self):
        self.assertEqual(paragraphs("  one \n\n\n two\n \n three"), ["one", "two", "three"])


class Quotes(unittest.TestCase):
    text = "Sam “came” home. Ali came too."

    def test_exact_in_code_points(self):
        self.assertEqual(find_quote("😀 Ali", "Ali"), {"status": "found", "range": [2, 5], "original": "Ali"})

    def test_relaxes_typography_and_returns_original(self):
        r = find_quote(self.text, 'Sam "came" home')
        self.assertEqual((r["status"], r["original"]), ("found", "Sam “came” home"))

    def test_ellipsis_and_spaces(self):
        self.assertEqual(find_quote("Later…  gone", "Later... gone")["status"], "found")

    def test_letters_and_case_not_relaxed(self):
        self.assertEqual(find_quote(self.text, "sam")["status"], "missing")
        self.assertEqual(find_quote(self.text, "Som")["status"], "missing")

    def test_ambiguity_and_hint(self):
        self.assertEqual(find_quote("went and went", "went"), {"status": "ambiguous", "count": 2})
        self.assertEqual(find_quote("went and went", "went", (5, 13))["range"], [9, 13])

    def test_empty(self):
        self.assertEqual(find_quote(self.text, "  ")["status"], "missing")


class Splitting(unittest.TestCase):
    def raw(self, text):
        return {"text": text, "headings": [], "extractor": "test"}

    def test_turkish_headings(self):
        units, confidence = split(self.raw("Künye\n\n1. Bölüm: İstanbul\n\nBir.\n\nBİRİNCİ BÖLÜM\n\nİki."), "novel")
        self.assertEqual(confidence, "high")
        self.assertEqual([u["title"] for u in units], [None, "1. Bölüm: İstanbul", "BİRİNCİ BÖLÜM"])
        self.assertEqual(units[1]["paragraphs"], ["Bir."])
        self.assertEqual([u["id"] for u in units], ["c1", "c2", "c3"])

    def test_english_headings(self):
        self.assertEqual(split(self.raw("Chapter 1\n\nOne."), "novel")[0][0]["title"], "Chapter 1")

    def test_confidence(self):
        self.assertEqual(split(self.raw("Only text."), "novel")[1], "low")
        self.assertEqual(split(self.raw("Only text."), "stories")[1], "high")

    def test_oversized_unit(self):
        p = "a" * (MAX_UNIT_CHARS - 10)
        units, _ = split(self.raw(f"# Long\n\n{p}\n\n{p}"), "novel")
        self.assertEqual([u["title"] for u in units], ["Long (1)", "Long (2)"])


class Formats(unittest.TestCase):
    def test_bom_and_yaml(self):
        self.assertEqual(read_plain("﻿---\nname: x\n---\nText", True)["text"], "Text")
        self.assertEqual(read_plain("---\nstays", False)["text"], "---\nstays")

    def test_docx(self):
        xml = """<w:document><w:body>
          <w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Intro</w:t></w:r></w:p>
          <w:p><w:r><w:t xml:space="preserve">Ali &amp; </w:t></w:r><w:r><w:t>Bob</w:t></w:r></w:p>
          <w:p></w:p></w:body></w:document>"""
        r = read_docx(zipped({"word/document.xml": xml}))
        self.assertEqual(r["text"], "Intro\n\nAli & Bob")
        self.assertEqual(r["headings"], [0])

    def test_broken_docx(self):
        with self.assertRaisesRegex(TextError, "could not be read"):
            read_docx(zipped({"a.txt": "x"}))


CONTAINER = '<container><rootfiles><rootfile full-path="OEBPS/book.opf"/></rootfiles></container>'
OPF = """<package><manifest>
  <item id="nav" href="nav.xhtml" properties="nav"/>
  <item id="b" href="b%20two.xhtml"/><item id="a" href="a.xhtml"/><item id="c" href="c.xhtml"/>
</manifest><spine><itemref idref="a"/><itemref idref="b"/><itemref idref="c" linear="no"/></spine></package>"""


def page(content):
    return f"<html><head><title>Ignored</title><style>p{{}}</style></head><body>{content}</body></html>"


def book(extra=None):
    files = {
        "META-INF/container.xml": CONTAINER,
        "OEBPS/book.opf": OPF,
        "OEBPS/nav.xhtml": page("<p>Contents</p>"),
        "OEBPS/a.xhtml": page("<h1>One</h1><p>First &amp; <em>best</em>.</p>"),
        "OEBPS/b two.xhtml": page("<p>No heading here.</p><p>Second line.</p>"),
        "OEBPS/c.xhtml": page("<p>Left out.</p>"),
    }
    files.update(extra or {})
    return zipped(files)


class Epub(unittest.TestCase):
    def test_spine_order(self):
        r = read_epub(book())
        self.assertEqual(r["text"], "One\n\nFirst & best.\n\nNo heading here.\n\nSecond line.")
        self.assertEqual(r["headings"], [0, 2])

    def test_protected(self):
        with self.assertRaises(TextError):
            read_epub(book({"META-INF/encryption.xml": "<encryption><enc>AES</enc></encryption>"}))

    def test_not_epub(self):
        with self.assertRaises(TextError):
            read_epub(zipped({"a.txt": "x"}))


class Measurement(unittest.TestCase):
    def test_counts_and_turkish_case(self):
        m = measure("“Nasılsın?” dedi Işık.\n\nKapıyı açtı ve çıktı. Kapıyı açtı ve çıktı.\n\nIŞIK ışık ışık.")
        self.assertEqual(m["paragraphs"], 3)
        self.assertAlmostEqual(m["dialogue_ratio"], 1 / 3)
        self.assertEqual(m["frequent_words"][0], {"word": "ışık", "count": 4})
        self.assertIn({"phrase": "kapıyı açtı ve çıktı", "count": 2}, m["repetition_candidates"])


UNITS = [
    {"id": "b1", "body": "Kapıyı Beşir açtı. Sonra Beşir çay getirdi. Yine Beşir gülümsedi. Bahçede Beşir koştu. Firdevs Hanım kırk beş yaşındaydı. Hava güzeldi."},
    {"id": "b2", "body": "Bülent Bekir’le koşar. Nihal’in annesi de o akşam bahçeye indi. Herkes sustu."},
]


class Facts(unittest.TestCase):
    def test_fact_lines(self):
        lines = [f"{x['unit']}: {x['sentence']}" for x in fact_lines(UNITS)]
        self.assertIn("b1: Firdevs Hanım kırk beş yaşındaydı.", lines)
        self.assertIn("b2: Nihal’in annesi de o akşam bahçeye indi.", lines)
        self.assertNotIn("b1: Hava güzeldi.", lines)

    def test_names(self):
        self.assertEqual(names("Nihal’in annesi geldi"), ["Nihal"])
        self.assertEqual(names("Bugün Ayşe geldi"), ["Ayşe"])

    def test_long_sentence_window(self):
        long = " ".join(f"word{i}" for i in range(50)) + " Firdevs Hanım kırk beş yaşındaydı " + " ".join(f"tail{i}" for i in range(50)) + "."
        line = fact_lines([{"id": "u", "body": long}])[0]
        self.assertIn(line["sentence"], long)
        self.assertLessEqual(len(line["sentence"].split()), 40)

    def test_name_variants(self):
        v = name_variants(UNITS + [{"id": "b3", "body": "Kapıyı Beşiri bekledi."}])
        self.assertEqual([f"{x['rare']}~{x['common']}" for x in v], ["Bekir~Beşir"])


class Board(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.work = os.path.join(self.dir, "work")
        path = os.path.join(self.dir, "book.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write("---\ntitle: x\n---\n# Bir\n\nAli eve geldi. Kapı “açıktı”.\n\nAnnesi bekliyordu.\n\n# İki\n\nAli uyudu.")
        self.summary = board.prepare(path, "novel", self.work)

    def notes(self, name, data):
        path = os.path.join(self.dir, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        return path

    def test_prepare(self):
        self.assertTrue(self.summary["chapters_found"])
        self.assertEqual([c["id"] for c in self.summary["chapters"]], ["c1", "c2"])
        self.assertTrue(os.path.exists(os.path.join(self.work, "facts.json")))

    def test_check_keeps_true_quotes_fixes_locations_drops_false(self):
        units = board._load(os.path.join(self.work, "units.json"))["units"]
        self.assertEqual(check_quote(units, "c1p1", 'Kapı "açıktı"')["status"], "found")
        self.assertEqual(check_quote(units, "c1p1", "Ali uyudu.")["location"], "c2p1")
        path = self.notes("editor.json", {"role": "editor", "notes": [
            {"kind": "problem", "priority": "low", "message": "ok", "evidence": [{"location": "c1p2", "quote": "Annesi bekliyordu."}]},
            {"kind": "problem", "priority": "high", "message": "made up", "evidence": [{"location": "c1p1", "quote": "Ali denize girdi."}]},
            {"kind": "strength", "priority": "low", "message": "moved", "evidence": [{"location": "c1p1", "quote": "Ali uyudu."}]},
        ]})
        r = board.check(path, self.work)
        self.assertEqual((r["kept"], r["dropped"], r["locations_fixed"]), (2, 1, 1))

    def test_merge_orders_and_removes_repeats(self):
        e = {"location": "c1p1", "quote": "Ali eve geldi."}
        a = self.notes("a.json", {"role": "editor", "notes": [{"kind": "problem", "priority": "low", "message": "a", "evidence": [e]}],
                                  "stages": [{"no": 1, "state": "absent"}]})
        b = self.notes("b.json", {"role": "continuity", "notes": [
            {"kind": "problem", "priority": "low", "message": "same", "evidence": [e]},
            {"kind": "problem", "priority": "high", "message": "first", "evidence": [{"location": "c2p1", "quote": "Ali uyudu."}]},
        ]})
        r = board.merge([a, b], self.work)
        self.assertEqual((r["notes"], r["repeats_removed"]), (2, 1))
        merged = board._load(r["written"])
        self.assertEqual(merged["notes"][0]["message"], "first")
        self.assertEqual(merged["stages"], [{"no": 1, "state": "absent"}])

    def test_unsupported_format(self):
        path = os.path.join(self.dir, "book.pdf")
        open(path, "w").close()
        self.assertEqual(board.main(["prepare", path, "--work", self.work]), 1)


if __name__ == "__main__":
    unittest.main()
