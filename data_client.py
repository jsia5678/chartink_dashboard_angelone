import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from logzero import logger
import time

class DataClient:
    """
    Universal data client using yfinance and TradingView data
    No API keys required!
    """
    
    def __init__(self):
        self.exchange_suffixes = {
            'NSE': '.NS',
            'BSE': '.BO',
            'NSE_FO': '.NFO',
            'BSE_FO': '.BF'
        }
    
    def get_historical_data(self, symbol: str, from_date: str, to_date: str, 
                          interval: str = "1h") -> Optional[pd.DataFrame]:
        """
        Fetch historical OHLC data using yfinance
        
        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            from_date: Start date in YYYY-MM-DD format
            to_date: End date in YYYY-MM-DD format
            interval: Time interval (1m, 5m, 15m, 30m, 1h, 1d)
        
        Returns:
            DataFrame with OHLC data or None if failed
        """
        try:
            # Try different symbol formats
            symbol_formats = [
                f"{symbol}.NS",  # NSE
                f"{symbol}.BO",  # BSE
                symbol,          # Direct symbol
                f"{symbol}-EQ.NS",  # NSE with EQ suffix
                f"{symbol}-BE.NS"   # NSE with BE suffix
            ]
            
            for symbol_format in symbol_formats:
                try:
                    logger.info(f"Trying symbol format: {symbol_format}")
                    
                    # Create ticker object
                    ticker = yf.Ticker(symbol_format)
                    
                    # Fetch historical data
                    df = ticker.history(
                        start=from_date,
                        end=to_date,
                        interval=interval,
                        auto_adjust=True,
                        prepost=True,
                        threads=True
                    )
                    
                    if not df.empty:
                        # Clean and format the data
                        df = df.reset_index()
                        df.columns = df.columns.str.lower()
                        
                        # Rename columns to match expected format
                        column_mapping = {
                            'datetime': 'datetime',
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
                        elif 'datetime' not in df.columns:
                            df['datetime'] = df.index
                        
                        # Convert to datetime if needed
                        if not pd.api.types.is_datetime64_any_dtype(df['datetime']):
                            df['datetime'] = pd.to_datetime(df['datetime'])
                        
                        # Sort by datetime
                        df = df.sort_values('datetime')
                        
                        logger.info(f"Successfully fetched {len(df)} records for {symbol_format}")
                        return df
                    
                except Exception as e:
                    logger.warning(f"Failed to fetch data for {symbol_format}: {str(e)}")
                    continue
            
            logger.error(f"Failed to fetch data for symbol: {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return None
    
    def get_symbol_token(self, symbol: str) -> Optional[str]:
        """
        Get symbol token (for compatibility with existing code)
        Returns the symbol itself since yfinance doesn't need tokens
        """
        return symbol
    
    def get_hourly_data_for_entry(self, symbol: str, entry_datetime: datetime, 
                                 days_back: int = 5) -> Optional[Dict]:
        """
        Get hourly data around entry time for backtesting
        
        Args:
            symbol: Stock symbol
            entry_datetime: Entry date and time
            days_back: Days to look back for data
        
        Returns:
            Dict with entry price and hourly candles or None
        """
        try:
            # Calculate date range
            from_date = (entry_datetime - timedelta(days=days_back)).strftime('%Y-%m-%d')
            to_date = (entry_datetime + timedelta(days=20)).strftime('%Y-%m-%d')
            
            # Get hourly data
            df = self.get_historical_data(
                symbol=symbol,
                from_date=from_date,
                to_date=to_date,
                interval="1h"
            )
            
            if df is None or df.empty:
                logger.warning(f"No hourly data found for {symbol}")
                return None
            
            # Find the closest hourly candle at or before entry time
            entry_time = entry_datetime.replace(minute=0, second=0, microsecond=0)
            
            # Filter candles at or before entry time
            available_candles = df[df['datetime'] <= entry_time]
            
            if available_candles.empty:
                # If no candle at entry time, use the latest available
                latest_candle = df.iloc[-1]
                entry_price = latest_candle['open']
                logger.info(f"Using latest available candle for {symbol} at {latest_candle['datetime']}")
            else:
                # Use the closest candle at or before entry time
                closest_candle = available_candles.iloc[-1]
                entry_price = closest_candle['open']
                logger.info(f"Using candle for {symbol} at {closest_candle['datetime']}")
            
            return {
                'entry_price': entry_price,
                'hourly_data': df,
                'entry_candle_time': entry_time
            }
            
        except Exception as e:
            logger.error(f"Error getting hourly data for {symbol}: {str(e)}")
            return None
    
    def get_daily_data_for_exit(self, symbol: str, entry_datetime: datetime, 
                               max_days: int = 20) -> Optional[pd.DataFrame]:
        """
        Get daily data for exit calculations
        
        Args:
            symbol: Stock symbol
            entry_datetime: Entry date and time
            max_days: Maximum holding period in days
        
        Returns:
            DataFrame with daily OHLC data or None
        """
        try:
            # Calculate date range
            from_date = entry_datetime.strftime('%Y-%m-%d')
            to_date = (entry_datetime + timedelta(days=max_days + 5)).strftime('%Y-%m-%d')
            
            # Get daily data
            df = self.get_historical_data(
                symbol=symbol,
                from_date=from_date,
                to_date=to_date,
                interval="1d"
            )
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting daily data for {symbol}: {str(e)}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test if data source is working
        """
        try:
            # Test with a common stock
            test_df = self.get_historical_data(
                symbol="RELIANCE",
                from_date="2024-01-01",
                to_date="2024-01-02",
                interval="1d"
            )
            
            if test_df is not None and not test_df.empty:
                logger.info("Data client test successful!")
                return True
            else:
                logger.error("Data client test failed - no data returned")
                return False
                
        except Exception as e:
            logger.error(f"Data client test failed: {str(e)}")
            return False
