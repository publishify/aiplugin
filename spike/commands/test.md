---
description: Run the Publishify capability checks on an attached or named file (test only).
argument-hint: <file>
---

The user wrote: $ARGUMENTS

Run these checks in order and report each as worked, failed or not available. Never send text from the file to any tool.

1. Call the `whoami` tool of the publishify-spike server.
2. Call `ask_form`. If a form appears, the user fills it in.
3. Call `show_window`. Ask the user whether a Publishify window appeared and whether its button worked.
4. Call `start_board` and keep the `session` it returns.
5. Use the `word-count` skill on the file: run `scripts/count_words.py`, and if Node.js is available also `scripts/count_words.mjs`.
6. For each script that ran, call `report_counts` with the session, the app name, the language, and the numbers it printed.
7. Finish with a short table: check, result.
