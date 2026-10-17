# Setup and local workspaces

[Documentation](README.md) · [Getting started](GETTING_STARTED.md) · [Project overview](../README.md)

Commands using `./start.sh` assume your terminal is in the SimShelf source checkout.

## Open the app

From a fresh checkout, explicitly set up its dedicated Python environment once:

```bash
./start.sh --setup
./start.sh
```

The app opens at **http://127.0.0.1:8740**. Keep the terminal running while using
the browser. Closing the browser does not interrupt recorded runs. Stopping the server cancels
its portal-launched runs; terminal/editor recorders remain independent.
Press Ctrl+C in the server terminal to stop the interface.

Python 3.11 or newer is required. The launcher keeps its environment and default
workspace outside the checkout. For a checkout at `/path/to/SimShelf/SimShelf`:

```text
/path/to/SimShelf/
  SimShelf/                 source checkout
  environments/SimShelf/    dedicated development Python environment
  workspaces/SimShelf/      persistent library
  workspaces/SimShelf-demo/ optional demo library
  test-output/SimShelf/     optional demo sources and outputs
```

`--setup` explicitly creates or updates only the launcher's dedicated environment.
Normal startup never installs dependencies. An active editor/terminal virtual
environment is not modified. Existing environments without this checkout's
ownership marker are refused; select a new path instead. A failed setup can be
retried with the same command. The built browser interface is included, so Node.js
is not needed to use the application.

Workspace precedence for the launcher is `--workspace PATH` (before `--cli` or
`--demo`), then `SIMSHELF_HOME`, then the external default above. Relative paths
resolve from the invoking terminal directory; `~` is expanded. Empty overrides
are rejected. `SIMSHELF_DEV_ROOT` changes the parent development directory and
`SIMSHELF_DEV_ENV` selects a dedicated environment path, which must be outside the
checkout. Set the same overrides for setup and subsequent commands. Environments
belong to one checkout: a different clone needs its own environment path. Library
paths are independent of code revisions; updating source does not move records.

For a different local workspace:

```bash
SIMSHELF_HOME=/path/to/my-library ./start.sh
```

The workspace contains the database and retained files, not your source project.
Keep it on a local disk. Register simulation source folders separately.

## Choose an appearance

Use **Appearance** in the sidebar to choose System, Light, Dark, Onyx,
Slate or Linen. System follows your operating system; the other palettes
keep their chosen light/dark appearance. The browser remembers your selection
on this local portal address. Themes change colors only, including subtle logo
colors; they do not change layout or simulation data.

## Try the included example

The example needs only Python and SimShelf. It computes a small damped scalar
wave, writes actual field images and summary files, and keeps raw fields as
references. Create four real runs in a separate demo workspace:

```bash
./start.sh --demo
./start.sh --workspace ../workspaces/SimShelf-demo
```

One run deliberately fails to demonstrate retained partial results. The default
workspace is unaffected. Running the demo command again appends another set of
runs; it never clears existing history. Each invocation copies the two example
source files to a new external `test-output/SimShelf/scalar-demo-*` folder, which
also retains its outputs and is registered as a separate simulation. Keep these
folders while their reference-only files are useful. The demo honors an explicit
`SIMSHELF_HOME` or `--workspace`; unset it to use the separate default demo library.
Use `./start.sh --demo --output-root /external/path` to select another output root.
