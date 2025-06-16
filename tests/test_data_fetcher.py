"""Tests for the data fetcher module."""

import pytest
from datetime import datetime, timedelta
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
import tempfile
import zipfile
import io
import urllib.error

from arc_verifier.data.fetcher import BinanceDataFetcher, MarketDataManager


class TestBinanceDataFetcher:
    """Test cases for BinanceDataFetcher."""
    
    @pytest.fixture
    def fetcher(self, tmp_path):
        """Create a BinanceDataFetcher instance with temp directory."""
        return BinanceDataFetcher(data_dir=str(tmp_path))
    
    @pytest.fixture
    def mock_kline_data(self):
        """Create mock kline data CSV content."""
        # 2024-01-01 00:00:00 UTC = 1704067200000 ms
        # 2024-01-01 01:00:00 UTC = 1704070800000 ms
        csv_content = """1704067200000,42000.0,42500.0,41800.0,42300.0,1500.5,1704070799999,63157500.0,3500,800.3,33733650.0,0
1704070800000,42300.0,42600.0,42100.0,42400.0,1200.2,1704074399999,50888480.0,2800,650.5,27599200.0,0"""
        return csv_content
    
    def test_init(self, tmp_path):
        """Test fetcher initialization."""
        fetcher = BinanceDataFetcher(data_dir=str(tmp_path))
        assert fetcher.data_dir.exists()
        assert fetcher.BASE_URL == "https://data.binance.vision"
    
    def test_invalid_interval(self, fetcher):
        """Test fetching with invalid interval."""
        with pytest.raises(ValueError, match="Invalid interval"):
            fetcher.fetch_klines("BTCUSDT", "2h", "2024-01-01", "2024-01-02")
    
    @patch('urllib.request.urlretrieve')
    def test_fetch_daily_klines(self, mock_urlretrieve, fetcher, mock_kline_data, tmp_path):
        """Test fetching daily klines data."""
        # Create mock zip file
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            zf.writestr("BTCUSDT-1h-2024-01-01.csv", mock_kline_data)
        zip_buffer.seek(0)
        
        # Mock the download to write our test zip
        # Only return data for the first day, 404 for the second
        def side_effect(url, filepath):
            if "2024-01-01" in url:
                with open(filepath, 'wb') as f:
                    f.write(zip_buffer.getvalue())
            else:
                raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
        
        mock_urlretrieve.side_effect = side_effect
        
        # Fetch data
        df = fetcher.fetch_klines("BTCUSDT", "1h", "2024-01-01", "2024-01-01")
        
        # Verify - we should only get 1 candle when filtering to exactly 2024-01-01
        # because the filter is based on date boundaries
        assert len(df) == 1
        assert df.iloc[0]['open'] == 42000.0
        assert df.iloc[0]['close'] == 42300.0
        assert isinstance(df.index[0], pd.Timestamp)
    
    def test_load_klines_from_zip(self, fetcher, mock_kline_data, tmp_path):
        """Test loading klines from zip file."""
        # Create test zip file
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("test.csv", mock_kline_data)
        
        # Load data
        df = fetcher._load_klines_from_zip(zip_path)
        
        # Verify columns and data (timestamp becomes index, so not in columns)
        expected_columns = [
            'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 
            'taker_buy_base', 'taker_buy_quote', 'ignore'
        ]
        assert list(df.columns) == expected_columns
        assert df.index.name == 'timestamp'
        assert len(df) == 2
        assert df['open'].dtype == float
        assert df['close'].dtype == float
    
    def test_get_symbols(self, fetcher):
        """Test getting list of symbols."""
        symbols = fetcher.get_symbols()
        assert isinstance(symbols, list)
        assert "BTCUSDT" in symbols
        assert "ETHUSDT" in symbols
        assert len(symbols) >= 10


class TestMarketDataManager:
    """Test cases for MarketDataManager."""
    
    @pytest.fixture
    def manager(self, tmp_path):
        """Create a MarketDataManager instance."""
        return MarketDataManager(data_dir=str(tmp_path))
    
    @patch.object(BinanceDataFetcher, 'fetch_klines')
    def test_fetch_market_data(self, mock_fetch, manager):
        """Test fetching market data for multiple symbols."""
        # Mock return data
        mock_df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=24, freq='h'),
            'open': [42000] * 24,
            'close': [42100] * 24,
            'volume': [100] * 24
        })
        mock_fetch.return_value = mock_df
        
        # Fetch data
        data = manager.fetch_market_data(
            symbols=["BTCUSDT", "ETHUSDT"],
            start_date="2024-01-01",
            end_date="2024-01-02"
        )
        
        # Verify
        assert len(data) == 2
        assert "BTCUSDT" in data
        assert "ETHUSDT" in data
        assert len(data["BTCUSDT"]) == 24
    
    def test_unsupported_source(self, manager):
        """Test using unsupported data source."""
        with pytest.raises(NotImplementedError, match="Source coinbase not yet implemented"):
            manager.fetch_market_data(
                symbols=["BTCUSDT"],
                start_date="2024-01-01",
                end_date="2024-01-02",
                source="coinbase"
            )
    
    @patch.object(MarketDataManager, 'fetch_market_data')
    def test_prepare_regime_data(self, mock_fetch, manager):
        """Test preparing regime data."""
        # Mock return data
        mock_data = {
            "BTCUSDT": pd.DataFrame({
                'timestamp': pd.date_range('2024-01-01', periods=24, freq='h'),
                'close': [42000 + i * 10 for i in range(24)]
            })
        }
        mock_fetch.return_value = mock_data
        
        # Custom regime windows
        regimes = {
            "test_bull": ("2024-01-01", "2024-01-02"),
            "test_bear": ("2024-02-01", "2024-02-02")
        }
        
        # Get regime data
        regime_data = manager.prepare_regime_data(
            symbols=["BTCUSDT"],
            regime_windows=regimes
        )
        
        # Verify
        assert len(regime_data) == 2
        assert "test_bull" in regime_data
        assert "test_bear" in regime_data
        assert "BTCUSDT" in regime_data["test_bull"]
        
    @patch.object(BinanceDataFetcher, 'fetch_klines')
    def test_fetch_market_data_error_handling(self, mock_fetch, manager):
        """Test error handling when fetching data."""
        # Make first call succeed, second fail
        mock_fetch.side_effect = [
            pd.DataFrame({'timestamp': [1], 'close': [42000]}),
            Exception("Network error")
        ]
        
        # Fetch data
        data = manager.fetch_market_data(
            symbols=["BTCUSDT", "ETHUSDT"],
            start_date="2024-01-01",
            end_date="2024-01-02"
        )
        
        # Should only have successful symbol
        assert len(data) == 1
        assert "BTCUSDT" in data
        assert "ETHUSDT" not in data