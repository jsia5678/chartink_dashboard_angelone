import requests
import json
import time
import logging
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Optional, Tuple
import os
from dotenv import load_dotenv
import pyotp
from logzero import logger

# Import the official SmartAPI library
from SmartApi import SmartConnect

load_dotenv()

class SmartAPIClient:
    """
    Angel One SmartAPI client using the official SmartAPI Python library
    """
    
    def __init__(self):
        # API credentials - these should be set as environment variables
        self.api_key = os.getenv('ANGEL_API_KEY')
        self.client_code = os.getenv('ANGEL_CLIENT_CODE')
        self.pin = os.getenv('ANGEL_PIN')
        self.totp_secret = os.getenv('ANGEL_TOTP_SECRET')
        
        # Initialize the official SmartAPI client
        self.smart_api = None
        self.auth_token = None
        self.refresh_token = None
        self.feed_token = None
        
        if not all([self.api_key, self.client_code, self.pin]):
            logger.warning("SmartAPI credentials not found in environment variables")
    
    def login(self) -> bool:
        """
        Authenticate with SmartAPI using the official SmartAPI Python library
        """
        try:
            if not all([self.api_key, self.client_code, self.pin]):
                logger.error("Missing required credentials for SmartAPI login")
                return False
            
            # Initialize the official SmartAPI client
            self.smart_api = SmartConnect(self.api_key)
            
            # Generate TOTP if secret is provided
            totp = ""
            if self.totp_secret:
                try:
                    totp = pyotp.TOTP(self.totp_secret).now()
                    logger.info(f"TOTP generated successfully: {totp}")
                except Exception as e:
                    logger.error(f"TOTP generation failed: {str(e)}")
                    return False
            
            # Use the official library's generateSession method
            logger.info(f"Attempting login for client: {self.client_code}")
            data = self.smart_api.generateSession(self.client_code, self.pin, totp)
            
            logger.info(f"Login response: {data}")
            
            if data['status'] == False:
                logger.error(f"Login failed: {data}")
                return False
            else:
                # Store authentication tokens
                self.auth_token = data['data']['jwtToken']
                self.refresh_token = data['data']['refreshToken']
                self.feed_token = self.smart_api.getfeedToken()
                
                logger.info("Successfully authenticated with SmartAPI using official library")
                return True
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False
    
    
    
    def get_historical_data(self, symbol: str, from_date: str, to_date: str, 
                          interval: str = "ONE_MINUTE") -> Optional[pd.DataFrame]:
        """
        Fetch historical OHLC data for a symbol using the official SmartAPI library
        
        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            interval: Time interval (ONE_MINUTE, FIVE_MINUTE, FIFTEEN_MINUTE, ONE_HOUR, ONE_DAY)
            from_date: Start date in YYYY-MM-DD format
            to_date: End date in YYYY-MM-DD format
        
        Returns:
            DataFrame with OHLC data or None if failed
        """
        try:
            if not self.smart_api:
                if not self.login():
                    logger.error("Failed to authenticate")
                    return None
            
            # Get symbol token first
            symbol_token = self.get_symbol_token(symbol)
            if not symbol_token:
                logger.error(f"Could not get token for symbol: {symbol}")
                return None
            
            # Use the official library's getCandleData method
            historic_param = {
                "exchange": "NSE",
                "symboltoken": symbol_token,
                "interval": interval,
                "fromdate": f"{from_date} 09:00",
                "todate": f"{to_date} 15:30"
            }
            
            logger.info(f"Fetching historical data for {symbol} with token {symbol_token}")
            data = self.smart_api.getCandleData(historic_param)
            
            logger.info(f"Historical data response: {data}")
            
            if data and isinstance(data, list) and len(data) > 0:
                df = pd.DataFrame(data)
                # Convert timestamp to datetime
                df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
                df = df.sort_values('datetime')
                return df
            else:
                logger.warning(f"No data found for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return None
    
    def get_symbol_token(self, symbol: str) -> Optional[str]:
        """
        Get token for a symbol using the official SmartAPI library
        """
        try:
            if not self.smart_api:
                if not self.login():
                    return None
            
            # Use the official library's search method
            logger.info(f"Searching for symbol: {symbol}")
            data = self.smart_api.searchSymbol("NSE", symbol)
            
            logger.info(f"Symbol search response: {data}")
            
            if data and isinstance(data, list) and len(data) > 0:
                for item in data:
                    # Look for exact match or symbol with -EQ suffix
                    if (item.get('symbol') == symbol or 
                        item.get('symbol') == f"{symbol}-EQ" or
                        item.get('symbol') == f"{symbol}-BE"):
                        token = item.get('token')
                        logger.info(f"Found token {token} for symbol {symbol}")
                        return token
                
                logger.warning(f"No token found for symbol: {symbol}")
                return None
            else:
                logger.error(f"Symbol search failed: No data returned")
                return None
                
        except Exception as e:
            logger.error(f"Error searching symbol {symbol}: {str(e)}")
            return None
    
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
                interval="ONE_HOUR"
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
                interval="ONE_DAY"
            )
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting daily data for {symbol}: {str(e)}")
            return None
