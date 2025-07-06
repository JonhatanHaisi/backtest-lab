"""
Analysis module for stepwise OHLC data analysis with signals and plotting.

This module provides a comprehensive framework for analyzing OHLC data
in a stepwise manner, with support for custom signals, caching, and
flexible plotting capabilities.
"""

# Core exceptions
from .exceptions import (
    AnalysisError,
    DataValidationError,
    PlotError,
    PlotRenderError,
    SignalCalculationError,
    SignalDependencyError,
    StepError,
    StepProgressionError,
)

# Plotting system
from .plotting import MatplotlibRenderer, PlotlyRenderer, PlotManager, PlotRenderer

# Signal classes and utilities
from .signals import (
    ComposedSignal,
    FuncSignal,
    Signal,
    TopBottomSignal,
    create_rsi_signal,
    create_sma_signal,
)

# Step class for immutable analysis snapshots
from .step import Step

# Main wrapper for stepwise analysis
from .wrapper import StepwiseAnalyzer

__all__ = [
    # Exceptions
    "AnalysisError",
    "SignalCalculationError",
    "SignalDependencyError",
    "StepError",
    "StepProgressionError",
    "PlotError",
    "PlotRenderError",
    "DataValidationError",
    # Signals
    "Signal",
    "TopBottomSignal",
    "ComposedSignal",
    "FuncSignal",
    "create_sma_signal",
    "create_rsi_signal",
    # Step
    "Step",
    # Wrapper
    "StepwiseAnalyzer",
    # Plotting
    "PlotRenderer",
    "MatplotlibRenderer",
    "PlotlyRenderer",
    "PlotManager",
]
