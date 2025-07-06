"""
Advanced example demonstrating multiple timeframes for the same symbol.
Shows how to save and load PETR3.SA data with different frequencies.
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
        
        print("=== Multiple Timeframes Example ===\n")
        
        # Load the same symbol with different frequencies
        frequencies = [DataFrequency.DAILY, DataFrequency.WEEKLY]
        saved_files = []
        
        for frequency in frequencies:
            print(f"Loading PETR3.SA data ({frequency.value})...")
            
            # Adjust date range based on frequency
            if frequency == DataFrequency.DAILY:
                days = 30
            elif frequency == DataFrequency.WEEKLY:
                days = 90  # More days for weekly data
            else:
                days = 30
            
            data = loader.get_data(
                symbol="PETR3.SA",
                start_date=datetime.now() - timedelta(days=days),
                end_date=datetime.now(),
                frequency=frequency
            )
            
            print(f"✓ Loaded {len(data.data)} rows for {data.symbol} ({frequency.value})")
            
            # Save with timeframe in filename
            saved_file = loader.save_data_with_timeframe(
                data, 
                data_dir, 
                frequency, 
                format='parquet'
            )
            saved_files.append(saved_file)
            print(f"✓ Saved to: {saved_file.name}")
        
        # Now demonstrate loading specific timeframes
        print(f"\nLoading specific timeframes...")
        loader.add_file_provider(data_dir)
        
        # Show available symbols and timeframes
        file_provider = loader.providers['file']
        available_symbols = file_provider.get_available_symbols()
        combinations = file_provider.get_symbol_timeframe_combinations()
        
        print(f"Available symbols: {available_symbols}")
        for symbol, timeframes in combinations.items():
            timeframe_values = [tf.value for tf in timeframes]
            print(f"  {symbol}: {timeframe_values}")
        
        # Load each timeframe specifically
        for frequency in frequencies:
            print(f"\nLoading {frequency.value} data via file provider...")
            loaded_data = loader.get_data(
                symbol="PETR3.SA", 
                frequency=frequency,
                provider="file"
            )
            print(f"✓ Loaded {len(loaded_data.data)} rows for {frequency.value}")
            
            # Show first few rows to verify different data
            print(f"  First date: {loaded_data.data.index[0].strftime('%Y-%m-%d')}")
            print(f"  Last date: {loaded_data.data.index[-1].strftime('%Y-%m-%d')}")
            
            if loaded_data.metadata:
                print(f"  Source file: {Path(loaded_data.metadata['source_file']).name}")
        
        print("\n=== Multiple timeframes example completed! ===")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        print(f"\nCleaning up...")
        if data_dir.exists():
            files_removed = []
            for file in data_dir.glob("*"):
                if file.is_file():
                    files_removed.append(file.name)
                    file.unlink()
            if files_removed:
                print(f"✓ Removed files: {', '.join(files_removed)}")
            else:
                print(f"✓ No files to clean up")

if __name__ == "__main__":
    main()
