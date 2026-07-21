from pathlib import Path
import os
import yaml
# from dataclasses import dataclass

# @dataclass
class Config():

    def __init__(self):
        self.path = self._yamlfile()
        self.data = self._load()

    def _yamlfile(self):
        config_file = os.environ.get("OCT_PUBLISH_CONFIG")

        if config_file:
            return Path(config_file)

        root = Path(__file__).resolve().parent.parent.parent
        return root / "config.yaml"

    def _load(self):
        if not self.path.exists():
            raise FileNotFoundError(
                f"Missing config file: {self.path}"
            )

        with open(self.path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def get(self, key, default=None):
        """
        支持:
        config.get("database.host")
        """

        value = self.data

        for k in key.split("."):
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default

        return value