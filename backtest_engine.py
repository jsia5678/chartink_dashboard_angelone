import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from data_provider import ProfessionalDataProvider

logger = logging.getLogger(__name__)

class BacktestEngine:
    """
    Professional backtesting engine using data provider (like algo companies)
    """
    
    def __init__(self, data_provider: ProfessionalDataProvider):
        self.data_provider = data_provider
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
        
        for idx, trade in trades_df.iterrows():
            try:
                logger.info(f"Processing trade {idx + 1}/{len(trades_df)}: {trade['stock_name']}")
                
                symbol = trade['stock_name']
                entry_datetime = trade['entry_datetime']
                
                         # Get entry price from professional data provider
                         entry_price = self.data_provider.get_entry_price(symbol, entry_datetime)
                         
                         if entry_price is None:
                             logger.warning(f"Could not get entry price for {symbol}")
                             continue
                         
                         # Get exit price after holding_days
                         exit_price = self.data_provider.get_exit_price(symbol, entry_datetime, holding_days)
                
                if exit_price is None:
                    logger.warning(f"Could not get exit price for {symbol}")
                    continue
                
                # Calculate returns
                pnl = exit_price - entry_price
                pnl_pct = (pnl / entry_price) * 100
                
                exit_date = entry_datetime + timedelta(days=holding_days)
                
                result = {
                    'stock_name': symbol,
                    'entry_date': entry_datetime.strftime('%Y-%m-%d'),
                    'entry_price': round(entry_price, 2),
                    'exit_date': exit_date.strftime('%Y-%m-%d'),
                    'exit_price': round(exit_price, 2),
                    'days_held': holding_days,
                    'pnl': round(pnl, 2),
                    'pnl_pct': round(pnl_pct, 2)
                }
                
                results.append(result)
                logger.info(f"Trade completed: {symbol} - {pnl_pct:.2f}% in {holding_days} days")
                
            except Exception as e:
                logger.error(f"Error processing trade {idx + 1}: {str(e)}")
                continue
        
        logger.info(f"Backtest completed: {len(results)} trades processed")
        
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