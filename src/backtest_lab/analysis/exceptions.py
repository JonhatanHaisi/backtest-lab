"""
Custom exceptions for the analysis module.
"""


class AnalysisError(Exception):
    """Base exception for all analysis-related errors."""

    pass


class SignalCalculationError(AnalysisError):
    """Exception raised when signal calculation encounters an error."""

    pass


class SignalDependencyError(AnalysisError):
    """Exception raised when signal dependencies are not met or invalid."""

    pass


class StepError(AnalysisError):
    """Exception raised when step creation or manipulation fails."""

    pass


class StepProgressionError(AnalysisError):
    """Exception raised when stepwise progression encounters an error."""

    pass


class PlotError(AnalysisError):
    """Exception raised when plotting operations fail."""

    pass


class PlotRenderError(AnalysisError):
    """Exception raised when plot rendering fails."""

    pass


class DataValidationError(AnalysisError):
    """Exception raised when data validation fails."""

    pass
