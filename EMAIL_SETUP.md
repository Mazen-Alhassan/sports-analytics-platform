# 📧 Email Notifications Setup for Kyuri

This guide will help you set up email notifications for betting alerts in your Kyuri Sports Betting Platform.

## 🚨 Important: Gmail App Password Required

Gmail requires an **App Password** for third-party applications, not your regular Gmail password.

## 📋 Step-by-Step Setup

### 1. Enable 2-Factor Authentication

1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Navigate to **Security** > **2-Step Verification**
3. Enable 2FA if not already enabled

### 2. Generate App Password

1. In your Google Account, go to **Security**
2. Under "2-Step Verification", click **App passwords**
3. Select **Mail** as the app
4. Select **Other** as the device and name it "Kyuri"
5. Copy the 16-character password (ignore spaces)

### 3. Set Environment Variables

#### Option A: Use the Setup Script (Recommended)

```bash
python setup_email.py
```

#### Option B: Manual Setup

Add these to your shell profile (`~/.bashrc`, `~/.zshrc`, or `~/.bash_profile`):

```bash
export EMAIL_ADDRESS='your-email@gmail.com'
export EMAIL_PASSWORD='your-16-char-app-password'
```

Then reload your shell:

```bash
source ~/.bashrc  # or ~/.zshrc
```

### 4. Restart Kyuri

```bash
python app.py
```

## 🧪 Testing

1. Open Kyuri in your browser: http://localhost:5000
2. Go to the **Notifications** card in the sidebar
3. Enter your email address
4. Click **Test** to send a test email
5. Check your inbox for the test message

## 🔧 Troubleshooting

### "Username and Password not accepted"

- You're using your regular Gmail password instead of an App Password
- Generate a new App Password following steps 1-2 above

### "Less secure app access"

- Gmail no longer supports this - you MUST use App Passwords
- Cannot be bypassed with modern Gmail accounts

### Environment Variables Not Working

Make sure you:

1. Set the variables correctly (no typos)
2. Restarted your terminal/shell
3. Restarted the Kyuri application

## 📱 What You'll Receive

Once configured, you'll get email alerts for:

- 🚨 **Arbitrage Opportunities**: Risk-free profit chances
- 🔥 **Steam Movement**: When multiple bookmakers move odds in the same direction
- 📈 **Line Movement**: Significant odds changes indicating value

## ⚡ Quick Test Commands

Test if environment variables are set:

```bash
echo $EMAIL_ADDRESS
echo $EMAIL_PASSWORD
```

## 🔐 Security Notes

- App Passwords are safer than your main password
- Each app gets its own unique password
- You can revoke app passwords anytime in Google settings
- Never share your app password

## 📞 Need Help?

If you're still having issues:

1. Double-check you're using an App Password (not regular password)
2. Verify 2FA is enabled on your Google account
3. Make sure the environment variables are set correctly
4. Check the Kyuri console output for detailed error messages
