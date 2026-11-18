# Installation

Plugin version 0.1.9, 19 November 2026. The board server for every app is `https://mcp.publishify.app`; you sign in once with Google or an e-mail code.

| App | How | State |
| --- | --- | --- |
| Claude Code and the Claude desktop app | Plugin marketplace | Ready; full board tested |
| Codex | Plugin marketplace | Installs; no forms or windows yet |
| ChatGPT | Custom connector | Sign-in, form and window tested on 15 Nov; full board not yet |
| Gemini CLI (terminal) | Extension | Installs; server and both skills are picked up (19 Nov); full board not yet |
| Gemini web and mobile app | Not possible | Accepts only Google's own integrations |

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
codex plugin add publishify@publishify
```

Check: Codex should report `publishify@publishify` with the current version (0.1.9 or later). Codex installs the same package as Claude. It has no forms or windows: answer the board's questions in chat, and approve the tool calls Codex asks about.

## ChatGPT

1. ChatGPT desktop or web → **Customize → Plugins → Add**.
2. Name: `publishify`. Connection: **Server URL** `https://mcp.publishify.app`. Authentication: **OAuth**.
3. Tick **I understand and want to continue**, then **Create as a plugin**.
4. **Connect publishify** and sign in (Google or an e-mail code). The plugin page should then show your connected account and the URL `https://mcp.publishify.app`.
5. In a new chat, choose Publishify with **+**, attach your manuscript, and ask ChatGPT to review it with Publishify.

The connector brings the form and the role cards. The scripts (quotation checks, dashboard) are in this repository's `skills/publishify/scripts/`; until a ChatGPT package is ready, attach them to the chat with your manuscript.

## Gemini CLI

Gemini CLI is Google's terminal tool. It needs Node.js 20 or later.

```sh
npm install -g @google/gemini-cli
gemini extensions install https://github.com/publishify/plugin
```

Answer `y` when it asks to continue. Check:

```sh
gemini extensions list
```

You should see `publishify (0.1.9)` or later, with the MCP server `publishify` and the agent skills `publishify` and `publishify-fiction`. Then sign in to Publishify **inside** Gemini CLI (these are not shell commands):

1. Run `gemini` in the terminal. Gemini's own prompt opens.
2. At that prompt, type `/mcp auth publishify`. Publishify's sign-in page opens in the browser; continue with Google or an e-mail code.
3. Still at Gemini's prompt, add your manuscript with `@` and ask for a review, for example: `@~/Desktop/my-book.docx Review this with Publishify, a preview is enough.`

The first time, Gemini also asks you to sign in to Google for Gemini itself ("Gemini Code Assist and Gemini CLI"); that is separate from the Publishify sign-in. Type `/quit` to leave Gemini.

The `npm warn` lines about `keytar` and `install-scripts` during the install are harmless.

The Gemini web and mobile app (gemini.google.com) does not accept third-party extensions or MCP servers, so Publishify cannot be added there.

## If something goes wrong

**"publishify is already registered from a different source"** (Claude or Codex). An older Publishify marketplace (the retired Masthead or test package) is still registered under the same name. Remove it, then add the current one:

```sh
# Claude
claude plugin marketplace remove publishify
claude plugin marketplace add publishify/plugin
claude plugin install publishify@publishify

# Codex
codex plugin marketplace remove publishify
codex plugin marketplace add publishify/plugin
codex plugin add publishify@publishify
```

**It installed `masthead` (version 0.1.x).** That is the retired Masthead plugin from the old marketplace. Remove it (`claude plugin uninstall masthead@publishify` or `codex plugin remove masthead@publishify`), then run the commands above.

**`publishify/aiplugin`.** The old address still redirects here, but always use `publishify/plugin`.

**The connector asks to sign in again.** Sign in with the same Google account or e-mail as before; your licence belongs to that e-mail.

## What you need

- An AI app that can run Python 3 for the scripts (nothing else to install).
- A Publishify account. Three previews a month are free; the full board uses one review from your plan. [Pricing](https://publishify.app/pricing/)
