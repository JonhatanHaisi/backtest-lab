"""
Signal base classes and implementations for the analysis module.
"""

import hashlib
import json
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Union

import pandas as pd

from .exceptions import SignalCalculationError


class Signal(ABC):
    """Abstract base class for all signals."""

    def __init__(self, name: str, cache_window: Optional[int] = None):
        """Initialize a signal."""
        self.name = name
        self.cache_window = cache_window
        self._cache: Dict[str, Any] = {}
        self._dependencies: List[str] = []

    @abstractmethod
    def calculate(self, ohlc: pd.DataFrame, **kwargs) -> Union[pd.Series, pd.DataFrame]:
        """Calculate the signal values for the given OHLC data."""
        pass

    def get_cache_key(self, ohlc: pd.DataFrame, **kwargs) -> str:
        """Generate a cache key for the given parameters."""
        data_info = {
            "shape": ohlc.shape,
            "first_date": str(ohlc.index[0]) if len(ohlc) > 0 else None,
            "last_date": str(ohlc.index[-1]) if len(ohlc) > 0 else None,
            "params": kwargs,
        }
        key_str = json.dumps(data_info, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get_cached_result(
        self, cache_key: str
    ) -> Optional[Union[pd.Series, pd.DataFrame]]:
        """Get cached result for the given cache key."""
        return self._cache.get(cache_key)

    def cache_result(self, cache_key: str, result: Union[pd.Series, pd.DataFrame]):
        """Cache a calculation result."""
        self._cache[cache_key] = result

        # Simple cache cleanup based on size
        if self.cache_window and len(self._cache) > self.cache_window:
            # Remove oldest entries (simple FIFO)
            keys_to_remove = list(self._cache.keys())[: -self.cache_window]
            for key in keys_to_remove:
                del self._cache[key]

    def clear_cache(self):
        """Clear all cached results."""
        self._cache.clear()

    def add_dependency(self, signal_name: str):
        """Add a dependency on another signal."""
        if signal_name not in self._dependencies:
            self._dependencies.append(signal_name)

    def get_dependencies(self) -> List[str]:
        """Get list of signal dependencies."""
        return self._dependencies.copy()

    def validate_data(self, ohlc: pd.DataFrame):
        """Validate input OHLC data."""
        required_columns = ["open", "high", "low", "close"]
        missing_columns = [col for col in required_columns if col not in ohlc.columns]

        if missing_columns:
            raise SignalCalculationError(
                f"Missing required columns in OHLC data: {missing_columns}"
            )

        if ohlc.empty:
            raise SignalCalculationError("OHLC data is empty")

    def __call__(self, ohlc: pd.DataFrame, **kwargs) -> Union[pd.Series, pd.DataFrame]:
        """Calculate signal with caching support."""
        try:
            self.validate_data(ohlc)

            # Check cache first
            cache_key = self.get_cache_key(ohlc, **kwargs)
            cached_result = self.get_cached_result(cache_key)

            if cached_result is not None:
                return cached_result

            # Calculate and cache result
            result = self.calculate(ohlc, **kwargs)
            self.cache_result(cache_key, result)

            return result

        except Exception as e:
            raise SignalCalculationError(
                f"Error calculating signal '{self.name}': {str(e)}"
            )


class TopBottomSignal(Signal):
    """Signal that identifies tops and bottoms in price data."""

    def __init__(
        self,
        name: str = "top_bottom",
        window: int = 5,
        price_col: str = "close",
        cache_window: Optional[int] = None,
    ):
        """Initialize TopBottomSignal."""
        super().__init__(name, cache_window)
        self.window = window
        self.price_col = price_col

    def calculate(self, ohlc: pd.DataFrame, **kwargs) -> pd.Series:
        """Calculate top/bottom signals."""
        window = kwargs.get("window", self.window)
        price_col = kwargs.get("price_col", self.price_col)

        prices = ohlc[price_col]
        result = pd.Series(0, index=prices.index)

        # Simple peak/trough detection using rolling max/min
        rolling_max = prices.rolling(window=window, center=True).max()
        rolling_min = prices.rolling(window=window, center=True).min()

        # Mark tops and bottoms
        result[prices == rolling_max] = 1
        result[prices == rolling_min] = -1

        return result


class ComposedSignal(Signal):
    """Signal that combines multiple other signals."""

    def __init__(
        self,
        name: str,
        signals: List[Signal],
        composition_func: Callable[
            [Dict[str, Union[pd.Series, pd.DataFrame]]], Union[pd.Series, pd.DataFrame]
        ],
        cache_window: Optional[int] = None,
    ):
        """Initialize ComposedSignal."""
        super().__init__(name, cache_window)
        self.signals = signals
        self.composition_func = composition_func

        # Add dependencies
        for signal in signals:
            self.add_dependency(signal.name)

    def calculate(self, ohlc: pd.DataFrame, **kwargs) -> Union[pd.Series, pd.DataFrame]:
        """Calculate composed signal."""
        # Calculate all component signals
        signal_results = {}
        for signal in self.signals:
            signal_results[signal.name] = signal(ohlc, **kwargs)

        # Apply composition function
        return self.composition_func(signal_results)


class FuncSignal(Signal):
    """Signal that wraps a user-defined function."""

    def __init__(
        self,
        name: str,
        func: Callable[[pd.DataFrame], Union[pd.Series, pd.DataFrame]],
        cache_window: Optional[int] = None,
    ):
        """Initialize FuncSignal."""
        super().__init__(name, cache_window)
        self.func = func

    def calculate(self, ohlc: pd.DataFrame, **kwargs) -> Union[pd.Series, pd.DataFrame]:
        """Calculate signal using the wrapped function."""
        return self.func(ohlc, **kwargs)


# Utility functions for creating common signals
def create_sma_signal(name: str, period: int, price_col: str = "close") -> FuncSignal:
    """Create a Simple Moving Average signal."""

    def sma_func(ohlc: pd.DataFrame, **kwargs) -> pd.Series:
        p = kwargs.get("period", period)
        col = kwargs.get("price_col", price_col)
        return ohlc[col].rolling(window=p).mean()

    return FuncSignal(name, sma_func)


def create_rsi_signal(
    name: str, period: int = 14, price_col: str = "close"
) -> FuncSignal:
    """Create a Relative Strength Index signal."""

    def rsi_func(ohlc: pd.DataFrame, **kwargs) -> pd.Series:
        p = kwargs.get("period", period)
        col = kwargs.get("price_col", price_col)

        prices = ohlc[col]
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=p).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=p).mean()

        rs = gain / loss
        return 100 - (100 / (1 + rs))

    return FuncSignal(name, rsi_func)
