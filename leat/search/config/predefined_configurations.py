"""Predefined Configurations"""

import importlib.resources as resources
from pathlib import Path
from typing import List


DEFAULT_CONFIG_DIRECTORY = resources.files("leat") / "data" / "config"
"""Base location for configuration files for predefined configurations"""

PREDEFINED_CONFIGURATIONS = {
    "BasicSearch": DEFAULT_CONFIG_DIRECTORY / "BasicSearch.json"
}
"""Mapping from string names to path of configuration file"""


class PredefinedConfigurations:
    """
    Predefined configurations

    Attributes:
      data: dict: Mapping from string names to path of configuration file

    """

    data: dict = PREDEFINED_CONFIGURATIONS

    @classmethod
    def list(cls) -> List[str]:
        """Returns names of predefined configurations"""
        return list(PREDEFINED_CONFIGURATIONS.keys())
