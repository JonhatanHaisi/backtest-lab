"""
Main stepwise analysis wrapper for the analysis module.

This module provides the StepwiseAnalyzer class which orchestrates the stepwise
progression through OHLC data with signal application and analysis.
"""

from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional, Union

import pandas as pd

from .exceptions import AnalysisError, DataValidationError, StepProgressionError
from .signals import Signal
from .step import Step


class StepwiseAnalyzer:
    """
    Main wrapper for stepwise analysis of OHLC data with signals.

    This class manages the progression through OHLC data, applying signals
    at each step and maintaining the analysis state.
    """

    def __init__(
        self,
        ohlc: pd.DataFrame,
        signals: Optional[List[Signal]] = None,
        initial_window: int = 50,
        step_size: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize StepwiseAnalyzer.

        Args:
            ohlc: Full OHLC DataFrame to analyze
            signals: List of signals to apply at each step
            initial_window: Initial window size for the first step
            step_size: Number of periods to advance in each step
            metadata: Additional metadata for the analysis

        Raises:
            AnalysisError: If initialization fails
            DataValidationError: If OHLC data is invalid
        """
        try:
            self._validate_ohlc(ohlc)

            self._full_ohlc = ohlc.copy()
            self._signals = signals or []
            self._initial_window = initial_window
            self._step_size = step_size
            self._metadata = metadata or {}

            # Analysis state
            self._current_step: Optional[Step] = None
            self._steps: List[Step] = []
            self._current_index = 0
            self._signal_registry: Dict[str, Signal] = {}

            # Register signals
            for signal in self._signals:
                self._signal_registry[signal.name] = signal

            # Initialize first step
            self._initialize_first_step()

        except Exception as e:
            raise AnalysisError(f"Failed to initialize StepwiseAnalyzer: {str(e)}")

    def _validate_ohlc(self, ohlc: pd.DataFrame):
        """
        Validate OHLC data.

        Args:
            ohlc: OHLC DataFrame to validate

        Raises:
            DataValidationError: If validation fails
        """
        if ohlc.empty:
            raise DataValidationError("OHLC data cannot be empty")

        required_columns = ["open", "high", "low", "close"]
        missing_columns = [col for col in required_columns if col not in ohlc.columns]

        if missing_columns:
            raise DataValidationError(
                f"Missing required OHLC columns: {missing_columns}"
            )

        if not isinstance(ohlc.index, pd.DatetimeIndex):
            raise DataValidationError("OHLC data must have a DatetimeIndex")

        if not ohlc.index.is_monotonic_increasing:
            raise DataValidationError("OHLC data must be sorted by date")

    def _initialize_first_step(self):
        """Initialize the first step of the analysis."""
        if len(self._full_ohlc) < self._initial_window:
            raise StepProgressionError(
                f"Insufficient data: need at least {self._initial_window} periods, "
                f"got {len(self._full_ohlc)}"
            )

        # Create initial OHLC slice
        initial_ohlc = self._full_ohlc.iloc[: self._initial_window]

        # Apply signals
        signals_results = self._apply_signals(initial_ohlc)

        # Create first step
        step_metadata = {
            "window_size": self._initial_window,
            "is_initial_step": True,
            **self._metadata,
        }

        self._current_step = Step(
            ohlc=initial_ohlc,
            step_index=0,
            signals=signals_results,
            metadata=step_metadata,
        )

        self._steps.append(self._current_step)
        self._current_index = self._initial_window

    def _apply_signals(
        self, ohlc: pd.DataFrame
    ) -> Dict[str, Union[pd.Series, pd.DataFrame]]:
        """
        Apply all signals to the given OHLC data.

        Args:
            ohlc: OHLC DataFrame

        Returns:
            Dictionary of signal results

        Raises:
            AnalysisError: If signal application fails
        """
        results = {}

        for signal in self._signals:
            try:
                results[signal.name] = signal(ohlc)
            except Exception as e:
                raise AnalysisError(f"Failed to apply signal '{signal.name}': {str(e)}")

        return results

    def add_signal(self, signal: Signal, recalculate: bool = True):
        """
        Add a new signal to the analysis.

        Args:
            signal: Signal to add
            recalculate: Whether to recalculate all existing steps

        Raises:
            AnalysisError: If signal addition fails
        """
        if signal.name in self._signal_registry:
            raise AnalysisError(f"Signal '{signal.name}' already exists")

        self._signals.append(signal)
        self._signal_registry[signal.name] = signal

        if recalculate:
            self._recalculate_all_steps()

    def remove_signal(self, signal_name: str, recalculate: bool = True):
        """
        Remove a signal from the analysis.

        Args:
            signal_name: Name of the signal to remove
            recalculate: Whether to recalculate all existing steps

        Raises:
            AnalysisError: If signal removal fails
        """
        if signal_name not in self._signal_registry:
            raise AnalysisError(f"Signal '{signal_name}' not found")

        # Remove from lists
        self._signals = [s for s in self._signals if s.name != signal_name]
        del self._signal_registry[signal_name]

        if recalculate:
            self._recalculate_all_steps()

    def _recalculate_all_steps(self):
        """Recalculate all existing steps with current signals."""
        if not self._steps:
            return

        # Clear cache for all signals
        for signal in self._signals:
            signal.clear_cache()

        # Recalculate each step
        new_steps = []

        for i, step in enumerate(self._steps):
            # Get the OHLC data for this step
            if i == 0:
                ohlc = self._full_ohlc.iloc[: self._initial_window]
            else:
                end_idx = self._initial_window + i * self._step_size
                ohlc = self._full_ohlc.iloc[:end_idx]

            # Apply signals
            signals_results = self._apply_signals(ohlc)

            # Create new step
            previous_step = new_steps[-1] if new_steps else None
            new_step = Step(
                ohlc=ohlc,
                step_index=i,
                signals=signals_results,
                metadata=step.metadata,
                previous_step=previous_step,
            )

            new_steps.append(new_step)

        self._steps = new_steps
        self._current_step = self._steps[-1] if self._steps else None

    def next_step(self) -> Optional[Step]:
        """
        Advance to the next step in the analysis.

        Returns:
            Next step or None if no more data available

        Raises:
            StepProgressionError: If step progression fails
        """
        # Check if we have more data
        next_index = self._current_index + self._step_size
        if next_index >= len(self._full_ohlc):
            return None

        try:
            # Create OHLC slice for next step
            next_ohlc = self._full_ohlc.iloc[:next_index]

            # Apply signals
            signals_results = self._apply_signals(next_ohlc)

            # Create next step
            step_metadata = {
                "window_size": len(next_ohlc),
                "step_size": self._step_size,
                **self._metadata,
            }

            next_step = Step(
                ohlc=next_ohlc,
                step_index=len(self._steps),
                signals=signals_results,
                metadata=step_metadata,
                previous_step=self._current_step,
            )

            self._steps.append(next_step)
            self._current_step = next_step
            self._current_index = next_index

            return next_step

        except Exception as e:
            raise StepProgressionError(f"Failed to advance to next step: {str(e)}")

    def previous_step(self) -> Optional[Step]:
        """
        Go back to the previous step.

        Returns:
            Previous step or None if at first step
        """
        if len(self._steps) <= 1:
            return None

        # Remove current step and go back
        self._steps.pop()
        self._current_step = self._steps[-1] if self._steps else None
        self._current_index = (
            self._initial_window + (len(self._steps) - 1) * self._step_size
        )

        return self._current_step

    def jump_to_step(self, step_index: int) -> Optional[Step]:
        """
        Jump to a specific step index.

        Args:
            step_index: Index of the step to jump to

        Returns:
            Step at the specified index or None if invalid

        Raises:
            StepProgressionError: If jump fails
        """
        if step_index < 0:
            return None

        # If step already exists, return it
        if step_index < len(self._steps):
            self._current_step = self._steps[step_index]
            self._current_index = self._initial_window + step_index * self._step_size
            return self._current_step

        # Calculate steps needed
        steps_needed = step_index - len(self._steps) + 1

        # Check if we have enough data
        required_index = self._initial_window + step_index * self._step_size
        if required_index >= len(self._full_ohlc):
            return None

        # Generate steps up to the target
        for _ in range(steps_needed):
            if self.next_step() is None:
                break

        return self._current_step

    def jump_to_date(self, target_date: datetime) -> Optional[Step]:
        """
        Jump to the step that includes the specified date.

        Args:
            target_date: Target date to jump to

        Returns:
            Step containing the target date or None if not found
        """
        if (
            target_date < self._full_ohlc.index[0]
            or target_date > self._full_ohlc.index[-1]
        ):
            return None

        # Find the index of the target date
        try:
            target_idx = self._full_ohlc.index.get_loc(target_date)
        except KeyError:
            # Date not found, find the nearest date
            target_idx = self._full_ohlc.index.get_indexer(
                [target_date], method="nearest"
            )[0]

        # Calculate which step this corresponds to
        if target_idx < self._initial_window:
            step_index = 0
        else:
            step_index = (target_idx - self._initial_window) // self._step_size + 1

        return self.jump_to_step(step_index)

    def get_step_iterator(
        self, start_step: int = 0, end_step: Optional[int] = None
    ) -> Iterator[Step]:
        """
        Get an iterator over steps in the specified range.

        Args:
            start_step: Starting step index
            end_step: Ending step index (None for all remaining steps)

        Yields:
            Step objects in the specified range
        """
        current_step_idx = len(self._steps) - 1 if self._steps else -1

        # Generate steps up to end_step if needed
        if end_step is not None:
            while current_step_idx < end_step:
                next_step = self.next_step()
                if next_step is None:
                    break
                current_step_idx += 1

        # Yield steps in range
        for i in range(start_step, min(len(self._steps), end_step or len(self._steps))):
            yield self._steps[i]

    def get_signal_history(
        self, signal_name: str, start_step: int = 0, end_step: Optional[int] = None
    ) -> List[Union[pd.Series, pd.DataFrame]]:
        """
        Get the history of a signal across multiple steps.

        Args:
            signal_name: Name of the signal
            start_step: Starting step index
            end_step: Ending step index (None for all available steps)

        Returns:
            List of signal values across steps
        """
        history = []

        for step in self.get_step_iterator(start_step, end_step):
            signal_value = step.get_signal(signal_name)
            if signal_value is not None:
                history.append(signal_value)

        return history

    def analyze_signal_progression(self, signal_name: str) -> Dict[str, Any]:
        """
        Analyze how a signal changes across steps.

        Args:
            signal_name: Name of the signal to analyze

        Returns:
            Dictionary with progression analysis
        """
        if signal_name not in self._signal_registry:
            raise AnalysisError(f"Signal '{signal_name}' not found")

        history = self.get_signal_history(signal_name)
        if not history:
            return {"error": "No signal history available"}

        # Analyze progression
        analysis = {
            "signal_name": signal_name,
            "total_steps": len(history),
            "data_growth": [len(sig) for sig in history],
            "value_ranges": [],
        }

        for i, signal_data in enumerate(history):
            if isinstance(signal_data, pd.Series):
                value_range = {
                    "step": i,
                    "min": signal_data.min(),
                    "max": signal_data.max(),
                    "mean": signal_data.mean(),
                    "std": signal_data.std(),
                }
            else:
                # For DataFrame signals, analyze each column
                value_range = {"step": i, "columns": {}}
                for col in signal_data.columns:
                    value_range["columns"][col] = {
                        "min": signal_data[col].min(),
                        "max": signal_data[col].max(),
                        "mean": signal_data[col].mean(),
                        "std": signal_data[col].std(),
                    }

            analysis["value_ranges"].append(value_range)

        return analysis

    def reset_to_beginning(self):
        """Reset the analysis to the beginning (first step)."""
        if self._steps:
            self._current_step = self._steps[0]
            self._current_index = self._initial_window

    def reset_completely(self):
        """Reset the analysis completely, clearing all steps."""
        self._steps.clear()
        self._current_step = None
        self._current_index = 0

        # Clear signal caches
        for signal in self._signals:
            signal.clear_cache()

        # Reinitialize
        self._initialize_first_step()

    @property
    def current_step(self) -> Optional[Step]:
        """Get the current step."""
        return self._current_step

    @property
    def total_steps(self) -> int:
        """Get the total number of steps generated."""
        return len(self._steps)

    @property
    def current_step_index(self) -> int:
        """Get the current step index."""
        return len(self._steps) - 1 if self._steps else -1

    @property
    def signal_names(self) -> List[str]:
        """Get list of all signal names."""
        return list(self._signal_registry.keys())

    @property
    def can_advance(self) -> bool:
        """Check if we can advance to the next step."""
        next_index = self._current_index + self._step_size
        return next_index < len(self._full_ohlc)

    @property
    def progress_percentage(self) -> float:
        """Get the current progress as a percentage."""
        if not self._steps:
            return 0.0

        return (self._current_index / len(self._full_ohlc)) * 100

    def summary(self) -> Dict[str, Any]:
        """
        Get a summary of the analysis state.

        Returns:
            Dictionary with analysis summary
        """
        return {
            "total_data_points": len(self._full_ohlc),
            "initial_window": self._initial_window,
            "step_size": self._step_size,
            "total_steps": self.total_steps,
            "current_step_index": self.current_step_index,
            "current_data_length": len(self._current_step.ohlc)
            if self._current_step
            else 0,
            "progress_percentage": self.progress_percentage,
            "can_advance": self.can_advance,
            "signals": self.signal_names,
            "date_range": {
                "start": self._full_ohlc.index[0],
                "end": self._full_ohlc.index[-1],
                "current": self._current_step.current_date
                if self._current_step
                else None,
            },
        }

    def __len__(self) -> int:
        """Get the total number of steps."""
        return len(self._steps)

    def __iter__(self) -> Iterator[Step]:
        """Iterate over all steps."""
        return iter(self._steps)

    def __getitem__(self, index: int) -> Step:
        """Get a step by index."""
        return self._steps[index]
