"""File-based data provider for loading market data from saved files."""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

from ..base import (
    DataFrequency,
    DataProvider,
    MarketData,
    MarketDataRequest,
    generate_filename,
    parse_filename,
)


class FileDataProvider(DataProvider):
    """Data provider for loading market data from local files."""

    def __init__(self, data_directory: Union[str, Path] = None):
        """Initialize FileDataProvider.

        Args:
            data_directory: Directory containing market data files. If None, uses current directory.
        """
        super().__init__()
        self.data_directory = Path(data_directory) if data_directory else Path.cwd()
        self.supported_formats = [".parquet", ".csv"]

    @property
    def provider_name(self) -> str:
        return "File Data Provider"

    def get_data(self, request: MarketDataRequest) -> MarketData:
        """Load market data from file based on the request.

        Args:
            request: Market data request

        Returns:
            MarketData instance

        Raises:
            FileNotFoundError: If no suitable file is found for the symbol
            ValueError: If file format is not supported
        """
        symbol = request.symbol
        frequency = request.frequency

        # Try to find a file for this symbol with the specific frequency
        file_path = self._find_file_for_symbol(symbol, frequency)

        if not file_path:
            raise FileNotFoundError(
                f"No data file found for symbol {symbol} with frequency {frequency.value} in {self.data_directory}"
            )

        # Load data based on file extension
        market_data = self._load_market_data_from_file(file_path, symbol)

        # Filter data by date range if specified
        if request.start_date or request.end_date:
            market_data = self._filter_by_date_range(
                market_data, request.start_date, request.end_date
            )

        # Add provider information to metadata
        self._add_provider_metadata(market_data, file_path, frequency)

        return market_data

    def _load_market_data_from_file(self, file_path: Path, symbol: str) -> MarketData:
        """Load market data from file based on its extension.

        Args:
            file_path: Path to the data file
            symbol: Symbol for the data

        Returns:
            MarketData instance

        Raises:
            ValueError: If file format is not supported
        """
        file_extension = file_path.suffix.lower()

        if file_extension == ".parquet":
            return MarketData.load_from_parquet(file_path, symbol)
        elif file_extension == ".csv":
            return MarketData.load_from_csv(file_path, symbol)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")

    def _add_provider_metadata(
        self, market_data: MarketData, file_path: Path, frequency: DataFrequency = None
    ) -> None:
        """Add provider metadata to market data.

        Args:
            market_data: MarketData instance to update
            file_path: Path to the source file
            frequency: Data frequency
        """
        if market_data.metadata is None:
            market_data.metadata = {}

        # Parse filename to get frequency if not provided
        if frequency is None:
            _, frequency = parse_filename(file_path.name)

        market_data.metadata.update(
            {
                "provider": self.provider_name,
                "source_file": str(file_path),
                "frequency": frequency.value if frequency else None,
                "loaded_at": datetime.now().isoformat(),
            }
        )

    def validate_symbol(self, symbol: str, frequency: DataFrequency = None) -> bool:
        """Check if a file exists for the given symbol and frequency.

        Args:
            symbol: Symbol to validate
            frequency: Optional frequency to check for specific timeframe

        Returns:
            True if file exists, False otherwise
        """
        return self._find_file_for_symbol(symbol, frequency) is not None

    def get_available_symbols(self) -> List[str]:
        """Get list of available symbols based on files in the data directory.

        Returns:
            List of unique symbols (without timeframe info)
        """
        symbols = set()

        if not self.data_directory.exists():
            return []

        for file_path in self.data_directory.iterdir():
            if (
                file_path.is_file()
                and file_path.suffix.lower() in self.supported_formats
            ):
                # Parse filename to extract symbol and frequency
                symbol, frequency = parse_filename(file_path.name)
                symbols.add(symbol)

        return sorted(list(symbols))

    def _find_file_for_symbol(
        self, symbol: str, frequency: DataFrequency = None
    ) -> Optional[Path]:
        """Find a data file for the given symbol and frequency.

        Args:
            symbol: Symbol to search for
            frequency: Optional frequency to match specific timeframe

        Returns:
            Path to the file if found, None otherwise
        """
        if not self.data_directory.exists():
            return None

        # If frequency is specified, look for exact match first
        if frequency:
            for extension in self.supported_formats:
                filename = generate_filename(symbol, frequency, extension)
                file_path = self.data_directory / filename
                if file_path.exists():
                    return file_path

        # Fallback: look for any file with the symbol (legacy support)
        symbol_lower = symbol.lower()
        symbol_upper = symbol.upper()

        # Try different naming conventions and formats
        for file_pattern in [symbol_lower, symbol_upper, symbol]:
            for extension in self.supported_formats:
                file_path = self.data_directory / f"{file_pattern}{extension}"
                if file_path.exists():
                    return file_path

        # Try to find any file that starts with the symbol
        for file_path in self.data_directory.iterdir():
            if (
                file_path.is_file()
                and file_path.suffix.lower() in self.supported_formats
            ):
                parsed_symbol, parsed_frequency = parse_filename(file_path.name)
                if parsed_symbol == symbol.upper():
                    return file_path

        return None

    def _filter_by_date_range(
        self,
        market_data: MarketData,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> MarketData:
        """Filter market data by date range.

        Args:
            market_data: Original market data
            start_date: Start date for filtering
            end_date: End date for filtering

        Returns:
            Filtered MarketData instance
        """
        df = market_data.data.copy()

        # Handle timezone-aware datetime comparison
        if start_date:
            # Convert start_date to match the timezone of the index
            if hasattr(df.index, "tz") and df.index.tz is not None:
                if start_date.tzinfo is None:
                    # Make start_date timezone-aware using the same timezone as the index
                    start_date = start_date.replace(tzinfo=df.index.tz)
                else:
                    # Convert to the same timezone as the index
                    start_date = start_date.astimezone(df.index.tz)
            elif start_date.tzinfo is not None:
                # If index is timezone-naive but start_date is timezone-aware, convert to naive
                start_date = start_date.replace(tzinfo=None)

            df = df[df.index >= start_date]

        if end_date:
            # Convert end_date to match the timezone of the index
            if hasattr(df.index, "tz") and df.index.tz is not None:
                if end_date.tzinfo is None:
                    # Make end_date timezone-aware using the same timezone as the index
                    end_date = end_date.replace(tzinfo=df.index.tz)
                else:
                    # Convert to the same timezone as the index
                    end_date = end_date.astimezone(df.index.tz)
            elif end_date.tzinfo is not None:
                # If index is timezone-naive but end_date is timezone-aware, convert to naive
                end_date = end_date.replace(tzinfo=None)

            df = df[df.index <= end_date]

        # Update metadata
        metadata = market_data.metadata.copy() if market_data.metadata else {}
        metadata.update(
            {
                "filtered": True,
                "filter_start_date": start_date.isoformat() if start_date else None,
                "filter_end_date": end_date.isoformat() if end_date else None,
                "original_rows": len(market_data.data),
                "filtered_rows": len(df),
            }
        )

        return MarketData(symbol=market_data.symbol, data=df, metadata=metadata)

    def list_files(self) -> Dict[str, List[Path]]:
        """List all available data files organized by format.

        Returns:
            Dictionary with format as key and list of file paths as values
        """
        files_by_format = {ext: [] for ext in self.supported_formats}

        if not self.data_directory.exists():
            return files_by_format

        for file_path in self.data_directory.iterdir():
            if (
                file_path.is_file()
                and file_path.suffix.lower() in self.supported_formats
            ):
                files_by_format[file_path.suffix.lower()].append(file_path)

        return files_by_format

    def get_available_timeframes(self, symbol: str) -> List[DataFrequency]:
        """Get list of available timeframes for a specific symbol.

        Args:
            symbol: Symbol to check

        Returns:
            List of available DataFrequency values for the symbol
        """
        timeframes = []

        if not self.data_directory.exists():
            return timeframes

        symbol_upper = symbol.upper()

        for file_path in self.data_directory.iterdir():
            if (
                file_path.is_file()
                and file_path.suffix.lower() in self.supported_formats
            ):
                parsed_symbol, parsed_frequency = parse_filename(file_path.name)
                if parsed_symbol == symbol_upper and parsed_frequency:
                    timeframes.append(parsed_frequency)

        return sorted(timeframes, key=lambda x: x.value)

    def get_symbol_timeframe_combinations(self) -> Dict[str, List[DataFrequency]]:
        """Get all symbol-timeframe combinations available.

        Returns:
            Dictionary mapping symbols to their available timeframes
        """
        combinations = {}

        if not self.data_directory.exists():
            return combinations

        for file_path in self.data_directory.iterdir():
            if (
                file_path.is_file()
                and file_path.suffix.lower() in self.supported_formats
            ):
                symbol, frequency = parse_filename(file_path.name)
                if symbol not in combinations:
                    combinations[symbol] = []
                if frequency and frequency not in combinations[symbol]:
                    combinations[symbol].append(frequency)

        # Sort timeframes for each symbol
        for symbol in combinations:
            combinations[symbol].sort(key=lambda x: x.value)

        return combinations
