#!/usr/bin/env python3
"""
Kraken Audit — Client-Facing Reporter Module
Produces:
  1. ASCII Console Savings Dashboard (real-time batch summary)
  2. Professional PDF Audit Reports for flagged invoices
"""

import os
import json
import subprocess
from datetime import datetime
from collections import defaultdict

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "docs", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)


# ─────────────────────────────────────────────
#  DATABASE HELPERS
# ─────────────────────────────────────────────

def _run_db(sql: str):
    """Execute a read-only query against the shared Turso database."""
    try:
        result = subprocess.run(["team-db", sql], capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except Exception:
        pass
    return []


def fetch_session_data() -> dict:
    """Pull all audit records from the DB and structure them for the dashboard."""
    invoices = _run_db("SELECT * FROM audit_invoices ORDER BY created_at DESC")
    flags = _run_db("SELECT * FROM audit_compliance_flags")

    # Index flags by invoice_id
    flags_by_invoice = defaultdict(list)
    for f in flags:
        flags_by_invoice[f["invoice_id"]].append(f)

    total_flags = len(flags)
    total_savings = sum(f.get("estimated_savings", 0) or 0 for f in flags)
    vendor_breakdown = defaultdict(lambda: {"invoices": 0, "flags": 0, "savings": 0.0})

    for inv in invoices:
        vname = inv.get("vendor_name", "Unknown") or "Unknown"
        vendor_breakdown[vname]["invoices"] += 1
        inv_flags = flags_by_invoice.get(inv["id"], [])
        vendor_breakdown[vname]["flags"] += len(inv_flags)
        vendor_breakdown[vname]["savings"] += sum(
            f.get("estimated_savings", 0) or 0 for f in inv_flags
        )

    return {
        "total_invoices": len(invoices),
        "total_flags": total_flags,
        "total_savings": total_savings,
        "vendors": dict(vendor_breakdown),
    }


# ─────────────────────────────────────────────
#  1. ASCII CONSOLE SAVINGS DASHBOARD
# ─────────────────────────────────────────────

DASHBOARD_HEADER = r"""
  _   __                      _    _           _ _   _
 | | / /                     | |  | |         | | | (_)
 | |/ /  __ _ _ __ __ _  __ _| | _| |_   _  __| | |_ _  ___  _ __
 |    \ / _` | '__/ _` |/ _` | |/ / | | | |/ _` | __| |/ _ \| '_ \
 | |\  \ (_| | | | (_| | (_| |   <| | |_| | (_| | |_| | (_) | | | |
 \_| \_/\__,_|_|  \__,_|\__,_|_|\_\_|\__,_|\__,_|\__|_|\___/|_| |_|
"""


def print_dashboard(data: dict = None):
    """Print a highly visual ASCII savings dashboard to the terminal."""
    if data is None:
        data = fetch_session_data()

    total_inv = data["total_invoices"]
    total_flags = data["total_flags"]
    total_savings = data["total_savings"]
    vendors = data["vendors"]

    print(DASHBOARD_HEADER)
    print("  ╔══════════════════════════════════════════════════════════╗")
    print("  ║            KRAAKEN AUDIT — SAVINGS DASHBOARD            ║")
    print("  ╚══════════════════════════════════════════════════════════╝")
    print(f"  🕐  Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # ── Summary Cards ──
    print("  ┌──────────────────────────────┬──────────────────────────────┐")
    print(f"  │  📄  Total Invoices Audited  │  🚩  Compliance Flags Found  │")
    print(f"  │         {total_inv:>6}          │            {total_flags:>3}              │")
    print("  ├──────────────────────────────┼──────────────────────────────┤")
    print(f"  │  💰  Total Financial Leakage  │                              │")
    print(f"  │         ${total_savings:>8,.2f}       │                              │")
    print("  └──────────────────────────────┴──────────────────────────────┘")
    print()

    # ── Per-Vendor Breakdown ──
    if vendors:
        print("  ┌─────────────────────────────────────────────────────────────────┐")
        print("  │                 BREAKDOWN BY VENDOR                              │")
        print("  ├─────────────────────┬──────────┬──────────┬─────────────────────┤")
        print("  │  Vendor             │ Invoices │   Flags  │  Leakage ($)        │")
        print("  ├─────────────────────┼──────────┼──────────┼─────────────────────┤")
        for vname, vdata in sorted(vendors.items(), key=lambda x: -x[1]["savings"]):
            vshort = vname[:19] if len(vname) > 19 else vname
            print(f"  │  {vshort:<19} │    {vdata['invoices']:>3}   │    {vdata['flags']:>3}   │  ${vdata['savings']:>9,.2f}       │")
        print("  └─────────────────────┴──────────┴──────────┴─────────────────────┘")
    else:
        print("  ⚠️   No audit data found in database yet.")
        print("       Process some invoices first!")

    print()
    print("  ══════════════════════════════════════════════════════════")
    if total_savings > 0:
        print(f"  ✅  RECOMMENDED ACTION: Recover ${total_savings:,.2f} from flagged invoices.")
    else:
        print("  ✅  All invoices compliant — no cost recovery needed.")
    print()


# ─────────────────────────────────────────────
#  2. PDF CLIENT AUDIT REPORT
# ─────────────────────────────────────────────

def generate_pdf_report(invoice_meta: dict, compliance_results: list):
    """
    Generate a beautifully formatted, client-facing PDF audit report
    for any invoice that triggered compliance flags.

    Args:
        invoice_meta: dict with vendor_name, invoice_number, invoice_date, total_amount, currency
        compliance_results: list of dicts with flag_type, severity, description, estimated_savings
    """
    if not compliance_results:
        return None  # Only generate reports for flagged invoices

    inv_num = invoice_meta.get("invoice_number", "unknown")
    vendor = invoice_meta.get("vendor_name", "Unknown Vendor")
    date = invoice_meta.get("invoice_date", "N/A")
    total = invoice_meta.get("total_amount", 0)
    currency = invoice_meta.get("currency", "USD")

    total_savings = sum(f.get("estimated_savings", 0) or 0 for f in compliance_results)

    filename = f"audit_report_{inv_num}.pdf"
    filepath = os.path.join(REPORTS_DIR, filename)

    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor, black, white
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable,
    )
    import html

    doc = SimpleDocTemplate(
        filepath, pagesize=letter,
        leftMargin=0.75*inch, rightMargin=0.75*inch,
        topMargin=0.6*inch, bottomMargin=0.6*inch,
    )

    styles = getSampleStyleSheet()

    # ── Custom Styles ──
    s_title = ParagraphStyle("RepTitle", fontSize=20, textColor=HexColor("#1a237e"),
                              spaceAfter=2, fontName="Helvetica-Bold")
    s_subtitle = ParagraphStyle("RepSub", fontSize=9, textColor=HexColor("#666666"),
                                 spaceAfter=12)
    s_section = ParagraphStyle("RepSection", fontSize=13, textColor=HexColor("#1a237e"),
                               spaceBefore=14, spaceAfter=6, fontName="Helvetica-Bold")
    s_body = ParagraphStyle("RepBody", fontSize=9.5, leading=14, spaceAfter=4)
    s_flag_title = ParagraphStyle("FlagTitle", fontSize=11, textColor=HexColor("#c62828"),
                                   fontName="Helvetica-Bold", spaceAfter=2)
    s_savings = ParagraphStyle("Savings", fontSize=12, textColor=HexColor("#2e7d32"),
                                fontName="Helvetica-Bold", spaceAfter=2)
    s_footer = ParagraphStyle("Footer", fontSize=7.5, textColor=HexColor("#999999"),
                               spaceBefore=10)
    s_label = ParagraphStyle("Label", fontSize=9, fontName="Helvetica-Bold", textColor=HexColor("#333333"))
    s_value = ParagraphStyle("Value", fontSize=9, textColor=black)

    story = []

    # ── Header ──
    story.append(Paragraph("KRAAKEN AUDIT", s_title))
    story.append(Paragraph("Automated HVAC Invoice Forensics &bull; Client Audit Report", s_subtitle))
    story.append(HRFlowable(width="100%", thickness=1.5, color=HexColor("#1a237e")))
    story.append(Spacer(1, 0.1*inch))

    # ── Invoice Info Block ──
    info_data = [
        [Paragraph("INVOICE", s_label), Paragraph(f"{inv_num}", s_value),
         Paragraph("VENDOR", s_label), Paragraph(f"{vendor}", s_value)],
        [Paragraph("DATE", s_label), Paragraph(f"{date}", s_value),
         Paragraph("TOTAL BILLED", s_label), Paragraph(f"{currency} {total:,.2f}", s_value)],
    ]
    info_table = Table(info_data, colWidths=[0.7*inch, 1.5*inch, 0.7*inch, 1.5*inch])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, HexColor("#cccccc")),
        ("LINEBELOW", (0, 1), (-1, 1), 0.5, HexColor("#cccccc")),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.15*inch))

    # ── Audit Finding ──
    story.append(Paragraph("AUDIT FINDING", s_section))

    if total_savings > 0:
        story.append(Paragraph(
            f"This invoice contains <b>{len(compliance_results)} compliance violation(s)</b> "
            f"totalling <b>{currency} {total_savings:,.2f}</b> in identified overcharges.",
            s_body
        ))
        story.append(Spacer(1, 0.08*inch))

        for i, flag in enumerate(compliance_results, 1):
            rule = flag.get("flag_type", "Compliance Rule")
            desc = flag.get("description", "")
            savings = flag.get("estimated_savings", 0)
            severity = flag.get("severity", "medium").upper()

            # Severity badge
            sev_color = {"HIGH": "#c62828", "MEDIUM": "#ef6c00", "LOW": "#f9a825"}
            badge = f'<font color="{sev_color.get(severity, "#333")}">[{severity}]</font>'

            story.append(Paragraph(
                f"<b>Violation #{i}:</b> {badge} <b>{rule}</b>",
                s_flag_title
            ))
            story.append(Paragraph(f"{desc}", s_body))

            # Overcharge amount
            if savings > 0:
                rec_payout = total - savings
                story.append(Paragraph(
                    f"💲 <b>Overcharge Identified:</b> {currency} {savings:,.2f}  &nbsp;&nbsp;|&nbsp;&nbsp; "
                    f"✅ <b>Recommended Payout:</b> {currency} {rec_payout:,.2f}",
                    s_savings
                ))
            story.append(Spacer(1, 0.06*inch))

        # ── Savings Summary ──
        story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#2e7d32")))
        story.append(Spacer(1, 0.06*inch))
        rec_total = total - total_savings
        summary_data = [
            [Paragraph("<b>Total Amount Billed</b>", ParagraphStyle("b1", fontSize=10, fontName="Helvetica-Bold")),
             Paragraph(f"{currency} {total:,.2f}", ParagraphStyle("v1", fontSize=10, alignment=TA_RIGHT))],
            [Paragraph("<b>Total Overcharge Identified</b>",
                       ParagraphStyle("b2", fontSize=10, fontName="Helvetica-Bold", textColor=HexColor("#c62828"))),
             Paragraph(f"{currency} {total_savings:,.2f}",
                       ParagraphStyle("v2", fontSize=10, alignment=TA_RIGHT, textColor=HexColor("#c62828")))],
            [Paragraph("<b>Recommended Final Payment</b>",
                       ParagraphStyle("b3", fontSize=12, fontName="Helvetica-Bold", textColor=HexColor("#2e7d32"))),
             Paragraph(f"{currency} {rec_total:,.2f}",
                       ParagraphStyle("v3", fontSize=12, alignment=TA_RIGHT, textColor=HexColor("#2e7d32")))],
        ]
        summary_tbl = Table(summary_data, colWidths=[3*inch, 1.8*inch])
        summary_tbl.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, HexColor("#cccccc")),
            ("LINEBELOW", (0, 1), (-1, 1), 0.5, HexColor("#cccccc")),
            ("LINEABOVE", (0, 2), (-1, 2), 2, HexColor("#2e7d32")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(summary_tbl)
    else:
        story.append(Paragraph("No compliance violations were identified for this invoice.", s_body))

    # ── Footer ──
    story.append(Spacer(1, 0.2*inch))
    story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#cccccc")))
    story.append(Paragraph(
        f"Report generated by Kraken Audit &bull; {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} &bull; "
        "This report is an automated analysis based on the Knowledge Fortress compliance rulebook. "
        "Recommended payouts are suggestions and should be verified with your service provider.",
        s_footer
    ))

    doc.build(story)
    return filepath


# ─────────────────────────────────────────────
#  CONVENIENCE: Full Report Run
# ─────────────────────────────────────────────

def report_on_invoice(invoice_meta: dict, compliance_results: list):
    """
    Called after each invoice is processed.
    1. Generates PDF report if flags exist
    2. Returns path to PDF (or None)
    """
    pdf_path = None
    if compliance_results:
        pdf_path = generate_pdf_report(invoice_meta, compliance_results)
        fname = os.path.basename(pdf_path) if pdf_path else "N/A"
        print(f"  📄  PDF Report: docs/reports/{fname}")
    return pdf_path


def batch_summary():
    """Fetch all data and print the console dashboard."""
    data = fetch_session_data()
    print_dashboard(data)
    return data


if __name__ == "__main__":
    # Standalone: print the dashboard from existing DB data
    batch_summary()