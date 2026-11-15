<div align="center">

# Publishify

### Your AI Editorial Board

**Write wherever you choose. Bring a board to your manuscript.**

[Website](https://publishify.app/) · [Türkçe README](README.tr.md) · [How it works](docs/architecture.md) · [Current status](docs/status.md)

![Stage: F1 development](https://img.shields.io/badge/stage-F1_development-7fb671)
![First desk: Fiction](https://img.shields.io/badge/first_desk-Fiction-a9cf9c)
![First host: Claude](https://img.shields.io/badge/first_host-Claude-7fb671)

</div>

<p align="center"><img src="docs/assets/editorial-board-en.png" width="680" alt="Illustrative Publishify agent office and Seven Stages narrative map"></p>
<p align="center"><em>A visual explanation of the intended board, not a real review or a benchmark result.</em></p>

Publishify is a comprehensive **AI editorial board plugin**. It brings an Editor, a Continuity Auditor and a simulated Reader Panel into the AI application you already use, then organises their findings into an evidence-linked dashboard and downloadable report.

Your writing tool stays your choice. Your manuscript is processed in your AI environment. The final editorial decision stays with you.

> **Status — 15 November 2026:** The product is being built. **F1 starts with the Fiction desk for Claude.** This repository currently contains the completed technical spike under `spike/`; the spike server has been retired. Production installation and full-book evaluation are not available yet. Do not use the old spike installation commands as a product setup guide.

## A board with defined work

| Role | What it examines | What it should return |
| --- | --- | --- |
| **Editor** | Chapter structure, pace, viewpoint, character behaviour and strengths | Source-linked observations, reasons and editorial questions |
| **Continuity Auditor** | Names, dates, ages, events and candidate inconsistencies from the fact ledger | A reasoned finding with both relevant source locations |
| **Reader Panel** | Curiosity, clarity, emotional response and reader expectations | Clearly labelled simulated reader perspectives |

Python scripts handle measurable work: parsing files, splitting chapters, counting, locating quotations and extracting candidates for review. The AI interprets context. A matching quotation makes a note inspectable; it does not make its interpretation infallible.

[Explore the Fiction desk →](docs/fiction-desk.md)

## From manuscript to dashboard

1. **Connect the plugin.** Authorise your Publishify account and choose the review scope when the product is released.
2. **Attach the manuscript in your AI application.** File-processing scripts run in that AI environment.
3. **Run the board.** The MCP service provides the desk, role cards and next assignment; your own AI carries out the reading.
4. **Inspect the evidence.** Check quotations and compare passages rather than relying on a general verdict.
5. **Open the report.** Structured results become a dashboard and downloadable output inside the AI environment.

The board advises; it does not automatically rewrite your manuscript.

## What runs where?

| Your AI environment | Publishify MCP service |
| --- | --- |
| Manuscript file and extracted full text | Sign-in and account identity |
| Reading agents and model usage | Email-linked licences and usage allowances |
| Python parsing, counting and quotation checks | Session and task coordination |
| Contextual interpretation | Versioned desk catalogue and role cards |
| Dashboard and report generation | Validation of submitted tool results |

**The manuscript file and extracted full text are not uploaded to Publishify.** Submitted results can contain short quotations. The AI provider still processes your attachment under its own terms. Publishify does not run the reading model on its server or offer a persistent server-side manuscript/report archive.

[Architecture and data boundaries →](docs/architecture.md) · [Privacy →](docs/privacy.md)

## Installation

**There is no production installation recipe yet.** The repository still exposes a test marketplace and retired spike code; installing that package will not start a production review.

F1 is preparing a plugin package for Claude with these planned commands:

```text
/publishify:review
/publishify:status
```

Command syntax, sign-in and UI capabilities depend on the host. The release guide will replace this section after the real package, OAuth service and Fiction quality evaluation pass acceptance checks. [Installation and prerequisites →](docs/installation.md)

## What has actually been tested?

Founder-recorded technical trials on **15 November 2026** used a small sample file and the spike server. They checked transport, UI and execution — not novel-reading quality.

| Host | Observed in the trial | Still unverified or limited |
| --- | --- | --- |
| **Claude web** | Sign-in, form, window/button, scripts on an attached sample | Visual confirmation of the cloud upload path; full product review |
| **Claude desktop** | Plugin package, connection, UI and scripts | Initial file trial ran on the Mac, not a cloud attachment |
| **Claude Code — desktop Code tab** | Commands, connection and scripts | Form did not render; window button failed; terminal is a separate test |
| **ChatGPT Plus** | Custom OAuth MCP, form, window/button, attached Python script | Packaged-skill installation; Free/Pro plan behaviour |
| **Codex CLI** | Unmodified Claude package installed; OAuth and scripts | Forms/inline windows absent; state-changing tools required approval |

Cursor and Gemini CLI were not tested. Real separate-context subagents were not tested. These observations are not universal availability guarantees. [Evidence and acceptance criteria →](docs/status.md)

## The first release, without the guesswork

- **Desk:** Fiction, for novels and stories; Claude first.
- **Inputs being prepared:** DOCX, EPUB, Markdown and TXT. PDF is a report output, not a promised F1 manuscript input.
- **Narrative lens:** Ali Osman Akçaoğlu’s *Wayfarer’s Seven Stages* — a map, not a mandatory plot formula.
- **Pricing:** Not announced. Limited one-off, monthly and yearly licences and three free preliminary reviews per month are planned; limits and re-review allowances must be stated before sales open.
- **AI usage:** Runs through the user's AI account, under that provider's limits. Publishify's service licence is separate.

[Read the F1 roadmap →](docs/roadmap.md)

## More desks, when they are ready

The wider product plan covers **Books, Publication Preparation, Students, Academic, and Business/Institutions**. These are roadmap groups, not completed products. The first build does not promise all desks at launch. Contracts, patents and medical texts are outside the defined scope.

## Repository map

```text
.claude-plugin/marketplace.json   Existing test marketplace; not the product release
spike/                          Retired technical trial, preserved as history
README.md                       English introduction
README.tr.md                    Türkçe tanıtım
docs/architecture.md            Responsibility and data boundaries
docs/fiction-desk.md            First desk: roles, evidence and outputs
docs/installation.md            Prerequisites and installation status
docs/status.md                  What the trials establish — and do not
docs/roadmap.md                 F1 scope and release gates
docs/privacy.md                 Manuscript handling and service data
docs/contributing.md            Documentation and contribution guidelines
docs/assets/                    Website board artwork, PNG and SVG, EN/TR
```

## Contribute and follow

Start with [contributing](docs/contributing.md). Keep technical-spike history separate from product code. Do not submit manuscripts, personal information, credentials or private server implementation in public issues.

- [Public website source](https://github.com/publishify/publishify)
- [English website](https://publishify.app/) · [Türkçe site](https://publishify.app/tr/)
- [Seven Stages guide](https://publishify.app/blog/the-wayfarers-seven-stages/)
- [Contact](mailto:info@publishify.app)

No open-source software licence has been selected in this repository. Public visibility alone does not grant a licence to reuse the code, brand or artwork. Do not describe this project as MIT-licensed unless an actual licence is added.
