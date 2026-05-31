from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from datetime import datetime
import io

SEVERITY_COLORS = {
    "CRITICAL": colors.HexColor("#F87171"),
    "HIGH":     colors.HexColor("#FB923C"),
    "MEDIUM":   colors.HexColor("#FBBF24"),
    "LOW":      colors.HexColor("#4ADE80"),
    "INFO":     colors.HexColor("#38BDF8"),
    "ERROR":    colors.HexColor("#64748B"),
}

def generate_pdf_report(results: list) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )

    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=20,
        textColor=colors.HexColor("#1E3A5F"),
        spaceAfter=4,
        fontName='Helvetica-Bold'
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=16
    )
    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor("#64748B"),
        fontName='Helvetica-Bold',
        spaceBefore=8,
        spaceAfter=2
    )
    value_style = ParagraphStyle(
        'Value',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=4,
        leading=14
    )
    action_style = ParagraphStyle(
        'Action',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor("#0D4F7C"),
        spaceAfter=4,
        leading=14,
        fontName='Helvetica-Oblique'
    )

    story.append(Paragraph("SOC Triage Report", title_style))
    story.append(Paragraph(
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} &nbsp;|&nbsp; Total Alerts: {len(results)}",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#E2E8F0")))
    story.append(Spacer(1, 8))

    # Summary table
    severity_counts = {}
    for r in results:
        s = r.get("severity", "ERROR")
        severity_counts[s] = severity_counts.get(s, 0) + 1

    summary_data = [["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO", "FALSE POS"]]
    fp_count = sum(1 for r in results if str(r.get("is_false_positive","")).lower() == "true")
    summary_data.append([
        str(severity_counts.get("CRITICAL", 0)),
        str(severity_counts.get("HIGH", 0)),
        str(severity_counts.get("MEDIUM", 0)),
        str(severity_counts.get("LOW", 0)),
        str(severity_counts.get("INFO", 0)),
        str(fp_count)
    ])

    summary_table = Table(summary_data, colWidths=[28*mm]*6)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F1F5F9")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#64748B")),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('FONTSIZE', (0,1), (-1,1), 16),
        ('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,1), [colors.white]),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TEXTCOLOR', (0,1), (0,1), colors.HexColor("#F87171")),
        ('TEXTCOLOR', (1,1), (1,1), colors.HexColor("#FB923C")),
        ('TEXTCOLOR', (2,1), (2,1), colors.HexColor("#FBBF24")),
        ('TEXTCOLOR', (3,1), (3,1), colors.HexColor("#4ADE80")),
        ('TEXTCOLOR', (4,1), (4,1), colors.HexColor("#38BDF8")),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 16))

    # Individual alerts
    for r in results:
        sev = r.get("severity", "ERROR")
        sev_color = SEVERITY_COLORS.get(sev, colors.HexColor("#64748B"))

        # Alert header row
        header_data = [[
            Paragraph(f"<b>[{sev}]</b>", ParagraphStyle('H', fontSize=10,
                textColor=sev_color, fontName='Helvetica-Bold')),
            Paragraph(
                f"<b>{r.get('alert_id','N/A')}</b> &mdash; {r.get('original_type','N/A')}",
                ParagraphStyle('H2', fontSize=10,
                    textColor=colors.HexColor("#1E293B"), fontName='Helvetica-Bold')
            )
        ]]
        header_table = Table(header_data, colWidths=[22*mm, 148*mm])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LINEAFTER', (0,0), (0,-1), 2, sev_color),
        ]))
        story.append(header_table)

        # Alert details
        story.append(Paragraph("HOSTNAME", label_style))
        story.append(Paragraph(r.get('hostname', 'N/A'), value_style))
        story.append(Paragraph("CATEGORY", label_style))
        story.append(Paragraph(
            f"{r.get('category','N/A')} &nbsp;|&nbsp; Confidence: {r.get('confidence','N/A')}%",
            value_style
        ))
        story.append(Paragraph("ANALYSIS", label_style))
        story.append(Paragraph(r.get('summary', 'N/A'), value_style))
        story.append(Paragraph("RECOMMENDED ACTION", label_style))
        story.append(Paragraph(r.get('recommended_action', 'N/A'), action_style))

        if str(r.get("is_false_positive","")).lower() == "true":
            story.append(Paragraph("FALSE POSITIVE REASON", label_style))
            story.append(Paragraph(r.get('false_positive_reason', 'N/A'),
                ParagraphStyle('FP', parent=styles['Normal'], fontSize=10,
                    textColor=colors.HexColor("#FBBF24"))))

        story.append(HRFlowable(width="100%", thickness=0.5,
            color=colors.HexColor("#E2E8F0")))
        story.append(Spacer(1, 8))

    doc.build(story)
    return buffer.getvalue()