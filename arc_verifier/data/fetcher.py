"""Historical market data fetcher for performance verification.

This module provides interfaces to fetch historical price data from:
1. Binance: Downloads historical klines data from public data repository
2. Coinbase: Fetches candles data via API (future implementation)
"""

import os
import time
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import urllib.request
import pandas as pd
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .registry import DataRegistry


class BinanceDataFetcher:
    """Fetches historical klines data from Binance public data repository."""
    
    BASE_URL = "https://data.binance.vision"
    INTERVALS = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
    
    def __init__(self, data_dir: str = "market_data"):
        """Initialize Binance data fetcher.
        
        Args:
            data_dir: Directory to store downloaded data
        """
        self.console = Console()
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.registry = DataRegistry(data_dir)
        
    def fetch_klines(self, 
                    symbol: str,
                    interval: str,
                    start_date: str,
                    end_date: str,
                    force_download: bool = False) -> pd.DataFrame:
        """Fetch historical klines data for a symbol.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            interval: Kline interval (e.g., '1h', '1d')
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            force_download: Force re-download even if files exist
            
        Returns:
            DataFrame with OHLCV data
        """
        if interval not in self.INTERVALS:
            raise ValueError(f"Invalid interval. Must be one of {self.INTERVALS}")
            
        # Check cache first (unless force download)
        if not force_download and self.registry.is_cached(symbol, start_date, end_date, interval):
            self.console.print(f"[green]Loading {symbol} from cache[/green]")
            df = self.registry.load_from_cache(symbol, start_date, end_date, interval)
            if df is not None:
                return df
                
        # Convert dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Download required files
        self.console.print(f"[blue]Fetching {symbol} {interval} data from {start_date} to {end_date}[/blue]")
        
        all_data = []
        
        # Determine if we need daily or monthly files based on date range
        days_diff = (end - start).days
        
        if days_diff <= 35:  # Use daily files for short ranges
            all_data.extend(self._fetch_daily_files(symbol, interval, start, end, force_download))
        else:  # Use monthly files for longer ranges
            all_data.extend(self._fetch_monthly_files(symbol, interval, start, end, force_download))
            
        if not all_data:
            self.console.print("[red]No data found for the specified date range[/red]")
            return pd.DataFrame()
            
        # Combine all data
        df = pd.concat(all_data)
        
        # Sort by index (timestamp)
        df = df.sort_index()
        
        # Filter to exact date range
        df = df[(df.index >= start) & (df.index <= end)]
        
        self.console.print(f"[green]Loaded {len(df)} candles[/green]")
        
        # Cache the result for future use
        if not df.empty:
            self.registry.save_to_cache(df, symbol, start_date, end_date, interval)
        
        return df
    
    def _fetch_daily_files(self, 
                          symbol: str,
                          interval: str,
                          start: datetime,
                          end: datetime,
                          force_download: bool) -> List[pd.DataFrame]:
        """Fetch daily kline files."""
        dataframes = []
        current = start
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Downloading daily files...", total=None)
            
            while current <= end:
                date_str = current.strftime("%Y-%m-%d")
                
                try:
                    df = self._download_and_load_daily(symbol, interval, date_str, force_download)
                    if df is not None:
                        dataframes.append(df)
                except Exception as e:
                    self.console.print(f"[yellow]Warning: Failed to fetch {date_str}: {e}[/yellow]")
                
                current += timedelta(days=1)
                
        return dataframes
    
    def _fetch_monthly_files(self,
                           symbol: str,
                           interval: str,
                           start: datetime,
                           end: datetime,
                           force_download: bool) -> List[pd.DataFrame]:
        """Fetch monthly kline files."""
        dataframes = []
        
        # Calculate months to fetch
        current = datetime(start.year, start.month, 1)
        end_month = datetime(end.year, end.month, 1)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task("Downloading monthly files...", total=None)
            
            while current <= end_month:
                year = current.year
                month = current.month
                
                try:
                    df = self._download_and_load_monthly(symbol, interval, year, month, force_download)
                    if df is not None:
                        dataframes.append(df)
                except Exception as e:
                    self.console.print(f"[yellow]Warning: Failed to fetch {year}-{month:02d}: {e}[/yellow]")
                
                # Move to next month
                if month == 12:
                    current = datetime(year + 1, 1, 1)
                else:
                    current = datetime(year, month + 1, 1)
                    
        return dataframes
    
    def _download_and_load_daily(self,
                               symbol: str,
                               interval: str,
                               date: str,
                               force_download: bool) -> Optional[pd.DataFrame]:
        """Download and load a daily klines file."""
        filename = f"{symbol}-{interval}-{date}.zip"
        filepath = self.data_dir / "daily" / symbol / interval / filename
        
        if not filepath.exists() or force_download:
            # Download file
            url = f"{self.BASE_URL}/data/spot/daily/klines/{symbol}/{interval}/{filename}"
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                urllib.request.urlretrieve(url, filepath)
                time.sleep(0.1)  # Be nice to the server
                # Register in data registry
                self.registry.register_raw_data(symbol, interval, date, filepath)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return None  # File doesn't exist
                raise
                
        # Load data
        return self._load_klines_from_zip(filepath)
    
    def _download_and_load_monthly(self,
                                 symbol: str,
                                 interval: str,
                                 year: int,
                                 month: int,
                                 force_download: bool) -> Optional[pd.DataFrame]:
        """Download and load a monthly klines file."""
        filename = f"{symbol}-{interval}-{year}-{month:02d}.zip"
        filepath = self.data_dir / "monthly" / symbol / interval / filename
        
        if not filepath.exists() or force_download:
            # Download file
            url = f"{self.BASE_URL}/data/spot/monthly/klines/{symbol}/{interval}/{filename}"
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                urllib.request.urlretrieve(url, filepath)
                time.sleep(0.1)  # Be nice to the server
                # Register in data registry
                self.registry.register_raw_data(symbol, interval, f"{year}-{month:02d}", filepath)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return None  # File doesn't exist
                raise
                
        # Load data
        return self._load_klines_from_zip(filepath)
    
    def _load_klines_from_zip(self, filepath: Path) -> pd.DataFrame:
        """Load klines data from a zip file."""
        # Extract and read CSV
        with zipfile.ZipFile(filepath, 'r') as z:
            # Get the CSV filename (should be the only file)
            csv_name = z.namelist()[0]
            
            # Read directly from zip
            with z.open(csv_name) as f:
                df = pd.read_csv(f, header=None)
                
        # Set column names according to Binance format
        df.columns = [
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 
            'taker_buy_base', 'taker_buy_quote', 'ignore'
        ]
        
        # Convert timestamp to datetime (from milliseconds)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Convert numeric columns
        numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'quote_volume']
        df[numeric_cols] = df[numeric_cols].astype(float)
        
        # Set timestamp as index
        df.set_index('timestamp', inplace=True)
        
        return df
    
    def get_symbols(self) -> List[str]:
        """Get list of commonly traded symbols."""
        # Return a curated list of liquid trading pairs
        return [
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
            "SOLUSDT", "DOGEUSDT", "MATICUSDT", "AVAXUSDT", "LINKUSDT",
            "UNIUSDT", "LTCUSDT", "NEARUSDT", "ATOMUSDT", "FTMUSDT"
        ]


class MarketDataManager:
    """Manages market data fetching and caching for performance verification."""
    
    def __init__(self, data_dir: str = "market_data"):
        """Initialize market data manager."""
        self.console = Console()
        self.binance = BinanceDataFetcher(data_dir)
        self.registry = DataRegistry(data_dir)
        # TODO: Add Coinbase fetcher when needed
        
    def fetch_market_data(self,
                         symbols: List[str],
                         start_date: str,
                         end_date: str,
                         interval: str = "1h",
                         source: str = "binance") -> Dict[str, pd.DataFrame]:
        """Fetch market data for multiple symbols.
        
        Args:
            symbols: List of trading symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: Kline interval
            source: Data source ('binance' or 'coinbase')
            
        Returns:
            Dictionary mapping symbols to DataFrames
        """
        if source != "binance":
            raise NotImplementedError(f"Source {source} not yet implemented")
            
        data = {}
        
        for symbol in symbols:
            try:
                df = self.binance.fetch_klines(symbol, interval, start_date, end_date)
                if not df.empty:
                    data[symbol] = df
            except Exception as e:
                self.console.print(f"[red]Error fetching {symbol}: {e}[/red]")
                
        return data
    
    def prepare_regime_data(self,
                          symbols: List[str] = None,
                          regime_windows: Dict[str, Tuple[str, str]] = None) -> Dict[str, Dict[str, pd.DataFrame]]:
        """Prepare market data for different market regimes.
        
        Args:
            symbols: Trading symbols (defaults to major pairs)
            regime_windows: Dict of regime name to (start_date, end_date)
            
        Returns:
            Nested dict: {regime: {symbol: DataFrame}}
        """
        if symbols is None:
            symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
            
        if regime_windows is None:
            # Use regime windows from registry
            regime_windows = {}
            for regime_name, regime_info in self.registry.registry.get("regime_windows", {}).items():
                regime_windows[regime_name] = (regime_info["start"], regime_info["end"])
            
        regime_data = {}
        
        for regime, (start, end) in regime_windows.items():
            self.console.print(f"\n[cyan]Fetching {regime} market regime data[/cyan]")
            regime_data[regime] = self.fetch_market_data(symbols, start, end)
            
        return regime_data
    
    def show_data_summary(self):
        """Display a summary of available data."""
        self.registry.print_summary()