"""Counts words and characters of a txt, md or docx file. Prints one JSON line, no text from the file."""
import json
import re
import sys
import zipfile
from xml.etree import ElementTree


def read_text(path: str) -> str:
    if path.lower().endswith(".docx"):
        with zipfile.ZipFile(path) as z:
            root = ElementTree.fromstring(z.read("word/document.xml"))
        ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        return "\n".join("".join(t.text or "" for t in p.iter(ns + "t")) for p in root.iter(ns + "p"))
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


text = read_text(sys.argv[1])
print(json.dumps({"language": "python", "words": len(re.findall(r"\w+", text)), "characters": len(text)}))
