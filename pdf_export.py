import json
import os
from datetime import datetime, date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable
)
from reportlab.lib.styles import ParagraphStyle
from remainder import send_daily_nudge
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# Color Palette Configs
RED_BG      = colors.HexColor('#FEE2E2')
RED_ACCENT  = colors.HexColor('#DC2626')
YEL_BG      = colors.HexColor('#FEF9C3')
YEL_ACCENT  = colors.HexColor('#CA8A04')
GRN_BG      = colors.HexColor('#DCFCE7')
GRN_ACCENT  = colors.HexColor('#16A34A')

HEADER_BG   = colors.HexColor('#1E3A8F')
HEADER_FG   = colors.white
ALT_ROW     = colors.HexColor('#F8FAFC')
WHITE       = colors.white
BORDER      = colors.HexColor('#CBD5E1')
TEXT_DARK   = colors.HexColor('#1E293B')
TEXT_MID    = colors.HexColor('#475569')
TEXT_LIGHT  = colors.HexColor('#94A3B8')

# Dynamic Geometry Management
PAGE_W, PAGE_H = A4
MARGIN = 20 * mm
TABLE_W = PAGE_W - 2 * MARGIN

def get_styles():
    return {
        "title": ParagraphStyle(
            "title", fontName="Helvetica-Bold", fontSize=22,
            textColor=HEADER_BG, alignment=TA_CENTER, spaceAfter=2
        ),
        "subtitle": ParagraphStyle(
            "subtitle", fontName="Helvetica", fontSize=9,
            textColor=TEXT_MID, alignment=TA_CENTER, spaceAfter=10
        ),
        "date_cell": ParagraphStyle(
            "date_cell", fontName="Helvetica-Bold", fontSize=8,
            textColor=TEXT_DARK, leading=11
        ),
        "subject_cell": ParagraphStyle(
            "subject_cell", fontName="Helvetica-Bold", fontSize=8,
            textColor=TEXT_DARK, leading=11
        ),
        "topic_cell": ParagraphStyle(
            "topic_cell", fontName="Helvetica", fontSize=8,
            textColor=TEXT_MID, leading=12
        ),
        "min_cell": ParagraphStyle(
            "min_cell", fontName="Helvetica-Bold", fontSize=9,
            textColor=TEXT_DARK, alignment=TA_CENTER, leading=11
        ),
        "notes_cell": ParagraphStyle(
            "notes_cell", fontName="Helvetica-Oblique", fontSize=7,
            textColor=TEXT_MID, alignment=TA_CENTER, leading=11
        ),
        "col_header": ParagraphStyle(
            "col_header", fontName="Helvetica-Bold", fontSize=8,
            textColor=HEADER_FG, alignment=TA_CENTER, leading=10
        ),
        "legend_label": ParagraphStyle(
            "legend_label", fontName="Helvetica-Bold", fontSize=8,
            textColor=TEXT_DARK, leading=10
        ),
        "legend_sub": ParagraphStyle(
            "legend_sub", fontName="Helvetica", fontSize=7,
            textColor=TEXT_MID, leading=10
        ),
        "summary": ParagraphStyle(
            "summary", fontName="Helvetica", fontSize=8,
            textColor=TEXT_MID, alignment=TA_CENTER, leading=12
        ),
    }

def get_urgency(exam_date_str):
    try:
        exam = datetime.strptime(exam_date_str, "%Y-%m-%d").date()
        days_left = (exam - date.today()).days
    except Exception:
        days_left = 999

    if days_left <= 7:
        return "red", RED_BG, RED_ACCENT
    if days_left <= 14:
        return "yellow", YEL_BG, YEL_ACCENT
    return "green", GRN_BG, GRN_ACCENT

def load_timetable(json_path="timetable.json"):
    # Fallback simulation if file isn't present
    if not os.path.exists(json_path):
        print(f"Warning: '{json_path}' not found! Creating dummy template data for execution.")
        dummy_data = {
            "timetable": [
                {"date": "2026-06-22", "slots": [{"subject": "Math", "chapters_to_cover": ["Calculus", "Limits"], "duration_minutes": 90, "notes": "Hard", "exam_date": "2026-06-25"}]},
                {"date": "2026-06-23", "slots": [{"subject": "Physics", "chapters_to_cover": ["Optics"], "duration_minutes": 60, "notes": "Review", "exam_date": "2026-07-02"}]}
            ],
            "weekly_summary": "Keep up the great structural pace this week!"
        }
        with open(json_path, "w") as f:
            json.dump(dummy_data, f)

    with open(json_path) as f:
        data = json.load(f)
        rows = []

        for day in data["timetable"]:
            for slot in day["slots"]:
                rows.append({
                    "date":       day["date"],
                    "subject":    slot["subject"],
                    "topic":      ", ".join(slot["chapters_to_cover"]),
                    "minutes":    slot["duration_minutes"],
                    "notes":      slot.get("notes", ""),
                    "exam_date":  slot.get("exam_date", "2099-12-31"),
                })

        return rows, data.get("weekly_summary", "")

def build_legend(s):
    items = [
        (RED_BG, RED_ACCENT, "Exam week", "0 - 7 days left"),
        (YEL_BG, YEL_ACCENT, "Revision", "8 - 14 days left"),
        (GRN_BG, GRN_ACCENT, "New chapters", "15+ days left"),
    ]
    cells = []
    for bg, accent, label, sub in items:
        cells.append(
            Table(
                [[Paragraph(f"<b>{label}</b>", s["legend_label"])],
                [Paragraph(sub, s["legend_sub"])]],
                colWidths=[45 * mm],
                style=TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), bg),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LINEABOVE", (0, 0), (-1, 0), 2, accent),
                    ("ROUNDEDCORNERS", [3]),
                ])
            )
        )

    legend_table = Table(
        [cells],
        colWidths=[TABLE_W / 3] * 3,
        style=TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )
    return legend_table

def build_timetable_table(rows, s):
    col_w = [
        26 * mm,  # date
        42 * mm,  # subject
        TABLE_W - 26*mm - 42*mm - 18*mm - 20*mm,  # topics (fills remaining)
        18 * mm,  # time
        20 * mm,  # notes
    ]

    header = [
        Paragraph("DATE", s["col_header"]),
        Paragraph("SUBJECT", s["col_header"]),
        Paragraph("TOPICS", s["col_header"]),
        Paragraph("TIME", s["col_header"]),
        Paragraph("NOTES", s["col_header"]),
    ]

    table_data = [header]
    row_styles = []

    # FIXED: Re-indented loop block so all items process properly
    for i, row in enumerate(rows):
        zone, bg, accent = get_urgency(row["exam_date"])
        row_idx = i + 1

        fill = bg if i % 2 == 0 else colors.Color(
            bg.red * 0.97, bg.green * 0.97, bg.blue * 0.97
        )

        # Format date nicely
        try:
            d = datetime.strptime(row["date"], "%Y-%m-%d")
            date_str = d.strftime("%d %b<br/>%a")  # Reportlab uses <br/> instead of \n in Paragraphs
        except Exception:
            date_str = row["date"]

        # Topic formatting
        topic_text = row["topic"].replace(", ", "<br/>• ")
        if topic_text:
            topic_text = "• " + topic_text

        table_data.append([
            Paragraph(date_str, s["date_cell"]),
            Paragraph(row["subject"], s["subject_cell"]),
            Paragraph(topic_text, s["topic_cell"]),
            Paragraph(str(row["minutes"]) + " mins", s["min_cell"]),
            Paragraph(row["notes"] or "-", s["notes_cell"]),
        ])

        row_styles += [
            ("BACKGROUND", (0, row_idx), (-1, row_idx), fill),
            ("LINEABOVE", (0, row_idx), (-1, row_idx), 0.5, BORDER),
            ("LEFTPADDING", (0, row_idx), (0, row_idx), 8),
            ("TEXTCOLOR", (0, row_idx), (0, row_idx), accent),
        ]

    base_style = TableStyle([
        # Header Styling
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TOPPADDING", (0, 0), (-1, 0), 7),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
        ("LINEBELOW", (0, 0), (-1, 0), 2, colors.HexColor("#F59E0B")),

        # Grid Core Setup
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 1, BORDER),
        ("INNERGRID", (0, 1), (-1, -1), 0.3, BORDER),
    ])  

    for r_style in row_styles:
        base_style.add(*r_style)

    return Table(table_data, colWidths=col_w, repeatRows=1, style=base_style, hAlign='LEFT')

def generate_pdf(rows, summary="", output_path="timetable.pdf"):
    s = get_styles()  # FIXED: Pointing to valid function name get_styles()
    
    doc = SimpleDocTemplate(
        output_path, pagesize=A4, 
        leftMargin=MARGIN, rightMargin=MARGIN, 
        topMargin=MARGIN, bottomMargin=MARGIN, 
        title="StudyPilot"
    )
    
    generated_on = date.today().strftime("%d %b %Y")
    total_slots = len(rows)
    total_mins = sum(r["minutes"] for r in rows)
    
    story = [
        Paragraph("StudyPilot - Weekly Timetable", s["title"]),
        Spacer(1, 20),
        Paragraph(
            f"Generated {generated_on} - {total_slots} sessions - "
            f"{total_mins // 60}h {total_mins % 60}m total study time",
            s["subtitle"]
        ),
        HRFlowable(width=TABLE_W, thickness=1, color=BORDER, spaceAfter=6),
        build_legend(s),
        Spacer(1, 8),
        build_timetable_table(rows, s),
    ]
    
    if summary:
        story += [
            Spacer(1, 8),
            HRFlowable(width=TABLE_W, thickness=0.5, color=BORDER, spaceBefore=2, spaceAfter=4),
            Paragraph(summary, s["summary"]),
        ]
        
    # FIXED: Cleaned duplicate definitions, typo bugs, and string quotes down here
    doc.build(story)
    print(f"PDF saved -> {output_path}")

def trigger_daily_nudge(timetable_json_path, recipient_email):
    """
    Safely loads the timetable data to find 'rows', then triggers the email.
    """
    if not recipient_email:
        print("No email provided. Skipping daily nudge.")
        return
        
    try:
        rows, summary = load_timetable(timetable_json_path)
        send_daily_nudge(rows, recipient_email)
        print(f"Success: Daily nudge triggered for {recipient_email}")
    except Exception as e:
        print(f"An error occurred while sending nudge: {e}")


if __name__ == "__main__":
    # This block only runs if you execute pdf_export.py directly for testing
    test_email = "test@example.com"  
    rows, summary = load_timetable("timetable.json")
    generate_pdf(rows, summary, output_path="my_timetable.pdf")
    send_daily_nudge(rows, test_email)