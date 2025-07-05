"""Additional tests for edge cases and error scenarios"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from backtest_lab.data import (
    StockDataLoader,
    DataFrequency,
    MarketDataRequest,
    MarketData,
    YahooFinanceProvider
)


class TestEdgeCases:
    """Test edge cases and error scenarios"""
    
    def test_empty_symbol_handling(self):
        """Test handling of empty or invalid symbols"""
        # Test empty symbol
        with pytest.raises(ValueError):
            MarketDataRequest(symbol="")
        
        # Test whitespace-only symbol - this should be handled by model_post_init
        # After strip(), it becomes empty, so should fail
        with pytest.raises(ValueError):
            MarketDataRequest(symbol="   ")
    
    def test_invalid_date_ranges(self):
        """Test handling of invalid date ranges"""
        # Test end date before start date
        start_date = datetime(2024, 1, 10)
        end_date = datetime(2024, 1, 1)
        
        request = MarketDataRequest(
            symbol="AAPL",
            start_date=start_date,
            end_date=end_date,
            frequency=DataFrequency.DAILY
        )
        
        # The request should be created but might fail in provider
        assert request.start_date > request.end_date
    
    def test_future_date_handling(self):
        """Test handling of future dates"""
        future_date = datetime.now() + timedelta(days=365)
        
        request = MarketDataRequest(
            symbol="AAPL",
            start_date=future_date,
            end_date=future_date + timedelta(days=30),
            frequency=DataFrequency.DAILY
        )
        
        # Should be able to create request with future dates
        assert request.start_date > datetime.now()
    
    def test_very_large_date_range(self):
        """Test handling of very large date ranges"""
        start_date = datetime(1900, 1, 1)
        end_date = datetime.now()
        
        request = MarketDataRequest(
            symbol="AAPL",
            start_date=start_date,
            end_date=end_date,
            frequency=DataFrequency.DAILY
        )
        
        # Should be able to create request with large date range
        assert (request.end_date - request.start_date).days > 40000
    
    def test_symbol_normalization(self):
        """Test symbol normalization behavior"""
        # Test lowercase symbols get converted to uppercase
        request = MarketDataRequest(symbol="aapl")
        assert request.symbol == "AAPL"
        
        # Test symbols with whitespace
        request = MarketDataRequest(symbol="  AAPL  ")
        assert request.symbol == "AAPL"
        
        # Test mixed case
        request = MarketDataRequest(symbol="ApPl")
        assert request.symbol == "APPL"
    
    def test_provider_specific_params(self):
        """Test provider-specific parameters handling"""
        request = MarketDataRequest(
            symbol="AAPL",
            provider_specific_params={
                "timeout": 30,
                "retries": 3,
                "custom_param": "value"
            }
        )
        
        assert request.provider_specific_params["timeout"] == 30
        assert request.provider_specific_params["retries"] == 3
        assert request.provider_specific_params["custom_param"] == "value"
    
    def test_market_data_with_invalid_dataframe(self):
        """Test MarketData with invalid DataFrame"""
        # Test with empty DataFrame
        empty_df = pd.DataFrame()
        
        market_data = MarketData(
            symbol="AAPL",
            data=empty_df,
            metadata={"provider": "test"}
        )
        
        assert len(market_data.data) == 0
        assert market_data.symbol == "AAPL"
    
    def test_market_data_with_missing_columns(self):
        """Test MarketData with DataFrame missing expected columns"""
        # DataFrame with only some columns
        df = pd.DataFrame({
            'open': [100.0, 101.0],
            'close': [100.5, 101.5]
            # Missing: high, low, volume
        })
        
        market_data = MarketData(
            symbol="AAPL",
            data=df,
            metadata={"provider": "test"}
        )
        
        assert 'open' in market_data.data.columns
        assert 'close' in market_data.data.columns
        assert len(market_data.data) == 2
    
    def test_provider_network_errors(self):
        """Test provider behavior during network errors"""
        with patch('yfinance.Ticker') as mock_ticker:
            # Mock network error
            mock_ticker.side_effect = ConnectionError("Network error")
            
            provider = YahooFinanceProvider()
            request = MarketDataRequest(symbol="AAPL")
            
            with pytest.raises(ConnectionError):
                provider.get_data(request)
    
    def test_provider_timeout_errors(self):
        """Test provider behavior during timeout errors"""
        with patch('yfinance.Ticker') as mock_ticker:
            # Mock timeout error
            mock_ticker.side_effect = TimeoutError("Request timeout")
            
            provider = YahooFinanceProvider()
            request = MarketDataRequest(symbol="AAPL")
            
            with pytest.raises(TimeoutError):
                provider.get_data(request)
    
    def test_provider_invalid_symbol_response(self):
        """Test provider behavior with invalid symbol"""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_instance = Mock()
            mock_ticker.return_value = mock_instance
            
            # Mock empty data response
            mock_instance.history.return_value = pd.DataFrame()
            
            provider = YahooFinanceProvider()
            request = MarketDataRequest(symbol="INVALID")
            
            with pytest.raises(ValueError, match="No data found"):
                provider.get_data(request)
    
    def test_stock_loader_invalid_provider(self):
        """Test StockDataLoader with invalid provider"""
        loader = StockDataLoader()
        
        # Test with non-existent provider
        with pytest.raises(ValueError, match="Provider 'nonexistent' not found"):
            loader.get_data(symbol="AAPL", provider="nonexistent")
        
        # Test setting invalid default provider
        with pytest.raises(ValueError, match="Provider 'nonexistent' not found"):
            loader.set_default_provider("nonexistent")
    
    def test_stock_loader_empty_symbols_list(self):
        """Test StockDataLoader with empty symbols list"""
        loader = StockDataLoader()
        
        # Test with empty list
        result = loader.get_multiple_symbols(symbols=[])
        assert len(result) == 0
        assert isinstance(result, dict)
    
    def test_stock_loader_partial_failures(self):
        """Test StockDataLoader with partial failures in multiple symbols"""
        loader = StockDataLoader()
        
        # Mock provider that fails for some symbols
        mock_provider = Mock()
        
        def mock_get_data(request):
            if request.symbol == "INVALID":
                raise ValueError("Invalid symbol")
            return MarketData(
                symbol=request.symbol,
                data=pd.DataFrame({'open': [100], 'high': [101], 'low': [99], 'close': [100.5], 'volume': [1000]}),
                metadata={"provider": "mock"}
            )
        
        mock_provider.get_data = mock_get_data
        loader.providers['mock'] = mock_provider
        
        # Test with mixed valid and invalid symbols
        symbols = ["AAPL", "INVALID", "GOOGL"]
        result = loader.get_multiple_symbols(symbols=symbols, provider="mock")
        
        # Should get results for valid symbols only
        assert len(result) == 2
        assert "AAPL" in result
        assert "GOOGL" in result
        assert "INVALID" not in result
    
    def test_frequency_enum_completeness(self):
        """Test that all frequency values are properly defined"""
        frequencies = [
            DataFrequency.MINUTE_1,
            DataFrequency.MINUTE_5,
            DataFrequency.MINUTE_15,
            DataFrequency.MINUTE_30,
            DataFrequency.HOUR_1,
            DataFrequency.HOUR_4,
            DataFrequency.DAILY,
            DataFrequency.WEEKLY,
            DataFrequency.MONTHLY
        ]
        
        for freq in frequencies:
            assert freq.value is not None
            assert isinstance(freq.value, str)
            assert len(freq.value) > 0
    
    def test_metadata_handling(self):
        """Test metadata handling in MarketData"""
        # Test with None metadata
        market_data = MarketData(
            symbol="AAPL",
            data=pd.DataFrame({'open': [100], 'close': [100.5]}),
            metadata=None
        )
        
        assert market_data.metadata is None
        
        # Test with empty metadata
        market_data = MarketData(
            symbol="AAPL",
            data=pd.DataFrame({'open': [100], 'close': [100.5]}),
            metadata={}
        )
        
        assert market_data.metadata == {}
        
        # Test with complex metadata
        complex_metadata = {
            'provider': 'Yahoo Finance',
            'nested': {
                'key': 'value',
                'number': 42
            },
            'list': [1, 2, 3]
        }
        
        market_data = MarketData(
            symbol="AAPL",
            data=pd.DataFrame({'open': [100], 'close': [100.5]}),
            metadata=complex_metadata
        )
        
        assert market_data.metadata == complex_metadata
    
    def test_yahoo_provider_edge_cases(self):
        """Test Yahoo provider edge cases"""
        provider = YahooFinanceProvider()
        
        # Test provider name
        assert provider.provider_name == "Yahoo Finance"
        
        # Test with custom config
        config = {"timeout": 60, "retries": 5}
        provider_with_config = YahooFinanceProvider(config)
        assert provider_with_config.config == config
        
        # Test frequency mapping
        assert DataFrequency.MINUTE_1 in provider.FREQUENCY_MAPPING
        assert DataFrequency.DAILY in provider.FREQUENCY_MAPPING
        assert DataFrequency.MONTHLY in provider.FREQUENCY_MAPPING
    
    def test_pydantic_model_validation(self):
        """Test Pydantic model validation"""
        # Test that invalid data types raise validation errors
        with pytest.raises(ValueError):
            MarketDataRequest(symbol=123)  # Should be string
        
        with pytest.raises(ValueError):
            MarketDataRequest(symbol="AAPL", start_date="invalid_date")  # Should be datetime
        
        # Test that valid data passes validation
        valid_request = MarketDataRequest(
            symbol="AAPL",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 10),
            frequency=DataFrequency.DAILY
        )
        
        assert valid_request.symbol == "AAPL"
        assert isinstance(valid_request.start_date, datetime)
        assert isinstance(valid_request.end_date, datetime)
        assert valid_request.frequency == DataFrequency.DAILY
