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

load_dotenv()

class SmartAPIClient:
    """
    Angel One SmartAPI client for fetching historical data using official library approach
    """
    
    def __init__(self):
        self.base_url = "https://apiconnect.angelbroking.com"
        self.session = requests.Session()
        self.access_token = None
        self.refresh_token = None
        self.feed_token = None
        self.jwt_token = None
        
        # API credentials - these should be set as environment variables
        self.api_key = os.getenv('ANGEL_API_KEY')
        self.client_code = os.getenv('ANGEL_CLIENT_CODE')
        self.pin = os.getenv('ANGEL_PIN')
        self.totp_secret = os.getenv('ANGEL_TOTP_SECRET')
        
        if not all([self.api_key, self.client_code, self.pin]):
            logger.warning("SmartAPI credentials not found in environment variables")
    
    def login(self) -> bool:
        """
        Authenticate with SmartAPI using multiple approaches for better compatibility
        """
        try:
            if not all([self.api_key, self.client_code, self.pin]):
                logger.error("Missing required credentials for SmartAPI login")
                return False
            
            # Generate TOTP if secret is provided
            totp = ""
            if self.totp_secret:
                try:
                    totp = pyotp.TOTP(self.totp_secret).now()
                    logger.info(f"TOTP generated successfully: {totp}")
                except Exception as e:
                    logger.error(f"TOTP generation failed: {str(e)}")
                    # Continue without TOTP if generation fails
                    totp = ""
            
            # Try multiple authentication approaches
            auth_methods = [
                self._try_login_method_1,  # Original method
                self._try_login_method_2,  # Alternative method
                self._try_login_method_3   # Fallback method
            ]
            
            for i, method in enumerate(auth_methods, 1):
                logger.info(f"Trying authentication method {i}")
                if method(totp):
                    logger.info(f"Authentication successful with method {i}")
                    return True
                logger.warning(f"Authentication method {i} failed, trying next...")
            
            logger.error("All authentication methods failed")
            return False
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False
    
    def _try_login_method_1(self, totp: str) -> bool:
        """Original SmartAPI authentication method"""
        try:
            login_url = f"{self.base_url}/rest/auth/angelbroking/user/v1/loginByPassword"
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-UserType': 'USER',
                'X-SourceID': 'WEB',
                'X-ClientLocalIP': '192.168.1.1',
                'X-ClientPublicIP': '192.168.1.1',
                'X-MACAddress': '00:00:00:00:00:00',
                'X-PrivateKey': self.api_key
            }
            
            payload = {
                "clientcode": self.client_code,
                "password": self.pin,
                "totp": totp
            }
            
            logger.info(f"Method 1 - Attempting login for client: {self.client_code}")
            response = self.session.post(login_url, headers=headers, json=payload)
            
            logger.info(f"Method 1 - Response status: {response.status_code}")
            logger.info(f"Method 1 - Response text: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') and data.get('data'):
                    self._store_auth_tokens(data['data'])
                    return True
                else:
                    logger.error(f"Method 1 - Login failed: {data.get('message', 'Unknown error')}")
                    return False
            else:
                logger.error(f"Method 1 - Request failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Method 1 - Error: {str(e)}")
            return False
    
    def _try_login_method_2(self, totp: str) -> bool:
        """Alternative authentication method with different headers"""
        try:
            login_url = f"{self.base_url}/rest/auth/angelbroking/user/v1/loginByPassword"
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-UserType': 'USER',
                'X-SourceID': 'WEB',
                'X-ClientLocalIP': '127.0.0.1',
                'X-ClientPublicIP': '127.0.0.1',
                'X-MACAddress': '00:00:00:00:00:00',
                'X-PrivateKey': self.api_key
            }
            
            payload = {
                "clientcode": self.client_code,
                "password": self.pin,
                "totp": totp
            }
            
            logger.info(f"Method 2 - Attempting login for client: {self.client_code}")
            response = self.session.post(login_url, headers=headers, json=payload)
            
            logger.info(f"Method 2 - Response status: {response.status_code}")
            logger.info(f"Method 2 - Response text: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') and data.get('data'):
                    self._store_auth_tokens(data['data'])
                    return True
                else:
                    logger.error(f"Method 2 - Login failed: {data.get('message', 'Unknown error')}")
                    return False
            else:
                logger.error(f"Method 2 - Request failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Method 2 - Error: {str(e)}")
            return False
    
    def _try_login_method_3(self, totp: str) -> bool:
        """Fallback method without TOTP"""
        try:
            login_url = f"{self.base_url}/rest/auth/angelbroking/user/v1/loginByPassword"
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-UserType': 'USER',
                'X-SourceID': 'WEB',
                'X-ClientLocalIP': '192.168.1.1',
                'X-ClientPublicIP': '192.168.1.1',
                'X-MACAddress': '00:00:00:00:00:00',
                'X-PrivateKey': self.api_key
            }
            
            payload = {
                "clientcode": self.client_code,
                "password": self.pin,
                "totp": ""  # Try without TOTP
            }
            
            logger.info(f"Method 3 - Attempting login without TOTP for client: {self.client_code}")
            response = self.session.post(login_url, headers=headers, json=payload)
            
            logger.info(f"Method 3 - Response status: {response.status_code}")
            logger.info(f"Method 3 - Response text: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') and data.get('data'):
                    self._store_auth_tokens(data['data'])
                    return True
                else:
                    logger.error(f"Method 3 - Login failed: {data.get('message', 'Unknown error')}")
                    return False
            else:
                logger.error(f"Method 3 - Request failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Method 3 - Error: {str(e)}")
            return False
    
    def _store_auth_tokens(self, data: dict):
        """Store authentication tokens and update session headers"""
        self.access_token = data['jwtToken']
        self.refresh_token = data['refreshToken']
        self.feed_token = data['feedToken']
        self.jwt_token = data['jwtToken']
        
        # Update session headers for future requests
        self.session.headers.update({
            'Authorization': f'Bearer {self.jwt_token}',
            'X-UserType': 'USER',
            'X-SourceID': 'WEB',
            'X-ClientLocalIP': '192.168.1.1',
            'X-ClientPublicIP': '192.168.1.1',
            'X-MACAddress': '00:00:00:00:00:00',
            'X-PrivateKey': self.api_key
        })
        
        logger.info("Authentication tokens stored successfully")
    
    
    def get_historical_data(self, symbol: str, from_date: str, to_date: str, 
                          interval: str = "ONE_MINUTE") -> Optional[pd.DataFrame]:
        """
        Fetch historical OHLC data for a symbol using official SmartAPI approach
        
        Args:
            symbol: Stock symbol (e.g., "RELIANCE")
            interval: Time interval (ONE_MINUTE, FIVE_MINUTE, FIFTEEN_MINUTE, ONE_HOUR, ONE_DAY)
            from_date: Start date in YYYY-MM-DD format
            to_date: End date in YYYY-MM-DD format
        
        Returns:
            DataFrame with OHLC data or None if failed
        """
        try:
            if not self.access_token:
                if not self.login():
                    logger.error("Failed to authenticate")
                    return None
            
            # Get symbol token first
            symbol_token = self.get_symbol_token(symbol)
            if not symbol_token:
                logger.error(f"Could not get token for symbol: {symbol}")
                return None
            
            # Historical data endpoint using official approach
            url = f"{self.base_url}/rest/secure/angelbroking/historical/v1/getCandleData"
            
            # Format dates properly for the API
            from_date_formatted = f"{from_date} 09:00"
            to_date_formatted = f"{to_date} 15:30"
            
            payload = {
                "exchange": "NSE",
                "symboltoken": symbol_token,
                "interval": interval,
                "fromdate": from_date_formatted,
                "todate": to_date_formatted
            }
            
            logger.info(f"Fetching historical data for {symbol} with token {symbol_token}")
            response = self.session.post(url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Historical data response: {data}")
                
                if data.get('status') and data.get('data'):
                    candles = data['data']
                    if candles:
                        df = pd.DataFrame(candles)
                        # Convert timestamp to datetime
                        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
                        df = df.sort_values('datetime')
                        return df
                    else:
                        logger.warning(f"No data found for {symbol}")
                        return None
                else:
                    logger.error(f"API error: {data.get('message', 'Unknown error')}")
                    return None
            else:
                logger.error(f"Historical data request failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return None
    
    def get_symbol_token(self, symbol: str) -> Optional[str]:
        """
        Get token for a symbol using official SmartAPI approach
        """
        try:
            if not self.access_token:
                if not self.login():
                    return None
            
            # Search symbol endpoint
            url = f"{self.base_url}/rest/secure/angelbroking/market/v1/search"
            
            payload = {
                "searchtext": symbol
            }
            
            logger.info(f"Searching for symbol: {symbol}")
            response = self.session.post(url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Symbol search response: {data}")
                
                if data.get('status') and data.get('data'):
                    for item in data['data']:
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
                    logger.error(f"Symbol search failed: {data.get('message', 'Unknown error')}")
                    return None
            else:
                logger.error(f"Symbol search request failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
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
