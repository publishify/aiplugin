# Installation

Plugin version 0.1.9, 19 November 2026. The board server for every app is `https://mcp.publishify.app`; you sign in once with Google or an e-mail code.

| App | How | State |
| --- | --- | --- |
| Claude Code and the Claude desktop app | Plugin marketplace | Ready; full board tested |
| Codex | Plugin marketplace | Installs; no forms or windows yet |
| ChatGPT | Custom connector | Sign-in, form and window tested on 15 Nov; full board not yet |
| Gemini CLI | Extension | Not yet tested |

## Claude Code and the Claude desktop app

```text
/plugin marketplace add publishify/plugin
/plugin install publishify@publishify
```

From a terminal: `claude plugin marketplace add publishify/plugin`, then `claude plugin install publishify@publishify`. To update: `claude plugin marketplace update publishify`, then `claude plugin update publishify@publishify`, and restart Claude.

Then add your manuscript (DOCX, EPUB, Markdown or TXT) and run `/publishify:review`, or say "Review this with Publishify".

## Codex

```sh
codex plugin marketplace add publishify/plugin
codex plugin add publishify
```

Codex installs the same package. It has no forms or windows: answer the board's questions in chat, and approve the tool calls Codex asks about.

## ChatGPT

1. Settings → Apps (Connectors) → turn on developer mode → **Create** a custom connector.
2. Name: Publishify. URL: `https://mcp.publishify.app`. Authentication: OAuth.
3. In a chat, turn on the Publishify connector, attach your manuscript, and ask ChatGPT to review it with Publishify.

The connector brings the form and the role cards. The scripts (quotation checks, dashboard) are in this repository's `skills/publishify/scripts/`; until a ChatGPT package is ready, attach them to the chat with your manuscript.

## Gemini CLI

```sh
gemini extensions install https://github.com/publishify/plugin
```

The extension (`gemini-extension.json`) adds the Publishify server and the board's instructions (`GEMINI.md`). Not yet tested end to end.

## What you need

- An AI app that can run Python 3 for the scripts (nothing else to install).
- A Publishify account. Three previews a month are free; the full board uses one review from your plan. [Pricing](https://publishify.app/pricing/)
