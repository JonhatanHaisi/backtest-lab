"""
Plotting manager and backends for the analysis module.

This module provides flexible plotting capabilities for stepwise analysis,
supporting multiple backends and customizable visualizations.
"""

import warnings
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .exceptions import PlotError, PlotRenderError
from .step import Step


class PlotRenderer(ABC):
    """
    Abstract base class for plot rendering backends.

    This allows for pluggable plotting backends (matplotlib, plotly, etc.).
    """

    @abstractmethod
    def create_figure(
        self, figsize: Tuple[int, int] = (12, 8), title: Optional[str] = None
    ) -> Any:
        """
        Create a new figure.

        Args:
            figsize: Figure size (width, height)
            title: Optional figure title

        Returns:
            Figure object
        """
        pass

    @abstractmethod
    def add_candlestick_plot(
        self, fig: Any, ohlc: pd.DataFrame, subplot: int = 1, name: str = "OHLC"
    ) -> Any:
        """
        Add a candlestick plot to the figure.

        Args:
            fig: Figure object
            ohlc: OHLC DataFrame
            subplot: Subplot index
            name: Plot name

        Returns:
            Plot object
        """
        pass

    @abstractmethod
    def add_line_plot(
        self,
        fig: Any,
        data: pd.Series,
        subplot: int = 1,
        name: str = "Line",
        color: Optional[str] = None,
    ) -> Any:
        """
        Add a line plot to the figure.

        Args:
            fig: Figure object
            data: Data series to plot
            subplot: Subplot index
            name: Plot name
            color: Line color

        Returns:
            Plot object
        """
        pass

    @abstractmethod
    def add_scatter_plot(
        self,
        fig: Any,
        data: pd.Series,
        subplot: int = 1,
        name: str = "Scatter",
        color: Optional[str] = None,
        marker: str = "o",
    ) -> Any:
        """
        Add a scatter plot to the figure.

        Args:
            fig: Figure object
            data: Data series to plot
            subplot: Subplot index
            name: Plot name
            color: Marker color
            marker: Marker style

        Returns:
            Plot object
        """
        pass

    @abstractmethod
    def add_marker(
        self,
        fig: Any,
        date: datetime,
        value: float,
        subplot: int = 1,
        marker_type: str = "circle",
        color: str = "red",
        size: int = 8,
    ) -> Any:
        """
        Add a marker to the plot.

        Args:
            fig: Figure object
            date: Date for the marker
            value: Value for the marker
            subplot: Subplot index
            marker_type: Type of marker
            color: Marker color
            size: Marker size

        Returns:
            Marker object
        """
        pass

    @abstractmethod
    def create_subplots(
        self, fig: Any, rows: int, cols: int = 1, shared_x: bool = True
    ) -> List[Any]:
        """
        Create subplots in the figure.

        Args:
            fig: Figure object
            rows: Number of rows
            cols: Number of columns
            shared_x: Whether to share x-axis

        Returns:
            List of subplot objects
        """
        pass

    @abstractmethod
    def show(self, fig: Any):
        """
        Display the figure.

        Args:
            fig: Figure object
        """
        pass

    @abstractmethod
    def save(self, fig: Any, filename: str, dpi: int = 300):
        """
        Save the figure to file.

        Args:
            fig: Figure object
            filename: Output filename
            dpi: Resolution in DPI
        """
        pass


class MatplotlibRenderer(PlotRenderer):
    """Matplotlib implementation of PlotRenderer."""

    def __init__(self):
        """Initialize matplotlib renderer."""
        try:
            import matplotlib.dates as mdates
            import matplotlib.pyplot as plt
            from matplotlib.patches import Rectangle

            self.plt = plt
            self.mdates = mdates
            self.Rectangle = Rectangle

        except ImportError:
            raise PlotError("Matplotlib is required for MatplotlibRenderer")

    def create_figure(
        self, figsize: Tuple[int, int] = (12, 8), title: Optional[str] = None
    ) -> Any:
        """Create a matplotlib figure."""
        fig, ax = self.plt.subplots(figsize=figsize)
        if title:
            fig.suptitle(title)
        return fig

    def add_candlestick_plot(
        self, fig: Any, ohlc: pd.DataFrame, subplot: int = 1, name: str = "OHLC"
    ) -> Any:
        """Add candlestick plot using matplotlib."""
        try:
            from matplotlib.patches import Rectangle
            from matplotlib.dates import date2num

            ax = (
                fig.get_axes()[subplot - 1]
                if len(fig.get_axes()) >= subplot
                else fig.gca()
            )

            # Convert to numeric if needed
            dates = ohlc.index
            # Convert dates to numeric values for matplotlib
            numeric_dates = date2num(dates)
            opens = ohlc["open"].values
            highs = ohlc["high"].values
            lows = ohlc["low"].values
            closes = ohlc["close"].values

            # Create candlesticks
            width = 0.6
            for i, (date_num, open_val, high_val, low_val, close_val) in enumerate(
                zip(numeric_dates, opens, highs, lows, closes)
            ):
                color = "green" if close_val >= open_val else "red"

                # High-low line
                ax.plot([date_num, date_num], [low_val, high_val], color="black", linewidth=1)

                # Body rectangle
                height = abs(close_val - open_val)
                bottom = min(open_val, close_val)
                rect = Rectangle(
                    (date_num, bottom),
                    width,
                    height,
                    facecolor=color,
                    alpha=0.7,
                    edgecolor="black",
                )
                ax.add_patch(rect)

            ax.set_ylabel("Price")
            ax.set_title(name)
            ax.grid(True, alpha=0.3)

            return ax

        except Exception as e:
            raise PlotRenderError(f"Failed to create candlestick plot: {str(e)}")

    def add_line_plot(
        self,
        fig: Any,
        data: pd.Series,
        subplot: int = 1,
        name: str = "Line",
        color: Optional[str] = None,
    ) -> Any:
        """Add line plot to matplotlib figure."""
        ax = (
            fig.get_axes()[subplot - 1] if len(fig.get_axes()) >= subplot else fig.gca()
        )
        line = ax.plot(data.index, data.values, label=name, color=color)
        ax.legend()
        ax.grid(True, alpha=0.3)
        return line

    def add_scatter_plot(
        self,
        fig: Any,
        data: pd.Series,
        subplot: int = 1,
        name: str = "Scatter",
        color: Optional[str] = None,
        marker: str = "o",
    ) -> Any:
        """Add scatter plot to matplotlib figure."""
        ax = (
            fig.get_axes()[subplot - 1] if len(fig.get_axes()) >= subplot else fig.gca()
        )
        scatter = ax.scatter(
            data.index, data.values, label=name, color=color, marker=marker
        )
        ax.legend()
        ax.grid(True, alpha=0.3)
        return scatter

    def add_marker(
        self,
        fig: Any,
        date: datetime,
        value: float,
        subplot: int = 1,
        marker_type: str = "circle",
        color: str = "red",
        size: int = 8,
    ) -> Any:
        """Add marker to matplotlib figure."""
        ax = (
            fig.get_axes()[subplot - 1] if len(fig.get_axes()) >= subplot else fig.gca()
        )
        marker = ax.scatter(
            [date],
            [value],
            s=size * 10,
            c=color,
            marker="o" if marker_type == "circle" else marker_type,
        )
        return marker

    def create_subplots(
        self, fig: Any, rows: int, cols: int = 1, shared_x: bool = True
    ) -> List[Any]:
        """Create subplots in matplotlib figure."""
        fig.clear()
        axes = fig.subplots(rows, cols, sharex=shared_x if shared_x else None)
        return axes if isinstance(axes, list) else [axes]

    def show(self, fig: Any):
        """Display matplotlib figure."""
        self.plt.show()

    def save(self, fig: Any, filename: str, dpi: int = 300):
        """Save matplotlib figure."""
        fig.savefig(filename, dpi=dpi, bbox_inches="tight")


class PlotlyRenderer(PlotRenderer):
    """Plotly implementation of PlotRenderer."""

    def __init__(self):
        """Initialize plotly renderer."""
        try:
            import plotly.graph_objects as go
            import plotly.subplots as sp

            self.go = go
            self.sp = sp

        except ImportError:
            raise PlotError("Plotly is required for PlotlyRenderer")

    def create_figure(
        self, figsize: Tuple[int, int] = (12, 8), title: Optional[str] = None
    ) -> Any:
        """Create a plotly figure."""
        fig = self.go.Figure()
        fig.update_layout(width=figsize[0] * 100, height=figsize[1] * 100, title=title)
        return fig

    def add_candlestick_plot(
        self, fig: Any, ohlc: pd.DataFrame, subplot: int = 1, name: str = "OHLC"
    ) -> Any:
        """Add candlestick plot to plotly figure."""
        candlestick = self.go.Candlestick(
            x=ohlc.index,
            open=ohlc["open"],
            high=ohlc["high"],
            low=ohlc["low"],
            close=ohlc["close"],
            name=name,
        )
        fig.add_trace(candlestick, row=subplot, col=1)
        return candlestick

    def add_line_plot(
        self,
        fig: Any,
        data: pd.Series,
        subplot: int = 1,
        name: str = "Line",
        color: Optional[str] = None,
    ) -> Any:
        """Add line plot to plotly figure."""
        line = self.go.Scatter(
            x=data.index,
            y=data.values,
            mode="lines",
            name=name,
            line=dict(color=color) if color else None,
        )
        fig.add_trace(line, row=subplot, col=1)
        return line

    def add_scatter_plot(
        self,
        fig: Any,
        data: pd.Series,
        subplot: int = 1,
        name: str = "Scatter",
        color: Optional[str] = None,
        marker: str = "circle",
    ) -> Any:
        """Add scatter plot to plotly figure."""
        scatter = self.go.Scatter(
            x=data.index,
            y=data.values,
            mode="markers",
            name=name,
            marker=dict(color=color, symbol=marker) if color else dict(symbol=marker),
        )
        fig.add_trace(scatter, row=subplot, col=1)
        return scatter

    def add_marker(
        self,
        fig: Any,
        date: datetime,
        value: float,
        subplot: int = 1,
        marker_type: str = "circle",
        color: str = "red",
        size: int = 8,
    ) -> Any:
        """Add marker to plotly figure."""
        marker = self.go.Scatter(
            x=[date],
            y=[value],
            mode="markers",
            marker=dict(color=color, symbol=marker_type, size=size),
            showlegend=False,
        )
        fig.add_trace(marker, row=subplot, col=1)
        return marker

    def create_subplots(
        self, fig: Any, rows: int, cols: int = 1, shared_x: bool = True
    ) -> List[Any]:
        """Create subplots in plotly figure."""
        # Create new subplot figure
        subplot_fig = self.sp.make_subplots(
            rows=rows, cols=cols, shared_xaxes=shared_x, vertical_spacing=0.1
        )

        # Copy layout settings
        subplot_fig.update_layout(fig.layout)

        return [subplot_fig]  # Return as list for consistency

    def show(self, fig: Any):
        """Display plotly figure."""
        fig.show()

    def save(self, fig: Any, filename: str, dpi: int = 300):
        """Save plotly figure."""
        if filename.endswith(".html"):
            fig.write_html(filename)
        else:
            fig.write_image(filename, width=dpi * 4, height=dpi * 3)


class PlotManager:
    """
    Manager for creating and customizing plots for stepwise analysis.

    This class provides high-level plotting functionality with support
    for multiple backends and customizable visualizations.
    """

    def __init__(self, renderer: Optional[PlotRenderer] = None):
        """
        Initialize PlotManager.

        Args:
            renderer: Plot renderer backend to use (defaults to matplotlib)
        """
        if renderer is None:
            # Try to use matplotlib by default
            try:
                renderer = MatplotlibRenderer()
            except PlotError:
                try:
                    renderer = PlotlyRenderer()
                except PlotError:
                    raise PlotError(
                        "No plotting backend available (matplotlib or plotly required)"
                    )

        self.renderer = renderer
        self._plot_configs: Dict[str, Dict] = {}

    def configure_plot(self, plot_name: str, config: Dict[str, Any]):
        """
        Configure a plot with specific settings.

        Args:
            plot_name: Name of the plot configuration
            config: Configuration dictionary
        """
        self._plot_configs[plot_name] = config

    def plot_step(
        self,
        step: Step,
        signals: Optional[List[str]] = None,
        title: Optional[str] = None,
        figsize: Tuple[int, int] = (12, 8),
        show_markers: bool = True,
    ) -> Any:
        """
        Plot a single step with OHLC data and signals.

        Args:
            step: Step to plot
            signals: List of signal names to plot (None for all)
            title: Plot title
            figsize: Figure size
            show_markers: Whether to show signal markers

        Returns:
            Figure object
        """
        try:
            # Create figure
            if title is None:
                title = (
                    f"Step {step.step_index} - {step.current_date.strftime('%Y-%m-%d')}"
                )

            fig = self.renderer.create_figure(figsize=figsize, title=title)

            # Determine subplot layout
            signal_names = signals or step.get_signal_names()
            num_subplots = 1 + len(signal_names)  # 1 for OHLC + signals

            if num_subplots > 1:
                axes = self.renderer.create_subplots(fig, num_subplots, shared_x=True)

            # Plot OHLC data
            self.renderer.add_candlestick_plot(fig, step.ohlc, subplot=1, name="OHLC")

            # Plot signals
            for i, signal_name in enumerate(signal_names):
                signal_data = step.get_signal(signal_name)
                if signal_data is not None:
                    subplot_idx = i + 2

                    if isinstance(signal_data, pd.Series):
                        self.renderer.add_line_plot(
                            fig, signal_data, subplot=subplot_idx, name=signal_name
                        )

                        # Add markers for significant values
                        if show_markers:
                            self._add_signal_markers(
                                fig, signal_data, signal_name, subplot_idx
                            )

                    else:
                        # Handle DataFrame signals (plot each column)
                        for col in signal_data.columns:
                            self.renderer.add_line_plot(
                                fig,
                                signal_data[col],
                                subplot=subplot_idx,
                                name=f"{signal_name}_{col}",
                            )

            return fig

        except Exception as e:
            raise PlotRenderError(f"Failed to plot step: {str(e)}")

    def plot_signal_progression(
        self,
        steps: List[Step],
        signal_name: str,
        title: Optional[str] = None,
        figsize: Tuple[int, int] = (12, 6),
    ) -> Any:
        """
        Plot how a signal evolves across multiple steps.

        Args:
            steps: List of steps to analyze
            signal_name: Name of the signal to plot
            title: Plot title
            figsize: Figure size

        Returns:
            Figure object
        """
        try:
            if title is None:
                title = f"Signal Progression: {signal_name}"

            fig = self.renderer.create_figure(figsize=figsize, title=title)

            # Collect signal data from all steps
            for i, step in enumerate(steps):
                signal_data = step.get_signal(signal_name)
                if signal_data is not None:
                    if isinstance(signal_data, pd.Series):
                        # Use different colors for each step
                        color = f"C{i % 10}"  # Cycle through colors
                        self.renderer.add_line_plot(
                            fig,
                            signal_data,
                            name=f"Step {step.step_index}",
                            color=color,
                        )

            return fig

        except Exception as e:
            raise PlotRenderError(f"Failed to plot signal progression: {str(e)}")

    def plot_comparison(
        self,
        step1: Step,
        step2: Step,
        signals: Optional[List[str]] = None,
        title: Optional[str] = None,
        figsize: Tuple[int, int] = (15, 10),
    ) -> Any:
        """
        Plot comparison between two steps.

        Args:
            step1: First step
            step2: Second step
            signals: List of signals to compare
            title: Plot title
            figsize: Figure size

        Returns:
            Figure object
        """
        try:
            if title is None:
                title = f"Step Comparison: {step1.step_index} vs {step2.step_index}"

            fig = self.renderer.create_figure(figsize=figsize, title=title)

            # Get common signals
            signal_names = signals or list(
                set(step1.get_signal_names()) & set(step2.get_signal_names())
            )

            # Create subplots
            num_subplots = 1 + len(signal_names)
            if num_subplots > 1:
                axes = self.renderer.create_subplots(fig, num_subplots, shared_x=True)

            # Plot OHLC comparison
            self.renderer.add_candlestick_plot(
                fig, step1.ohlc, subplot=1, name="Step 1 OHLC"
            )

            # Find overlapping period for comparison
            common_dates = step1.ohlc.index.intersection(step2.ohlc.index)
            if len(common_dates) > 0:
                step2_ohlc_common = step2.ohlc.loc[common_dates]
                # Add step2 as overlay (you might want to modify this based on renderer)

            # Plot signal comparisons
            for i, signal_name in enumerate(signal_names):
                signal1 = step1.get_signal(signal_name)
                signal2 = step2.get_signal(signal_name)

                if signal1 is not None and signal2 is not None:
                    subplot_idx = i + 2

                    if isinstance(signal1, pd.Series) and isinstance(
                        signal2, pd.Series
                    ):
                        self.renderer.add_line_plot(
                            fig,
                            signal1,
                            subplot=subplot_idx,
                            name=f"{signal_name} (Step {step1.step_index})",
                            color="blue",
                        )
                        self.renderer.add_line_plot(
                            fig,
                            signal2,
                            subplot=subplot_idx,
                            name=f"{signal_name} (Step {step2.step_index})",
                            color="red",
                        )

            return fig

        except Exception as e:
            raise PlotRenderError(f"Failed to plot comparison: {str(e)}")

    def _add_signal_markers(
        self, fig: Any, signal_data: pd.Series, signal_name: str, subplot: int
    ):
        """Add markers for significant signal values."""
        try:
            # Add markers for extreme values or specific conditions
            if signal_name.lower() in ["top_bottom", "tops_bottoms"]:
                # Mark tops and bottoms
                tops = signal_data[signal_data == 1]
                bottoms = signal_data[signal_data == -1]

                for date, value in tops.items():
                    self.renderer.add_marker(
                        fig,
                        date,
                        value,
                        subplot=subplot,
                        color="green",
                        marker_type="triangle-up",
                    )

                for date, value in bottoms.items():
                    self.renderer.add_marker(
                        fig,
                        date,
                        value,
                        subplot=subplot,
                        color="red",
                        marker_type="triangle-down",
                    )

            elif "rsi" in signal_name.lower():
                # Mark overbought/oversold levels
                overbought = signal_data[signal_data > 70]
                oversold = signal_data[signal_data < 30]

                for date, value in overbought.items():
                    self.renderer.add_marker(
                        fig,
                        date,
                        value,
                        subplot=subplot,
                        color="red",
                        marker_type="circle",
                    )

                for date, value in oversold.items():
                    self.renderer.add_marker(
                        fig,
                        date,
                        value,
                        subplot=subplot,
                        color="green",
                        marker_type="circle",
                    )

        except Exception as e:
            # Don't fail the entire plot if markers fail
            warnings.warn(f"Failed to add markers for {signal_name}: {str(e)}")

    def save_plot(self, fig: Any, filename: str, dpi: int = 300):
        """
        Save plot to file.

        Args:
            fig: Figure object
            filename: Output filename
            dpi: Resolution in DPI
        """
        try:
            self.renderer.save(fig, filename, dpi=dpi)
        except Exception as e:
            raise PlotRenderError(f"Failed to save plot: {str(e)}")

    def show_plot(self, fig: Any):
        """
        Display plot.

        Args:
            fig: Figure object
        """
        try:
            self.renderer.show(fig)
        except Exception as e:
            raise PlotRenderError(f"Failed to show plot: {str(e)}")

    def set_renderer(self, renderer: PlotRenderer):
        """
        Set a new plot renderer.

        Args:
            renderer: New renderer to use
        """
        self.renderer = renderer

    def get_available_renderers(self) -> List[str]:
        """
        Get list of available renderers.

        Returns:
            List of renderer names
        """
        available = []

        try:
            MatplotlibRenderer()
            available.append("matplotlib")
        except PlotError:
            pass

        try:
            PlotlyRenderer()
            available.append("plotly")
        except PlotError:
            pass

        return available
