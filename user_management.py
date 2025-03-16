import hashlib
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from database import (
    create_or_update_user, get_user_by_email, update_user_profile,
    verify_user, get_user_risk_assessment, store_risk_assessment
)

class User:
    def __init__(self, username: str, password: str, email: str, name: str = None):
        self.username = username
        self.password = password
        self.email = email
        self.name = name
        
    def login(self) -> bool:
        """User login method"""
        pass
        
    def signup(self) -> bool:
        """User signup method"""
        pass
        
    def send_alert(self, message: str) -> bool:
        """Send alert to user"""
        try:
            return True
        except Exception as e:
            print(f"Error sending alert: {e}")
            return False

class UserManager:
    def __init__(self):
        pass

    def create_user(self, email, password, user_data=None):
        try:
            if user_data is None:
                user_data = {
                    "email": email,
                    "password": password
                }
            return create_or_update_user(user_data)
        except Exception as e:
            print(f"Error creating user: {e}")
            return None

    def verify_user(self, email, password):
        return verify_user(email, password)

    def get_user_profile(self, user_id):
        assessment = get_user_risk_assessment(user_id)
        if assessment:
            return {
                'risk_profile': assessment.get('profile'),
                'score': assessment.get('score')
            }
        return None

    def update_risk_profile(self, user_id, risk_profile):
        try:
            assessment_data = {
                'profile': risk_profile,
                'score': self._calculate_risk_score(risk_profile)
            }
            return store_risk_assessment(user_id, assessment_data)
        except Exception as e:
            print(f"Error updating risk profile: {e}")
            return None

    def _calculate_risk_score(self, risk_profile):
        risk_scores = {
            'conservative': 20,
            'moderate_conservative': 40,
            'moderate': 60,
            'moderate_aggressive': 80,
            'aggressive': 100
        }
        return risk_scores.get(risk_profile, 50)

    def register_user(self, username, password, email):
        if username in self.users:
            raise ValueError("Username already exists")

        user_id = str(uuid.uuid4())
        salt = uuid.uuid4().hex
        hashed_password = self._hash_password(password, salt)

        user = {
            'user_id': user_id,
            'username': username,
            'password': hashed_password,
            'salt': salt,
            'email': email,
            'created_at': datetime.now(),
            'profile': {}
        }

        self.users[username] = user
        return user_id

    def authenticate_user(self, username, password):
        if username not in self.users:
            return False

        user = self.users[username]
        hashed_password = self._hash_password(password, user['salt'])
        return hashed_password == user['password']

    def _hash_password(self, password, salt):
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

    def update_profile(self, user_id, profile_data):
        for user in self.users.values():
            if user['user_id'] == user_id:
                user['profile'].update(profile_data)
                return True
        return False
