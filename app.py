from flask import Flask, render_template, request, jsonify, redirect, url_for, session
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
from datetime import datetime
import re
from bson.objectid import ObjectId

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.secret_key = os.urandom(24)  # Change this to a random secret key
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Initialize components
risk_assessor = RiskAssessor()
user_manager = UserManager()
recommendation_engine = RecommendationEngine()

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

            # Validate required fields
            if not all([email, password, name, phone_number, date_of_birth, gender, 
                       marital_status, annual_income, financial_literacy_level, 
                       preferred_notification_method]):
                return render_template('signup.html', 
                    error="All fields are required. Please fill in all information.")

            # Validate email format
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                return render_template('signup.html', 
                    error="Please enter a valid email address.")

            # Validate phone number format
            if not re.match(r"^\+?1?\d{9,15}$", phone_number):
                return render_template('signup.html', 
                    error="Please enter a valid phone number.")

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

            # Create or update user
            user_id = create_or_update_user(user_data)
            if user_id:
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
            return render_template('signup.html', 
                error="An error occurred during signup. Please try again.")

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
    
    risk_profile = risk_assessor.assess_risk(user_id, responses)
    stored_profile = risk_assessor.get_risk_profile(user_id)
    
    success = user_manager.update_risk_profile(user_id, risk_profile)
    
    return jsonify({
        'risk_profile': risk_profile,
        'risk_score': stored_profile['score'],
        'detailed_responses': stored_profile['responses']
    })

@app.route('/results')
def results():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('results.html')

@app.route('/recommendations')
def recommendations():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    risk_profile = user_manager.get_user_profile(user_id)
    
    if not risk_profile:
        return redirect(url_for('questionnaire'))
    
    recommendations = recommendation_engine.get_recommendations_with_news(risk_profile, user_id)
    
    return render_template('recommendations.html', recommendations=recommendations)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True) 
