from logging import Logger
import os, yaml
from rag_app.app.models import ConfigurationsModel
from rag_app.app.core.errors import ConfigurationsError
from pydantic import ValidationError

class Configurations:
    def __init__(self, logger: Logger, yaml_values: ConfigurationsModel):
        self.logger = logger
        self.yaml_values = yaml_values

    def __getattr__(self, name):
        return getattr(self.yaml_values, name)

    @classmethod
    def load(cls, logger: Logger):
        yaml_path = os.getenv("CONFIGS_PATH")
        print(f"configs path from .env: {yaml_path}")
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)
        try:
            yaml_values = ConfigurationsModel(**data)
        except ValidationError as e:
            raise ConfigurationsError(f"Invalid configuration: {e}") from e

        return cls(logger, yaml_values)
    
    @classmethod
    def from_model(cls, logger: Logger, configs_model: ConfigurationsModel):
        """Explicitly construct from a ConfigurationsModel (for testing)."""
        return cls(logger, configs_model)