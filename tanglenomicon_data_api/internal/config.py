"""internal.config holds and loads the configuration for the server."""

import yaml
from pathlib import Path

config: dict = None


def load(path: str):
    """Load the configuration from file.

    Parameters
    ----------
    path : str
        The path to find the configuration on disk.
    """
    global config
    path = Path.cwd() / Path(path)
    config = dict()
    with open(path) as f:
        config.update(yaml.load(f, Loader=yaml.FullLoader))
    ...
