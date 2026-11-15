---
name: publishify
description: Run a Publishify editorial board on a manuscript the person added. Use when they ask Publishify to review, read, assess or give editorial notes on their book, story or other document, or run /publishify:review.
---

# Publishify editorial board

Publishify is an editorial board that runs in this AI. The Publishify server (the `publishify` connector) holds the person's sign-in, licence, the desk catalogue and the role cards. The work itself never goes to Publishify: you read it here, and the scripts in `scripts/` run here. Never put text from the work into a Publishify tool; tools take ids, choices and numbers only.

Speak to the person in their language throughout, and pass their language as a BCP 47 tag (`en`, `tr`, `fa`, `pt-BR`…) to every Publishify tool.

## 1. The form

1. Call `get_form` with the person's language.
   - If it answers `needs_translation`, translate every string it sent into that language as a publishing professional would, keep the keys and any `{n}`, and call `get_form` again with `translations`. Do not show the list to the person.
2. Let the person choose; never choose for them.
   - If a Publishify window appears, wait for their choice from it.
   - Otherwise call `fill_form`, which asks with a plain form.
   - If that is not supported, ask in chat, one step at a time, showing each question's example answer: what they wrote (the work), what they would like (board review and its mode; topics for a focused review), then the work's own questions.
3. Locked options need Pro or have used this month's free previews. If the form's `account.licensed` is false, tell them they are on the free plan (3 previews a month) and that Pro opens from `buy_url` with their e-mail filled in, so it unlocks here once they pay. Do not work around a lock.

## 2. The file

- In a chat app the person adds the file with **+**. Find the attached file in your code environment (for example under `/mnt/user-data/uploads/`). On a computer, use the path they gave.
- Supported: docx, epub, md, txt. For anything else, ask for one of those.
- If no file is attached yet, ask for it and wait.

## 3. Start

1. A full board or focused review uses one review from the person's licence; a preview is free. Tell them which before starting, and start only when they agree.
2. Call `start_board` with the confirmed work (`desk`), `service`, answers, mode, topics and language. Keep the `session` id. If a board stopped earlier, pass `session` to resume it; that never charges again.
3. Prepare the work (Python 3, no packages needed):

```
python3 <this skill's folder>/scripts/board.py prepare "<file>" --form <novel|novella|stories> --work publishify-work
```

It splits the work into chapters and paragraphs with ids like `c3p12`, and writes `units.json`, `measure.json` and `facts.json` into `publishify-work/`. Use those ids as note locations.

## 4. The roles

Repeat until `next_task` says `done`:

1. Call `next_task` with the session. It returns one role's card.
2. Play that role on the work exactly as the card says, reading `units.json` (the continuity checker also reads `facts.json`; the editor also reads `measure.json`). If this app can run a separate agent or task, give each role, and each reader of the reader panel, its own, so they do not influence each other.
3. Save the role's JSON notes to `publishify-work/<role>.json`, then check its quotes:

```
python3 <this skill's folder>/scripts/board.py check publishify-work/<role>.json --work publishify-work
```

Notes whose quote is not in the work are dropped. Never repair a quote by guessing.

For the editor-in-chief, first merge every role's checked notes, then do what its card says with `publishify-work/merged.json`:

```
python3 <this skill's folder>/scripts/board.py merge publishify-work/*.checked.json --work publishify-work
```

## 5. Finish

1. Call `finish_board` with the session.
2. Show the person the result: the editor-in-chief's summary, then the notes in order, each with its quote and location, grouped by topic; then, if the editor mapped them, the stages under the title "The Wayfarer's Seven Stages (Hero's Journey template)" in the person's language (Turkish: "Yolcunun Yedi Merhalesi (Kahramanın Yolculuğu Şablonu)"). Offer the notes as a file to download.
3. Say that the notes come from an AI and can be wrong, and that the board does not rewrite the work or give a verdict.

If anything fails, tell the person what happened in plain words and what they can do; the session can be resumed later with its id.
