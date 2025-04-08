from flask import Flask, render_template, request, jsonify, redirect, url_for, session, make_response, send_from_directory, send_file
from risk_assessment import RiskAssessor
from user_management import UserManager
from recommendation_engine import RecommendationEngine
from flask_cors import CORS
from flask_session import Session
import os
from google.oauth2 import id_token
from google.auth.transport import requests
from dotenv import load_dotenv
import json
import asyncio
from database import (
    create_or_update_user, get_user_by_email, update_user_details,
    has_risk_assessment, has_recommendations, get_user_recommendations,
    risk_assessments_collection, recommendations_collection,
    get_user_risk_assessment
)
from datetime import datetime, timedelta
import re
from bson.objectid import ObjectId
import platform
import time
import traceback
from functools import wraps
from flask_caching import Cache
import logging
from logging.handlers import RotatingFileHandler
from news_service import NewsService

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
logger.addHandler(handler)

app = Flask(__name__, static_folder='static')
CORS(app) 
app.secret_key = os.urandom(24)  
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.context_processor
def inject_now():
    """Make the current datetime available to all templates."""
    return {'now': datetime.now()}

@app.before_request
def before_request():
    if not request.path.startswith('/static/'):
        response = make_response()
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

risk_assessor = RiskAssessor()
user_manager = UserManager()
recommendation_engine = RecommendationEngine()

if platform.system().lower() == 'windows':
    import socket
    
    old_socket = socket.socket
    def new_socket(*args, **kwargs):
        s = old_socket(*args, **kwargs)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s
    socket.socket = new_socket

cache = Cache(app, config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 300
})

@app.route('/')
def index():
    session.clear()
    return render_template('index.html')

@app.route('/retake-assessment')
def retake_assessment():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    
    try:
        risk_assessments_collection.delete_many({"user_id": ObjectId(user_id)})
        recommendations_collection.delete_many({"user_id": ObjectId(user_id)})
        print(f"Deleted risk assessments for user {user_id}")
    except Exception as e:
        print(f"Error deleting risk assessments: {e}")
    
    return redirect(url_for('questionnaire'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        try:
            user_id = session['user_id']
            recommendations_collection.delete_many({"user_id": ObjectId(user_id)})
            keys_to_remove = [k for k in session.keys() if 
                            k in ('cached_recommendations', 'recommendation_timestamp', 
                                 'selected_risk_profile', 'cache_buster')]
            for key in keys_to_remove:
                session.pop(key, None)
                
        except Exception as e:
            print(f"Error clearing old recommendations: {e}")
    
    if request.method == 'POST':
        if request.is_json:
            token = request.json.get('token')
            try:
                idinfo = id_token.verify_oauth2_token(
                    token,
                    requests.Request(),
                    os.getenv('GOOGLE_CLIENT_ID')
                )
                email = idinfo['email']
                user = get_user_by_email(email)
                if not user:
                    user_data = {
                        "email": email,
                        "name": idinfo.get('name', ''),
                        "account_creation_date": datetime.utcnow(),
                        "preferred_notification_method": "Email"
                    }
                    user_id = create_or_update_user(user_data)
                else:
                    user_id = user['_id']
                session.clear()
                session['username'] = email
                session['user_id'] = str(user_id)

                if has_risk_assessment(user_id):
                    return redirect(url_for('recommendations'))
                return redirect(url_for('questionnaire'))

            except ValueError as e:
                return jsonify({'error': str(e)}), 400
        else:
            email = request.form.get('email')
            password = request.form.get('password')
            if user_manager.verify_user(email, password):
                user = get_user_by_email(email)
                session.clear()
                session['username'] = email
                session['user_id'] = str(user['_id'])

                if has_risk_assessment(user['_id']):
                    return redirect(url_for('recommendations'))
                return redirect(url_for('questionnaire'))
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html', google_client_id=os.getenv('GOOGLE_CLIENT_ID'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')
            name = request.form.get('name')
            phone_number = request.form.get('phone_number')
            date_of_birth = request.form.get('date_of_birth')
            gender = request.form.get('gender')
            marital_status = request.form.get('marital_status')
            annual_income = request.form.get('annual_income')
            financial_literacy_level = request.form.get('financial_literacy_level')
            preferred_notification_method = request.form.get('preferred_notification_method')

            print(f"Processing signup for: {email}")
            print(f"Form data: {request.form}")
            if not all([email, password, name, phone_number, date_of_birth, gender, 
                       marital_status, annual_income, financial_literacy_level, 
                       preferred_notification_method]):
                return render_template('signup.html', 
                    error="All fields are required. Please fill in all information.")

            validator = recommendation_engine

            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                return render_template('signup.html', 
                    error="Please enter a valid email address.")

            if not validator._validate_password_strength(password):
                return render_template('signup.html', 
                    error="Password must be at least 8 characters and include uppercase, lowercase, number, and special character (@$!%*?&).")

            if not validator._validate_phone_number(phone_number):
                return render_template('signup.html', 
                    error="Please enter a valid phone number (10-15 digits, optionally starting with +).")

            if not validator._validate_age(date_of_birth):
                return render_template('signup.html', 
                    error="You must be at least 18 years old to register.")

            if financial_literacy_level not in ['Beginner', 'Intermediate', 'Advanced']:
                return render_template('signup.html', 
                    error="Please select a valid financial literacy level.")

            try:
                annual_income = float(annual_income)
                if annual_income <= 0:
                    raise ValueError
            except ValueError:
                return render_template('signup.html', 
                    error="Please enter a valid annual income.")

            user_data = {
                "email": email,
                "password": password,
                "name": name,
                "phone_number": phone_number,
                "date_of_birth": date_of_birth,
                "gender": gender,
                "marital_status": marital_status,
                "annual_income": annual_income,
                "financial_literacy_level": financial_literacy_level,
                "preferred_notification_method": preferred_notification_method
            }

            print("Attempting to create user...")
            user_id = validator.create_user(email, password, user_data)
            
            if user_id:
                print(f"User created successfully with ID: {user_id}")

                session.clear()
                session['username'] = email
                session['user_id'] = str(user_id)
                
                if has_risk_assessment(user_id):
                    return redirect(url_for('portfolio'))
                return redirect(url_for('questionnaire'))
            
            return render_template('signup.html', 
                error="Email already exists. Please use a different email or login.")

        except Exception as e:
            print(f"Error during signup: {e}")
            import traceback
            traceback.print_exc()
            return render_template('signup.html', 
                error=f"An error occurred during signup: {str(e)}")

    return render_template('signup.html')

@app.route('/questionnaire')
def questionnaire():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    if has_risk_assessment(user_id):
        return redirect(url_for('portfolio'))
        
    return render_template('questionnaire.html')

@app.route('/portfolio')
def portfolio():
    """Display user's investment portfolio"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']

    recommendations = get_user_recommendations(user_id)
    if not recommendations:
        risk_assessment = get_user_risk_assessment(user_id)
        recommendation_engine = RecommendationEngine()
        recommendations = recommendation_engine.get_recommendations(risk_assessment['profile'] if risk_assessment else 'Moderate')
    
    if 'market_sentiment' not in recommendations:
        recommendations['market_sentiment'] = {
            'score': 65, 
            'analysis': 'Current market conditions indicate moderate optimism with some caution advised.'
        }
    
    if 'news' not in recommendations:
        recommendations['news'] = []
    
    risk_profile = recommendations.get('risk_profile', 'Moderate')
    
    cache_buster = str(datetime.now().timestamp())
    
    return render_template('recommendations.html', 
                          recommendations=recommendations,
                          selected_profile=risk_profile,
                          cache_buster=cache_buster,
                          logout_url=url_for('logout'))

@app.route('/generate-question', methods=['POST'])
def generate_question():
    """Generate a risk assessment question."""
    try:
        data = request.get_json()
        current_question = data.get('current_question', 1)
        responses = data.get('responses', {})
        
        question_data = risk_assessor.generate_question(current_question, responses)

        if not isinstance(question_data, dict):
            return jsonify({'error': 'Invalid question data from risk assessor'})

        if 'question' not in question_data:
            if 'id' in question_data and 'text' in question_data and 'options' in question_data:
                question_data = {
                    'question': question_data,
                    'total_questions': question_data.get('total_questions', 10)
                }
            else:
                question_data = {
                    'question': {
                        'id': current_question,
                        'text': f'Question {current_question}',
                        'description': 'Please select the most appropriate answer.',
                        'options': [
                            {'value': '1', 'text': 'Option 1'},
                            {'value': '2', 'text': 'Option 2'},
                            {'value': '3', 'text': 'Option 3'},
                            {'value': '4', 'text': 'Option 4'}
                        ]
                    },
                    'total_questions': 10
                }
                
        app.logger.info(f"Question data being returned: {question_data}")
        
        return jsonify(question_data)
        
    except Exception as e:
        app.logger.error(f"Error generating question: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/api/assess-risk', methods=['POST'])
def assess_risk():
    user_id = session.get('user_id')
    responses = request.json.get('responses')
    
    if not user_id or not responses:
        return jsonify({'error': 'Missing user_id or responses'}), 400
    
    try:
        print(f"Assessing risk for user {user_id} with {len(responses)} responses")
        
        risk_profile = risk_assessor.assess_risk(user_id, responses)
        stored_profile = risk_assessor.get_risk_profile(user_id)
        
        print(f"Risk assessment complete: {stored_profile}")

        session['selected_risk_profile'] = stored_profile['profile']

        return jsonify({
            'risk_profile': stored_profile['profile'],
            'risk_score': stored_profile['score'],
            'detailed_responses': stored_profile['responses']
        })
        
    except Exception as e:
        print(f"Error in risk assessment: {e}")
        return jsonify({'error': 'An error occurred during risk assessment'}), 500

@app.route('/results')
def results():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('results.html')

@app.before_request
def check_recommendations_format():
    """Ensure all recommendation data has necessary fields to prevent template errors"""
    if 'user_id' in session:
        if 'cached_recommendations' in session:
            cached = session['cached_recommendations']
            if isinstance(cached, dict) and 'market_sentiment' not in cached:
                cached['market_sentiment'] = {
                    'score': 65, 
                    'analysis': 'Current market conditions indicate moderate optimism with some caution advised.'
                }
                session['cached_recommendations'] = cached

def get_recommendations_with_sentiment(risk_profile):
    """Wrapper to ensure recommendations always include market_sentiment"""
    engine = RecommendationEngine()
    recommendations = engine.get_recommendations(risk_profile)
    
    if 'market_sentiment' not in recommendations:
        recommendations['market_sentiment'] = {
            'score': 65, 
            'analysis': 'Current market conditions indicate moderate optimism with some caution advised.'
        }
    
    if 'news' not in recommendations:
        recommendations['news'] = []
        
    return recommendations

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def no_cache(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = make_response(f(*args, **kwargs))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    return decorated_function

@cache.memoize(timeout=300)
def get_cached_recommendations(user_id, risk_profile):
    """Get cached recommendations or generate new ones"""
    try:
        recommendations = get_user_recommendations(user_id)
        if not recommendations:
            engine = RecommendationEngine()
            recommendations = engine.get_recommendations(risk_profile)
            recommendations.update({
                'market_sentiment': {
                    'score': 65,
                    'analysis': 'Current market conditions indicate moderate optimism.'
                },
                'news': recommendations.get('news', []),
                'timestamp': datetime.now().isoformat(),
                'selected_profile': risk_profile
            })
            
            save_data = recommendations.copy()
            save_data["user_id"] = ObjectId(user_id)
            save_data["created_at"] = datetime.now()
            recommendations_collection.insert_one(save_data)
            
        return recommendations
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return None

@app.route('/recommendations', methods=['GET', 'POST'])
@login_required
@no_cache
def recommendations():
    """Generate and display investment recommendations"""
    user_id = session['user_id']

    if request.method == 'POST':
        raw_profile = request.form.get('risk_profile', '').strip().lower()
    else:
        risk_assessment = get_user_risk_assessment(user_id)
        raw_profile = (risk_assessment.get('profile') if risk_assessment 
                      else session.get('selected_risk_profile', 'moderate')).lower()

    risk_profile = {
        'aggressive': 'Aggressive',
        'conservative': 'Conservative'
    }.get(raw_profile, 'Moderate')
    
    session['selected_risk_profile'] = risk_profile
    cache_buster = str(datetime.now().timestamp())

    recommendations = get_cached_recommendations(user_id, risk_profile)
    if not recommendations:
        return render_template('error.html', 
                             message="Unable to generate recommendations. Please try again.")
    
    recommendations['cache_buster'] = cache_buster
    
    logger.info(f"Generated recommendations for user {user_id} with profile {risk_profile}")
    
    return render_template('recommendations.html',
                         recommendations=recommendations,
                         selected_profile=risk_profile,
                         cache_buster=cache_buster,
                         logout_url=url_for('logout'))

@app.route('/logout')
def logout():
    """Completely log out and clear all session data"""
    session.clear()
    response = make_response(redirect(url_for('index')))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/clear-cache')
def clear_cache():
    """Force clear cache and redirect to recommendations"""
    if 'cached_recommendations' in session:
        session.pop('cached_recommendations')
    if 'recommendation_timestamp' in session:
        session.pop('recommendation_timestamp')
    response = make_response(redirect(url_for('recommendations')))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

@app.route('/debug/risk-profile')
def debug_risk_profile():
    """Debug endpoint to check user's risk profile and recommendations"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
        
    user_id = session['user_id']

    risk_assessment = get_user_risk_assessment(user_id)

    raw_assessments = list(risk_assessments_collection.find({"user_id": ObjectId(user_id)}))
    for assessment in raw_assessments:
        assessment['_id'] = str(assessment['_id'])
        assessment['user_id'] = str(assessment['user_id'])

    recommendations = recommendation_engine.get_recommendations_with_news(risk_assessment)
    
    debug_info = {
        'user_id': user_id,
        'username': session.get('username'),
        'risk_assessment': risk_assessment,
        'raw_assessments_count': len(raw_assessments),
        'raw_assessments': raw_assessments,
        'recommendations': recommendations,
        'session_data': dict(session)
    }
    
    return jsonify(debug_info)

@app.route('/debug-template')
def debug_template():
    """Debug route to test template rendering"""
    sample_data = {
        'market_sentiment': {
            'score': 65,
            'analysis': 'This is a test sentiment analysis.'
        },
        'asset_allocation': {
            'Stocks': 60,
            'Bonds': 30,
            'Cash': 10
        },
        'investments': [
            {'symbol': 'VTI', 'name': 'Vanguard Total Stock Market ETF', 'type': 'ETF', 'risk_level': 'Moderate', 'allocation': 0.4}
        ],
        'news': [
            {'title': 'Test News', 'description': 'This is a test news item', 'source': 'Test Source', 'url': '#'}
        ]
    }
    
    print("Attempting to render recommendations.html template")
    try:
        return render_template('recommendations.html', 
                              recommendations=sample_data,
                              selected_profile="Test Profile",
                              cache_buster=str(time.time()))
    except Exception as e:
        print(f"Error rendering template: {e}")
        return f"<h1>Template Error</h1><p>{str(e)}</p><pre>{traceback.format_exc()}</pre>"

@app.route('/market-sentiment')
def market_sentiment():
    """Market sentiment analysis page."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    sentiment_data = {
        'score': 65,
        'summary': 'Market sentiment is moderately bullish with ongoing caution due to inflation concerns.',
        'last_updated': datetime.now().strftime('%B %d, %Y'),
        'volatility': {
            'value': 'Moderate',
            'trend': 3.2,
            'description': 'Market volatility has increased slightly over the past week but remains within normal ranges.'
        },
        'economic_outlook': {
            'value': 'Positive',
            'trend': 1.5,
            'description': 'Economic indicators suggest continued growth, though at a slightly reduced pace.'
        },
        'investor_sentiment': {
            'value': 'Cautious',
            'trend': -2.1,
            'description': 'Investor sentiment has declined slightly, with a more cautious approach to new positions.'
        },
        'technical_analysis': {
            'value': 'Bullish',
            'trend': 4.7,
            'description': 'Technical indicators suggest upward momentum in major indices.'
        }
    }
    
    return render_template('market_sentiment.html', sentiment_data=sentiment_data)

@app.route('/contact')
def contact():
    """Contact page."""
    return render_template('contact.html')

@app.route('/favicon.ico')
def favicon():
    """Serve the favicon."""
    favicon_options = [
        'favicon.jpeg',
        'favicon.ico',
        'bull.jpeg'
    ]
    
    for favicon_file in favicon_options:
        favicon_path = os.path.join(app.root_path, 'static', 'images', favicon_file)
        if os.path.exists(favicon_path):
            logger.info(f"Serving favicon from: {favicon_path}")
            return send_from_directory(
                os.path.join(app.root_path, 'static', 'images'),
                favicon_file
            )

    logger.warning("No favicon found, returning empty response")
    return "", 200, {'Content-Type': 'image/x-icon'}

@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f"Unhandled error: {error}")
    return render_template('error.html', 
                         message="An unexpected error occurred. Please try again."), 500

@app.route('/debug-question-api')
def debug_question_api():
    """Debug endpoint to check the generate-question API response format"""
    sample_request = {
        'current_question': 1,
        'responses': {}
    }

    from risk_assessment import RiskAssessor 
    assessor = RiskAssessor()
    question_data = assessor.generate_question(sample_request.get('current_question'), sample_request.get('responses'))

    return jsonify({
        'raw_response': question_data,
        'has_question_property': 'question' in question_data if isinstance(question_data, dict) else False,
        'response_type': str(type(question_data)),
        'suggested_format': {
            'question': {
                'id': 1,
                'text': 'Sample question text',
                'description': 'Optional description',
                'options': [
                    {'value': '1', 'text': 'Option 1', 'description': 'Option 1 description'},
                    {'value': '2', 'text': 'Option 2'}
                ]
            },
            'total_questions': 10
        }
    })

@app.route('/api/market-news')
def get_market_news():
    """API endpoint to fetch latest market news."""
    tickers = ["NVDA", "AMZN", "TSLA", "QQQ", "VWO", "VBK", "HYG"]

    try:
        from recommendation_engine import RecommendationEngine
        engine = RecommendationEngine()

        all_news = []
        
        for ticker in tickers:
            try:
                logger.info(f"Fetching news for {ticker}")

                ticker_news = engine.fetch_news(ticker)

                logger.info(f"Got {len(ticker_news) if ticker_news else 0} news items for {ticker}")
                
                if ticker_news:
                    for item in ticker_news:
                        if isinstance(item, dict):
                            item['ticker'] = ticker
                    
                    all_news.extend(ticker_news)
            except Exception as e:
                logger.warning(f"Error fetching news for {ticker}: {e}")

        if all_news and len(all_news) > 0:
            logger.info(f"Successfully retrieved {len(all_news)} news items from recommendation engine")
            return jsonify({"news": all_news})
            
    except Exception as e:
        logger.error(f"Error using recommendation engine for news: {str(e)}")
        logger.debug(traceback.format_exc())
    logger.warning("All news fetch methods failed, using hardcoded news")
    
    news_items = [
        {
            "title": "NVIDIA Reports Record Quarterly Revenue",
            "description": "NVIDIA announced record revenue for the quarter, driven by strong demand for AI chips and data center solutions.",
            "source": "Tech Daily",
            "url": "#",
            "ticker": "NVDA"
        },
        {
            "title": "Amazon Expands Global E-Commerce Operations",
            "description": "Amazon is expanding its global footprint with new fulfillment centers and delivery options in emerging markets.",
            "source": "Market Watch",
            "url": "#",
            "ticker": "AMZN"
        },
        {
            "title": "Tesla Unveils Next Generation Electric Vehicle",
            "description": "Tesla has revealed its latest electric vehicle model with extended range and advanced autonomous features.",
            "source": "Auto News",
            "url": "#",
            "ticker": "TSLA"
        },
        {
            "title": "QQQ ETF Reaches New High on Tech Performance",
            "description": "The Invesco QQQ Trust ETF has reached a new all-time high as technology stocks continue to outperform the broader market.",
            "source": "ETF Daily",
            "url": "#",
            "ticker": "QQQ"
        },
        {
            "title": "Emerging Markets Show Strong Potential for Growth",
            "description": "Economic forecasts indicate robust growth potential in emerging markets, with several regions outpacing developed economies.",
            "source": "Global Markets Today",
            "url": "#",
            "ticker": "VWO"
        },
        {
            "title": "Small-Cap Growth Stocks Outperform in Recent Rally",
            "description": "Small-cap growth companies have shown strong performance in the recent market rally, outpacing large-cap counterparts.",
            "source": "Small Cap Investor",
            "url": "#", 
            "ticker": "VBK"
        },
        {
            "title": "High Yield Bonds Show Resilience Amid Rate Concerns",
            "description": "The high-yield bond market has demonstrated resilience despite ongoing concerns about interest rate fluctuations.",
            "source": "Bond Market Review",
            "url": "#",
            "ticker": "HYG"
        }
    ]
    
    logger.info(f"Providing {len(news_items)} hardcoded news items")
    return jsonify({"news": news_items})

@app.route('/api/market-sentiment')
def get_market_sentiment_data():
    """API endpoint to fetch market sentiment data."""
    sentiment_data = {
        'score': 65,
        'summary': 'Market sentiment is moderately bullish with ongoing caution due to inflation concerns.',
        'last_updated': 'March 29, 2025',
        'volatility': {
            'value': 'Moderate',
            'trend': 3.2,
            'description': 'Market volatility has increased slightly over the past week but remains within normal ranges.'
        },
        'economic_outlook': {
            'value': 'Positive',
            'trend': 1.5,
            'description': 'Economic indicators suggest continued growth, though at a slightly reduced pace.'
        },
        'investor_sentiment': {
            'value': 'Cautious',
            'trend': -2.1,
            'description': 'Investor sentiment has declined slightly, with a more cautious approach to new positions.'
        }
    }
    return jsonify({"sentiment": sentiment_data})

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors gracefully."""
    logger.warning(f"404 error: {request.path} not found")
    if request.path.startswith('/static/'):
        if request.path.endswith(('.ico', '.jpeg', '.jpg', '.png', '.svg')):
            logger.info(f"Image not found: {request.path}")
            return send_from_directory(
                os.path.join(app.root_path, 'static'),
                'images/1px.png' if os.path.exists(os.path.join(app.root_path, 'static', 'images', '1px.png')) else 'favicon.ico'
            )
    
    return render_template('error.html', message="Page not found"), 404

if __name__ == '__main__':
    from werkzeug.debug import DebuggedApplication
    app.debug = True
    app.wsgi_app = DebuggedApplication(app.wsgi_app, True)
    app.run(use_reloader=False, threaded=False, port=5000) 