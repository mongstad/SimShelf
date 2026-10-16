"""Record Python simulations without a running web server."""

from ._version import __version__


def run(simulation, **kwargs):
    """Start a run, or join the run established by ``simshelf record``."""
    from .recording import Run
    return Run(simulation, **kwargs)


__all__ = ["run", "__version__"]
