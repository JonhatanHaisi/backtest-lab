"""
Simple example demonstrating market data loading with Brazilian stock PETR3.SA
Shows how to save files with timeframe information in the filename.
"""
from datetime import datetime, timedelta
from pathlib import Path
from backtest_lab.data import StockDataLoader, DataFrequency

def main():
    # Create data directory
    data_dir = Path(".data")
    data_dir.mkdir(exist_ok=True)
    
    try:
        loader = StockDataLoader()
        
        print("=== Market Data Loading Example ===\n")
        
        # Load Brazilian stock data (daily)
        print("Loading Brazilian stock data (PETR3.SA - Daily)...")
        daily_data = loader.get_data(
            symbol="PETR3.SA",
            start_date=datetime.now() - timedelta(days=30),
            end_date=datetime.now(),
            frequency=DataFrequency.DAILY
        )
        
        print(f"✓ Loaded {len(daily_data.data)} rows for {daily_data.symbol}")
        print(f"  Date range: {daily_data.data.index.min().strftime('%Y-%m-%d')} to {daily_data.data.index.max().strftime('%Y-%m-%d')}")
        
        # Save with timeframe in filename
        print("\nSaving data with timeframe in filename...")
        saved_file = loader.save_data_with_timeframe(
            daily_data, 
            data_dir, 
            DataFrequency.DAILY, 
            format='parquet'
        )
        print(f"✓ Saved to: {saved_file}")
        
        # Load using file provider (will match the timeframe)
        print("\nLoading via file provider...")
        loader.add_file_provider(data_dir)
        
        # Load the same data using file provider with specific frequency
        loaded_data = loader.get_data(
            symbol="PETR3.SA", 
            frequency=DataFrequency.DAILY,
            provider="file"
        )
        print(f"✓ Loaded {len(loaded_data.data)} rows via file provider")
        
        # Show metadata with frequency info
        if loaded_data.metadata:
            print(f"  Frequency: {loaded_data.metadata.get('frequency', 'N/A')}")
            print(f"  Source: {Path(loaded_data.metadata.get('source_file', '')).name}")
        
        print("\n=== Example completed successfully! ===")
        
    finally:
        # Cleanup
        print(f"\nCleaning up...")
        if data_dir.exists():
            for file in data_dir.glob("*"):
                if file.is_file():
                    file.unlink()
            print(f"✓ Cleaned up {data_dir}")

if __name__ == "__main__":
    main()