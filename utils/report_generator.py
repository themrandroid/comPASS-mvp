"""
PDF Report Generator

Generates comprehensive PDF reports matching the dashboard layout.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from datetime import datetime
import io
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')


class TestReportGenerator:
    """Generate PDF reports matching dashboard layout."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        self.width, self.height = letter
        
    def _setup_custom_styles(self):
        """Create custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#0066cc'),
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12,
            spaceBefore=15,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='CardText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            leading=14
        ))
    
    def _create_header(self, test_title: str, test_subject: str) -> List:
        """Create report header matching dashboard."""
        elements = []
        
        title = Paragraph("📊 Analytics Dashboard Report", self.styles['ReportTitle'])
        elements.append(title)
        
        test_info = Paragraph(
            f"<b>Test:</b> {test_title} &nbsp;&nbsp;&nbsp; <b>Subject:</b> {test_subject}",
            self.styles['Normal']
        )
        elements.append(test_info)
        
        date_para = Paragraph(
            f"<i>Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</i>",
            self.styles['Normal']
        )
        elements.append(date_para)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_key_metrics(self, analytics: Dict) -> List:
        """Match dashboard Key Metrics section."""
        elements = []
        
        elements.append(Paragraph("📈 Key Metrics", self.styles['SectionHeading']))
        
        stats = analytics['statistics']
        readiness = analytics['class_readiness']
        risk_stats = analytics['risk_classification']['stats']
        
        # Create 4-column metrics table
        data = [[
            Paragraph("<b>Total Students</b>", self.styles['CardText']),
            Paragraph("<b>Average Score</b>", self.styles['CardText']),
            Paragraph("<b>Readiness Score</b>", self.styles['CardText']),
            Paragraph("<b>High Risk Students</b>", self.styles['CardText'])
        ], [
            Paragraph(f"<font size=16><b>{analytics['total_submissions']}</b></font>", self.styles['CardText']),
            Paragraph(f"<font size=16><b>{stats['mean']:.1f}%</b></font>", self.styles['CardText']),
            Paragraph(f"<font size=16><b>{readiness['readiness_score']:.1f}/100</b></font>", self.styles['CardText']),
            Paragraph(f"<font size=16 color='#dc3545'><b>{risk_stats['high_risk_count']}</b></font>", self.styles['CardText'])
        ]]
        
        table = Table(data, colWidths=[1.5*inch]*4)
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
            ('BACKGROUND', (0, 1), (-1, 1), colors.white),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_readiness_assessment(self, analytics: Dict) -> List:
        """Match dashboard Class Readiness Assessment."""
        elements = []
        
        elements.append(Paragraph("🎯 Class Readiness Assessment", self.styles['SectionHeading']))
        
        readiness = analytics['class_readiness']
        status = readiness['status']
        
        # Determine colors
        if status == 'Exam Ready':
            bg_color = colors.HexColor('#d4edda')
            border_color = colors.HexColor('#28a745')
            emoji = '🟢'
        elif status == 'Borderline':
            bg_color = colors.HexColor('#fff3cd')
            border_color = colors.HexColor('#ffc107')
            emoji = '🟡'
        else:
            bg_color = colors.HexColor('#f8d7da')
            border_color = colors.HexColor('#dc3545')
            emoji = '🔴'
        
        # Readiness card data
        card_data = [[
            Paragraph(f"<b>{emoji} {status}</b>", self.styles['SectionHeading']),
        ], [
            Paragraph(
                f"<b>Average Performance:</b> {readiness['average_percentage']:.1f}%<br/>"
                f"<b>Performance Spread:</b> {readiness['std_deviation']:.1f}% std dev<br/>"
                f"<b>High Performers:</b> {readiness['high_performers_pct']:.1f}%<br/>"
                f"<b>At Risk:</b> {readiness['at_risk_pct']:.1f}%",
                self.styles['CardText']
            )
        ], [
            Paragraph(
                f"<b>Recommendation:</b><br/>{readiness['recommendation']}",
                self.styles['CardText']
            )
        ]]
        
        table = Table(card_data, colWidths=[6*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), bg_color),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('BOX', (0, 0), (-1, -1), 3, border_color),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_topic_performance(self, analytics: Dict) -> List:
        """Match dashboard Topic Performance Analysis."""
        elements = []
        
        elements.append(Paragraph("📚 Topic Performance Analysis", self.styles['SectionHeading']))
        
        topic_perf = analytics['topic_performance']
        
        # Bar chart
        fig, ax = plt.subplots(figsize=(7, 4))
        
        topics = list(topic_perf.keys())
        accuracies = [stats['accuracy'] for stats in topic_perf.values()]
        colors_bar = ['#28a745' if a >= 75 else '#ffc107' if a >= 60 else '#dc3545' for a in accuracies]
        
        bars = ax.barh(topics, accuracies, color=colors_bar)
        ax.axvline(x=60, color='orange', linestyle='--', linewidth=2, label='Target (60%)')
        ax.set_xlabel('Accuracy (%)', fontsize=11)
        ax.set_title('Topic Accuracy Overview', fontsize=13, fontweight='bold')
        ax.set_xlim(0, 100)
        ax.legend()
        ax.grid(axis='x', alpha=0.3)
        
        plt.tight_layout()
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        img = Image(img_buffer, width=6*inch, height=3*inch)
        elements.append(img)
        elements.append(Spacer(1, 0.2*inch))
        
        # Topic table
        topic_data = [['Topic', 'Accuracy', 'Correct/Total', 'Status']]
        for topic, stats in sorted(topic_perf.items(), key=lambda x: x[1]['accuracy'], reverse=True):
            status = '🟢 Strong' if stats['accuracy'] >= 75 else ('🟡 Moderate' if stats['accuracy'] >= 60 else '🔴 Weak')
            topic_data.append([
                topic,
                f"{stats['accuracy']:.1f}%",
                f"{stats['correct']}/{stats['total_attempts']}",
                status
            ])
        
        table = Table(topic_data, colWidths=[2.5*inch, 1.2*inch, 1.2*inch, 1.1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.2*inch))
        
        return elements
    
    def _create_risk_classification(self, analytics: Dict) -> List:
        """Match dashboard Student Risk Classification."""
        elements = []
        
        elements.append(Paragraph("👥 Student Risk Analysis", self.styles['SectionHeading']))
        
        risk_data = analytics['risk_classification']
        risk_stats = risk_data['stats']
        
        # Risk summary cards (3 columns)
        summary_data = [[
            Paragraph("<b>🔴 High Risk</b>", self.styles['CardText']),
            Paragraph("<b>🟡 Medium Risk</b>", self.styles['CardText']),
            Paragraph("<b>🟢 Low Risk</b>", self.styles['CardText'])
        ], [
            Paragraph(f"<font size=18><b>{risk_stats['high_risk_count']}</b></font>", self.styles['CardText']),
            Paragraph(f"<font size=18><b>{risk_stats['medium_risk_count']}</b></font>", self.styles['CardText']),
            Paragraph(f"<font size=18><b>{risk_stats['low_risk_count']}</b></font>", self.styles['CardText'])
        ], [
            Paragraph("Students < 40%", self.styles['CardText']),
            Paragraph("Students 40-65%", self.styles['CardText']),
            Paragraph("Students > 65%", self.styles['CardText'])
        ]]
        
        table = Table(summary_data, colWidths=[2*inch]*3)
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8d7da')),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#fff3cd')),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor('#d4edda')),
            ('BOX', (0, 0), (-1, -1), 1, colors.grey),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        # Student performance table
        elements.append(Paragraph("<b>Student Performance Table</b>", self.styles['CardText']))
        elements.append(Spacer(1, 0.1*inch))
        
        all_students = []
        for student in risk_data['high_risk']:
            all_students.append({'name': student['name'], 'percentage': student['percentage'], 'risk': '🔴 High Risk'})
        for student in risk_data['medium_risk']:
            all_students.append({'name': student['name'], 'percentage': student['percentage'], 'risk': '🟡 Medium Risk'})
        for student in risk_data['low_risk']:
            all_students.append({'name': student['name'], 'percentage': student['percentage'], 'risk': '🟢 Low Risk'})
        
        student_data = [['Student', 'Score (%)', 'Risk Level']]
        for student in all_students[:20]:  # Limit to 20 for PDF space
            student_data.append([
                student['name'],
                f"{student['percentage']:.1f}%",
                student['risk']
            ])
        
        student_table = Table(student_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        student_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0066cc')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        
        elements.append(student_table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def _create_ai_insights(self, ai_insights: Dict) -> List:
        """Match dashboard AI-Powered Insights."""
        elements = []
        
        elements.append(Paragraph("🤖 AI-Powered Insights", self.styles['SectionHeading']))
        
        if not ai_insights:
            elements.append(Paragraph("AI insights unavailable", self.styles['CardText']))
            return elements
        
        # 2x2 grid of insight cards
        insights_data = [[
            Paragraph(f"<b>📝 Summary</b><br/>{ai_insights.get('summary', 'N/A')}", self.styles['CardText']),
            Paragraph(f"<b>⚠️ Areas of Concern</b><br/>{ai_insights.get('weaknesses', 'N/A')}", self.styles['CardText'])
        ], [
            Paragraph(f"<b>✅ Strengths</b><br/>{ai_insights.get('strengths', 'N/A')}", self.styles['CardText']),
            Paragraph(f"<b>🎯 Action Items</b><br/>{ai_insights.get('action_items', 'N/A')}", self.styles['CardText'])
        ]]
        
        table = Table(insights_data, colWidths=[3*inch]*2)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e7f3ff')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOX', (0, 0), (-1, -1), 2, colors.HexColor('#0066cc')),
            ('INNERGRID', (0, 0), (-1, -1), 1, colors.HexColor('#0066cc')),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 0.3*inch))
        
        return elements
    
    def generate_report(
        self,
        test_title: str,
        test_subject: str,
        analytics: Dict,
        ai_insights: Optional[Dict] = None,
        revision_plan: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> io.BytesIO:
        """Generate PDF matching dashboard layout."""
        
        if output_path:
            buffer = open(output_path, 'wb')
        else:
            buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                rightMargin=0.75*inch, leftMargin=0.75*inch,
                                topMargin=1*inch, bottomMargin=1*inch)
        
        story = []
        
        # Header
        story.extend(self._create_header(test_title, test_subject))
        
        # Key Metrics
        story.extend(self._create_key_metrics(analytics))
        
        # Class Readiness
        story.extend(self._create_readiness_assessment(analytics))
        
        # Topic Performance
        story.extend(self._create_topic_performance(analytics))
        
        story.append(PageBreak())
        
        # Risk Classification
        story.extend(self._create_risk_classification(analytics))
        
        # AI Insights
        story.extend(self._create_ai_insights(ai_insights or {}))
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer = Paragraph(
            "<i>Generated by comPASS - Smart Test Analytics & Decision Support System</i>",
            self.styles['Normal']
        )
        story.append(footer)
        
        doc.build(story)
        
        if not output_path:
            buffer.seek(0)
        else:
            buffer.close()
            buffer = open(output_path, 'rb')
            buffer = io.BytesIO(buffer.read())
        
        return buffer


# Global instance
report_generator = TestReportGenerator()


def generate_test_report(
    test_title: str,
    test_subject: str,
    analytics: Dict,
    ai_insights: Optional[Dict] = None,
    revision_plan: Optional[str] = None
) -> io.BytesIO:
    """Generate PDF report matching dashboard."""
    return report_generator.generate_report(
        test_title, test_subject, analytics, ai_insights, revision_plan
    )