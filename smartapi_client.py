import requests
import json
import time
import logging
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Optional, Tuple
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class SmartAPIClient:
    """
    Angel One SmartAPI client for fetching historical data
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
        Authenticate with SmartAPI using MPIN
        """
        try:
            if not all([self.api_key, self.client_code, self.pin]):
                logger.error("Missing required credentials for SmartAPI login")
                return False
            
            # Login endpoint
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
                "totp": self._generate_totp() if self.totp_secret else ""
            }
            
            response = self.session.post(login_url, headers=headers, json=payload)
            
            logger.info(f"Login response status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    logger.info(f"Login response data: {data}")
                    
                    if data.get('status') and data.get('data'):
                        self.access_token = data['data']['jwtToken']
                        self.refresh_token = data['data']['refreshToken']
                        self.feed_token = data['data']['feedToken']
                        self.jwt_token = data['data']['jwtToken']
                        
                        # Update session headers
                        self.session.headers.update({
                            'Authorization': f'Bearer {self.jwt_token}',
                            'X-UserType': 'USER',
                            'X-SourceID': 'WEB',
                            'X-ClientLocalIP': '192.168.1.1',
                            'X-ClientPublicIP': '192.168.1.1',
                            'X-MACAddress': '00:00:00:00:00:00',
                            'X-PrivateKey': self.api_key
                        })
                        
                        logger.info("Successfully authenticated with SmartAPI")
                        return True
                    else:
                        error_msg = data.get('message', 'Unknown error')
                        logger.error(f"Login failed: {error_msg}")
                        logger.error(f"Full response: {data}")
                        return False
                except Exception as json_error:
                    logger.error(f"Error parsing login response: {str(json_error)}")
                    logger.error(f"Response text: {response.text}")
                    return False
            else:
                logger.error(f"Login request failed with status: {response.status_code}")
                logger.error(f"Response text: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False
    
    def _generate_totp(self) -> str:
        """
        Generate TOTP for 2FA authentication
        """
        try:
            import pyotp
            totp = pyotp.TOTP(self.totp_secret)
            return totp.now()
        except Exception as e:
            logger.error(f"TOTP generation error: {str(e)}")
            return ""
    
    def get_historical_data(self, symbol: str, from_date: str, to_date: str, 
                          interval: str = "ONE_MINUTE") -> Optional[pd.DataFrame]:
        """
        Fetch historical OHLC data for a symbol
        
        Args:
            symbol: Stock symbol (e.g., "NSE:RELIANCE-EQ")
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
            
            # Historical data endpoint
            url = f"{self.base_url}/rest/secure/angelbroking/historical/v1/getCandleData"
            
            payload = {
                "mode": "FULL",
                "exchangeTokens": {
                    "NSE": [symbol.split(':')[1] if ':' in symbol else symbol]
                },
                "interval": interval,
                "fromDate": from_date,
                "toDate": to_date
            }
            
            response = self.session.post(url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') and data.get('data'):
                    candles = data['data']['fetched']
                    if candles:
                        df = pd.DataFrame(candles)
                        df['datetime'] = pd.to_datetime(df['datetime'])
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
                return None
                
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return None
    
    def get_symbol_token(self, symbol: str) -> Optional[str]:
        """
        Get token for a symbol (required for historical data)
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
            
            response = self.session.post(url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') and data.get('data'):
                    for item in data['data']:
                        if item.get('symbol') == symbol:
                            return item.get('token')
                return None
            else:
                logger.error(f"Symbol search failed: {response.status_code}")
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
