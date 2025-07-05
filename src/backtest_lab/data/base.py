from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime
import pandas as pd
from pydantic import BaseModel, Field, ConfigDict, field_validator
from enum import Enum

# Should be able to fetch data from the provider and keep a copy in memory
# Should be able to save data in different formats, by default should use parquet
# Should be able to load data from different formats, by default should use parquet
# Should be able to add more data to an existing dataframe
# This is an interface and we will have subclasses for different data providers

# Planning to allow downloading OHLC and ticker data when available


class DataFrequency(Enum):
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAILY = "1d"
    WEEKLY = "1wk"
    MONTHLY = "1mo"


class MarketDataRequest(BaseModel):
    """Model for market data requests. This model is used to specify the parameters for fetching market data from a provider."""

    symbol: str = Field(description="The symbol for the market data request, e.g., 'AAPL' for Apple Inc.")
    start_date: Optional[datetime] = Field(
        None, description="The start date for the market data request. If None, defaults to the earliest available data."
    )
    end_date: Optional[datetime] = Field(
        None, description="The end date for the market data request. If None, defaults to the latest available data."
    )
    frequency: DataFrequency = Field(
        DataFrequency.DAILY, description="The frequency of the market data request."
    )
    provider_specific_params: Optional[Dict[str, Any]] = Field(
        None,
        description="Provider-specific parameters for the market data request. This can include additional options required by the data provider."
    )

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        if not v:
            raise ValueError("Symbol cannot be empty")
        cleaned = v.strip().upper()
        if not cleaned:
            raise ValueError("Symbol cannot be empty after cleaning")
        return cleaned
    

class MarketData(BaseModel):
    """Model for market data. This model is used to represent the market data fetched from a provider."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    symbol: str = Field(min_length=1, description="The symbol for the market data, e.g., 'AAPL' for Apple Inc.")
    data: pd.DataFrame = Field(description="The market data as a pandas DataFrame. The DataFrame should have a DateTime index and columns for open, high, low, close, volume, etc.")
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadata associated with the market data, such as the source of the data, the date it was fetched, etc."
    )


class DataProvider(ABC):
    """Interface for data providers. This class defines the methods that must be implemented by any data provider."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    @abstractmethod
    def get_data(self, request: MarketDataRequest) -> MarketData:
        """Get market data based on the request."""
        pass
    
    @abstractmethod
    def validate_symbol(self, symbol: str) -> bool:
        """Validate if the symbol is available in the provider's data."""
        pass
    
    @abstractmethod
    def get_available_symbols(self) -> List[str]:
        """Get a list of available symbols in the provider's data."""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the data provider."""
        pass


class AsyncDataProvider(DataProvider):
    """Interface for asynchronous data providers. This class defines the methods that must be implemented by any asynchronous data provider."""
    
    @abstractmethod
    async def get_data_async(self, request: MarketDataRequest) -> MarketData:
        """Get market data asynchronously based on the request."""
        pass