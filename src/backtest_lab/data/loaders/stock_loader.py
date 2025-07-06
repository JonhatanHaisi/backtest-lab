from typing import Dict, Optional, List, Union
from datetime import datetime
from pathlib import Path

from ..base import DataProvider, MarketDataRequest, MarketData, DataFrequency, generate_filename
from ..providers.yahoo import YahooFinanceProvider
from ..providers.file_provider import FileDataProvider


class StockDataLoader:
    """Main class for loading stock data from various providers."""
    
    def __init__(self, data_directory: Union[str, Path] = None):
        """Initialize StockDataLoader.
        
        Args:
            data_directory: Directory for file-based data loading. If provided, 
                          adds a file provider to the available providers.
        """
        self.providers: Dict[str, DataProvider] = {
            'yahoo': YahooFinanceProvider(),
        }
        
        # Add file provider if data directory is specified
        if data_directory:
            self.providers['file'] = FileDataProvider(data_directory)
        
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
    
    def save_data(self, market_data: MarketData, filepath: Union[str, Path], format: str = 'parquet') -> None:
        """Save market data to file.
        
        Args:
            market_data: MarketData instance to save
            filepath: Path to save the file
            format: File format ('parquet' or 'csv')
        """
        format_lower = format.lower()
        if format_lower == 'parquet':
            market_data.save_to_parquet(filepath)
        elif format_lower == 'csv':
            market_data.save_to_csv(filepath)
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'parquet' or 'csv'.")
    
    def save_data_with_timeframe(self, market_data: MarketData, data_directory: Union[str, Path], 
                                frequency: DataFrequency, format: str = 'parquet') -> Path:
        """Save market data to file with automatic filename generation including timeframe.
        
        Args:
            market_data: MarketData instance to save
            data_directory: Directory to save the file
            frequency: Data frequency for filename generation
            format: File format ('parquet' or 'csv')
            
        Returns:
            Path to the saved file
        """
        data_dir = Path(data_directory)
        data_dir.mkdir(exist_ok=True)
        
        # Generate filename with timeframe
        extension = '.parquet' if format.lower() == 'parquet' else '.csv'
        filename = generate_filename(market_data.symbol, frequency, extension)
        filepath = data_dir / filename
        
        # Save the data
        self.save_data(market_data, filepath, format)
        
        return filepath
    
    def load_from_file(self, filepath: Union[str, Path], symbol: str = None) -> MarketData:
        """Load market data from file.
        
        Args:
            filepath: Path to the data file
            symbol: Symbol for the data (if not provided, will extract from filename)
            
        Returns:
            MarketData instance
        """
        filepath = Path(filepath)
        file_extension = filepath.suffix.lower()
        
        if file_extension == '.parquet':
            return MarketData.load_from_parquet(filepath, symbol)
        elif file_extension == '.csv':
            return MarketData.load_from_csv(filepath, symbol)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}. Use .parquet or .csv files.")
    
    def add_file_provider(self, data_directory: Union[str, Path]) -> None:
        """Add or update file provider with specified data directory.
        
        Args:
            data_directory: Directory containing data files
        """
        self.providers['file'] = FileDataProvider(data_directory)
    
    def validate_symbol(self, symbol: str, provider: Optional[str] = None) -> bool:
        """Validates if a symbol is available in the provider's data"""
        provider_name = provider or self.default_provider
        return self.providers[provider_name].validate_symbol(symbol)
    
    def get_available_providers(self) -> List[str]:
        """Returns a list of available data providers"""
        return list(self.providers.keys())