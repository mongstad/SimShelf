from __future__ import annotations

import argparse
import json
import socket
import errno
import sys
import threading
import webbrowser
from pathlib import Path

from . import __version__
from .backup import create_backup, restore_backup
from .common import default_workspace
from .recording import record_command
from .store import Store


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(prog="simshelf", description="Your local simulation library and run journal.")
    cli.add_argument("--workspace", type=Path, help="Workspace folder (or set SIMSHELF_HOME)")
    cli.add_argument("--version", action="version", version=f"SimShelf {__version__}")
    commands = cli.add_subparsers(dest="action", required=True)
    commands.add_parser("init", help="Create the local workspace")
    add = commands.add_parser("add", help="Register an existing simulation folder")
    add.add_argument("folder", type=Path)
    add.add_argument("--name")
    add.add_argument("--entry", dest="entrypoint", help="Entry file relative to the simulation folder")
    add.add_argument("--version-file", help="Python file containing SIMSHELF_VERSION")
    record = commands.add_parser("record", help="Record a terminal command, preserving its exit status")
    record.add_argument("--simulation", "-s", required=True)
    record.add_argument("--name")
    record.add_argument("--tag", action="append", default=[])
    record.add_argument("--cwd", type=Path, help="Working directory; defaults to your current directory")
    record.add_argument("--output-dir", help="Run-specific capture folder relative to the simulation folder")
    record.add_argument("command", nargs=argparse.REMAINDER)
    ui = commands.add_parser("ui", help="Open the local browser interface")
    ui.add_argument("--port", type=int, default=8740)
    ui.add_argument("--no-open", action="store_true")
    listing = commands.add_parser("list", help="List simulations or runs")
    listing.add_argument("--simulation")
    listing.add_argument("--json", action="store_true")
    show = commands.add_parser("show", help="Print a run record as JSON")
    show.add_argument("run_id")
    backup = commands.add_parser("backup", help="Back up the database and retained files")
    backup.add_argument("destination", type=Path)
    restore = commands.add_parser("restore", help="Restore into a new or empty workspace")
    restore.add_argument("archive", type=Path)
    restore.add_argument("--to", type=Path, required=True)
    commands.add_parser("doctor", help="Recover pending records and detect interrupted runs")
    return cli


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.action == "restore":
            restored = restore_backup(args.archive, args.to)
            print(f"Restored workspace: {restored.path}")
            return 0
        store = Store(args.workspace)
        if args.action == "init":
            print(f"Workspace ready: {store.path}")
        elif args.action == "add":
            sim = store.add_simulation(args.folder, args.name, args.entrypoint, args.version_file)
            print(f"Registered {sim['name']}\nSimulation ID: {sim['id']}\nSource folder: {sim['root']}")
        elif args.action == "record":
            command = args.command[1:] if args.command[:1] == ["--"] else args.command
            _, code = record_command(store, args.simulation, command, name=args.name, tags=args.tag, cwd=args.cwd, output_dir=args.output_dir)
            return code
        elif args.action == "ui":
            import uvicorn
            from .api import create_app
            if not 1 <= args.port <= 65535:
                raise ValueError("Port must be between 1 and 65535")
            url = f"http://127.0.0.1:{args.port}"
            # Reserve the actual listener before opening a browser. No probe/close race.
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
                listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    listener.bind(("127.0.0.1", args.port))
                    listener.listen(2048)
                except OSError as exc:
                    if exc.errno == errno.EADDRINUSE:
                        raise ValueError(f"Port {args.port} is already in use. Open {url} to check the existing server, or choose another --port. Stop an existing SimShelf instance using Quit SimShelf or its original terminal.") from exc
                    raise
                app = create_app(store.path, request_shutdown=lambda: setattr(server, "should_exit", True))
                server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=args.port, log_level="warning"))
                print(f"SimShelf: {url}\nWorkspace: {store.path}", flush=True)
                timer = None
                if not args.no_open:
                    timer = threading.Timer(1, lambda: webbrowser.open(url))
                    timer.daemon = True
                    timer.start()
                try:
                    server.run(sockets=[listener])
                finally:
                    if timer:
                        timer.cancel()
        elif args.action == "list":
            store.reconcile()
            items = store.runs(simulation=args.simulation) if args.simulation else store.simulations()
            if args.json:
                print(json.dumps(items, indent=2))
            else:
                for item in items:
                    print(f"{item['id']}  {item.get('status', ''):12} {item['name']}  {item.get('version', '')}")
                if not items:
                    print("No records yet. Register a folder with simshelf add.")
        elif args.action == "show":
            store.reconcile()
            print(json.dumps(store.run(args.run_id), indent=2))
        elif args.action == "backup":
            print(f"Backup saved: {create_backup(store, args.destination)}")
        elif args.action == "doctor":
            print(json.dumps(store.reconcile(), indent=2))
        return 0
    except (ValueError, OSError) as exc:
        print(f"SimShelf: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
