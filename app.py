from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.utils
import json
import os
from datetime import datetime, timedelta
import requests
import time
from io import BytesIO
import base64
from backtest_engine import BacktestEngine
from enhanced_data_client import EnhancedDataClient
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.secret_key = 'your-secret-key-here'

# Global variables to store data
uploaded_data = None
backtest_results = None

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    global uploaded_data
    
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'Please upload a CSV file'}), 400
        
        # Read CSV file
        df = pd.read_csv(file)
        
        # Validate required columns - check for your CSV format
        if 'date' in df.columns and 'symbol' in df.columns:
            # Your CSV format: date, symbol, marketcapname, sector
            df['entry_datetime'] = pd.to_datetime(df['date'], format='%d-%m-%Y %I:%M %p')
            df['stock_name'] = df['symbol']
        elif 'stock_name' in df.columns and 'entry_date' in df.columns and 'entry_time' in df.columns:
            # Original format: stock_name, entry_date, entry_time
            df['entry_date'] = pd.to_datetime(df['entry_date'])
            df['entry_datetime'] = pd.to_datetime(df['entry_date'].astype(str) + ' ' + df['entry_time'].astype(str))
        else:
            return jsonify({
                'error': 'CSV must have either: (date, symbol) OR (stock_name, entry_date, entry_time)',
                'available_columns': list(df.columns),
                'expected_formats': [
                    'Format 1: date, symbol, marketcapname, sector',
                    'Format 2: stock_name, entry_date, entry_time'
                ]
            }), 400
        
        uploaded_data = df
        logger.info(f"Uploaded {len(df)} trades")
        
        return jsonify({
            'success': True,
            'message': f'Successfully uploaded {len(df)} trades',
            'preview': df.head().to_dict('records')
        })
    
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/run_backtest', methods=['POST'])
def run_backtest():
    global uploaded_data, backtest_results
    
    try:
        if uploaded_data is None:
            return jsonify({'error': 'No data uploaded. Please upload a CSV file first.'}), 400
        
        # Get parameters from request
        data = request.get_json()
        holding_days = int(data.get('holding_days', 10))
        
        # Use the new data client (no credentials required!)
        data_client = EnhancedDataClient()
        
        # Initialize backtest engine with data client
        engine = BacktestEngine(data_client)
        
        # Run backtest
        logger.info("Starting simple backtest...")
        results = engine.run_backtest(
            trades_df=uploaded_data,
            holding_days=holding_days
        )
        
        backtest_results = results
        
        # Calculate performance metrics
        metrics = engine.calculate_performance_metrics(results)
        
        return jsonify({
            'success': True,
            'metrics': metrics,
            'total_trades': len(results)
        })
    
    except Exception as e:
        logger.error(f"Backtest error: {str(e)}")
        return jsonify({'error': f'Error running backtest: {str(e)}'}), 500

@app.route('/export_results', methods=['GET'])
def export_results():
    global backtest_results
    
    try:
        if backtest_results is None:
            return jsonify({'error': 'No backtest results available'}), 400
        
        # Create CSV file with results
        output = BytesIO()
        csv_data = backtest_results.to_csv(index=False)
        output.write(csv_data.encode('utf-8'))
        output.seek(0)
        
        return send_file(
            output,
            as_attachment=True,
            download_name=f'backtest_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            mimetype='text/csv'
        )
    
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        return jsonify({'error': f'Error exporting results: {str(e)}'}), 500

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/credentials_status')
def credentials_status():
    # No credentials needed with the new data client!
    return jsonify({
        'has_credentials': True,
        'data_source': 'yfinance (Yahoo Finance)',
        'message': 'No API credentials required!'
    })


@app.route('/test_data_source')
def test_data_source():
    """Test if data source is working"""
           try:
               data_client = EnhancedDataClient()
               success = data_client.test_connection()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Data source is working!',
                'data_source': 'yfinance (Yahoo Finance)',
                'features': [
                    'No API keys required',
                    'Supports NSE/BSE Indian stocks',
                    'Historical data available',
                    'Multiple timeframes supported'
                ]
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Data source test failed'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Data source test failed: {str(e)}'
        }), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
