import hashlib
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class UserManager:
    def __init__(self):
        self.users = {}  
        self.sessions = {}  

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
        if email not in self.users:
            self.users[email] = {
                'password': password,
                'risk_profile': None
            }
            return True
        return False

    def verify_user(self, email, password):
        return email in self.users and self.users[email]['password'] == password

    def get_user_profile(self, user_id):
        if user_id in self.users:
            return self.users[user_id].get('risk_profile')
        return None

    def update_risk_profile(self, user_id, risk_profile):
        if user_id in self.users:
            self.users[user_id]['risk_profile'] = risk_profile
            return True
        return False
