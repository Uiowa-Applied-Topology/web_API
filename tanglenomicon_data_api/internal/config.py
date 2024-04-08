from pydantic_settings import BaseSettings
import yaml
from pathlib import Path



class Settings(BaseSettings):
    yaml_settings : dict = {}
    def load(self, path: str):
        path = Path.cwd()/Path(path)
        self.yaml_settings = dict()
        with open(path) as f:
            self.yaml_settings.update(yaml.load(f, Loader=yaml.FullLoader))
        ...