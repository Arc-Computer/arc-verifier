#!/usr/bin/env python3
"""Helper script to download market data for Arc-Verifier performance testing.

Usage:
    python scripts/download_market_data.py --help
    python scripts/download_market_data.py --regimes  # Download default regime data
    python scripts/download_market_data.py --symbol BTCUSDT --start 2024-01-01 --end 2024-01-31
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from arc_verifier.data_fetcher import MarketDataManager
from rich.console import Console
from rich.progress import track

console = Console()


def download_regime_data(manager: MarketDataManager, symbols: list):
    """Download data for all pre-defined market regimes."""
    console.print("\n[bold cyan]Downloading Market Regime Data[/bold cyan]\n")
    
    # Get regime windows from registry
    regime_windows = {}
    for regime_name, regime_info in manager.registry.registry.get("regime_windows", {}).items():
        regime_windows[regime_name] = (regime_info["start"], regime_info["end"])
        console.print(f"[yellow]{regime_name}:[/yellow] {regime_info['description']}")
        console.print(f"  Period: {regime_info['start']} to {regime_info['end']}")
        console.print(f"  BTC Range: ${regime_info['btc_range'][0]:,} - ${regime_info['btc_range'][1]:,}\n")
    
    # Download data for each regime
    for regime, (start, end) in regime_windows.items():
        console.print(f"\n[cyan]Downloading {regime} data...[/cyan]")
        for symbol in track(symbols, description=f"Fetching {regime}"):
            try:
                manager.binance.fetch_klines(symbol, "1h", start, end)
            except Exception as e:
                console.print(f"[red]Error fetching {symbol}: {e}[/red]")


def download_custom_range(manager: MarketDataManager, symbol: str, start: str, end: str, interval: str):
    """Download data for a custom date range."""
    console.print(f"\n[bold cyan]Downloading {symbol} {interval} data[/bold cyan]")
    console.print(f"Period: {start} to {end}\n")
    
    try:
        df = manager.binance.fetch_klines(symbol, interval, start, end)
        console.print(f"[green]✓ Downloaded {len(df)} candles[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Download market data for Arc-Verifier testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download all regime data for default symbols
  python scripts/download_market_data.py --regimes
  
  # Download specific symbol and date range
  python scripts/download_market_data.py --symbol BTCUSDT --start 2024-01-01 --end 2024-01-31
  
  # Download multiple symbols for regimes
  python scripts/download_market_data.py --regimes --symbols BTCUSDT ETHUSDT SOLUSDT NEARUSDT
  
  # Show data summary
  python scripts/download_market_data.py --summary
        """
    )
    
    parser.add_argument("--regimes", action="store_true", 
                       help="Download data for pre-defined market regimes")
    parser.add_argument("--symbol", type=str, 
                       help="Symbol to download (e.g., BTCUSDT)")
    parser.add_argument("--start", type=str, 
                       help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, 
                       help="End date (YYYY-MM-DD)")
    parser.add_argument("--interval", type=str, default="1h",
                       choices=["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
                       help="Kline interval (default: 1h)")
    parser.add_argument("--symbols", nargs="+", 
                       default=["BTCUSDT", "ETHUSDT", "SOLUSDT"],
                       help="Symbols to download for regime data")
    parser.add_argument("--data-dir", type=str, default="market_data",
                       help="Directory to store data (default: market_data)")
    parser.add_argument("--summary", action="store_true",
                       help="Show summary of available data")
    
    args = parser.parse_args()
    
    # Initialize manager
    manager = MarketDataManager(args.data_dir)
    
    # Handle different modes
    if args.summary:
        manager.show_data_summary()
    elif args.regimes:
        download_regime_data(manager, args.symbols)
        console.print("\n[green]✓ Regime data download complete![/green]")
        manager.show_data_summary()
    elif args.symbol and args.start and args.end:
        download_custom_range(manager, args.symbol, args.start, args.end, args.interval)
        manager.show_data_summary()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()