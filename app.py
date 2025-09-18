from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import logging
from backtest_engine import BacktestEngine
from kite_client import KiteDataClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.secret_key = 'your-secret-key-here'

# Global variables
uploaded_data = None
backtest_results = None
kite_client = None

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
        
        # Check if Kite Connect is authenticated
        if kite_client is None or not kite_client.is_authenticated:
            return jsonify({'error': 'Kite Connect not authenticated. Please setup credentials first.'}), 400
        
        # Initialize backtest engine with Kite Connect client
        engine = BacktestEngine(kite_client)
        
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

@app.route('/setup_credentials')
def setup_credentials():
    return render_template('setup_credentials.html')

@app.route('/save_credentials', methods=['POST'])
def save_credentials():
    global kite_client
    
    try:
        data = request.get_json()
        api_key = data.get('api_key')
        api_secret = data.get('api_secret')
        access_token = data.get('access_token')
        
        if not api_key or not api_secret or not access_token:
            return jsonify({'error': 'API key, API secret, and access token are required'}), 400
        
        # Initialize Kite Connect client
        kite_client = KiteDataClient()
        
        # Authenticate
        success = kite_client.authenticate(api_key, api_secret, access_token)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Kite Connect credentials saved and authenticated successfully!'
            })
        else:
            return jsonify({'error': 'Authentication failed. Please check your credentials.'}), 400
            
    except Exception as e:
        logger.error(f"Error saving credentials: {str(e)}")
        return jsonify({'error': f'Error saving credentials: {str(e)}'}), 500

@app.route('/credentials_status')
def credentials_status():
    global kite_client
    
    if kite_client and kite_client.is_authenticated:
        return jsonify({
            'has_credentials': True,
            'data_source': 'Zerodha Kite Connect',
            'message': 'Kite Connect is authenticated and ready!'
        })
    else:
        return jsonify({
            'has_credentials': False,
            'data_source': 'None',
            'message': 'Please setup Kite Connect credentials'
        })

@app.route('/test_connection')
def test_connection():
    global kite_client
    
    try:
        if kite_client and kite_client.is_authenticated:
            success = kite_client.test_connection()
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Kite Connect connection test successful!'
                })
            else:
                return jsonify({'error': 'Kite Connect connection test failed'}), 400
        else:
            return jsonify({'error': 'Kite Connect not authenticated'}), 400
            
    except Exception as e:
        logger.error(f"Connection test error: {str(e)}")
        return jsonify({'error': f'Connection test failed: {str(e)}'}), 500

@app.route('/kite_redirect')
def kite_redirect():
    """Handle Kite Connect redirect with request_token and automatically exchange for access_token"""
    import hashlib
    import requests
    
    request_token = request.args.get('request_token')
    status = request.args.get('status')
    
    if status == 'success' and request_token:
        try:
            # Get credentials from environment variables or user input
            API_KEY = os.environ.get('KITE_API_KEY')
            API_SECRET = os.environ.get('KITE_API_SECRET')
            
            if not API_KEY or not API_SECRET:
                return f"""
                <html>
                <head><title>Configuration Error</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h2>❌ Configuration Error</h2>
                    <p>API credentials not configured. Please set KITE_API_KEY and KITE_API_SECRET environment variables.</p>
                    <hr>
                    <p><a href="/setup_credentials">← Setup Credentials</a></p>
                </body>
                </html>
                """
            
            # Generate checksum (SHA-256 of api_key + request_token + api_secret)
            checksum = hashlib.sha256(f"{API_KEY}{request_token}{API_SECRET}".encode()).hexdigest()
            
            # POST to /session/token to get access_token
            token_url = "https://api.kite.trade/session/token"
            headers = {"X-Kite-Version": "3"}
            data = {
                "api_key": API_KEY,
                "request_token": request_token,
                "checksum": checksum
            }
            
            logger.info(f"Exchanging request_token for access_token...")
            response = requests.post(token_url, headers=headers, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                if token_data.get('status') == 'success':
                    access_token = token_data['data']['access_token']
                    user_name = token_data['data']['user_name']
                    user_id = token_data['data']['user_id']
                    
                    logger.info(f"Successfully obtained access_token for user: {user_name}")
                    
                    return f"""
                    <html>
                    <head>
                        <title>Kite Connect Success</title>
                        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
                        <style>
                            body {{ background-color: #f0f2f5; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
                            .success-container {{ max-width: 600px; margin: 50px auto; background: white; border-radius: 15px; padding: 40px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
                            .token-box {{ background: #f8f9fa; border: 2px solid #28a745; border-radius: 10px; padding: 20px; margin: 20px 0; }}
                            .btn-custom {{ border-radius: 25px; padding: 12px 30px; font-weight: 600; }}
                        </style>
                    </head>
                    <body>
                        <div class="success-container text-center">
                            <div class="mb-4">
                                <i class="fas fa-check-circle" style="font-size: 4rem; color: #28a745;"></i>
                            </div>
                            <h2 class="text-success mb-3">🎉 Kite Connect Login Successful!</h2>
                            <p class="text-muted mb-4">Welcome, <strong>{user_name}</strong> (ID: {user_id})</p>
                            
                            <div class="token-box">
                                <h5 class="text-success mb-3">✅ Access Token Generated Successfully!</h5>
                                <div class="mb-3">
                                    <label class="form-label"><strong>Access Token:</strong></label>
                                    <input type="text" class="form-control" value="{access_token}" readonly style="font-family: monospace; background: #fff;">
                                </div>
                                <button class="btn btn-outline-success btn-sm" onclick="navigator.clipboard.writeText('{access_token}')">
                                    📋 Copy Access Token
                                </button>
                            </div>
                            
                            <div class="alert alert-info">
                                <strong>Next Steps:</strong><br>
                                1. Copy the access token above<br>
                                2. Go to <a href="/setup_credentials" class="alert-link">Setup Credentials</a><br>
                                3. Enter your API Key, API Secret, and this Access Token<br>
                                4. Click "Save & Test Credentials"
                            </div>
                            
                            <div class="mt-4">
                                <a href="/setup_credentials" class="btn btn-primary btn-custom me-3">
                                    <i class="fas fa-cog"></i> Setup Credentials
                                </a>
                                <a href="/" class="btn btn-outline-secondary btn-custom">
                                    <i class="fas fa-home"></i> Back to Dashboard
                                </a>
                            </div>
                        </div>
                        
                        <script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/js/all.min.js"></script>
                    </body>
                    </html>
                    """
                else:
                    error_msg = token_data.get('message', 'Unknown error')
                    logger.error(f"Token exchange failed: {error_msg}")
                    return f"""
                    <html>
                    <head><title>Token Exchange Failed</title></head>
                    <body style="font-family: Arial; text-align: center; padding: 50px;">
                        <h2>❌ Token Exchange Failed</h2>
                        <p>Error: {error_msg}</p>
                        <hr>
                        <p><a href="/setup_credentials">← Try Again</a></p>
                    </body>
                    </html>
                    """
            else:
                logger.error(f"HTTP error {response.status_code}: {response.text}")
                return f"""
                <html>
                <head><title>HTTP Error</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h2>❌ HTTP Error {response.status_code}</h2>
                    <p>Response: {response.text}</p>
                    <hr>
                    <p><a href="/setup_credentials">← Try Again</a></p>
                </body>
                </html>
                """
                
        except Exception as e:
            logger.error(f"Error in token exchange: {str(e)}")
            return f"""
            <html>
            <head><title>Error</title></head>
            <body style="font-family: Arial; text-align: center; padding: 50px;">
                <h2>❌ Error</h2>
                <p>Error: {str(e)}</p>
                <hr>
                <p><a href="/setup_credentials">← Try Again</a></p>
            </body>
            </html>
            """
    else:
        return f"""
        <html>
        <head><title>Kite Connect Error</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h2>❌ Kite Connect Login Failed</h2>
            <p>Status: {status}</p>
            <p>Request Token: {request_token}</p>
            <hr>
            <p><a href="/setup_credentials">← Try Again</a></p>
        </body>
        </html>
        """

@app.route('/generate_login_url')
def generate_login_url():
    """Generate Kite Connect login URL"""
    API_KEY = os.environ.get('KITE_API_KEY')
    
    if not API_KEY:
        return f"""
        <html>
        <head><title>Configuration Error</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h2>❌ Configuration Error</h2>
            <p>API key not configured. Please set KITE_API_KEY environment variable.</p>
            <hr>
            <p><a href="/setup_credentials">← Setup Credentials</a></p>
        </body>
        </html>
        """
    
    login_url = f"https://kite.zerodha.com/connect/login?v=3&api_key={API_KEY}"
    
    return f"""
    <html>
    <head>
        <title>Kite Connect Login</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {{ background-color: #f0f2f5; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
            .login-container {{ max-width: 600px; margin: 50px auto; background: white; border-radius: 15px; padding: 40px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }}
            .btn-custom {{ border-radius: 25px; padding: 12px 30px; font-weight: 600; }}
        </style>
    </head>
    <body>
        <div class="login-container text-center">
            <div class="mb-4">
                <i class="fas fa-external-link-alt" style="font-size: 4rem; color: #007bff;"></i>
            </div>
            <h2 class="text-primary mb-3">🔗 Kite Connect Login</h2>
            <p class="text-muted mb-4">Click the button below to login to Kite Connect and get your access token automatically!</p>
            
            <div class="alert alert-info mb-4">
                <strong>What happens next:</strong><br>
                1. You'll be redirected to Kite Connect login page<br>
                2. Login with your Zerodha credentials<br>
                3. You'll be redirected back with your access token<br>
                4. The system will automatically set up your credentials!
            </div>
            
            <div class="mb-4">
                <a href="{login_url}" class="btn btn-primary btn-custom btn-lg" target="_blank">
                    <i class="fas fa-sign-in-alt"></i> Login to Kite Connect
                </a>
            </div>
            
            <div class="mt-4">
                <a href="/setup_credentials" class="btn btn-outline-secondary btn-custom me-3">
                    <i class="fas fa-cog"></i> Manual Setup
                </a>
                <a href="/" class="btn btn-outline-secondary btn-custom">
                    <i class="fas fa-home"></i> Back to Dashboard
                </a>
            </div>
        </div>
        
        <script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/js/all.min.js"></script>
    </body>
    </html>
    """

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)