"""Click command line and REPL interface for Penpot."""

from __future__ import annotations

import json
import shlex
import sys
from pathlib import Path
from typing import Any

import click

from .api import ApiError, PenpotApi
from .config import Config, ConfigError, default_config_path, load_config, normalize_server, prompt_config, save_config
from .utils.repl_skin import ReplSkin

VERSION = "0.1.0"


def _emit(ctx: click.Context, value: Any, local_json: bool = False) -> None:
    if ctx.obj.get("json") or local_json:
        click.echo(json.dumps(value, indent=2, default=str))
    elif isinstance(value, (dict, list)):
        click.echo(json.dumps(value, indent=2, default=str))
    else:
        click.echo(value)


def _config(ctx: click.Context) -> Config:
    try:
        return load_config()
    except ConfigError as exc:
        if ctx.obj.get("from_repl") or not sys.stdin.isatty():
            raise click.ClickException(f"{exc}. Run 'cli-anything-penpot config init' or set PENPOT_SERVER and PENPOT_TOKEN.") from exc
        config = prompt_config()
        path = save_config(config)
        click.echo(f"Saved configuration to {path}", err=True)
        return config


def _api(ctx: click.Context) -> PenpotApi:
    return PenpotApi(_config(ctx), timeout=ctx.obj.get("timeout", 30.0))


def _json_option(function):
    return click.option("--json", "local_json", is_flag=True, help="Emit machine-readable JSON.")(function)


@click.group(invoke_without_command=True)
@click.version_option(VERSION, prog_name="cli-anything-penpot")
@click.option("--json", "json_output", is_flag=True, help="Emit machine-readable JSON.")
@click.option("--timeout", type=click.FloatRange(min=1), default=30.0, show_default=True, help="HTTP timeout in seconds.")
@click.pass_context
def cli(ctx: click.Context, json_output: bool, timeout: float) -> None:
    """Control Penpot through its authenticated HTTP API."""
    ctx.ensure_object(dict)
    ctx.obj.update(json=json_output, timeout=timeout)
    if ctx.invoked_subcommand is None:
        _run_repl(ctx)


@cli.group()
def config() -> None:
    """Create, inspect, and manage local credentials."""


@config.command("init")
@_json_option
def config_init(local_json: bool) -> None:
    """Prompt for the server and access token, then save them securely."""
    value = prompt_config()
    path = save_config(value)
    result = {"saved": str(path), "server": value.server}
    click.echo(json.dumps(result, indent=2) if local_json else f"Saved configuration to {path}")


@config.command("show")
@_json_option
def config_show(local_json: bool) -> None:
    """Show the configured server without revealing the token."""
    path = default_config_path()
    try:
        value = load_config(path)
    except ConfigError:
        result = {"configured": False, "path": str(path)}
    else:
        result = {"configured": True, "path": str(path), "server": value.server, "token": "<redacted>"}
    if local_json:
        click.echo(json.dumps(result, indent=2))
    elif not result["configured"]:
        click.echo(f"Not configured ({path})")
    else:
        click.echo(f"Server: {result['server']}\nToken: <redacted>\nPath: {result['path']}")


@config.command("set")
@click.option("--server", required=True, help="Penpot server URL.")
@click.option("--token", required=True, help="Penpot access token.")
@_json_option
def config_set(server: str, token: str, local_json: bool) -> None:
    """Set credentials without putting them in shell history when possible."""
    value = Config(normalize_server(server), token)
    path = save_config(value)
    result = {"saved": str(path), "server": value.server}
    click.echo(json.dumps(result, indent=2) if local_json else f"Saved configuration to {path}")


@cli.command()
@_json_option
def status(local_json: bool) -> None:
    """Validate the token and return the authenticated profile."""
    profile = _api(click.get_current_context()).profile()
    _emit(click.get_current_context(), profile, local_json)


@cli.group()
def teams() -> None:
    """List teams available to the authenticated user."""


@teams.command("list")
@_json_option
def teams_list(local_json: bool) -> None:
    """Call Penpot's get-owned-teams method."""
    ctx = click.get_current_context()
    _emit(ctx, _api(ctx).teams(), local_json)


@cli.group()
def projects() -> None:
    """Inspect projects in a team."""


@projects.command("list")
@click.option("--team-id", required=True, help="Team UUID.")
@_json_option
def projects_list(team_id: str, local_json: bool) -> None:
    """List projects with the OpenAPI get-projects method."""
    ctx = click.get_current_context()
    _emit(ctx, _api(ctx).projects(team_id), local_json)


@cli.group()
def files() -> None:
    """Inspect files in a project."""


@files.command("list")
@click.option("--project-id", required=True, help="Project UUID.")
@_json_option
def files_list(project_id: str, local_json: bool) -> None:
    """List files with the OpenAPI get-project-files method."""
    ctx = click.get_current_context()
    _emit(ctx, _api(ctx).files(project_id), local_json)


@cli.group()
def file() -> None:
    """Read page and thumbnail data from a file."""


@file.command("page")
@click.option("--file-id", required=True, help="File UUID.")
@click.option("--page-id", help="Page UUID; required with --object-id.")
@click.option("--object-id", help="Object UUID to retrieve, optionally with children.")
@_json_option
def file_page(file_id: str, page_id: str | None, object_id: str | None, local_json: bool) -> None:
    """Retrieve a page or selected object using get-page."""
    if object_id and not page_id:
        raise click.UsageError("--page-id is required when --object-id is supplied")
    ctx = click.get_current_context()
    _emit(ctx, _api(ctx).page(file_id, page_id, object_id), local_json)


@file.command("thumbnail-data")
@click.option("--file-id", required=True, help="File UUID.")
@_json_option
def file_thumbnail(file_id: str, local_json: bool) -> None:
    """Retrieve partial file data used for thumbnail rendering."""
    ctx = click.get_current_context()
    _emit(ctx, _api(ctx).post("get-file-data-for-thumbnail", {"fileId": file_id}), local_json)


@cli.group()
def api() -> None:
    """Call a documented Penpot RPC method directly."""


@api.command("call")
@click.argument("method")
@click.option("--data", default="{}", show_default=True, help="JSON object sent as the request body.")
@_json_option
def api_call(method: str, data: str, local_json: bool) -> None:
    """POST METHOD with JSON DATA; useful for newly documented Penpot methods."""
    if "/" in method or not method or method.startswith("."):
        raise click.BadParameter("must be a Penpot method name, not a URL path", param_hint="method")
    try:
        payload = json.loads(data)
    except json.JSONDecodeError as exc:
        raise click.BadParameter(f"invalid JSON: {exc}", param_hint="--data") from exc
    if not isinstance(payload, dict):
        raise click.BadParameter("must decode to a JSON object", param_hint="--data")
    ctx = click.get_current_context()
    _emit(ctx, _api(ctx).post(method, payload), local_json)
def _run_repl(ctx: click.Context) -> None:
    try:
        load_config()
    except ConfigError as exc:
        value = prompt_config()
        path = save_config(value)
        click.echo(f"Saved configuration to {path}", err=True)
    skin = ReplSkin("penpot", VERSION)
    skin.print_banner()
    commands = {
        "status": "Validate credentials and show profile",
        "teams list": "List owned teams",
        "projects list --team-id UUID": "List team projects",
        "files list --project-id UUID": "List project files",
        "file page --file-id UUID": "Read page data",
        "api call METHOD --data '{}'": "Call a documented RPC method",
        "config init": "Set up server and token",
        "help": "Show this command list",
        "quit": "Exit the REPL",
    }
    session = skin.create_prompt_session()
    while True:
        try:
            line = skin.get_input(session).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            skin.print_goodbye()
            return
        if not line:
            continue
        if line in {"quit", "exit"}:
            skin.print_goodbye()
            return
        if line == "help":
            skin.help(commands)
            continue
        try:
            cli.main(args=shlex.split(line), prog_name="cli-anything-penpot", standalone_mode=False, obj={"from_repl": True, "json": False, "timeout": ctx.obj["timeout"]})
        except (click.ClickException, click.UsageError) as exc:
            skin.error(exc.format_message())
        except ApiError as exc:
            skin.error(str(exc))
        except ConfigError as exc:
            skin.error(str(exc))


def main() -> None:
    try:
        cli()
    except (ApiError, ConfigError) as exc:
        raise click.ClickException(str(exc)) from exc
