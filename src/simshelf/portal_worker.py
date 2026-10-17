"""Internal recorder supervisor. Its control pipe belongs to one UI server."""
import json
import os
import signal
import sys
import threading

from .portal import execution_settings
from .recording import record_command
from .store import Store


def main():
    cancel = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: cancel.set())
    try:
        request = json.loads(sys.stdin.buffer.readline())
        # Only the server holds the write end; server crash/restart is cancellation.
        def watch():
            os.read(sys.stdin.fileno(), 1)
            cancel.set()
        threading.Thread(target=watch, daemon=True).start()
        store = Store(request["workspace"])
        plan = execution_settings(store.simulation(request["simulation"]), request["settings"])
        if plan["output_review"]["requires_acknowledgement"] and not request.get("acknowledge_outputs", False):
            raise ValueError("Output coverage changed; review output paths before launching")
        def started(run_id):
            try:
                print(json.dumps({"run_id": run_id}), flush=True)
            except BrokenPipeError:
                cancel.set()
        record_command(store, request["simulation"], plan["command"], name=request["name"],
                       cwd=plan["cwd"], output_dir=plan["settings"]["output_dir"],
                       cancel=cancel, on_started=started, quiet=True, progress_mode=plan["settings"]["progress_mode"], launch={"kind": "portal", "output_review": plan["output_review"], "outputs_acknowledged": request.get("acknowledge_outputs", False)})
    except Exception as exc:
        try:
            print(json.dumps({"error": str(exc)}), flush=True)
        except BrokenPipeError:
            pass
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
