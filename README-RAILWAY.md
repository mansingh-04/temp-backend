# Railway Deployment Guide

This guide will help you deploy the Website Analyzer application to Railway.

## Prerequisites

1. Create a [Railway](https://railway.app/) account
2. Install the [Railway CLI](https://docs.railway.app/develop/cli) (optional but recommended)
3. Have your Gemini API key ready

## Deployment Steps

### 1. Configure Environment Variables

You'll need to set up the following environment variables in your Railway project:

For the backend service:
- `GEMINI_API_KEY`: Your Gemini API key for AI analysis
- `PORT`: 5050 (Railway will configure the external port automatically)

For the frontend service:
- `REACT_APP_API_URL`: This will be automatically set via the railway.toml configuration

### 2. Deploy to Railway

#### Option 1: Using Railway CLI

1. Login to Railway CLI:
   ```
   railway login
   ```

2. Link the project to Railway:
   ```
   railway link
   ```

3. Deploy the project:
   ```
   railway up
   ```

#### Option 2: Using Railway Dashboard

1. Create a new project in the Railway dashboard
2. Connect your GitHub repository
3. Railway will automatically detect the railway.toml configuration
4. Set the required environment variables in the Railway dashboard

### 3. Verify Deployment

Once deployed, you can access your application at the URL provided by Railway.

## Troubleshooting

- If you encounter CORS issues, make sure your backend service is correctly accepting requests from your frontend service
- Check the logs in the Railway dashboard for any errors
- Make sure your Gemini API key is valid and correctly set 