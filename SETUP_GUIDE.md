# Setup Guide - Chartink Backtesting Dashboard

This guide will walk you through setting up the Chartink Backtesting Dashboard step by step.

## Prerequisites

- Python 3.8 or higher
- Angel One trading account with API access
- GitHub account (for Railway deployment)

## Step 1: Angel One API Setup

### 1.1 Create Angel One Account
1. Visit [Angel One](https://www.angelone.in/)
2. Sign up for a trading account
3. Complete KYC verification

### 1.2 Enable API Access
1. Log into your Angel One account
2. Go to "Settings" → "API Access"
3. Request API access (may require approval)
4. Generate API credentials:
   - API Key
   - Client Code
   - PIN
   - TOTP Secret (for 2FA)

### 1.3 Test API Access
You can test your API credentials using the SmartAPI documentation at [smartapi.angelbroking.com/docs](https://smartapi.angelbroking.com/docs)

## Step 2: Local Development Setup

### 2.1 Clone the Repository
```bash
git clone <your-repo-url>
cd chartink_dashboard_angelone
```

### 2.2 Install Dependencies
```bash
pip install -r requirements.txt
```

### 2.3 Configure Environment Variables
```bash
# Copy the example file
cp env.example .env

# Edit .env with your credentials
nano .env  # or use any text editor
```

Add your Angel One credentials:
```env
ANGEL_API_KEY=your_actual_api_key
ANGEL_CLIENT_CODE=your_actual_client_code
ANGEL_PIN=your_actual_pin
ANGEL_TOTP_SECRET=your_actual_totp_secret
```

### 2.4 Run the Application
```bash
python app.py
```

Visit `http://localhost:5000` to access the dashboard.

## Step 3: Railway.com Deployment

### 3.1 Prepare for Deployment
1. Push your code to GitHub
2. Ensure all environment variables are in `env.example`

### 3.2 Deploy to Railway
1. Visit [Railway.app](https://railway.app/)
2. Sign up with your GitHub account
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway will automatically detect the Python app

### 3.3 Configure Environment Variables
1. In Railway dashboard, go to your project
2. Click on "Variables" tab
3. Add the following variables:
   - `ANGEL_API_KEY`: Your Angel One API key
   - `ANGEL_CLIENT_CODE`: Your Angel One client code
   - `ANGEL_PIN`: Your Angel One PIN
   - `ANGEL_TOTP_SECRET`: Your TOTP secret
   - `SECRET_KEY`: A random secret key for Flask

### 3.4 Deploy
1. Railway will automatically deploy your app
2. Wait for deployment to complete
3. Your app will be available at the provided Railway URL

## Step 4: Testing Your Setup

### 4.1 Test CSV Upload
1. Create a test CSV file with sample data:
```csv
stock_name,entry_date,entry_time
RELIANCE,2024-01-15,09:30:00
TCS,2024-01-15,10:15:00
```

2. Upload the CSV file
3. Set backtest parameters:
   - Stop Loss: 5%
   - Target Profit: 10%
   - Max Holding Days: 10

4. Run the backtest

### 4.2 Verify Results
- Check that the dashboard shows results
- Verify that charts are displayed
- Test the export functionality

## Step 5: Production Considerations

### 5.1 Security
- Never commit your `.env` file to version control
- Use strong, unique secret keys
- Regularly rotate your API credentials

### 5.2 Performance
- Monitor API rate limits
- Consider caching for frequently accessed data
- Optimize CSV file sizes for better performance

### 5.3 Monitoring
- Set up health checks
- Monitor application logs
- Track API usage and costs

## Troubleshooting

### Common Setup Issues

1. **Import Errors**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **API Authentication Failures**
   - Double-check your credentials
   - Ensure your account has API access
   - Verify TOTP secret is correct

3. **Railway Deployment Issues**
   - Check environment variables are set
   - Review deployment logs
   - Ensure `Procfile` is present

4. **CSV Upload Issues**
   - Verify CSV format matches requirements
   - Check file size limits
   - Ensure proper column names

### Getting Help

1. Check the main README.md for detailed documentation
2. Review Angel One SmartAPI documentation
3. Check Railway deployment logs
4. Verify your CSV file format

## Next Steps

Once your setup is complete:

1. **Upload Your Data**: Prepare your Chartink CSV files
2. **Run Backtests**: Test different parameters and strategies
3. **Analyze Results**: Use the dashboard metrics and charts
4. **Export Data**: Download results for further analysis
5. **Iterate**: Refine your strategy based on results

## Support

For technical support:
- Check the troubleshooting section
- Review application logs
- Ensure all prerequisites are met
- Verify API credentials and permissions

Remember: This tool is for backtesting only. Always do your own research before making investment decisions.
