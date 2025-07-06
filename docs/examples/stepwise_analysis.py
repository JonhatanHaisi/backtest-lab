"""
Enhanced stepwise analysis example.

This example demonstrates the new stepwise analysis system with signals,
step progression, and plotting capabilities.
"""

import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

# Add the src directory to the path so we can import our modules
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from backtest_lab.analysis import (
    ComposedSignal,
    FuncSignal,
    MatplotlibRenderer,
    PlotManager,
    StepwiseAnalyzer,
    TopBottomSignal,
    create_rsi_signal,
    create_sma_signal,
)
from backtest_lab.data import StockDataLoader

# Constants
DEFAULT_SYMBOL = "PETR4.SA"
DEFAULT_TIMEFRAME = "1d"
SAMPLE_DATA_START = "2020-01-01"
SAMPLE_DATA_END = "2023-12-31"
INITIAL_WINDOW = 100
STEP_SIZE = 20
DEMO_STEPS = 5
RANDOM_SEED = 42

# Sample data generation parameters
SAMPLE_DATA_BASE_PRICE = 100
SAMPLE_DATA_VOLATILITY = 0.02
SAMPLE_DATA_NOISE_RANGE = (-1, 1)
SAMPLE_DATA_HIGH_NOISE = (0, 2)
SAMPLE_DATA_LOW_NOISE = (0, 2)
SAMPLE_DATA_VOLUME_RANGE = (1000000, 10000000)


def load_market_data(symbol: str = DEFAULT_SYMBOL) -> pd.DataFrame:
    """
    Load market data for the specified symbol.

    Args:
        symbol: Stock symbol to load data for

    Returns:
        DataFrame with OHLC data

    Raises:
        ValueError: If data loading fails and sample data cannot be created
    """
    print(f"Loading OHLC data for {symbol}...")
    loader = StockDataLoader()

    try:
        from backtest_lab.data.base import DataFrequency

        market_data = loader.get_data(symbol, frequency=DataFrequency.DAILY)
        data = market_data.data
        print(f"Loaded {len(data)} data points for {symbol}")
        print(f"Date range: {data.index[0]} to {data.index[-1]}")
        return data
    except Exception as e:
        print(f"Error loading data: {e}")
        print("Creating sample data for demonstration...")
        return _create_sample_data()


def _create_sample_data() -> pd.DataFrame:
    """
    Create sample OHLC data for demonstration purposes.

    Returns:
        DataFrame with sample OHLC data
    """
    dates = pd.date_range(start=SAMPLE_DATA_START, end=SAMPLE_DATA_END, freq="D")
    np.random.seed(RANDOM_SEED)

    # Generate realistic OHLC data with proper relationships
    close_prices = SAMPLE_DATA_BASE_PRICE + np.cumsum(
        np.random.randn(len(dates)) * SAMPLE_DATA_VOLATILITY
    )

    # Ensure proper OHLC relationships:
    # high >= max(open, close), low <= min(open, close)
    open_prices = close_prices + np.random.uniform(*SAMPLE_DATA_NOISE_RANGE, len(dates))

    # Calculate high and low with proper constraints
    high_noise = np.random.uniform(*SAMPLE_DATA_HIGH_NOISE, len(dates))
    low_noise = np.random.uniform(*SAMPLE_DATA_LOW_NOISE, len(dates))

    high_prices = np.maximum(open_prices, close_prices) + high_noise
    low_prices = np.minimum(open_prices, close_prices) - low_noise

    volumes = np.random.randint(*SAMPLE_DATA_VOLUME_RANGE, len(dates))

    data = pd.DataFrame(
        {
            "open": open_prices,
            "high": high_prices,
            "low": low_prices,
            "close": close_prices,
            "volume": volumes,
        },
        index=dates,
    )

    print(f"Created {len(data)} sample data points")
    return data


def create_signals() -> List:
    """
    Create a list of technical analysis signals.

    Returns:
        List of signal objects
    """
    print("Creating signals...")

    # 1. Top/Bottom signal
    top_bottom_signal = TopBottomSignal(name="top_bottom", window=10, price_col="close")

    # 2. Moving averages
    sma_20 = create_sma_signal("sma_20", 20)
    sma_50 = create_sma_signal("sma_50", 50)

    # 3. RSI signal
    rsi_signal = create_rsi_signal("rsi_14", 14)

    # 4. Custom signal: Price momentum
    momentum_signal = FuncSignal("momentum_10", _momentum_func)

    # 5. Composed signal: SMA crossover
    sma_crossover = ComposedSignal(
        name="sma_crossover",
        signals=[sma_20, sma_50],
        composition_func=_sma_crossover_func,
    )

    return [
        top_bottom_signal,
        sma_20,
        sma_50,
        rsi_signal,
        momentum_signal,
        sma_crossover,
    ]


def _momentum_func(ohlc: pd.DataFrame, period: int = 10) -> pd.Series:
    """Calculate price momentum over specified period."""
    return ohlc["close"].pct_change(period) * 100


def _sma_crossover_func(signals: Dict[str, pd.Series]) -> pd.Series:
    """
    Detect SMA crossover signals.

    Args:
        signals: Dictionary containing SMA signals

    Returns:
        Series with crossover signals (1=bullish, -1=bearish, 0=neutral)
    """
    sma_20 = signals["sma_20"]
    sma_50 = signals["sma_50"]

    # Calculate crossover
    crossover = pd.Series(0, index=sma_20.index)

    # Bullish crossover (20 crosses above 50)
    bullish = (sma_20 > sma_50) & (sma_20.shift(1) <= sma_50.shift(1))
    crossover[bullish] = 1

    # Bearish crossover (20 crosses below 50)
    bearish = (sma_20 < sma_50) & (sma_20.shift(1) >= sma_50.shift(1))
    crossover[bearish] = -1

    return crossover


def initialize_analyzer(
    data: pd.DataFrame,
    signals: List,
    symbol: str = DEFAULT_SYMBOL,
    timeframe: str = DEFAULT_TIMEFRAME,
) -> StepwiseAnalyzer:
    """
    Initialize the stepwise analyzer with data and signals.

    Args:
        data: OHLC data DataFrame
        signals: List of signal objects
        symbol: Stock symbol
        timeframe: Data timeframe

    Returns:
        Configured StepwiseAnalyzer instance
    """
    print("Initializing stepwise analyzer...")

    analyzer = StepwiseAnalyzer(
        ohlc=data,
        signals=signals,
        initial_window=INITIAL_WINDOW,
        step_size=STEP_SIZE,
        metadata={"symbol": symbol, "timeframe": timeframe},
    )

    print(f"Analyzer initialized with {analyzer.total_steps} initial steps")
    print(f"Can advance: {analyzer.can_advance}")
    print(f"Progress: {analyzer.progress_percentage:.1f}%")

    return analyzer


def demonstrate_step_progression(analyzer: StepwiseAnalyzer) -> None:
    """
    Demonstrate step progression functionality.

    Args:
        analyzer: Configured StepwiseAnalyzer instance
    """
    print("\nDemonstrating step progression...")

    for i in range(DEMO_STEPS):
        if analyzer.can_advance:
            step = analyzer.next_step()
            print(
                f"Step {step.step_index}: {step.data_length} data points, "
                f"current date: {step.current_date.strftime('%Y-%m-%d')}"
            )

            # Show signal values for current date
            current_signals = _get_current_signals(step)
            print(f"  Current signals: {current_signals}")
        else:
            print("  Cannot advance further")
            break


def _get_current_signals(step) -> Dict[str, float]:
    """
    Extract current signal values from a step.

    Args:
        step: Analysis step object

    Returns:
        Dictionary of signal names and their current values
    """
    current_signals = {}
    for signal_name in step.get_signal_names():
        signal_data = step.get_latest_signal_values(signal_name, 1)
        if signal_data is not None and not signal_data.empty:
            current_signals[signal_name] = signal_data.iloc[-1]
    return current_signals


def analyze_current_step(analyzer: StepwiseAnalyzer) -> None:
    """
    Analyze the current step and show signal progressions.

    Args:
        analyzer: Configured StepwiseAnalyzer instance
    """
    print("\nAnalyzing current step...")
    current_step = analyzer.current_step

    if not current_step:
        print("No current step available")
        return

    summary = current_step.summary()
    print(f"Step summary: {summary}")

    # Analyze signal progression
    print("\nAnalyzing signal progression...")
    target_signals = ["sma_20", "rsi_14", "top_bottom"]

    for signal_name in target_signals:
        if signal_name in analyzer.signal_names:
            progression = analyzer.analyze_signal_progression(signal_name)
            print(f"{signal_name} progression: {progression['total_steps']} steps")


def create_plots(analyzer: StepwiseAnalyzer, symbol: str, timeframe: str) -> None:
    """
    Create and save analysis plots.

    Args:
        analyzer: Configured StepwiseAnalyzer instance
        symbol: Stock symbol
        timeframe: Data timeframe
    """
    try:
        print("\nCreating plots...")

        plot_manager = PlotManager(MatplotlibRenderer())
        current_step = analyzer.current_step

        if not current_step:
            print("No current step available for plotting")
            return

        # Plot current step
        fig1 = plot_manager.plot_step(
            current_step,
            signals=["sma_20", "sma_50", "rsi_14"],
            title=f"Current Step Analysis - {symbol}",
            show_markers=True,
        )

        # Save plot
        plot_manager.save_plot(fig1, f"step_analysis_{symbol}_{timeframe}.png")
        print("Saved step analysis plot")

        # Plot signal progression
        steps_for_progression = list(analyzer.get_step_iterator(0, 5))
        fig2 = plot_manager.plot_signal_progression(
            steps_for_progression,
            "rsi_14",
            title=f"RSI Progression - {symbol}",
        )

        plot_manager.save_plot(fig2, f"rsi_progression_{symbol}_{timeframe}.png")
        print("Saved RSI progression plot")

    except ImportError as e:
        print(f"Plotting failed - missing dependency: {e}")
    except Exception as e:
        print(f"Plotting failed: {e}")


def demonstrate_step_comparison(analyzer: StepwiseAnalyzer) -> None:
    """
    Demonstrate step comparison functionality.

    Args:
        analyzer: Configured StepwiseAnalyzer instance
    """
    print("\nDemonstrating step comparison...")

    # Get a few steps for comparison
    steps = list(analyzer.get_step_iterator(0, 3))

    if len(steps) < 2:
        print("Not enough steps for comparison")
        return

    step1, step2 = steps[0], steps[-1]
    print(f"Comparing Step {step1.step_index} vs Step {step2.step_index}")

    # Compare signal values
    target_signals = ["sma_20", "rsi_14"]
    for signal_name in target_signals:
        comparison = step2.compare_with_previous(signal_name)
        if comparison:
            print(f"  {signal_name} comparison: {comparison}")


def demonstrate_navigation(analyzer: StepwiseAnalyzer, data: pd.DataFrame) -> None:
    """
    Demonstrate navigation functionality.

    Args:
        analyzer: Configured StepwiseAnalyzer instance
        data: Original OHLC data
    """
    print("\nDemonstrating navigation...")

    # Jump to specific date
    target_date = data.index[len(data) // 2]  # Middle of data
    step = analyzer.jump_to_date(target_date)

    if step:
        print(f"Jumped to date {target_date.strftime('%Y-%m-%d')}")
        print(f"Step {step.step_index}: {step.data_length} data points")

    # Jump to specific step
    step = analyzer.jump_to_step(10)
    if step:
        print(f"Jumped to step 10: {step.current_date.strftime('%Y-%m-%d')}")


def show_final_summary(analyzer: StepwiseAnalyzer) -> None:
    """
    Show final analysis summary.

    Args:
        analyzer: Configured StepwiseAnalyzer instance
    """
    print("\nFinal Analysis Summary:")
    print("=" * 40)

    summary = analyzer.summary()
    for key, value in summary.items():
        print(f"{key}: {value}")


def main() -> None:
    """Main example function demonstrating stepwise analysis."""
    print("Enhanced Stepwise Analysis Example")
    print("=" * 40)

    # Load data
    data = load_market_data(DEFAULT_SYMBOL)

    # Create signals
    signals = create_signals()

    # Initialize analyzer
    analyzer = initialize_analyzer(data, signals, DEFAULT_SYMBOL, DEFAULT_TIMEFRAME)

    # Demonstrate functionality
    demonstrate_step_progression(analyzer)
    analyze_current_step(analyzer)
    create_plots(analyzer, DEFAULT_SYMBOL, DEFAULT_TIMEFRAME)
    demonstrate_step_comparison(analyzer)
    demonstrate_navigation(analyzer, data)
    show_final_summary(analyzer)

    print("\nExample completed successfully!")


if __name__ == "__main__":
    main()
