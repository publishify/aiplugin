---
name: publishify-fiction
description: The Fiction desk of Publishify, for novels, novellas and story collections. Use with the publishify skill when the person wants editorial notes on fiction.
---

# Fiction desk

Run the board with the **publishify** skill; this page adds what is particular to fiction.

- **Who reads:** the editor, the continuity checker, a panel of three readers, then the editor-in-chief. A preview is the editor alone.
- **What to add with +:** the novel or story file (docx, epub, md or txt). For a book in a series, the earlier books can be added too; the continuity checker will compare against them.
- **Form answers:** what it is (novel, novella, short stories), the genre, and whether it is part of a series. Pass the first as `--form` to `board.py prepare`.
- **Continuity:** `facts.json` lists fact sentences, name variants (a rare name one letter from a frequent one) and life checks (a dead person appearing later). They are candidates, not findings: check each one in the work. A memory, a dream, a grave or mourning is not a contradiction.
- **Seven Stages:** on a full board the editor maps the book onto the Wayfarer's Seven Stages: Call, Guide, Threshold, Trial, Awakening, Reward, Return. It is a lens, not a score; an absent stage is not a fault.
- **Never:** rewrite the author's sentences, promise publication, or say whether the book is good enough.
