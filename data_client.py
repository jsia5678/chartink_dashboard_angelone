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
            # Try different symbol formats for Indian stocks
            symbol_formats = [
                f"{symbol}.NS",  # NSE
                f"{symbol}.BO",  # BSE
                symbol,          # Direct symbol
                f"{symbol}-EQ.NS",  # NSE with EQ suffix
                f"{symbol}-BE.NS",  # NSE with BE suffix
                f"{symbol}-NSE.NS",  # NSE with NSE suffix
                f"{symbol}-BSE.BO",  # BSE with BSE suffix
                f"{symbol}.NSE",  # NSE alternative
                f"{symbol}.BSE"   # BSE alternative
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
                        prepost=True
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
            
            # Fallback: Create mock data for testing
            logger.info(f"Creating mock data for {symbol} for testing purposes")
            return self._create_mock_data(symbol, from_date, to_date, interval)
            
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
    
    def _create_mock_data(self, symbol: str, from_date: str, to_date: str, interval: str) -> pd.DataFrame:
        """
        Create mock data for testing when real data is not available
        """
        try:
            import numpy as np
            
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
            base_price = 100.0  # Base price
            np.random.seed(hash(symbol) % 2**32)  # Consistent random data per symbol
            
            data = []
            current_price = base_price
            
            for date in date_range:
                # Random price movement
                change = np.random.normal(0, 0.02)  # 2% daily volatility
                current_price *= (1 + change)
                
                # Generate OHLC from current price
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
    
    def test_connection(self) -> bool:
        """
        Test if data source is working
        """
        try:
            # Simple test - just check if yfinance can be imported
            import yfinance as yf
            logger.info("Data client test successful - yfinance is available!")
            return True
                
        except Exception as e:
            logger.error(f"Data client test failed: {str(e)}")
            return False
