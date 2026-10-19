"""Read-only activity projection for simulation administration guidance."""
from __future__ import annotations

import json


def blocks_administration(run):
    # Keep the existing removal contract, including terminal-but-pending capture.
    return run['status'] not in {'completed', 'failed', 'interrupted'} or run.get('capture_status') == 'pending'


def has_active_runs(conn, ident):
    # No list limit, search, status filter, or ownership restriction. Iterate rather
    # than materializing all historical run records, and stop at the first match.
    return any(blocks_administration(json.loads(row[0])) for row in conn.execute(
        'SELECT data FROM runs WHERE simulation_id=?', (ident,)))
