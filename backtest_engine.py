import pandas as pd
import numpy as np
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enhanced_data_client import EnhancedDataClient

logger = logging.getLogger(__name__)

class BacktestEngine:
    """
    Simple backtesting engine for Chartink signals - just hold for N days and show returns
    """
    
    def __init__(self, data_client: EnhancedDataClient):
        self.data_client = data_client
        self.results = []
    
    def run_backtest(self, trades_df: pd.DataFrame, holding_days: int = 10) -> pd.DataFrame:
        """
        Run simple backtest - hold each position for N days and show returns
        
        Args:
            trades_df: DataFrame with columns ['stock_name', 'entry_date', 'entry_time']
            holding_days: Number of days to hold each position (default: 10)
        
        Returns:
            DataFrame with backtest results showing returns after N days
        """
        logger.info(f"Starting simple backtest with {len(trades_df)} trades")
        logger.info(f"Parameters: Holding Days={holding_days}")
        
        results = []
        successful_trades = 0
        failed_trades = 0
        
        for idx, trade in trades_df.iterrows():
            try:
                logger.info(f"Processing trade {idx + 1}/{len(trades_df)}: {trade['stock_name']}")
                
                symbol = trade['stock_name']
                entry_time = trade['entry_datetime']
                
                # Get daily data for the holding period
                from_date = entry_time.strftime('%Y-%m-%d')
                to_date = (entry_time + timedelta(days=holding_days + 5)).strftime('%Y-%m-%d')
                
                daily_data = self.data_client.get_historical_data(
                    symbol=symbol,
                    from_date=from_date,
                    to_date=to_date,
                    interval="1d"
                )
                
                if daily_data is None or daily_data.empty:
                    logger.warning(f"No data found for {symbol}")
                    failed_trades += 1
                    continue
                
                # Find entry price (closest available price to entry time)
                entry_date = entry_time.date()
                entry_candles = daily_data[daily_data['datetime'].dt.date <= entry_date]
                
                if entry_candles.empty:
                    # Use first available candle
                    entry_price = daily_data.iloc[0]['open']
                    actual_entry_date = daily_data.iloc[0]['datetime'].date()
                else:
                    # Use closest candle to entry date
                    entry_price = entry_candles.iloc[-1]['close']
                    actual_entry_date = entry_candles.iloc[-1]['datetime'].date()
                
                # Find exit price (after holding_days)
                exit_date = actual_entry_date + timedelta(days=holding_days)
                exit_candles = daily_data[daily_data['datetime'].dt.date >= exit_date]
                
                if exit_candles.empty:
                    # Use last available candle
                    exit_price = daily_data.iloc[-1]['close']
                    actual_exit_date = daily_data.iloc[-1]['datetime'].date()
                else:
                    # Use first candle on or after exit date
                    exit_price = exit_candles.iloc[0]['open']
                    actual_exit_date = exit_candles.iloc[0]['datetime'].date()
                
                # Calculate returns
                pnl = exit_price - entry_price
                pnl_pct = (pnl / entry_price) * 100
                actual_days_held = (actual_exit_date - actual_entry_date).days
                
                result = {
                    'stock_name': symbol,
                    'entry_date': actual_entry_date.strftime('%Y-%m-%d'),
                    'entry_price': round(entry_price, 2),
                    'exit_date': actual_exit_date.strftime('%Y-%m-%d'),
                    'exit_price': round(exit_price, 2),
                    'days_held': actual_days_held,
                    'pnl': round(pnl, 2),
                    'pnl_pct': round(pnl_pct, 2)
                }
                
                results.append(result)
                successful_trades += 1
                
                logger.info(f"Trade completed: {symbol} - {pnl_pct:.2f}% in {actual_days_held} days")
                
            except Exception as e:
                logger.error(f"Error processing trade {idx + 1}: {str(e)}")
                failed_trades += 1
                continue
        
        logger.info(f"Backtest completed: {successful_trades} successful, {failed_trades} failed")
        
        if not results:
            logger.warning("No successful trades to analyze")
            return pd.DataFrame()
        
        results_df = pd.DataFrame(results)
        self.results = results_df
        
        return results_df
    
    def calculate_performance_metrics(self, results_df: pd.DataFrame) -> Dict:
        """
        Calculate simple performance metrics
        """
        if results_df.empty:
            return {}
        
        total_trades = len(results_df)
        winning_trades = len(results_df[results_df['pnl_pct'] > 0])
        losing_trades = len(results_df[results_df['pnl_pct'] < 0])
        
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        avg_return = results_df['pnl_pct'].mean()
        total_return = results_df['pnl_pct'].sum()
        
        best_trade = results_df['pnl_pct'].max()
        worst_trade = results_df['pnl_pct'].min()
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(win_rate, 2),
            'avg_return': round(avg_return, 2),
            'total_return': round(total_return, 2),
            'best_trade': round(best_trade, 2),
            'worst_trade': round(worst_trade, 2)
        }