# Chartink Backtesting Dashboard

A clean, minimal backtesting dashboard for Chartink scanner signals. Ready for your new data source integration.

## Features

- **CSV Upload**: Upload Chartink scanner signals directly via drag-and-drop interface
- **Simple Backtesting**: Hold positions for N days and calculate returns
- **Performance Metrics**: Win rate, total trades, average return, best/worst trade
- **Export Results**: Download backtest results to CSV format
- **Railway Ready**: Easy deployment on Railway.com with no server management

## Quick Start

### 1. Clean Codebase

This dashboard has been cleaned of all complex data source integrations and is ready for your new software integration.

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

## Integration Ready

The codebase is clean and ready for your new data source integration:

- **`backtest_engine.py`**: Contains mock data - replace with your new data source
- **`app.py`**: Clean Flask app with minimal dependencies
- **No complex data clients**: All removed for clean integration

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

## Next Steps

1. **Integrate your new data source** in `backtest_engine.py`
2. **Replace mock data** with real price data
3. **Test with your CSV files**
4. **Deploy to Railway.com**

## Support

This is a clean, minimal codebase ready for your new data source integration. All complex data source logic has been removed for easy customization.