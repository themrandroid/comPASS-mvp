"""
Firebase Initialization and Helper Functions

This module handles:
- Firebase Admin SDK initialization
- Firestore database connection
- Common database operations
- Connection health checks
"""

import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import streamlit as st


class FirebaseManager:
    """
    Singleton class to manage Firebase connection and operations.
    Ensures single initialization across Streamlit reruns.
    """
    
    _instance = None
    _db = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FirebaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Firebase connection if not already done."""
        if not FirebaseManager._initialized:
            self._initialize_firebase()
            FirebaseManager._initialized = True
    
    # def _initialize_firebase(self):
    #     """
    #     Initialize Firebase Admin SDK with service account credentials.
    #     Uses environment variable or Streamlit secrets for credentials path.
    #     """
    #     try:
    #         # Check if already initialized
    #         if not firebase_admin._apps:
    #             # Try to get credentials path from environment or Streamlit secrets
    #             creds_path = None
                
    #             # Method 1: From .env file (local development)
    #             if os.path.exists('.env'):
    #                 from dotenv import load_dotenv
    #                 load_dotenv()
    #                 creds_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
                
    #             # Method 2: From Streamlit / Hugging Face Secrets
    #             if not creds_path:
    #                 if "FIREBASE_CREDENTIALS" in st.secrets:
    #                     import json
    #                     firebase_dict = json.loads(st.secrets["FIREBASE_CREDENTIALS"])
    #                     cred = credentials.Certificate(firebase_dict)
    #                     firebase_admin.initialize_app(cred)
    #                     FirebaseManager._db = firestore.client()
    #                     return

                
    #             # Method 3: Direct file path (local development)
    #             if not creds_path:
    #                 creds_path = 'firebase-credentials.json'
                
    #             # Initialize with file
    #             if os.path.exists(creds_path):
    #                 cred = credentials.Certificate(creds_path)
    #                 firebase_admin.initialize_app(cred)
    #                 FirebaseManager._db = firestore.client()
    #             else:
    #                 raise FileNotFoundError(
    #                     f"Firebase credentials not found. Please configure either:\n"
    #                     f"1. Add firebase credentials to Streamlit secrets (for deployment)\n"
    #                     f"2. Set FIREBASE_CREDENTIALS_PATH in .env\n"
    #                     f"3. Place firebase-credentials.json in project root"
    #                 )
    #         else:
    #             # Already initialized, just get the client
    #             FirebaseManager._db = firestore.client()
                
    #     except Exception as e:
    #         st.error(f"Firebase initialization failed: {str(e)}")
    #         raise
    
    def _initialize_firebase(self):
        try:
            if not firebase_admin._apps:
                # 1. ENV VAR (Hugging Face)
                firebase_json = os.getenv("FIREBASE_CREDENTIALS")
                if firebase_json:
                    import json
                    cred = credentials.Certificate(json.loads(firebase_json))
                    firebase_admin.initialize_app(cred)
                    FirebaseManager._db = firestore.client()
                    return

                # 2. Local .env
                if os.path.exists(".env"):
                    from dotenv import load_dotenv
                    load_dotenv()
                    creds_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
                    if creds_path and os.path.exists(creds_path):
                        cred = credentials.Certificate(creds_path)
                        firebase_admin.initialize_app(cred)
                        FirebaseManager._db = firestore.client()
                        return

                # 3. Local JSON fallback
                if os.path.exists("firebase-credentials.json"):
                    cred = credentials.Certificate("firebase-credentials.json")
                    firebase_admin.initialize_app(cred)
                    FirebaseManager._db = firestore.client()
                    return

                raise FileNotFoundError("Firebase credentials not found")

            FirebaseManager._db = firestore.client()

        except Exception as e:
            raise RuntimeError(f"Firebase initialization failed: {e}")


    @property
    def db(self):
        """Get Firestore database client."""
        if FirebaseManager._db is None:
            self._initialize_firebase()
        return FirebaseManager._db
    
    def health_check(self) -> bool:
        """
        Verify Firebase connection is working.
        
        Returns:
            bool: True if connection is healthy
        """
        try:
            # Try to read from a test collection
            self.db.collection('_health_check').limit(1).get()
            return True
        except Exception as e:
            st.error(f"Firebase health check failed: {str(e)}")
            return False


# Initialize global Firebase manager
firebase_manager = FirebaseManager()


# ========================================
# TEACHER OPERATIONS
# ========================================

def create_teacher_profile(teacher_id: str, email: str) -> bool:
    """
    Create a teacher profile document in Firestore.
    
    Args:
        teacher_id: Firebase Auth UID
        email: Teacher's email address
    
    Returns:
        bool: True if successful
    """
    try:
        db = firebase_manager.db
        db.collection('teachers').document(teacher_id).set({
            'email': email,
            'created_at': firestore.SERVER_TIMESTAMP,
            'display_name': email.split('@')[0]  # Default display name
        })
        return True
    except Exception as e:
        st.error(f"Error creating teacher profile: {str(e)}")
        return False


def get_teacher_profile(teacher_id: str) -> Optional[Dict]:
    """
    Retrieve teacher profile from Firestore.
    
    Args:
        teacher_id: Firebase Auth UID
    
    Returns:
        dict: Teacher profile data or None if not found
    """
    try:
        db = firebase_manager.db
        doc = db.collection('teachers').document(teacher_id).get()
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        st.error(f"Error fetching teacher profile: {str(e)}")
        return None


# ========================================
# TEST OPERATIONS
# ========================================

def create_test(teacher_id: str, test_data: Dict) -> Optional[str]:
    """
    Create a new test document in Firestore.
    
    Args:
        teacher_id: Owner's Firebase Auth UID
        test_data: Dictionary containing test metadata
            Required keys: title, subject, duration, expiry_time, access_code, total_questions
    
    Returns:
        str: Test document ID if successful, None otherwise
    """
    try:
        db = firebase_manager.db
        
        # Add required fields
        test_data['teacher_id'] = teacher_id
        test_data['created_at'] = firestore.SERVER_TIMESTAMP
        test_data['status'] = 'active'
        
        # Create test document
        test_ref = db.collection('tests').document()
        test_ref.set(test_data)
        
        return test_ref.id
    except Exception as e:
        st.error(f"Error creating test: {str(e)}")
        return None


def get_tests_by_teacher(teacher_id: str) -> List[Dict]:
    """
    Retrieve all tests created by a specific teacher.
    
    Args:
        teacher_id: Firebase Auth UID
    
    Returns:
        list: List of test documents with their IDs
    """
    try:
        db = firebase_manager.db
        tests_ref = db.collection('tests').where('teacher_id', '==', teacher_id)
        tests = tests_ref.order_by('created_at', direction=firestore.Query.DESCENDING).stream()
        
        result = []
        for test in tests:
            test_data = test.to_dict()
            test_data['id'] = test.id
            result.append(test_data)
        
        return result
    except Exception as e:
        st.error(f"Error fetching tests: {str(e)}")
        return []


def get_test_by_id(test_id: str) -> Optional[Dict]:
    """
    Retrieve a specific test by ID.
    
    Args:
        test_id: Test document ID
    
    Returns:
        dict: Test data with ID or None if not found
    """
    try:
        db = firebase_manager.db
        doc = db.collection('tests').document(test_id).get()
        if doc.exists:
            test_data = doc.to_dict()
            test_data['id'] = doc.id
            return test_data
        return None
    except Exception as e:
        st.error(f"Error fetching test: {str(e)}")
        return None


def validate_access_code(test_id: str, access_code: str) -> bool:
    """
    Validate student access code for a test.
    
    Args:
        test_id: Test document ID
        access_code: Code provided by student
    
    Returns:
        bool: True if code is valid and test is active
    """
    try:
        test = get_test_by_id(test_id)
        if not test:
            return False
        
        # Check access code (case-insensitive)
        if test['access_code'].upper() != access_code.upper():
            return False
        
        # Check if test has expired (primary check)
        expiry_time = test.get('expiry_time')
        if isinstance(expiry_time, datetime):
            # Ensure timezone-aware comparison
            if expiry_time.tzinfo is None:
                expiry_time = expiry_time.replace(tzinfo=timezone.utc)
            
            if datetime.now(timezone.utc) > expiry_time:
                return False
        
        # Fallback: check stored status
        if test.get('status') == 'expired':
            return False
        
        return True
    except Exception as e:
        st.error(f"Error validating access code: {str(e)}")
        return False

# ========================================
# QUESTION OPERATIONS
# ========================================

def create_questions_batch(test_id: str, questions: List[Dict]) -> bool:
    """
    Create multiple questions for a test in a batch operation.
    
    Args:
        test_id: Parent test document ID
        questions: List of question dictionaries
    
    Returns:
        bool: True if all questions created successfully
    """
    try:
        db = firebase_manager.db
        batch = db.batch()
        
        for idx, question in enumerate(questions, start=1):
            question['test_id'] = test_id
            question['question_number'] = idx
            
            question_ref = db.collection('questions').document()
            batch.set(question_ref, question)
        
        batch.commit()
        return True
    except Exception as e:
        st.error(f"Error creating questions: {str(e)}")
        return False


def get_questions_by_test(test_id: str) -> List[Dict]:
    """
    Retrieve all questions for a specific test.
    
    Args:
        test_id: Test document ID
    
    Returns:
        list: List of question documents ordered by question_number
    """
    try:
        db = firebase_manager.db
        questions_ref = db.collection('questions').where('test_id', '==', test_id)
        questions = questions_ref.order_by('question_number').stream()
        
        result = []
        for question in questions:
            question_data = question.to_dict()
            question_data['id'] = question.id
            result.append(question_data)
        
        return result
    except Exception as e:
        st.error(f"Error fetching questions: {str(e)}")
        return []


# ========================================
# SUBMISSION OPERATIONS
# ========================================

def create_submission(submission_data: Dict) -> Optional[str]:
    """
    Create a new submission document.
    
    Args:
        submission_data: Dictionary containing submission details
            Required keys: test_id, student_name, answers, score, percentage, 
                          total_questions, time_taken
    
    Returns:
        str: Submission document ID if successful, None otherwise
    """
    try:
        db = firebase_manager.db
        
        submission_data['submitted_at'] = firestore.SERVER_TIMESTAMP
        
        submission_ref = db.collection('submissions').document()
        submission_ref.set(submission_data)
        
        return submission_ref.id
    except Exception as e:
        st.error(f"Error creating submission: {str(e)}")
        return None


def get_submissions_by_test(test_id: str) -> List[Dict]:
    """
    Retrieve all submissions for a specific test.
    
    Args:
        test_id: Test document ID
    
    Returns:
        list: List of submission documents with their IDs
    """
    try:
        db = firebase_manager.db
        submissions_ref = db.collection('submissions').where('test_id', '==', test_id)
        submissions = submissions_ref.order_by('submitted_at', direction=firestore.Query.DESCENDING).stream()
        
        result = []
        for submission in submissions:
            submission_data = submission.to_dict()
            submission_data['id'] = submission.id
            result.append(submission_data)
        
        return result
    except Exception as e:
        st.error(f"Error fetching submissions: {str(e)}")
        return []


def get_submission_count(test_id: str) -> int:
    """
    Get the number of submissions for a test.
    
    Args:
        test_id: Test document ID
    
    Returns:
        int: Number of submissions
    """
    try:
        db = firebase_manager.db
        submissions = db.collection('submissions').where('test_id', '==', test_id).stream()
        return sum(1 for _ in submissions)
    except Exception as e:
        st.error(f"Error counting submissions: {str(e)}")
        return 0