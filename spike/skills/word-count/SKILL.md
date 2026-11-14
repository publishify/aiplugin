---
name: word-count
description: Count the words and characters of a document the user attached (txt, md, docx). Used by the Publishify capability checks.
---

Find the attached file. In Claude's code environment uploaded files are usually under `/mnt/user-data/uploads/`; on the user's computer use the path they gave.

Run the Python script first:

```bash
python3 scripts/count_words.py "<file>"
```

If Node.js is available, also run:

```bash
node scripts/count_words.mjs "<file>"
```

Each prints one line of JSON: `{"language": ..., "words": ..., "characters": ...}`. Report those numbers only. Never quote or send text from the file.
