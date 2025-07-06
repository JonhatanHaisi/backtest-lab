# Examples

This directory contains simplified examples demonstrating the core functionality of the backtest-lab library.

## data_loading.py

A comprehensive example showing how to:
- Load market data for Brazilian stocks (PETR3.SA)
- Save data to files with timeframe information in the filename
- Load data from files with specific timeframes
- Use the file provider system with frequency matching
- Clean up temporary files automatically

## multiple_timeframes.py

An advanced example demonstrating:
- Loading the same symbol with different timeframes (daily, weekly)
- Saving multiple timeframes simultaneously
- Discovering available symbols and timeframes
- Loading specific timeframes from saved files

## File Naming Convention

The library now uses a smart filename convention that includes the timeframe:
- Format: `{symbol}_{timeframe}.{extension}`
- Examples: `petr3.sa_1d.parquet`, `aapl_1wk.csv`, `msft_1m.parquet`

This allows you to save and load the same symbol with different timeframes:
- `PETR3.SA_1d.parquet` - Daily data
- `PETR3.SA_1wk.parquet` - Weekly data  
- `PETR3.SA_1m.parquet` - 1-minute data

## Running the Examples

```bash
# Run the basic data loading example
python docs/examples/data_loading.py

# Run the multiple timeframes example
python docs/examples/multiple_timeframes.py
```

## Data Storage

All examples save data to the `.data` directory, which is:
- Ignored by git (included in `.gitignore`)
- Automatically cleaned up after each example runs
- Used consistently across all examples and tests

This ensures that examples don't leave temporary files behind and maintain a clean project structure.
