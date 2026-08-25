# CLI-Anything Penpot

A lightweight macOS-first command-line interface for Penpot’s authenticated HTTP API. It uses Python’s standard HTTP client and Click for a small, scriptable command surface.

## Install from source

```sh
python3 -m pip install -e .
cli-anything-penpot --help
```

The `penpot` command is an alias. Homebrew packaging instructions are in [`docs/homebrew.md`](docs/homebrew.md).

## First run

```sh
cli-anything-penpot config init
```

The CLI asks for the Penpot server address and access token. It stores only the server and token in `~/.config/penpot-cli/config.json` and applies owner-only permissions. For automation, use `PENPOT_SERVER` and `PENPOT_TOKEN` instead.

## Common commands

```sh
cli-anything-penpot --json status
cli-anything-penpot --json teams list
cli-anything-penpot --json projects list --team-id TEAM_UUID
cli-anything-penpot --json files list --project-id PROJECT_UUID
cli-anything-penpot --json file page --file-id FILE_UUID --page-id PAGE_UUID
cli-anything-penpot --json api call get-file --data '{"id":"FILE_UUID"}'
```

Use JSON output for agents and scripts. Errors are written to stderr with a non-zero exit code. Running without a command opens the interactive REPL.

## API boundary

Penpot’s MAIN API is JSON RPC: every operation is a POST to `/api/main/methods/<method>`. Access tokens use `Authorization: Token <token>`. The initial wrappers use methods present in the current OpenAPI reference; `api call` covers the rest without pretending undocumented schemas are stable.

- [OpenAPI reference](https://design.penpot.app/api/main/doc/openapi.json)
- [Rendered API reference](https://design.penpot.app/api/main/doc)
- [AI skill guide](skills/cli-anything-penpot/SKILL.md)
- [Package skill copy](src/cli_anything/penpot/skills/SKILL.md)

## Development

```sh
python3 -m pip install -e .
python3 -m unittest discover -s tests -v
```

No live Penpot token is required by the test suite. Never commit credentials.
