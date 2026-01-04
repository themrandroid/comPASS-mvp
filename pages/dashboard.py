"""
Analytics Dashboard Page

Displays comprehensive test analytics with visualizations:
- Topic performance heatmap
- Student risk classification table
- Class readiness indicator
- AI-generated insights
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime, timezone
import plotly.express as px
import plotly.graph_objects as go
from utils.auth import require_authentication, get_current_user_id
from utils.firebase import get_tests_by_teacher, get_test_by_id, get_submissions_by_test, get_questions_by_test
from utils.analytics import generate_comprehensive_analytics
from utils.ai_insights import get_quick_insights

# Protect this page
require_authentication()

# Page configuration
st.set_page_config(
    page_title="Analytics Dashboard - comPASS",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS
st.markdown("""
<style>

/* =======================
   GRID LAYOUT
======================= */
.risk-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin: 1.5rem 0;
}

/* =======================
   BASE METRIC CARD
======================= */
.metric-card {
    background: white;
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    border-left: 5px solid transparent;
}

/* =======================
   COMPACT GRID CARD
======================= */
.metric-card.compact {
    text-align: center;
}

.metric-card.compact h4 {
    margin-bottom: 0.5rem;
    font-size: 1rem;
}

.metric-card.compact h3 {
    font-size: 2rem;
    margin: 0.25rem 0;
}

.metric-card.compact p {
    font-size: 0.9rem;
    color: #555;
}

/* =======================
   DETAILED STATUS CARD
======================= */
.metric-card.detailed {
    text-align: left;
    margin-bottom: 1.5rem;
    border-left-color: var(--border-color);
}

.metric-card.detailed h2 {
    margin-bottom: 1rem;
}

.metric-card.detailed p {
    line-height: 1.6;
}

/* =======================
   RECOMMENDATION BOX
======================= */
.recommendation {
    background: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    margin-top: 1rem;
}

/* =======================
   RISK COLORS
======================= */
.high-risk {
    background: #f8d7da;
    border-left-color: #dc3545;
}

.medium-risk {
    background: #fff3cd;
    border-left-color: #ffc107;
}

.low-risk {
    background: #d4edda;
    border-left-color: #28a745;
}

/* =======================
   RESPONSIVE
======================= */
@media (max-width: 768px) {
    .risk-grid {
        grid-template-columns: 1fr;
    }
}

</style>
""", unsafe_allow_html=True)

# ========================================
# HEADER
# ========================================

st.title("📊 Analytics Dashboard")
st.markdown("Comprehensive test performance analytics.")

st.markdown("")
st.markdown("")

# ========================================
# TEST SELECTION
# ========================================

teacher_id = get_current_user_id()
tests = get_tests_by_teacher(teacher_id)

if not tests:
    st.info("📭 No tests created yet")
    if st.button("➕ Create Your First Test", use_container_width=True, type="primary"):
        st.switch_page("pages/create_test.py")
    st.stop()

# Test selector
if 'selected_test_id' not in st.session_state:
    st.session_state.selected_test_id = tests[0]['id']

test_ids = [t['id'] for t in tests]
test_titles = {t['id']: f"{t['title']} ({t['subject']})" for t in tests}

col1, col2 = st.columns([3, 1])

with col1:
    selected_test_id = st.selectbox(
        "Select a test to analyze",
        options=test_ids,
        format_func=lambda x: test_titles[x],
        index=test_ids.index(st.session_state.selected_test_id) if st.session_state.selected_test_id in test_ids else 0,
        key="dashboard_test_selector"
    )
    st.session_state.selected_test_id = selected_test_id

with col2:
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()

# ========================================
# LOAD DATA
# ========================================

with st.spinner("Loading test data..."):
    test = get_test_by_id(selected_test_id)
    submissions = get_submissions_by_test(selected_test_id)
    questions = get_questions_by_test(selected_test_id)

st.markdown("")
st.markdown("")

# ========================================
# CHECK FOR SUBMISSIONS
# ========================================

if len(submissions) == 0:
    st.info("📭 No submissions yet for this test")
    st.markdown(f"""
    ### Waiting for Student Responses
    
    **Test Details:**
    - **Title:** {test['title']}
    - **Subject:** {test['subject']}
    - **Questions:** {test['total_questions']}
    - **Access Code:** `{test['access_code']}`
    
    Share the test link and access code with your students. Analytics will appear here once they submit responses.
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📚 Back to My Tests", use_container_width=True):
            st.switch_page("pages/view_test.py")
    with col2:
        if st.button("➕ Create New Test", use_container_width=True):
            st.switch_page("pages/create_test.py")
    
    st.stop()

# ========================================
# GENERATE ANALYTICS
# ========================================

with st.spinner("Analyzing performance data..."):
    analytics = generate_comprehensive_analytics(questions, submissions)

if not analytics.get('has_data'):
    st.error("❌ Unable to generate analytics")
    st.stop()

# ========================================
# KEY METRICS OVERVIEW
# ========================================

st.markdown("### 📈 Key Metrics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Students", analytics['total_submissions'])

with col2:
    avg_score = analytics['statistics']['mean']
    st.metric("Average Score", f"{avg_score:.1f}%")

with col3:
    readiness_score = analytics['class_readiness']['readiness_score']
    st.metric("Readiness Score", f"{readiness_score:.1f}/100")

with col4:
    high_risk = analytics['risk_classification']['stats']['high_risk_count']
    st.metric("High Risk Students", high_risk, delta=None, delta_color="inverse")

st.markdown("")
st.markdown("")

# ========================================
# CLASS READINESS INDICATOR
# ========================================

st.markdown("### 🎯 Class Readiness Assessment")

readiness = analytics['class_readiness']
status = readiness['status']

# Determine card class and emoji
if status == 'Exam Ready':
    card_color = '#d4edda'
    border_color = '#28a745'
    emoji = '🟢'
elif status == 'Borderline':
    card_color = '#fff3cd'
    border_color = '#ffc107'
    emoji = '🟡'
else:
    card_color = '#f8d7da'
    border_color = '#dc3545'
    emoji = '🔴'

col1, col2 = st.columns([1, 2])

with col1:
    # Readiness gauge
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=readiness_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Readiness Score"},
        delta={'reference': 75},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "#28a745" if readiness_score >= 75 else ("#ffc107" if readiness_score >= 60 else "#dc3545")},
            'steps': [
                {'range': [0, 60], 'color': "#f8d7da"},
                {'range': [60, 75], 'color': "#fff3cd"},
                {'range': [75, 100], 'color': "#d4edda"}
            ],
            'threshold': {
                'line': {'color': "black", 'width': 4},
                'thickness': 0.75,
                'value': 75
            }
        }
    ))
    fig_gauge.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig_gauge, use_container_width=True)

with col2:
    st.markdown(
        f"""
        <div class="metric-card detailed" 
             style="border-left:5px solid {border_color};
                    background:{card_color};">

        <h2>{emoji} {status}</h2>

        **Average Performance:** {readiness['average_percentage']:.1f}%  
        **Performance Spread:** {readiness['std_deviation']:.1f}%  
        **High Performers:** {readiness['high_performers_pct']:.1f}%  
        **At Risk:** {readiness['at_risk_pct']:.1f}%  

        <div class="recommendation">
            <strong>Recommendation:</strong><br/>
            {readiness['recommendation']}
        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("")
st.markdown("")

# ========================================
# TOPIC PERFORMANCE
# ========================================

st.markdown("### 📚 Topic Performance Analysis")

topic_perf = analytics['topic_performance']

# Create dataframe for visualization
topic_data = []
for topic, stats in topic_perf.items():
    topic_data.append({
        'Topic': topic,
        'Accuracy (%)': stats['accuracy'],
        'Correct': stats['correct'],
        'Total Attempts': stats['total_attempts'],
        'Status': '🟢 Strong' if stats['accuracy'] >= 75 else ('🟡 Moderate' if stats['accuracy'] >= 60 else '🔴 Weak')
    })

df_topics = pd.DataFrame(topic_data).sort_values('Accuracy (%)', ascending=False)

# Bar chart
fig_topics = px.bar(
    df_topics,
    x='Topic',
    y='Accuracy (%)',
    color='Accuracy (%)',
    color_continuous_scale=['#dc3545', '#ffc107', '#28a745'],
    range_color=[0, 100],
    title="Topic Accuracy Overview"
)
fig_topics.add_hline(y=60, line_dash="dash", line_color="orange", annotation_text="Minimum Target (60%)")
fig_topics.update_layout(height=400)
st.plotly_chart(fig_topics, use_container_width=True)

# Table
st.dataframe(df_topics, use_container_width=True, hide_index=True)

# Weak topics highlight
weak_topics = analytics['weak_topics']
if weak_topics:
    st.warning(f"⚠️ **{len(weak_topics)} weak topic(s) identified** (< 60% accuracy)")
    cols = st.columns(min(len(weak_topics), 3))
    for idx, (topic, accuracy) in enumerate(weak_topics[:3]):
        with cols[idx]:
            st.metric(topic, f"{accuracy:.1f}%", delta=f"{accuracy - 60:.1f}% below target")

st.markdown("")
st.markdown("")

# ========================================
# STUDENT RISK CLASSIFICATION
# ========================================

st.markdown("### 👥 Student Risk Classification")

risk_data = analytics['risk_classification']

# Summary metrics
st.markdown(
    f"""
    <div class="risk-grid">
        <div class="metric-card compact high-risk">
            <h4>🔴 High Risk</h4>
            <h3>{risk_data['stats']['high_risk_count']}</h3>
            <p>Students below 40%</p>
        </div>
        <div class="metric-card compact medium-risk">
            <h4>🟡 Medium Risk</h4>
            <h3>{risk_data['stats']['medium_risk_count']}</h3>
            <p>Students between 40–65%</p>
        </div>
        <div class="metric-card compact low-risk">
            <h4>🟢 Low Risk</h4>
            <h3>{risk_data['stats']['low_risk_count']}</h3>
            <p>Students above 65%</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Detailed student table
st.markdown("#### Student Performance Table")

all_students = []
for student in risk_data['high_risk']:
    all_students.append({**student, 'risk': '🔴 High Risk'})
for student in risk_data['medium_risk']:
    all_students.append({**student, 'risk': '🟡 Medium Risk'})
for student in risk_data['low_risk']:
    all_students.append({**student, 'risk': '🟢 Low Risk'})

df_students = pd.DataFrame(all_students)
df_students = df_students.rename(columns={'name': 'Student', 'percentage': 'Score (%)', 'risk': 'Risk Level'})
df_students['Score (%)'] = df_students['Score (%)'].apply(lambda x: f"{x:.1f}%")
df_students = df_students[['Student', 'Score (%)', 'Risk Level']]

st.dataframe(df_students, use_container_width=True, hide_index=True)

st.markdown("")
st.markdown("")

# ========================================
# AI-POWERED INSIGHTS
# ========================================

st.markdown("### 🤖 AI-Powered Insights")

with st.spinner("Generating AI insights..."):
    quick_insights = get_quick_insights(analytics)

st.markdown("""
<style>
.insight-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
    margin: 1.5rem 0;
}

.insight-box {
    background: #e7f3ff;
    padding: 1.5rem;
    border-radius: 12px;
    border-left: 5px solid #0066cc;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    line-height: 1.6;
}

.insight-box h4 {
    margin-bottom: 0.75rem;
    font-size: 1.1rem;
    color: #0066cc;
}

.insight-box p {
    margin: 0;
    color: #333;
    font-weight: 400;
}

@media (max-width: 768px) {
    .insight-grid {
        grid-template-columns: 1fr;
    }
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    f"""
    <div class="insight-grid">
        <div class="insight-box">
            <h4>📝 Summary</h4>
            <p>{quick_insights.get('summary', 'AI insights unavailable')}</p>
        </div>
        <div class="insight-box">
            <h4>⚠️ Areas of Concern</h4>
            <p>{quick_insights.get('weaknesses', 'AI insights unavailable')}</p>
        </div>
        <div class="insight-box">
            <h4>✅ Strengths</h4>
            <p>{quick_insights.get('strengths', 'AI insights unavailable')}</p>
        </div>
        <div class="insight-box">
            <h4>🎯 Action Items</h4>
            <p>{quick_insights.get('action_items', 'AI insights unavailable')}</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("")
st.markdown("")

# ========================================
# ACTIONS
# ========================================

col1, col2, col3 = st.columns(3)

# ========================================
# ACTIONS
# ========================================

col1, col2, col3 = st.columns(3)

with col1:
    from utils.html_report_generator import generate_html_report
    from datetime import datetime, timezone
    
    html_report = generate_html_report(
        test_title=test['title'],
        test_subject=test['subject'],
        analytics=analytics,
        ai_insights=quick_insights
    )
    
    st.download_button(
        label="📄 Download HTML Report",
        data=html_report,
        file_name=f"Dashboard_{test['title'].replace(' ', '_')}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.html",
        mime="text/html",
        use_container_width=True,
        type="primary"
    )

with col2:
    if st.button("📚 Back to My Tests", use_container_width=True):
        st.switch_page("pages/view_test.py")

with col3:
    if st.button("➕ Create New Test", use_container_width=True):
        st.switch_page("pages/create_test.py")

st.caption("Built with ❤️ by Mr. Android for Nigerian tutorial centers | MVP v1.0")