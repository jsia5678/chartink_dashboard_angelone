from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import logging
from backtest_engine import BacktestEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.secret_key = 'your-secret-key-here'

# Global variables
uploaded_data = None
backtest_results = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    global uploaded_data
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    try:
        # Read CSV file
        df = pd.read_csv(file)
        
        # Validate required columns
        required_columns = ['date', 'symbol', 'marketcapname', 'sector']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return jsonify({
                'error': f'Missing required columns: {", ".join(missing_columns)}'
            }), 400
        
        # Parse dates and create entry_datetime
        df['entry_date'] = pd.to_datetime(df['date'], format='%d-%m-%Y %I:%M %p', errors='coerce')
        df['entry_datetime'] = df['entry_date']
        df['stock_name'] = df['symbol']
        
        # Remove rows with invalid dates
        df = df.dropna(subset=['entry_date'])
        
        if df.empty:
            return jsonify({'error': 'No valid entries found in CSV'}), 400
        
        uploaded_data = df
        
        return jsonify({
            'success': True,
            'message': f'Successfully uploaded {len(df)} trades',
            'data': df.to_dict('records')[:5]  # Return first 5 rows as preview
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
        
        # Initialize backtest engine
        engine = BacktestEngine()
        
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
    
    if backtest_results is None:
        return jsonify({'error': 'No results to export'}), 400
    
    try:
        # Create CSV in memory
        output = BytesIO()
        backtest_results.to_csv(output, index=False)
        output.seek(0)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'backtest_results_{timestamp}.csv'
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
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