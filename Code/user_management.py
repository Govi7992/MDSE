import hashlib
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User:
    def __init__(self, username: str, password: str, email: str, name: str = None):
        self.username = username
        self.password = password
        self.email = email
        self.name = name
        
    def login(self) -> bool:
        """User login method"""
        # Implementation
        pass
        
    def signup(self) -> bool:
        """User signup method"""
        # Implementation
        pass
        
    def send_alert(self, message: str) -> bool:
        """Send alert to user"""
        try:
            # Implementation for sending alerts
            return True
        except Exception as e:
            print(f"Error sending alert: {e}")
            return False

class UserManager:
    def __init__(self):
        self.users = {}  # Dictionary to store user data
        self.sessions = {}  # Active sessions

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

    def create_user(self, email, password):
        """Create a new user with in-memory storage"""
        if email in self.users:
            return False
        
        user = User(username=email, password=password, email=email)
        self.users[email] = {
            'user': user,
            'password': password,
            'risk_profile': None
        }
        return True

    def verify_user(self, email, password):
        """Verify user credentials from in-memory storage"""
        user_data = self.users.get(email)
        if not user_data:
            return False
        return user_data['password'] == password

    def get_user_profile(self, user_id):
        if user_id in self.users:
            return self.users[user_id].get('risk_profile')
        return None

    def update_risk_profile(self, user_id, risk_profile):
        if user_id in self.users:
            self.users[user_id]['risk_profile'] = risk_profile
            return True
        return False
