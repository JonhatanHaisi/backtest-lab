"""Tests for base classes"""
import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock

from backtest_lab.data.base import DataFrequency, MarketDataRequest, MarketData, DataProvider


class TestDataFrequency:
    """Test DataFrequency enum"""
    
    def test_frequency_values(self):
        """Test that frequency values are correct"""
        assert DataFrequency.MINUTE_1.value == "1m"
        assert DataFrequency.MINUTE_5.value == "5m"
        assert DataFrequency.MINUTE_15.value == "15m"
        assert DataFrequency.MINUTE_30.value == "30m"
        assert DataFrequency.HOUR_1.value == "1h"
        assert DataFrequency.HOUR_4.value == "4h"
        assert DataFrequency.DAILY.value == "1d"
        assert DataFrequency.WEEKLY.value == "1wk"
        assert DataFrequency.MONTHLY.value == "1mo"
    
    def test_frequency_enum_members(self):
        """Test that all expected frequency members exist"""
        expected_members = [
            "MINUTE_1", "MINUTE_5", "MINUTE_15", "MINUTE_30",
            "HOUR_1", "HOUR_4", "DAILY", "WEEKLY", "MONTHLY"
        ]
        actual_members = [member.name for member in DataFrequency]
        assert set(actual_members) == set(expected_members)


class TestMarketDataRequest:
    """Test MarketDataRequest model"""
    
    def test_create_basic_request(self):
        """Test creating a basic market data request"""
        request = MarketDataRequest(symbol="AAPL")
        
        assert request.symbol == "AAPL"
        assert request.start_date is None
        assert request.end_date is None
        assert request.frequency == DataFrequency.DAILY
        assert request.provider_specific_params is None
    
    def test_create_full_request(self):
        """Test creating a full market data request with all parameters"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 10)
        params = {"param1": "value1", "param2": "value2"}
        
        request = MarketDataRequest(
            symbol="GOOGL",
            start_date=start_date,
            end_date=end_date,
            frequency=DataFrequency.HOUR_1,
            provider_specific_params=params
        )
        
        assert request.symbol == "GOOGL"
        assert request.start_date == start_date
        assert request.end_date == end_date
        assert request.frequency == DataFrequency.HOUR_1
        assert request.provider_specific_params == params
    
    def test_symbol_normalization(self):
        """Test that symbol is normalized to uppercase and trimmed"""
        request = MarketDataRequest(symbol="  aapl  ")
        assert request.symbol == "AAPL"
        
        request = MarketDataRequest(symbol="googl")
        assert request.symbol == "GOOGL"
        
        request = MarketDataRequest(symbol="MSFT")
        assert request.symbol == "MSFT"
    
    def test_symbol_validation(self):
        """Test symbol validation"""
        # Valid symbols
        MarketDataRequest(symbol="AAPL")
        MarketDataRequest(symbol="GOOGL")
        MarketDataRequest(symbol="PETR4.SA")
        
        # Invalid symbols should raise validation error
        with pytest.raises(ValueError):
            MarketDataRequest(symbol="")
    
    def test_frequency_default(self):
        """Test that frequency defaults to DAILY"""
        request = MarketDataRequest(symbol="AAPL")
        assert request.frequency == DataFrequency.DAILY
    
    def test_dates_optional(self):
        """Test that dates are optional"""
        request = MarketDataRequest(symbol="AAPL")
        assert request.start_date is None
        assert request.end_date is None
    
    def test_provider_params_optional(self):
        """Test that provider specific params are optional"""
        request = MarketDataRequest(symbol="AAPL")
        assert request.provider_specific_params is None
    
    def test_request_serialization(self):
        """Test that request can be serialized to dict"""
        request = MarketDataRequest(
            symbol="AAPL",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 10),
            frequency=DataFrequency.DAILY
        )
        
        data = request.model_dump()
        assert data["symbol"] == "AAPL"
        assert data["frequency"] == DataFrequency.DAILY  # Enum value, not string
    
    def test_request_from_dict(self):
        """Test creating request from dictionary"""
        data = {
            "symbol": "AAPL",
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-01-10T00:00:00",
            "frequency": "1d"
        }
        
        request = MarketDataRequest(**data)
        assert request.symbol == "AAPL"
        assert request.frequency == DataFrequency.DAILY


class TestMarketData:
    """Test MarketData model"""
    
    def test_create_market_data(self, sample_ohlcv_data):
        """Test creating market data"""
        metadata = {"provider": "test", "rows_count": len(sample_ohlcv_data)}
        
        market_data = MarketData(
            symbol="AAPL",
            data=sample_ohlcv_data,
            metadata=metadata
        )
        
        assert market_data.symbol == "AAPL"
        assert isinstance(market_data.data, pd.DataFrame)
        assert market_data.metadata == metadata
    
    def test_market_data_with_minimal_info(self, sample_ohlcv_data):
        """Test creating market data with minimal information"""
        market_data = MarketData(
            symbol="AAPL",
            data=sample_ohlcv_data
        )
        
        assert market_data.symbol == "AAPL"
        assert isinstance(market_data.data, pd.DataFrame)
        assert market_data.metadata is None
    
    def test_market_data_dataframe_properties(self, sample_ohlcv_data):
        """Test that data is a proper DataFrame with expected columns"""
        market_data = MarketData(
            symbol="AAPL",
            data=sample_ohlcv_data
        )
        
        df = market_data.data
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert 'open' in df.columns
        assert 'high' in df.columns
        assert 'low' in df.columns
        assert 'close' in df.columns
        assert 'volume' in df.columns
    
    def test_market_data_symbol_validation(self, sample_ohlcv_data):
        """Test symbol validation in market data"""
        with pytest.raises(ValueError):
            MarketData(symbol="", data=sample_ohlcv_data)
    
    def test_market_data_with_empty_dataframe(self):
        """Test creating market data with empty DataFrame"""
        empty_df = pd.DataFrame()
        market_data = MarketData(
            symbol="AAPL",
            data=empty_df
        )
        
        assert market_data.symbol == "AAPL"
        assert len(market_data.data) == 0
    
    def test_market_data_serialization(self, sample_ohlcv_data):
        """Test that market data can be serialized (excluding DataFrame)"""
        market_data = MarketData(
            symbol="AAPL",
            data=sample_ohlcv_data,
            metadata={"provider": "test"}
        )
        
        # Should be able to access attributes
        assert market_data.symbol == "AAPL"
        assert market_data.metadata["provider"] == "test"


class TestDataProvider:
    """Test DataProvider abstract class"""
    
    def test_cannot_instantiate_abstract_class(self):
        """Test that DataProvider cannot be instantiated directly"""
        with pytest.raises(TypeError):
            DataProvider()
    
    def test_abstract_methods_must_be_implemented(self):
        """Test that abstract methods must be implemented in subclasses"""
        class IncompleteProvider(DataProvider):
            pass
        
        with pytest.raises(TypeError):
            IncompleteProvider()
    
    def test_concrete_provider_implementation(self):
        """Test a concrete implementation of DataProvider"""
        class TestProvider(DataProvider):
            def get_data(self, request):
                return Mock()
            
            def validate_symbol(self, symbol):
                return True
            
            def get_available_symbols(self):
                return ["AAPL", "GOOGL"]
            
            @property
            def provider_name(self):
                return "Test Provider"
        
        provider = TestProvider()
        assert provider.provider_name == "Test Provider"
        assert provider.validate_symbol("AAPL") is True
        assert provider.get_available_symbols() == ["AAPL", "GOOGL"]
        assert provider.config == {}
    
    def test_provider_with_config(self):
        """Test provider with configuration"""
        class TestProvider(DataProvider):
            def get_data(self, request):
                return Mock()
            
            def validate_symbol(self, symbol):
                return True
            
            def get_available_symbols(self):
                return []
            
            @property
            def provider_name(self):
                return "Test Provider"
        
        config = {"timeout": 30, "retries": 3}
        provider = TestProvider(config)
        assert provider.config == config
    
    def test_provider_method_signatures(self):
        """Test that provider methods have correct signatures"""
        class TestProvider(DataProvider):
            def get_data(self, request: MarketDataRequest) -> MarketData:
                return Mock(spec=MarketData)
            
            def validate_symbol(self, symbol: str) -> bool:
                return True
            
            def get_available_symbols(self) -> list:
                return []
            
            @property
            def provider_name(self) -> str:
                return "Test Provider"
        
        provider = TestProvider()
        
        # Test that methods exist and are callable
        assert callable(provider.get_data)
        assert callable(provider.validate_symbol)
        assert callable(provider.get_available_symbols)
        assert hasattr(provider, 'provider_name')


class TestDataProviderIntegration:
    """Integration tests for DataProvider functionality"""
    
    def test_provider_with_market_data_request(self, sample_market_data_request, sample_ohlcv_data):
        """Test provider integration with MarketDataRequest"""
        class TestProvider(DataProvider):
            def get_data(self, request: MarketDataRequest) -> MarketData:
                return MarketData(
                    symbol=request.symbol,
                    data=sample_ohlcv_data,
                    metadata={"provider": self.provider_name}
                )
            
            def validate_symbol(self, symbol: str) -> bool:
                return symbol in ["AAPL", "GOOGL", "MSFT"]
            
            def get_available_symbols(self) -> list:
                return ["AAPL", "GOOGL", "MSFT"]
            
            @property
            def provider_name(self) -> str:
                return "Test Provider"
        
        provider = TestProvider()
        result = provider.get_data(sample_market_data_request)
        
        assert isinstance(result, MarketData)
        assert result.symbol == "AAPL"
        assert result.metadata["provider"] == "Test Provider"
        assert len(result.data) > 0
    
    def test_provider_symbol_validation(self):
        """Test provider symbol validation"""
        class TestProvider(DataProvider):
            def get_data(self, request: MarketDataRequest) -> MarketData:
                return Mock()
            
            def validate_symbol(self, symbol: str) -> bool:
                valid_symbols = ["AAPL", "GOOGL", "MSFT"]
                return symbol.upper() in valid_symbols
            
            def get_available_symbols(self) -> list:
                return ["AAPL", "GOOGL", "MSFT"]
            
            @property
            def provider_name(self) -> str:
                return "Test Provider"
        
        provider = TestProvider()
        
        # Test valid symbols
        assert provider.validate_symbol("AAPL") is True
        assert provider.validate_symbol("aapl") is True
        assert provider.validate_symbol("GOOGL") is True
        
        # Test invalid symbols
        assert provider.validate_symbol("INVALID") is False
        assert provider.validate_symbol("") is False
