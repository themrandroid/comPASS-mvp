"""
Authentication Module

This module handles:
- Teacher signup and login using Firebase Auth
- Session management with Streamlit
- Authentication state validation
- Logout functionality
"""

import streamlit as st
from firebase_admin import auth
from utils.firebase import create_teacher_profile, get_teacher_profile
from typing import Optional, Dict, Tuple


# ========================================
# SESSION STATE MANAGEMENT
# ========================================

def init_session_state():
    """
    Initialize authentication-related session state variables.
    Called at the start of the app.
    """
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    
    if 'user_profile' not in st.session_state:
        st.session_state.user_profile = None


def is_authenticated() -> bool:
    """
    Check if user is currently authenticated.
    
    Returns:
        bool: True if user is logged in
    """
    return st.session_state.get('authenticated', False)


def get_current_user_id() -> Optional[str]:
    """
    Get the currently authenticated user's ID.
    
    Returns:
        str: User ID (Firebase Auth UID) or None
    """
    return st.session_state.get('user_id')


def get_current_user_email() -> Optional[str]:
    """
    Get the currently authenticated user's email.
    
    Returns:
        str: User email or None
    """
    return st.session_state.get('user_email')


# ========================================
# AUTHENTICATION OPERATIONS
# ========================================

def signup_teacher(email: str, password: str) -> Tuple[bool, str]:
    """
    Create a new teacher account using Firebase Auth.
    
    Args:
        email: Teacher's email address
        password: Password (minimum 6 characters)
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Input validation
        if not email or not password:
            return False, "Email and password are required"
        
        if len(password) < 6:
            return False, "Password must be at least 6 characters"
        
        # Create user in Firebase Auth
        user = auth.create_user(
            email=email,
            password=password,
            email_verified=False
        )
        
        # Create teacher profile in Firestore
        profile_created = create_teacher_profile(user.uid, email)
        
        if not profile_created:
            # Rollback: delete the auth user if profile creation fails
            auth.delete_user(user.uid)
            return False, "Failed to create teacher profile"
        
        return True, "Account created successfully!"
    
    except auth.EmailAlreadyExistsError:
        return False, "An account with this email already exists"
    
    except Exception as e:
        return False, f"Signup failed: {str(e):.32}"


def login_teacher(email: str, password: str) -> Tuple[bool, str]:
    """
    Authenticate a teacher using email and password.
    
    Note: Firebase Admin SDK doesn't directly support password verification.
    In production, you would use Firebase Client SDK or REST API.
    For MVP, we're using a simplified approach with Auth REST API.
    
    Args:
        email: Teacher's email
        password: Teacher's password
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # Input validation
        if not email or not password:
            return False, "Email and password are required"
        
        # Use Firebase Auth REST API for password verification
        import requests
        import os
        
        # Get Firebase Web API Key from environment or Streamlit secrets
        api_key = os.getenv('FIREBASE_WEB_API_KEY')
        
        # Try Streamlit secrets if env var not found
        if not api_key and hasattr(st, 'secrets'):
            try:
                api_key = st.secrets.get('FIREBASE_WEB_API_KEY')
            except Exception:
                pass
        
        if not api_key:
            # For development, try to get from Firebase project
            # In production, set this in Streamlit secrets
            st.warning("FIREBASE_WEB_API_KEY not set. Using simplified auth for development.")
            # Simplified approach: just check if user exists
            user = auth.get_user_by_email(email)
            
            # Update session state
            st.session_state.authenticated = True
            st.session_state.user_id = user.uid
            st.session_state.user_email = email
            
            # Load user profile
            profile = get_teacher_profile(user.uid)
            st.session_state.user_profile = profile
            
            return True, "Login successful!"
        
        # Production approach: verify with REST API
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            user_id = data['localId']
            
            # Update session state
            st.session_state.authenticated = True
            st.session_state.user_id = user_id
            st.session_state.user_email = email
            
            # Load user profile
            profile = get_teacher_profile(user_id)
            st.session_state.user_profile = profile
            
            return True, "Login successful!"
        else:
            error_data = response.json()
            error_message = error_data.get('error', {}).get('message', 'Unknown error')
            
            if 'INVALID_PASSWORD' in error_message:
                return False, "Invalid email or password"
            elif 'EMAIL_NOT_FOUND' in error_message:
                return False, "No account found with this email"
            else:
                return False, f"Login failed: {error_message}"
    
    except auth.UserNotFoundError:
        return False, "No account found with this email"
    
    except Exception as e:
        return False, f"Login failed: {str(e):.15}"


def logout_teacher():
    """
    Log out the current teacher by clearing session state.
    """
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.user_email = None
    st.session_state.user_profile = None
    
    # Clear any other session data
    for key in list(st.session_state.keys()):
        if key not in ['authenticated', 'user_id', 'user_email', 'user_profile']:
            del st.session_state[key]


# ========================================
# ROUTE PROTECTION
# ========================================

def require_authentication():
    """
    Decorator-like function to protect routes.
    Call this at the start of authenticated pages.
    Redirects to login if not authenticated.
    """
    init_session_state()
    
    if not is_authenticated():
        st.warning("⚠️ Please log in to access this page")
        st.info("Redirecting to login page...")
        st.switch_page("pages/login.py")
        st.stop()


# ========================================
# PASSWORD RESET
# ========================================

def send_password_reset_email(email: str) -> Tuple[bool, str]:
    """
    Send password reset email to user.
    
    Note: This requires Firebase Client SDK or REST API.
    For MVP, we'll use the REST API approach.
    
    Args:
        email: User's email address
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        import requests
        import os
        
        api_key = os.getenv('FIREBASE_WEB_API_KEY')
        
        # Try Streamlit secrets if env var not found
        if not api_key and hasattr(st, 'secrets'):
            try:
                api_key = st.secrets.get('FIREBASE_WEB_API_KEY')
            except Exception:
                pass
        
        if not api_key:
            return False, "Password reset not configured. Please contact admin."
        
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={api_key}"
        payload = {
            "requestType": "PASSWORD_RESET",
            "email": email
        }
        
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            return True, "Password reset email sent! Check your inbox."
        else:
            return False, "Failed to send reset email. Please check your email address."
    
    except Exception as e:
        return False, f"Error: {str(e)}"


# ========================================
# HELPER FUNCTIONS
# ========================================

def get_user_display_name() -> str:
    """
    Get a friendly display name for the current user.
    
    Returns:
        str: Display name or email prefix
    """
    if st.session_state.user_profile:
        return st.session_state.user_profile.get('display_name', 'Teacher')
    elif st.session_state.user_email:
        return st.session_state.user_email.split('@')[0]
    return 'Teacher'