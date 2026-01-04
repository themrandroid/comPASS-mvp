"""
Test Submission Handler

This page handles:
- Final submission confirmation
- Answer grading
- Score calculation
- Saving submission to Firestore
- Redirecting to results page
"""

import streamlit as st
from datetime import datetime, timezone, timedelta
from utils.firebase import create_submission

# Page configuration
st.set_page_config(
    page_title="Submit Test - comPASS",
    page_icon="✅",
    layout="centered"
)

# ========================================
# CHECK TEST SESSION
# ========================================

if 'test_session' not in st.session_state:
    st.error("❌ No active test session")
    st.stop()

session = st.session_state.test_session

# Check if already submitted
if session.get('submitted', False):
    st.warning("⚠️ Test already submitted")
    st.info("Redirecting to results...")
    st.switch_page("pages/test_results.py")
    st.stop()

# ========================================
# SUBMISSION CONFIRMATION
# ========================================

questions = session['questions']
total_questions = len(questions)
answered_count = len(session['answers'])
unanswered_count = total_questions - answered_count

st.title("✅ Submit Test")
st.markdown(f"### {session['test_title']}")

st.markdown("")
st.markdown("")

# Show submission summary
st.markdown("### Submission Summary")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Questions", total_questions)

with col2:
    st.metric("Answered", answered_count)

with col3:
    st.metric("Unanswered", unanswered_count)

st.markdown("")
st.markdown("")

# Warning for unanswered questions
if unanswered_count > 0:
    st.warning(f"⚠️ You have {unanswered_count} unanswered question(s). These will be marked as incorrect.")

# Confirmation
st.markdown("### ⚠️ Final Confirmation")
st.markdown("""
**Please confirm:**
- You have answered all questions you want to answer
- You are ready to submit your test
- **You cannot change your answers after submission**
""")

confirm_submit = st.checkbox("I confirm that I want to submit this test", key="confirm_submit")

st.markdown("")
st.markdown("")

col1, col2 = st.columns(2)

with col1:
    if st.button("🔙 Back to Test", use_container_width=True):
        # Check if time remaining
        session = st.session_state.test_session
        start_time = session['start_time']
        duration_seconds = session['duration'] * 60
        end_time = start_time + timedelta(seconds=duration_seconds)
        time_remaining = (end_time - datetime.now(timezone.utc)).total_seconds()
        
        if time_remaining <= 0:
            st.error("⏰ Time expired. Cannot return to test.")
            st.caption("click the confirmation box and submit your test.")
            st.stop()
        
        st.switch_page("pages/exam_interface.py")

with col2:
    submit_final = st.button(
        "✅ Submit Final Answers",
        use_container_width=True,
        type="primary",
        disabled=not confirm_submit
    )

# ========================================
# PROCESS SUBMISSION
# ========================================

if submit_final and confirm_submit:
    with st.spinner("Grading your test..."):
        # Calculate score
        correct_count = 0
        topic_scores = {}  # topic -> {'correct': 0, 'total': 0}
        
        for question in questions:
            q_id = question['id']
            correct_option = question['correct_option']
            student_answer = session['answers'].get(q_id)
            
            # Topic tracking
            topic = question['topic']
            if topic not in topic_scores:
                topic_scores[topic] = {'correct': 0, 'total': 0}
            topic_scores[topic]['total'] += 1
            
            # Check if correct
            if student_answer and student_answer.upper() == correct_option.upper():
                correct_count += 1
                topic_scores[topic]['correct'] += 1
        
        # Calculate percentage
        percentage = (correct_count / total_questions) * 100 if total_questions > 0 else 0
        
        # Calculate time taken
        start_time = session['start_time']
        time_taken = int((datetime.now(timezone.utc) - start_time).total_seconds())
        
        # ✅ STORE time_taken in session BEFORE creating submission
        session['time_taken'] = time_taken
        session['score'] = correct_count
        session['percentage'] = percentage
        session['topic_scores'] = topic_scores
        
        # Prepare submission data
        submission_data = {
            'test_id': session['test_id'],
            'student_name': session['student_name'],
            'answers': session['answers'],
            'score': correct_count,
            'percentage': round(percentage, 2),
            'total_questions': total_questions,
            'time_taken': time_taken
        }
        
        # Save to Firestore
        submission_id = create_submission(submission_data)
        
        if submission_id:
            st.success("✅ Test submitted successfully!")
            
            # Store submission ID and mark as submitted
            session['submission_id'] = submission_id
            session['submitted'] = True
            
            st.balloons()
            st.info("Redirecting to your results...")
            
            # Redirect to results page
            st.switch_page("pages/test_results.py")
        else:
            st.error("❌ Failed to submit test. Please try again or contact your teacher.")
            if st.button("🔄 Retry Submission", use_container_width=True):
                st.rerun()

st.caption("comPASS v1.0 | Test Submission")