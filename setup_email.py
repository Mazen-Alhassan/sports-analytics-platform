#!/usr/bin/env python3
"""
Email Configuration Setup Script for Kyuri Sports Betting Platform
"""

import os
import getpass

def setup_email_credentials():
    """
    Interactive script to set up email credentials for Kyuri notifications.
    """
    print("🏀 Kyuri Sports Betting Platform - Email Setup")
    print("=" * 50)
    print()
    
    print("📧 Email Notification Setup")
    print("To enable email notifications, you need a Gmail account with 2FA enabled.")
    print()
    
    # Get email address
    while True:
        email = input("Enter your Gmail address: ").strip()
        if "@gmail.com" in email.lower():
            break
        print("Please enter a valid Gmail address (must contain @gmail.com)")
    
    print()
    print("🔐 App Password Setup Required")
    print("You need to create a Gmail App Password (not your regular password)")
    print("Steps:")
    print("1. Go to your Google Account settings")
    print("2. Enable 2-Factor Authentication if not already enabled")
    print("3. Go to Security > 2-Step Verification > App passwords")
    print("4. Generate a new app password for 'Mail'")
    print("5. Copy the 16-character password (no spaces)")
    print()
    print("More info: https://support.google.com/accounts/answer/185833")
    print()
    
    # Get app password
    app_password = getpass.getpass("Enter your Gmail App Password (16 chars): ").strip()
    
    if len(app_password) != 16:
        print("⚠️  Warning: App passwords are typically 16 characters long")
        confirm = input("Continue anyway? (y/n): ").lower()
        if confirm != 'y':
            print("Setup cancelled.")
            return
    
    # Set environment variables
    os.environ['EMAIL_ADDRESS'] = email
    os.environ['EMAIL_PASSWORD'] = app_password
    
    print()
    print("✅ Email credentials configured for this session!")
    print()
    print("🔧 To make this permanent, add these to your shell profile:")
    print(f"export EMAIL_ADDRESS='{email}'")
    print(f"export EMAIL_PASSWORD='{app_password}'")
    print()
    print("📝 Add to ~/.bashrc, ~/.zshrc, or ~/.bash_profile")
    print()
    
    # Test the configuration
    test = input("Would you like to test the email configuration? (y/n): ").lower()
    if test == 'y':
        test_email = input("Enter test email address (or press Enter to use your Gmail): ").strip()
        if not test_email:
            test_email = email
            
        print(f"Testing email to {test_email}...")
        
        # Import and test email function
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = email
            msg['To'] = test_email
            msg['Subject'] = "Kyuri Email Test - Configuration Successful!"
            
            body = """
            <h2>🎉 Email Configuration Successful!</h2>
            <p>Your Kyuri Sports Betting Platform email notifications are now configured.</p>
            <p>You'll receive alerts for:</p>
            <ul>
                <li>🚨 Arbitrage opportunities</li>
                <li>🔥 Steam movements</li>
                <li>📈 Significant line movements</li>
            </ul>
            <p><em>This is a test message from Kyuri setup script.</em></p>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(email, app_password)
            server.sendmail(email, test_email, msg.as_string())
            server.quit()
            
            print("✅ Test email sent successfully!")
            print("📬 Check your inbox to confirm.")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            print("💡 Make sure you're using an App Password, not your regular Gmail password")
    
    print()
    print("🚀 Setup complete! Restart your Kyuri application to use email notifications.")

if __name__ == "__main__":
    setup_email_credentials() 