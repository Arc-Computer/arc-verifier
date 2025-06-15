# Market Data Directory

This directory contains historical cryptocurrency market data used for Arc-Verifier's performance verification testing.

## Directory Structure

```
market_data/
├── README.md              # This file
├── registry.json          # Data inventory and metadata
├── cache/                 # Processed data in Parquet format (faster loading)
│   └── BTCUSDT_1h_2024-01-01_to_2024-01-31.parquet
├── daily/                 # Raw daily data from Binance (ZIP files)
│   └── BTCUSDT/
│       └── 1h/
│           └── BTCUSDT-1h-2024-01-01.zip
└── monthly/               # Raw monthly data from Binance (ZIP files)
    └── BTCUSDT/
        └── 1h/
            └── BTCUSDT-1h-2024-01.zip
```

## Data Format

### Raw Data (ZIP files)
- Source: Binance public data repository
- Format: Compressed CSV files
- Columns: timestamp, open, high, low, close, volume, close_time, quote_volume, trades, taker_buy_base, taker_buy_quote, ignore

### Cached Data (Parquet files)
- Format: Apache Parquet (columnar storage)
- Compression: Snappy
- Contains: Processed DataFrame with datetime index
- Benefits: 5-10x faster loading, 50% smaller size

## Pre-defined Market Regimes

The tool includes pre-defined 30-day windows representing different market conditions:

| Regime | Period | Description | BTC Range |
|--------|--------|-------------|-----------|
| bull_2024 | Oct 2024 | October bull run | $60k - $73k |
| bear_2024 | May 2024 | May correction | $64k - $57k |
| volatile_2024 | Mar 2024 | High volatility | $61k - $71k |
| sideways_2024 | Jul 2024 | Consolidation | $63k - $68k |

## Downloading Data

Use the provided download script:

```bash
# Download all regime data for default symbols
python scripts/download_market_data.py --regimes

# Download specific symbol and date range
python scripts/download_market_data.py --symbol BTCUSDT --start 2024-01-01 --end 2024-01-31

# Show data summary
python scripts/download_market_data.py --summary
```

## Data Sources

1. **Binance** (Primary)
   - Public data repository: https://data.binance.vision/
   - No API key required
   - Historical spot market data

2. **Coinbase** (Future)
   - REST API: https://docs.cdp.coinbase.com/
   - Requires API key for historical data
   - Backup data source

## Storage Requirements

Approximate sizes:
- 1 symbol, 1 month, 1h candles: ~500 KB (ZIP), ~200 KB (Parquet)
- 10 symbols, 4 regimes (4 months): ~20 MB total
- Full year of data for 10 symbols: ~60 MB

## Adding Custom Data

To add your own historical data:

1. Follow the Binance CSV format
2. Compress as ZIP
3. Place in appropriate directory structure
4. Run verification to update registry

## Performance Tips

1. **Use Cached Data**: The tool automatically caches fetched data as Parquet files
2. **Pre-download Regimes**: Run `download_market_data.py --regimes` before testing
3. **Parallel Processing**: The tool can process multiple symbols in parallel
4. **Memory Efficiency**: Data is loaded in chunks when needed

## Troubleshooting

**Missing Data**: If data download fails, check:
- Internet connection
- Binance data availability for the requested date
- Sufficient disk space

**Corrupted Cache**: If cache loading fails:
- Delete the corrupted `.parquet` file
- The tool will re-fetch and cache the data

**Performance Issues**: For large datasets:
- Use specific date ranges instead of full history
- Consider using monthly files for long-term data
- Increase system RAM for extensive backtesting