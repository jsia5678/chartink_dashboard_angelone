import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from kiteconnect import KiteConnect
import os

logger = logging.getLogger(__name__)

class KiteDataClient:
    """
    Zerodha Kite Connect data client for historical data
    Based on: https://kite.trade/docs/connect/v3/historical/
    """
    
    def __init__(self):
        self.kite = None
        self.instruments_cache = None
        self.is_authenticated = False
        self.api_key = None
        self.api_secret = None
        
    def authenticate(self, api_key: str, api_secret: str, access_token: str) -> bool:
        """
        Authenticate with Kite Connect API
        
        Args:
            api_key: Your Kite Connect API key
            api_secret: Your Kite Connect API secret
            access_token: Your access token from login flow
            
        Returns:
            bool: True if authentication successful
        """
        try:
            self.api_key = api_key
            self.api_secret = api_secret
            self.kite = KiteConnect(api_key=api_key)
            self.kite.set_access_token(access_token)
            
            # Test authentication by fetching profile
            profile = self.kite.profile()
            logger.info(f"Successfully authenticated as: {profile.get('user_name', 'Unknown')}")
            
            self.is_authenticated = True
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            self.is_authenticated = False
            return False
    
    def get_instruments(self) -> pd.DataFrame:
        """
        Get all instruments from Kite Connect
        Based on: https://kite.trade/docs/connect/v3/market-quotes/
        """
        try:
            if not self.is_authenticated:
                raise Exception("Not authenticated. Please authenticate first.")
            
            if self.instruments_cache is None:
                logger.info("Fetching instruments from Kite Connect...")
                instruments = self.kite.instruments()
                self.instruments_cache = pd.DataFrame(instruments)
                logger.info(f"Fetched {len(self.instruments_cache)} instruments")
            
            return self.instruments_cache
            
        except Exception as e:
            logger.error(f"Error fetching instruments: {str(e)}")
            return pd.DataFrame()
    
    def get_instrument_token(self, symbol: str, exchange: str = "NSE") -> Optional[int]:
        """
        Get instrument token for a symbol
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE', 'TCS')
            exchange: Exchange (NSE, BSE, etc.)
            
        Returns:
            int: Instrument token or None if not found
        """
        try:
            instruments_df = self.get_instruments()
            
            if instruments_df.empty:
                return None
            
            # Search for the symbol
            mask = (instruments_df['tradingsymbol'] == symbol) & (instruments_df['exchange'] == exchange)
            matching_instruments = instruments_df[mask]
            
            if not matching_instruments.empty:
                token = matching_instruments.iloc[0]['instrument_token']
                logger.info(f"Found instrument token for {symbol}: {token}")
                return token
            
            # Try with different variations
            variations = [
                f"{symbol}-EQ",
                f"{symbol}-BE", 
                f"{symbol}-SM",
                symbol
            ]
            
            for variation in variations:
                mask = (instruments_df['tradingsymbol'] == variation) & (instruments_df['exchange'] == exchange)
                matching_instruments = instruments_df[mask]
                
                if not matching_instruments.empty:
                    token = matching_instruments.iloc[0]['instrument_token']
                    logger.info(f"Found instrument token for {variation}: {token}")
                    return token
            
            logger.warning(f"Instrument token not found for {symbol} on {exchange}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting instrument token for {symbol}: {str(e)}")
            return None
    
    def get_historical_data(self, symbol: str, from_date: str, to_date: str, 
                          interval: str = "day", exchange: str = "NSE") -> Optional[pd.DataFrame]:
        """
        Get historical data from Kite Connect
        Based on: https://kite.trade/docs/connect/v3/historical/
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE')
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            interval: Data interval (minute, 3minute, 5minute, 15minute, 30minute, 60minute, day)
            exchange: Exchange (NSE, BSE, etc.)
            
        Returns:
            pd.DataFrame: Historical OHLC data
        """
        try:
            if not self.is_authenticated:
                raise Exception("Not authenticated. Please authenticate first.")
            
            # Get instrument token
            instrument_token = self.get_instrument_token(symbol, exchange)
            if instrument_token is None:
                logger.warning(f"Cannot find instrument token for {symbol}")
                return None
            
            # Convert date strings to datetime
            from_dt = pd.to_datetime(from_date)
            to_dt = pd.to_datetime(to_date)
            
            logger.info(f"Fetching historical data for {symbol} from {from_date} to {to_date}")
            
            # Fetch historical data
            historical_data = self.kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_dt,
                to_date=to_dt,
                interval=interval
            )
            
            if not historical_data:
                logger.warning(f"No historical data found for {symbol}")
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(historical_data)
            
            # Standardize column names
            df.columns = df.columns.str.lower()
            
            # Ensure datetime column exists
            if 'date' in df.columns:
                df['datetime'] = pd.to_datetime(df['date'])
            elif 'datetime' not in df.columns:
                df['datetime'] = df.index
            
            # Sort by datetime
            df = df.sort_values('datetime')
            
            # Select required columns
            required_columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
            available_columns = [col for col in required_columns if col in df.columns]
            df = df[available_columns]
            
            logger.info(f"Successfully fetched {len(df)} records for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return None
    
    def get_entry_price(self, symbol: str, entry_datetime: datetime, 
                       exchange: str = "NSE") -> Optional[float]:
        """
        Get entry price for a specific datetime
        
        Args:
            symbol: Stock symbol
            entry_datetime: Entry date and time
            exchange: Exchange
            
        Returns:
            float: Entry price or None if not found
        """
        try:
            # Get data for the entry date
            from_date = entry_datetime.strftime('%Y-%m-%d')
            to_date = (entry_datetime + timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Try minute data first for precise entry
            df = self.get_historical_data(symbol, from_date, to_date, "minute", exchange)
            
            if df is not None and not df.empty:
                # Find closest candle to entry time
                df['time_diff'] = abs(df['datetime'] - entry_datetime)
                closest_candle = df.loc[df['time_diff'].idxmin()]
                return closest_candle['open']
            
            # Fallback to daily data
            df = self.get_historical_data(symbol, from_date, to_date, "day", exchange)
            
            if df is not None and not df.empty:
                return df.iloc[0]['open']
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting entry price for {symbol}: {str(e)}")
            return None
    
    def get_exit_price(self, symbol: str, entry_datetime: datetime, 
                      holding_days: int, exchange: str = "NSE") -> Optional[float]:
        """
        Get exit price after holding for specified days
        
        Args:
            symbol: Stock symbol
            entry_datetime: Entry date and time
            holding_days: Number of days to hold
            exchange: Exchange
            
        Returns:
            float: Exit price or None if not found
        """
        try:
            # Calculate exit date
            exit_date = entry_datetime + timedelta(days=holding_days)
            
            # Get data for the exit date
            from_date = exit_date.strftime('%Y-%m-%d')
            to_date = (exit_date + timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Try minute data first for precise exit
            df = self.get_historical_data(symbol, from_date, to_date, "minute", exchange)
            
            if df is not None and not df.empty:
                # Find closest candle to exit time
                df['time_diff'] = abs(df['datetime'] - exit_date)
                closest_candle = df.loc[df['time_diff'].idxmin()]
                return closest_candle['open']
            
            # Fallback to daily data
            df = self.get_historical_data(symbol, from_date, to_date, "day", exchange)
            
            if df is not None and not df.empty:
                return df.iloc[0]['open']
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting exit price for {symbol}: {str(e)}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test if Kite Connect is working
        """
        try:
            if not self.is_authenticated:
                logger.warning("Not authenticated with Kite Connect")
                return False
            
            # Test by fetching profile
            profile = self.kite.profile()
            logger.info(f"Kite Connect test successful. User: {profile.get('user_name', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Kite Connect test failed: {str(e)}")
            return False
