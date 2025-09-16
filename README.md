# Chartink Backtesting Dashboard

A comprehensive web-based backtesting dashboard for Chartink scanner signals using Yahoo Finance historical data.

## Features

- **CSV Upload**: Upload Chartink scanner signals directly via drag-and-drop interface
- **Yahoo Finance Integration**: Fetch real-time historical OHLC data from Yahoo Finance (no API keys required!)
- **Advanced Backtesting**: Support for Stop Loss, Target Profit, and time-based exits
- **Performance Metrics**: Win rate, drawdown, risk-reward ratio, and more
- **Interactive Charts**: Equity curve and returns distribution visualization
- **Export Results**: Download backtest results to CSV format
- **Railway Ready**: Easy deployment on Railway.com with no server management

## Quick Start

### 1. No API Credentials Required!

This dashboard uses Yahoo Finance (yfinance) for historical data, which is completely free and doesn't require any API keys or authentication.

### 2. Upload Your Chartink CSV

1. Export your Chartink scanner signals as CSV
2. Upload the CSV file to the dashboard
3. The dashboard supports the format: `date, symbol, marketcapname, sector`

### 3. Configure Backtest Parameters

- **Stop Loss %**: Set your stop loss percentage (e.g., 5%)
- **Target Profit %**: Set your target profit percentage (e.g., 10%)
- **Max Holding Days**: Maximum days to hold a position (e.g., 10 days)

### 4. Run Backtest

Click "Run Backtest" to analyze your strategy performance.

### 5. View Results

- **Performance Metrics**: Win rate, average returns, max drawdown
- **Equity Curve**: Visual representation of your strategy performance
- **Trade Details**: Individual trade results and analysis
- **Export**: Download results as CSV for further analysis

## CSV Format

The dashboard supports Chartink CSV exports with the following format:

```csv
date,symbol,marketcapname,sector
06-08-2025 10:15 am,YATHARTH,Midcap,Pharmaceuticals
06-08-2025 10:15 am,KAMATHOTEL,Smallcap,Services
```

## Deployment

### Railway.com (Recommended)

1. Fork this repository
2. Connect your GitHub account to Railway
3. Deploy from GitHub
4. No environment variables needed!

### Local Development

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the app: `python app.py`
4. Open http://localhost:5000

## Technical Details

- **Backend**: Flask (Python)
- **Data Source**: Yahoo Finance (yfinance)
- **Frontend**: Bootstrap 5 + Plotly.js
- **Database**: In-memory (no database required)
- **Deployment**: Railway.com ready

## Supported Exchanges

- **NSE**: National Stock Exchange of India
- **BSE**: Bombay Stock Exchange
- **NSE F&O**: NSE Futures & Options
- **BSE F&O**: BSE Futures & Options

## Data Coverage

- **Historical Data**: Available for most Indian stocks
- **Timeframes**: 1 minute, 5 minutes, 15 minutes, 30 minutes, 1 hour, 1 day
- **Data Quality**: High-quality OHLC data from Yahoo Finance

## Troubleshooting

### Common Issues

1. **No data found for symbol**: The stock symbol might not be available on Yahoo Finance
2. **CSV format error**: Ensure your CSV has the correct format with date and symbol columns
3. **Deployment issues**: Check Railway logs for any deployment errors

### Getting Help

- Check the Railway deployment logs
- Verify your CSV format matches the expected structure
- Ensure the stock symbols are valid NSE/BSE symbols

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This tool is for educational and research purposes only. Always do your own research before making investment decisions. Past performance does not guarantee future results.