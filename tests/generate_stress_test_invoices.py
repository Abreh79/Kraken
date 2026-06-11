#!/usr/bin/env python3
"""
Generate the three stress-test invoices from Manus AI as PDFs
and drop them into the ingestion directory.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_RIGHT
import html

INCOMING = "/home/team/shared/invoices/incoming"
os.makedirs(INCOMING, exist_ok=True)


def esc(text):
    return html.escape(str(text))


def build_invoice(filename, vendor, inv_no, date, bill_to, site, total,
                  tech_log, line_items):
    """Render a professional multi-page HVAC invoice PDF."""
    filepath = os.path.join(INCOMING, filename)
    doc = SimpleDocTemplate(filepath, pagesize=letter,
                            leftMargin=0.6*inch, rightMargin=0.6*inch,
                            topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()

    s_title = ParagraphStyle("T", fontSize=16, textColor=HexColor("#1a237e"), spaceAfter=2, fontName="Helvetica-Bold")
    s_sub = ParagraphStyle("Sub", fontSize=8.5, textColor=HexColor("#666"), spaceAfter=10)
    s_hdr = ParagraphStyle("H", fontSize=11, textColor=HexColor("#1a237e"), spaceBefore=10, spaceAfter=4, fontName="Helvetica-Bold")
    s_cell = ParagraphStyle("C", fontSize=7.8, leading=10)
    s_cell_b = ParagraphStyle("CB", fontSize=7.8, leading=10, fontName="Helvetica-Bold")
    s_sm = ParagraphStyle("SM", fontSize=7.5, textColor=HexColor("#888"))

    story = []
    story.append(Paragraph(f"<b>{esc(vendor)}</b>", s_title))
    story.append(Paragraph("HVAC Service &amp; Repair &bull; Commercial Invoice", s_sub))
    story.append(HRFlowable(width="100%", thickness=1.5, color=HexColor("#1a237e")))
    story.append(Spacer(1, 6))

    # Info block
    info = [
        [Paragraph("<b>Invoice #:</b>", s_cell_b), Paragraph(esc(inv_no), s_cell),
         Paragraph("<b>Date:</b>", s_cell_b), Paragraph(esc(date), s_cell)],
        [Paragraph("<b>Bill To:</b>", s_cell_b), Paragraph(esc(bill_to), s_cell),
         Paragraph("<b>Site:</b>", s_cell_b), Paragraph(esc(site), s_cell)],
    ]
    t = Table(info, colWidths=[0.55*inch, 1.35*inch, 0.55*inch, 1.55*inch])
    t.setStyle(TableStyle([("FONTSIZE", (0,0), (-1,-1), 8), ("BOTTOMPADDING", (0,0), (-1,-1), 3)]))
    story.append(t)
    story.append(Spacer(1, 8))

    # Technician log
    story.append(Paragraph("<b>TECHNICIAN DISPATCH LOG</b>", s_hdr))
    th = [["Tech", "Role", "Hours", "Rate", "Task", "Total"]]
    tr = []
    for row in tech_log:
        tr.append([Paragraph(esc(row[0]), s_cell), Paragraph(esc(row[1]), s_cell),
                   Paragraph(esc(row[2]), s_cell), Paragraph(esc(row[3]), s_cell),
                   Paragraph(esc(row[4]), s_cell), Paragraph(f"${row[5]:,.2f}", s_cell)])
    tw = [0.7, 0.75, 0.5, 0.55, 2.0, 0.55]
    t2 = Table(th + tr, colWidths=[x*inch for x in tw])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), HexColor("#e8eaf6")),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 7.5),
        ("GRID", (0,0), (-1,-1), 0.4, HexColor("#ccc")),
        ("ALIGN", (2,0), (-1,-1), "RIGHT"),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("TOPPADDING", (0,0), (-1,-1), 3),
    ]))
    story.append(t2)

    # Line items
    story.append(Paragraph("<b>LINE ITEMS / PARTS &amp; MATERIALS</b>", s_hdr))
    lh = [["Item", "Description", "Qty", "Unit Price", "Total"]]
    lr = []
    for row in line_items:
        lr.append([Paragraph(esc(row[0]), s_cell), Paragraph(esc(row[1]), s_cell),
                   Paragraph(str(row[2]), s_cell), Paragraph(f"${row[3]:,.2f}", s_cell),
                   Paragraph(f"${row[4]:,.2f}", s_cell)])
    lw = [0.5, 2.3, 0.35, 0.55, 0.55]
    t3 = Table(lh + lr, colWidths=[x*inch for x in lw])
    t3.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), HexColor("#e8eaf6")),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 7.5),
        ("GRID", (0,0), (-1,-1), 0.4, HexColor("#ccc")),
        ("ALIGN", (2,0), (-1,-1), "RIGHT"),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
        ("TOPPADDING", (0,0), (-1,-1), 3),
    ]))
    story.append(t3)
    story.append(Spacer(1, 8))

    # Grand total
    story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#1a237e")))
    gt = [[Paragraph("<b>GRAND TOTAL</b>", ParagraphStyle("GT", fontSize=11, fontName="Helvetica-Bold")),
           Paragraph(f"<b>${total:,.2f}</b>", ParagraphStyle("GTV", fontSize=11, fontName="Helvetica-Bold", alignment=TA_RIGHT))]]
    tg = Table(gt, colWidths=[3.5*inch, 1.0*inch])
    tg.setStyle(TableStyle([("BOTTOMPADDING", (0,0), (-1,-1), 4), ("TOPPADDING", (0,0), (-1,-1), 4)]))
    story.append(tg)

    doc.build(story)
    print(f"  ✅ {filename}  (${total:,.2f})")
    return filepath


def generate_all():
    print("📄 Kraken Audit — Stress Test Invoice Generator")
    print("=" * 50)

    # ── INVOICE 1: Arctic Breeze ──
    build_invoice(
        filename="INV-ARB-2026-04.pdf",
        vendor="Arctic Breeze Mechanical Services LLC",
        inv_no="ARB-2026-04",
        date="2026-06-10",
        bill_to="Sunset Ridge Property Management LLC",
        site="Sunset Ridge Office Complex, Dallas, TX",
        total=14755.99,
        tech_log=[
            ("D. Hargrove", "Apprentice", "4.0", "$135/hr", "Refrigerant recovery & recharge RTU-4", 540.00),
            ("M. Calloway", "Master Pipefitter", "3.0", "$115/hr", "Filter replacement - Bldg A AHU-1 thru AHU-6", 345.00),
            ("T. Okafor", "Journeyman EPA", "1.5", "$90/hr", "Capacitor replacement - RTU-2", 135.00),
            ("S. Petrov", "Journeyman EPA", "1.0", "$135/hr", "Diagnostic inspection - Bldg C chiller", 135.00),
            ("R. Nguyen", "Apprentice", "3.0R/2.0OT", "$135/hr", "Assisted refrigerant recovery Bldg B RTU-7", 675.00),
            ("B. Thornton", "Senior Tech/BAS", "6.0R/2.0OT", "$135/hr", "BACnet DDC programming Bldg A", 1080.00),
        ],
        line_items=[
            ("R-001", "R-410A Refrigerant - RTU-4 recharge", 8.5, 145.00, 1232.50),
            ("R-002", "R-410A Refrigerant - Bldg B RTU-7 recharge", 6.0, 145.00, 870.00),
            ("R-003", "Refrigerant recovery cylinder rental (2 cyl)", 2, 45.00, 90.00),
            ("R-004", "EPA refrigerant handling fee (uncertified tech)", 1, 175.00, 175.00),
            ("R-005", "Nitrogen pressure test - RTU-4 and RTU-7", 2, 85.00, 170.00),
            ("PM-001", "Filter replacement - AHU-1 thru AHU-6 (MERV-8, no part #)", 6, 185.00, 1110.00),
            ("PM-002", "Preventive maintenance Bldg B (3 RTUs) lump sum", 1, 1800.00, 1800.00),
            ("PM-003", "Evaporator coil cleaning - AHU-3, Bldg A", 1, 285.00, 285.00),
            ("PM-004", "Condenser coil cleaning - RTU-2 and RTU-4", 2, 195.00, 390.00),
            ("PM-005", "Misc PM materials and supplies - Bldg C", 1, 640.00, 640.00),
            ("CR-001", "Dual-run capacitor RTU-2 (45/5 440V) no part #", 1, 485.00, 485.00),
            ("CR-002", "Contactor RTU-4 (40A 3-pole #CONT-40A-3P-24V)", 1, 178.00, 178.00),
            ("CR-003", "Thermostat - Bldg C Suite 310 (T6 Pro) Senior Tech rate", 1, 395.00, 395.00),
            ("CR-004", "Blower motor AHU-3 (1/2 HP PSC #MOT-PSC-0.5HP-460V)", 1, 435.00, 435.00),
            ("CR-005", "Fixed AC problems Bldg B server room flat rate", 1, 950.00, 950.00),
            ("CR-006", "Expansion valve RTU-4 (TXV #TXV-R410A-3T)", 1, 325.00, 325.00),
            ("DF-001", "Standard diagnostic - Bldg C chiller (10AM no emergency)", 1, 250.00, 250.00),
            ("DF-002", "After-hours emergency dispatch fee (no times documented)", 1, 385.00, 385.00),
            ("DF-003", "City of Dallas mechanical permit - RTU-4", 1, 145.00, 145.00),
            ("DF-004", "EPA Section 608 refrigerant disposal doc fee", 1, 55.00, 55.00),
            ("DF-005", "Fuel surcharge and travel (no mileage documented)", 1, 320.00, 320.00),
        ],
    )

    # ── INVOICE 2: Pinnacle Climate ──
    build_invoice(
        filename="INV-PCS-2026-1.pdf",
        vendor="Pinnacle Climate Solutions Inc.",
        inv_no="PCS-2026-1",
        date="2026-06-10",
        bill_to="Lakewood Medical Plaza Partners LP",
        site="Lakewood Medical Plaza, Houston, TX",
        total=13755.33,
        tech_log=[
            ("C. Vasquez", "Master Pipefitter", "5.0", "$115/hr", "R-22 recovery & recharge Bldg 1 AHU-2", 575.00),
            ("A. Mbeki", "Senior Tech/BAS", "3.0", "$135/hr", "Thermostat replacement Bldg 2 (basic T6 Pro)", 405.00),
            ("D. Kowalski", "Journeyman EPA", "2.0R/3.0DT", "$180/hr DT", "Blower motor replacement Bldg 3 AHU-5 (Tue)", 900.00),
            ("F. Delacroix", "Journeyman EPA", "1.0", "$135/hr", "Diagnostic Bldg 4 RTU (standard 9:30AM)", 135.00),
            ("G. Osei", "Journeyman EPA", "6.0", "$90/hr", "Condenser coil cleaning & PM Bldg 1", 540.00),
            ("H. Steinberg", "Apprentice", "4.0", "$135/hr", "R-22 refrigerant handling assist", 540.00),
        ],
        line_items=[
            ("R-001", "R-22 Refrigerant - Bldg 1 AHU-2 recharge (no reclaimer cert #)", 7.5, 285.00, 2137.50),
            ("R-002", "Refrigerant recovery - R-22 recovered from AHU-2", 4.5, 35.00, 157.50),
            ("R-003", "Leak detection - AHU-2 evaporator coil", 1, 145.00, 145.00),
            ("R-004", "Nitrogen pressure test - AHU-2 post-repair", 1, 85.00, 85.00),
            ("R-005", "Deep vacuum evacuation AHU-2 (500 micron)", 1, 110.00, 110.00),
            ("CR-001", "Blower motor Bldg 3 AHU-5 (1/2 HP PSC) no part #. Double-time Tuesday", 1, 1450.00, 1450.00),
            ("CR-002", "Thermostat replacement Bldg 2 (T6 Pro x3) Senior Tech rate", 3, 285.00, 855.00),
            ("CR-003", "Contactor Bldg 4 RTU-6 (30A 2-pole #CONT-30A-2P-24V)", 1, 132.00, 132.00),
            ("CR-004", "Repaired bad parts Bldg 4 RTU-8 flat rate", 1, 780.00, 780.00),
            ("CR-005", "Dual-run capacitor Bldg 1 RTU-2 (35/5 440V #CAP-35-5-440)", 1, 128.00, 128.00),
            ("CR-006", "Replaced HVAC components Bldg 2 mech room, no itemization", 1, 1240.00, 1240.00),
            ("PM-001", "Preventive maintenance Bldg 1 RTU-1, RTU-2, RTU-3", 3, 195.00, 585.00),
            ("PM-002", "Diagnostic inspection Bldg 4 RTU-9 (standard hours)", 1, 310.00, 310.00),
            ("PM-003", "Filter replacement Bldg 3 AHU-4/AHU-5 (MERV-8) no part #", 2, 165.00, 330.00),
            ("PM-004", "Belt replacement Bldg 1 AHU-2 (Part #BELT-B48)", 1, 67.00, 67.00),
            ("PM-005", "Misc service charges Bldg 2 and Bldg 4", 1, 875.00, 875.00),
        ],
    )

    # ── INVOICE 3: Vanguard Industrial ──
    build_invoice(
        filename="INV-VIG-2026-01.pdf",
        vendor="Vanguard Industrial HVAC Systems LLC",
        inv_no="VIG-2026-01",
        date="2026-06-10",
        bill_to="Northgate Logistics & Distribution LLC",
        site="Northgate Distribution Center, Phoenix, AZ",
        total=27368.88,
        tech_log=[
            ("W. Abramowitz", "Master Pipefitter", "4.0", "$115/hr", "Filter replacement - Warehouse A MAU x8", 460.00),
            ("P. Nakamura", "Journeyman EPA", "8.0R/4.0OT", "$90/hr", "Chiller teardown & tube cleaning 150-ton", 900.00),
            ("L. Oduya", "Journeyman EPA", "4.0", "$155/hr", "Warehouse C R-410A recharge RTU-11/12", 620.00),
            ("K. Fitzgerald", "Senior Tech/BAS", "6.0", "$135/hr", "VFD parameter programming chiller pumps x3", 810.00),
            ("T. Okonkwo", "Apprentice", "3.0", "$155/hr", "Refrigerant recovery assist Warehouse C", 465.00),
            ("M. Guerrero", "Journeyman EPA", "1.0", "$155/hr", "Diagnostic Warehouse D RTU-15 (11AM)", 155.00),
            ("J. Abernathy", "Master Pipefitter", "5.0R/2.0OT", "$115/hr", "Compressor replacement RTU-3 5-ton scroll", 805.00),
        ],
        line_items=[
            ("R-001", "R-410A Refrigerant - Warehouse C RTU-11 recharge", 10.5, 165.00, 1732.50),
            ("R-002", "R-410A Refrigerant - Warehouse C RTU-12 recharge", 7.0, 165.00, 1155.00),
            ("R-003", "Refrigerant recovery R-410A from RTU-11/12", 6.5, 28.00, 182.00),
            ("R-004", "Electronic leak detection - RTU-11 and RTU-12", 2, 145.00, 290.00),
            ("R-005", "Nitrogen pressure test - RTU-11 and RTU-12", 2, 85.00, 170.00),
            ("R-006", "Deep vacuum evacuation RTU-11 and RTU-12", 2, 110.00, 220.00),
            ("M-001", "Chiller teardown & eddy current tube test 150-ton 30XA", 1, 3200.00, 3200.00),
            ("M-002", "Compressor replacement RTU-3 (Copeland 5-ton scroll)", 1, 2045.00, 2045.00),
            ("M-003", "VFD programming chiller pump VFDs x3", 3, 810.00, 2430.00),
            ("M-004", "General HVAC repairs Warehouse D. No parts, no hours", 1, 2100.00, 2100.00),
            ("M-005", "Cooling tower fill media inspection/partial replacement", 1, 921.00, 921.00),
            ("M-006", "Misc mechanical repairs Warehouses A and C. No breakdown", 1, 1580.00, 1580.00),
            ("PM-001", "Filter replacement MAU-1 thru MAU-8 (Master rate)", 8, 195.00, 1560.00),
            ("PM-002", "Preventive maintenance all warehouses. Lump sum", 1, 1950.00, 1950.00),
            ("PM-003", "Diagnostic inspection Warehouse D RTU-15 (11AM)", 1, 195.00, 195.00),
            ("PM-004", "Condenser coil cleaning Warehouse A RTU-1 thru RTU-4", 4, 185.00, 740.00),
            ("PM-005", "Drain pan treatment Warehouse B AHU-6, AHU-7", 2, 81.00, 162.00),
            ("PM-006", "Misc PM supplies and labor Warehouse D", 1, 720.00, 720.00),
        ],
    )

    print("=" * 50)
    print(f"📂 All 3 invoices in: {INCOMING}/")
    print(f"💰 Combined total: ${14755.99 + 13755.33 + 27368.88:,.2f}")


if __name__ == "__main__":
    generate_all()