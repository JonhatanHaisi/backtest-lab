import yfinance as yf
import pandas as pd
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from ..base import DataProvider, MarketDataRequest, MarketData, DataFrequency


class YahooFinanceProvider(DataProvider):
    """Yahoo Finance Data Provider"""
    
    FREQUENCY_MAPPING = {
        DataFrequency.MINUTE_1: "1m",
        DataFrequency.MINUTE_5: "5m",
        DataFrequency.MINUTE_15: "15m",
        DataFrequency.MINUTE_30: "30m",
        DataFrequency.HOUR_1: "1h",
        DataFrequency.DAILY: "1d",
        DataFrequency.WEEKLY: "1wk",
        DataFrequency.MONTHLY: "1mo",
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
    
    @property
    def provider_name(self) -> str:
        return "Yahoo Finance"
    
    def get_data(self, request: MarketDataRequest) -> MarketData:
        """Gets market data from Yahoo Finance based on the request."""
        try:
            ticker = yf.Ticker(request.symbol)
            
            # set start and end dates
            end_date = request.end_date or datetime.now()
            start_date = request.start_date or (end_date - timedelta(days=365))
            
            # get historical data
            interval = self.FREQUENCY_MAPPING.get(request.frequency, "1d")
            data = ticker.history(
                start=start_date,
                end=end_date,
                interval=interval,
                auto_adjust=True,
                prepost=True
            )
            
            if data.empty:
                raise ValueError(f"No data found for symbol {request.symbol}")
            
            # standardize columns
            data = self._standardize_columns(data)
            
            # Metadata
            info = ticker.info
            metadata = {
                'provider': self.provider_name,
                'symbol': request.symbol,
                'frequency': request.frequency.value,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'rows_count': len(data),
                'company_name': info.get('longName', ''),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
            }
            
            return MarketData(
                symbol=request.symbol,
                data=data,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Error fetching data for {request.symbol}: {str(e)}")
            raise
    
    def validate_symbol(self, symbol: str) -> bool:
        """Validates if the symbol is available in Yahoo Finance."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return 'symbol' in info or 'shortName' in info
        except:
            return False
    
    def get_available_symbols(self) -> List[str]:
        """Yahoo Finance does not provide a direct endpoint for symbol listing."""
        raise NotImplementedError("Yahoo Finance doesn't provide symbol listing endpoint")
    
    def _standardize_columns(self, data: pd.DataFrame) -> pd.DataFrame:
        """Standardizes the DataFrame columns to match the expected format."""
        column_mapping = {
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume',
            'Adj Close': 'adj_close'
        }
        
        data = data.rename(columns=column_mapping)
        
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in data.columns:
                data[col] = None
        
        return data[required_columns + ['adj_close'] if 'adj_close' in data.columns else required_columns]