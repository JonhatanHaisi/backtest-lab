"""
Step class for the stepwise analysis system.
"""

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from .exceptions import DataValidationError, StepError


class Step:
    """Immutable step in the stepwise analysis representing OHLC data with applied signals."""

    def __init__(
        self,
        ohlc: pd.DataFrame,
        step_index: int,
        signals: Optional[Dict[str, Union[pd.Series, pd.DataFrame]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        previous_step: Optional["Step"] = None,
    ):
        """Initialize a Step."""
        try:
            self._validate_ohlc(ohlc)

            # Store immutable copies
            self._ohlc = ohlc.copy()
            self._step_index = step_index
            self._signals = signals.copy() if signals else {}
            self._metadata = metadata.copy() if metadata else {}
            self._previous_step = previous_step
            self._created_at = datetime.now()

            # Freeze the step (make it immutable)
            self._frozen = True

        except Exception as e:
            raise StepError(f"Failed to create step: {str(e)}")

    def _validate_ohlc(self, ohlc: pd.DataFrame):
        """Validate OHLC data."""
        if ohlc.empty:
            raise DataValidationError("OHLC data cannot be empty")

        required_columns = ["open", "high", "low", "close"]
        missing_columns = [col for col in required_columns if col not in ohlc.columns]

        if missing_columns:
            raise DataValidationError(
                f"Missing required OHLC columns: {missing_columns}"
            )

        # Check for invalid OHLC relationships
        invalid_ohlc = (
            (ohlc["high"] < ohlc["low"])
            | (ohlc["high"] < ohlc["open"])
            | (ohlc["high"] < ohlc["close"])
            | (ohlc["low"] > ohlc["open"])
            | (ohlc["low"] > ohlc["close"])
        )

        if invalid_ohlc.any():
            raise DataValidationError(
                f"Invalid OHLC relationships found at {invalid_ohlc.sum()} rows"
            )

    @property
    def ohlc(self) -> pd.DataFrame:
        """Get OHLC data (immutable copy)."""
        return self._ohlc.copy()

    @property
    def step_index(self) -> int:
        """Get step index."""
        return self._step_index

    @property
    def signals(self) -> Dict[str, Union[pd.Series, pd.DataFrame]]:
        """Get signals (immutable copy)."""
        return deepcopy(self._signals)

    @property
    def metadata(self) -> Dict[str, Any]:
        """Get metadata (immutable copy)."""
        return deepcopy(self._metadata)

    @property
    def previous_step(self) -> Optional["Step"]:
        """Get reference to previous step."""
        return self._previous_step

    @property
    def created_at(self) -> datetime:
        """Get creation timestamp."""
        return self._created_at

    @property
    def current_date(self) -> datetime:
        """Get the current date (last date in OHLC data)."""
        return self._ohlc.index[-1]

    @property
    def data_length(self) -> int:
        """Get the number of data points in this step."""
        return len(self._ohlc)

    def get_signal(self, signal_name: str) -> Optional[Union[pd.Series, pd.DataFrame]]:
        """
        Get a specific signal result.

        Args:
            signal_name: Name of the signal to retrieve

        Returns:
            Signal result or None if not found
        """
        return deepcopy(self._signals.get(signal_name))

    def has_signal(self, signal_name: str) -> bool:
        """
        Check if a signal exists in this step.

        Args:
            signal_name: Name of the signal to check

        Returns:
            True if signal exists, False otherwise
        """
        return signal_name in self._signals

    def get_signal_names(self) -> List[str]:
        """
        Get list of all signal names in this step.

        Returns:
            List of signal names
        """
        return list(self._signals.keys())

    def get_metadata_value(self, key: str, default: Any = None) -> Any:
        """
        Get a metadata value.

        Args:
            key: Metadata key
            default: Default value if key not found

        Returns:
            Metadata value or default
        """
        return self._metadata.get(key, default)

    def get_price_slice(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Get a slice of OHLC data for a specific date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Sliced OHLC DataFrame
        """
        ohlc = self._ohlc

        if start_date is not None:
            ohlc = ohlc[ohlc.index >= start_date]

        if end_date is not None:
            ohlc = ohlc[ohlc.index <= end_date]

        return ohlc.copy()

    def get_signal_slice(
        self,
        signal_name: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Optional[Union[pd.Series, pd.DataFrame]]:
        """
        Get a slice of signal data for a specific date range.

        Args:
            signal_name: Name of the signal
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Sliced signal data or None if signal not found
        """
        signal_data = self._signals.get(signal_name)
        if signal_data is None:
            return None

        if start_date is not None:
            signal_data = signal_data[signal_data.index >= start_date]

        if end_date is not None:
            signal_data = signal_data[signal_data.index <= end_date]

        return signal_data.copy()

    def get_latest_values(self, n: int = 1) -> pd.DataFrame:
        """
        Get the latest N rows of OHLC data.

        Args:
            n: Number of latest rows to retrieve

        Returns:
            Latest OHLC data
        """
        return self._ohlc.tail(n).copy()

    def get_latest_signal_values(
        self, signal_name: str, n: int = 1
    ) -> Optional[Union[pd.Series, pd.DataFrame]]:
        """
        Get the latest N values of a signal.

        Args:
            signal_name: Name of the signal
            n: Number of latest values to retrieve

        Returns:
            Latest signal values or None if signal not found
        """
        signal_data = self._signals.get(signal_name)
        if signal_data is None:
            return None

        return signal_data.tail(n).copy()

    def compare_with_previous(self, signal_name: str) -> Optional[Dict[str, Any]]:
        """
        Compare a signal with its values in the previous step.

        Args:
            signal_name: Name of the signal to compare

        Returns:
            Dictionary with comparison results or None if no previous step
        """
        if self._previous_step is None:
            return None

        current_signal = self._signals.get(signal_name)
        previous_signal = self._previous_step.get_signal(signal_name)

        if current_signal is None or previous_signal is None:
            return None

        # Find common dates
        common_dates = current_signal.index.intersection(previous_signal.index)
        if len(common_dates) == 0:
            return None

        # Compare values
        current_values = current_signal.loc[common_dates]
        previous_values = previous_signal.loc[common_dates]

        if isinstance(current_values, pd.Series):
            changes = current_values - previous_values
            return {
                "changed_values": changes[changes != 0],
                "total_changes": (changes != 0).sum(),
                "max_change": changes.abs().max(),
                "mean_change": changes.mean(),
            }
        else:
            # For DataFrame signals, return column-wise comparison
            comparison = {}
            for col in current_values.columns:
                if col in previous_values.columns:
                    changes = current_values[col] - previous_values[col]
                    comparison[col] = {
                        "changed_values": changes[changes != 0],
                        "total_changes": (changes != 0).sum(),
                        "max_change": changes.abs().max(),
                        "mean_change": changes.mean(),
                    }
            return comparison

    def summary(self) -> Dict[str, Any]:
        """
        Get a summary of this step.

        Returns:
            Dictionary with step summary information
        """
        return {
            "step_index": self._step_index,
            "data_length": self.data_length,
            "current_date": self.current_date,
            "date_range": {"start": self._ohlc.index[0], "end": self._ohlc.index[-1]},
            "signals": list(self._signals.keys()),
            "metadata_keys": list(self._metadata.keys()),
            "has_previous_step": self._previous_step is not None,
            "created_at": self._created_at,
        }

    def __len__(self) -> int:
        """Get the number of data points in this step."""
        return len(self._ohlc)

    def __str__(self) -> str:
        """String representation of the step."""
        return (
            f"Step {self._step_index}: {self.data_length} data points, "
            f"{len(self._signals)} signals, current date: {self.current_date}"
        )

    def __repr__(self) -> str:
        """Detailed representation of the step."""
        return (
            f"Step(index={self._step_index}, data_length={self.data_length}, "
            f"signals={list(self._signals.keys())}, "
            f"current_date={self.current_date})"
        )

    def __setattr__(self, name: str, value: Any):
        """Prevent modification after freezing."""
        if hasattr(self, "_frozen") and self._frozen:
            raise StepError("Step objects are immutable and cannot be modified")
        super().__setattr__(name, value)
