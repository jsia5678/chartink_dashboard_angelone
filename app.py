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
from smartapi_client import SmartAPIClient
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

@app.route('/setup')
def setup():
    return render_template('setup.html')

@app.route('/save_credentials', methods=['POST'])
def save_credentials():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['api_key', 'client_code', 'pin']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        # Save credentials to environment (in production, use proper secret management)
        credentials = {
            'ANGEL_API_KEY': data['api_key'],
            'ANGEL_CLIENT_CODE': data['client_code'],
            'ANGEL_PIN': data['pin'],
            'ANGEL_TOTP_SECRET': data.get('totp_secret', '')
        }
        
        # Test the credentials
        from smartapi_client import SmartAPIClient
        api_client = SmartAPIClient()
        
        # Temporarily set credentials for testing
        api_client.api_key = data['api_key']
        api_client.client_code = data['client_code']
        api_client.pin = data['pin']
        api_client.totp_secret = data.get('totp_secret', '')
        
        # Test login
        if api_client.login():
            return jsonify({
                'success': True,
                'message': 'Credentials saved and tested successfully!'
            })
        else:
            return jsonify({
                'error': 'Invalid credentials. Please check your API key, client code, and PIN.'
            }), 400
            
    except Exception as e:
        logger.error(f"Credentials error: {str(e)}")
        return jsonify({'error': f'Error saving credentials: {str(e)}'}), 500

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
        stop_loss_pct = float(data.get('stop_loss_pct', 5))
        target_profit_pct = float(data.get('target_profit_pct', 10))
        max_holding_days = int(data.get('max_holding_days', 10))
        
        # Initialize SmartAPI client
        api_client = SmartAPIClient()
        
        # Initialize backtest engine
        engine = BacktestEngine(api_client)
        
        # Run backtest
        logger.info("Starting backtest...")
        results = engine.run_backtest(
            trades_df=uploaded_data,
            stop_loss_pct=stop_loss_pct,
            target_profit_pct=target_profit_pct,
            max_holding_days=max_holding_days
        )
        
        backtest_results = results
        
        # Calculate performance metrics
        metrics = engine.calculate_metrics(results)
        
        # Generate charts
        equity_curve = engine.generate_equity_curve(results)
        returns_distribution = engine.generate_returns_distribution(results)
        
        return jsonify({
            'success': True,
            'metrics': metrics,
            'equity_curve': equity_curve,
            'returns_distribution': returns_distribution,
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
