#!/usr/bin/env python3
"""
Mock Invoice Generator for Kraken Audit
Generates sample HVAC invoices for end-to-end pipeline testing.
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_RIGHT

INCOMING_DIR = "/home/team/shared/invoices/incoming"
os.makedirs(INCOMING_DIR, exist_ok=True)

def build_invoice(filename, vendor, date, invoice_id, tech, rate, hours, parts, vague_charges, is_clean=True):
    """Generate a professional-looking HVAC invoice PDF."""
    filepath = os.path.join(INCOMING_DIR, filename)
    doc = SimpleDocTemplate(filepath, pagesize=letter,
                            leftMargin=0.6*inch, rightMargin=0.6*inch,
                            topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    
    # Custom styles
    title_style = ParagraphStyle('InvoiceTitle', fontSize=18, spaceAfter=4, textColor=HexColor('#1a237e'))
    header_style = ParagraphStyle('Header', fontSize=10, spaceAfter=2, textColor=HexColor('#555555'))
    bold_style = ParagraphStyle('Bold', parent=normal, fontSize=9, spaceAfter=3)
    cell_style = ParagraphStyle('Cell', fontSize=8.5, spaceAfter=1)
    cell_bold = ParagraphStyle('CellBold', fontSize=8.5, spaceAfter=1, fontName='Helvetica-Bold')
    small_style = ParagraphStyle('Small', fontSize=7.5, textColor=HexColor('#888888'))

    story = []
    
    # Header
    story.append(Paragraph(f"<b>{vendor}</b>", title_style))
    story.append(Paragraph("HVAC Service & Repair", header_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Invoice info block
    info_data = [
        [Paragraph("<b>Invoice #:</b>", cell_bold), Paragraph(invoice_id, cell_style),
         Paragraph("<b>Date:</b>", cell_bold), Paragraph(date, cell_style)],
        [Paragraph("<b>Terms:</b>", cell_bold), Paragraph("Net 30", cell_style),
         Paragraph("<b>PO #:</b>", cell_bold), Paragraph("N/A", cell_style)],
    ]
    info_table = Table(info_data, colWidths=[0.6*inch, 1.2*inch, 0.5*inch, 1.2*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.15*inch))
    
    # Labor section
    story.append(Paragraph("<b>LABOR CHARGES</b>", bold_style))
    labor_header = [['Technician', 'Description', 'Rate', 'Hours', 'Total']]
    labor_rows = [[Paragraph(tech, cell_style), Paragraph("Service labor as described", cell_style),
                   Paragraph(f"${rate:.2f}/hr", cell_style),
                   Paragraph(f"{hours:.1f}", cell_style),
                   Paragraph(f"${rate * hours:.2f}", cell_style)]]
    labor_table = Table(labor_header + labor_rows, colWidths=[1.2*inch, 1.2*inch, 0.7*inch, 0.5*inch, 0.7*inch])
    labor_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#e8eaf6')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(labor_table)
    story.append(Spacer(1, 0.1*inch))
    
    # Parts & Materials section
    story.append(Paragraph("<b>PARTS &amp; MATERIALS</b>", bold_style))
    parts_header = [['Part #', 'Description', 'Qty', 'Unit Cost', 'Total']]
    parts_rows = []
    for p in parts:
        parts_rows.append([
            Paragraph(p.get('part_no', ''), cell_style),
            Paragraph(p['desc'], cell_style),
            Paragraph(str(p['qty']), cell_style),
            Paragraph(f"${p['unit_cost']:.2f}", cell_style),
            Paragraph(f"${p['qty'] * p['unit_cost']:.2f}", cell_style),
        ])
    parts_table = Table(parts_header + parts_rows, colWidths=[0.8*inch, 1.5*inch, 0.4*inch, 0.65*inch, 0.7*inch])
    parts_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#e8eaf6')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8.5),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(parts_table)
    story.append(Spacer(1, 0.1*inch))
    
    # Vague/Other Charges
    if vague_charges:
        story.append(Paragraph("<b>OTHER CHARGES</b>", bold_style))
        vague_header = [['Type', 'Description', 'Amount']]
        vague_rows = []
        for v in vague_charges:
            vague_rows.append([
                Paragraph(v['type'], cell_style),
                Paragraph(v['desc'], cell_style),
                Paragraph(f"${v['amount']:.2f}", cell_style),
            ])
        vague_table = Table(vague_header + vague_rows, colWidths=[0.8*inch, 2.4*inch, 0.7*inch])
        vague_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#fff3e0')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8.5),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
            ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(vague_table)
        story.append(Spacer(1, 0.1*inch))
    
    # Total
    labor_total = rate * hours
    parts_total = sum(p['qty'] * p['unit_cost'] for p in parts)
    vague_total = sum(v['amount'] for v in vague_charges)
    grand_total = labor_total + parts_total + vague_total
    
    total_data = [
        [Paragraph("", cell_style), Paragraph("", cell_style),
         Paragraph("<b>Subtotal:</b>", cell_bold), Paragraph(f"${labor_total + parts_total + vague_total:.2f}", cell_style)],
    ]
    if vague_total > 0:
        total_data.append([
            Paragraph("", cell_style), Paragraph("", cell_style),
            Paragraph("<b>Total Due:</b>", cell_bold),
            Paragraph(f"<b>${grand_total:.2f}</b>", ParagraphStyle('BoldTotal', fontSize=10, fontName='Helvetica-Bold'))
        ])
    total_table = Table(total_data, colWidths=[1.2*inch, 1.2*inch, 0.7*inch, 0.7*inch])
    total_table.setStyle(TableStyle([
        ('LINEABOVE', (2, 0), (-1, 0), 1, HexColor('#000000')),
        ('LINEABOVE', (2, -1), (-1, -1), 2, HexColor('#000000')),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(total_table)
    story.append(Spacer(1, 0.15*inch))
    
    # Footer
    status = "PASS" if is_clean else "AUDIT REQUIRED"
    status_color = '#2e7d32' if is_clean else '#c62828'
    story.append(Paragraph(
        f'<font color="{status_color}"><b>{status}</b></font>',
        ParagraphStyle('Status', fontSize=9, spaceBefore=6)
    ))
    story.append(Paragraph(
        "Thank you for your business.",
        ParagraphStyle('Footer', fontSize=7.5, textColor=HexColor('#999999'), spaceBefore=4)
    ))
    
    doc.build(story)
    print(f"  ✅ Created: {filename}")
    return filepath


def generate_all():
    print("📄 Kraken Audit — Mock Invoice Generator")
    print("=" * 45)
    
    # ─────────────────────────────────────────────
    # 1. CLEAN INVOICE — Standard Journeyman work
    #    Properly itemized capacitor swap
    #    Labor: $85/hr (under $95 cap) → should PASS
    # ─────────────────────────────────────────────
    build_invoice(
        filename="INV-CLEAN-2026-001.pdf",
        vendor="Pinnacle Mechanical Services",
        date="2026-06-10",
        invoice_id="INV-CLEAN-2026-001",
        tech="Journeyman Dave Miller",
        rate=85.00,
        hours=1.5,
        parts=[
            {"part_no": "CAP-45-5-440", "desc": "45/5 MFD Dual Run Capacitor", "qty": 1, "unit_cost": 42.50},
            {"part_no": "CONT-2P-24V",  "desc": "2-Pole 24V Contactor",       "qty": 1, "unit_cost": 38.00},
        ],
        vague_charges=[],
        is_clean=True
    )
    
    # ─────────────────────────────────────────────
    # 2. DIRTY INVOICE — Multiple violations
    #    - Vague lump-sum: "Fixed AC - $600"
    #    - $140/hr for basic filter swap (standard hours)
    #    → Should trigger: Labor Cap + Vague Billing + Role Discrepancy
    # ─────────────────────────────────────────────
    build_invoice(
        filename="INV-DIRTY-2026-002.pdf",
        vendor="QuickFix HVAC LLC",
        date="2026-06-10",
        invoice_id="INV-DIRTY-2026-002",
        tech="Master Tech Bob Johnson",
        rate=140.00,
        hours=1.0,
        parts=[],
        vague_charges=[
            {"type": "MISC", "desc": "Fixed AC - $600 (lump sum - no breakdown)", "amount": 600.00},
        ],
        is_clean=False
    )
    
    print("=" * 45)
    print(f"📂 Both invoices in: {INCOMING_DIR}/")
    print("🚀 Ready for pipeline! Run: python kraken_audit/watcher_integrated.py")

if __name__ == "__main__":
    generate_all()