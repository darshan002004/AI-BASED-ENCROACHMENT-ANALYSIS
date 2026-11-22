from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse, StreamingResponse
from app.database import get_db
import csv
import io
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from app.config import settings

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/csv")
async def export_incidents_csv():
    db = get_db()
    col = db.get_collection("incidents")
    incidents = await col.find({}).to_list(1000)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Incident ID", "Title", "Location", "Type", "Severity", "Status",
        "Accessibility Score (%)", "Occupancy (%)", "Occupied Area (sqm)",
        "Date Reported", "Assigned Officer", "Resolution Date"
    ])

    for inc in incidents:
        writer.writerow([
            inc.get("incident_number", ""),
            inc.get("title", ""),
            inc.get("location_name", ""),
            inc.get("primary_encroachment_type", ""),
            inc.get("severity", ""),
            inc.get("status", ""),
            inc.get("accessibility_score", ""),
            inc.get("occupancy_percentage", ""),
            inc.get("occupied_area_sqm", ""),
            inc.get("date_reported", ""),
            inc.get("assigned_officer_name", "Unassigned"),
            inc.get("resolution_date", "Pending")
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=encrowatch_incidents_{datetime.utcnow().strftime('%Y%m%d')}.csv"}
    )

@router.get("/pdf/incident/{incident_id}")
async def export_incident_pdf(incident_id: str):
    db = get_db()
    col = db.get_collection("incidents")
    inc = await col.find_one({"$or": [{"_id": incident_id}, {"id": incident_id}]})
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    pdf_filename = f"report_{inc.get('incident_number', 'ENC')}.pdf"
    pdf_path = os.path.join(settings.UPLOAD_DIR, "reports", pdf_filename)
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

    doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor("#0F172A"), spaceAfter=10)
    sub_style = ParagraphStyle('SubStyle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor("#64748B"), spaceAfter=15)
    bold_style = ParagraphStyle('BoldStyle', parent=styles['Normal'], fontSize=11, fontName="Helvetica-Bold", textColor=colors.HexColor("#1E293B"))
    normal_style = ParagraphStyle('NormalText', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor("#334155"))

    elements = []

    # Header
    elements.append(Paragraph("ENCROWATCH AI — SMART CITY AUDIT REPORT", title_style))
    elements.append(Paragraph(f"Official AI Incident Investigation Dossier | Generated on {datetime.utcnow().strftime('%d %b %Y %I:%M %p')}", sub_style))
    elements.append(Spacer(1, 10))

    # AI Confidence text
    conf_val = inc.get("confidence")
    conf_display = f"{int(conf_val * 100)}%" if conf_val is not None else "Uncalibrated / N/A"

    # Metadata Table
    meta_data = [
        [Paragraph("Incident Number", bold_style), Paragraph(inc.get("incident_number", "N/A"), normal_style),
         Paragraph("Status", bold_style), Paragraph(inc.get("status", "N/A"), bold_style)],
        [Paragraph("Location", bold_style), Paragraph(f"{inc.get('location_name', 'N/A')} (Lat: {inc.get('latitude', '')}, Lng: {inc.get('longitude', '')})", normal_style),
         Paragraph("Severity", bold_style), Paragraph(inc.get("severity", "N/A"), bold_style)],
        [Paragraph("Encroachment Type", bold_style), Paragraph(inc.get("primary_encroachment_type", "N/A"), normal_style),
         Paragraph("AI Confidence", bold_style), Paragraph(conf_display, normal_style)],
        [Paragraph("Reported On", bold_style), Paragraph(f"{inc.get('date_reported', '')} {inc.get('time_reported', '')}".strip() or "N/A", normal_style),
         Paragraph("Assigned Officer", bold_style), Paragraph(inc.get("assigned_officer_name") or "Unassigned", normal_style)],
    ]
    t_meta = Table(meta_data, colWidths=[120, 150, 120, 150])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t_meta)
    elements.append(Spacer(1, 15))

    # Metrics Section - honest measurements
    f_area = inc.get("footpath_area_sqm")
    occ_area = inc.get("occupied_area_sqm")
    f_area_str = f"{round(float(f_area), 1)} sq.m" if f_area is not None else "Uncalibrated"
    occ_area_str = f"{round(float(occ_area), 1)} sq.m" if occ_area is not None else "Uncalibrated"
    free_area_str = f"{round(float(f_area) - float(occ_area), 1)} sq.m" if (f_area is not None and occ_area is not None) else "Uncalibrated"

    occ_pct = inc.get("occupancy_percentage")
    occ_pct_str = f"{round(float(occ_pct), 1)}%" if occ_pct is not None else "0.0%"

    acc_score = inc.get("accessibility_score")
    acc_score_str = f"{round(float(acc_score), 1)}%" if acc_score is not None else "N/A"
    acc_status_str = inc.get("accessibility_status") or "Pending Assessment"

    elements.append(Paragraph("Accessibility & Obstruction Metrics", title_style))
    metrics_data = [
        ["Footpath Area", f_area_str, "Occupied Area", occ_area_str],
        ["Occupancy Ratio", occ_pct_str, "Free Walkway Area", free_area_str],
        ["Accessibility Score", acc_score_str, "Accessibility Status", acc_status_str]
    ]
    t_metrics = Table(metrics_data, colWidths=[130, 140, 130, 140])
    t_metrics.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#94A3B8")),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    elements.append(t_metrics)
    elements.append(Spacer(1, 15))

    # Reason & Hazards
    elements.append(Paragraph("AI Diagnostic Summary & Justification", bold_style))
    elements.append(Paragraph(inc.get("severity_reason", "Encroachment detected in designated pedestrian path."), normal_style))
    elements.append(Spacer(1, 10))

    warnings = inc.get("warnings", [])
    if warnings:
        elements.append(Paragraph("Identified Safety Hazards:", bold_style))
        for w in warnings:
            elements.append(Paragraph(f"• {w}", normal_style))
        elements.append(Spacer(1, 15))

    # Resolution Details if available
    ai_ver = inc.get("ai_verification")
    if ai_ver:
        elements.append(Paragraph("Before / After AI Verification Result", title_style))
        ver_data = [
            ["Verification Result", ai_ver.get("status", "N/A"), "Cleared Ratio", f"{ai_ver.get('cleared_percentage', 100)}%"],
            ["Original Obstruction", ai_ver.get("original_obstruction", "N/A"), "Current Status", ai_ver.get("current_obstruction", "N/A")]
        ]
        t_ver = Table(ver_data, colWidths=[130, 140, 130, 140])
        t_ver.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#DCFCE7")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#86EFAC")),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(t_ver)

    doc.build(elements)

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=pdf_filename
    )
