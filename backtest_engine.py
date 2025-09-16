import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.utils
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from data_client import DataClient

logger = logging.getLogger(__name__)

class BacktestEngine:
    """
    Backtesting engine for Chartink signals using Yahoo Finance data
    """
    
    def __init__(self, data_client: DataClient):
        self.data_client = data_client
        self.results = []
    
    def run_backtest(self, trades_df: pd.DataFrame, stop_loss_pct: float = 5.0, 
                    target_profit_pct: float = 10.0, max_holding_days: int = 10) -> pd.DataFrame:
        """
        Run backtest on the provided trades
        
        Args:
            trades_df: DataFrame with columns ['stock_name', 'entry_date', 'entry_time']
            stop_loss_pct: Stop loss percentage (e.g., 5.0 for 5%)
            target_profit_pct: Target profit percentage (e.g., 10.0 for 10%)
            max_holding_days: Maximum holding period in days
        
        Returns:
            DataFrame with backtest results
        """
        logger.info(f"Starting backtest with {len(trades_df)} trades")
        logger.info(f"Parameters: SL={stop_loss_pct}%, TP={target_profit_pct}%, Max Days={max_holding_days}")
        
        results = []
        successful_trades = 0
        failed_trades = 0
        
        for idx, trade in trades_df.iterrows():
            try:
                logger.info(f"Processing trade {idx + 1}/{len(trades_df)}: {trade['stock_name']}")
                
                # Use stock name directly for yfinance
                symbol = trade['stock_name']
                
                # Get entry data
                entry_data = self.data_client.get_hourly_data_for_entry(
                    symbol=symbol,
                    entry_datetime=trade['entry_datetime']
                )
                
                if entry_data is None:
                    logger.warning(f"No entry data found for {trade['stock_name']}")
                    failed_trades += 1
                    continue
                
                entry_price = entry_data['entry_price']
                
                # Get daily data for exit calculations
                daily_data = self.data_client.get_daily_data_for_exit(
                    symbol=symbol,
                    entry_datetime=trade['entry_datetime'],
                    max_days=max_holding_days
                )
                
                if daily_data is None or daily_data.empty:
                    logger.warning(f"No daily data found for {trade['stock_name']}")
                    failed_trades += 1
                    continue
                
                # Simulate trade
                trade_result = self._simulate_trade(
                    symbol=trade['stock_name'],
                    entry_price=entry_price,
                    entry_datetime=trade['entry_datetime'],
                    daily_data=daily_data,
                    stop_loss_pct=stop_loss_pct,
                    target_profit_pct=target_profit_pct,
                    max_holding_days=max_holding_days
                )
                
                if trade_result:
                    results.append(trade_result)
                    successful_trades += 1
                else:
                    failed_trades += 1
                
                # Add delay to avoid rate limiting
                time.sleep(0.2)
                
            except Exception as e:
                logger.error(f"Error processing trade {trade['stock_name']}: {str(e)}")
                failed_trades += 1
                continue
        
        logger.info(f"Backtest completed: {successful_trades} successful, {failed_trades} failed")
        
        if results:
            results_df = pd.DataFrame(results)
            return results_df
        else:
            return pd.DataFrame()
    
    def _simulate_trade(self, symbol: str, entry_price: float, entry_datetime: datetime,
                       daily_data: pd.DataFrame, stop_loss_pct: float, target_profit_pct: float,
                       max_holding_days: int) -> Optional[Dict]:
        """
        Simulate a single trade with SL/TP logic
        """
        try:
            # Calculate SL and TP levels
            stop_loss_price = entry_price * (1 - stop_loss_pct / 100)
            target_price = entry_price * (1 + target_profit_pct / 100)
            
            # Filter data from entry date onwards
            daily_data['datetime'] = pd.to_datetime(daily_data['datetime'])
            trade_data = daily_data[daily_data['datetime'] >= entry_datetime.date()].copy()
            
            if trade_data.empty:
                return None
            
            # Check each day for SL/TP hit
            for idx, row in trade_data.iterrows():
                current_date = row['datetime']
                days_held = (current_date - entry_datetime.date()).days
                
                # Check if max holding period reached
                if days_held >= max_holding_days:
                    exit_price = row['close']
                    exit_reason = f"Max holding period ({max_holding_days} days)"
                    break
                
                # Check for stop loss hit (using low of the day)
                if row['low'] <= stop_loss_price:
                    exit_price = stop_loss_price
                    exit_reason = f"Stop Loss ({stop_loss_pct}%)"
                    break
                
                # Check for target profit hit (using high of the day)
                if row['high'] >= target_price:
                    exit_price = target_price
                    exit_reason = f"Target Profit ({target_profit_pct}%)"
                    break
            else:
                # If no exit condition met, exit at last available price
                exit_price = trade_data.iloc[-1]['close']
                exit_reason = f"End of data ({days_held} days)"
            
            # Calculate returns
            pnl = exit_price - entry_price
            pnl_pct = (pnl / entry_price) * 100
            is_winner = pnl > 0
            
            return {
                'symbol': symbol,
                'entry_date': entry_datetime.strftime('%Y-%m-%d'),
                'entry_time': entry_datetime.strftime('%H:%M:%S'),
                'entry_price': entry_price,
                'exit_price': exit_price,
                'exit_reason': exit_reason,
                'days_held': days_held,
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'is_winner': is_winner,
                'stop_loss_price': stop_loss_price,
                'target_price': target_price
            }
            
        except Exception as e:
            logger.error(f"Error simulating trade for {symbol}: {str(e)}")
            return None
    
    def calculate_metrics(self, results_df: pd.DataFrame) -> Dict:
        """
        Calculate performance metrics from backtest results
        """
        if results_df.empty:
            return {}
        
        try:
            # Basic metrics
            total_trades = len(results_df)
            winning_trades = len(results_df[results_df['is_winner'] == True])
            losing_trades = total_trades - winning_trades
            
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
            
            # P&L metrics
            total_pnl = results_df['pnl'].sum()
            avg_pnl = results_df['pnl'].mean()
            avg_pnl_pct = results_df['pnl_pct'].mean()
            
            # Win/Loss metrics
            winning_pnl = results_df[results_df['is_winner'] == True]['pnl']
            losing_pnl = results_df[results_df['is_winner'] == False]['pnl']
            
            avg_win = winning_pnl.mean() if len(winning_pnl) > 0 else 0
            avg_loss = losing_pnl.mean() if len(losing_pnl) > 0 else 0
            
            # Risk-Reward ratio
            risk_reward_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0
            
            # Drawdown calculation
            cumulative_pnl = results_df['pnl'].cumsum()
            running_max = cumulative_pnl.expanding().max()
            drawdown = cumulative_pnl - running_max
            max_drawdown = drawdown.min()
            max_drawdown_pct = (max_drawdown / running_max.max()) * 100 if running_max.max() != 0 else 0
            
            # Additional metrics
            best_trade = results_df['pnl_pct'].max()
            worst_trade = results_df['pnl_pct'].min()
            avg_holding_days = results_df['days_held'].mean()
            
            # Exit reason analysis
            exit_reasons = results_df['exit_reason'].value_counts().to_dict()
            
            return {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': round(win_rate, 2),
                'total_pnl': round(total_pnl, 2),
                'avg_pnl': round(avg_pnl, 2),
                'avg_pnl_pct': round(avg_pnl_pct, 2),
                'avg_win': round(avg_win, 2),
                'avg_loss': round(avg_loss, 2),
                'risk_reward_ratio': round(risk_reward_ratio, 2),
                'max_drawdown': round(max_drawdown, 2),
                'max_drawdown_pct': round(max_drawdown_pct, 2),
                'best_trade': round(best_trade, 2),
                'worst_trade': round(worst_trade, 2),
                'avg_holding_days': round(avg_holding_days, 1),
                'exit_reasons': exit_reasons
            }
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            return {}
    
    def generate_equity_curve(self, results_df: pd.DataFrame) -> str:
        """
        Generate equity curve chart
        """
        try:
            if results_df.empty:
                return json.dumps({})
            
            # Calculate cumulative P&L
            results_df['cumulative_pnl'] = results_df['pnl'].cumsum()
            
            # Create equity curve chart
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=list(range(len(results_df))),
                y=results_df['cumulative_pnl'],
                mode='lines',
                name='Equity Curve',
                line=dict(color='blue', width=2)
            ))
            
            fig.update_layout(
                title='Equity Curve',
                xaxis_title='Trade Number',
                yaxis_title='Cumulative P&L',
                hovermode='x unified',
                showlegend=True
            )
            
            return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
            
        except Exception as e:
            logger.error(f"Error generating equity curve: {str(e)}")
            return json.dumps({})
    
    def generate_returns_distribution(self, results_df: pd.DataFrame) -> str:
        """
        Generate returns distribution chart
        """
        try:
            if results_df.empty:
                return json.dumps({})
            
            # Create histogram of returns
            fig = go.Figure()
            
            fig.add_trace(go.Histogram(
                x=results_df['pnl_pct'],
                nbinsx=20,
                name='Returns Distribution',
                marker_color='lightblue',
                opacity=0.7
            ))
            
            # Add vertical line at 0%
            fig.add_vline(x=0, line_dash="dash", line_color="red", 
                         annotation_text="Break-even")
            
            fig.update_layout(
                title='Returns Distribution',
                xaxis_title='Return (%)',
                yaxis_title='Frequency',
                showlegend=True
            )
            
            return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
            
        except Exception as e:
            logger.error(f"Error generating returns distribution: {str(e)}")
            return json.dumps({})
