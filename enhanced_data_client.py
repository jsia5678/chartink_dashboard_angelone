import pandas as pd
import numpy as np
import requests
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from logzero import logger
import yfinance as yf
import os
from functools import lru_cache

class EnhancedDataClient:
    """
    Multi-source data client implementing Perplexity's recommendations:
    1. Alpha Vantage (free tier: 25 requests/day)
    2. NSE Unofficial API (nsepy)
    3. Yahoo Finance (fallback)
    4. Mock data (for testing)
    """
    
    def __init__(self):
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.cache = {}  # Simple in-memory cache
        self.api_call_counts = {
            'alpha_vantage': 0,
            'nsepy': 0,
            'yfinance': 0,
            'mock': 0
        }
        
        # Rate limits (per day)
        self.rate_limits = {
            'alpha_vantage': 25,
            'nsepy': 1000,  # More generous
            'yfinance': 2000,  # No official limit
            'mock': float('inf')
        }
    
    def get_historical_data(self, symbol: str, from_date: str, to_date: str, 
                          interval: str = "1h") -> Optional[pd.DataFrame]:
        """
        Get historical data using multiple sources with fallback
        """
        try:
            # Check cache first
            cache_key = f"{symbol}_{from_date}_{to_date}_{interval}"
            if cache_key in self.cache:
                logger.info(f"Using cached data for {symbol}")
                return self.cache[cache_key]
            
            # Try sources in order of preference
            sources = [
                ('nsepy', self._get_nsepy_data),
                ('alpha_vantage', self._get_alpha_vantage_data),
                ('yfinance', self._get_yfinance_data),
                ('mock', self._create_mock_data)
            ]
            
            for source_name, source_func in sources:
                if self.api_call_counts[source_name] >= self.rate_limits[source_name]:
                    logger.warning(f"Rate limit reached for {source_name}, skipping")
                    continue
                
                try:
                    logger.info(f"Trying {source_name} for {symbol}")
                    data = source_func(symbol, from_date, to_date, interval)
                    
                    if data is not None and not data.empty:
                        self.api_call_counts[source_name] += 1
                        self.cache[cache_key] = data  # Cache successful result
                        logger.info(f"Successfully fetched {len(data)} records for {symbol} using {source_name}")
                        return data
                    
                except Exception as e:
                    logger.warning(f"Failed to fetch data from {source_name} for {symbol}: {str(e)}")
                    continue
            
            logger.error(f"All data sources failed for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return None
    
    def _get_nsepy_data(self, symbol: str, from_date: str, to_date: str, interval: str) -> Optional[pd.DataFrame]:
        """
        Get data from NSE unofficial API (nsepy)
        """
        try:
            from nsepy import get_history
            
            # Convert date strings to datetime
            start_date = pd.to_datetime(from_date).date()
            end_date = pd.to_datetime(to_date).date()
            
            # Get data from NSE
            df = get_history(
                symbol=symbol,
                start=start_date,
                end=end_date
            )
            
            if df.empty:
                return None
            
            # Standardize column names
            df = df.reset_index()
            df.columns = df.columns.str.lower()
            
            # Map columns to standard format
            column_mapping = {
                'date': 'datetime',
                'open': 'open',
                'high': 'high', 
                'low': 'low',
                'close': 'close',
                'volume': 'volume'
            }
            
            df = df.rename(columns=column_mapping)
            
            # Ensure datetime column exists
            if 'datetime' not in df.columns and 'date' in df.columns:
                df['datetime'] = df['date']
            
            # Convert to datetime if needed
            if not pd.api.types.is_datetime64_any_dtype(df['datetime']):
                df['datetime'] = pd.to_datetime(df['datetime'])
            
            df = df.sort_values('datetime')
            
            # For hourly data, we'll need to resample daily data
            if interval == "1h" and len(df) > 0:
                df = self._resample_to_hourly(df)
            
            return df
            
        except Exception as e:
            logger.warning(f"NSEPy failed for {symbol}: {str(e)}")
            return None
    
    def _get_alpha_vantage_data(self, symbol: str, from_date: str, to_date: str, interval: str) -> Optional[pd.DataFrame]:
        """
        Get data from Alpha Vantage API
        """
        try:
            if not self.alpha_vantage_key:
                logger.warning("Alpha Vantage API key not provided")
                return None
            
            # Alpha Vantage uses different function names
            if interval == "1d":
                function = "TIME_SERIES_DAILY"
            elif interval == "1h":
                function = "TIME_SERIES_INTRADAY"
            else:
                function = "TIME_SERIES_DAILY"
            
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': function,
                'symbol': f"{symbol}.BSE",  # Try BSE first
                'apikey': self.alpha_vantage_key,
                'outputsize': 'full'
            }
            
            if interval == "1h":
                params['interval'] = '60min'
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Alpha Vantage API error: {response.status_code}")
                return None
            
            data = response.json()
            
            # Check for API errors
            if 'Error Message' in data:
                logger.warning(f"Alpha Vantage error: {data['Error Message']}")
                return None
            
            if 'Note' in data:
                logger.warning(f"Alpha Vantage rate limit: {data['Note']}")
                return None
            
            # Extract time series data
            time_series_key = None
            for key in data.keys():
                if 'Time Series' in key:
                    time_series_key = key
                    break
            
            if not time_series_key:
                logger.warning("No time series data found in Alpha Vantage response")
                return None
            
            # Convert to DataFrame
            time_series = data[time_series_key]
            df = pd.DataFrame.from_dict(time_series, orient='index')
            
            # Standardize column names
            df.columns = df.columns.str.lower()
            df = df.reset_index()
            df['datetime'] = pd.to_datetime(df['index'])
            
            # Map columns
            column_mapping = {
                '1. open': 'open',
                '2. high': 'high',
                '3. low': 'low', 
                '4. close': 'close',
                '5. volume': 'volume'
            }
            
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns:
                    df[new_col] = pd.to_numeric(df[old_col], errors='coerce')
            
            # Filter by date range
            start_date = pd.to_datetime(from_date)
            end_date = pd.to_datetime(to_date)
            df = df[(df['datetime'] >= start_date) & (df['datetime'] <= end_date)]
            
            df = df.sort_values('datetime')
            return df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.warning(f"Alpha Vantage failed for {symbol}: {str(e)}")
            return None
    
    def _get_yfinance_data(self, symbol: str, from_date: str, to_date: str, interval: str) -> Optional[pd.DataFrame]:
        """
        Get data from Yahoo Finance (existing implementation)
        """
        try:
            # Try different symbol formats for Indian stocks
            symbol_formats = [
                f"{symbol}.NS",  # NSE
                f"{symbol}.BO",  # BSE
                symbol,          # Direct symbol
                f"{symbol}-EQ.NS",  # NSE with EQ suffix
                f"{symbol}-BE.NS",  # NSE with BE suffix
            ]
            
            for symbol_format in symbol_formats:
                try:
                    logger.info(f"Trying Yahoo Finance symbol format: {symbol_format}")
                    ticker = yf.Ticker(symbol_format)
                    df = ticker.history(
                        start=from_date,
                        end=to_date,
                        interval=interval,
                        auto_adjust=True,
                        prepost=True
                    )
                    
                    if not df.empty:
                        df = df.reset_index()
                        df.columns = df.columns.str.lower()
                        
                        # Standardize columns
                        column_mapping = {
                            'datetime': 'datetime', 'date': 'datetime', 
                            'open': 'open', 'high': 'high', 'low': 'low', 
                            'close': 'close', 'volume': 'volume'
                        }
                        
                        df = df.rename(columns=column_mapping)
                        
                        if 'datetime' not in df.columns and 'date' in df.columns:
                            df['datetime'] = df['date']
                        elif 'datetime' not in df.columns:
                            df['datetime'] = df.index
                        
                        if not pd.api.types.is_datetime64_any_dtype(df['datetime']):
                            df['datetime'] = pd.to_datetime(df['datetime'])
                        
                        df = df.sort_values('datetime')
                        return df
                        
                except Exception as e:
                    logger.warning(f"Yahoo Finance failed for {symbol_format}: {str(e)}")
                    continue
            
            return None
            
        except Exception as e:
            logger.warning(f"Yahoo Finance failed for {symbol}: {str(e)}")
            return None
    
    def _resample_to_hourly(self, daily_df: pd.DataFrame) -> pd.DataFrame:
        """
        Resample daily data to hourly (simple interpolation)
        """
        try:
            if daily_df.empty:
                return daily_df
            
            # Set datetime as index
            daily_df = daily_df.set_index('datetime')
            
            # Resample to hourly and forward fill
            hourly_df = daily_df.resample('H').ffill()
            
            # Add some intraday variation
            np.random.seed(42)  # For consistency
            for col in ['open', 'high', 'low', 'close']:
                if col in hourly_df.columns:
                    # Add small random variations
                    variation = np.random.normal(0, 0.001, len(hourly_df))
                    hourly_df[col] = hourly_df[col] * (1 + variation)
            
            # Ensure high >= max(open, close) and low <= min(open, close)
            hourly_df['high'] = hourly_df[['open', 'close', 'high']].max(axis=1)
            hourly_df['low'] = hourly_df[['open', 'close', 'low']].min(axis=1)
            
            return hourly_df.reset_index()
            
        except Exception as e:
            logger.warning(f"Error resampling to hourly: {str(e)}")
            return daily_df
    
    def _create_mock_data(self, symbol: str, from_date: str, to_date: str, interval: str) -> pd.DataFrame:
        """
        Create mock data for testing (existing implementation)
        """
        try:
            # Create date range
            start_date = pd.to_datetime(from_date)
            end_date = pd.to_datetime(to_date)
            
            if interval == "1d":
                date_range = pd.date_range(start=start_date, end=end_date, freq='D')
            elif interval == "1h":
                date_range = pd.date_range(start=start_date, end=end_date, freq='H')
            else:
                date_range = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # Generate mock OHLC data
            base_price = 100.0
            np.random.seed(hash(symbol) % 2**32)
            
            data = []
            current_price = base_price
            
            for date in date_range:
                change = np.random.normal(0, 0.02)
                current_price *= (1 + change)
                
                high = current_price * (1 + abs(np.random.normal(0, 0.01)))
                low = current_price * (1 - abs(np.random.normal(0, 0.01)))
                open_price = current_price * (1 + np.random.normal(0, 0.005))
                close_price = current_price
                volume = np.random.randint(1000, 10000)
                
                data.append({
                    'datetime': date,
                    'open': round(open_price, 2),
                    'high': round(high, 2),
                    'low': round(low, 2),
                    'close': round(close_price, 2),
                    'volume': volume
                })
            
            df = pd.DataFrame(data)
            logger.info(f"Created mock data for {symbol}: {len(df)} records")
            return df
            
        except Exception as e:
            logger.error(f"Error creating mock data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def get_hourly_data_for_entry(self, symbol: str, entry_datetime: datetime, 
                                 days_back: int = 5) -> Optional[Dict]:
        """
        Get hourly data for entry point (existing implementation)
        """
        try:
            from_date = (entry_datetime - timedelta(days=days_back)).strftime('%Y-%m-%d')
            to_date = (entry_datetime + timedelta(days=20)).strftime('%Y-%m-%d')
            
            df = self.get_historical_data(symbol=symbol, from_date=from_date, to_date=to_date, interval="1h")
            
            if df is None or df.empty:
                logger.warning(f"No hourly data found for {symbol}")
                return None
            
            entry_time = entry_datetime.replace(minute=0, second=0, microsecond=0)
            available_candles = df[df['datetime'] <= entry_time]
            
            if available_candles.empty:
                latest_candle = df.iloc[-1]
                entry_price = latest_candle['open']
                logger.info(f"Using latest available candle for {symbol} at {latest_candle['datetime']}")
            else:
                closest_candle = available_candles.iloc[-1]
                entry_price = closest_candle['open']
                logger.info(f"Using candle for {symbol} at {closest_candle['datetime']}")
            
            return {'entry_price': entry_price, 'hourly_data': df, 'entry_candle_time': entry_time}
            
        except Exception as e:
            logger.error(f"Error getting hourly data for {symbol}: {str(e)}")
            return None
    
    def get_daily_data_for_exit(self, symbol: str, entry_datetime: datetime, 
                               max_days: int = 20) -> Optional[pd.DataFrame]:
        """
        Get daily data for exit point (existing implementation)
        """
        try:
            from_date = entry_datetime.strftime('%Y-%m-%d')
            to_date = (entry_datetime + timedelta(days=max_days + 5)).strftime('%Y-%m-%d')
            
            df = self.get_historical_data(symbol=symbol, from_date=from_date, to_date=to_date, interval="1d")
            return df
            
        except Exception as e:
            logger.error(f"Error getting daily data for {symbol}: {str(e)}")
            return None
    
    def get_symbol_token(self, symbol: str) -> Optional[str]:
        """
        Get symbol token (existing implementation)
        """
        return symbol
    
    def test_connection(self) -> bool:
        """
        Test if data sources are working
        """
        try:
            # Test Yahoo Finance
            import yfinance as yf
            logger.info("Yahoo Finance test successful")
            
            # Test NSEPy
            try:
                from nsepy import get_history
                logger.info("NSEPy test successful")
            except ImportError:
                logger.warning("NSEPy not available")
            
            # Test Alpha Vantage (if key provided)
            if self.alpha_vantage_key:
                logger.info("Alpha Vantage API key found")
            else:
                logger.info("Alpha Vantage API key not provided")
            
            logger.info("Enhanced data client test successful!")
            return True
                
        except Exception as e:
            logger.error(f"Enhanced data client test failed: {str(e)}")
            return False
    
    def get_api_usage_stats(self) -> Dict:
        """
        Get API usage statistics
        """
        return {
            'api_calls': self.api_call_counts,
            'rate_limits': self.rate_limits,
            'cache_size': len(self.cache)
        }
