# Test plan

## Test inventory

- `test_core.py`: 8 unit tests for configuration and HTTP behavior.
- `test_integration.py`: 5 mocked HTTP/CLI workflow tests; deterministic and external-service-free.
- `test_full_e2e.py`: 1 credential-gated live Penpot workflow; ordinary runs skip it unless credentials are supplied.

## Unit coverage

### `config.py`

- Normalize bare hosts, trailing slashes, and an already-specified RPC path.
- Reject empty and non-HTTP(S) servers.
- Load valid JSON and reject missing, malformed, and empty-token configuration.
- Environment overrides require both variables.
- Save owner-only configuration permissions.

### `api.py`

- POST JSON body and `Authorization: Token` header.
- Verify-token sends its required token body without relying on a header.
- Decode JSON responses and convert HTTP failures to actionable `ApiError` values.

## CLI and integration coverage

- `--help` and `--version` work through the installed entry point.
- `config show` redacts credentials.
- `status`, teams, projects, files, and page commands map to documented RPC methods.
- `--json` emits parseable stdout.
- Missing setup fails clearly in non-interactive mode.
- The direct API command accepts JSON objects and rejects invalid JSON and URL paths.
- The default REPL asks for first-run setup and exits with `quit`.

## Live backend workflow

`test_full_e2e.py` invokes the installed `cli-anything-penpot` command with `CLI_ANYTHING_FORCE_INSTALLED=1`, `PENPOT_SERVER`, and `PENPOT_TOKEN`. It runs `status` and `teams list`, validates JSON, and fails clearly when supplied credentials cannot reach the backend. No credentials are stored in CI.

## Realistic workflows

1. **Inspect a Penpot workspace**: configure credentials, call `status`, list owned teams, list a team’s projects, list project files, retrieve a file page.
2. **Use an evolving API**: call a rendered-doc-only method through `api call` while preserving the exact JSON response for an agent.

## Test results

Command: `python3 -m compileall -q src && PYTHONPATH=src python3 -m unittest discover -s tests -v`

```text
Ran 14 tests in 0.542s

OK (skipped=1)
```

The one skip is the live backend workflow, which requires user-provided `PENPOT_SERVER` and `PENPOT_TOKEN`. The mocked HTTP workflow exercises the same command mappings without exposing credentials.
