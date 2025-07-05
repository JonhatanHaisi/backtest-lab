"""Tests for the example scripts in docs/examples/"""
import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime, timedelta

# Add src to path to import backtest_lab
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from backtest_lab.data import StockDataLoader, DataFrequency, MarketData


class TestDataLoadingExample:
    """Test the data loading example script"""
    
    def test_example_single_symbol_loading(self, sample_ohlcv_data):
        """Test single symbol loading from the example"""
        # Create a loader and mock its provider
        loader = StockDataLoader()
        
        # Mock the Yahoo provider
        mock_provider = Mock()
        mock_provider.get_data.return_value = MarketData(
            symbol="PETR3.SA",
            data=sample_ohlcv_data,
            metadata={
                'provider': 'Yahoo Finance',
                'symbol': 'PETR3.SA',
                'rows_count': len(sample_ohlcv_data),
                'start_date': (datetime.now() - timedelta(days=30)).isoformat(),
                'end_date': datetime.now().isoformat()
            }
        )
        
        # Replace the yahoo provider with our mock
        loader.providers['yahoo'] = mock_provider
        
        # Simulate the example code
        data = loader.get_data(
            symbol="PETR3.SA",
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            frequency=DataFrequency.DAILY
        )
        
        # Verify the example works as expected
        assert data.symbol == "PETR3.SA"
        assert len(data.data) > 0
        assert 'open' in data.data.columns
        assert 'high' in data.data.columns
        assert 'low' in data.data.columns
        assert 'close' in data.data.columns
        assert 'volume' in data.data.columns
        
        # Verify the provider was called correctly
        mock_provider.get_data.assert_called_once()
        call_args = mock_provider.get_data.call_args[0][0]  # First argument is the request
        assert call_args.symbol == "PETR3.SA"
        assert call_args.frequency == DataFrequency.DAILY
    
    def test_example_multiple_symbols_loading(self, sample_ohlcv_data):
        """Test multiple symbols loading from the example"""
        # Create a loader and mock its provider
        loader = StockDataLoader()
        
        # Mock the Yahoo provider
        mock_provider = Mock()
        
        # Mock the get_multiple_symbols method to return expected results
        symbols = ["AAPL", "GOOGL", "MSFT"]
        mock_results = {}
        for symbol in symbols:
            mock_results[symbol] = MarketData(
                symbol=symbol,
                data=sample_ohlcv_data,
                metadata={
                    'provider': 'Yahoo Finance',
                    'symbol': symbol,
                    'rows_count': len(sample_ohlcv_data)
                }
            )
        
        # Mock the provider's get_data method to return appropriate data for each symbol
        def mock_get_data(request):
            return MarketData(
                symbol=request.symbol,
                data=sample_ohlcv_data,
                metadata={
                    'provider': 'Yahoo Finance',
                    'symbol': request.symbol,
                    'rows_count': len(sample_ohlcv_data)
                }
            )
        
        mock_provider.get_data.side_effect = mock_get_data
        loader.providers['yahoo'] = mock_provider
        
        # Simulate the example code
        multi_data = loader.get_multiple_symbols(
            symbols=symbols,
            start_date=datetime.now() - timedelta(days=30),
            frequency=DataFrequency.DAILY
        )
        
        # Verify the example works as expected
        assert len(multi_data) == 3
        for symbol in symbols:
            assert symbol in multi_data
            assert multi_data[symbol].symbol == symbol
            assert len(multi_data[symbol].data) > 0
        
        # Verify the provider was called correctly (once for each symbol)
        assert mock_provider.get_data.call_count == 3
    
    def test_example_with_real_imports(self):
        """Test that the example imports work correctly"""
        # Test that we can import all the classes used in the example
        from backtest_lab.data import StockDataLoader, DataFrequency
        from datetime import datetime, timedelta
        
        # Test that the classes can be instantiated
        loader = StockDataLoader()
        assert loader is not None
        assert hasattr(loader, 'get_data')
        assert hasattr(loader, 'get_multiple_symbols')
        
        # Test that the enum works
        assert DataFrequency.DAILY.value == "1d"
        
        # Test that datetime operations work
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        assert start_date < end_date
    
    def test_example_error_handling(self):
        """Test error handling in the example scenario"""
        with patch('backtest_lab.data.StockDataLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader_class.return_value = mock_loader
            
            # Mock an error scenario
            mock_loader.get_data.side_effect = ValueError("No data found for symbol")
            
            loader = StockDataLoader()
            
            # The example should handle this gracefully
            with pytest.raises(ValueError, match="No data found for symbol"):
                loader.get_data(
                    symbol="INVALID",
                    start_date=datetime.now() - timedelta(days=30),
                    end_date=datetime.now(),
                    frequency=DataFrequency.DAILY
                )
    
    def test_example_output_format(self, sample_ohlcv_data):
        """Test that the example output format matches expectations"""
        with patch('backtest_lab.data.StockDataLoader') as mock_loader_class:
            mock_loader = Mock()
            mock_loader_class.return_value = mock_loader
            
            mock_loader.get_data.return_value = MarketData(
                symbol="AAPL",
                data=sample_ohlcv_data,
                metadata={'provider': 'Yahoo Finance'}
            )
            
            loader = StockDataLoader()
            data = loader.get_data(
                symbol="AAPL",
                start_date=datetime.now() - timedelta(days=30),
                end_date=datetime.now(),
                frequency=DataFrequency.DAILY
            )
            
            # Test that the output can be used as shown in example
            assert isinstance(data.data, pd.DataFrame)
            assert len(data.data) > 0
            
            # Test that head() method works (used in example)
            head_data = data.data.head()
            assert isinstance(head_data, pd.DataFrame)
            assert len(head_data) <= 5
    
    @pytest.mark.integration
    def test_example_integration_with_mock_network(self, sample_ohlcv_data):
        """Test the example with network-like behavior"""
        # This test simulates the network calls that would happen in real usage
        with patch('yfinance.Ticker') as mock_ticker_class:
            mock_ticker = Mock()
            mock_ticker_class.return_value = mock_ticker
            
            # Mock successful history call
            mock_ticker.history.return_value = pd.DataFrame({
                'Open': [100.0, 101.0, 102.0],
                'High': [101.0, 102.0, 103.0],
                'Low': [99.0, 100.0, 101.0],
                'Close': [100.5, 101.5, 102.5],
                'Volume': [1000000, 1100000, 1200000],
                'Adj Close': [100.5, 101.5, 102.5]
            }, index=pd.date_range('2024-01-01', periods=3, freq='D'))
            
            mock_ticker.info = {
                'symbol': 'AAPL',
                'longName': 'Apple Inc.',
                'sector': 'Technology',
                'industry': 'Consumer Electronics'
            }
            
            # Run the example code
            loader = StockDataLoader()
            data = loader.get_data(
                symbol="AAPL",
                start_date=datetime.now() - timedelta(days=30),
                end_date=datetime.now(),
                frequency=DataFrequency.DAILY
            )
            
            # Verify the integration works
            assert data.symbol == "AAPL"
            assert len(data.data) == 3
            assert 'open' in data.data.columns
            assert data.metadata['provider'] == 'Yahoo Finance'
            assert data.metadata['company_name'] == 'Apple Inc.'
