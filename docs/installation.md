# Installation

The first release is for **Claude**: Claude Code and the Claude desktop app with plugins. Version 0.1.7, 18 November 2026.

## Claude Code and the Claude desktop app

```text
/plugin marketplace add publishify/plugin
/plugin install publishify@publishify
```

From a terminal, the same with the `claude` command:

```sh
claude plugin marketplace add publishify/plugin
claude plugin install publishify@publishify
```

To update later: `claude plugin marketplace update publishify`, then `claude plugin update publishify@publishify`, and restart Claude.

The plugin adds the Publishify connector (`https://mcp.publishify.app`), two commands (`/publishify:review`, `/publishify:status`) and the board's skills and scripts.

## First run

1. Add your manuscript (DOCX, EPUB, Markdown or TXT) and run `/publishify:review`, or say "Review this with Publishify".
2. Sign in to Publishify when asked: Google or a code sent to your e-mail.
3. Answer the form in your own language: what you wrote, what you would like, and the questions for your work.
4. The board reads in turn. When it finishes, you get `publishify-work/dashboard.html`.

## What you need

- Claude with plugins and code execution (the scripts need Python 3; nothing else to install).
- A Publishify account. Three previews a month are free; the full board uses one review from your plan. [Pricing](https://publishify.app/pricing/)

## Other AI applications

ChatGPT, Codex, Cursor and Gemini are on the roadmap. Codex can install the same package (`codex plugin marketplace add publishify/plugin`), but forms and windows are not available there yet. [Status](status.md)

The old name `publishify/aiplugin` still redirects to this repository; use `publishify/plugin`.
