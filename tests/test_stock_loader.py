"""Tests for StockDataLoader"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from backtest_lab.data.base import MarketDataRequest, MarketData, DataFrequency, DataProvider
from backtest_lab.data.loaders.stock_loader import StockDataLoader
from backtest_lab.data.providers.yahoo import YahooFinanceProvider


class TestStockDataLoader:
    """Test StockDataLoader class"""
    
    def test_loader_initialization(self):
        """Test loader initialization"""
        loader = StockDataLoader()
        
        assert 'yahoo' in loader.providers
        assert loader.default_provider == 'yahoo'
        assert isinstance(loader.providers['yahoo'], YahooFinanceProvider)
    
    def test_add_provider(self):
        """Test adding a new provider"""
        loader = StockDataLoader()
        
        # Create mock provider
        mock_provider = Mock(spec=DataProvider)
        mock_provider.provider_name = "Mock Provider"
        
        # Add provider
        loader.add_provider('mock', mock_provider)
        
        assert 'mock' in loader.providers
        assert loader.providers['mock'] == mock_provider
    
    def test_set_default_provider(self):
        """Test setting default provider"""
        loader = StockDataLoader()
        
        # Add a new provider
        mock_provider = Mock(spec=DataProvider)
        loader.add_provider('mock', mock_provider)
        
        # Set as default
        loader.set_default_provider('mock')
        assert loader.default_provider == 'mock'
    
    def test_set_invalid_default_provider(self):
        """Test setting invalid default provider"""
        loader = StockDataLoader()
        
        with pytest.raises(ValueError, match="Provider 'invalid' not found"):
            loader.set_default_provider('invalid')
    
    def test_get_available_providers(self):
        """Test getting available providers"""
        loader = StockDataLoader()
        
        providers = loader.get_available_providers()
        assert 'yahoo' in providers
        assert isinstance(providers, list)
        
        # Add another provider
        mock_provider = Mock(spec=DataProvider)
        loader.add_provider('mock', mock_provider)
        
        providers = loader.get_available_providers()
        assert 'yahoo' in providers
        assert 'mock' in providers
        assert len(providers) == 2
    
    def test_get_data_with_default_provider(self, sample_ohlcv_data):
        """Test getting data with default provider"""
        loader = StockDataLoader()
        
        # Mock the default provider
        mock_provider = Mock(spec=DataProvider)
        mock_market_data = MarketData(
            symbol="AAPL",
            data=sample_ohlcv_data,
            metadata={"provider": "mock"}
        )
        mock_provider.get_data.return_value = mock_market_data
        
        # Replace default provider
        loader.providers['yahoo'] = mock_provider
        
        # Test
        result = loader.get_data(
            symbol="AAPL",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 10)
        )
        
        # Assertions
        assert isinstance(result, MarketData)
        assert result.symbol == "AAPL"
        
        # Check that provider was called with correct request
        mock_provider.get_data.assert_called_once()
        call_args = mock_provider.get_data.call_args[0][0]
        assert isinstance(call_args, MarketDataRequest)
        assert call_args.symbol == "AAPL"
        assert call_args.start_date == datetime(2024, 1, 1)
        assert call_args.end_date == datetime(2024, 1, 10)
        assert call_args.frequency == DataFrequency.DAILY
    
    def test_get_data_with_specific_provider(self, sample_ohlcv_data):
        """Test getting data with specific provider"""
        loader = StockDataLoader()
        
        # Add mock provider
        mock_provider = Mock(spec=DataProvider)
        mock_market_data = MarketData(
            symbol="AAPL",
            data=sample_ohlcv_data,
            metadata={"provider": "mock"}
        )
        mock_provider.get_data.return_value = mock_market_data
        loader.add_provider('mock', mock_provider)
        
        # Test with specific provider
        result = loader.get_data(
            symbol="AAPL",
            provider="mock"
        )
        
        assert isinstance(result, MarketData)
        assert result.symbol == "AAPL"
        mock_provider.get_data.assert_called_once()
    
    def test_get_data_with_invalid_provider(self):
        """Test getting data with invalid provider"""
        loader = StockDataLoader()
        
        with pytest.raises(ValueError, match="Provider 'invalid' not found"):
            loader.get_data(symbol="AAPL", provider="invalid")
    
    def test_get_data_with_all_parameters(self, sample_ohlcv_data):
        """Test getting data with all parameters"""
        loader = StockDataLoader()
        
        # Mock provider
        mock_provider = Mock(spec=DataProvider)
        mock_market_data = MarketData(
            symbol="AAPL",
            data=sample_ohlcv_data,
            metadata={"provider": "mock"}
        )
        mock_provider.get_data.return_value = mock_market_data
        loader.providers['yahoo'] = mock_provider
        
        # Test with all parameters
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 10)
        frequency = DataFrequency.HOUR_1
        
        result = loader.get_data(
            symbol="AAPL",
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            custom_param="test_value"
        )
        
        # Check request parameters
        call_args = mock_provider.get_data.call_args[0][0]
        assert call_args.symbol == "AAPL"
        assert call_args.start_date == start_date
        assert call_args.end_date == end_date
        assert call_args.frequency == frequency
        assert call_args.provider_specific_params == {"custom_param": "test_value"}
    
    def test_get_multiple_symbols_success(self, sample_ohlcv_data):
        """Test getting multiple symbols successfully"""
        loader = StockDataLoader()
        
        # Mock provider
        mock_provider = Mock(spec=DataProvider)
        
        def mock_get_data(request):
            return MarketData(
                symbol=request.symbol,
                data=sample_ohlcv_data,
                metadata={"provider": "mock"}
            )
        
        mock_provider.get_data.side_effect = mock_get_data
        loader.providers['yahoo'] = mock_provider
        
        # Test multiple symbols
        symbols = ["AAPL", "GOOGL", "MSFT"]
        results = loader.get_multiple_symbols(symbols)
        
        assert len(results) == 3
        assert "AAPL" in results
        assert "GOOGL" in results
        assert "MSFT" in results
        
        for symbol in symbols:
            assert isinstance(results[symbol], MarketData)
            assert results[symbol].symbol == symbol
        
        # Check that provider was called for each symbol
        assert mock_provider.get_data.call_count == 3
    
    def test_get_multiple_symbols_with_failures(self, sample_ohlcv_data, capsys):
        """Test getting multiple symbols with some failures"""
        loader = StockDataLoader()
        
        # Mock provider
        mock_provider = Mock(spec=DataProvider)
        
        def mock_get_data(request):
            if request.symbol == "INVALID":
                raise ValueError("Invalid symbol")
            return MarketData(
                symbol=request.symbol,
                data=sample_ohlcv_data,
                metadata={"provider": "mock"}
            )
        
        mock_provider.get_data.side_effect = mock_get_data
        loader.providers['yahoo'] = mock_provider
        
        # Test with some invalid symbols
        symbols = ["AAPL", "INVALID", "GOOGL"]
        results = loader.get_multiple_symbols(symbols)
        
        # Should only have successful results
        assert len(results) == 2
        assert "AAPL" in results
        assert "GOOGL" in results
        assert "INVALID" not in results
        
        # Check that error was printed
        captured = capsys.readouterr()
        assert "Error loading INVALID" in captured.out
    
    def test_get_multiple_symbols_with_parameters(self, sample_ohlcv_data):
        """Test getting multiple symbols with parameters"""
        loader = StockDataLoader()
        
        # Mock provider
        mock_provider = Mock(spec=DataProvider)
        
        def mock_get_data(request):
            return MarketData(
                symbol=request.symbol,
                data=sample_ohlcv_data,
                metadata={"provider": "mock"}
            )
        
        mock_provider.get_data.side_effect = mock_get_data
        loader.providers['yahoo'] = mock_provider
        
        # Test with parameters
        symbols = ["AAPL", "GOOGL"]
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 10)
        frequency = DataFrequency.HOUR_1
        
        results = loader.get_multiple_symbols(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            custom_param="test"
        )
        
        assert len(results) == 2
        
        # Check that all calls had correct parameters
        for call in mock_provider.get_data.call_args_list:
            request = call[0][0]
            assert request.start_date == start_date
            assert request.end_date == end_date
            assert request.frequency == frequency
            assert request.provider_specific_params == {"custom_param": "test"}
    
    def test_validate_symbol_with_default_provider(self):
        """Test symbol validation with default provider"""
        loader = StockDataLoader()
        
        # Mock provider
        mock_provider = Mock(spec=DataProvider)
        mock_provider.validate_symbol.return_value = True
        loader.providers['yahoo'] = mock_provider
        
        result = loader.validate_symbol("AAPL")
        
        assert result is True
        mock_provider.validate_symbol.assert_called_once_with("AAPL")
    
    def test_validate_symbol_with_specific_provider(self):
        """Test symbol validation with specific provider"""
        loader = StockDataLoader()
        
        # Add mock provider
        mock_provider = Mock(spec=DataProvider)
        mock_provider.validate_symbol.return_value = False
        loader.add_provider('mock', mock_provider)
        
        result = loader.validate_symbol("INVALID", provider="mock")
        
        assert result is False
        mock_provider.validate_symbol.assert_called_once_with("INVALID")
    
    def test_validate_symbol_with_invalid_provider(self):
        """Test symbol validation with invalid provider"""
        loader = StockDataLoader()
        
        with pytest.raises(KeyError):
            loader.validate_symbol("AAPL", provider="invalid")
    
    def test_loader_with_real_yahoo_provider(self):
        """Test loader with real Yahoo provider (no network)"""
        loader = StockDataLoader()
        
        # Check that Yahoo provider is properly initialized
        assert 'yahoo' in loader.providers
        assert isinstance(loader.providers['yahoo'], YahooFinanceProvider)
        assert loader.default_provider == 'yahoo'
        
        # Check provider name
        yahoo_provider = loader.providers['yahoo']
        assert yahoo_provider.provider_name == "Yahoo Finance"


class TestStockDataLoaderIntegration:
    """Integration tests for StockDataLoader"""
    
    def test_loader_with_multiple_providers(self, sample_ohlcv_data):
        """Test loader with multiple providers"""
        loader = StockDataLoader()
        
        # Add multiple mock providers
        mock_provider1 = Mock(spec=DataProvider)
        mock_provider1.provider_name = "Provider 1"
        mock_provider1.get_data.return_value = MarketData(
            symbol="AAPL",
            data=sample_ohlcv_data,
            metadata={"provider": "provider1"}
        )
        
        mock_provider2 = Mock(spec=DataProvider)
        mock_provider2.provider_name = "Provider 2"
        mock_provider2.get_data.return_value = MarketData(
            symbol="AAPL",
            data=sample_ohlcv_data,
            metadata={"provider": "provider2"}
        )
        
        loader.add_provider('provider1', mock_provider1)
        loader.add_provider('provider2', mock_provider2)
        
        # Test with different providers
        result1 = loader.get_data("AAPL", provider="provider1")
        result2 = loader.get_data("AAPL", provider="provider2")
        
        assert result1.metadata["provider"] == "provider1"
        assert result2.metadata["provider"] == "provider2"
        
        mock_provider1.get_data.assert_called_once()
        mock_provider2.get_data.assert_called_once()
    
    def test_loader_fallback_behavior(self, sample_ohlcv_data):
        """Test loader fallback behavior"""
        loader = StockDataLoader()
        
        # Mock provider that fails sometimes
        mock_provider = Mock(spec=DataProvider)
        
        def mock_get_data_with_fallback(request):
            if request.symbol == "FAIL":
                raise ValueError("Provider failure")
            return MarketData(
                symbol=request.symbol,
                data=sample_ohlcv_data,
                metadata={"provider": "mock"}
            )
        
        mock_provider.get_data.side_effect = mock_get_data_with_fallback
        loader.providers['yahoo'] = mock_provider
        
        # Test successful request
        result = loader.get_data("AAPL")
        assert isinstance(result, MarketData)
        assert result.symbol == "AAPL"
        
        # Test failed request
        with pytest.raises(ValueError):
            loader.get_data("FAIL")
    
    @pytest.mark.integration
    @pytest.mark.network
    def test_real_data_loading_integration(self):
        """Test real data loading - requires network"""
        loader = StockDataLoader()
        
        try:
            # Test with real Yahoo provider
            result = loader.get_data(
                symbol="AAPL",
                start_date=datetime.now() - timedelta(days=5),
                end_date=datetime.now() - timedelta(days=1),
                frequency=DataFrequency.DAILY
            )
            
            assert isinstance(result, MarketData)
            assert result.symbol == "AAPL"
            assert len(result.data) > 0
            assert result.metadata["provider"] == "Yahoo Finance"
            
        except Exception as e:
            pytest.skip(f"Network test failed: {e}")
    
    @pytest.mark.integration
    @pytest.mark.network
    def test_real_multiple_symbols_integration(self):
        """Test real multiple symbols loading - requires network"""
        loader = StockDataLoader()
        
        try:
            symbols = ["AAPL", "GOOGL"]
            results = loader.get_multiple_symbols(
                symbols=symbols,
                start_date=datetime.now() - timedelta(days=5),
                end_date=datetime.now() - timedelta(days=1),
                frequency=DataFrequency.DAILY
            )
            
            assert len(results) == 2
            for symbol in symbols:
                assert symbol in results
                assert isinstance(results[symbol], MarketData)
                assert results[symbol].symbol == symbol
                assert len(results[symbol].data) > 0
                
        except Exception as e:
            pytest.skip(f"Network test failed: {e}")
    
    @pytest.mark.integration
    @pytest.mark.network
    def test_real_symbol_validation_integration(self):
        """Test real symbol validation - requires network"""
        loader = StockDataLoader()
        
        try:
            # Test valid symbol
            assert loader.validate_symbol("AAPL") is True
            
            # Test invalid symbol
            assert loader.validate_symbol("INVALID_SYMBOL_123") is False
            
        except Exception as e:
            pytest.skip(f"Network test failed: {e}")


class TestStockDataLoaderErrorHandling:
    """Test error handling in StockDataLoader"""
    
    def test_provider_error_propagation(self):
        """Test that provider errors are properly propagated"""
        loader = StockDataLoader()
        
        # Mock provider that raises exception
        mock_provider = Mock(spec=DataProvider)
        mock_provider.get_data.side_effect = ValueError("Provider error")
        loader.providers['yahoo'] = mock_provider
        
        with pytest.raises(ValueError, match="Provider error"):
            loader.get_data("AAPL")
    
    def test_multiple_symbols_error_handling(self, sample_ohlcv_data, capsys):
        """Test error handling in multiple symbols loading"""
        loader = StockDataLoader()
        
        # Mock provider with mixed success/failure
        mock_provider = Mock(spec=DataProvider)
        
        def mock_get_data_mixed(request):
            if request.symbol in ["FAIL1", "FAIL2"]:
                raise ValueError(f"Error for {request.symbol}")
            return MarketData(
                symbol=request.symbol,
                data=sample_ohlcv_data,
                metadata={"provider": "mock"}
            )
        
        mock_provider.get_data.side_effect = mock_get_data_mixed
        loader.providers['yahoo'] = mock_provider
        
        # Test with mixed symbols
        symbols = ["AAPL", "FAIL1", "GOOGL", "FAIL2", "MSFT"]
        results = loader.get_multiple_symbols(symbols)
        
        # Should have successful results only
        assert len(results) == 3
        assert "AAPL" in results
        assert "GOOGL" in results
        assert "MSFT" in results
        assert "FAIL1" not in results
        assert "FAIL2" not in results
        
        # Check error messages
        captured = capsys.readouterr()
        assert "Error loading FAIL1" in captured.out
        assert "Error loading FAIL2" in captured.out
    
    def test_empty_symbols_list(self):
        """Test handling of empty symbols list"""
        loader = StockDataLoader()
        
        results = loader.get_multiple_symbols([])
        
        assert len(results) == 0
        assert isinstance(results, dict)
    
    def test_none_symbols_handling(self):
        """Test handling of None in symbols list"""
        loader = StockDataLoader()
        
        # Mock provider
        mock_provider = Mock(spec=DataProvider)
        mock_provider.get_data.side_effect = ValueError("Invalid symbol")
        loader.providers['yahoo'] = mock_provider
        
        # This should handle the error gracefully
        results = loader.get_multiple_symbols([None])
        
        assert len(results) == 0
