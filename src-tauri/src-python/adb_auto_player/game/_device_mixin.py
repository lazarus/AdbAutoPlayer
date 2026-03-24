"""Device lifecycle, stream management, and screenshot handling."""

import logging
from abc import ABC
from time import sleep

import numpy as np
from adb_auto_player.device.adb import AdbController, DeviceStream
from adb_auto_player.exceptions import (
    AutoPlayerWarningError,
    GameNotRunningOrFrozenError,
    GenericAdbUnrecoverableError,
    UnsupportedResolutionError,
)
from adb_auto_player.file_loader import SettingsLoader
from adb_auto_player.image_manipulation import IO, Color
from adb_auto_player.models import ConfidenceValue
from adb_auto_player.models.device import DisplayInfo, Resolution
from adb_auto_player.models.geometry import Point


class DeviceMixin(ABC):
    """Manages ADB device connection, screen streaming, and game lifecycle."""

    def __init__(self) -> None:
        """Initialize device state."""
        self.default_threshold: ConfidenceValue = ConfidenceValue("90%")
        # e.g. AFK Journey
        #   Global: com.farlightgames.igame.gp
        #   Vietnam: com.farlightgames.igame.gp.vn
        #   Global will cover both cases because it checks for the prefix
        self.package_name_prefixes: list[str] = []
        # Assuming landscape for most games
        self.base_resolution: Resolution = Resolution.from_string("1920x1080")
        self._device: AdbController | None = None
        self._stream: DeviceStream | None = None
        self._target_package_name: str | None = None

    @property
    def display_info(self) -> DisplayInfo:
        """Resolves and returns DisplayInfo instance."""
        return self.device.get_display_info()

    @property
    def device(self) -> AdbController:
        """Get device."""
        if self._device is None:
            self._device = AdbController()
        return self._device

    @property
    def center(self) -> Point:
        """Return center Point of display."""
        return self.base_resolution.center

    def start_stream(self) -> None:
        """Start the device stream."""
        try:
            self._stream = DeviceStream(self.device)
        except AutoPlayerWarningError as e:
            logging.warning(f"{e}")

        if self._stream is None:
            return

        self._stream.start()
        time_waiting_for_stream_to_start = 0
        attempts = 10
        while True:
            if time_waiting_for_stream_to_start >= attempts:
                logging.error("Could not start Device Stream using screenshots instead")
                if self._stream:
                    self._stream.stop()
                    self._stream = None
                break
            if self._stream and self._stream.get_latest_frame() is not None:
                logging.debug("Device Stream started")
                break
            sleep(1)
            time_waiting_for_stream_to_start += 1

    def stop_stream(self) -> None:
        """Stop the device stream."""
        if self._stream:
            self._stream.stop()
            self._stream = None

    def open_eyes(self, device_streaming: bool = True) -> None:
        """Give the bot eyes.

        Set the device for the game and start the device stream.

        Args:
            device_streaming (bool, optional): Whether to start the device stream.
        """
        self._set_device_resolution()
        self._check_requirements()

        self._start_device_streaming(device_streaming=device_streaming)
        self._check_screenshot_matches_display_resolution(device_streaming_check=False)

        if self.is_game_running():
            return

        logging.warning("Game is not running, trying to start the game.")
        self.start_game()
        if not self.is_game_running():
            raise GameNotRunningOrFrozenError("Game could not be started, exiting...")

    def _start_device_streaming(self, device_streaming: bool = True) -> None:
        if not device_streaming:
            if self._stream:
                logging.debug("Stopping device streaming")
                self._stream.stop()
            return

        if self._stream:
            logging.debug("Device stream already started")
            return

        if not SettingsLoader.adb_settings().device.streaming:
            logging.warning("Real-time Display Streaming is disabled in ADB Settings")
            return

        self.start_stream()
        self._check_screenshot_matches_display_resolution(device_streaming_check=True)

    def _set_device_resolution(self) -> None:
        if not SettingsLoader.adb_settings().device.use_wm_resize:
            return
        if not self.base_resolution == self.display_info.normalized_resolution:
            self.device.set_display_size(str(self.base_resolution))

    def _check_requirements(self) -> None:
        """Validates Device properties such as resolution and orientation.

        Raises:
             UnsupportedResolutionError: Device resolution is not supported.
        """
        current = self.display_info.normalized_resolution
        base = self.base_resolution

        if base == current:
            return

        msg = f"This bot only supports: {base} resolution, detected: {current}"

        if (
            base.orientation == self.display_info.orientation
            or base.is_square
            or current.is_square
        ):
            raise UnsupportedResolutionError(msg)

        orientation_hint = "Portrait" if base.is_portrait else "Landscape"
        raise UnsupportedResolutionError(
            f"{msg} and must be in {orientation_hint} orientation: "
            "https://AdbAutoPlayer.github.io/AdbAutoPlayer/user-guide/"
            "troubleshoot.html#this-bot-only-works-in-portrait-mode"
        )

    def _check_screenshot_matches_display_resolution(
        self, device_streaming_check: bool = False
    ) -> None:
        height, width = self.get_screenshot().shape[:2]
        if (width, height) != self.display_info.dimensions:
            if device_streaming_check:
                logging.warning(
                    f"Device Stream resolution ({width}, {height}) "
                    f"does not match Display Resolution {self.display_info}, "
                    "stopping Device Streaming"
                )
                self.stop_stream()
                return
            raise GenericAdbUnrecoverableError(
                f"Screenshot resolution ({width}, {height}) "
                f"does not match Display Resolution {self.display_info}"
            )

    def get_screenshot(self) -> np.ndarray:
        """Gets screenshot from device using stream or screencap.

        Raises:
            GenericAdbUnrecoverableError: Screenshot cannot be recorded.
        """
        if self._stream:
            image = self._stream.get_latest_frame()
            if image is not None:
                return Color.to_bgr(image)

        max_retries = 3
        for attempt in range(max_retries):
            try:
                data = self.device.screenshot()
                if isinstance(data, bytes):
                    return IO.get_bgr_np_array_from_png_bytes(data)
            except (OSError, ValueError) as e:
                logging.debug(
                    f"Attempt {attempt + 1}/{max_retries}: "
                    f"Failed to process screenshot: {e}"
                )
                sleep(0.1)

        raise GenericAdbUnrecoverableError(
            f"Screenshots cannot be recorded from device: {self.device.identifier}"
        )

    def is_game_running(self) -> bool:
        """Check if Game is still running."""
        if app := self.device.get_running_app():
            if self._target_package_name:
                return app == self._target_package_name
            if any(pn in app for pn in self.package_name_prefixes):
                self._target_package_name = app
                return True
        return False

    def force_stop_game(self) -> None:
        """Force stops the Game."""
        if not self._target_package_name:
            return
        self.device.stop_game(self._target_package_name)

    def start_game(self) -> None:
        """Start the Game.

        Raises:
            GameStartError: Game cannot be started.
        """
        if not self._target_package_name:
            return
        self.device.start_game(self._target_package_name)

    def restart_game(self) -> None:
        """Restart the Game.

        Calls force_stop_game() and start_game().
        """
        self.force_stop_game()
        self.start_game()
