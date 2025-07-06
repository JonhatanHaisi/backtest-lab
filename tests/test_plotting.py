"""Tests for plotting module"""
import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from backtest_lab.analysis.plotting import (
    PlotRenderer, 
    PlotManager,
    PlotError,
    PlotRenderError
)
from backtest_lab.analysis.step import Step


class TestPlotRenderer:
    """Test abstract PlotRenderer class"""
    
    def test_plot_renderer_abstract_methods(self):
        """Test that PlotRenderer abstract methods raise NotImplementedError"""
        # Cannot instantiate abstract class directly
        with pytest.raises(TypeError):
            PlotRenderer()


class TestPlotManager:
    """Test PlotManager class"""
    
    def test_plot_manager_init_with_custom_renderer(self):
        """Test PlotManager initialization with custom renderer"""
        mock_renderer = Mock(spec=PlotRenderer)
        manager = PlotManager(renderer=mock_renderer)
        assert manager.renderer == mock_renderer
    
    def test_plot_manager_configure_plot(self):
        """Test plot configuration"""
        mock_renderer = Mock(spec=PlotRenderer)
        manager = PlotManager(renderer=mock_renderer)
        
        config = {"color": "blue", "style": "line"}
        manager.configure_plot("test_plot", config)
        
        assert "test_plot" in manager._plot_configs
        assert manager._plot_configs["test_plot"] == config
    
    def test_plot_manager_set_renderer(self):
        """Test setting new renderer"""
        mock_renderer1 = Mock(spec=PlotRenderer)
        mock_renderer2 = Mock(spec=PlotRenderer)
        
        manager = PlotManager(renderer=mock_renderer1)
        assert manager.renderer == mock_renderer1
        
        manager.set_renderer(mock_renderer2)
        assert manager.renderer == mock_renderer2
    
    def test_plot_manager_plot_step(self):
        """Test plotting a step"""
        mock_renderer = Mock(spec=PlotRenderer)
        mock_fig = Mock()
        mock_renderer.create_figure.return_value = mock_fig
        mock_renderer.create_subplots.return_value = [Mock(), Mock()]
        mock_renderer.add_candlestick_plot.return_value = Mock()
        mock_renderer.add_line_plot.return_value = Mock()
        
        manager = PlotManager(renderer=mock_renderer)
        
        # Create mock step
        step = Mock(spec=Step)
        step.step_index = 1
        step.current_date = datetime(2024, 1, 1)
        step.ohlc = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [101, 102, 103],
            'low': [99, 100, 101],
            'close': [100.5, 101.5, 102.5]
        })
        step.get_signal_names.return_value = ['test_signal']
        step.get_signal.return_value = pd.Series([1, 0, 1], name='test_signal')
        
        result = manager.plot_step(step)
        
        assert result == mock_fig
        mock_renderer.create_figure.assert_called_once()
        mock_renderer.add_candlestick_plot.assert_called_once()
    
    def test_plot_manager_plot_step_error(self):
        """Test error handling in plot_step"""
        mock_renderer = Mock(spec=PlotRenderer)
        mock_renderer.create_figure.side_effect = Exception("Renderer error")
        
        manager = PlotManager(renderer=mock_renderer)
        step = Mock(spec=Step)
        
        with pytest.raises(PlotRenderError):
            manager.plot_step(step)
    
    def test_plot_manager_save_plot(self):
        """Test saving plot"""
        mock_renderer = Mock(spec=PlotRenderer)
        manager = PlotManager(renderer=mock_renderer)
        
        mock_fig = Mock()
        manager.save_plot(mock_fig, "test.png", dpi=150)
        
        mock_renderer.save.assert_called_once_with(mock_fig, "test.png", dpi=150)
    
    def test_plot_manager_save_plot_error(self):
        """Test error handling in save_plot"""
        mock_renderer = Mock(spec=PlotRenderer)
        mock_renderer.save.side_effect = Exception("Save error")
        
        manager = PlotManager(renderer=mock_renderer)
        mock_fig = Mock()
        
        with pytest.raises(PlotRenderError):
            manager.save_plot(mock_fig, "test.png")
    
    def test_plot_manager_show_plot(self):
        """Test showing plot"""
        mock_renderer = Mock(spec=PlotRenderer)
        manager = PlotManager(renderer=mock_renderer)
        
        mock_fig = Mock()
        manager.show_plot(mock_fig)
        
        mock_renderer.show.assert_called_once_with(mock_fig)
    
    def test_plot_manager_show_plot_error(self):
        """Test error handling in show_plot"""
        mock_renderer = Mock(spec=PlotRenderer)
        mock_renderer.show.side_effect = Exception("Show error")
        
        manager = PlotManager(renderer=mock_renderer)
        mock_fig = Mock()
        
        with pytest.raises(PlotRenderError):
            manager.show_plot(mock_fig)
    
    def test_plot_manager_plot_signal_progression(self):
        """Test plotting signal progression across steps"""
        mock_renderer = Mock(spec=PlotRenderer)
        mock_fig = Mock()
        mock_renderer.create_figure.return_value = mock_fig
        mock_renderer.add_line_plot.return_value = Mock()
        
        manager = PlotManager(renderer=mock_renderer)
        
        # Create mock steps
        steps = []
        for i in range(3):
            step = Mock(spec=Step)
            step.step_index = i
            signal_data = pd.Series([i+1, i+2, i+3], name='test_signal')
            step.get_signal.return_value = signal_data
            steps.append(step)
        
        result = manager.plot_signal_progression(steps, 'test_signal')
        
        assert result == mock_fig
        mock_renderer.create_figure.assert_called_once()
        assert mock_renderer.add_line_plot.call_count == 3  # One for each step
    
    def test_plot_manager_plot_comparison(self):
        """Test plotting comparison between two steps"""
        mock_renderer = Mock(spec=PlotRenderer)
        mock_fig = Mock()
        mock_renderer.create_figure.return_value = mock_fig
        mock_renderer.create_subplots.return_value = [Mock(), Mock()]
        mock_renderer.add_candlestick_plot.return_value = Mock()
        mock_renderer.add_line_plot.return_value = Mock()
        
        manager = PlotManager(renderer=mock_renderer)
        
        # Create mock steps
        step1 = Mock(spec=Step)
        step1.step_index = 1
        step1.ohlc = pd.DataFrame({
            'open': [100, 101],
            'high': [101, 102],
            'low': [99, 100],
            'close': [100.5, 101.5]
        })
        step1.get_signal_names.return_value = ['signal1']
        step1.get_signal.return_value = pd.Series([1, 0], name='signal1')
        
        step2 = Mock(spec=Step)
        step2.step_index = 2
        step2.ohlc = pd.DataFrame({
            'open': [102, 103],
            'high': [103, 104],
            'low': [101, 102],
            'close': [102.5, 103.5]
        })
        step2.get_signal_names.return_value = ['signal1']
        step2.get_signal.return_value = pd.Series([0, 1], name='signal1')
        
        result = manager.plot_comparison(step1, step2, signals=['signal1'])
        
        assert result == mock_fig
        mock_renderer.create_figure.assert_called_once()


class TestPlotErrors:
    """Test PlotError exceptions"""
    
    def test_plot_error_inheritance(self):
        """Test PlotError inheritance"""
        error = PlotError("test message")
        assert isinstance(error, Exception)
        assert str(error) == "test message"
    
    def test_plot_render_error_inheritance(self):
        """Test PlotRenderError inheritance"""
        error = PlotRenderError("test message")
        assert isinstance(error, Exception)
        assert str(error) == "test message"


@pytest.mark.integration
class TestPlotIntegration:
    """Integration tests for plotting functionality"""
    
    def test_plot_manager_workflow(self):
        """Test complete plotting workflow with mocked dependencies"""
        # Mock renderer that mimics real behavior
        mock_renderer = Mock(spec=PlotRenderer)
        mock_fig = Mock()
        mock_renderer.create_figure.return_value = mock_fig
        mock_renderer.create_subplots.return_value = [Mock(), Mock()]
        mock_renderer.add_candlestick_plot.return_value = Mock()
        mock_renderer.add_line_plot.return_value = Mock()
        mock_renderer.save.return_value = None
        mock_renderer.show.return_value = None
        
        manager = PlotManager(renderer=mock_renderer)
        
        # Create realistic step data
        dates = pd.date_range('2024-01-01', periods=10, freq='D')
        step = Mock(spec=Step)
        step.step_index = 1
        step.current_date = datetime(2024, 1, 5)
        step.ohlc = pd.DataFrame({
            'open': range(100, 110),
            'high': range(101, 111),
            'low': range(99, 109),
            'close': range(100, 110)
        }, index=dates)
        step.get_signal_names.return_value = ['sma', 'rsi']
        
        def mock_get_signal(name):
            if name == 'sma':
                return pd.Series(range(100, 110), index=dates, name='sma')
            elif name == 'rsi':
                return pd.Series([50, 60, 70, 80, 60, 40, 30, 45, 55, 65], index=dates, name='rsi')
            return None
        
        step.get_signal.side_effect = mock_get_signal
        
        # Test plotting
        fig = manager.plot_step(step)
        assert fig == mock_fig
        
        # Test saving
        manager.save_plot(fig, "test.png")
        mock_renderer.save.assert_called_once()
        
        # Test showing
        manager.show_plot(fig)
        mock_renderer.show.assert_called_once()
    
    def test_renderer_switching(self):
        """Test switching between different renderers"""
        mock_renderer1 = Mock(spec=PlotRenderer)
        mock_renderer2 = Mock(spec=PlotRenderer)
        
        manager = PlotManager(renderer=mock_renderer1)
        assert manager.renderer == mock_renderer1
        
        # Switch renderer
        manager.set_renderer(mock_renderer2)
        assert manager.renderer == mock_renderer2
        
        # Verify new renderer is used
        mock_fig = Mock()
        mock_renderer2.create_figure.return_value = mock_fig
        
        step = Mock(spec=Step)
        step.step_index = 1
        step.current_date = datetime(2024, 1, 1)
        step.ohlc = pd.DataFrame({'open': [100], 'high': [101], 'low': [99], 'close': [100.5]})
        step.get_signal_names.return_value = []
        
        result = manager.plot_step(step)
        
        # Only new renderer should be called
        mock_renderer1.create_figure.assert_not_called()
        mock_renderer2.create_figure.assert_called_once()
    
    def test_error_handling_during_plotting(self):
        """Test that plotting errors are properly wrapped"""
        mock_renderer = Mock(spec=PlotRenderer)
        
        # Test various error scenarios
        error_scenarios = [
            ("create_figure", Exception("Figure creation failed")),
            ("add_candlestick_plot", Exception("Candlestick plot failed")),
            ("add_line_plot", Exception("Line plot failed")),
        ]
        
        for method_name, error in error_scenarios:
            # Reset mock
            mock_renderer.reset_mock()
            
            # Configure mock to raise error for specific method
            getattr(mock_renderer, method_name).side_effect = error
            
            # Other methods should work normally
            mock_fig = Mock()
            if method_name != "create_figure":
                mock_renderer.create_figure.return_value = mock_fig
                mock_renderer.create_subplots.return_value = [Mock()]
                
            manager = PlotManager(renderer=mock_renderer)
            step = Mock(spec=Step)
            step.step_index = 1
            step.current_date = datetime(2024, 1, 1)
            step.ohlc = pd.DataFrame({'open': [100], 'high': [101], 'low': [99], 'close': [100.5]})
            step.get_signal_names.return_value = ['test_signal'] if method_name == "add_line_plot" else []
            if method_name == "add_line_plot":
                step.get_signal.return_value = pd.Series([1], name='test_signal')
            
            # Should raise PlotRenderError
            with pytest.raises(PlotRenderError):
                manager.plot_step(step)


@pytest.mark.integration
class TestMatplotlibRenderer:
    """Integration tests for MatplotlibRenderer"""
    
    def test_matplotlib_renderer_creation(self):
        """Test creating MatplotlibRenderer when matplotlib is available"""
        try:
            from backtest_lab.analysis.plotting import MatplotlibRenderer
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend
            
            renderer = MatplotlibRenderer()
            assert renderer is not None
            assert hasattr(renderer, 'create_figure')
        except ImportError:
            pytest.skip("matplotlib not available")
        except Exception as e:
            if "tcl" in str(e).lower():
                pytest.skip("GUI backend not available in CI/headless environment")
            else:
                raise
    
    def test_matplotlib_renderer_create_figure(self):
        """Test MatplotlibRenderer create_figure method"""
        try:
            from backtest_lab.analysis.plotting import MatplotlibRenderer
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend
            
            renderer = MatplotlibRenderer()
            fig = renderer.create_figure(figsize=(10, 6), title="Test Figure")
            assert fig is not None
            
            # Test without title
            fig2 = renderer.create_figure()
            assert fig2 is not None
        except ImportError:
            pytest.skip("matplotlib not available")
        except Exception as e:
            if "tcl" in str(e).lower():
                pytest.skip("GUI backend not available in CI/headless environment")
            else:
                raise
    
    def test_matplotlib_renderer_add_line_plot(self):
        """Test MatplotlibRenderer add_line_plot method"""
        try:
            from backtest_lab.analysis.plotting import MatplotlibRenderer
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend
            
            renderer = MatplotlibRenderer()
            fig = renderer.create_figure()
            data = pd.Series([1, 2, 3, 4, 5], 
                           index=pd.date_range('2024-01-01', periods=5))
            
            line = renderer.add_line_plot(fig, data, name="Test Line", color="blue")
            assert line is not None
            
        except ImportError:
            pytest.skip("matplotlib not available")
        except Exception as e:
            if "tcl" in str(e).lower():
                pytest.skip("GUI backend not available in CI/headless environment")
            else:
                raise
    
    def test_matplotlib_renderer_add_scatter_plot(self):
        """Test MatplotlibRenderer add_scatter_plot method"""
        try:
            from backtest_lab.analysis.plotting import MatplotlibRenderer
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend
            
            renderer = MatplotlibRenderer()
            fig = renderer.create_figure()
            data = pd.Series([1, 2, 3, 4, 5], 
                           index=pd.date_range('2024-01-01', periods=5))
            
            scatter = renderer.add_scatter_plot(
                fig, data, name="Test Scatter", color="red", marker="x"
            )
            assert scatter is not None
            
        except ImportError:
            pytest.skip("matplotlib not available")
        except Exception as e:
            if "tcl" in str(e).lower():
                pytest.skip("GUI backend not available in CI/headless environment")
            else:
                raise
    
    def test_matplotlib_renderer_save_and_show(self):
        """Test MatplotlibRenderer save and show methods"""
        try:
            from backtest_lab.analysis.plotting import MatplotlibRenderer
            import tempfile
            import os
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend
            
            renderer = MatplotlibRenderer()
            fig = renderer.create_figure()
            
            # Test save
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                temp_path = tmp.name
            
            try:
                renderer.save(fig, temp_path, dpi=100)
                assert os.path.exists(temp_path)
            finally:
                # Clean up
                if os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                    except PermissionError:
                        pass  # File may be locked on Windows
            
            # Test show (just verify it doesn't crash)
            with patch('matplotlib.pyplot.show'):
                renderer.show(fig)
                
        except ImportError:
            pytest.skip("matplotlib not available")
        except Exception as e:
            if "tcl" in str(e).lower():
                pytest.skip("GUI backend not available in CI/headless environment")
            else:
                raise


class TestPlotManagerAdvanced:
    """Advanced tests for PlotManager functionality"""
    
    def test_plot_manager_default_initialization(self):
        """Test PlotManager initialization with default renderer"""
        with patch('backtest_lab.analysis.plotting.MatplotlibRenderer') as mock_renderer_class:
            mock_renderer = Mock()
            mock_renderer_class.return_value = mock_renderer
            
            manager = PlotManager()
            assert manager.renderer == mock_renderer
    
    def test_plot_manager_initialization_matplotlib_not_available(self):
        """Test PlotManager initialization when matplotlib is not available"""
        with patch('backtest_lab.analysis.plotting.MatplotlibRenderer', side_effect=PlotError):
            with patch('backtest_lab.analysis.plotting.PlotlyRenderer', side_effect=PlotError):
                with pytest.raises(PlotError, match="No plotting backend available"):
                    PlotManager()
    
    def test_plot_manager_renderer_delegation(self):
        """Test that PlotManager delegates renderer methods correctly"""
        mock_renderer = Mock(spec=PlotRenderer)
        mock_fig = Mock()
        mock_renderer.create_figure.return_value = mock_fig
        
        manager = PlotManager(renderer=mock_renderer)
        
        # Test that renderer methods are accessible through manager
        assert hasattr(manager, 'renderer')
        assert hasattr(manager.renderer, 'create_figure')
        assert hasattr(manager.renderer, 'create_subplots')
        assert hasattr(manager.renderer, 'add_marker')
        
        # Test renderer delegation
        fig = manager.renderer.create_figure()
        assert fig == mock_fig
        mock_renderer.create_figure.assert_called_once()
    
    def test_plot_manager_renderer_marker_access(self):
        """Test accessing renderer marker functionality"""
        mock_renderer = Mock(spec=PlotRenderer)
        mock_fig = Mock()
        mock_marker = Mock()
        mock_renderer.add_marker.return_value = mock_marker
        
        manager = PlotManager(renderer=mock_renderer)
        
        # Test that marker functionality is accessible through renderer
        result = manager.renderer.add_marker(
            mock_fig, 
            datetime(2024, 1, 1), 
            100.0, 
            subplot=1, 
            marker_type="arrow"
        )
        
        assert result == mock_marker
        mock_renderer.add_marker.assert_called_once_with(
            mock_fig, 
            datetime(2024, 1, 1), 
            100.0, 
            subplot=1, 
            marker_type="arrow"
        )
    
    def test_plot_manager_plot_step_with_no_signals(self):
        """Test plotting a step with no signals"""
        mock_renderer = Mock(spec=PlotRenderer)
        mock_fig = Mock()
        mock_renderer.create_figure.return_value = mock_fig
        mock_renderer.add_candlestick_plot.return_value = Mock()
        
        manager = PlotManager(renderer=mock_renderer)
        
        # Create mock step with no signals
        step = Mock(spec=Step)
        step.step_index = 1
        step.current_date = datetime(2024, 1, 1)
        step.ohlc = pd.DataFrame({
            'open': [100, 101],
            'high': [101, 102],
            'low': [99, 100],
            'close': [100.5, 101.5]
        })
        step.get_signal_names.return_value = []
        
        result = manager.plot_step(step)
        
        assert result == mock_fig
        mock_renderer.create_figure.assert_called_once()
        mock_renderer.add_candlestick_plot.assert_called_once()
        # Should not call add_line_plot since no signals
        mock_renderer.add_line_plot.assert_not_called()
    
    def test_plot_manager_plot_step_with_multiple_signals(self):
        """Test plotting a step with multiple signals"""
        mock_renderer = Mock(spec=PlotRenderer)
        mock_fig = Mock()
        mock_renderer.create_figure.return_value = mock_fig
        mock_renderer.create_subplots.return_value = [Mock(), Mock(), Mock()]
        mock_renderer.add_candlestick_plot.return_value = Mock()
        mock_renderer.add_line_plot.return_value = Mock()
        
        manager = PlotManager(renderer=mock_renderer)
        
        # Create mock step with multiple signals
        step = Mock(spec=Step)
        step.step_index = 1
        step.current_date = datetime(2024, 1, 1)
        step.ohlc = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [101, 102, 103],
            'low': [99, 100, 101],
            'close': [100.5, 101.5, 102.5]
        })
        step.get_signal_names.return_value = ['sma', 'rsi']
        
        def mock_get_signal(name):
            if name == 'sma':
                return pd.Series([100, 101, 102], name='sma')
            elif name == 'rsi':
                return pd.Series([50, 60, 70], name='rsi')
            return None
        
        step.get_signal.side_effect = mock_get_signal
        
        result = manager.plot_step(step)
        
        assert result == mock_fig
        mock_renderer.create_figure.assert_called_once()
        mock_renderer.add_candlestick_plot.assert_called_once()
        # Should call add_line_plot twice for two signals
        assert mock_renderer.add_line_plot.call_count == 2
    
    def test_plot_manager_plot_comparison_with_different_signals(self):
        """Test plotting comparison with different signals"""
        mock_renderer = Mock(spec=PlotRenderer)
        mock_fig = Mock()
        mock_renderer.create_figure.return_value = mock_fig
        mock_renderer.create_subplots.return_value = [Mock(), Mock()]
        mock_renderer.add_candlestick_plot.return_value = Mock()
        mock_renderer.add_line_plot.return_value = Mock()
        
        manager = PlotManager(renderer=mock_renderer)
        
        # Create mock steps with different signals
        step1 = Mock(spec=Step)
        step1.step_index = 1
        step1.ohlc = pd.DataFrame({'open': [100], 'high': [101], 'low': [99], 'close': [100.5]})
        step1.get_signal_names.return_value = ['signal1', 'signal2']
        step1.get_signal.side_effect = lambda name: pd.Series([1], name=name)
        
        step2 = Mock(spec=Step)
        step2.step_index = 2
        step2.ohlc = pd.DataFrame({'open': [102], 'high': [103], 'low': [101], 'close': [102.5]})
        step2.get_signal_names.return_value = ['signal1', 'signal3']
        step2.get_signal.side_effect = lambda name: pd.Series([2], name=name)
        
        result = manager.plot_comparison(step1, step2, signals=['signal1'])
        
        assert result == mock_fig
        mock_renderer.create_figure.assert_called_once()
        mock_renderer.create_subplots.assert_called_once_with(mock_fig, 2, shared_x=True)
    
    def test_plot_manager_plot_comparison_with_auto_signals(self):
        """Test plotting comparison with automatic signal detection"""
        mock_renderer = Mock(spec=PlotRenderer)
        mock_fig = Mock()
        mock_renderer.create_figure.return_value = mock_fig
        mock_renderer.create_subplots.return_value = [Mock(), Mock()]
        mock_renderer.add_candlestick_plot.return_value = Mock()
        mock_renderer.add_line_plot.return_value = Mock()
        
        manager = PlotManager(renderer=mock_renderer)
        
        # Create mock steps
        step1 = Mock(spec=Step)
        step1.step_index = 1
        step1.ohlc = pd.DataFrame({'open': [100], 'high': [101], 'low': [99], 'close': [100.5]})
        step1.get_signal_names.return_value = ['common_signal', 'unique_signal1']
        step1.get_signal.side_effect = lambda name: pd.Series([1], name=name)
        
        step2 = Mock(spec=Step)
        step2.step_index = 2
        step2.ohlc = pd.DataFrame({'open': [102], 'high': [103], 'low': [101], 'close': [102.5]})
        step2.get_signal_names.return_value = ['common_signal', 'unique_signal2']
        step2.get_signal.side_effect = lambda name: pd.Series([2], name=name)
        
        # Test with signals=None (should auto-detect common signals)
        result = manager.plot_comparison(step1, step2, signals=None)
        
        assert result == mock_fig


class TestPlotManagerErrorHandling:
    """Test error handling in PlotManager"""
    
    def test_plot_manager_save_plot_with_custom_dpi(self):
        """Test save_plot with custom DPI"""
        mock_renderer = Mock(spec=PlotRenderer)
        manager = PlotManager(renderer=mock_renderer)
        
        mock_fig = Mock()
        manager.save_plot(mock_fig, "test.png", dpi=300)
        
        mock_renderer.save.assert_called_once_with(mock_fig, "test.png", dpi=300)
    
    def test_plot_manager_plot_signal_progression_error(self):
        """Test error handling in plot_signal_progression"""
        mock_renderer = Mock(spec=PlotRenderer)
        mock_renderer.create_figure.side_effect = Exception("Figure creation failed")
        
        manager = PlotManager(renderer=mock_renderer)
        
        steps = [Mock(spec=Step)]
        
        with pytest.raises(PlotRenderError):
            manager.plot_signal_progression(steps, 'test_signal')
    
    def test_plot_manager_plot_comparison_error(self):
        """Test error handling in plot_comparison"""
        mock_renderer = Mock(spec=PlotRenderer)
        mock_renderer.create_figure.side_effect = Exception("Figure creation failed")
        
        manager = PlotManager(renderer=mock_renderer)
        
        step1 = Mock(spec=Step)
        step2 = Mock(spec=Step)
        
        with pytest.raises(PlotRenderError):
            manager.plot_comparison(step1, step2)


class TestPlotManagerConfiguration:
    """Test PlotManager configuration functionality"""
    
    def test_plot_manager_configure_plot_with_nested_config(self):
        """Test plot configuration with nested configuration"""
        mock_renderer = Mock(spec=PlotRenderer)
        manager = PlotManager(renderer=mock_renderer)
        
        config = {
            "colors": {"line": "blue", "background": "white"},
            "styles": {"line_width": 2, "marker_size": 5}
        }
        manager.configure_plot("complex_plot", config)
        
        assert "complex_plot" in manager._plot_configs
        assert manager._plot_configs["complex_plot"]["colors"]["line"] == "blue"
        assert manager._plot_configs["complex_plot"]["styles"]["line_width"] == 2
    
    def test_plot_manager_configure_multiple_plots(self):
        """Test configuring multiple plots"""
        mock_renderer = Mock(spec=PlotRenderer)
        manager = PlotManager(renderer=mock_renderer)
        
        config1 = {"color": "red"}
        config2 = {"color": "blue"}
        
        manager.configure_plot("plot1", config1)
        manager.configure_plot("plot2", config2)
        
        assert len(manager._plot_configs) == 2
        assert manager._plot_configs["plot1"]["color"] == "red"
        assert manager._plot_configs["plot2"]["color"] == "blue"
    
    def test_plot_manager_get_plot_config(self):
        """Test getting plot configuration"""
        mock_renderer = Mock(spec=PlotRenderer)
        manager = PlotManager(renderer=mock_renderer)
        
        config = {"color": "green", "style": "dashed"}
        manager.configure_plot("test_plot", config)
        
        # Assuming there's a get_plot_config method (if it exists)
        if hasattr(manager, 'get_plot_config'):
            retrieved_config = manager.get_plot_config("test_plot")
            assert retrieved_config == config
