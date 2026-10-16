"""Record Python simulations without a running web server."""

__version__ = "0.1.0"


def run(simulation, **kwargs):
    """Start a run, or join the run established by ``simshelf record``."""
    from .recording import Run
    return Run(simulation, **kwargs)


__all__ = ["run", "__version__"]
