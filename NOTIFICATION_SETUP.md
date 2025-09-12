# Notification Setup Guide

## Email Notifications Setup

### 1. Gmail Configuration

1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. Set environment variables:
   ```bash
   export EMAIL_ADDRESS="your-email@gmail.com"
   export EMAIL_PASSWORD="your-app-password"
   ```

### 2. Other Email Providers

Update the SMTP settings in `app.py`:

- **Outlook**: `smtp.live.com`, port 587
- **Yahoo**: `smtp.mail.yahoo.com`, port 587
- **Custom**: Check your provider's SMTP settings

## SMS Notifications Setup

### 1. Twilio Account

1. Sign up at [twilio.com](https://www.twilio.com)
2. Get your Account SID and Auth Token from the dashboard
3. Purchase a phone number or use the trial number
4. Set environment variables:
   ```bash
   export TWILIO_ACCOUNT_SID="your-account-sid"
   export TWILIO_AUTH_TOKEN="your-auth-token"
   export TWILIO_PHONE_NUMBER="+1234567890"
   ```

### 2. Alternative SMS Providers

You can replace Twilio with other providers by modifying the `send_sms_alert()` function in `app.py`.

## Installation

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Set environment variables (see above)

3. Run the application:
   ```bash
   python app.py
   ```

## Features

### Alert Types

- **Arbitrage Opportunities**: When total implied probability < 100%
- **Steam Movement**: When multiple bookmakers move odds in same direction
- **Line Movement**: When odds change by more than 0.10 points

### Notification Methods

- **Email**: HTML formatted alerts with detailed information
- **SMS**: Concise text alerts for mobile notifications

### Usage

1. Start live updates on any sport
2. Subscribe to email/SMS notifications in the sidebar
3. Test notifications to verify setup
4. Receive real-time alerts when opportunities are detected

## Security Notes

- Never commit API keys or passwords to version control
- Use environment variables for all sensitive configuration
- Consider using a dedicated email account for notifications
- Monitor your Twilio usage to avoid unexpected charges
