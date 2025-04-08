import hashlib
import uuid
import re
from datetime import datetime, timedelta
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
            existing_user = get_user_by_email(email)
            if existing_user:
                raise ValueError("Email already exists")

            if not self._validate_password_strength(password):
                raise ValueError("Password does not meet security requirements")

            if user_data and 'phone_number' in user_data:
                if not self._validate_phone_number(user_data['phone_number']):
                    raise ValueError("Invalid phone number format")

            if user_data and 'date_of_birth' in user_data:
                if not self._validate_age(user_data['date_of_birth']):
                    raise ValueError("User must be at least 18 years old")

            if user_data and 'financial_literacy_level' in user_data:
                if not self._validate_financial_literacy_level(user_data['financial_literacy_level']):
                    raise ValueError("Invalid financial literacy level")
            
            if user_data is None:
                user_data = {
                    "email": email,
                    "password": password
                }
            return create_or_update_user(user_data)
        except Exception as e:
            print(f"Error creating user: {e}")
            raise

    def _validate_password_strength(self, password):
        """OCL: PasswordStrength"""
        if len(password) < 8:
            return False
        if not re.search(r"[A-Z]", password):
            return False
        if not re.search(r"[a-z]", password):
            return False
        if not re.search(r"[0-9]", password):
            return False
        if not re.search(r"[@$!%*?&]", password):
            return False
        return True
        
    def _validate_phone_number(self, phone_number):
        """OCL: ValidPhoneNumber"""
        return bool(re.match(r'^\+?[0-9]{10,15}$', phone_number))
        
    def _validate_age(self, date_of_birth):
        """OCL: AgeRestriction"""
        try:
            dob = datetime.strptime(date_of_birth, '%Y-%m-%d')
            today = datetime.now()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            return age >= 18
        except:
            return False
            
    def _validate_financial_literacy_level(self, level):
        """OCL: ValidFinancialLiteracyLevel"""
        return level in ['Beginner', 'Intermediate', 'Advanced']

    def verify_user(self, email, password):
        return verify_user(email, password)

    def get_user_profile(self, user_id):
        assessment = get_user_risk_assessment(user_id)
        if assessment:
            return {
                'risk_tolerance': assessment.get('profile'),
                'investment_horizon': 'Medium', 
                'financial_goals': ['Retirement', 'Growth'], 
                'current_holdings': {}, 
                'risk_profile': assessment.get('profile'),
                'score': assessment.get('score')
            }
        return None

    def update_risk_profile(self, user_id, risk_profile):
        try:
            self._deactivate_previous_assessments(user_id)
            
            risk_score = self._calculate_risk_score(risk_profile)

            if not (0 <= risk_score <= 100):
                raise ValueError("Risk score must be between 0 and 100")

            expected_profile = self._get_expected_profile_for_score(risk_score)
            if expected_profile != risk_profile:
                risk_profile = expected_profile
            
            assessment_data = {
                'profile': risk_profile,
                'score': risk_score,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'active': True
            }
            return store_risk_assessment(user_id, assessment_data)
        except Exception as e:
            print(f"Error updating risk profile: {e}")
            return None
            
    def _deactivate_previous_assessments(self, user_id):
        """Implement OCL: SingleActiveAssessment"""
        pass

    def _calculate_risk_score(self, risk_profile):
        risk_scores = {
            'conservative': 20,
            'moderate_conservative': 40,
            'moderate': 60,
            'moderate_aggressive': 80,
            'aggressive': 100
        }
        return risk_scores.get(risk_profile, 50)
        
    def _get_expected_profile_for_score(self, score):
        """OCL: CorrectRiskProfileMapping"""
        if 0 <= score <= 20:
            return 'conservative'
        elif 21 <= score <= 40:
            return 'moderate_conservative'
        elif 41 <= score <= 60:
            return 'moderate'
        elif 61 <= score <= 80:
            return 'moderate_aggressive'
        else:
            return 'aggressive'

    def register_user(self, username, password, email):
        if self._email_exists(email):
            raise ValueError("Email already exists")

        if not self._validate_password_strength(password):
            raise ValueError("Password does not meet security requirements")

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

        return user_id
        
    def _email_exists(self, email):
        """Check if email already exists - OCL: UniqueEmail"""
        return get_user_by_email(email) is not None

    def authenticate_user(self, username, password):
        pass

    def _hash_password(self, password, salt):
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

    def update_profile(self, user_id, profile_data):
        pass