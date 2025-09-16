# Chartink Backtesting Dashboard

A comprehensive web-based backtesting dashboard for Chartink scanner signals using Angel One SmartAPI historical data.

## Features

- **CSV Upload**: Upload Chartink scanner signals directly via drag-and-drop interface
- **SmartAPI Integration**: Fetch real-time historical OHLC data from Angel One
- **Advanced Backtesting**: Support for Stop Loss, Target Profit, and time-based exits
- **Performance Metrics**: Win rate, drawdown, risk-reward ratio, and more
- **Interactive Charts**: Equity curve and returns distribution visualization
- **Export Results**: Download backtest results to Excel format
- **Railway Ready**: Easy deployment on Railway.com with no server management

## Quick Start

### 1. Setup Angel One SmartAPI Credentials

1. Create an account at [Angel One](https://www.angelone.in/)
2. Generate API credentials from your account settings
3. Set up environment variables:

```bash
# Copy the example file
cp env.example .env

# Edit .env with your credentials
ANGEL_API_KEY=your_api_key_here
ANGEL_CLIENT_CODE=your_client_code_here
ANGEL_PIN=your_pin_here
ANGEL_TOTP_SECRET=your_totp_secret_here
```

### 2. Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

Visit `http://localhost:5000` to access the dashboard.

### 3. Deploy to Railway.com

1. Fork this repository to your GitHub account
2. Connect your GitHub account to [Railway.com](https://railway.app/)
3. Create a new project and connect your repository
4. Add environment variables in Railway dashboard:
   - `ANGEL_API_KEY`
   - `ANGEL_CLIENT_CODE`
   - `ANGEL_PIN`
   - `ANGEL_TOTP_SECRET`
5. Deploy!

## Usage Guide

### Step 1: Prepare Your CSV File

Your CSV file should contain the following columns:
- `stock_name`: Stock symbol (e.g., "RELIANCE", "TCS")
- `entry_date`: Entry date in YYYY-MM-DD format
- `entry_time`: Entry time in HH:MM:SS format

Example CSV:
```csv
stock_name,entry_date,entry_time
RELIANCE,2024-01-15,09:30:00
TCS,2024-01-15,10:15:00
INFY,2024-01-16,11:00:00
```

### Step 2: Upload and Configure

1. **Upload CSV**: Drag and drop your CSV file or click "Choose File"
2. **Set Parameters**:
   - **Stop Loss (%)**: Maximum loss percentage (e.g., 5%)
   - **Target Profit (%)**: Target profit percentage (e.g., 10%)
   - **Max Holding Days**: Maximum days to hold a position (e.g., 10)
3. **Run Backtest**: Click "Run Backtest" to start the analysis

### Step 3: Analyze Results

The dashboard displays:

#### Performance Metrics
- **Win Rate**: Percentage of profitable trades
- **Total Trades**: Number of trades analyzed
- **Average Return**: Mean return per trade
- **Risk-Reward Ratio**: Average win to average loss ratio
- **Max Drawdown**: Maximum peak-to-trough decline
- **Best/Worst Trade**: Highest and lowest individual returns
- **Average Holding Days**: Mean holding period

#### Visualizations
- **Equity Curve**: Cumulative P&L over time
- **Returns Distribution**: Histogram of trade returns

#### Export Options
- Download results to Excel for further analysis

## Backtesting Logic

### Entry Logic
- Uses 1-hour candle price at the specified entry time
- If no exact 1-hour candle exists, uses the closest earlier candle
- Entry price is the open price of the selected candle

### Exit Logic
1. **Stop Loss**: Exit if price hits the stop loss level
2. **Target Profit**: Exit if price hits the target profit level
3. **Time-based Exit**: Exit after maximum holding days if neither SL nor TP is hit
4. **End of Data**: Exit at the last available price if data runs out

### Data Handling
- Fetches historical data from Angel One SmartAPI
- Handles missing data gracefully by skipping problematic trades
- Includes rate limiting to respect API limits
- Supports both hourly and daily data for accurate backtesting

## Technical Details

### Architecture
- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Charts**: Plotly.js for interactive visualizations
- **Data Processing**: Pandas for data manipulation
- **API Integration**: Angel One SmartAPI for historical data

### File Structure
```
├── app.py                 # Main Flask application
├── smartapi_client.py     # Angel One API integration
├── backtest_engine.py     # Backtesting logic
├── requirements.txt       # Python dependencies
├── Procfile              # Railway deployment config
├── railway.json          # Railway configuration
├── templates/
│   └── index.html        # Main dashboard template
├── static/
│   ├── css/              # Custom styles
│   └── js/
│       └── app.js        # Frontend JavaScript
└── README.md             # This file
```

### API Endpoints
- `GET /`: Main dashboard
- `POST /upload`: Upload CSV file
- `POST /run_backtest`: Run backtest with parameters
- `GET /export_results`: Download results as Excel
- `GET /health`: Health check endpoint

## Troubleshooting

### Common Issues

1. **"No data found for stock"**
   - Check if the stock symbol is correct
   - Ensure the stock is listed on NSE
   - Verify the date range has available data

2. **"Authentication failed"**
   - Verify your Angel One API credentials
   - Check if your account has API access enabled
   - Ensure TOTP secret is correct for 2FA

3. **"Rate limit exceeded"**
   - The system includes automatic rate limiting
   - Wait a few minutes and try again
   - Consider reducing the number of trades in your CSV

4. **"Missing required columns"**
   - Ensure your CSV has: stock_name, entry_date, entry_time
   - Check column names match exactly (case-sensitive)
   - Verify date format is YYYY-MM-DD

### Performance Tips

- **Batch Size**: Process smaller batches of trades for faster results
- **Date Range**: Limit your CSV to recent data for better performance
- **API Limits**: The system respects Angel One's rate limits automatically

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review Angel One SmartAPI documentation
3. Ensure your CSV format matches the requirements
4. Verify your API credentials are correct

## License

This project is for educational and personal use. Please ensure compliance with Angel One's terms of service and applicable regulations.

## Disclaimer

This tool is for backtesting purposes only. Past performance does not guarantee future results. Always do your own research before making investment decisions. The authors are not responsible for any financial losses.