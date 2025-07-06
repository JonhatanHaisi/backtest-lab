import json
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, field_validator


class DataFrequency(Enum):
    """Enumeration for different data frequencies."""

    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAILY = "1d"
    WEEKLY = "1wk"
    MONTHLY = "1mo"


def generate_filename(
    symbol: str, frequency: DataFrequency, extension: str = ".parquet"
) -> str:
    """Generate a filename with symbol and timeframe.

    Args:
        symbol: Stock symbol
        frequency: Data frequency/timeframe
        extension: File extension (default: '.parquet')

    Returns:
        Filename in format: symbol_timeframe.extension (e.g., 'PETR3.SA_1d.parquet')
    """
    # Clean the symbol for safe filename usage
    safe_symbol = symbol.replace("/", "_").replace("\\", "_").replace(":", "_")
    filename = f"{safe_symbol.lower()}_{frequency.value}{extension}"
    return filename


def parse_filename(filename: str) -> tuple[str, Optional[DataFrequency]]:
    """Parse a filename to extract symbol and frequency.

    Args:
        filename: Filename to parse

    Returns:
        Tuple of (symbol, frequency) - frequency is None if not found
    """
    # Remove file extension
    name_without_ext = Path(filename).stem

    # Try to find frequency pattern
    for freq in DataFrequency:
        if name_without_ext.endswith(f"_{freq.value}"):
            symbol = name_without_ext[: -len(f"_{freq.value}")].upper()
            return symbol, freq

    # If no frequency found, return the whole name as symbol
    return name_without_ext.upper(), None


class MarketDataRequest(BaseModel):
    """Model for market data requests. This model is used to specify the parameters for fetching market data from a provider."""

    symbol: str = Field(
        description="The symbol for the market data request, e.g., 'AAPL' for Apple Inc."
    )
    start_date: Optional[datetime] = Field(
        None,
        description="The start date for the market data request. If None, defaults to the earliest available data.",
    )
    end_date: Optional[datetime] = Field(
        None,
        description="The end date for the market data request. If None, defaults to the latest available data.",
    )
    frequency: DataFrequency = Field(
        DataFrequency.DAILY, description="The frequency of the market data request."
    )
    provider_specific_params: Optional[Dict[str, Any]] = Field(
        None,
        description="Provider-specific parameters for the market data request. This can include additional options required by the data provider.",
    )

    @field_validator("symbol")
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

    symbol: str = Field(
        min_length=1,
        description="The symbol for the market data, e.g., 'AAPL' for Apple Inc.",
    )
    data: pd.DataFrame = Field(
        description="The market data as a pandas DataFrame. The DataFrame should have a DateTime index and columns for open, high, low, close, volume, etc."
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadata associated with the market data, such as the source of the data, the date it was fetched, etc.",
    )

    def save_to_parquet(self, filepath: Union[str, Path]) -> None:
        """Save market data to Parquet format.

        Args:
            filepath: Path to save the Parquet file
        """
        filepath = Path(filepath)

        # Ensure data has datetime index
        df = self._prepare_data_for_save()

        # Save to parquet
        df.to_parquet(filepath)

        # Save metadata separately if it exists
        self._save_metadata(filepath)

    def save_to_csv(self, filepath: Union[str, Path]) -> None:
        """Save market data to CSV format.

        Args:
            filepath: Path to save the CSV file
        """
        filepath = Path(filepath)

        # Ensure data has datetime index
        df = self._prepare_data_for_save()

        # Save to CSV with datetime index
        df.to_csv(filepath, index=True)

        # Save metadata separately if it exists
        self._save_metadata(filepath)

    def _save_metadata(self, filepath: Path) -> None:
        """Save metadata to a separate JSON file.

        Args:
            filepath: Path to the data file (metadata will be saved alongside)
        """
        if self.metadata:
            metadata_path = filepath.with_suffix(".metadata.json")
            with open(metadata_path, "w") as f:
                json.dump(self.metadata, f, indent=2, default=str)

    def _prepare_data_for_save(self) -> pd.DataFrame:
        """Prepare data for saving, ensuring proper format and required columns."""
        df = self.data.copy()

        # Ensure datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            if "date" in df.columns:
                df = df.set_index("date")
            elif "datetime" in df.columns:
                df = df.set_index("datetime")
            else:
                # Try to convert the current index to datetime
                try:
                    df.index = pd.to_datetime(df.index)
                except:
                    raise ValueError(
                        "Cannot convert index to datetime. Data must have a datetime index or 'date'/'datetime' column."
                    )

        # Ensure required OHLCV columns exist
        required_columns = ["open", "high", "low", "close", "volume"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Sort by date
        df = df.sort_index()

        return df

    @classmethod
    def load_from_parquet(
        cls, filepath: Union[str, Path], symbol: str = None
    ) -> "MarketData":
        """Load market data from Parquet format.

        Args:
            filepath: Path to the Parquet file
            symbol: Symbol for the market data (if not provided, will try to extract from filename)

        Returns:
            MarketData instance
        """
        filepath = Path(filepath)

        # Load data
        df = pd.read_parquet(filepath)

        return cls._create_from_loaded_data(df, filepath, symbol)

    @classmethod
    def load_from_csv(
        cls, filepath: Union[str, Path], symbol: str = None
    ) -> "MarketData":
        """Load market data from CSV format.

        Args:
            filepath: Path to the CSV file
            symbol: Symbol for the market data (if not provided, will try to extract from filename)

        Returns:
            MarketData instance
        """
        filepath = Path(filepath)

        # Load data with first column as index
        df = pd.read_csv(filepath, index_col=0, parse_dates=True)

        return cls._create_from_loaded_data(df, filepath, symbol)

    @classmethod
    def _create_from_loaded_data(
        cls, df: pd.DataFrame, filepath: Path, symbol: str = None
    ) -> "MarketData":
        """Create MarketData instance from loaded DataFrame and file path.

        Args:
            df: Loaded DataFrame
            filepath: Path to the file
            symbol: Symbol for the market data

        Returns:
            MarketData instance
        """
        # Load metadata if exists
        metadata = cls._load_metadata(filepath)

        # Extract symbol from metadata or filename if not provided
        if symbol is None:
            symbol = cls._extract_symbol_from_metadata_or_filename(metadata, filepath)

        # Ensure datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        return cls(symbol=symbol, data=df, metadata=metadata)

    @classmethod
    def _load_metadata(cls, filepath: Path) -> Optional[Dict[str, Any]]:
        """Load metadata from JSON file if it exists.

        Args:
            filepath: Path to the data file

        Returns:
            Metadata dictionary or None if file doesn't exist
        """
        metadata_path = filepath.with_suffix(".metadata.json")
        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                return json.load(f)
        return None

    @classmethod
    def _extract_symbol_from_metadata_or_filename(
        cls, metadata: Optional[Dict[str, Any]], filepath: Path
    ) -> str:
        """Extract symbol from metadata or filename.

        Args:
            metadata: Metadata dictionary
            filepath: Path to the file

        Returns:
            Symbol string
        """
        if metadata and "symbol" in metadata:
            return metadata["symbol"]
        else:
            return filepath.stem.upper()


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
