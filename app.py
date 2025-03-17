from flask import Flask, render_template, request, jsonify, redirect, url_for, session, make_response, send_from_directory
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
    risk_assessments_collection, recommendations_collection
)
from datetime import datetime, timedelta
import re
from bson.objectid import ObjectId
import platform

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for all routes
app.secret_key = os.urandom(24)  # Change this to a random secret key
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Disable Flask's template caching
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Add a before_request handler to control caching
@app.before_request
def before_request():
    # Clear cache for dynamic pages
    if not request.path.startswith('/static/'):
        response = make_response()
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

# Initialize components
risk_assessor = RiskAssessor()
user_manager = UserManager()
recommendation_engine = RecommendationEngine()

# Add at the top of app.py
if platform.system().lower() == 'windows':
    # Fix socket handling on Windows
    import socket
    
    # Monkey patch socket.socket to handle socket cleanup better
    old_socket = socket.socket
    def new_socket(*args, **kwargs):
        s = old_socket(*args, **kwargs)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s
    socket.socket = new_socket

@app.route('/')
def index():
    # Clear any existing session data
    session.clear()
    return render_template('index.html')

@app.route('/retake-assessment')
def retake_assessment():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Clear the risk assessment data but keep user session
    user_id = session['user_id']
    risk_assessments_collection.delete_many({"user_id": ObjectId(user_id)})
    recommendations_collection.delete_many({"user_id": ObjectId(user_id)})
    
    return redirect(url_for('questionnaire'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Clear any existing recommendations at the start of login
    if 'user_id' in session:
        try:
            # Clear old recommendations from database
            user_id = session['user_id']
            recommendations_collection.delete_many({"user_id": ObjectId(user_id)})
            
            # Clear all recommendation-related session data
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

                # Clear any existing session data
                session.clear()
                session['username'] = email
                session['user_id'] = str(user_id)

                if has_risk_assessment(user_id):
                    return redirect(url_for('portfolio'))
                return redirect(url_for('questionnaire'))

            except ValueError as e:
                return jsonify({'error': str(e)}), 400
        else:
            email = request.form.get('email')
            password = request.form.get('password')
            if user_manager.verify_user(email, password):
                user = get_user_by_email(email)
                # Clear any existing session data
                session.clear()
                session['username'] = email
                session['user_id'] = str(user['_id'])

                if has_risk_assessment(user['_id']):
                    return redirect(url_for('portfolio'))
                return redirect(url_for('questionnaire'))
            return render_template('login.html', error="Invalid credentials")
    
    # For GET requests, render the login page with Google client ID
    return render_template('login.html', google_client_id=os.getenv('GOOGLE_CLIENT_ID'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            # Get all required fields
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

            # Validate required fields
            if not all([email, password, name, phone_number, date_of_birth, gender, 
                       marital_status, annual_income, financial_literacy_level, 
                       preferred_notification_method]):
                return render_template('signup.html', 
                    error="All fields are required. Please fill in all information.")

            # Create validator instance
            validator = recommendation_engine

            # Validate email format
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                return render_template('signup.html', 
                    error="Please enter a valid email address.")

            # Validate password strength
            if not validator._validate_password_strength(password):
                return render_template('signup.html', 
                    error="Password must be at least 8 characters and include uppercase, lowercase, number, and special character (@$!%*?&).")

            # Validate phone number format
            if not validator._validate_phone_number(phone_number):
                return render_template('signup.html', 
                    error="Please enter a valid phone number (10-15 digits, optionally starting with +).")

            # Validate age
            if not validator._validate_age(date_of_birth):
                return render_template('signup.html', 
                    error="You must be at least 18 years old to register.")

            # Validate financial literacy level
            if financial_literacy_level not in ['Beginner', 'Intermediate', 'Advanced']:
                return render_template('signup.html', 
                    error="Please select a valid financial literacy level.")

            # Validate annual income
            try:
                annual_income = float(annual_income)
                if annual_income <= 0:
                    raise ValueError
            except ValueError:
                return render_template('signup.html', 
                    error="Please enter a valid annual income.")

            # Create user data dictionary
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

            # Create or update user using the validator's create_user method
            print("Attempting to create user...")
            user_id = validator.create_user(email, password, user_data)
            
            if user_id:
                print(f"User created successfully with ID: {user_id}")
                # Clear any existing session data
                session.clear()
                session['username'] = email
                session['user_id'] = str(user_id)
                
                # Check if user already has risk assessment
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
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    if not has_risk_assessment(user_id):
        return redirect(url_for('questionnaire'))
    
    recommendations = get_user_recommendations(user_id)
    if not recommendations:
        risk_profile = user_manager.get_user_profile(user_id)
        recommendations = recommendation_engine.get_recommendations_with_news(risk_profile, user_id)
    
    return render_template('recommendations.html', recommendations=recommendations)

@app.route('/generate-question', methods=['POST'])
def generate_question():
    try:
        previous_responses = request.json.get('previous_responses', {})
        question = risk_assessor.generate_question(previous_responses)
        return jsonify({'question': question})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/assess-risk', methods=['POST'])
def assess_risk():
    user_id = session.get('user_id')
    responses = request.json.get('responses')
    
    if not user_id or not responses:
        return jsonify({'error': 'Missing user_id or responses'}), 400
    
    try:
        # OCL: MinimumResponses
        if len(responses) < 3:
            return jsonify({'error': 'A minimum of 3 responses is required'}), 400
        
        # Execute risk assessment with OCL constraints
        risk_profile = risk_assessor.assess_risk(user_id, responses)
        stored_profile = risk_assessor.get_risk_profile(user_id)
        
        # Update user profile
        success = user_manager.update_risk_profile(user_id, risk_profile)
        
        # OCL: CorrectRiskProfileMapping - Verify the mapping is correct
        risk_score = stored_profile['score']
        expected_profile = None
        
        if 0 <= risk_score <= 20:
            expected_profile = 'conservative'
        elif 21 <= risk_score <= 40:
            expected_profile = 'moderate_conservative'
        elif 41 <= risk_score <= 60:
            expected_profile = 'moderate'
        elif 61 <= risk_score <= 80:
            expected_profile = 'moderate_aggressive'
        else:  # 81-100
            expected_profile = 'aggressive'
            
        if stored_profile['profile'] != expected_profile:
            print(f"Warning: Risk profile mismatch. Expected {expected_profile}, got {stored_profile['profile']}")
            # Correct the profile
            risk_assessor.store_risk_assessment(user_id, {
                'profile': expected_profile,
                'score': risk_score,
                'responses': responses
            })
            stored_profile['profile'] = expected_profile
        
        return jsonify({
            'risk_profile': stored_profile['profile'],
            'risk_score': stored_profile['score'],
            'detailed_responses': stored_profile['responses']
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error in risk assessment: {e}")
        return jsonify({'error': 'An error occurred during risk assessment'}), 500

@app.route('/results')
def results():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('results.html')

@app.route('/recommendations', methods=['GET', 'POST'])
def recommendations():
    """Generate and display investment recommendations"""
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user information
    user_id = session['user_id']
    
    # FORCE DELETE existing recommendations in database
    try:
        recommendations_collection.delete_many({"user_id": ObjectId(user_id)})
    except Exception as e:
        print(f"Error deleting old recommendations: {e}")
    
    # Clear all cached data
    session_keys = list(session.keys())  # Create a copy of keys to avoid modification during iteration
    for key in session_keys:
        if key not in ['user_id', 'username']:  # Keep only essential user data
            session.pop(key, None)
    
    # Generate fresh cache buster
    cache_buster = str(datetime.now().timestamp())
    session['cache_buster'] = cache_buster
    
    # Get risk profile selection
    valid_profiles = {'Conservative', 'Moderate', 'Aggressive'}
    
    if request.method == 'POST':
        risk_profile = request.form.get('risk_profile', 'Moderate')
        if risk_profile not in valid_profiles:
            risk_profile = 'Moderate'
        session['selected_risk_profile'] = risk_profile
    else:
        risk_profile = session.get('selected_risk_profile', 'Moderate')
        if risk_profile not in valid_profiles:
            risk_profile = 'Moderate'
    
    # Always generate fresh recommendations
    engine = RecommendationEngine()
    recommendations = engine.get_recommendations(risk_profile)
    
    # Add timestamp for cache busting
    recommendations['timestamp'] = datetime.now().isoformat()
    recommendations['cache_buster'] = cache_buster
    
    # Debug output
    print(f"Generated NEW recommendations for profile: {risk_profile}")
    print(f"Asset allocation: {recommendations.get('asset_allocation', {})}")
    print(f"Number of investments: {len(recommendations.get('investments', []))}")
    print(f"Cache buster: {cache_buster}")
    
    # Create response with enhanced cache prevention
    response = make_response(render_template('recommendation_display.html', 
                          recommendations=recommendations,
                          selected_profile=risk_profile,
                          cache_buster=cache_buster))
                          
    # Set aggressive cache prevention headers
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['X-Cache-Buster'] = cache_buster
    
    # Save to database with cache buster
    try:
        # First, remove all existing recommendations for this user
        recommendations_collection.delete_many({"user_id": ObjectId(user_id)})
        
        # Store new recommendations with cache buster
        save_data = recommendations.copy()
        save_data["user_id"] = ObjectId(user_id)
        save_data["created_at"] = datetime.now()
        save_data["cache_buster"] = cache_buster
        recommendations_collection.insert_one(save_data)
    except Exception as e:
        print(f"Error saving recommendations: {e}")
    
    return response

@app.route('/logout')
def logout():
    """Completely log out and clear all session data"""
    # Clear all session data
    session.clear()
    
    # Return with cache-clearing headers
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
    # Clear session data related to recommendations
    if 'cached_recommendations' in session:
        session.pop('cached_recommendations')
    if 'recommendation_timestamp' in session:
        session.pop('recommendation_timestamp')
    
    # Create a response that forces cache clearing
    response = make_response(redirect(url_for('recommendations')))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

if __name__ == '__main__':
    # Set up explicit debugger configuration
    from werkzeug.debug import DebuggedApplication
    
    # Configure debug application
    app.debug = True
    app.wsgi_app = DebuggedApplication(app.wsgi_app, True)
    
    # Run with settings that avoid socket errors
    app.run(use_reloader=False, threaded=False, port=5000) 
