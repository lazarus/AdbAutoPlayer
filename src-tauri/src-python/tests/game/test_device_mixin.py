"""Tests for DeviceMixin methods."""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
from adb_auto_player.exceptions import (
    GenericAdbUnrecoverableError,
    UnsupportedResolutionError,
)
from adb_auto_player.game import Game
from adb_auto_player.models.device import DisplayInfo, Orientation, Resolution
from pydantic import BaseModel


class MockSettings(BaseModel):
    pass


class MockGame(Game):
    @property
    def template_dir(self) -> Path:
        return Path(".")

    @property
    def settings(self) -> BaseModel:
        return MockSettings()


class TestGetScreenshot(unittest.TestCase):
    """Tests for DeviceMixin.get_screenshot stream/screencap logic."""

    def setUp(self):
        self.game = MockGame()
        self.mock_device: MagicMock = MagicMock()
        self.mock_device.identifier = "test:5555"
        self.game._device = self.mock_device  # type: ignore[assignment]
        self.fake_frame = np.zeros((100, 100, 3), dtype=np.uint8)

    def test_stream_frame_used_when_available(self):
        """Returns converted frame from stream; does not call screencap."""
        mock_stream: MagicMock = MagicMock()
        mock_stream.get_latest_frame.return_value = self.fake_frame
        self.game._stream = mock_stream  # type: ignore[assignment]

        result = self.game.get_screenshot()

        self.assertIsNotNone(result)
        self.mock_device.screenshot.assert_not_called()

    def test_stream_none_falls_back_to_screencap(self):
        """Falls back to screencap when stream has no frame yet."""
        mock_stream: MagicMock = MagicMock()
        mock_stream.get_latest_frame.return_value = None
        self.game._stream = mock_stream  # type: ignore[assignment]
        self.mock_device.screenshot.return_value = b"png_bytes"

        with patch(
            "adb_auto_player.game._device_mixin.IO.get_bgr_np_array_from_png_bytes",
            return_value=self.fake_frame,
        ):
            result = self.game.get_screenshot()

        np.testing.assert_array_equal(result, self.fake_frame)
        self.mock_device.screenshot.assert_called_once()

    def test_no_stream_screencap_succeeds(self):
        """Uses screencap directly when no stream is active."""
        self.mock_device.screenshot.return_value = b"png_bytes"

        with patch(
            "adb_auto_player.game._device_mixin.IO.get_bgr_np_array_from_png_bytes",
            return_value=self.fake_frame,
        ):
            result = self.game.get_screenshot()

        np.testing.assert_array_equal(result, self.fake_frame)
        self.mock_device.screenshot.assert_called_once()

    def test_screencap_retried_three_times_on_oserror(self):
        """Retries screencap 3 times on OSError before raising."""
        self.mock_device.screenshot.side_effect = OSError("disconnected")

        with patch("adb_auto_player.game._device_mixin.sleep"):
            with self.assertRaises(GenericAdbUnrecoverableError):
                self.game.get_screenshot()

        self.assertEqual(self.mock_device.screenshot.call_count, 3)

    def test_screencap_non_bytes_result_exhausts_retries(self):
        """Raises after retries when screencap returns non-bytes."""
        self.mock_device.screenshot.return_value = None

        with patch("adb_auto_player.game._device_mixin.sleep"):
            with self.assertRaises(GenericAdbUnrecoverableError):
                self.game.get_screenshot()


class TestIsGameRunning(unittest.TestCase):
    """Tests for DeviceMixin.is_game_running prefix matching logic."""

    def setUp(self):
        self.game = MockGame()
        self.mock_device: MagicMock = MagicMock()
        self.game._device = self.mock_device  # type: ignore[assignment]
        self.game.package_name_prefixes = ["com.example.game"]

    def test_no_running_app_returns_false(self):
        """Returns False when device reports no foreground app."""
        self.mock_device.get_running_app.return_value = None
        self.assertFalse(self.game.is_game_running())

    def test_prefix_match_returns_true_and_caches_package(self):
        """Returns True and stores the full package name on first match."""
        self.mock_device.get_running_app.return_value = "com.example.game.global"

        self.assertTrue(self.game.is_game_running())
        self.assertEqual(self.game._target_package_name, "com.example.game.global")

    def test_no_prefix_match_returns_false(self):
        """Returns False when running app does not match any prefix."""
        self.mock_device.get_running_app.return_value = "com.other.app"

        self.assertFalse(self.game.is_game_running())
        self.assertIsNone(self.game._target_package_name)

    def test_cached_target_exact_match_returns_true(self):
        """Returns True when running app matches the cached target package."""
        self.game._target_package_name = "com.example.game.global"
        self.mock_device.get_running_app.return_value = "com.example.game.global"

        self.assertTrue(self.game.is_game_running())

    def test_cached_target_different_variant_returns_false(self):
        """Returns False when running app differs from cached target."""
        self.game._target_package_name = "com.example.game.global"
        self.mock_device.get_running_app.return_value = "com.example.game.vn"

        self.assertFalse(self.game.is_game_running())


class TestCheckRequirements(unittest.TestCase):
    """Tests for DeviceMixin._check_requirements resolution validation."""

    def setUp(self):
        self.game = MockGame()
        self.mock_device: MagicMock = MagicMock()
        self.game._device = self.mock_device  # type: ignore[assignment]

    def _set_display(self, resolution: Resolution, orientation: Orientation) -> None:
        self.mock_device.get_display_info.return_value = DisplayInfo(
            resolution=resolution,
            orientation=orientation,
        )

    def test_matching_resolution_passes(self):
        """No exception when display matches base resolution."""
        self.game.base_resolution = Resolution(1080, 1920)
        self._set_display(Resolution(1080, 1920), Orientation.PORTRAIT)
        self.game._check_requirements()  # must not raise

    def test_wrong_resolution_same_orientation_raises(self):
        """Raises UnsupportedResolutionError for mismatched resolution."""
        self.game.base_resolution = Resolution(1080, 1920)
        self._set_display(Resolution(720, 1280), Orientation.PORTRAIT)

        with self.assertRaises(UnsupportedResolutionError):
            self.game._check_requirements()

    def test_wrong_orientation_raises_with_orientation_hint(self):
        """Error message includes required orientation when orientations differ."""
        self.game.base_resolution = Resolution(1080, 1920)  # portrait base
        self._set_display(Resolution(1920, 1080), Orientation.LANDSCAPE)

        with self.assertRaises(UnsupportedResolutionError) as ctx:
            self.game._check_requirements()

        self.assertIn("Portrait", str(ctx.exception))
