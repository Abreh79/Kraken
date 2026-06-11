"""
Kraken Audit — SaaS Frontend API Server
FastAPI backend serving the customer-facing dashboard.
"""

import os
import json
import subprocess
import shutil
import uuid
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Kraken Audit API", version="1.0.0")

# ─── CORS: allow Vercel / any frontend origin ───
BACKEND_HOST = os.environ.get("KRAKEN_HOST", "http://localhost:8080")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Wide open for demo — restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
INCOMING_DIR = Path("/home/team/shared/invoices/incoming")
REPORTS_DIR = BASE_DIR.parent / "docs" / "reports"
PROCESSED_DIR = Path("/home/team/shared/invoices/processed")

INCOMING_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ─────────────────────────────────────────────
#  DATABASE HELPERS
# ─────────────────────────────────────────────

def _db(sql: str) -> list:
    try:
        r = subprocess.run(["team-db", sql], capture_output=True, text=True, timeout=10)
        if r.returncode == 0 and r.stdout.strip():
            return json.loads(r.stdout)
    except Exception:
        pass
    return []


def _get_available_reports():
    """Return a dict of { invoice_number: pdf_path } for download."""
    reports = {}
    if REPORTS_DIR.exists():
        for f in REPORTS_DIR.iterdir():
            if f.suffix.lower() == ".pdf" and f.name.startswith("audit_report_"):
                inv = f.name.replace("audit_report_", "").replace(".pdf", "")
                reports[inv] = f.name
    return reports


# ─────────────────────────────────────────────
#  API ENDPOINTS
# ─────────────────────────────────────────────

@app.get("/api/health")
def health_check():
    """Health endpoint for Vercel / uptime monitoring."""
    return {
        "status": "ok",
        "service": "Kraken Audit API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/dashboard")
def get_dashboard():
    """Aggregate metrics: total invoices, flags, leakage, per-vendor."""
    invoices = _db("SELECT * FROM audit_invoices ORDER BY created_at DESC")
    flags = _db("SELECT * FROM audit_compliance_flags")

    flags_by_inv = {}
    for f in flags:
        flags_by_inv.setdefault(f["invoice_id"], []).append(f)

    total_inv = len(invoices)
    total_flags = len(flags)
    total_savings = sum(f.get("estimated_savings", 0) or 0 for f in flags)

    vendor_map = {}
    for inv in invoices:
        vname = inv.get("vendor_name", "Unknown") or "Unknown"
        if vname not in vendor_map:
            vendor_map[vname] = {"invoices": 0, "flags": 0, "savings": 0.0}
        vendor_map[vname]["invoices"] += 1
        inv_flags = flags_by_inv.get(inv["id"], [])
        vendor_map[vname]["flags"] += len(inv_flags)
        vendor_map[vname]["savings"] += sum(
            f.get("estimated_savings", 0) or 0 for f in inv_flags
        )

    return {
        "total_invoices": total_inv,
        "total_flags": total_flags,
        "total_savings": total_savings,
        "vendors": vendor_map,
        "updated_at": datetime.now().isoformat(),
    }


@app.get("/api/invoices")
def get_invoices():
    """List all processed invoices with audit status and downloadable reports."""
    invoices = _db("SELECT * FROM audit_invoices ORDER BY created_at DESC")
    flags = _db("SELECT * FROM audit_compliance_flags")
    available_reports = _get_available_reports()

    flags_by_inv = {}
    for f in flags:
        flags_by_inv.setdefault(f["invoice_id"], []).append(f)

    result = []
    for inv in invoices:
        inv_flags = flags_by_inv.get(inv["id"], [])
        inv_num = inv.get("invoice_number", "") or ""
        status = "FLAGGED" if inv_flags else "PASS"
        total_savings = sum(f.get("estimated_savings", 0) or 0 for f in inv_flags)
        has_report = inv_num in available_reports

        result.append({
            "id": inv["id"],
            "vendor_name": inv.get("vendor_name", "Unknown"),
            "invoice_number": inv_num,
            "invoice_date": inv.get("invoice_date", ""),
            "total_amount": inv.get("total_amount", 0),
            "currency": inv.get("currency", "USD"),
            "status": status,
            "flags": len(inv_flags),
            "savings": total_savings,
            "has_report": has_report,
            "report_file": available_reports.get(inv_num),
        })

    return {"invoices": result, "total": len(result)}


@app.get("/api/reports/{filename}")
def download_report(filename: str):
    """Serve a PDF audit report for download."""
    filepath = REPORTS_DIR / filename
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(str(filepath), media_type="application/pdf",
                        filename=filename)


@app.post("/api/upload")
async def upload_invoice(file: UploadFile = File(...)):
    """Accept a PDF invoice upload and queue it for processing."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".pdf", ".png", ".jpg", ".jpeg"):
        raise HTTPException(status_code=400,
                            detail=f"Unsupported file type: {ext}. Use PDF, PNG, or JPEG.")

    # Save to incoming directory
    safe_name = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    dest = INCOMING_DIR / safe_name
    content = await file.read()
    dest.write_bytes(content)

    return {
        "message": f"Invoice {file.filename} queued for audit",
        "filename": safe_name,
        "size_bytes": len(content),
    }


@app.get("/")
def serve_index():
    """Serve the main SPA."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(index_path.read_text())
    return HTMLResponse("<h1>Kraken Audit — Frontend not built yet</h1>")


if __name__ == "__main__":
    import uvicorn
    print("🐙 Kraken Audit Dashboard — http://0.0.0.0:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)