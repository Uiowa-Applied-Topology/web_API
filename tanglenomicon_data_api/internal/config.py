from pydantic_settings import BaseSettings
import yaml
from pathlib import Path

config : dict = None

def load(path: str):
    global config
    path = Path.cwd()/Path(path)
    config = dict()
    with open(path) as f:
        config.update(yaml.load(f, Loader=yaml.FullLoader))
    ...