from flask import Blueprint, request, jsonify, make_response
from models.user import User
from functools import wraps

# Create auth blueprint
auth_bp = Blueprint('auth', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check if token is in the headers
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]  # Bearer <token>
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
            
        user_id = User.verify_token(token)
        if not user_id:
            return jsonify({'message': 'Token is invalid or expired!'}), 401
            
        return f(user_id, *args, **kwargs)
    
    return decorated

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password are required!'}), 400
    
    user_id = User.create_user(data['username'], data['password'])
    
    if not user_id:
        return jsonify({'message': 'Username already exists!'}), 400
    
    # Generate token
    token = User.generate_token(user_id)
    
    response = make_response(jsonify({
        'message': 'User registered successfully',
        'user_id': user_id
    }), 201)
    
    # Set HTTP-only cookie
    response.set_cookie(
        'auth_token',
        value=token,
        httponly=True,
        secure=True,  # In production, set this to True for HTTPS
        samesite='Lax'
    )
    
    return response

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password are required!'}), 400
    
    user_id = User.authenticate(data['username'], data['password'])
    
    if not user_id:
        return jsonify({'message': 'Invalid username or password!'}), 401
    
    # Generate token
    token = User.generate_token(user_id)
    
    response = make_response(jsonify({
        'message': 'Login successful',
        'user_id': user_id
    }))
    
    # Set HTTP-only cookie
    response.set_cookie(
        'auth_token',
        value=token,
        httponly=True,
        secure=True,  # In production, set this to True for HTTPS
        samesite='Lax'
    )
    
    return response

@auth_bp.route('/check_auth', methods=['GET'])
@token_required
def check_auth(user_id):
    return jsonify({
        'message': 'User is authenticated',
        'user_id': user_id
    })

@auth_bp.route('/logout', methods=['POST'])
def logout():
    response = make_response(jsonify({'message': 'Successfully logged out'}))
    response.delete_cookie('auth_token')
    return response
