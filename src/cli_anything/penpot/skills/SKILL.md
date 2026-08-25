---
name: "cli-anything-penpot"
description: "Control Penpot through its authenticated JSON RPC API from macOS shells and AI agents."
---

# CLI-Anything Penpot

## Install

Development: `python3 -m pip install -e .`
Homebrew (after publishing the tap): `brew install alvaroum/tap/cli-anything-penpot`

The executable is `cli-anything-penpot`; `penpot` is an equivalent alias.

## Authentication

On the first authenticated command, the CLI prompts for a server address and Penpot access token and stores them in `~/.config/penpot-cli/config.json` with owner-only permissions. The token is never shown by `config show`.

For automation, avoid prompts:

```sh
PENPOT_SERVER=https://design.penpot.app PENPOT_TOKEN="$PENPOT_TOKEN" cli-anything-penpot --json status
```

`PENPOT_CONFIG=/path/to/config.json` selects another config file. `PENPOT_SERVER` and `PENPOT_TOKEN` must be supplied together.

Penpot access tokens use `Authorization: Token <token>`. The client sends JSON POST requests to `/api/main/methods/<method>`.

## Command contract

Use `--json` before a command or after a leaf command. JSON is the stable interface for agents; stdout contains only the result. Errors go to stderr and exit non-zero.

```sh
cli-anything-penpot --json status
cli-anything-penpot --json teams list
cli-anything-penpot --json projects list --team-id TEAM_UUID
cli-anything-penpot --json files list --project-id PROJECT_UUID
cli-anything-penpot --json file page --file-id FILE_UUID --page-id PAGE_UUID
cli-anything-penpot --json file thumbnail-data --file-id FILE_UUID
```

The default output is pretty JSON for API-shaped results. Do not parse human labels; use `--json`.

## Direct API escape hatch

The API is broad and evolves. Call any documented method without waiting for a dedicated wrapper:

```sh
cli-anything-penpot --json api call get-file --data '{"id":"FILE_UUID"}'
```

`METHOD` is a method name, not a URL. `--data` must be a JSON object. The CLI always uses POST, matching the OpenAPI reference.

## Verified OpenAPI methods

- `verify-token`: token in request body; used by the API contract, not the default status command.
- `get-profile`: `{}` → profile; used by `status`.
- `get-owned-teams`: `{}` → owned teams; used by `teams list`.
- `get-projects`: `{"teamId": "..."}`; used by `projects list`.
- `get-project-files`: `{"projectId": "..."}`; used by `files list`.
- `get-page`: `fileId`, optional `pageId`, optional `objectId`; object retrieval requires page ID.
- `get-file-data-for-thumbnail`: `fileId`; used by `file thumbnail-data`.

The rendered docs contain additional methods absent from the current OpenAPI file (for example `get-file`). Use `api call` for those and check the server’s own versioned documentation.

## REPL

Running with no command opens the state-free interactive REPL. Type `help`, then enter the same subcommands without the executable name. REPL output is intended for humans; add `--json` to individual commands for machine parsing.

## Failure handling

- Missing setup: run `config init` or set both environment variables.
- HTTP 401/403: refresh the Penpot access token and retry.
- HTTP 404: check the server URL and method name against its API docs.
- Transport errors: verify network access and the server address.
- Invalid IDs and request bodies are reported before or by the Penpot API; no silent fallback occurs.

## Source of truth

API contract: <https://design.penpot.app/api/main/doc/openapi.json>
Rendered reference: <https://design.penpot.app/api/main/doc>
