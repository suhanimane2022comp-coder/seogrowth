from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
from typing import Dict, Any


def generate_pdf_report(report_data: Dict[str, Any]) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=60, bottomMargin=50)

    styles = getSampleStyleSheet()
    story = []

    # Custom styles
    title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontSize=24, textColor=colors.HexColor('#1a1a2e'), spaceAfter=20)
    h2_style = ParagraphStyle('CustomH2', parent=styles['Heading2'], fontSize=16, textColor=colors.HexColor('#16213e'), spaceAfter=10, spaceBefore=20)
    h3_style = ParagraphStyle('CustomH3', parent=styles['Heading3'], fontSize=13, textColor=colors.HexColor('#0f3460'), spaceAfter=8, spaceBefore=12)
    body_style = ParagraphStyle('CustomBody', parent=styles['Normal'], fontSize=10, spaceAfter=6, leading=14)
    score_style = ParagraphStyle('Score', parent=styles['Normal'], fontSize=14, textColor=colors.HexColor('#e94560'), spaceAfter=4, alignment=TA_CENTER)

    summary = report_data.get("executive_summary", {})
    scores = report_data.get("seo_scores", {})

    # Title
    story.append(Paragraph("SEO Growth Report", title_style))
    story.append(Paragraph(f"<b>{summary.get('business_name', 'Business')}</b>", h2_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#e94560')))
    story.append(Spacer(1, 20))

    # Executive Summary
    story.append(Paragraph("Executive Summary", h2_style))
    story.append(Paragraph(summary.get("summary", ""), body_style))
    story.append(Spacer(1, 15))

    # Score Table
    score_data = [
        ["Metric", "Score", "Rating"],
        ["Overall SEO Score", f"{scores.get('overall_score', 0)}/100", _get_rating(scores.get('overall_score', 0))],
        ["Technical SEO", f"{scores.get('technical_score', 0)}/100", _get_rating(scores.get('technical_score', 0))],
        ["Content Quality", f"{scores.get('content_score', 0)}/100", _get_rating(scores.get('content_score', 0))],
        ["Keyword Coverage", f"{scores.get('keyword_score', 0)}/100", _get_rating(scores.get('keyword_score', 0))],
        ["Metadata Quality", f"{scores.get('metadata_score', 0)}/100", _get_rating(scores.get('metadata_score', 0))],
    ]

    score_table = Table(score_data, colWidths=[200, 100, 150])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8f9fa'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(Paragraph("SEO Scores", h2_style))
    story.append(score_table)
    story.append(Spacer(1, 20))

    # Issues
    issues = report_data.get("technical_seo", {}).get("issues", [])
    if issues:
        story.append(Paragraph("SEO Issues Found", h2_style))
        critical = [i for i in issues if i.get("severity") == "critical"]
        warnings = [i for i in issues if i.get("severity") == "warning"]

        if critical:
            story.append(Paragraph(f"Critical Issues ({len(critical)})", h3_style))
            for issue in critical[:10]:
                story.append(Paragraph(f"• <b>{issue.get('issue_type', '').replace('_', ' ').title()}</b>: {issue.get('description', '')}", body_style))

        if warnings:
            story.append(Paragraph(f"Warnings ({len(warnings)})", h3_style))
            for issue in warnings[:10]:
                story.append(Paragraph(f"• {issue.get('description', '')}", body_style))
        story.append(Spacer(1, 15))

    # Keywords
    keywords = report_data.get("keyword_opportunities", {})
    if keywords:
        story.append(Paragraph("Keyword Opportunities", h2_style))
        for kw_type, kw_list in keywords.items():
            if kw_list:
                story.append(Paragraph(f"{kw_type.replace('_', ' ').title()}", h3_style))
                story.append(Paragraph(", ".join(kw_list[:8]), body_style))
        story.append(Spacer(1, 15))

    # Content Gaps
    gaps = report_data.get("content_gaps", {})
    if gaps:
        story.append(Paragraph("Content Gap Analysis", h2_style))
        for gap_type, gap_list in gaps.items():
            if gap_list:
                story.append(Paragraph(f"{gap_type.replace('_', ' ').title()}", h3_style))
                for item in gap_list:
                    story.append(Paragraph(f"• {item}", body_style))

    # FAQs
    content = report_data.get("generated_content", {})
    faqs = content.get("faqs", [])
    if faqs:
        story.append(Paragraph("Generated FAQs", h2_style))
        for faq in faqs[:6]:
            story.append(Paragraph(f"<b>Q: {faq.get('question', '')}</b>", body_style))
            story.append(Paragraph(f"A: {faq.get('answer', '')}", body_style))
            story.append(Spacer(1, 5))

    # Blog Ideas
    blogs = content.get("blog_ideas", [])
    if blogs:
        story.append(Paragraph("Blog Content Ideas", h2_style))
        for blog in blogs:
            story.append(Paragraph(f"• <b>{blog.get('title', '')}</b> — Target keyword: {blog.get('target_keyword', '')}", body_style))

    # Improvement Plan
    plan = report_data.get("improvement_plan", [])
    if plan:
        story.append(Spacer(1, 15))
        story.append(Paragraph("Improvement Plan", h2_style))
        for item in plan:
            story.append(Paragraph(f"Priority {item.get('priority')}: {item.get('action')} ({item.get('timeframe')})", h3_style))
            for task in item.get("tasks", []):
                story.append(Paragraph(f"• {task}", body_style))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    story.append(Paragraph(f"Report generated by SEO Growth AI Agent | {report_data.get('generated_at', '')}", ParagraphStyle('footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def _get_rating(score: float) -> str:
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Average"
    elif score >= 20:
        return "Poor"
    else:
        return "Critical"
