"""Help for the continuity checker on long books, ported from the Publishify platform
(board/core/src/text/facts.ts and prompts/facts-tr.ts, 2026-11-14).

A model loses track of two contradicting sentences thousands of words apart, so the checker gets:
- fact sentences: sentences that name someone and carry an age, number, colour, death, time,
  season or family tie, in book order with their unit;
- name variants: a rare name one letter away from a frequent one (Beşir / Bekir);
- life checks: after a death, later sentences that bring the same person back.
Keyword lists are Turkish; other languages fall back to names and digits only.
"""

import re

STRONG_TR = [
    "yaş", "doğdu", "doğmuş", "öldü", "ölmüş", "ölü", "vefat", "rahmetli", "merhum", "cenaze", "mezar", "toprağa",
    "beyaz", "siyah", "kırmızı", "mavi", "yeşil", "sarı", "mor", "kahverengi", "gri", "pembe", "turuncu", "ela", "lacivert",
    "pazartesi", "salı", "çarşamba", "perşembe", "cuma", "cumartesi",
    "ocak", "şubat", "mart", "nisan", "mayıs", "haziran", "temmuz", "ağustos", "eylül", "ekim", "kasım", "aralık",
]
WEAK_TR = [
    "sene", "yıl", "kış", "bahar", "sonbahar", "sabah", "akşam", "gece", "öğle", "ezan", "güneş",
    "anne", "baba", "abla", "ağabey", "kardeş", "oğl", "karısı", "kocası", "dede", "nine", "teyze", "amca", "dayı", "hala",
    "yirmi", "otuz", "kırk", "elli", "altmış", "yetmiş", "seksen", "doksan",
]
DEATH_TR = ["öldü", "ölmüş", "ölümü", "ölümünden", "vefat", "rahmetli", "merhum", "cenaze", "toprağa ver", "kaybettik"]
KIN_TR = ["anne", "baba", "abla", "ağabey", "kardeş", "oğl", "karısı", "kocası", "dede", "nine", "teyze", "amca", "dayı", "hala"]


def _words(stems):
    return re.compile("|".join(rf"(?:^|[\W\d_]){re.escape(w)}" for w in stems), re.I)


STRONG = _words(STRONG_TR)
WEAK = _words(WEAK_TR)
DEATH = _words(DEATH_TR)
DIGIT = re.compile(r"\d")


def sentences(text):
    parts = re.split(r"(?<=[.!?…])\s+|\n+", text.replace("\r", ""))
    return [s.strip() for s in parts if len(s.strip()) > 1 and not s.strip().startswith("#")]


def _is_name(word):
    return len(word) >= 3 and word.isalpha() and word[0].isupper() and word[1:].islower()


def names(sentence):
    """Capitalised words that are not sentence openers, without a possessive or case suffix."""
    out = []
    # Dialogue dashes and opening quotes are not words: the opener is the first token with a letter.
    tokens = sentence.split()
    while tokens and not re.search(r"[^\W\d_]", tokens[0]):
        tokens = tokens[1:]
    for i, w in enumerate(tokens):
        clean = re.sub(r"^[«“\"‘(—–-]+", "", w)
        clean = re.sub(r"[’'][^\W\d_]*$", "", clean)
        clean = re.sub(r"[\W\d_]+$", "", clean)
        # A sentence opener counts only with an apostrophe suffix, which marks a name.
        if i == 0 and not re.search(r"[’']", w):
            continue
        if _is_name(clean):
            out.append(clean)
    return out


def _window(s):
    """A long sentence is cut to forty words around its first fact; the cut is still an exact quote."""
    w = s.split()
    if len(w) <= 60:
        return s
    at = next(
        (i for i, x in enumerate(w) if STRONG.search(" " + x) or DIGIT.search(x) or WEAK.search(" " + x)),
        0,
    )
    return " ".join(w[max(0, at - 20) : at + 20])


def fact_lines(units, max_words=9000):
    """units: [{"id": "c1", "body": "..."}]"""
    lines, total = [], 0
    for u in units:
        for s in sentences(u["body"]):
            strong = STRONG.search(s) or DIGIT.search(s)
            if not strong and not (names(s) and WEAK.search(s)):
                continue
            line = _window(s)
            n = len(line.split())
            if total + n > max_words:
                return lines
            lines.append({"unit": u["id"], "sentence": line})
            total += n
    return lines


def _one_apart(a, b):
    if a == b or abs(len(a) - len(b)) > 1:
        return False
    i = 0
    while i < len(a) and i < len(b) and a[i] == b[i]:
        i += 1
    j = 0
    while j < len(a) - i and j < len(b) - i and a[len(a) - 1 - j] == b[len(b) - 1 - j]:
        j += 1
    return len(a) - i - j <= 1 and len(b) - i - j <= 1


def name_variants(units):
    count, where, order = {}, {}, []
    for u in units:
        for s in sentences(u["body"]):
            for n in dict.fromkeys(names(s)):
                if n not in count:
                    order.append(n)
                count[n] = count.get(n, 0) + 1
                where.setdefault(n, []).append({"unit": u["id"], "sentence": s})
    out = []
    for rare in order:
        rc = count[rare]
        if rc > 2 or len(rare) < 4:
            continue
        for common in order:
            cc = count[common]
            # A trailing extra letter is a case ending (Nihale, Beşiri), not another name.
            if cc >= 4 and len(common) >= 4 and _one_apart(rare, common) and not rare.startswith(common):
                out.append(
                    {
                        "rare": rare,
                        "common": common,
                        "rare_count": rc,
                        "common_count": cc,
                        "sentences": where[rare] + where[common][:1],
                    }
                )
    return out


def life_checks(units, per_death=6, total=40):
    """After a sentence stating a death, later sentences that bring the same person back: the dead
    person's name, or a family word from the death sentence with a name from its paragraph."""
    all_lines, paragraph = [], 0
    for u in units:
        for block in re.split(r"\n\s*\n", u["body"]):
            paragraph += 1
            for s in sentences(block):
                all_lines.append(({"unit": u["id"], "sentence": _window(s)}, paragraph))
    out, used = [], 0
    for i, (line, p) in enumerate(all_lines):
        if not DEATH.search(line["sentence"]) or used >= total:
            continue
        kin = [k for k in KIN_TR if _words([k]).search(line["sentence"])]
        dead = names(line["sentence"])
        owners = {n for x, q in all_lines if q == p for n in names(x["sentence"])}
        if not kin and not dead:
            continue
        later = []
        for x, _ in all_lines[i + 1 :]:
            if len(later) >= per_death:
                break
            s = x["sentence"]
            if DEATH.search(s):
                continue
            ns = names(s)
            by_name = any(n in ns for n in dead)
            by_kin = any(_words([k]).search(s) for k in kin) and any(n in owners for n in ns)
            if by_name or by_kin:
                later.append(x)
        if later:
            out.append({"death": line, "later": later})
            used += len(later)
    return out
