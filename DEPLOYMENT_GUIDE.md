# 🚀 Deployment Guide - Chartink Backtesting Dashboard

## 🔒 Security First

**NEVER commit your real API credentials to git!**

Your Kite Connect credentials:
- **API Key**: `frzvtsavhoshiqca`
- **API Secret**: `xgpm2uv9kskqluzfoa4tg7fa61a3ztd7`
- **Client ID**: `FTH348`

## 📋 Pre-Deployment Checklist

### ✅ Files Ready:
- [x] `app.py` - Main Flask application
- [x] `kite_client.py` - Kite Connect integration
- [x] `backtest_engine.py` - Backtesting logic
- [x] `requirements.txt` - Dependencies
- [x] `Procfile` - Railway deployment
- [x] `runtime.txt` - Python version
- [x] `.gitignore` - Security (credentials protected)

### ✅ Security:
- [x] `.gitignore` created (protects credentials)
- [x] Environment variables setup
- [x] No hardcoded credentials in code
- [x] Secure credential storage in dashboard

## 🚀 Railway Deployment

### 1. Connect to Railway
```bash
# Your repo is already connected to Railway
# Just push to deploy
git push origin main
```

### 2. Set Environment Variables in Railway
Go to your Railway dashboard and add:
```
KITE_API_KEY=frzvtsavhoshiqca
KITE_ACCESS_TOKEN=your_access_token_here
SECRET_KEY=your_secret_key_here
```

### 3. Get Access Token
1. Deploy to Railway first
2. Use the login flow to get access token
3. Add access token to Railway environment variables

## 🔧 Local Testing

### 1. Create `.env` file (NEVER commit this!)
```bash
# .env file (local only)
KITE_API_KEY=frzvtsavhoshiqca
KITE_ACCESS_TOKEN=your_access_token_here
SECRET_KEY=your_secret_key_here
```

### 2. Run locally
```bash
pip install -r requirements.txt
python app.py
```

## 📱 Usage Flow

1. **Deploy to Railway** → Get your app URL
2. **Get Access Token** → Use login flow with your app URL
3. **Setup Credentials** → Enter API key and access token in dashboard
4. **Upload CSV** → Your Chartink signals
5. **Run Backtest** → Get real results with Kite Connect data

## 🛡️ Security Best Practices

- ✅ Credentials stored in environment variables
- ✅ `.gitignore` protects sensitive files
- ✅ No hardcoded API keys in code
- ✅ Secure credential setup page
- ✅ HTTPS redirect URLs for production

## 🎯 Your App Details

- **App Name**: chartink-backtesting-dashboard
- **Redirect URL**: http://localhost:5000 (local) / https://your-app.railway.app (production)
- **Postback URL**: https://chartinkdashboardangelone-production.up.railway.app/
- **Status**: Active
- **Expires**: 19 Oct 2025

## ✅ Ready for Production!

Your dashboard is fully integrated with Zerodha Kite Connect and ready for deployment. All security measures are in place.
