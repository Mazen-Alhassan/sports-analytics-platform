from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime, timezone
import pytz
from collections import defaultdict
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from twilio.rest import Client

app = Flask(__name__)

# API Configuration
ODDS_API_KEY = 'ba807efa3b017ed4cb064a59bdde4fe6'  # Replace with your Odds API key
ODDS_BASE_URL = 'https://api.the-odds-api.com/v4/sports'
NBA_STATS_BASE_URL = 'https://api-nba-v1.p.rapidapi.com'
NBA_API_KEY = 'a92520124bmsh1d35026bb6db4c9p16ca55jsn2ef321a19a33'  # Replace with your NBA API key
HEADERS = {
    'X-RapidAPI-Key': NBA_API_KEY,
    'X-RapidAPI-Host': 'api-nba-v1.p.rapidapi.com'
}

# Email Configuration
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS', 'your-email@gmail.com')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', 'your-app-password')

# Twilio Configuration (for SMS)
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', 'your-twilio-sid')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', 'your-twilio-token')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '+1234567890')

# Email Configuration Warning
if EMAIL_ADDRESS == 'your-email@gmail.com' or EMAIL_PASSWORD == 'your-app-password':
    print("⚠️  EMAIL CONFIGURATION REQUIRED:")
    print("   To enable email notifications, you need to set up:")
    print("   1. Set EMAIL_ADDRESS environment variable to your Gmail address")
    print("   2. Set EMAIL_PASSWORD environment variable to your Gmail App Password")
    print("   3. Enable 2-Factor Authentication on your Gmail account")
    print("   4. Generate an App Password: https://support.google.com/accounts/answer/185833")
    print("   Example setup:")
    print("   export EMAIL_ADDRESS='your@gmail.com'")
    print("   export EMAIL_PASSWORD='your-16-char-app-password'")
    print("")

# User notification preferences (in production, this would be in a database)
user_notifications = {
    'email_alerts': [],
    'sms_alerts': []
}

DEFAULT_REGIONS = 'us'
DEFAULT_MARKETS = 'h2h,spreads'
DEFAULT_ODDS_FORMAT = 'decimal'
DEFAULT_DATE_FORMAT = 'iso'
TENNIS_REGION_FALLBACKS = ['uk', 'eu', 'us']  # Some tennis books are non-US

# Timezone Configuration
ET = pytz.timezone('US/Eastern')  # Eastern Time zone


def fetch_sports():
    """
    Fetches a list of available sports from the Odds API.
    Consolidates all tennis categories into a single option.
    """
    try:
        response = requests.get(
            ODDS_BASE_URL,
            params={
                'api_key': ODDS_API_KEY,
                'all': 'true'  # Ensures all sports are returned, including tennis
            }
        )
        response.raise_for_status()
        data = response.json()

        # Filter and consolidate tennis categories
        consolidated_sports = []
        tennis_added = False

        for sport in data:
            # Check if it's a tennis category
            if sport['key'].startswith('tennis_'):
                if not tennis_added:
                    # Add a single tennis entry
                    consolidated_sports.append({
                        'key': 'tennis',
                        'title': 'Tennis (All Tournaments)'
                    })
                    tennis_added = True
            else:
                # Add non-tennis sports as usual
                consolidated_sports.append(sport)

        return consolidated_sports
    except requests.RequestException as e:
        print(f"Error fetching sports: {e}")
        return []


def fetch_odds(sport_key):
    """
    Fetches odds for a given sport key.
    If the sport key is 'tennis', it fetches all tennis matches from various tournaments.
    """
    try:
        # If the sport key is 'tennis', we need to fetch all tennis tournaments
        if sport_key == 'tennis':
            # First, get all sports to identify tennis tournaments
            all_sports = requests.get(
                ODDS_BASE_URL,
                params={
                    'api_key': ODDS_API_KEY,
                    'all': 'true'
                },
                timeout=15
            ).json()

            # Extract all tennis tournament keys
            tennis_keys = [sport['key'] for sport in all_sports if sport['key'].startswith('tennis_')]

            # Fetch odds for each tennis tournament and combine results
            all_tennis_odds = []
            for tennis_key in tennis_keys:
                # Try multiple regions for tennis since availability varies
                fetched = False
                for region in TENNIS_REGION_FALLBACKS:
                    try:
                        response = requests.get(
                            f"{ODDS_BASE_URL}/{tennis_key}/odds",
                            params={
                                'api_key': ODDS_API_KEY,
                                'regions': region,
                                'markets': 'h2h',  # tennis is typically moneyline
                                'oddsFormat': DEFAULT_ODDS_FORMAT,
                                'dateFormat': DEFAULT_DATE_FORMAT,
                            },
                            timeout=15
                        )
                        response.raise_for_status()
                        tournament_odds = response.json()
                        if tournament_odds:
                            all_tennis_odds.extend(tournament_odds)
                            fetched = True
                            break
                    except requests.RequestException as e:
                        print(f"Error fetching odds for {tennis_key} in region {region}: {e}")
                if not fetched:
                    print(f"No odds found for {tennis_key} across regions {TENNIS_REGION_FALLBACKS}")

            if all_tennis_odds:
                return all_tennis_odds

            # Fallback: pull upcoming odds across all sports and filter tennis
            for region in TENNIS_REGION_FALLBACKS:
                try:
                    resp = requests.get(
                        f"{ODDS_BASE_URL}/upcoming/odds",
                        params={
                            'api_key': ODDS_API_KEY,
                            'regions': region,
                            'markets': 'h2h',
                            'oddsFormat': DEFAULT_ODDS_FORMAT,
                            'dateFormat': DEFAULT_DATE_FORMAT,
                        },
                        timeout=15
                    )
                    resp.raise_for_status()
                    upcoming = resp.json()
                    tennis_only = [e for e in upcoming if e.get('sport_key', '').startswith('tennis_')]
                    if tennis_only:
                        print(f"Using upcoming/odds fallback for tennis (region={region}) with {len(tennis_only)} events")
                        return tennis_only
                except requests.RequestException as e:
                    print(f"Upcoming fallback error (region {region}): {e}")

            # If still empty, return empty list
            return []
        else:
            # For non-tennis sports, try primary request
            try:
                response = requests.get(
                    f"{ODDS_BASE_URL}/{sport_key}/odds",
                    params={
                        'api_key': ODDS_API_KEY,
                        'regions': DEFAULT_REGIONS,
                        'markets': DEFAULT_MARKETS,
                        'oddsFormat': DEFAULT_ODDS_FORMAT,
                        'dateFormat': DEFAULT_DATE_FORMAT,
                    },
                    timeout=15
                )
                response.raise_for_status()
                data = response.json()
                if data:
                    return data
            except requests.RequestException as e:
                print(f"Primary fetch error for {sport_key}: {e}")

            # Region/market fallback for broader coverage
            region_combo = 'us,us2,uk,eu'
            for markets in ['h2h', 'h2h,spreads', 'h2h,spreads,totals']:
                try:
                    resp = requests.get(
                        f"{ODDS_BASE_URL}/{sport_key}/odds",
                        params={
                            'api_key': ODDS_API_KEY,
                            'regions': region_combo,
                            'markets': markets,
                            'oddsFormat': DEFAULT_ODDS_FORMAT,
                            'dateFormat': DEFAULT_DATE_FORMAT,
                        },
                        timeout=15
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    if data:
                        print(f"Using fallback ({region_combo}, markets={markets}) for {sport_key}, events={len(data)}")
                        return data
                except requests.RequestException as e:
                    print(f"Fallback error for {sport_key} ({markets}): {e}")

            # Final fallback: upcoming across all sports filtered by sport_key
            try:
                resp = requests.get(
                    f"{ODDS_BASE_URL}/upcoming/odds",
                    params={
                        'api_key': ODDS_API_KEY,
                        'regions': region_combo,
                        'markets': 'h2h',
                        'oddsFormat': DEFAULT_ODDS_FORMAT,
                        'dateFormat': DEFAULT_DATE_FORMAT,
                    },
                    timeout=15
                )
                resp.raise_for_status()
                upcoming = resp.json()
                filtered = [e for e in upcoming if e.get('sport_key') == sport_key]
                if filtered:
                    print(f"Using upcoming/odds fallback for {sport_key} with {len(filtered)} events")
                    return filtered
            except requests.RequestException as e:
                print(f"Upcoming fallback error for {sport_key}: {e}")

            return []
    except requests.RequestException as e:
        print(f"Error fetching odds: {e}")
        return []


def calculate_implied_probability(odds):
    """
    Calculate the implied probability from decimal odds.
    Formula: 1 / odds
    """
    return (1 / odds) * 100


def calculate_winnings(odds, bet_amount=10):
    """
    Calculate potential winnings for a given bet amount.
    Formula: (odds - 1) * bet_amount
    """
    return (odds - 1) * bet_amount


def process_odds_data(odds):
    """
    Processes odds data for web display.
    Returns structured data for the template.
    """
    if not odds:
        return {"error": "No odds available for this sport or region. For tennis, availability may be UK/EU only."}

    # Get the current UTC and ET time
    current_time = datetime.now(timezone.utc)
    current_date_et = datetime.now(ET).date()

    # Filter and sort events by commencement time (nearest first)
    future_events = [
        event for event in odds if 'commence_time' in event and datetime.fromisoformat(
            event['commence_time'].replace('Z', '+00:00')) > current_time
    ]
    future_events.sort(key=lambda x: datetime.fromisoformat(x['commence_time'].replace('Z', '+00:00')))

    if not future_events:
        return {"error": "No upcoming events."}

    # Process events
    processed_events = []
    for event in future_events:
        home_team = event.get('home_team', "TBA")
        away_team = event.get('away_team', "TBA")
        commence_time = event.get('commence_time')
        tournament = event.get('sport_title', "")  # Get tournament name if available

        event_data = {
            "home_team": home_team,
            "away_team": away_team,
            "tournament": tournament,
            "sport_key": event.get('sport_key', ""),
            "bookmakers": []
        }

        try:
            event_time_utc = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
            event_time_et = event_time_utc.astimezone(ET)  # Convert to Eastern Time
            formatted_time = event_time_et.strftime('%Y-%m-%d %I:%M:%S %p %Z')  # 12-hour format with AM/PM
            # Add rich time metadata for UI grouping/filters
            event_data["time"] = formatted_time
            event_data["date_iso"] = event_time_et.strftime('%Y-%m-%d')
            event_data["weekday"] = event_time_et.strftime('%A')
            event_data["is_today"] = event_time_et.date() == current_date_et
        except (TypeError, ValueError):
            event_data["time"] = "TBA (Invalid or missing date)"

        # Process bookmakers and odds
        best_suggestion = None
        highest_probability = 0

        for bookmaker in event.get('bookmakers', []):
            bookmaker_data = {
                "name": bookmaker['title'],
                "markets": []
            }

            for market in bookmaker.get('markets', []):
                market_data = {
                    "key": market['key'],
                    "outcomes": []
                }

                if market['key'] == 'h2h':  # Head-to-head market
                    for outcome in market['outcomes']:
                        name = outcome['name']
                        price = outcome['price']
                        probability = calculate_implied_probability(price)
                        winnings = calculate_winnings(price)

                        outcome_data = {
                            "name": name,
                            "price": price,
                            "probability": round(probability, 2),
                            "winnings": round(winnings, 2)
                        }

                        market_data["outcomes"].append(outcome_data)

                        # Update the best suggestion
                        if probability > highest_probability:
                            highest_probability = probability
                            best_suggestion = name

                bookmaker_data["markets"].append(market_data)

            event_data["bookmakers"].append(bookmaker_data)

        # Add suggestion
        event_data["suggestion"] = {
            "team": best_suggestion,
            "probability": round(highest_probability, 2) if highest_probability > 0 else None
        }

        processed_events.append(event_data)

    return {"events": processed_events}


def send_email_alert(to_email, subject, message):
    """
    Send email alert for betting opportunities.
    """
    try:
        # Check if email credentials are configured
        if EMAIL_ADDRESS == 'your-email@gmail.com' or EMAIL_PASSWORD == 'your-app-password':
            print("❌ Email not configured. Please set EMAIL_ADDRESS and EMAIL_PASSWORD environment variables.")
            return False
            
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(message, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, to_email, text)
        server.quit()
        
        print(f"✅ Email sent successfully to {to_email}")
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        if "Username and Password not accepted" in str(e):
            print("💡 Gmail requires an App Password, not your regular password.")
            print("   Visit: https://support.google.com/accounts/answer/185833")
        return False


def send_sms_alert(to_phone, message):
    """
    Send SMS alert for betting opportunities.
    """
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        message = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to_phone
        )
        
        return True
    except Exception as e:
        print(f"Error sending SMS: {e}")
        return False


def format_alert_message(alert_data, format_type='email'):
    """
    Format alert message for email or SMS.
    """
    if format_type == 'email':
        if alert_data['type'] == 'arbitrage':
            return f"""
            <h2>🚨 Arbitrage Opportunity Detected!</h2>
            <p><strong>Game:</strong> {alert_data['game']}</p>
            <p><strong>Guaranteed Profit:</strong> {alert_data['profit']}%</p>
            <p><strong>Total Implied Probability:</strong> {alert_data['totalProb']}%</p>
            <p>This is a risk-free betting opportunity. Act quickly as odds may change!</p>
            <hr>
            <p><em>Sent by Kyuri Sports Betting Analyzer</em></p>
            """
        elif alert_data['type'] == 'steam':
            return f"""
            <h2>🔥 Steam Movement Alert!</h2>
            <p><strong>Game:</strong> {alert_data['game']}</p>
            <p><strong>Outcome:</strong> {alert_data['outcome']}</p>
            <p><strong>Movement:</strong> {alert_data['direction'].upper()}</p>
            <p><strong>Bookmakers:</strong> {alert_data['bookmakers']} books moved</p>
            <p><strong>Average Change:</strong> {alert_data['avgChange']}</p>
            <p>Multiple bookmakers are moving in the same direction - this could indicate sharp money!</p>
            <hr>
            <p><em>Sent by Kyuri Sports Betting Analyzer</em></p>
            """
        elif alert_data['type'] == 'movement':
            return f"""
            <h2>📈 Significant Line Movement!</h2>
            <p><strong>Game:</strong> {alert_data['game']}</p>
            <p><strong>Bookmaker:</strong> {alert_data['bookmaker']}</p>
            <p><strong>Outcome:</strong> {alert_data['outcome']}</p>
            <p><strong>Movement:</strong> {alert_data['from']} → {alert_data['to']} ({alert_data['change']})</p>
            <p>Significant line movement detected. This could be a betting opportunity!</p>
            <hr>
            <p><em>Sent by Kyuri Sports Betting Analyzer</em></p>
            """
    else:  # SMS format
        if alert_data['type'] == 'arbitrage':
            return f"🚨 ARBITRAGE: {alert_data['game']} - {alert_data['profit']}% guaranteed profit! Act fast!"
        elif alert_data['type'] == 'steam':
            return f"🔥 STEAM: {alert_data['game']} - {alert_data['outcome']} moved {alert_data['direction']} across {alert_data['bookmakers']} books"
        elif alert_data['type'] == 'movement':
            return f"📈 LINE MOVE: {alert_data['game']} - {alert_data['outcome']} @ {alert_data['bookmaker']}: {alert_data['from']}→{alert_data['to']}"


def generate_auto_parlay(odds):
    """
    Automatically builds a parlay with teams that have a 65% or higher implied probability of winning.
    Averages odds and probabilities for each team across all bookmakers and includes each team only once.
    """
    # Dictionary to store average odds and probabilities for each team
    team_data = defaultdict(lambda: {'total_odds': 0, 'total_probability': 0, 'count': 0, 'game': ''})

    # Collect odds and probabilities for each team
    for event in odds:
        home_team = event.get('home_team', "TBA")
        away_team = event.get('away_team', "TBA")
        game = f"{home_team} vs {away_team}"

        for bookmaker in event.get('bookmakers', []):
            for market in bookmaker.get('markets', []):
                if market['key'] == 'h2h':  # Head-to-head market
                    for outcome in market['outcomes']:
                        team = outcome['name']
                        odds_value = outcome['price']
                        probability = calculate_implied_probability(odds_value)

                        # Update team data
                        team_data[team]['total_odds'] += odds_value
                        team_data[team]['total_probability'] += probability
                        team_data[team]['count'] += 1
                        team_data[team]['game'] = game

    # Calculate averages and filter teams with 65%+ probability
    high_probability_teams = []
    for team, data in team_data.items():
        if data['count'] > 0:
            avg_odds = data['total_odds'] / data['count']
            avg_probability = data['total_probability'] / data['count']

            if avg_probability >= 65:
                high_probability_teams.append({
                    'team': team,
                    'odds': round(avg_odds, 2),
                    'probability': round(avg_probability, 2),
                    'game': data['game']
                })

    if not high_probability_teams:
        return {"error": "No teams found with a 65% or higher implied probability."}

    # Calculate combined odds and implied probability
    combined_odds = 1.0
    for team in high_probability_teams:
        combined_odds *= team['odds']

    implied_probability = calculate_implied_probability(combined_odds)
    potential_winnings = calculate_winnings(combined_odds)

    return {
        "teams": high_probability_teams,
        "combined_odds": round(combined_odds, 2),
        "implied_probability": round(implied_probability, 2),
        "potential_winnings": round(potential_winnings, 2),
        "num_legs": len(high_probability_teams)
    }


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/sports')
def api_sports():
    sports = fetch_sports()
    return jsonify(sports)


@app.route('/api/odds/<sport_key>')
def api_odds(sport_key):
    odds = fetch_odds(sport_key)
    return jsonify(process_odds_data(odds))


@app.route('/api/parlay/<sport_key>')
def api_parlay(sport_key):
    odds = fetch_odds(sport_key)
    parlay_data = generate_auto_parlay(odds)
    return jsonify(parlay_data)


@app.route('/api/notifications/subscribe', methods=['POST'])
def subscribe_notifications():
    """
    Subscribe to email or SMS notifications.
    """
    data = request.get_json()
    notification_type = data.get('type')  # 'email' or 'sms'
    contact = data.get('contact')  # email address or phone number
    alert_types = data.get('alert_types', ['arbitrage', 'steam', 'movement'])
    
    if not notification_type or not contact:
        return jsonify({'error': 'Missing notification type or contact information'}), 400
    
    if notification_type == 'email':
        user_notifications['email_alerts'].append({
            'email': contact,
            'alert_types': alert_types,
            'created_at': datetime.now().isoformat()
        })
    elif notification_type == 'sms':
        user_notifications['sms_alerts'].append({
            'phone': contact,
            'alert_types': alert_types,
            'created_at': datetime.now().isoformat()
        })
    else:
        return jsonify({'error': 'Invalid notification type'}), 400
    
    return jsonify({'success': True, 'message': f'{notification_type.upper()} notifications enabled'})


@app.route('/api/notifications/unsubscribe', methods=['POST'])
def unsubscribe_notifications():
    """
    Unsubscribe from notifications.
    """
    data = request.get_json()
    notification_type = data.get('type')
    contact = data.get('contact')
    
    if notification_type == 'email':
        user_notifications['email_alerts'] = [
            alert for alert in user_notifications['email_alerts'] 
            if alert['email'] != contact
        ]
    elif notification_type == 'sms':
        user_notifications['sms_alerts'] = [
            alert for alert in user_notifications['sms_alerts'] 
            if alert['phone'] != contact
        ]
    
    return jsonify({'success': True, 'message': 'Unsubscribed successfully'})


@app.route('/api/notifications/send-alert', methods=['POST'])
def send_alert_notification():
    """
    Send alert notifications to subscribed users.
    This would typically be called by the frontend when alerts are detected.
    """
    data = request.get_json()
    alert_data = data.get('alert_data')
    
    if not alert_data:
        return jsonify({'error': 'Missing alert data'}), 400
    
    sent_count = 0
    
    # Send email alerts
    for email_sub in user_notifications['email_alerts']:
        if alert_data['type'] in email_sub['alert_types']:
            subject = f"Kyuri Alert: {alert_data['type'].title()} Opportunity"
            message = format_alert_message(alert_data, 'email')
            
            if send_email_alert(email_sub['email'], subject, message):
                sent_count += 1
    
    # Send SMS alerts
    for sms_sub in user_notifications['sms_alerts']:
        if alert_data['type'] in sms_sub['alert_types']:
            message = format_alert_message(alert_data, 'sms')
            
            if send_sms_alert(sms_sub['phone'], message):
                sent_count += 1
    
    return jsonify({
        'success': True, 
        'message': f'Alert sent to {sent_count} subscribers'
    })


@app.route('/api/notifications/test', methods=['POST'])
def test_notifications():
    """
    Test notification system.
    """
    data = request.get_json()
    notification_type = data.get('type')
    contact = data.get('contact')
    
    test_alert = {
        'type': 'arbitrage',
        'game': 'Test Team A @ Test Team B',
        'profit': '5.25',
        'totalProb': '94.75'
    }
    
    if notification_type == 'email':
        # Check if email is configured before attempting to send
        if EMAIL_ADDRESS == 'your-email@gmail.com' or EMAIL_PASSWORD == 'your-app-password':
            return jsonify({
                'success': False,
                'message': 'Email not configured. Please set up Gmail credentials first. Check the server console for setup instructions.'
            })
            
        subject = "Kyuri Test Alert"
        message = format_alert_message(test_alert, 'email')
        success = send_email_alert(contact, subject, message)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Test email sent successfully! Check your inbox.'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send test email. Check server console for details. You may need to set up Gmail App Password.'
            })
            
    elif notification_type == 'sms':
        message = format_alert_message(test_alert, 'sms')
        success = send_sms_alert(contact, message)
        
        return jsonify({
            'success': success,
            'message': 'Test SMS sent successfully!' if success else 'Failed to send test SMS. Check Twilio configuration.'
        })
    else:
        return jsonify({'error': 'Invalid notification type'}), 400


if __name__ == '__main__':
    app.run(debug=True)