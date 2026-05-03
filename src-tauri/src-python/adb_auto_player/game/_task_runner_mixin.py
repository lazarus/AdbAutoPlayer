"""Custom routine scheduling and task execution."""

import logging
from abc import abstractmethod

import cv2
from adb_auto_player.exceptions import (
    AutoPlayerError,
    AutoPlayerUnrecoverableError,
    GameNotRunningOrFrozenError,
)
from adb_auto_player.image_manipulation import IO
from adb_auto_player.models.pydantic import TaskListSettings
from adb_auto_player.models.registries import CustomRoutineEntry
from adb_auto_player.registries import CUSTOM_ROUTINE_REGISTRY
from adb_auto_player.util import Execute
from pydantic import BaseModel

from ._template_mixin import TemplateMixin


class TaskRunnerMixin(TemplateMixin):
    """Schedules and executes custom routines and task lists."""

    @property
    @abstractmethod
    def settings(self) -> BaseModel:
        """Required property to return the game settings."""
        ...

    def _get_custom_routine_settings(self, name: str) -> TaskListSettings:
        if hasattr(self.settings, name):
            attribute = getattr(self.settings, name)
            if isinstance(attribute, TaskListSettings):
                return attribute
            else:
                raise ValueError(
                    f"Attribute '{name}' exists but is not MyCustomRoutineSettings"
                )
        raise AttributeError(f"Settings has no attribute '{name}'")

    def _execute_custom_routine(self, settings: TaskListSettings) -> None:
        game_commands = self._get_game_commands()
        if not game_commands:
            logging.error("Failed to load Custom Routine Tasks.")
            return

        custom_routines: dict[str, CustomRoutineEntry] = {}
        for task in settings.tasks:
            routine = self._get_custom_routine_for_task(task, game_commands)
            if not routine:
                logging.error(f"Task '{task}' not found")
            else:
                custom_routines[task] = routine

        if not custom_routines:
            logging.error("No Tasks found")
            return

        self._execute_tasks(custom_routines)
        while settings.repeat:
            self._execute_tasks(custom_routines)

    def _get_game_commands(self) -> dict[str, CustomRoutineEntry] | None:
        commands = CUSTOM_ROUTINE_REGISTRY
        for module, cmds in commands.items():
            if module in self.__module__:
                return cmds
        return None

    def _get_custom_routine_for_task(
        self, task: str, game_commands: dict[str, CustomRoutineEntry]
    ) -> CustomRoutineEntry | None:
        for label, custom_routine_entry in game_commands.items():
            if task == label:
                return custom_routine_entry
        return None

    def _execute_tasks(self, tasks: dict[str, CustomRoutineEntry]) -> None:
        all_tasks_failed = True

        for task, routine in tasks.items():
            error = Execute.function(
                callable_function=routine.func,
                kwargs=routine.kwargs,
            )
            self._handle_task_error(task, error)
            if not error:
                all_tasks_failed = False

        if all_tasks_failed:
            self.restart_game()

    def _handle_task_error(self, task: str, error: Exception | None) -> None:
        if not error:
            return

        if isinstance(error, cv2.error):
            if self._stream:
                logging.error(
                    "CV2 error attempting to clear caches and stopping device "
                    f"streaming, original error message: {error}"
                )
                self._stream.stop()
            else:
                logging.error(
                    "CV2 error attempting to clear caches, original error message: "
                    f"{error}"
                )
            IO.cache_clear()
            return

        if isinstance(error, KeyboardInterrupt):
            raise error

        if isinstance(error, AutoPlayerUnrecoverableError):
            logging.error(
                f"Task '{task}' failed with critical error: {error}, exiting..."
            )
            raise error

        if isinstance(error, GameNotRunningOrFrozenError):
            logging.warning(
                f"Task '{task}' failed because the game crashed or is frozen, "
                "attempting to restart it."
            )
            self.restart_game()
            return

        if isinstance(error, AutoPlayerError):
            if not self.is_game_running():
                logging.warning(
                    f"Task '{task}' failed because the game crashed, "
                    "attempting to restart it."
                )
                self.start_game()
                return
            else:
                logging.warning(f"Task '{task}' failed moving to next Task.")
                return

        logging.error(
            f"Task '{task}' failed with unexpected Error: {error} moving to next Task."
        )
