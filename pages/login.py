"""
Teacher Login/Signup Page

This page handles:
- Teacher login with email/password
- New teacher signup
- Password reset (future enhancement)
- Redirect to dashboard on successful authentication
"""

import streamlit as st
from utils.auth import (
    init_session_state, 
    login_teacher, 
    signup_teacher, 
    is_authenticated
)

# Initialize session state
init_session_state()

# Page configuration
st.set_page_config(
    page_title="Teacher Login - comPASS",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Check if already logged in
if is_authenticated():
    st.success("✅ Already logged in!")
    st.info("Redirecting to dashboard...")
    st.switch_page("pages/dashboard.py")
    st.stop()

# Custom CSS for login page
st.markdown("""
<style>
    .main {
        padding: 2rem 1rem;
    }
    
    .login-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .login-card {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        padding: 0.75rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ========================================
# HEADER
# ========================================

st.markdown('<div class="login-header">', unsafe_allow_html=True)
st.title("Teacher Login")
st.caption("comPASS - Smart Test Analytics")
st.markdown('</div>', unsafe_allow_html=True)

# ========================================
# TAB INTERFACE: Login vs Signup
# ========================================

tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])

# ========================================
# LOGIN TAB
# ========================================

with tab1:
    st.markdown("### Welcome Back!")
    st.markdown("Log in to access your test analytics dashboard.")
    
    with st.form("login_form", clear_on_submit=False):
        email = st.text_input(
            "Email Address",
            placeholder="teacher@example.com",
            key="login_email"
        )
        
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            key="login_password"
        )
        
        # col1, col2 = st.columns([3, 1])
        
        # with col1:
        submit_login = st.form_submit_button(
            "🔓 Login",
            use_container_width=True,
            type="primary"
        )
        
        # with col2:
        #     forgot_password = st.form_submit_button(
        #         "Forgot?",
        #         use_container_width=True
        #     )
    
    # Handle login submission
    if submit_login:
        if not email or not password:
            st.error("❌ Please enter both email and password")
        else:
            with st.spinner("Authenticating..."):
                success, message = login_teacher(email, password)
                
                if success:
                    st.success(f"✅ {message}")
                    st.balloons()
                    st.info("Redirecting to dashboard...")
                    # Use st.rerun() to refresh and trigger redirect
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
    
    # Handle password reset
    # if forgot_password:
    #     if not email:
    #         st.warning("⚠️ Please enter your email address first")
    #     else:
    #         with st.spinner("Sending reset email..."):
    #             success, message = send_password_reset_email(email)
    #             if success:
    #                 st.success(f"✅ {message}")
    #             else:
    #                 st.info("💡 If you don't have FIREBASE_WEB_API_KEY set, contact admin for password reset")

# ========================================
# SIGNUP TAB
# ========================================

with tab2:
    st.markdown("### Create New Account")
    st.markdown("Join comPASS to start analyzing your test data.")
    
    with st.form("signup_form", clear_on_submit=True):
        new_email = st.text_input(
            "Email Address",
            placeholder="teacher@example.com",
            key="signup_email",
            help="Use a valid email address. This will be your login username."
        )
        
        new_password = st.text_input(
            "Password",
            type="password",
            placeholder="Minimum 6 characters",
            key="signup_password",
            help="Choose a strong password with at least 6 characters"
        )
        
        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="Re-enter your password",
            key="signup_confirm_password"
        )
        
        # Terms acceptance
        accept_terms = st.checkbox(
            "I agree to the terms of service and privacy policy",
            key="accept_terms"
        )
        
        submit_signup = st.form_submit_button(
            "📝 Create Account",
            use_container_width=True,
            type="primary"
        )
    
    # Handle signup submission
    if submit_signup:
        # Validation
        if not new_email or not new_password or not confirm_password:
            st.error("❌ Please fill in all fields")
        elif new_password != confirm_password:
            st.error("❌ Passwords do not match")
        elif len(new_password) < 6:
            st.error("❌ Password must be at least 6 characters")
        elif not accept_terms:
            st.error("❌ Please accept the terms of service")
        else:
            with st.spinner("Creating your account..."):
                success, message = signup_teacher(new_email, new_password)
                
                if success:
                    st.success(f"✅ {message}")
                    st.balloons()
                    st.info("👉 Please switch to the Login tab to sign in")
                else:
                    st.error(f"❌ {message}")

# ========================================
# FOOTER & HELP
# ========================================

st.markdown("")

with st.expander("ℹ️ Need Help?"):
    st.markdown("""
    **First time here?**
    1. Create an account using the Sign Up tab
    2. Use a valid email address
    3. Choose a strong password (minimum 6 characters)
    4. Log in and start creating tests!
    
    **Having issues?**
    - Ensure your email is correctly formatted
    - Check that passwords match during signup
    - Contact administrator if problems persist
    """)

with st.expander("🔒 Security & Privacy"):
    st.markdown("""
    **Your data is secure:**
    - All passwords are encrypted using Firebase Authentication
    - We never store passwords in plain text
    - Your email is only used for login and notifications
    - Test data is isolated per teacher account
    
    **Privacy:**
    - Student names are not stored as personal accounts
    - Only test responses are recorded
    - You control all data you create
    """)

st.markdown("")
st.caption("Built with ❤️ by Mr. Android for Nigerian tutorial centers | MVP v1.0")