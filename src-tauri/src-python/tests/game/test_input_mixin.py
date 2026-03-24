"""Tests for InputMixin swipe direction coordinate calculation."""

import unittest
from pathlib import Path
from unittest.mock import MagicMock

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


PORTRAIT_1080x1920 = DisplayInfo(
    resolution=Resolution(width=1080, height=1920),
    orientation=Orientation.PORTRAIT,
)


class TestSwipeDirection(unittest.TestCase):
    """Tests for InputMixin._swipe_direction coordinate calculation.

    Display: 1080x1920 portrait → rx=1080, ry=1920.
    """

    def setUp(self):
        self.game = MockGame()
        self.mock_device: MagicMock = MagicMock()
        self.game._device = self.mock_device  # type: ignore[assignment]
        self.mock_device.get_display_info.return_value = PORTRAIT_1080x1920

    def _swipe_args(self):
        """Return (start_point, end_point, duration) from the last swipe call."""
        call = self.mock_device.swipe.call_args
        start, end = call.args
        duration = call.kwargs["duration"]
        return start, end, duration

    # ── swipe_down ────────────────────────────────────────────────────────────

    def test_swipe_down_defaults(self):
        """swipe_down() uses horizontal center, full vertical span."""
        self.game.swipe_down()
        start, end, duration = self._swipe_args()
        self.assertEqual(start.x, 540)
        self.assertEqual(start.y, 0)
        self.assertEqual(end.x, 540)
        self.assertEqual(end.y, 1920)
        self.assertEqual(duration, 1.0)

    def test_swipe_down_custom_coords(self):
        """swipe_down() respects explicit x, sy, ey arguments."""
        self.game.swipe_down(x=200, sy=100, ey=1800)
        start, end, _ = self._swipe_args()
        self.assertEqual(start.x, 200)
        self.assertEqual(start.y, 100)
        self.assertEqual(end.x, 200)
        self.assertEqual(end.y, 1800)

    def test_swipe_down_invalid_coords_raises(self):
        """swipe_down() raises ValueError when start >= end."""
        with self.assertRaises(ValueError):
            self.game.swipe_down(sy=1000, ey=500)

    # ── swipe_up ──────────────────────────────────────────────────────────────

    def test_swipe_up_defaults(self):
        """swipe_up() uses horizontal center, bottom-to-top span."""
        self.game.swipe_up()
        start, end, duration = self._swipe_args()
        self.assertEqual(start.x, 540)
        self.assertEqual(start.y, 1920)
        self.assertEqual(end.x, 540)
        self.assertEqual(end.y, 0)
        self.assertEqual(duration, 1.0)

    def test_swipe_up_invalid_coords_raises(self):
        """swipe_up() raises ValueError when start <= end."""
        with self.assertRaises(ValueError):
            self.game.swipe_up(sy=100, ey=500)

    # ── swipe_right ───────────────────────────────────────────────────────────

    def test_swipe_right_defaults(self):
        """swipe_right() uses vertical center, full horizontal span."""
        self.game.swipe_right()
        start, end, duration = self._swipe_args()
        self.assertEqual(start.x, 0)
        self.assertEqual(start.y, 960)
        self.assertEqual(end.x, 1080)
        self.assertEqual(end.y, 960)
        self.assertEqual(duration, 1.0)

    def test_swipe_right_custom_coords(self):
        """swipe_right() respects explicit y, sx, ex arguments."""
        self.game.swipe_right(y=400, sx=50, ex=900)
        start, end, _ = self._swipe_args()
        self.assertEqual(start.x, 50)
        self.assertEqual(start.y, 400)
        self.assertEqual(end.x, 900)
        self.assertEqual(end.y, 400)

    def test_swipe_right_invalid_coords_raises(self):
        """swipe_right() raises ValueError when start >= end."""
        with self.assertRaises(ValueError):
            self.game.swipe_right(sx=900, ex=100)

    # ── swipe_left ────────────────────────────────────────────────────────────

    def test_swipe_left_defaults(self):
        """swipe_left() uses vertical center, right-to-left span."""
        self.game.swipe_left()
        start, end, duration = self._swipe_args()
        self.assertEqual(start.x, 1080)
        self.assertEqual(start.y, 960)
        self.assertEqual(end.x, 0)
        self.assertEqual(end.y, 960)
        self.assertEqual(duration, 1.0)

    def test_swipe_left_invalid_coords_raises(self):
        """swipe_left() raises ValueError when start <= end."""
        with self.assertRaises(ValueError):
            self.game.swipe_left(sx=100, ex=900)

    # ── custom duration ───────────────────────────────────────────────────────

    def test_custom_duration_passed_through(self):
        """Duration argument is forwarded to device.swipe."""
        self.game.swipe_down(duration=2.5)
        _, _, duration = self._swipe_args()
        self.assertEqual(duration, 2.5)
