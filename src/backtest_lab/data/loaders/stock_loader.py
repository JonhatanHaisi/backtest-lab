from typing import Dict, Optional, List
from datetime import datetime

from ..base import DataProvider, MarketDataRequest, MarketData, DataFrequency
from ..providers.yahoo import YahooFinanceProvider


class StockDataLoader:
    """Main class for loading stock data from various providers."""
    
    def __init__(self):
        self.providers: Dict[str, DataProvider] = {
            'yahoo': YahooFinanceProvider(),
        }
        self.default_provider = 'yahoo'
    
    def add_provider(self, name: str, provider: DataProvider):
        """Include a new data provider"""
        self.providers[name] = provider
    
    def set_default_provider(self, provider_name: str):
        """Set the default data provider"""
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not found")
        self.default_provider = provider_name
    
    def get_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        frequency: DataFrequency = DataFrequency.DAILY,
        provider: Optional[str] = None,
        **kwargs
    ) -> MarketData:
        """Loads market data for a given symbol"""
        
        provider_name = provider or self.default_provider
        
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not found")
        
        request = MarketDataRequest(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            provider_specific_params=kwargs
        )
        
        return self.providers[provider_name].get_data(request)
    
    def get_multiple_symbols(
        self,
        symbols: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        frequency: DataFrequency = DataFrequency.DAILY,
        provider: Optional[str] = None,
        **kwargs
    ) -> Dict[str, MarketData]:
        """Loads market data for multiple symbols"""
        
        results = {}
        for symbol in symbols:
            try:
                data = self.get_data(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    frequency=frequency,
                    provider=provider,
                    **kwargs
                )
                results[symbol] = data
            except Exception as e:
                print(f"Error loading {symbol}: {str(e)}")
                continue
        
        return results
    
    def validate_symbol(self, symbol: str, provider: Optional[str] = None) -> bool:
        """Validates if a symbol is available in the provider's data"""
        provider_name = provider or self.default_provider
        return self.providers[provider_name].validate_symbol(symbol)
    
    def get_available_providers(self) -> List[str]:
        """Returns a list of available data providers"""
        return list(self.providers.keys())