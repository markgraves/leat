"""Predefined Configurations"""

from pathlib import Path

DEFAULT_CONFIG_DIRECTORY = Path(__file__).parent.parent.parent / "data" / "config"

PREDEFINED_CONFIGURATIONS = {
    "BasicSearch": DEFAULT_CONFIG_DIRECTORY / "BasicSearch.json"
}


class PredefinedConfigurations:

    data = PREDEFINED_CONFIGURATIONS

    @classmethod
    def list(cls):
        return list(PREDEFINED_CONFIGURATIONS.keys())
