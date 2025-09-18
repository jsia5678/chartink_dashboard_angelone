# Chartink Backtesting Dashboard

A comprehensive backtesting dashboard for Chartink scanner signals using Zerodha Kite Connect API for real historical data.

## Features

- **CSV Upload**: Upload Chartink scanner signals directly via drag-and-drop interface
- **Zerodha Kite Connect**: Real historical data from NSE/BSE via official API
- **Simple Backtesting**: Hold positions for N days and calculate returns
- **Performance Metrics**: Win rate, total trades, average return, best/worst trade
- **Export Results**: Download backtest results to CSV format
- **Railway Ready**: Easy deployment on Railway.com with no server management

## Quick Start

### 1. Setup Kite Connect Credentials

1. Get your API key from [Kite Connect](https://kite.trade/)
2. Get your access token through the login flow
3. Click "Setup Credentials" on the dashboard
4. Enter your API key and access token
5. Test the connection

### 2. Upload Your Chartink CSV

1. Export your Chartink scanner signals as CSV
2. Upload the CSV file to the dashboard
3. The dashboard supports the format: `date, symbol, marketcapname, sector`

### 3. Configure Backtest Parameters

- **Hold for how many days?**: Set the number of days to hold each position (e.g., 10 days)

### 4. Run Backtest

Click "Run Simple Backtest" to process your signals and see the results.

### 5. View Results

The dashboard will show:
- **Performance Metrics**: Win rate, total trades, average return, etc.
- **Results Table**: Individual trade results with entry/exit prices and returns
- **Export Option**: Download results as CSV

## CSV Format

Your CSV file should have these columns:
- `date`: Entry date and time (format: DD-MM-YYYY H:MM AM/PM)
- `symbol`: Stock symbol (e.g., RELIANCE, TCS)
- `marketcapname`: Market cap category
- `sector`: Stock sector

Example:
```csv
date,symbol,marketcapname,sector
06-08-2025 10:15 am,RELIANCE,Large Cap,Energy
06-08-2025 10:30 am,TCS,Large Cap,Technology
```

## Kite Connect Integration

The dashboard is fully integrated with Zerodha Kite Connect:

- **`kite_client.py`**: Complete Kite Connect API integration
- **`backtest_engine.py`**: Uses real historical data from Kite Connect
- **`app.py`**: Flask app with authentication and data fetching
- **Credentials Setup**: Secure credential management system

## Deployment

### Railway.com (Recommended)

1. Fork this repository
2. Connect to Railway.com
3. Deploy automatically
4. No server management required

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

## File Structure

```
├── app.py                 # Main Flask application
├── backtest_engine.py     # Backtesting logic (ready for your data source)
├── templates/
│   └── index.html        # Dashboard UI
├── static/
│   └── js/
│       └── app.js        # Frontend JavaScript
├── requirements.txt      # Python dependencies
├── Procfile             # Railway deployment config
└── README.md            # This file
```

## API Documentation

- **Kite Connect API**: [https://kite.trade/docs/connect/v3/](https://kite.trade/docs/connect/v3/)
- **Historical Data**: [https://kite.trade/docs/connect/v3/historical/](https://kite.trade/docs/connect/v3/historical/)
- **Python Client**: [https://github.com/zerodha/pykiteconnect](https://github.com/zerodha/pykiteconnect)

## Next Steps

1. **Get Kite Connect credentials** from [kite.trade](https://kite.trade/)
2. **Setup credentials** in the dashboard
3. **Test with your CSV files**
4. **Deploy to Railway.com**

## Support

This dashboard is fully integrated with Zerodha Kite Connect API for real historical data fetching. All data source issues have been resolved with the official API.