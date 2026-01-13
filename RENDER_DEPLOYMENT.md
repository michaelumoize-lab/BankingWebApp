# Banking Web App - Render Deployment Guide

## Prerequisites
1. GitHub account
2. Render account (https://render.com)

## Deployment Steps

### Step 1: Push to GitHub
```bash
git remote add origin https://github.com/YOUR_USERNAME/BankingWebApp.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Render
1. Go to https://render.com and sign in with GitHub
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `bankingwebapp` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && python bankapp/manage.py migrate && python bankapp/manage.py collectstatic --noinput`
   - **Start Command**: `gunicorn bankapp.wsgi:application --bind 0.0.0.0:$PORT`
   - **Plan**: Free tier (or paid if needed)

### Step 3: Add Environment Variables
In Render dashboard → Environment:
- `DEBUG`: `False`
- `SECRET_KEY`: Generate a new Django secret key
- Database is auto-provided by Render

### Step 4: Deploy
Click "Create Web Service" and wait for deployment to complete.

## Features
- ✅ Django 6.0.1 with custom User authentication
- ✅ Loans system with EMI calculation
- ✅ Bank statements generation
- ✅ 4-digit PIN authentication
- ✅ Bill payments
- ✅ Customer reviews with admin approval
- ✅ Modern dashboard with analytics charts
- ✅ Responsive design (mobile-friendly)
- ✅ Color scheme: Orange, Blue, Green

## Database
- Local: SQLite3 (db.sqlite3)
- Production: PostgreSQL (auto-provided by Render)

## Admin Access
After deployment:
1. Create a superuser: `python bankapp/manage.py createsuperuser`
2. Access admin at: `https://your-app-name.onrender.com/admin`

## Troubleshooting
- Check logs in Render dashboard
- Ensure all environment variables are set
- Verify `requirements.txt` has all dependencies
- Confirm static files are being served correctly
