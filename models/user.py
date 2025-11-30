import os
from datetime import datetime, timedelta
import jwt
import bcrypt
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv('MONGODB_URI', 'mongodb+srv://susheelkrishnajabade_db_user:wa3MRtNS9RyOD9Oj@cluster-store.9dhlqbj.mongodb.net/?appName=Cluster-Store'))
db = client['healthmate']
users_collection = db['users']

class User:
    def __init__(self, username, password=None, _id=None):
        self.username = username
        self.password = password
        self._id = _id
    
    @staticmethod
    def create_user(username, password):
        """Create a new user with hashed password"""
        if users_collection.find_one({"username": username}):
            return None  # User already exists
        
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user_data = {
            "username": username,
            "password": hashed.decode('utf-8'),
            "created_at": datetime.utcnow()
        }
        
        result = users_collection.insert_one(user_data)
        return str(result.inserted_id)
    
    @staticmethod
    def authenticate(username, password):
        """Authenticate a user"""
        user = users_collection.find_one({"username": username})
        if not user:
            return None
        
        if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return str(user['_id'])
        return None
    
    @staticmethod
    def generate_token(user_id):
        """Generate JWT token"""
        payload = {
            'exp': datetime.utcnow() + timedelta(days=1),
            'iat': datetime.utcnow(),
            'sub': user_id
        }
        return jwt.encode(
            payload,
            os.getenv('JWT_SECRET', 'your-secret-key'),
            algorithm='HS256'
        )
    
    @staticmethod
    def verify_token(token):
        """Verify JWT token and return user_id if valid"""
        try:
            payload = jwt.decode(
                token,
                os.getenv('JWT_SECRET', 'your-secret-key'),
                algorithms=['HS256']
            )
            return payload['sub']
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
