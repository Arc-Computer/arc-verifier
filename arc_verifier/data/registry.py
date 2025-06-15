"""Data registry for tracking available market data and efficient caching."""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import pandas as pd
from rich.console import Console
from rich.table import Table


class DataRegistry:
    """Manages market data inventory and caching."""
    
    def __init__(self, data_dir: str = "market_data"):
        """Initialize data registry.
        
        Args:
            data_dir: Root directory for market data storage
        """
        self.console = Console()
        self.data_dir = Path(data_dir)
        self.cache_dir = self.data_dir / "cache"
        self.registry_file = self.data_dir / "registry.json"
        
        # Ensure directories exist
        self.data_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Load or create registry
        self.registry = self._load_registry()
        
    def _load_registry(self) -> Dict:
        """Load registry from file or create new one."""
        if self.registry_file.exists():
            with open(self.registry_file, 'r') as f:
                return json.load(f)
        else:
            return {
                "version": "1.0",
                "last_updated": datetime.now().isoformat(),
                "data_sources": {},
                "cached_files": {},
                "regime_windows": self._get_default_regimes()
            }
    
    def _save_registry(self):
        """Save registry to file."""
        self.registry["last_updated"] = datetime.now().isoformat()
        with open(self.registry_file, 'w') as f:
            json.dump(self.registry, f, indent=2)
    
    def _get_default_regimes(self) -> Dict[str, Dict]:
        """Get default market regime windows."""
        return {
            "bull_2024": {
                "start": "2024-10-01",
                "end": "2024-10-31",
                "description": "October 2024 bull run",
                "btc_range": [60000, 73000]
            },
            "bear_2024": {
                "start": "2024-05-01", 
                "end": "2024-05-31",
                "description": "May 2024 correction",
                "btc_range": [64000, 57000]
            },
            "volatile_2024": {
                "start": "2024-03-01",
                "end": "2024-03-31", 
                "description": "March 2024 high volatility",
                "btc_range": [61000, 71000]
            },
            "sideways_2024": {
                "start": "2024-07-01",
                "end": "2024-07-31",
                "description": "July 2024 consolidation",
                "btc_range": [63000, 68000]
            }
        }
    
    def register_raw_data(self, symbol: str, interval: str, date: str, file_path: Path):
        """Register a raw data file in the registry.
        
        Args:
            symbol: Trading pair symbol
            interval: Kline interval
            date: Date of the data
            file_path: Path to the data file
        """
        if "data_sources" not in self.registry:
            self.registry["data_sources"] = {}
            
        if symbol not in self.registry["data_sources"]:
            self.registry["data_sources"][symbol] = {}
            
        if interval not in self.registry["data_sources"][symbol]:
            self.registry["data_sources"][symbol][interval] = {}
            
        # Calculate file hash for integrity
        file_hash = self._calculate_file_hash(file_path)
        
        self.registry["data_sources"][symbol][interval][date] = {
            "path": str(file_path.relative_to(self.data_dir)),
            "size": file_path.stat().st_size,
            "hash": file_hash,
            "registered": datetime.now().isoformat()
        }
        
        self._save_registry()
    
    def get_cached_path(self, symbol: str, start_date: str, end_date: str, interval: str) -> Path:
        """Get path for cached parquet file.
        
        Args:
            symbol: Trading pair symbol
            start_date: Start date
            end_date: End date  
            interval: Kline interval
            
        Returns:
            Path to cached file
        """
        filename = f"{symbol}_{interval}_{start_date}_to_{end_date}.parquet"
        return self.cache_dir / filename
    
    def is_cached(self, symbol: str, start_date: str, end_date: str, interval: str) -> bool:
        """Check if data range is cached.
        
        Args:
            symbol: Trading pair symbol
            start_date: Start date
            end_date: End date
            interval: Kline interval
            
        Returns:
            True if cached file exists
        """
        cache_path = self.get_cached_path(symbol, start_date, end_date, interval)
        return cache_path.exists()
    
    def save_to_cache(self, df: pd.DataFrame, symbol: str, start_date: str, end_date: str, interval: str):
        """Save DataFrame to cache as parquet.
        
        Args:
            df: DataFrame to cache
            symbol: Trading pair symbol
            start_date: Start date
            end_date: End date
            interval: Kline interval
        """
        cache_path = self.get_cached_path(symbol, start_date, end_date, interval)
        
        # Save as parquet (much more efficient than CSV)
        df.to_parquet(cache_path, compression='snappy')
        
        # Update registry
        cache_key = f"{symbol}_{interval}_{start_date}_to_{end_date}"
        self.registry["cached_files"][cache_key] = {
            "path": str(cache_path.relative_to(self.data_dir)),
            "rows": len(df),
            "size": cache_path.stat().st_size,
            "created": datetime.now().isoformat()
        }
        
        self._save_registry()
        
    def load_from_cache(self, symbol: str, start_date: str, end_date: str, interval: str) -> Optional[pd.DataFrame]:
        """Load DataFrame from cache.
        
        Args:
            symbol: Trading pair symbol
            start_date: Start date
            end_date: End date
            interval: Kline interval
            
        Returns:
            Cached DataFrame or None if not found
        """
        cache_path = self.get_cached_path(symbol, start_date, end_date, interval)
        
        if cache_path.exists():
            try:
                return pd.read_parquet(cache_path)
            except Exception as e:
                self.console.print(f"[yellow]Warning: Failed to load cache: {e}[/yellow]")
                # Remove corrupted cache
                cache_path.unlink()
                return None
        
        return None
    
    def get_missing_dates(self, symbol: str, interval: str, start_date: str, end_date: str) -> List[str]:
        """Get list of missing dates for a symbol/interval combination.
        
        Args:
            symbol: Trading pair symbol
            interval: Kline interval
            start_date: Start date
            end_date: End date
            
        Returns:
            List of missing dates
        """
        missing = []
        
        # Check daily files
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        current = start
        
        while current <= end:
            date_str = current.strftime("%Y-%m-%d")
            
            # Check if we have this date in registry
            if (symbol not in self.registry.get("data_sources", {}) or
                interval not in self.registry["data_sources"][symbol] or
                date_str not in self.registry["data_sources"][symbol][interval]):
                
                # Also check if file exists on disk
                daily_path = self.data_dir / "daily" / symbol / interval / f"{symbol}-{interval}-{date_str}.zip"
                monthly_path = self.data_dir / "monthly" / symbol / interval / f"{symbol}-{interval}-{current.year}-{current.month:02d}.zip"
                
                if not daily_path.exists() and not monthly_path.exists():
                    missing.append(date_str)
                    
            current = datetime(current.year, current.month, current.day) + pd.Timedelta(days=1)
            
        return missing
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def print_summary(self):
        """Print a summary of available data."""
        table = Table(title="Market Data Registry Summary")
        table.add_column("Symbol", style="cyan")
        table.add_column("Interval", style="green")
        table.add_column("Date Range", style="yellow")
        table.add_column("Files", style="blue")
        table.add_column("Cached", style="magenta")
        
        # First, collect data from cached files
        cache_summary = {}
        for cache_key, cache_info in self.registry.get("cached_files", {}).items():
            # Parse cache key: SYMBOL_INTERVAL_START_to_END
            parts = cache_key.split("_")
            if len(parts) >= 5:
                symbol = parts[0]
                interval = parts[1]
                start_date = parts[2]
                end_date = parts[4]
                
                if symbol not in cache_summary:
                    cache_summary[symbol] = {}
                if interval not in cache_summary[symbol]:
                    cache_summary[symbol][interval] = {"dates": [], "count": 0}
                    
                cache_summary[symbol][interval]["dates"].extend([start_date, end_date])
                cache_summary[symbol][interval]["count"] += 1
        
        # Display cached data summary
        for symbol in sorted(cache_summary.keys()):
            for interval in sorted(cache_summary[symbol].keys()):
                dates = cache_summary[symbol][interval]["dates"]
                if dates:
                    date_range = f"{min(dates)} to {max(dates)}"
                    
                    # Count raw files
                    file_count = 0
                    if symbol in self.registry.get("data_sources", {}):
                        if interval in self.registry["data_sources"][symbol]:
                            file_count = len(self.registry["data_sources"][symbol][interval])
                    
                    cache_count = cache_summary[symbol][interval]["count"]
                    table.add_row(symbol, interval, date_range, str(file_count), str(cache_count))
        
        self.console.print(table)
        
        # Print regime windows
        if self.registry.get("regime_windows"):
            regime_table = Table(title="Market Regime Windows")
            regime_table.add_column("Regime", style="cyan")
            regime_table.add_column("Period", style="green")
            regime_table.add_column("Description", style="yellow")
            regime_table.add_column("BTC Range", style="blue")
            
            for regime, info in self.registry["regime_windows"].items():
                period = f"{info['start']} to {info['end']}"
                btc_range = f"${info['btc_range'][0]:,} - ${info['btc_range'][1]:,}"
                regime_table.add_row(regime, period, info['description'], btc_range)
                
            self.console.print("\n")
            self.console.print(regime_table)