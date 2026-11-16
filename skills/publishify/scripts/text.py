"""Reading, splitting and measuring a work, on the person's computer or in their AI's sandbox.

Ported from the Publishify platform (board/core/src/text, 2026-11-14). Standard library only, so it
runs in Claude, ChatGPT's code interpreter and Codex without installing anything. Nothing here
sends text anywhere.
"""

import html
import posixpath
import re
import unicodedata
import zipfile
from urllib.parse import unquote

MAX_UNIT_CHARS = 40_000

# A word is letters or digits, joined by an apostrophe or hyphen ("don't", "Nihal'in").
_LETTER_OR_DIGIT = r"[^\W_]"
WORD = re.compile(rf"{_LETTER_OR_DIGIT}+(?:['’-]{_LETTER_OR_DIGIT}+)*")


class TextError(Exception):
    """A file Publishify cannot read; the message is safe to show the person."""


def canonical(text):
    """Line endings to \\n and Unicode to NFC. Nothing else is cleaned."""
    return unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))


def paragraphs(text):
    """Paragraphs separated by blank lines, trimmed."""
    return [p.strip() for p in re.split(r"\n\s*\n", canonical(text)) if p.strip()]


def words(text):
    return WORD.findall(text)


def lower(text, language="tr"):
    """Lower case that knows Turkish dotted and dotless i."""
    if language == "tr":
        text = text.replace("I", "ı").replace("İ", "i")
    return text.lower()


# --- file formats -------------------------------------------------------------------------------

_HEADING_STYLE = re.compile(r"^(?:heading|ba[sş]l[iı]k|title)", re.I)


def read_docx(data):
    """Paragraphs of a Word file; heading styles become section starts."""
    try:
        with zipfile.ZipFile(_as_file(data)) as z:
            xml = z.read("word/document.xml").decode("utf-8")
    except (KeyError, zipfile.BadZipFile) as e:
        raise TextError("The Word document could not be read.") from e
    ps, headings = [], []
    for p in re.finditer(r"<w:p(?:\s[^>]*)?>[\s\S]*?</w:p>", xml):
        block = p.group(0)
        text = ""
        for m in re.finditer(r"<w:t(?:\s[^>]*)?>([^<]*)</w:t>|<w:tab/>|<w:br/>", block):
            if m.group(1) is not None:
                text += html.unescape(m.group(1))
            else:
                text += "\t" if m.group(0) == "<w:tab/>" else "\n"
        text = text.strip()
        if not text:
            continue
        style = re.search(r'<w:pStyle\s+w:val="([^"]+)"', block)
        if style and _HEADING_STYLE.match(style.group(1)):
            headings.append(len(ps))
        ps.append(text)
    return {"text": "\n\n".join(ps), "headings": headings, "extractor": "docx@1"}


def _attr(tag, name):
    m = re.search(rf"\b{name}\s*=\s*[\"']([^\"']*)[\"']", tag, re.I)
    return m.group(1) if m else None


def read_epub(data):
    """An EPUB in spine order. Each spine file starts a new section."""
    try:
        z = zipfile.ZipFile(_as_file(data))
    except zipfile.BadZipFile as e:
        raise TextError("The EPUB could not be read.") from e
    names = set(z.namelist())

    def read(name):
        return z.read(name).decode("utf-8", "replace") if name in names else None

    encryption = read("META-INF/encryption.xml")
    if encryption and not re.search(r"obfuscation|font", encryption, re.I):
        raise TextError("This EPUB is protected and cannot be read.")
    root = _attr(read("META-INF/container.xml") or "", "full-path")
    opf = read(root) if root else None
    if not root or not opf:
        raise TextError("The EPUB could not be read.")
    base = root[: root.rfind("/") + 1] if "/" in root else ""
    items = {}
    for m in re.finditer(r"<item\s[^>]*>", opf, re.I):
        tag = m.group(0)
        item_id, href = _attr(tag, "id"), _attr(tag, "href")
        if item_id and href and not re.search(r"\bnav\b", _attr(tag, "properties") or "", re.I):
            items[item_id] = href
    ps, headings = [], []
    for m in re.finditer(r"<itemref\s[^>]*>", opf, re.I):
        tag = m.group(0)
        if _attr(tag, "linear") == "no":
            continue
        href = items.get(_attr(tag, "idref") or "")
        page = read(posixpath.normpath(base + unquote(href))) if href else None
        if not page:
            continue
        body = re.sub(r"<(head|script|style)\b[\s\S]*?</\1>", "", page, flags=re.I)
        first, has_heading = len(ps), False
        for b in re.finditer(r"<(h[1-6]|p|li|blockquote)\b[^>]*>([\s\S]*?)</\1>", body, re.I):
            inner = re.sub(r"<br\s*/?>", "\n", b.group(2), flags=re.I)
            text = html.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
            if not text:
                continue
            if re.match(r"^h[1-6]$", b.group(1), re.I):
                headings.append(len(ps))
                has_heading = True
            ps.append(text)
        if not has_heading and len(ps) > first:
            headings.append(first)
    if not ps:
        raise TextError("The EPUB has no readable text.")
    return {"text": "\n\n".join(ps), "headings": headings, "extractor": "epub@1"}


def read_plain(content, strip_yaml):
    text = content.lstrip("﻿")
    if strip_yaml:
        text = re.sub(r"^---\r?\n[\s\S]*?\r?\n---\r?\n", "", text, count=1)
    return {"text": text, "headings": [], "extractor": "text@1"}


def read_file(path):
    ext = posixpath.splitext(path.lower())[1]
    if ext in (".md", ".markdown"):
        with open(path, encoding="utf-8-sig") as f:
            return read_plain(f.read(), True)
    if ext == ".txt":
        with open(path, encoding="utf-8-sig") as f:
            return read_plain(f.read(), False)
    if ext in (".docx", ".epub"):
        with open(path, "rb") as f:
            data = f.read()
        return read_docx(data) if ext == ".docx" else read_epub(data)
    raise TextError(f"This file format is not supported yet: {ext or 'no extension'}. Use docx, epub, md or txt.")


def _as_file(data):
    import io

    return io.BytesIO(data)


# --- splitting ----------------------------------------------------------------------------------

_HEADINGS = [
    re.compile(r"^#{1,3}\s+\S"),
    re.compile(r"^(?:\d+\.?\s+)?bölüm\b", re.I),
    re.compile(r"^[A-ZÇĞİÖŞÜÂÎÛ]+(?:\s[A-ZÇĞİÖŞÜÂÎÛ]+)?\s+BÖLÜM\b"),
    re.compile(r"^(?:kısım|perde|sahne)\s+\S", re.I),
    re.compile(r"^(?:chapter|part|act|scene)\s+\S", re.I),
]
CHAPTERS_EXPECTED = {"novel", "novella"}


def is_heading(p):
    return len(p) <= 80 and any(r.search(p) for r in _HEADINGS)


def _chunks(ps):
    out, current, size = [], [], 0
    for p in ps:
        if current and size + len(p) > MAX_UNIT_CHARS:
            out.append(current)
            current, size = [], 0
        current.append(p)
        size += len(p) + 2
    if current:
        out.append(current)
    return out


def split(raw, form="novel"):
    """Units (chapters) with ids c1, c2…; paragraphs inside get ids c1p1, c1p2…"""
    ps = paragraphs(raw["text"])
    from_format = set(raw.get("headings") or [])
    groups, found = [], False
    for i, p in enumerate(ps):
        if i in from_format or is_heading(p):
            found = True
            groups.append({"title": re.sub(r"^#{1,3}\s+", "", p), "ps": []})
        elif groups:
            groups[-1]["ps"].append(p)
        else:
            groups.append({"title": None, "ps": [p]})
    units = []
    for g in groups:
        if not g["ps"]:
            continue
        parts = _chunks(g["ps"])
        for i, c in enumerate(parts):
            title = f"{g['title']} ({i + 1})" if g["title"] and len(parts) > 1 else g["title"]
            n = len(units) + 1
            units.append(
                {
                    "id": f"c{n}",
                    "title": title,
                    "paragraphs": c,
                    "words": sum(len(words(p)) for p in c),
                }
            )
    confidence = "high" if found or form not in CHAPTERS_EXPECTED else "low"
    return units, confidence


def body(unit):
    return "\n\n".join(unit["paragraphs"])


# --- language and measurement -------------------------------------------------------------------

_COMMON = {
    "en": "the and of to in that was with for his her had not but".split(),
    "tr": "bir ve bu için ile gibi ama çok daha olarak değil sonra kadar".split(),
    "de": "der die und das nicht ist ein eine mit auf für sich dem".split(),
    "fr": "le la les et des une dans que pour pas sur est avec".split(),
    "es": "el la los las y una que por para con pero del se".split(),
}


def detect_language(text):
    """A language tag, or "und" when the text does not clearly match one."""
    all_words = [w.lower() for w in words(text)]
    if not all_words:
        return "und"
    best, share = "und", 0.0
    for tag, common in _COMMON.items():
        s = set(common)
        score = sum(1 for w in all_words if w in s) / len(all_words)
        if score > share:
            best, share = tag, score
    return best if share >= 0.04 else "und"


_FUNCTION_WORDS = {
    "tr": "bir ve ile de da ki bu şu o için gibi ama daha çok en ne mi mı mu mü ya hem ise değil var yok",
    "en": "the and that this these those with for from not but you your she her his him they them their there here "
    "was were are been being have has had will would can could should what when where which who whom how why "
    "its it's i'm don't didn't than then into out about over under all any some one two very just more most "
    "said did does our ours yours too also only again upon",
    "fr": "les des une que qui pas mais est sont pour dans sur par avec sans sous plus bien comme tout tous toute "
    "toutes mon ton son mes tes ses nos vos leur leurs notre votre moi toi lui elle elles ils nous vous "
    "c’est c'est j’ai j'ai qu’il qu'il qu’elle qu'elle qu’on qu'on n’est n'est d’un d'un d’une d'une il était "
    "ont été être avoir fait dit très alors donc aussi encore cette ces cet cela ça ceci celui celle ceux "
    "quand où dont car non oui peu ici là puis même aux du au en et ou ni si je tu on ne se ce me te le la "
    "l’on l'on s’il s'il m’a m'a j’étais j'étais n’ai n'ai n’a n'a avait avais suis peut faire fit",
}
_FUNCTION_WORDS = {k: set(v.split()) for k, v in _FUNCTION_WORDS.items()}
_DIALOGUE = re.compile(r"^[\"“«‘'—–-]|[\"“«].+?[\"”»]")


def _tally(items):
    counts = {}
    for k in items:
        counts[k] = counts.get(k, 0) + 1
    return counts


def measure(text, language="tr"):
    """Counts made by code. Repetition candidates are counts, not errors."""
    ps = paragraphs(text)
    sentences = [s for s in re.split(r"[.!?…]+(?=\s|$)", text) if words(s)]
    all_words = [lower(w, language) for w in words(text)]
    skip = _FUNCTION_WORDS.get(language.split("-")[0], set())
    content = [w for w in all_words if len(w) > 2 and w not in skip]
    frequent = sorted(((w, c) for w, c in _tally(content).items() if c >= 3), key=lambda x: -x[1])[:30]
    grams = []
    for p in ps:
        w = [lower(x, language) for x in words(p)]
        for n in range(3, 7):
            grams.extend(" ".join(w[i : i + n]) for i in range(len(w) - n + 1))
    candidates = [(g, c) for g, c in _tally(grams).items() if c >= (3 if len(g.split(" ")) == 3 else 2)]
    repetition = [
        (g, c) for g, c in candidates if not any(o != g and g in o for o, _ in candidates)
    ]
    repetition.sort(key=lambda x: -x[1])
    return {
        "words": len(all_words),
        "sentences": len(sentences),
        "long_sentences": sum(1 for s in sentences if len(words(s)) > 35),
        "paragraphs": len(ps),
        "dialogue_ratio": (sum(1 for p in ps if _DIALOGUE.search(p)) / len(ps)) if ps else 0,
        "frequent_words": [{"word": w, "count": c} for w, c in frequent],
        "repetition_candidates": [{"phrase": g, "count": c} for g, c in repetition[:30]],
    }


# --- spelling -----------------------------------------------------------------------------------

_COMMON_ERRORS = {
    "tr": {
        "herkez": "herkes", "yanlız": "yalnız", "yalnış": "yanlış", "birşey": "bir şey",
        "herşey": "her şey", "hiçbirşey": "hiçbir şey", "hergün": "her gün", "birgün": "bir gün",
        "birsürü": "bir sürü", "şuan": "şu an", "orjinal": "orijinal", "tabiki": "tabii ki",
        "yada": "ya da", "makina": "makine", "süpriz": "sürpriz", "kiprik": "kirpik",
        "traş": "tıraş", "egzos": "egzoz",
    }
}


def spelling(units, language):
    """Common misspellings from a list, found without a model."""
    errors = _COMMON_ERRORS.get(language)
    if not errors:
        return []
    out = []
    for u in units:
        for i, p in enumerate(u["paragraphs"]):
            for w in re.findall(r"[^\W\d_]+", p):
                right = errors.get(lower(w, language))
                if right:
                    out.append({"location": f"{u['id']}p{i + 1}", "quote": w, "wrong": w, "right": right})
    return out
