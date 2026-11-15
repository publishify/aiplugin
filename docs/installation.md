# Installation status

**Production installation is not released.** Do not install the retired spike expecting a live editorial board.

## Current repository

The root marketplace is still called `publishify-test` and points to `publishify-spike` in `spike/`. Its server was removed after technical validation. These files are preserved as trial history. This documentation change does not rename the marketplace or implement the product.

## F1 target

A Publishify plugin package for Claude, a Publishify sign-in, a Fiction desk selection and an attachment processed in the AI host. Planned commands are `/publishify:review` and `/publishify:status`; exact host-specific syntax will be verified before release.

## Prerequisites to state at release

- A supported AI application and account with the required plugin, connector and execution capabilities.
- Access to the host's code-execution environment for the bundled Python scripts.
- A Publishify account and any required review allowance.
- For CLI clients: the client's own runtime requirements. Do not impose local Node.js, Python or `claude -p` on cloud-chat users without an actual requirement.

Host availability depends on client version, account and permissions. Do not infer plan eligibility from one account's trial or confuse web, desktop and CLI capabilities.

The production endpoint will only be documented as usable after it has been deployed and tested. No credential or private server implementation belongs in this public repository.
