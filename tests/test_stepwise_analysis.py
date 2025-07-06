"""
Test the new stepwise analysis system.
"""

import unittest
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from backtest_lab.analysis import (
    StepwiseAnalyzer,
    TopBottomSignal,
    FuncSignal,
    ComposedSignal,
    create_sma_signal,
    create_rsi_signal,
    Step,
    AnalysisError,
    StepError,
    PlotManager,
)


class TestStepwiseAnalysis(unittest.TestCase):
    """Test cases for the stepwise analysis system."""
    
    def setUp(self):
        """Set up test data."""
        # Create sample OHLC data
        np.random.seed(42)
        dates = pd.date_range(start='2020-01-01', end='2020-12-31', freq='D')
        
        # Generate realistic OHLC data with proper relationships
        close_prices = 100 + np.cumsum(np.random.randn(len(dates)) * 0.02)
        
        # Ensure proper OHLC relationships: high >= max(open, close), low <= min(open, close)
        open_prices = close_prices + np.random.uniform(-1, 1, len(dates))
        
        # Calculate high and low with proper constraints
        high_noise = np.random.uniform(0, 2, len(dates))
        low_noise = np.random.uniform(0, 2, len(dates))
        
        high_prices = np.maximum(open_prices, close_prices) + high_noise
        low_prices = np.minimum(open_prices, close_prices) - low_noise
        
        volumes = np.random.randint(1000000, 10000000, len(dates))
        
        self.ohlc = pd.DataFrame({
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': volumes
        }, index=dates)
    
    def test_signal_creation(self):
        """Test signal creation and calculation."""
        # Test TopBottomSignal
        tb_signal = TopBottomSignal("test_tb", window=5)
        result = tb_signal(self.ohlc)
        
        self.assertIsInstance(result, pd.Series)
        self.assertEqual(len(result), len(self.ohlc))
        self.assertTrue(all(val in [-1, 0, 1] for val in result.values))
        
        # Test FuncSignal
        def simple_func(ohlc):
            return ohlc['close'].rolling(window=10).mean()
        
        func_signal = FuncSignal("test_func", simple_func)
        result = func_signal(self.ohlc)
        
        self.assertIsInstance(result, pd.Series)
        self.assertEqual(len(result), len(self.ohlc))
        
        # Test utility functions
        sma_signal = create_sma_signal("sma_20", 20)
        result = sma_signal(self.ohlc)
        
        self.assertIsInstance(result, pd.Series)
        self.assertEqual(len(result), len(self.ohlc))
        
        rsi_signal = create_rsi_signal("rsi_14", 14)
        result = rsi_signal(self.ohlc)
        
        self.assertIsInstance(result, pd.Series)
        self.assertEqual(len(result), len(self.ohlc))
        self.assertTrue(all(0 <= val <= 100 for val in result.dropna().values))
    
    def test_composed_signal(self):
        """Test composed signal functionality."""
        sma_20 = create_sma_signal("sma_20", 20)
        sma_50 = create_sma_signal("sma_50", 50)
        
        def crossover_func(signals):
            sma_20_vals = signals['sma_20']
            sma_50_vals = signals['sma_50']
            return sma_20_vals > sma_50_vals
        
        crossover_signal = ComposedSignal(
            "crossover",
            [sma_20, sma_50],
            crossover_func
        )
        
        result = crossover_signal(self.ohlc)
        self.assertIsInstance(result, pd.Series)
        self.assertEqual(len(result), len(self.ohlc))
    
    def test_step_creation(self):
        """Test Step class functionality."""
        # Create a step
        step = Step(
            ohlc=self.ohlc.iloc[:100],
            step_index=0,
            signals={'test_signal': pd.Series(range(100), index=self.ohlc.index[:100])},
            metadata={'test': 'value'}
        )
        
        self.assertEqual(step.step_index, 0)
        self.assertEqual(step.data_length, 100)
        self.assertTrue(step.has_signal('test_signal'))
        self.assertFalse(step.has_signal('nonexistent'))
        self.assertEqual(step.get_metadata_value('test'), 'value')
        self.assertEqual(step.get_metadata_value('nonexistent', 'default'), 'default')
        
        # Test immutability
        with self.assertRaises(StepError):
            step.step_index = 1
    
    def test_stepwise_analyzer_initialization(self):
        """Test StepwiseAnalyzer initialization."""
        signals = [
            TopBottomSignal("tb", window=5),
            create_sma_signal("sma_20", 20)
        ]
        
        analyzer = StepwiseAnalyzer(
            ohlc=self.ohlc,
            signals=signals,
            initial_window=50,
            step_size=10
        )
        
        self.assertEqual(analyzer.total_steps, 1)
        self.assertTrue(analyzer.can_advance)
        self.assertEqual(len(analyzer.signal_names), 2)
        self.assertIn('tb', analyzer.signal_names)
        self.assertIn('sma_20', analyzer.signal_names)
        
        # Test current step
        current_step = analyzer.current_step
        self.assertIsNotNone(current_step)
        self.assertEqual(current_step.step_index, 0)
        self.assertEqual(current_step.data_length, 50)
    
    def test_step_progression(self):
        """Test step progression functionality."""
        signals = [create_sma_signal("sma_10", 10)]
        
        analyzer = StepwiseAnalyzer(
            ohlc=self.ohlc,
            signals=signals,
            initial_window=50,
            step_size=10
        )
        
        initial_steps = analyzer.total_steps
        
        # Advance to next step
        next_step = analyzer.next_step()
        self.assertIsNotNone(next_step)
        self.assertEqual(next_step.step_index, 1)
        self.assertEqual(next_step.data_length, 60)
        self.assertEqual(analyzer.total_steps, initial_steps + 1)
        
        # Test navigation
        step = analyzer.jump_to_step(0)
        self.assertIsNotNone(step)
        self.assertEqual(step.step_index, 0)
        
        # Test date navigation
        target_date = self.ohlc.index[100]
        step = analyzer.jump_to_date(target_date)
        self.assertIsNotNone(step)
    
    def test_signal_management(self):
        """Test adding and removing signals."""
        analyzer = StepwiseAnalyzer(
            ohlc=self.ohlc,
            signals=[],
            initial_window=50,
            step_size=10
        )
        
        self.assertEqual(len(analyzer.signal_names), 0)
        
        # Add a signal
        new_signal = create_sma_signal("sma_20", 20)
        analyzer.add_signal(new_signal)
        
        self.assertEqual(len(analyzer.signal_names), 1)
        self.assertIn('sma_20', analyzer.signal_names)
        
        # Remove a signal
        analyzer.remove_signal('sma_20')
        self.assertEqual(len(analyzer.signal_names), 0)
        self.assertNotIn('sma_20', analyzer.signal_names)
    
    def test_signal_caching(self):
        """Test signal caching functionality."""
        signal = create_sma_signal("sma_20", 20)
        
        # Calculate signal twice
        result1 = signal(self.ohlc)
        result2 = signal(self.ohlc)
        
        # Results should be identical (from cache)
        pd.testing.assert_series_equal(result1, result2)
        
        # Clear cache and recalculate
        signal.clear_cache()
        result3 = signal(self.ohlc)
        
        # Should still be identical
        pd.testing.assert_series_equal(result1, result3)
    
    def test_error_handling(self):
        """Test error handling in various scenarios."""
        # Test invalid OHLC data
        invalid_ohlc = pd.DataFrame({'a': [1, 2, 3]})
        
        with self.assertRaises(AnalysisError):
            StepwiseAnalyzer(ohlc=invalid_ohlc, signals=[], initial_window=10)
        
        # Test invalid signal
        def bad_func(ohlc):
            raise ValueError("Test error")
        
        bad_signal = FuncSignal("bad", bad_func)
        
        with self.assertRaises(AnalysisError):
            bad_signal(self.ohlc)
    
    def test_analysis_features(self):
        """Test analysis features like signal progression."""
        signals = [create_sma_signal("sma_20", 20)]
        
        analyzer = StepwiseAnalyzer(
            ohlc=self.ohlc,
            signals=signals,
            initial_window=50,
            step_size=10
        )
        
        # Generate a few steps
        for _ in range(3):
            if analyzer.can_advance:
                analyzer.next_step()
        
        # Analyze signal progression
        progression = analyzer.analyze_signal_progression('sma_20')
        self.assertIn('signal_name', progression)
        self.assertIn('total_steps', progression)
        self.assertEqual(progression['signal_name'], 'sma_20')
        self.assertGreater(progression['total_steps'], 0)
    
    def test_plot_manager_initialization(self):
        """Test PlotManager initialization."""
        # This test will check basic initialization
        # Full plotting tests would require matplotlib/plotly
        try:
            plot_manager = PlotManager()
            self.assertIsNotNone(plot_manager)
            self.assertIsNotNone(plot_manager.renderer)
        except Exception as e:
            # Expected if no plotting backend is available
            self.assertIn("plotting backend", str(e).lower())


if __name__ == '__main__':
    unittest.main()
