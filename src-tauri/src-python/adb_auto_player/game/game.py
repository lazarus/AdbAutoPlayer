"""ADB Auto Player Game Base Module."""

import logging
from abc import ABC, abstractmethod
from functools import cached_property
from pathlib import Path

from adb_auto_player.exceptions import AutoPlayerUnrecoverableError
from adb_auto_player.file_loader import SettingsLoader
from adb_auto_player.registries import GAME_REGISTRY
from pydantic import BaseModel

from ._task_runner_mixin import TaskRunnerMixin


class Game(TaskRunnerMixin, ABC):
    """Generic Game class."""

    @property
    @abstractmethod
    def settings(self) -> BaseModel:
        """Required property to return the game settings."""
        ...

    def _get_game_module(self) -> str:
        parts = self.__class__.__module__.split(".")
        try:
            index = parts.index("games")
            return parts[index + 1]
        except ValueError:
            raise ValueError("'games' not found in module path")
        except IndexError:
            raise ValueError("No module found after 'games' in module path")

    @property
    def settings_file_path(self) -> Path:
        """Path for settings file."""
        for module, game in GAME_REGISTRY.items():
            if module == self._get_game_module():
                if game.settings_file is None:
                    raise AutoPlayerUnrecoverableError(
                        "Game does not have any Settings"
                    )
                return SettingsLoader.settings_dir() / game.settings_file

        raise AutoPlayerUnrecoverableError("Game does not have any Settings")

    @cached_property
    def template_dir(self) -> Path:
        """Retrieve path to images."""
        module = self._get_game_module()
        template_dir = SettingsLoader.games_dir() / module / "templates"
        logging.debug(f"{module} template path: {template_dir}")
        return template_dir
