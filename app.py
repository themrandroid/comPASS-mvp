"""
comPASS - Smart Test Analytics & Decision Support System
Main Application Entry Point

This file serves as the landing page and routing hub for the Streamlit application.
"""

import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="comPASS - Smart Test Analytics",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for mobile-first responsive design
st.markdown("""
<style>
    /* Mobile-first styling */
    .main {
        padding: 1rem;
    }
    
    /* Button styling */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }
    
    /* Card-like containers */
    .element-container {
        margin-bottom: 1rem;
    }
    
    /* Responsive text */
    h1 {
        font-size: 1.8rem;
    }
    
    @media (min-width: 768px) {
        h1 {
            font-size: 2.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

def main():
    """
    Main application landing page.
    
    Routes users to:
    - Teacher login/signup
    - Student test access
    """
    
    # st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)

    # Hero section
    import streamlit.components.v1 as components

    # components.html(
    # """
    # <div style="
    #     background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    #     border-radius: 18px;
    #     padding: 2.75rem 2rem;
    #     margin-bottom: 2.5rem;
    #     color: white;
    #     font-family: Inter, system-ui, sans-serif;
    # ">

    #     <div style="
    #         max-width: 720px;
    #         margin: auto;
    #         text-align: center;
    #     ">

    #         <span style="
    #             background: rgba(255,255,255,0.18);
    #             padding: 0.35rem 0.9rem;
    #             border-radius: 999px;
    #             font-size: 0.85rem;
    #             font-weight: 500;
    #             display: inline-block;
    #             margin-bottom: 2rem;">
    #             🧭 Smart Analytics Platform
    #         </span>

    #         <h1 style="
    #             margin: 0;
    #             font-size: 2rem;
    #             font-weight: 700;
    #             letter-spacing: -1px;">
    #             comPASS
    #         </h1>

    #         <p style="
    #             margin: 0.85rem auto 0;
    #             font-size: 1.25rem;
    #             opacity: 0.9;
    #             line-height: 1.5;">
                
    #         </p>

    #     </div>
    # </div>
    # """,
    # height=300,
    # )

    st.markdown(
        """
        <h1 style="
            text-align: center;
            background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
            -webkit-background-clip: text;
            font-size: 3.5em;
            font-weight: 800;
            text-shadow: 2px 2px 6px rgba(0,0,0,0.2);
            letter-spacing: -2px;
            margin-bottom: -4px;
        ">
            comPASS
        </h1>

        <p style="
            text-align: center;
            margin-bottom: 30px;
        ">
             🧭Your Smart Analytics Platform
        </p>
        """,
        unsafe_allow_html=True,
    )
    
    # Hero section

    st.markdown("""
    ### Welcome to comPASS
    
    **For Tutorial Centers, Schools, and Independent Tutors**
    
    Transform your test data into actionable insights with:
    - 📈 Real-time analytics dashboards
    - 🎯 Student risk classification
    - 🤖 AI-powered revision recommendations
    - 📄 Comprehensive performance reports
    
    Get immediate intelligence after a single test.
    """)
    
    # with col2:
    #     st.info("**Quick Stats**\n\n✅ Instant grading\n\n✅ Mobile-optimized\n\n✅ Zero setup friction")
    
    st.markdown("")
    
    # Role selection
    st.markdown("### Get Started")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 👨‍🏫 For Teachers")
        st.markdown("""
        Create tests, upload questions, and access powerful analytics dashboards.
        """)
        
        if st.button("🔐 Teacher Login / Signup", use_container_width=True):
            st.switch_page("pages/login.py")
    
    with col2:
        st.markdown("#### 👨‍🎓 For Students")
        st.markdown("""
        Take a test using your access code. No account needed.
        """)
        
        # Student test ID input
        student_test_id = st.text_input(
            "Enter Test ID or paste test link",
            placeholder="e.g., abc123xyz",
            help="Get this from your teacher",
            key="student_test_id_input"
        )
        
        if st.button("📝 Access Test", use_container_width=True):
            if student_test_id:
                test_id = (
                    student_test_id.split("id=")[-1].split("&")[0]
                    if "id=" in student_test_id
                    else student_test_id
                )

                # ✅ STORE in session_state (THIS is the key)
                st.session_state["active_test_id"] = test_id.strip()

                # Optional: still set query param for refresh/share
                st.query_params.clear()
                st.query_params["id"] = test_id.strip()

                st.switch_page("pages/take_test.py")
            else:
                st.warning("Please enter a test ID or link")
    
    st.markdown("")
    
    # Features overview
    with st.expander("📖 How It Works"):
        st.markdown("""
        **For Teachers:**
        1. Sign up and log in securely
        2. Create a new test with subject, duration, and access code
        3. Upload questions in CSV format
        4. Share the test link and access code with students
        5. Monitor submissions and view analytics
        6. Download comprehensive PDF reports
        
        **For Students:**
        1. Open the test link shared by your teacher
        2. Enter your name and access code
        3. Answer questions one at a time
        4. Submit and get immediate feedback
        5. View your weak topics and AI-generated advice
        """)
    
    with st.expander("🎯 Key Features"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Analytics Engine**
            - Topic-wise performance breakdown
            - Student risk scoring (High/Medium/Low)
            - Class readiness indicator
            """)
        
        with col2:
            st.markdown("""
            **AI Insights**
            - Natural language recommendations
            - Priority revision topics
            - Intervention strategies
            - Data-driven decision support
            """)
    
    # Footer
    st.markdown("")
    st.caption("Built with ❤️ by Mr. Android for Nigerian tutorial centers | MVP v1.0")

main()