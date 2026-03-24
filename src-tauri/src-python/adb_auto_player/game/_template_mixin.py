"""Template matching, wait loops, and tap-until helpers."""

import logging
from abc import abstractmethod
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from time import monotonic, perf_counter, sleep
from typing import Literal, TypeVar

import numpy as np
from adb_auto_player.exceptions import (
    AutoPlayerUnrecoverableError,
    GameActionFailedError,
    GameTimeoutError,
)
from adb_auto_player.image_manipulation import IO, Color, Cropping
from adb_auto_player.models import ConfidenceValue
from adb_auto_player.models.geometry import Coordinates, Point, PointOutsideDisplay
from adb_auto_player.models.image_manipulation import CropRegions
from adb_auto_player.models.template_matching import MatchMode, TemplateMatchResult
from adb_auto_player.template_matching import TemplateMatcher

from ._input_mixin import InputMixin


class _UndesiredResultError(Exception):
    """Used for _execute_or_timeout."""

    pass


class TemplateMixin(InputMixin):
    """Template matching, waiting, and tap-until operations."""

    T = TypeVar("T")

    @property
    @abstractmethod
    def template_dir(self) -> Path:
        """Path to the game's template image directory."""
        ...

    def _load_image(
        self,
        template: str | Path,
        grayscale: bool = False,
    ) -> np.ndarray:
        return IO.load_image(
            image_path=self.template_dir / template,
            grayscale=grayscale,
        )

    # TODO: Change this function name.
    # It is the same as template_matching.find_template_match
    def game_find_template_match(
        self,
        template: str | Path,
        match_mode: MatchMode = MatchMode.BEST,
        threshold: ConfidenceValue | None = None,
        grayscale: bool = False,
        crop_regions: CropRegions = CropRegions(),
        screenshot: np.ndarray | None = None,
    ) -> TemplateMatchResult | None:
        """Find a template on the screen.

        Args:
            template (str | Path): Path to the template image.
            match_mode (MatchMode, optional): Defaults to MatchMode.BEST.
            threshold (ConfidenceValue, optional): Image similarity threshold.
            grayscale (bool, optional): Convert to grayscale boolean. Defaults to False.
            crop_regions (CropRegions, optional): Crop percentages.
            screenshot (np.ndarray, optional): Screenshot image. Will fetch screenshot
                if None

        Returns:
            TemplateMatchResult | None
        """
        crop_result = Cropping.crop(
            image=screenshot if screenshot is not None else self.get_screenshot(),
            crop_regions=crop_regions,
        )

        match = TemplateMatcher.find_template_match(
            base_image=crop_result.image,
            template_image=self._load_image(template=template, grayscale=grayscale),
            match_mode=match_mode,
            threshold=threshold or self.default_threshold,
            grayscale=grayscale,
        )

        if match is None:
            return None

        return match.with_offset(crop_result.offset).to_template_match_result(
            template=str(template)
        )

    def find_worst_match(
        self,
        template: str | Path,
        grayscale: bool = False,
        crop_regions: CropRegions = CropRegions(),
        screenshot: np.ndarray | None = None,
    ) -> None | TemplateMatchResult:
        """Find the most different match.

        Args:
            template (str | Path): Path to template image.
            grayscale (bool, optional): Convert to grayscale boolean. Defaults to False.
            crop_regions (CropRegions, optional): Crop percentages.
            screenshot (np.ndarray, optional): Screenshot image. Will fetch screenshot
                if None

        Returns:
            None | TemplateMatchResult: None or Result of worst Match.
        """
        crop_result = Cropping.crop(
            image=screenshot if screenshot is not None else self.get_screenshot(),
            crop_regions=crop_regions,
        )

        result = TemplateMatcher.find_worst_template_match(
            base_image=crop_result.image,
            template_image=self._load_image(template=template, grayscale=grayscale),
            grayscale=grayscale,
        )

        if result is None:
            return None

        return result.with_offset(crop_result.offset).to_template_match_result(
            template=str(template)
        )

    def find_all_template_matches(
        self,
        template: str | Path,
        threshold: ConfidenceValue | None = None,
        grayscale: bool = False,
        crop_regions: CropRegions = CropRegions(),
        min_distance: int = 10,
        screenshot: np.ndarray | None = None,
    ) -> list[TemplateMatchResult]:
        """Find all matches.

        Args:
            template (str | Path): Path to template image.
            threshold (float, optional): Image similarity threshold. Defaults to 0.9.
            grayscale (bool, optional): Convert to grayscale boolean. Defaults to False.
            crop_regions (CropRegions, optional): Crop percentages.
            min_distance (int, optional): Minimum distance between matches.
                Defaults to 10.
            screenshot (np.ndarray, optional): Screenshot image. Will fetch screenshot
                if None

        Returns:
            list[tuple[int, int]]: List of found coordinates.
        """
        crop_result = Cropping.crop(
            image=screenshot if screenshot is not None else self.get_screenshot(),
            crop_regions=crop_regions,
        )

        result = TemplateMatcher.find_all_template_matches(
            base_image=crop_result.image,
            template_image=self._load_image(template=template, grayscale=grayscale),
            threshold=threshold or self.default_threshold,
            grayscale=grayscale,
            min_distance=min_distance,
        )

        return [
            match.with_offset(crop_result.offset).to_template_match_result(
                template=str(template)
            )
            for match in result
        ]

    def find_any_template(
        self,
        templates: list[str],
        match_mode: MatchMode = MatchMode.BEST,
        threshold: ConfidenceValue | None = None,
        grayscale: bool = False,
        crop_regions: CropRegions = CropRegions(),
        screenshot: np.ndarray | None = None,
    ) -> TemplateMatchResult | None:
        """Find any first template on the screen.

        Args:
            templates (list[str]): List of templates to search for.
            match_mode (MatchMode, optional): String enum. Defaults to MatchMode.BEST.
            threshold (float, optional): Image similarity threshold. Defaults to 0.9.
            grayscale (bool, optional): Convert to grayscale boolean. Defaults to False.
            crop_regions (CropRegions, optional): Crop percentages.
            screenshot (np.ndarray, optional): Screenshot image. Will fetch screenshot
                if None

        Returns:
            TemplateMatchResult | None
        """
        screenshot = screenshot if screenshot is not None else self.get_screenshot()

        offset = None
        if crop_regions:
            cropped = Cropping.crop(screenshot, crop_regions)
            screenshot = cropped.image
            offset = cropped.offset

        if grayscale:
            screenshot = Color.to_grayscale(screenshot)

        for template in templates:
            result = self.game_find_template_match(
                template,
                match_mode=match_mode,
                threshold=threshold or self.default_threshold,
                screenshot=screenshot,
                grayscale=grayscale,
            )
            if result is not None:
                if offset:
                    return result.with_offset(offset)
                return result
        return None

    def wait_for_roi_change(
        self,
        start_image: np.ndarray,
        threshold: ConfidenceValue | None = None,
        grayscale: bool = False,
        crop_regions: CropRegions = CropRegions(),
        delay: float = 0.5,
        timeout: float = 30,
        timeout_message: str | None = None,
    ) -> Literal[True]:
        """Waits for a region of interest (ROI) on the screen to change.

        This function monitors a specific region of the screen defined by
        the crop values.
        If the crop values are all set to 0, it will monitor the entire
        screen for changes.
        A change is detected based on a similarity threshold between current and
        previous screen regions.

        Args:
            start_image (np.ndarray): Image to start monitoring.
            threshold (float): Similarity threshold. Defaults to 0.9.
            grayscale (bool): Whether to convert images to grayscale before comparison.
                Defaults to False.
            crop_regions (CropRegions): Crop percentages for trimming the image.
            delay (float): Delay between checks in seconds. Defaults to 0.5.
            timeout (float): Timeout in seconds. Defaults to 30.
            timeout_message (str | None): Custom timeout message. Defaults to None.

        Returns:
            bool: True if the region of interest has changed.

        Raises:
            GameTimeoutError: If no change is detected within the timeout period.
            ValueError: Invalid crop values.
        """
        crop_result = Cropping.crop(image=start_image, crop_regions=crop_regions)

        def roi_changed() -> Literal[True]:
            inner_crop_result = Cropping.crop(
                image=self.get_screenshot(),
                crop_regions=crop_regions,
            )
            if TemplateMatcher.similar_image(
                base_image=crop_result.image,
                template_image=inner_crop_result.image,
                threshold=threshold or self.default_threshold,
                grayscale=grayscale,
            ):
                raise _UndesiredResultError()
            return True

        if timeout_message is None:
            timeout_message = (
                f"Region of Interest has not changed after {timeout} seconds"
            )

        return self._execute_or_timeout(
            roi_changed, delay=delay, timeout=timeout, timeout_message=timeout_message
        )

    def wait_for_template(
        self,
        template: str | Path,
        threshold: ConfidenceValue | None = None,
        grayscale: bool = False,
        crop_regions: CropRegions = CropRegions(),
        delay: float = 0.5,
        timeout: float = 30,
        timeout_message: str | None = None,
    ) -> TemplateMatchResult:
        """Waits for the template to appear in the screen.

        Raises:
            GameTimeoutError: Template not found.
        """

        def find_template() -> TemplateMatchResult:
            result = self.game_find_template_match(
                template,
                threshold=threshold or self.default_threshold,
                grayscale=grayscale,
                crop_regions=crop_regions,
            )
            if result is not None:
                logging.debug(f"wait_for_template: {template} found")
                return result
            raise _UndesiredResultError()

        if timeout_message is None:
            timeout_message = (
                f"Could not find Template: '{template}' after {timeout} seconds"
            )

        return self._execute_or_timeout(
            find_template, delay=delay, timeout=timeout, timeout_message=timeout_message
        )

    def wait_until_template_disappears(
        self,
        template: str | Path,
        threshold: ConfidenceValue | None = None,
        grayscale: bool = False,
        crop_regions: CropRegions = CropRegions(),
        delay: float = 0.5,
        timeout: float = 30,
        timeout_message: str | None = None,
    ) -> None:
        """Waits for the template to disappear from the screen.

        Raises:
            GameTimeoutError: Template still visible.
        """

        def find_best_template() -> None:
            if self.game_find_template_match(
                template,
                threshold=threshold or self.default_threshold,
                grayscale=grayscale,
                crop_regions=crop_regions,
            ):
                raise _UndesiredResultError()
            logging.debug(
                f"wait_until_template_disappears: {template} no longer visible"
            )

        if timeout_message is None:
            timeout_message = (
                f"Template: {template} is still visible after {timeout} seconds"
            )

        self._execute_or_timeout(
            find_best_template,
            delay=delay,
            timeout=timeout,
            timeout_message=timeout_message,
        )

    def wait_for_any_template(
        self,
        templates: list[str],
        threshold: ConfidenceValue | None = None,
        grayscale: bool = False,
        crop_regions: CropRegions = CropRegions(),
        delay: float = 0.5,
        timeout: float = 30,
        timeout_message: str | None = None,
    ) -> TemplateMatchResult:
        """Waits for any template to appear on the screen.

        Raises:
            GameTimeoutError: No template visible.
        """

        def find_template() -> TemplateMatchResult:
            find_template_result = self.find_any_template(
                templates,
                threshold=threshold or self.default_threshold,
                grayscale=grayscale,
                crop_regions=crop_regions,
            )
            if find_template_result:
                return find_template_result
            raise _UndesiredResultError()

        if timeout_message is None:
            timeout_message = (
                f"None of the templates {templates} were found after {timeout} seconds"
            )

        return self._execute_or_timeout(
            find_template, delay=delay, timeout=timeout, timeout_message=timeout_message
        )

    def _tap_till_template_disappears(
        self,
        template: str | Path,
        threshold: ConfidenceValue | None = None,
        grayscale: bool = False,
        crop_regions: CropRegions = CropRegions(),
        tap_delay: float = 10.0,
        sleep_duration: float = 0.5,
        error_message: str | None = None,
    ) -> None:
        max_tap_count = 3
        tap_count = 0
        time_since_last_tap = tap_delay  # force immediate first tap

        while result := self.game_find_template_match(
            template,
            threshold=threshold,
            grayscale=grayscale,
            crop_regions=crop_regions,
        ):
            if tap_count >= max_tap_count:
                message = error_message
                if not message:
                    message = f"Failed to tap: {template}, Template still visible."
                raise GameActionFailedError(message)
            if time_since_last_tap >= tap_delay:
                self.tap(result)
                tap_count += 1
                time_since_last_tap -= (
                    tap_delay  # preserve overflow - more accurate timing
                )
            sleep(sleep_duration)
            time_since_last_tap += sleep_duration

    def _tap_coordinates_till_template_disappears(
        self,
        coordinates: Coordinates,
        template: str | Path,
        threshold: ConfidenceValue | None = None,
        grayscale: bool = False,
        crop_regions: CropRegions | None = None,
        tap_delay: float = 10.0,
        sleep_duration: float = 0.5,
    ) -> None:
        max_tap_count = 3
        tap_count = 0
        time_since_last_tap = tap_delay  # force immediate first tap
        while self.game_find_template_match(
            template=template,
            threshold=threshold,
            grayscale=grayscale,
            crop_regions=(crop_regions if crop_regions else CropRegions()),
        ):
            if tap_count >= max_tap_count:
                message = (
                    f"Failed to tap: {Point(coordinates.x, coordinates.y)}, "
                    f"Template: {template} still visible."
                )
                raise GameActionFailedError(message)
            if time_since_last_tap >= tap_delay:
                self.tap(coordinates)
                tap_count += 1
                time_since_last_tap -= (
                    tap_delay  # preserve overflow - more accurate timing
                )
            sleep(sleep_duration)
            time_since_last_tap += sleep_duration

    def assert_frame_and_input_delay_below_threshold(
        self,
        max_frame_delay: int = 10,
        max_input_delay: int = 80,
    ) -> None:
        """Assert no frame and input lag is below threshold.

        This is meant for bots where fast input/reaction time is needed.

        Args:
            max_frame_delay(int, optional): maximum frame delay in milliseconds.
            max_input_delay(int, optional): maximum input delay in milliseconds.

        Raises:
            AutoPlayerUnrecoverableError: frame or input delay above max allowed value.
        """
        # Debug screenshots add additional IO, we can disable this here because we know
        # the feature needs to be fast if this function is called...

        start_time = perf_counter()
        _ = self.get_screenshot()
        total_time = (perf_counter() - start_time) * 1000
        if total_time > max_frame_delay:
            raise AutoPlayerUnrecoverableError(
                f"Screenshot/Frame delay: {int(total_time)} ms above max frame delay: "
                f"{max_frame_delay} ms exiting..."
            )
        logging.info(f"Screenshot/Frame delay: {int(total_time)} ms")

        total_time = 0.0
        iterations = 10
        for _ in range(iterations):
            start_time = perf_counter()
            self.tap(PointOutsideDisplay(), log=False, non_blocking_sleep_duration=None)
            total_time += (perf_counter() - start_time) * 1000
        average_time = total_time / iterations
        if average_time > max_input_delay:
            raise AutoPlayerUnrecoverableError(
                f"Average input delay: {int(average_time)} ms above max input delay: "
                f"{max_input_delay} ms exiting..."
            )
        logging.info(f"Average input delay: {int(average_time)} ms")

    @lru_cache
    def get_templates_from_dir(self, subdir: str) -> list[str]:
        """Return a list of all files inside a given template subdirectory.

        returns relative paths (e.g. 'power_saving_mode/1.png').
        """
        template_dir = self.template_dir / subdir
        return [
            f"{subdir}/{path.name}" for path in template_dir.iterdir() if path.is_file()
        ]

    @staticmethod
    def _execute_or_timeout(
        operation: "Callable[[], TemplateMixin.T]",
        timeout_message: str,
        delay: float = 0.5,
        timeout: float = 30,
    ) -> "TemplateMixin.T":
        end_time = monotonic() + timeout

        while True:
            try:
                return operation()
            except _UndesiredResultError:
                if monotonic() >= end_time:
                    raise GameTimeoutError(timeout_message)
                sleep(delay)
