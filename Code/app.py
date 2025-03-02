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
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.is_json:
            # Handle Google Sign-In
            token = request.json.get('token')
            try:
                idinfo = id_token.verify_oauth2_token(
                    token,
                    requests.Request(),
                    os.getenv('GOOGLE_CLIENT_ID')
                )
                email = idinfo['email']
                if email not in user_manager.users:
                    user_manager.create_user(email, 'google_auth')
                session['username'] = email
                return jsonify({'success': True})
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
        else:
            # Handle regular login
            email = request.form.get('email')
            password = request.form.get('password')
            if user_manager.verify_user(email, password):
                session['username'] = email
                return redirect(url_for('questionnaire'))
            return render_template('login.html', error="Invalid credentials")
    
    # For GET requests, render the login page with Google client ID
    return render_template('login.html', google_client_id=os.getenv('GOOGLE_CLIENT_ID'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if user_manager.create_user(email, password):
            session['username'] = email
            return redirect(url_for('questionnaire'))
        return render_template('signup.html', error="Email already exists")
    return render_template('signup.html')

@app.route('/questionnaire')
def questionnaire():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('questionnaire.html')

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
    user_id = session.get('username', 'guest')
    responses = request.json.get('responses')
    
    if not user_id or not responses:
        return jsonify({'error': 'Missing user_id or responses'}), 400
    
    risk_profile = risk_assessor.assess_risk(user_id, responses)
    stored_profile = risk_assessor.get_risk_profile(user_id)
    
    # Update user's risk profile
    success = user_manager.update_risk_profile(user_id, risk_profile)
    print(f"Updated risk profile for {user_id}: {risk_profile}, Success: {success}")
    
    return jsonify({
        'risk_profile': risk_profile,
        'risk_score': stored_profile['score'],
        'detailed_responses': stored_profile['responses']
    })

@app.route('/results')
def results():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('results.html')

@app.route('/recommendations')
def recommendations():
    if 'username' not in session:
        print("User not logged in, redirecting to login.")
        return redirect(url_for('login'))
    
    user_id = session['username']
    print(f"Checking risk profile for user: {user_id}")
    print(f"All users: {user_manager.users}")  # Debug line
    
    risk_profile = user_manager.get_user_profile(user_id)
    print(f"Retrieved risk profile: {risk_profile}")
    
    if not risk_profile:
        print("No risk profile found, redirecting to questionnaire.")
        return redirect(url_for('questionnaire'))
    
    print(f"User ID: {user_id}, Risk Profile: {risk_profile}")
    
    recommendations = recommendation_engine.get_recommendations_with_news(risk_profile)
    print(f"Recommendations: {recommendations}")
    
    return render_template('recommendations.html', recommendations=recommendations)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True) 
