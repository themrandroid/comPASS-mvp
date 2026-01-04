"""
Analytics Engine

This module provides explainable analytics functions for test performance:
- Topic-wise accuracy
- Student risk classification
- Class readiness scoring
- Statistical aggregations

All formulas are simple, transparent, and actionable.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import defaultdict


# ========================================
# DATA PREPARATION
# ========================================

def prepare_analytics_data(questions: List[Dict], submissions: List[Dict]) -> pd.DataFrame:
    """
    Prepare a comprehensive dataframe for analytics.
    
    Args:
        questions: List of question documents from Firestore
        submissions: List of submission documents from Firestore
    
    Returns:
        pd.DataFrame: Merged data with student responses and correctness
    """
    # Create questions lookup
    questions_df = pd.DataFrame(questions)
    questions_lookup = {q['id']: q for q in questions}
    
    # Prepare student response data
    response_data = []
    
    for submission in submissions:
        student_name = submission['student_name']
        answers = submission['answers']
        
        for question_id, selected_option in answers.items():
            if question_id in questions_lookup:
                question = questions_lookup[question_id]
                is_correct = selected_option.upper() == question['correct_option'].upper()
                
                response_data.append({
                    'student_name': student_name,
                    'question_id': question_id,
                    'question': question['question'],
                    'topic': question['topic'],
                    'correct_option': question['correct_option'],
                    'selected_option': selected_option,
                    'is_correct': is_correct,
                    'score': submission['score'],
                    'percentage': submission['percentage']
                })
    
    if not response_data:
        return pd.DataFrame()
    
    df = pd.DataFrame(response_data)
    return df


# ========================================
# TOPIC-WISE ANALYTICS
# ========================================

def calculate_topic_performance(questions: List[Dict], submissions: List[Dict]) -> Dict:
    """
    Calculate accuracy and statistics per topic.
    
    Formula:
        Topic Accuracy = (Correct answers in topic) / (Total attempts in topic) × 100
    
    Args:
        questions: List of question documents
        submissions: List of submission documents
    
    Returns:
        dict: {
            topic_name: {
                'accuracy': float (0-100),
                'correct': int,
                'total_attempts': int,
                'total_questions': int,
                'students_attempted': int
            }
        }
    """
    df = prepare_analytics_data(questions, submissions)
    
    if df.empty:
        return {}
    
    topic_stats = {}
    
    # Get total questions per topic
    questions_per_topic = pd.DataFrame(questions).groupby('topic').size().to_dict()
    
    for topic in df['topic'].unique():
        topic_data = df[df['topic'] == topic]
        
        correct_count = topic_data['is_correct'].sum()
        total_attempts = len(topic_data)
        accuracy = (correct_count / total_attempts * 100) if total_attempts > 0 else 0
        students_attempted = topic_data['student_name'].nunique()
        
        topic_stats[topic] = {
            'accuracy': round(accuracy, 2),
            'correct': int(correct_count),
            'total_attempts': int(total_attempts),
            'total_questions': questions_per_topic.get(topic, 0),
            'students_attempted': students_attempted
        }
    
    return topic_stats


def identify_weak_topics(topic_performance: Dict, threshold: float = 60.0) -> List[Tuple[str, float]]:
    """
    Identify topics where class performance is below threshold.
    
    Args:
        topic_performance: Output from calculate_topic_performance()
        threshold: Percentage below which a topic is considered weak
    
    Returns:
        list: [(topic_name, accuracy), ...] sorted by accuracy ascending
    """
    weak_topics = [
        (topic, stats['accuracy'])
        for topic, stats in topic_performance.items()
        if stats['accuracy'] < threshold
    ]
    
    # Sort by accuracy (worst first)
    weak_topics.sort(key=lambda x: x[1])
    
    return weak_topics


def identify_strong_topics(topic_performance: Dict, threshold: float = 80.0) -> List[Tuple[str, float]]:
    """
    Identify topics where class performance exceeds threshold.
    
    Args:
        topic_performance: Output from calculate_topic_performance()
        threshold: Percentage above which a topic is considered strong
    
    Returns:
        list: [(topic_name, accuracy), ...] sorted by accuracy descending
    """
    strong_topics = [
        (topic, stats['accuracy'])
        for topic, stats in topic_performance.items()
        if stats['accuracy'] >= threshold
    ]
    
    # Sort by accuracy (best first)
    strong_topics.sort(key=lambda x: x[1], reverse=True)
    
    return strong_topics


# ========================================
# STUDENT RISK CLASSIFICATION
# ========================================

def classify_student_risk(
    submissions: List[Dict],
    high_risk_threshold: float = 40.0,
    medium_risk_threshold: float = 65.0
) -> Dict:
    """
    Classify students into risk categories based on performance.
    
    Risk Levels:
        - High Risk: < 40% (Critical intervention needed)
        - Medium Risk: 40-65% (Needs support)
        - Low Risk: > 65% (On track)
    
    Args:
        submissions: List of submission documents
        high_risk_threshold: Upper bound for high risk (default: 40%)
        medium_risk_threshold: Upper bound for medium risk (default: 65%)
    
    Returns:
        dict: {
            'high_risk': [{'name': str, 'percentage': float}, ...],
            'medium_risk': [...],
            'low_risk': [...],
            'stats': {
                'high_risk_count': int,
                'medium_risk_count': int,
                'low_risk_count': int,
                'total_students': int
            }
        }
    """
    high_risk = []
    medium_risk = []
    low_risk = []
    
    for submission in submissions:
        student_data = {
            'name': submission['student_name'],
            'percentage': submission['percentage'],
            'score': submission['score'],
            'total': submission['total_questions']
        }
        
        percentage = submission['percentage']
        
        if percentage < high_risk_threshold:
            high_risk.append(student_data)
        elif percentage < medium_risk_threshold:
            medium_risk.append(student_data)
        else:
            low_risk.append(student_data)
    
    # Sort each category by percentage (worst first for high/medium, best first for low)
    high_risk.sort(key=lambda x: x['percentage'])
    medium_risk.sort(key=lambda x: x['percentage'])
    low_risk.sort(key=lambda x: x['percentage'], reverse=True)
    
    return {
        'high_risk': high_risk,
        'medium_risk': medium_risk,
        'low_risk': low_risk,
        'stats': {
            'high_risk_count': len(high_risk),
            'medium_risk_count': len(medium_risk),
            'low_risk_count': len(low_risk),
            'total_students': len(submissions)
        }
    }




# ========================================
# CLASS READINESS INDICATOR
# ========================================

def calculate_class_readiness(submissions: List[Dict]) -> Dict:
    """
    Calculate overall class readiness score and status.
    
    Readiness Formula:
        Base Score = Average class percentage
        Adjustments:
            - Consistency bonus: +5 if std_dev < 15
            - High performer bonus: +3 if >50% students above 70%
            - At-risk penalty: -10 if >30% students below 40%
    
    Status Levels:
        - Exam Ready: Score ≥ 75
        - Borderline: Score 60-74
        - Not Ready: Score < 60
    
    Args:
        submissions: List of submission documents
    
    Returns:
        dict: {
            'readiness_score': float (0-100),
            'status': str (Exam Ready/Borderline/Not Ready),
            'average_percentage': float,
            'std_deviation': float,
            'high_performers_pct': float,
            'at_risk_pct': float,
            'recommendation': str
        }
    """
    if not submissions:
        return {
            'readiness_score': 0,
            'status': 'No Data',
            'average_percentage': 0,
            'std_deviation': 0,
            'high_performers_pct': 0,
            'at_risk_pct': 0,
            'recommendation': 'No submissions to analyze'
        }
    
    percentages = [s['percentage'] for s in submissions]
    
    # Base metrics
    avg_percentage = np.mean(percentages)
    std_dev = np.std(percentages)
    
    # Calculate proportions
    high_performers = sum(1 for p in percentages if p >= 70)
    at_risk_students = sum(1 for p in percentages if p < 40)
    
    high_performers_pct = (high_performers / len(submissions)) * 100
    at_risk_pct = (at_risk_students / len(submissions)) * 100
    
    # Calculate readiness score
    readiness_score = avg_percentage
    
    # Apply adjustments
    if std_dev < 15:  # Consistent performance
        readiness_score += 5
    
    if high_performers_pct > 50:  # Majority doing well
        readiness_score += 3
    
    if at_risk_pct > 30:  # Too many struggling
        readiness_score -= 10
    
    # Cap at 100
    readiness_score = min(100, max(0, readiness_score))
    
    # Determine status
    if readiness_score >= 75:
        status = 'Exam Ready'
        recommendation = 'Class is well-prepared. Focus on revision and practice.'
    elif readiness_score >= 60:
        status = 'Borderline'
        recommendation = 'Class needs targeted intervention on weak topics. 1-2 weeks of focused revision recommended.'
    else:
        status = 'Not Ready'
        recommendation = 'Significant gaps identified. Conduct intensive revision sessions.'
    
    return {
        'readiness_score': round(readiness_score, 2),
        'status': status,
        'average_percentage': round(avg_percentage, 2),
        'std_deviation': round(std_dev, 2),
        'high_performers_pct': round(high_performers_pct, 2),
        'at_risk_pct': round(at_risk_pct, 2),
        'recommendation': recommendation
    }


# ========================================
# STATISTICAL SUMMARIES
# ========================================

def calculate_test_statistics(submissions: List[Dict]) -> Dict:
    """
    Calculate basic statistical measures for the test.
    
    Args:
        submissions: List of submission documents
    
    Returns:
        dict: {
            'mean': float,
            'median': float,
            'mode': float,
            'std_deviation': float,
            'min_score': float,
            'max_score': float,
            'quartiles': {'Q1': float, 'Q2': float, 'Q3': float}
        }
    """
    if not submissions:
        return {}
    
    percentages = [s['percentage'] for s in submissions]
    
    return {
        'mean': round(np.mean(percentages), 2),
        'median': round(np.median(percentages), 2),
        'std_deviation': round(np.std(percentages), 2),
        'min_score': round(min(percentages), 2),
        'max_score': round(max(percentages), 2),
        'quartiles': {
            'Q1': round(np.percentile(percentages, 25), 2),
            'Q2': round(np.percentile(percentages, 50), 2),
            'Q3': round(np.percentile(percentages, 75), 2)
        }
    }

# ========================================
# COMPARATIVE ANALYTICS
# ========================================

def compare_student_to_class(student_submission: Dict, all_submissions: List[Dict]) -> Dict:
    """
    Compare a single student's performance to class average.
    
    Args:
        student_submission: Single submission document
        all_submissions: All submissions including the student's
    
    Returns:
        dict: {
            'student_percentage': float,
            'class_average': float,
            'difference': float (positive = above average),
            'percentile': float (0-100),
            'rank': int,
            'total_students': int,
            'performance_category': str
        }
    """
    student_pct = student_submission['percentage']
    all_percentages = [s['percentage'] for s in all_submissions]
    
    class_avg = np.mean(all_percentages)
    difference = student_pct - class_avg
    
    # Calculate percentile
    percentile = (sum(1 for p in all_percentages if p <= student_pct) / len(all_percentages)) * 100
    
    # Calculate rank
    sorted_scores = sorted(all_percentages, reverse=True)
    rank = sorted_scores.index(student_pct) + 1
    
    # Determine category
    if percentile >= 75:
        category = 'Top Performer'
    elif percentile >= 50:
        category = 'Above Average'
    elif percentile >= 25:
        category = 'Below Average'
    else:
        category = 'Needs Support'
    
    return {
        'student_percentage': round(student_pct, 2),
        'class_average': round(class_avg, 2),
        'difference': round(difference, 2),
        'percentile': round(percentile, 2),
        'rank': rank,
        'total_students': len(all_submissions),
        'performance_category': category
    }


# ========================================
# AGGREGATED INSIGHTS
# ========================================

def generate_comprehensive_analytics(questions: List[Dict], submissions: List[Dict]) -> Dict:
    """
    Generate all analytics in one comprehensive dictionary.
    This is the main function teachers will use.
    
    Args:
        questions: List of question documents
        submissions: List of submission documents
    
    Returns:
        dict: Complete analytics package with all metrics
    """
    if not submissions:
        return {
            'error': 'No submissions available',
            'has_data': False
        }
    
    analytics = {
        'has_data': True,
        'total_submissions': len(submissions),
        'total_questions': len(questions),
        
        # Topic analytics
        'topic_performance': calculate_topic_performance(questions, submissions),
        'weak_topics': identify_weak_topics(
            calculate_topic_performance(questions, submissions)
        ),
        'strong_topics': identify_strong_topics(
            calculate_topic_performance(questions, submissions)
        ),
        
        # Student risk
        'risk_classification': classify_student_risk(submissions),
        
        # Class readiness
        'class_readiness': calculate_class_readiness(submissions),
        
        # Statistical summary
        'statistics': calculate_test_statistics(submissions),
        
    }
    
    return analytics